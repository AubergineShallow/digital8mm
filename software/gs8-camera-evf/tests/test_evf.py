# SPDX-License-Identifier: MIT
"""Fake-device tests verify logic/ownership, never image quality or HDMI latency."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
from types import SimpleNamespace
from unittest.mock import patch
import json
import time
import unittest

from gs8_camera_evf.controls import ControlSelection
from gs8_camera_evf.controller import Controller, State
from gs8_camera_evf.evf import EvfPolicy, PicameraEvfBackend, fault_reporting_preview_class
from gs8_camera_evf.models import TakeSettings
from gs8_camera_evf.storage import ClipStore
from gs8_camera_evf.writer import InlineClipWriter


def settings(fps=24, shutter=90):
    return TakeSettings.from_selection(ControlSelection(fps, shutter, 1, 'custom', 'raw', 'clean', False), (1.5, 1.25))


def await_condition(predicate, timeout=3):
    end = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() >= end:
            raise AssertionError('worker condition timed out')
        time.sleep(.001)


class FakeRequest:
    def __init__(self, sequence, metadata, *, block=None, copy_error=False, acquire_error=False):
        self.refs = 1
        self.max_refs = 1
        self.stream_map = {'raw': 'raw'}
        self.request = SimpleNamespace(buffers={'raw': SimpleNamespace(metadata=SimpleNamespace(sequence=sequence))})
        self.metadata = deepcopy(metadata)
        self.pixels = bytearray(b'fake-pixels')
        self.block = block
        self.copy_entered = Event()
        self.copy_error = copy_error
        self.acquire_error = acquire_error

    def acquire(self):
        if self.acquire_error:
            raise RuntimeError('injected acquire error')
        self.refs += 1
        self.max_refs = max(self.max_refs, self.refs)

    def release(self):
        self.refs -= 1
        assert self.refs >= 0
        if self.refs == 0:
            self.pixels[:] = b'recycled!!!'

    def get_metadata(self):
        return deepcopy(self.metadata)

    def make_buffer(self, stream):
        self.copy_entered.set()
        if self.block:
            assert self.block.wait(3)
        if self.copy_error:
            raise RuntimeError('injected pixel copy error')
        return bytes(self.pixels)


class FakeCamera:
    def __init__(self):
        self.camera_properties = {'Model': 'imx296'}
        self.sensor_modes = [{'size': (1456, 1088), 'bit_depth': 10, 'fps': 60,
                              'unpacked': 'SBGGR10', 'crop_limits': (0, 0, 1456, 1088)}]
        self.camera_controls = dict.fromkeys(('AeEnable', 'AwbEnable', 'ExposureTime', 'AnalogueGain',
                                             'ColourGains', 'FrameDurationLimits', 'NoiseReductionMode'))
        self.options = {}
        self.helpers = SimpleNamespace(save_dng=self.save_dng)
        self.saved = []
        self.dng_block = None
        self.dng_entered = Event()
        self.dng_error = False
        self.closed = False
        self.started = False
        self.preview_started = False
        self.stop_failures = 0
        self.sequence = 0
        self.displayed = 0
        self.requests = []

    def create_video_configuration(self, **kwargs):
        kwargs['raw'].update(stride=2912, framesize=3168256)
        return kwargs

    def configure(self, config):
        self.config = deepcopy(config)

    def camera_configuration(self):
        return deepcopy(self.config)

    def start_preview(self, preview):
        self.preview_started = True

    def start(self):
        self.started = True

    def stop(self):
        if self.stop_failures:
            self.stop_failures -= 1
            raise RuntimeError('injected stop failure')
        self.started = False

    def stop_preview(self):
        self.preview_started = False

    def close(self):
        self.closed = True

    def save_dng(self, pixels, metadata, raw_config, output):
        self.dng_entered.set()
        if self.dng_block:
            assert self.dng_block.wait(3)
        if self.dng_error:
            raise RuntimeError('injected DNG failure')
        self.saved.append((pixels, deepcopy(metadata), deepcopy(raw_config)))
        output.write(b'TEST-ONLY-NOT-A-DNG:' + pixels)

    def frame(self, **kwargs):
        controls = self.config['controls']
        duration = controls['FrameDurationLimits'][0]
        data = {'SensorTimestamp': 1_000_000_000 + self.sequence * duration * 1000,
                'FrameDuration': duration, 'ExposureTime': controls['ExposureTime'],
                'AnalogueGain': controls['AnalogueGain'], 'ColourGains': controls['ColourGains']}
        data.update(kwargs.pop('metadata', {}))
        request = FakeRequest(self.sequence, data, **kwargs)
        self.sequence += 1
        self.requests.append(request)
        self.pre_callback(request)
        self.displayed += 1  # represents upstream preview after nonblocking callback
        request.release()  # event-loop ownership
        return request


def preview(owner):
    width, height = owner.policy.display_size
    mode = SimpleNamespace(hdisplay=width, vdisplay=height, htotal=width + 100, vtotal=height + 20,
                           flags=0, clock=(width + 100) * (height + 20) * 60 / 1000)
    return SimpleNamespace(crtc=SimpleNamespace(mode=mode, mode_valid=True, refresh=lambda: None))


class EvfTests(unittest.TestCase):
    def backend(self, fps=24, source=None):
        camera = FakeCamera()
        backend = PicameraEvfBackend(EvfPolicy(fps, source), camera_factory=lambda: camera, preview_factory=preview)
        backend.preflight(settings(fps))
        self.addCleanup(backend.close)
        for _ in range(backend.policy.source_fps):
            camera.frame()
        self.assertTrue(backend.warmed_up)
        return backend, camera

    def test_uniform_and_rational_cadence_do_not_duplicate(self):
        for fps in (18, 24):
            policy = EvfPolicy(fps)
            selected = [i for i in range(policy.source_fps * 10) if policy.selects(i)]
            self.assertEqual(len(selected), fps * 10)
            self.assertEqual(set(b - a for a, b in zip(selected, selected[1:])), {policy.source_fps // fps})
        self.assertEqual([i for i in range(11) if EvfPolicy(24, 60).selects(i)], [0, 3, 5, 8, 10])
        self.assertEqual(EvfPolicy(18, 60).describe()['sampling'], 'uneven_rational')

    def test_impossible_exposure_and_unimplemented_modes_are_rejected(self):
        for fps in (18, 24):
            policy = EvfPolicy(fps)
            policy.validate_settings(settings(fps))
            with self.assertRaisesRegex(ValueError, 'cannot fit'):
                policy.validate_settings(settings(fps, 180))
        for changed in (replace(settings(), audio=True), replace(settings(), capture_format='encoded'),
                        replace(settings(), wb_gains=None), replace(settings(), look='film')):
            with self.assertRaises(ValueError):
                EvfPolicy(24).validate_settings(changed)

    def test_full_sensor_colour_and_no_cached_capture(self):
        backend, camera = self.backend()
        self.assertEqual(camera.config['main'], {'size': (728, 544), 'format': 'XRGB8888'})
        self.assertFalse(camera.config['queue'])
        self.assertIsNone(camera.config['encode'])
        self.assertEqual(camera.config['controls']['NoiseReductionMode'], 0)
        self.assertEqual(backend._descriptor['evf']['hdmi_mode_verified']['width'], 1024)
        with self.assertRaisesRegex(ValueError, 'aspect'):
            EvfPolicy(24, preview_size=(640, 480))

    def test_wrong_hdmi_mode_fails_before_sensor_start(self):
        camera = FakeCamera()
        def wrong_preview(owner):
            result = preview(owner)
            result.crtc.mode.hdisplay = 1920
            return result
        backend = PicameraEvfBackend(EvfPolicy(24), camera_factory=lambda: camera, preview_factory=wrong_preview)
        with self.assertRaisesRegex(ValueError, 'HDMI mode'):
            backend.preflight(settings())
        self.assertTrue(camera.closed)
        self.assertFalse(camera.started)

    def test_raw_request_released_before_blocked_dng_and_preview_keeps_advancing(self):
        backend, camera = self.backend()
        camera.dng_block = Event()
        self.addCleanup(camera.dng_block.set)
        backend.start(settings(), time.monotonic_ns())
        request = camera.frame()
        self.assertTrue(camera.dng_entered.wait(2))
        self.assertEqual(request.refs, 0)
        self.assertEqual(request.max_refs, 2)
        before = camera.displayed
        camera.frame()
        camera.frame()
        self.assertEqual(camera.displayed, before + 2)
        backend.request_stop(time.monotonic_ns())
        self.assertFalse(backend.drained(0))
        camera.dng_block.set()
        await_condition(lambda: backend._processing == 0)
        frames = backend.poll(0)
        self.assertTrue(backend.drained(0))
        self.assertEqual([f.index for f in frames], [0, 1])
        self.assertTrue(all(b'fake-pixels' in f.payload for f in frames))

    def test_copier_overload_never_holds_second_camera_request(self):
        backend, camera = self.backend()
        block = Event()
        self.addCleanup(block.set)
        backend.start(settings(), time.monotonic_ns())
        first = camera.frame(block=block)
        self.assertTrue(first.copy_entered.wait(2))
        camera.frame()
        other = camera.frame()
        self.assertEqual(other.max_refs, 1)
        self.assertEqual(other.refs, 0)
        with self.assertRaisesRegex(RuntimeError, 'copier overload'):
            backend.poll(0)
        backend.request_stop(time.monotonic_ns())
        self.assertFalse(backend.drained(0))
        block.set()
        await_condition(lambda: backend._processing == 0)
        backend.poll(0)
        self.assertTrue(backend.drained(0))
        self.assertEqual(first.refs, 0)

    def test_copy_and_conversion_errors_drain_and_release(self):
        for copy_error in (False, True):
            with self.subTest(copy_error=copy_error):
                backend, camera = self.backend()
                camera.dng_error = not copy_error
                backend.start(settings(), time.monotonic_ns())
                request = camera.frame(copy_error=copy_error)
                await_condition(lambda: backend._processing == 0)
                with self.assertRaisesRegex(RuntimeError, 'injected'):
                    backend.poll(0)
                backend.request_stop(time.monotonic_ns())
                self.assertTrue(backend.drained(0))
                self.assertEqual(request.refs, 0)

    def test_bounded_conversion_queue_overload_releases_all_sensor_buffers(self):
        backend, camera = self.backend()
        camera.dng_block = Event()
        self.addCleanup(camera.dng_block.set)
        backend.start(settings(), time.monotonic_ns())
        camera.frame()
        self.assertTrue(camera.dng_entered.wait(2))
        for _ in range(3):
            camera.frame()
            camera.frame()
            await_condition(lambda: backend._busy_copy == 0)
        with self.assertRaisesRegex(RuntimeError, 'conversion queue full'):
            backend.poll(0)
        self.assertTrue(all(r.refs == 0 for r in camera.requests))
        self.assertEqual(backend._raw_copies.qsize(), 2)
        backend.request_stop(time.monotonic_ns())
        camera.dng_block.set()
        await_condition(lambda: backend._processing == 0)
        backend.poll(0)
        self.assertTrue(backend.drained(0))

    def test_bounded_output_queue_overload_is_explicit_and_preview_still_dispatches(self):
        backend, camera = self.backend()
        backend.start(settings(), time.monotonic_ns())
        before = camera.displayed
        for _ in range(9):
            camera.frame()
            await_condition(lambda: backend._processing == 0)
        self.assertEqual(camera.displayed, before + 9)
        self.assertEqual(backend._frames.qsize(), 4)
        with self.assertRaisesRegex(RuntimeError, 'output queue full'):
            backend.poll(0)
        backend.request_stop(time.monotonic_ns())
        self.assertEqual(len(backend.poll(0)), 4)
        self.assertTrue(backend.drained(0))

    def test_acquire_error_returns_semaphore_without_reference_leak(self):
        backend, camera = self.backend()
        backend.start(settings(), time.monotonic_ns())
        request = camera.frame(acquire_error=True)
        with self.assertRaisesRegex(RuntimeError, 'acquire'):
            backend.poll(0)
        self.assertEqual(request.refs, 0)
        self.assertEqual(backend._processing, 0)
        self.assertTrue(backend._retained.acquire(blocking=False))
        backend._retained.release()

    def test_handoff_exception_releases_already_acquired_request(self):
        backend, camera = self.backend()
        backend.start(settings(), time.monotonic_ns())
        with patch.object(backend._raw_requests, 'put_nowait', side_effect=RuntimeError('handoff injected failure')):
            request = camera.frame()
        self.assertEqual(request.max_refs, 2)
        self.assertEqual(request.refs, 0)
        self.assertEqual(backend._processing, 0)
        self.assertEqual(backend._busy_copy, 0)
        with self.assertRaisesRegex(RuntimeError, 'handoff'):
            backend.poll(0)

    def test_render_failure_returns_to_upstream_request_release_and_stop_job(self):
        errors = []
        owner = SimpleNamespace(_fail=errors.append)
        class BasePreview:
            def render_request(self, request):
                raise RuntimeError('HDMI plane disappeared')
        wrapped = fault_reporting_preview_class(BasePreview, owner)()
        request = FakeRequest(0, {})
        job_signalled = False
        # Mirrors the relevant upstream process_requests boundary: render,
        # release display reference, then signal a queued camera stop job.
        wrapped.render_request(request)
        request.release()
        job_signalled = True
        self.assertTrue(job_signalled)
        self.assertEqual(request.refs, 0)
        self.assertEqual(len(errors), 1)
        wrapped.render_request(request)
        self.assertEqual(len(errors), 1)

    def test_idle_sensor_stall_watchdog_uses_host_clock_not_sensor_epoch(self):
        backend, camera = self.backend()
        backend._clock = lambda: backend._last_callback_wall + 2_000_000_001
        with self.assertRaisesRegex(TimeoutError, 'stalled'):
            backend.check_health()

    def test_sensor_sequence_loss_is_not_disguised_as_intentional_sampling(self):
        backend, camera = self.backend()
        backend.start(settings(), time.monotonic_ns())
        camera.sequence += 1
        camera.frame()
        with self.assertRaisesRegex(RuntimeError, 'sequence gap'):
            backend.poll(0)

    def test_applied_exposure_or_timestamp_rate_mismatch_fails_take(self):
        for metadata in ({'ExposureTime': 30_000}, {'FrameDuration': 41_667}, {'SensorTimestamp': 2}):
            backend, camera = self.backend()
            backend.start(settings(), time.monotonic_ns())
            camera.frame(metadata=metadata)
            with self.assertRaises(RuntimeError):
                backend.poll(0)

    def test_counters_and_true_sensor_timestamps_preserved(self):
        backend, camera = self.backend(fps=18)
        backend.start(settings(18), time.monotonic_ns())
        frames = []
        for _ in range(9):
            camera.frame()
            await_condition(lambda: backend._processing == 0)
            frames += backend.poll(0)
        backend.request_stop(time.monotonic_ns())
        summary = backend.final_summary()
        self.assertEqual(summary['sensor_frames_observed'], 9)
        self.assertEqual(summary['sensor_frames_intentionally_not_recorded'], 6)
        self.assertEqual(summary['expected_frame_count'], 3)
        self.assertEqual([f.applied_metadata['sensor_source_index'] for f in frames], [0, 3, 6])
        self.assertEqual(frames[1].sensor_timestamp_ns - frames[0].sensor_timestamp_ns, 3 * 18_519_000)
        self.assertNotEqual(frames[1].sensor_timestamp_ns, frames[1].applied_metadata['record_pts_ns'])

    def test_repeated_takes_keep_preview_open_until_idle_shutdown(self):
        backend, camera = self.backend()
        selection = ControlSelection(24, 90, 1, 'custom', 'raw', 'clean', False)
        with TemporaryDirectory() as temporary, ClipStore(Path(temporary), reserve_bytes=0) as store:
            controller = Controller(store, backend, wb_gains=(1.5, 1.25), writer_factory=InlineClipWriter)
            now = 0
            def step(pressed=False, shutdown=False):
                nonlocal now
                now += 25_000_000
                controller.step(now, selection, trigger_pressed=pressed, shutdown_requested=shutdown)
            paths = []
            for _ in range(2):
                step(); step(); step(True); step(True)
                self.assertEqual(controller.state, State.STARTING)
                camera.frame()
                await_condition(lambda: backend._processing == 0)
                step(True)
                self.assertEqual(controller.state, State.RECORDING)
                step(); step(); step()
                self.assertEqual(controller.state, State.READY)
                paths.append(controller.last_clip)
                self.assertTrue(camera.preview_started)
                self.assertFalse(camera.closed)
            self.assertNotEqual(*paths)
            self.assertTrue(all(json.loads((p / 'manifest.json').read_text())['status'] == 'complete' for p in paths))
            step(shutdown=True)
            self.assertTrue(controller.safe_to_request_poweroff)
            self.assertTrue(camera.closed)
            self.assertFalse(camera.preview_started)

    def test_failed_close_does_not_claim_closed_and_retry_releases_camera(self):
        backend, camera = self.backend()
        camera.stop_failures = 1
        with self.assertRaisesRegex(RuntimeError, 'stop failure'):
            backend.close()
        self.assertFalse(backend._closed)
        self.assertFalse(camera.closed)
        backend.close()
        self.assertTrue(camera.closed)

    def test_idle_health_failure_closes_preview_and_inhibits_ready(self):
        backend, camera = self.backend()
        selection = ControlSelection(24, 90, 1, 'custom', 'raw', 'clean', False)
        with TemporaryDirectory() as temporary, ClipStore(Path(temporary), reserve_bytes=0) as store:
            controller = Controller(store, backend)
            backend._fail(RuntimeError('HDMI disconnected'))
            controller.step(0, selection, trigger_pressed=False)
            self.assertEqual(controller.state, State.FAULT)
            self.assertTrue(camera.closed)


if __name__ == '__main__':
    unittest.main()
