# SPDX-License-Identifier: MIT
"""Cadence policy and bounded Picamera2 colour EVF / DNG capture adapter.

Hardware code is lazy-loaded so the fault/ownership tests run without a Pi.
The event callback does metadata and reference handoff only; it never copies
pixels, compresses an image, waits for queue space, or performs filesystem I/O.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from copy import deepcopy
from io import BytesIO
from queue import Queue, Empty, Full
from threading import BoundedSemaphore, Event, Lock, Thread
import math
import time

from .models import Frame


# Keep the independently packaged PC planner's contract explicit here. These
# are provisional acceptance bounds, not measured IMX296 quantization limits.
# tests/test_evf_post_contract.py guards this boundary without a runtime import
# of post/gs8-sequence or a dependency on that package being installed on the Pi.
EXPOSURE_TOLERANCE_US = 100
EXPOSURE_TOLERANCE_FRACTION = 0.005
GAIN_TOLERANCE_ABSOLUTE = 0.01
GAIN_TOLERANCE_FRACTION = 0.01
MIN_COLOUR_GAIN = 0.01
MAX_COLOUR_GAIN = 32.0


def fault_reporting_preview_class(base, owner):
    """Catch display failure before Picamera2's request release/job signalling.

    Catching only handle_request is too late: process_requests releases its
    display reference after render_request returns, including on HDMI failure.
    """
    class FaultReportingDrmPreview(base):
        _display_failed = False

        def render_request(self, request):
            if self._display_failed:
                return
            try:
                super().render_request(request)
            except Exception as error:
                self._display_failed = True
                owner._fail(error)

        def handle_request(self, picam2):
            try:
                super().handle_request(picam2)
            except Exception as error:
                owner._fail(error)

    return FaultReportingDrmPreview


@dataclass(frozen=True)
class EvfPolicy:
    record_fps: int
    source_fps: int | None = None
    preview_size: tuple[int, int] = (728, 544)
    buffer_count: int = 4
    exposure_margin_us: int = 200
    display_size: tuple[int, int] = (1024, 768)

    def __post_init__(self):
        if self.record_fps not in (18, 24):
            raise ValueError('record FPS must be 18 or 24')
        if self.source_fps is None:
            object.__setattr__(self, 'source_fps', 54 if self.record_fps == 18 else 48)
        if self.source_fps not in (48, 54, 60) or self.source_fps <= self.record_fps:
            raise ValueError('source FPS must be 48, 54 or 60 and above record FPS')
        if self.buffer_count != 4:
            raise ValueError('this adapter is qualified in tests for exactly four camera buffers')
        if (len(self.preview_size) != 2 or any(type(v) is not int or v <= 0 or v % 2 for v in self.preview_size)):
            raise ValueError('preview dimensions must be positive even integers')
        if self.preview_size[0] * 1088 != self.preview_size[1] * 1456:
            raise ValueError('preview aspect ratio must equal the full sensor: use 728x544 or 1456x1088')
        if (len(self.display_size) != 2 or any(type(v) is not int or v <= 0 for v in self.display_size)):
            raise ValueError('HDMI canvas dimensions must be positive integers')
        if self.exposure_margin_us != 200:
            raise ValueError('the provisional sensor timing margin is fixed at 200 us')

    @property
    def frame_duration_us(self):
        return round(Fraction(1_000_000, self.source_fps))

    def validate_settings(self, settings):
        if settings.fps != self.record_fps:
            raise ValueError('take and EVF cadence differ')
        if settings.audio or settings.capture_format != 'raw':
            raise ValueError('EVF hardware adapter currently supports silent DNG only; audio/encoded are uncommissioned')
        if settings.look != 'clean':
            raise ValueError('EVF hardware adapter supports the clean ISP preview only; film/pxl are uncommissioned')
        if settings.wb_gains is None:
            raise ValueError('hardware capture requires measured --wb-gains RED BLUE')
        if any(not MIN_COLOUR_GAIN <= value <= MAX_COLOUR_GAIN for value in settings.wb_gains):
            raise ValueError('hardware white-balance gains must fit the PC planner range 0.01..32')
        limit = self.frame_duration_us - self.exposure_margin_us
        if not 0 < settings.exposure_us <= limit:
            raise ValueError(f'{settings.exposure_us} us exposure cannot fit {self.source_fps} FPS with '
                             f'timing margin (maximum {limit} us); explicitly select a shorter shutter angle')

    def selects(self, source_index):
        """Integer phase accumulator; first frame retained, never duplicated.

        Exact integer ratios have uniform spacing. For example 60 -> 24 has
        alternating 3/2 source periods; it is NOT evenly spaced 24 FPS capture.
        Uneven ratios remain available for commissioning, but are unsupported
        by the current PC planner. Do not replace true timestamps with nominal
        PTS to make such a take pass. Use the default 54 -> 18 or 48 -> 24 path.
        """
        if type(source_index) is not int or source_index < 0:
            raise ValueError('source index must be a nonnegative integer')
        return source_index == 0 or (source_index * self.record_fps // self.source_fps !=
                                     (source_index - 1) * self.record_fps // self.source_fps)

    def describe(self):
        uniform = self.source_fps % self.record_fps == 0
        return {'record_fps_nominal': self.record_fps, 'source_fps_requested': self.source_fps,
                'frame_duration_us_requested': self.frame_duration_us,
                'sampling': 'uniform_integer_ratio' if uniform else 'uneven_rational',
                'post_planner_sampling': ('uniform_candidate_requires_measured_cadence_validation' if uniform
                                          else 'unsupported_uneven_cadence'),
                'post_planner_sampling_note': ('Actual timestamps still require independent PC validation.' if uniform
                    else 'Commissioning only: current PC planner rejects uneven sampling; use 54 to 18 or 48 to 24 FPS.'),
                'preview_stream': 'main', 'preview_format_requested': 'XRGB8888',
                'preview_size_requested': list(self.preview_size), 'camera_buffers': self.buffer_count,
                'display_canvas_requested': list(self.display_size), 'display_aspect_policy': 'letterbox_full_sensor',
                'retained_raw_requests_max': 1, 'copied_raw_queue_max': 2, 'dng_output_queue_max': 4,
                'queue_last_capture': False, 'noise_reduction': 'off',
                'display_refresh_hz': 'external HDMI mode; must be measured',
                'latency_measured': False}


class PicameraEvfBackend:
    """Contract-2 capture adapter. One controller owner, two bounded workers.

    preflight opens continuous preview for warmup; start enables recording.
    request_stop gates recording immediately. Preview continues through writer
    drain; release_take resets take counters while retaining live preview.
    close releases camera and preview on shutdown or fault.
    Hardware is not commissioned merely because fake-camera tests pass.
    """
    simulated = False

    def __init__(self, policy: EvfPolicy, *, camera_factory=None, preview_factory=None, clock_ns=time.monotonic_ns):
        self.policy = policy
        self._camera_factory = camera_factory
        self._preview_factory = preview_factory
        self._clock = clock_ns
        self._lock = Lock()
        self._retained = BoundedSemaphore(1)
        self._raw_requests = Queue(maxsize=1)
        self._raw_copies = Queue(maxsize=2)
        self._frames = Queue(maxsize=4)
        self._exit = Event()
        self._camera = None
        self._workers = []
        self._opened = False
        self._preview_started = False
        self._camera_stop_done = False
        self._preview_stop_done = False
        self._closed = False
        self._recording = False
        self._busy_copy = 0
        self._busy_dng = 0
        self._processing = 0  # covers queue-to-worker handoff gaps as well as active work
        self._failure = None
        self._failure_reported = False
        self._stop_ns = None
        self._expected = 0
        self._delivered = 0
        self._observed = 0
        self._warmup = 0
        self._last_sequence = None
        self._last_timestamp = None
        self._source_first = None
        self._source_last = None
        self._first_timestamp = None
        self._final_timestamp = None
        self._callback_max_ns = 0
        self._last_callback_wall = None

    def _fail(self, error):
        with self._lock:
            if self._failure is None:
                self._failure = f'{type(error).__name__}: {error}'
            self._recording = False

    @property
    def warmed_up(self):
        with self._lock:
            return self._warmup >= self.policy.source_fps and self._failure is None

    def _open_camera(self):
        if self._camera_factory is not None:
            return self._camera_factory()
        from picamera2 import Picamera2
        return Picamera2()

    def _start_preview(self):
        if self._preview_factory is not None:
            preview = self._preview_factory(self)
        else:
            from picamera2.previews import DrmPreview
            FaultReportingDrmPreview = fault_reporting_preview_class(DrmPreview, self)

            # DRM scans the ISP DMA buffer; no Qt/compositor, JPEG or Python RGB copy.
            preview = FaultReportingDrmPreview(x=0, y=0, width=self.policy.display_size[0],
                                              height=self.policy.display_size[1])
        self._preview_started = True
        self._camera.start_preview(preview)
        crtc = preview.crtc
        crtc.refresh()
        mode = crtc.mode
        refresh = mode.clock * 1000 / (mode.htotal * mode.vtotal) if mode.htotal and mode.vtotal else 0
        if (not crtc.mode_valid or (mode.hdisplay, mode.vdisplay) != self.policy.display_size
                or not 59 <= refresh <= 61 or mode.flags & (1 << 4)):
            raise ValueError('active HDMI mode must match --display-size at progressive 60/59.94 Hz; configure KMS first')
        self._descriptor['evf']['hdmi_mode_verified'] = {'width': mode.hdisplay, 'height': mode.vdisplay,
                                                        'refresh_hz_from_timing': refresh, 'progressive': True}

    def preflight(self, settings):
        self.policy.validate_settings(settings)
        if self._opened:
            if settings != self._settings:
                raise ValueError('cannot change settings after continuous preview starts')
            return deepcopy(self._descriptor)
        if self._closed:
            raise RuntimeError('a closed backend cannot be reused; construct a new session')
        self._settings = settings
        try:
            self._camera = self._open_camera()
            model = str(self._camera.camera_properties.get('Model', ''))
            # Normalize only this exact sensor identity, not an arbitrary family
            # substring or an unknown suffix. RAW Bayer-mode checks below remain
            # mandatory before treating the sensor as the colour variant.
            if model.strip().casefold() != 'imx296':
                raise ValueError(f'expected colour IMX296; negotiated camera is {model!r}')
            candidates = [m for m in self._camera.sensor_modes
                          if tuple(m['size']) == (1456, 1088) and m['bit_depth'] == 10
                          and m['fps'] >= self.policy.source_fps - 0.05
                          and any(cfa in m['unpacked'] for cfa in ('RGGB', 'GRBG', 'GBRG', 'BGGR'))]
            if not candidates:
                raise ValueError('no full-resolution colour RAW10 mode supports the requested source FPS')
            mode = candidates[0]
            controls = {'AeEnable': False, 'AwbEnable': False, 'ExposureTime': settings.exposure_us,
                        'AnalogueGain': settings.analogue_gain, 'ColourGains': settings.wb_gains,
                        'FrameDurationLimits': (self.policy.frame_duration_us,) * 2,
                        'NoiseReductionMode': 0}
            missing = controls.keys() - self._camera.camera_controls.keys()
            if missing:
                raise ValueError(f'required camera controls unavailable: {sorted(missing)}')
            config = self._camera.create_video_configuration(
                main={'size': self.policy.preview_size, 'format': 'XRGB8888'},
                raw={'size': tuple(mode['size']), 'format': mode['unpacked']}, lores=None,
                sensor={'output_size': tuple(mode['size']), 'bit_depth': 10},
                buffer_count=self.policy.buffer_count, queue=False, display='main', encode=None, controls=controls)
            self._camera.configure(config)
            actual = self._camera.camera_configuration()
            if (tuple(actual['raw']['size']) != (1456, 1088) or actual['raw']['format'] != mode['unpacked']
                    or actual['main']['format'] != 'XRGB8888'
                    or tuple(actual['main']['size']) != self.policy.preview_size
                    or actual['buffer_count'] != 4 or actual['queue'] is not False):
                raise ValueError('camera changed a required stream format/size/buffer policy')
            self._raw_config = deepcopy(actual['raw'])
            self._descriptor = {'model': 'imx296', 'model_reported': model, 'mode': 'picamera2_colour_raw10_and_drm',
                                'width': actual['raw']['size'][0], 'height': actual['raw']['size'][1],
                                'bit_depth': mode['bit_depth'], 'crop': list(mode['crop_limits']),
                                'timestamp_clock': 'libcamera_SensorTimestamp_CLOCK_BOOTTIME_ns',
                                'raw_stream': deepcopy(self._raw_config), 'evf': self.policy.describe(),
                                'source_sequence_semantics': 'frame metadata sequence of raw libcamera buffer',
                                'record_sequence_semantics': 'selected recording samples only; see applied sensor_frame_sequence',
                                'simulated': False}
            self._camera.options['compress_level'] = 0
            self._camera.pre_callback = self._on_request
            self._workers = [Thread(target=self._copy_loop, name='gs8-evf-raw-copy'),
                             Thread(target=self._dng_loop, name='gs8-evf-dng')]
            for worker in self._workers:
                worker.start()
            self._start_preview()
            self._camera.start()
            self._opened = True
            self._last_callback_wall = self._clock()
            return deepcopy(self._descriptor)
        except Exception:
            try:
                self.close()
            except Exception:
                pass  # preserve the preflight cause; close retains live-worker ownership on timeout
            raise

    def start(self, settings, now_ns):
        if not self._opened or settings != self._settings or not self.warmed_up:
            raise RuntimeError('start requires successful preflight and one second of settled sensor metadata')
        with self._lock:
            if self._recording or self._stop_ns is not None:
                raise RuntimeError('one take per EVF backend session')
            self._recording = True

    def _on_request(self, request):
        entered = self._clock()
        self._last_callback_wall = entered
        acquired = False
        referenced = False
        counted = False
        try:
            metadata = request.get_metadata()
            sequence = int(request.request.buffers[request.stream_map['raw']].metadata.sequence)
            timestamp = metadata['SensorTimestamp']
            duration = metadata['FrameDuration']
            exposure = metadata['ExposureTime']
            gain = metadata['AnalogueGain']
            colours = metadata['ColourGains']
            if (type(timestamp) is not int or timestamp < 0 or sequence < 0
                    or len(colours) != 2
                    or any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0
                           for v in (duration, exposure, gain, *colours))
                    or exposure < 1
                    or any(not MIN_COLOUR_GAIN <= v <= MAX_COLOUR_GAIN for v in (gain, *colours))):
                raise ValueError('invalid per-frame sensor metadata')
            with self._lock:
                if self._failure:
                    return
                settled = (abs(duration - self.policy.frame_duration_us) <= self.policy.frame_duration_us * .02
                           and abs(exposure - self._settings.exposure_us) <= max(
                               EXPOSURE_TOLERANCE_US, self._settings.exposure_us * EXPOSURE_TOLERANCE_FRACTION)
                           and abs(gain - self._settings.analogue_gain) <= max(
                               GAIN_TOLERANCE_ABSOLUTE, self._settings.analogue_gain * GAIN_TOLERANCE_FRACTION)
                           and all(abs(a - b) <= max(GAIN_TOLERANCE_ABSOLUTE, b * GAIN_TOLERANCE_FRACTION)
                                   for a, b in zip(colours, self._settings.wb_gains)))
                if self._recording and not settled:
                    raise RuntimeError('applied frame duration/exposure/gain/WB differs from the locked take')
                if not self._recording:
                    self._warmup = self._warmup + 1 if settled else 0
                    self._last_sequence = sequence
                    self._last_timestamp = timestamp
                    return
                if self._last_sequence is not None and sequence != self._last_sequence + 1:
                    raise RuntimeError(f'sensor frame sequence gap/regression: {self._last_sequence} -> {sequence}')
                if self._last_timestamp is not None:
                    delta = timestamp - self._last_timestamp
                    if abs(delta - self.policy.frame_duration_us * 1000) > self.policy.frame_duration_us * 100:
                        raise RuntimeError('sensor timestamps do not sustain the requested source cadence')
                self._last_sequence, self._last_timestamp = sequence, timestamp
                if self._source_first is None:
                    self._source_first, self._first_timestamp = sequence, timestamp
                self._source_last, self._final_timestamp = sequence, timestamp
                source_index = self._observed
                self._observed += 1
                if not self.policy.selects(source_index):
                    return
                if not self._retained.acquire(blocking=False):
                    raise RuntimeError('raw copier overload; take failed to preserve live preview')
                acquired = True
                request.acquire()
                referenced = True
                self._busy_copy += 1
                self._processing += 1
                counted = True
                index = self._expected
                self._expected += 1
                packet = (index, source_index, sequence, timestamp, deepcopy(metadata), request)
                self._raw_requests.put_nowait(packet)
                acquired = False  # worker owns both reference and semaphore
                referenced = False
                counted = False
        except Exception as error:
            if acquired:
                if referenced:
                    try:
                        request.release()
                    except Exception as release_error:
                        self._fail(release_error)
                self._retained.release()
            if counted:
                with self._lock:
                    self._busy_copy -= 1
                    self._processing -= 1
            self._fail(error)
        finally:
            self._callback_max_ns = max(self._callback_max_ns, self._clock() - entered)

    def _copy_loop(self):
        while not self._exit.is_set() or not self._raw_requests.empty():
            try:
                packet = self._raw_requests.get(timeout=.02)
            except Empty:
                continue
            index, source_index, sequence, timestamp, metadata, request = packet
            try:
                # make_buffer explicitly copies into an owning ndarray in upstream Picamera2.
                # The sensor request is released before DNG conversion or storage starts.
                pixels = request.make_buffer('raw')
            except Exception as error:
                self._fail(error)
                pixels = None
            finally:
                try:
                    request.release()
                except Exception as error:
                    self._fail(error)
                self._retained.release()
            try:
                handed_off = False
                if pixels is not None:
                    self._raw_copies.put_nowait((index, source_index, sequence, timestamp, metadata, pixels))
                    handed_off = True
            except Full:
                self._fail(RuntimeError('DNG conversion queue full; recording failed, preview remains live'))
            finally:
                with self._lock:
                    self._busy_copy -= 1
                    if not handed_off:
                        self._processing -= 1
                self._raw_requests.task_done()

    def _dng_loop(self):
        while not self._exit.is_set() or self._busy_copy or not self._raw_copies.empty():
            try:
                packet = self._raw_copies.get(timeout=.02)
            except Empty:
                continue
            with self._lock:
                self._busy_dng += 1
            try:
                index, source_index, sequence, timestamp, metadata, pixels = packet
                stream = BytesIO()
                # Public Helpers API accepts an owning copy independently of CompletedRequest.
                self._camera.helpers.save_dng(pixels, metadata, self._raw_config, stream)
                applied = {'exposure_us': metadata['ExposureTime'], 'analogue_gain': metadata['AnalogueGain'],
                           'colour_gains': list(metadata['ColourGains']), 'frame_duration_us': metadata['FrameDuration'],
                           'sensor_frame_sequence': sequence, 'sensor_source_index': source_index,
                           'record_sample_index': index, 'record_pts_ns': round(Fraction(index * 1_000_000_000, self.policy.record_fps)),
                           'effective_shutter_angle_deg': metadata['ExposureTime'] * self.policy.record_fps * 360 / 1_000_000,
                           'libcamera_metadata': metadata}
                self._frames.put_nowait(Frame(index, timestamp, stream.getvalue(), applied))
            except Full:
                self._fail(RuntimeError('DNG output queue full; recording consumer is not keeping up'))
            except Exception as error:
                self._fail(error)
            finally:
                with self._lock:
                    self._busy_dng -= 1
                    self._processing -= 1
                self._raw_copies.task_done()

    def poll(self, now_ns):
        with self._lock:
            if self._failure and not self._failure_reported:
                self._failure_reported = True
                raise RuntimeError(self._failure)
        result = []
        for _ in range(4):
            try:
                result.append(self._frames.get_nowait())
                self._delivered += 1
            except Empty:
                break
        return result

    def request_stop(self, now_ns):
        with self._lock:
            self._recording = False
            if self._stop_ns is None:
                self._stop_ns = now_ns

    def drained(self, now_ns):
        with self._lock:
            return (self._stop_ns is not None and self._processing == 0
                    and self._raw_requests.empty() and self._raw_copies.empty() and self._frames.empty())

    def artifacts(self):
        return []

    def check_health(self):
        """Poll errors while live preview is idle as well as during a take."""
        with self._lock:
            if self._failure:
                raise RuntimeError(self._failure)
            if self._opened and self._last_callback_wall is not None and self._clock() - self._last_callback_wall > 2_000_000_000:
                raise TimeoutError('continuous EVF sensor callbacks have stalled for two seconds')

    def release_take(self):
        """After durable commit, retain continuous preview for another same-settings take."""
        if not self.drained(self._clock()):
            raise RuntimeError('cannot reset a take until all producers and output messages drain')
        self.check_health()
        with self._lock:
            self._stop_ns = None
            self._expected = self._delivered = self._observed = 0
            self._source_first = self._source_last = None
            self._first_timestamp = self._final_timestamp = None

    def final_summary(self):
        if not self.drained(self._clock()):
            raise RuntimeError('final counters unavailable before recording drain')
        measured = ((self._observed - 1) * 1_000_000_000 / (self._final_timestamp - self._first_timestamp)
                    if self._observed > 1 else None)
        return {'evidence': 'backend_counters', 'expected_frame_count': self._expected,
                'source_frame_count': self._expected, 'stop_requested_ns': self._stop_ns,
                'sensor_frames_observed': self._observed, 'sensor_sequence_first': self._source_first,
                'sensor_sequence_last': self._source_last, 'sensor_fps_measured': measured,
                'sensor_frames_intentionally_not_recorded': self._observed - self._expected,
                'callback_max_ns': self._callback_max_ns, 'evf': self.policy.describe()}

    def close(self):
        if self._closed:
            return
        self.request_stop(self._clock())
        errors = []
        if self._camera is not None and not self._camera_stop_done:
            # stop() joins the camera event boundary before any workers/camera data are freed.
            try:
                self._camera.stop()
                self._camera_stop_done = True
            except Exception as error:
                errors.append(error)
        if self._camera is not None and self._preview_started and not self._preview_stop_done:
            try:
                self._camera.stop_preview()
                self._preview_stop_done = True
            except Exception as error:
                errors.append(error)
        self._exit.set()
        for worker in self._workers:
            worker.join(timeout=10)
            if worker.is_alive():
                # Do not release a camera whose worker may still be reading its buffers.
                raise TimeoutError('EVF worker did not drain; camera ownership retained')
        if errors:
            raise RuntimeError('; '.join(str(e) for e in errors))
        if self._camera is not None:
            self._camera.close()
        self._closed = True
        self._opened = False
