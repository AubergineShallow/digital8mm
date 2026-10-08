# SPDX-License-Identifier: MIT
"""Screenless recording lifecycle with an explicit asynchronous drain boundary.

No GPIO or OS poweroff side effects occur here. The eventual system adapter may
request OS shutdown only after ``safe_to_request_poweroff``. It must never use
that flag to assert GPIO25/OS_HALTED: that is the late kernel halt handshake.
"""
from collections import deque
from enum import Enum

from .backends import CaptureBackend, validate_final_summary, validate_sensor_descriptor
from .controls import ControlSelection
from .models import Frame, TakeSettings
from .storage import ClipStore
from .writer import AsyncClipWriter


class State(str, Enum):
    CHECK = 'check'
    READY = 'ready'
    STARTING = 'starting'
    RECORDING = 'recording'
    STOPPING = 'stopping'
    FAULT = 'fault'
    SHUTDOWN = 'shutdown'


class Controller:
    def __init__(self, store: ClipStore, backend: CaptureBackend, *, trigger_debounce_ms=20,
                 drain_timeout_ms=5000, frame_timeout_ms=2000, wb_gains=None,
                 writer_factory=AsyncClipWriter, fault_observer=None):
        for name, value in (('trigger_debounce_ms', trigger_debounce_ms),
                            ('drain_timeout_ms', drain_timeout_ms), ('frame_timeout_ms', frame_timeout_ms)):
            if type(value) is not int or value <= 0:
                raise ValueError(f'{name} must be a positive integer')
        if fault_observer is not None and not callable(fault_observer):
            raise ValueError('fault_observer must be callable')
        self._fault_observer = fault_observer
        if type(backend.simulated) is not bool:
            raise ValueError('backend must explicitly declare simulated')
        self.store, self.backend = store, backend
        self.state = State.CHECK
        self.events = deque(maxlen=256)
        self.last_clip = None
        self.failure = None
        self.settings = None
        # Validate/copy calibration before a device or transaction can be opened.
        dummy = ControlSelection(18, 180, 1.0, '5600', 'raw', 'film', False)
        self.wb_gains = TakeSettings.from_selection(dummy, wb_gains).wb_gains
        self._writer_factory = writer_factory
        self._writer = None
        self._finish_future = None
        self._submitted_frames = 0
        self.inhibit_reason = None
        self._backend_closed = False
        self._debounce_ns = trigger_debounce_ms * 1_000_000
        self._drain_timeout_ns = drain_timeout_ms * 1_000_000
        self._frame_timeout_ns = frame_timeout_ms * 1_000_000
        self._last_ns = None
        self._candidate = None
        self._candidate_since = 0
        self._stable_trigger = None
        self._armed = False
        self._clip = None
        self._backend_engaged = False
        self._backend_quiescent = True
        self._stop_since = None
        self._stop_requested = False
        self._last_frame_at = None
        self._shutdown = False
        self._commit_ok = True

    @property
    def safe_to_request_poweroff(self):
        return (self.state == State.SHUTDOWN and self._backend_quiescent
                and self.store.active is None and self._commit_ok)

    def _event(self, now, name, **values):
        self.events.append({'monotonic_ns': now, 'event': name, **values})

    def _notify_fault(self, now, error):
        # D2 can retain its shutdown screen before fault cleanup closes DRM.
        # Observers cannot turn a fault into success or prevent capture drain.
        if self._fault_observer is not None:
            try:
                self._fault_observer(error)
            except Exception as observer_error:
                self._event(now, 'fault_observer_error', reason=str(observer_error))

    def _fault(self, now, error):
        if self.failure is None:
            self.failure = f'{type(error).__name__}: {error}'
            self._event(now, 'fault', reason=self.failure)
            self._notify_fault(now, error)
        self._armed = False
        self.state = State.FAULT
        if self._backend_engaged:
            self._stop(now)

    def _stop(self, now):
        if self._stop_since is None:
            self._stop_since = now
            self._event(now, 'stop_requested')
        if not self._stop_requested:
            try:
                self.backend.request_stop(now)
                self._stop_requested = True
            except Exception as error:
                # A failed stop call must never imply a drained capture queue.
                if self.failure is None:
                    self.failure = f'stop: {type(error).__name__}: {error}'
                    self._notify_fault(now, error)
                self.state = State.FAULT
        if self.failure is None:
            self.state = State.STOPPING
        self._armed = False

    def _start(self, now, selection):
        try:
            settings = TakeSettings.from_selection(selection, self.wb_gains)
            if settings.wb == 'custom' and settings.wb_gains is None and not self.backend.simulated:
                raise ValueError('custom WB has not been calibrated')
            sensor = self.backend.preflight(settings)
            self._backend_engaged = True  # even begin() failure must unwind preflight acquisition
            self._backend_quiescent = False
            self._backend_closed = False
            self._stop_since = None
            self._stop_requested = False
            self.settings = settings
            sensor = validate_sensor_descriptor(sensor)
            self._commit_ok = False
            self._clip = self.store.begin(settings.to_dict(), simulated=self.backend.simulated, sensor=sensor)
            self._writer = self._writer_factory(self._clip)
            self._submitted_frames = 0
            self._commit_ok = False
            self._last_frame_at = now
            self.backend.start(settings, now)
            self.state = State.STARTING
            self._event(now, 'take_started', clip_id=self._clip.manifest['clip_id'], settings=settings.to_dict())
        except Exception as error:
            self._fault(now, error)

    def _close(self, now):
        self._backend_engaged = False
        if self._clip is None:
            self._release_backend(now)
            return
        if self._writer is None:
            # Worker creation itself can fail after the transaction opened.
            # No worker owns these handles; keep the startup take incomplete.
            try:
                self._clip.abandon()
            finally:
                self._clip = None
                self._commit_ok = False
                self._release_backend(now)
            return
        # Preserve a durable failed take if audio finalization or another
        # artifact fails after the capture queue has safely drained.
        artifacts = []
        summary = None
        cancelled = self.failure is None and self._submitted_frames == 0
        if self.failure is None:
            try:
                summary = validate_final_summary(self.backend.final_summary(),
                                                 stop_since_ns=self._stop_since, now_ns=now)
                if not cancelled:
                    artifacts = self.backend.artifacts()
                    if not isinstance(artifacts, list):
                        raise RuntimeError('backend artifacts must be an explicit list')
                    audio_artifacts = [a for a in artifacts if a.kind in ('audio', 'simulated_audio')]
                    if len(audio_artifacts) != int(self.settings.audio):
                        raise RuntimeError('completed audio artifact count does not match requested audio mode')
                    for artifact in audio_artifacts:
                        if artifact.audio_info is None:
                            raise RuntimeError('audio timebase metadata is missing')
                        artifact.audio_info.to_dict()
            except Exception as error:
                self._fault(now, error)
        self._finish_future = self._writer.finish(artifacts, summary, self.failure, cancelled)
        self._complete_write(now)

    def _release_backend(self, now):
        try:
            keep_preview = (not self._shutdown and self.failure is None
                            and hasattr(self.backend, 'release_take'))
            if keep_preview:
                self.backend.release_take()
            else:
                self.backend.close()
            self._backend_closed = not keep_preview
            self._backend_quiescent = True
        except Exception as error:
            self._fault(now, error)

    def _complete_write(self, now):
        if self._finish_future is None or not self._finish_future.done():
            return
        try:
            path = self._finish_future.result()
            if self._clip.manifest['status'] == 'failed' and self.failure is None:
                self.failure = self._clip.manifest['failure'] or 'take failed'
                self._notify_fault(now, RuntimeError(self.failure))
            self.last_clip = path
            self._commit_ok = True
            self._event(now, 'take_closed', path=str(path), status=self._clip.manifest['status'])
        except Exception as error:
            self._fault(now, error)
            # A final commit error is never converted to successful completion.
            if self._clip is not None and not self._clip.closed:
                try:
                    self._clip.abandon()
                except Exception as close_error:
                    self._event(now, 'abandon_error', reason=str(close_error))
            self._commit_ok = False
        finally:
            self._writer.close()
            self._writer = None
            self._finish_future = None
            self._release_backend(now)
            self._clip = None
            self._armed = False
            self._stop_since = None
            self._stop_requested = False
        self.state = State.FAULT if self.failure else State.CHECK

    def step(self, now_ns: int, selection: ControlSelection | None, *, trigger_pressed: bool,
             shutdown_requested: bool = False):
        """Tick with a *qualified* selector sample; None inhibits a new take.

        Callers decode/debounce dial contacts separately. Trigger qualification
        is internal. Invalid selector samples during a take do not change its
        frozen settings. Ticks should be frequent; elapsed time cannot reveal
        unsampled bounce. No completion/STOP flag from a backend may substitute
        for its explicit drained() contract.
        """
        if type(now_ns) is not int or now_ns < 0 or (self._last_ns is not None and now_ns < self._last_ns):
            raise ValueError('time must be a nonnegative monotonic integer in nanoseconds')
        if type(trigger_pressed) is not bool or type(shutdown_requested) is not bool:
            raise ValueError('trigger and shutdown inputs must be boolean')
        if (not self._backend_engaged and not self._backend_closed and not self.failure
                and hasattr(self.backend, 'check_health')):
            try:
                self.backend.check_health()
            except Exception as error:
                self._backend_quiescent = False
                self._fault(now_ns, error)
        self.inhibit_reason = None
        if selection is not None:
            try:
                candidate = TakeSettings.from_selection(selection, self.wb_gains)
                if candidate.wb == 'custom' and candidate.wb_gains is None and not self.backend.simulated:
                    raise ValueError('custom WB has not been calibrated')
            except (TypeError, ValueError) as error:
                self.inhibit_reason = str(error)
                selection = None
        self._last_ns = now_ns
        if trigger_pressed != self._candidate:
            self._candidate = trigger_pressed
            self._candidate_since = now_ns
        stable = None
        rising = False
        if now_ns - self._candidate_since >= self._debounce_ns:
            stable = trigger_pressed
            rising = stable and self._stable_trigger is not True
            self._stable_trigger = stable
        if shutdown_requested and not self._shutdown:
            self._shutdown = True
            self._event(now_ns, 'shutdown_latched')
        was_active = self._backend_engaged or self._clip is not None
        if self._writer is not None:
            error = self._writer.poll_error()
            if error is not None:
                self._fault(now_ns, error)
        if self._backend_engaged:
            if self._shutdown or stable is False or self.failure:
                self._stop(now_ns)
            try:
                frames = self.backend.poll(now_ns)
                if not isinstance(frames, list):
                    raise RuntimeError('backend poll must return an explicit bounded list')
                for frame in frames:
                    if self.failure is None and self._writer is not None:
                        self._writer.submit(frame)
                        error = self._writer.poll_error()
                        if error is not None:
                            raise error
                        if isinstance(frame, Frame):
                            self._submitted_frames += 1
                            self._last_frame_at = now_ns
                        if isinstance(frame, Frame) and self.state == State.STARTING:
                            self.state = State.RECORDING
                            self._event(now_ns, 'first_frame_accepted')
                drained = self.backend.drained(now_ns) if self._stop_requested else False
                if type(drained) is not bool:
                    raise RuntimeError('backend drain acknowledgement must be boolean')
                if drained:
                    self._close(now_ns)
                elif self._stop_since is not None and now_ns - self._stop_since >= self._drain_timeout_ns:
                    self._fault(now_ns, TimeoutError('capture drain was not acknowledged'))
                elif self._stop_since is None and now_ns - self._last_frame_at >= self._frame_timeout_ns:
                    self._fault(now_ns, TimeoutError('no capture frames received within timeout'))
            except Exception as error:
                self._fault(now_ns, error)
        self._complete_write(now_ns)
        if (not self._backend_engaged and self._finish_future is None and not self._backend_quiescent
                and self._clip is None):
            self._release_backend(now_ns)
        if self._shutdown and self._backend_quiescent and self._clip is None and not self._backend_closed:
            self._backend_quiescent = False
            self._release_backend(now_ns)
        if self._shutdown and self._backend_quiescent and self._clip is None and self._commit_ok:
            self.state = State.SHUTDOWN
        elif not self._backend_engaged and self._clip is None and not self.failure and not self._shutdown:
            self.state = State.READY if selection is not None else State.CHECK
            # A release must be observed *after* closure. Holding or pressing
            # while the previous clip drains cannot start the next take.
            if not was_active and stable is False:
                self._armed = True
            elif not was_active and rising:
                armed = self._armed
                self._armed = False
                if armed and selection is not None:
                    self._start(now_ns, selection)
        return self.state

    def recover(self):
        """Explicit service recovery, never automatic after a recording fault."""
        if (self.state != State.FAULT or self._backend_engaged or not self._backend_quiescent or self.store.active is not None
                or self._stable_trigger is not False or self._candidate is not False or self._shutdown):
            raise RuntimeError('recovery requires stopped backend, released trigger and no shutdown request')
        if not self._commit_ok:
            raise RuntimeError('storage commit was not verified; restart and inspect incomplete footage')
        self.failure = None
        self.state = State.CHECK
        self._armed = False

    def indicators(self):
        """Semantic LED patterns; GPIO timing/driver remains a separate adapter."""
        return {'ready': 'steady' if self.state == State.READY else 'off',
                'rec': ('steady' if self.state == State.RECORDING else
                        'fast_blink' if self.state == State.STOPPING else
                        'slow_blink' if self.state == State.STARTING else 'off'),
                'check': 'blink' if self.failure else 'steady' if self.state == State.CHECK else 'off'}
