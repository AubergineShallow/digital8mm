# SPDX-License-Identifier: MIT
"""D2 controls/1S power integrated with the existing durable recorder.

One owner ticks this runtime with monotonic time and freshly acquired inputs.
Backends, display and OS actions remain injected. Nothing in this module opens
GPIO, unmounts media, drives a LED, or requests host shutdown.
"""
from dataclasses import asdict, dataclass

from .controller import Controller, State
from .backends import validate_sensor_descriptor
from .d2_controls import D2Controls
from .d2_power import D2BatteryPolicy
from .d2_readiness import D2Readiness, evaluate_readiness
from .evf import EvfPolicy, PicameraEvfBackend, MIN_COLOUR_GAIN, MAX_COLOUR_GAIN
from .models import TakeSettings
from .writer import AsyncClipWriter


@dataclass(frozen=True)
class D2Status:
    phase: str
    selected_fps: int | None
    selected_gain: float | None
    active_fps: int | None
    active_gain: float | None
    settings_pending: bool
    battery_millivolts: int | None
    battery_percent: float | None
    battery_warning: bool
    shutdown_reason: str | None
    failure: str | None
    clip: str | None
    simulation_only: bool
    readiness_state: str
    readiness_reasons: tuple[str, ...]
    hardware_qualified: bool = False

    def to_dict(self):
        return asdict(self)


class D2Runtime:
    """Toggle-record, frozen take settings, release-to-arm, safe session swaps.

    A control change during a take is pending. On durable close, the old
    preview session must acknowledge a full close before a new one is opened.
    No held/queued button starts a new take after warmup, saving, or a fault.
    Input loss and battery loss request the existing drained shutdown path.

    ``capture_safely_drained`` permits the external shutdown coordinator to
    close the store. It does NOT prove media sync/unmount or a halted OS.
    """
    def __init__(self, store, backend_factory, *, now_ns, wb_gains,
                 stop_millivolts=3300, writer_factory=AsyncClipWriter, simulation_only=True, commissioning=None, shutdown_observer=None):
        if type(simulation_only) is not bool:
            raise ValueError('simulation_only must be explicitly boolean')
        if not callable(backend_factory):
            raise ValueError('D2 requires an explicit backend factory')
        # Validate before any backend can acquire hardware or a clip can open.
        from .controls import ControlSelection
        validation = TakeSettings.from_selection(
            ControlSelection(24, 90, 1.0, 'custom', 'raw', 'clean', False), wb_gains)
        if validation.wb_gains is None:
            raise ValueError('D2 requires explicit measured WB gains (label test values in simulation)')
        if any(not MIN_COLOUR_GAIN <= value <= MAX_COLOUR_GAIN for value in validation.wb_gains):
            raise ValueError('D2 WB gains must be calibrated within 0.01..32 for the EVF/post contract')
        self.wb_gains = validation.wb_gains
        self.store, self.backend_factory, self.writer_factory = store, backend_factory, writer_factory
        self.controls = D2Controls()
        self.battery = D2BatteryPolicy(now_ns, stop_millivolts=stop_millivolts)
        self.controller = self.backend = None
        self.selection = self.prepared_selection = None
        self.failure = self.shutdown_reason = None
        self.last_clip = None
        self._started_ns = self._last_ns = now_ns
        self._prepared_ns = None
        self._trigger = self._start_armed = self._changing = False
        self._orphan_backend = None
        self._simulated = simulation_only
        self.readiness = D2Readiness(simulation_only, 'simulation_unqualified' if simulation_only else 'unready',
                                     () if simulation_only else ('health_evidence_missing',), None)
        if shutdown_observer is not None and not callable(shutdown_observer):
            raise ValueError('shutdown_observer must be callable')
        self.shutdown_observer = shutdown_observer
        self.commissioning = commissioning
        self._last_inputs = None
        self._post_prepare_resume = False
        self._release_after_ns = now_ns
        self._was_ready = False
        self._last_health_ns = None
        self._last_health_sample = None

    @property
    def capture_safely_drained(self):
        return (self.shutdown_reason is not None and self._orphan_backend is None
                and self.store.active is None
                and (self.controller is None or self.controller.safe_to_request_poweroff))

    def request_shutdown(self, reason='operator_shutdown'):
        if not isinstance(reason, str) or not reason:
            raise ValueError('shutdown requires a nonempty reason')
        first = self.shutdown_reason is None
        self.shutdown_reason = self.shutdown_reason or reason
        if first and self.shutdown_observer is not None:
            try:
                self.shutdown_observer()
            except Exception as error:
                self.failure = self.failure or f'shutdown_status_failed: {type(error).__name__}: {error}'
        self._trigger = self._start_armed = False

    def report_fault(self, reason, error):
        """Latch a display/adapter failure and request durable draining."""
        self._fail(reason, error)

    def _fail(self, reason, error):
        self.failure = self.failure or f'{reason}: {type(error).__name__}: {error}'
        self.request_shutdown(reason)

    def _prepare(self, now_ns, selection):
        backend = None
        try:
            settings = TakeSettings.from_selection(selection, self.wb_gains)
            backend = self.backend_factory(settings)
            if type(backend.simulated) is not bool:
                raise ValueError('backend must explicitly declare simulation status')
            if self._simulated is not None and backend.simulated != self._simulated:
                raise ValueError('a D2 runtime cannot switch between simulation and physical capture')
            self._simulated = backend.simulated
            descriptor = validate_sensor_descriptor(backend.preflight(settings))
            if descriptor.get('simulated') is not backend.simulated:
                raise ValueError('backend descriptor simulation flag disagrees with runtime')
            self.backend = backend
            self.controller = Controller(self.store, backend, trigger_debounce_ms=1,
                                         wb_gains=self.wb_gains, writer_factory=self.writer_factory,
                                         fault_observer=lambda error: self._fail('recorder_failed', error))
            self.prepared_selection, self._prepared_ns = selection, now_ns
            self._trigger = self._start_armed = False
            self._post_prepare_resume = True
        except Exception as error:
            self._fail('backend_prepare_failed', error)
            if backend is not None:
                try:
                    backend.close()
                except Exception:
                    # Keep ownership. A failed close must never permit poweroff.
                    self._orphan_backend = backend

    def step(self, now_ns, inputs=None, battery_sample=None, *, input_error=None,
             battery_error=None, shutdown_requested=False, health_sample=None):
        if type(now_ns) is not int or now_ns < self._last_ns:
            raise ValueError('D2 runtime clock must be monotonic integer nanoseconds')
        if type(shutdown_requested) is not bool:
            raise ValueError('shutdown_requested must be boolean')
        if (self._post_prepare_resume and now_ns - self._last_ns > self.controls.max_age_ns
                and not self._active() and not self.shutdown_reason):
            self.controls.requalify_after_idle_setup()
            self.battery = D2BatteryPolicy(now_ns, stop_millivolts=self.battery.stop_millivolts)
            self._last_inputs = None
            self._trigger = self._start_armed = False
        self._post_prepare_resume = False
        self._last_ns = now_ns
        if not self._simulated:
            self.readiness = evaluate_readiness(now_ns, health_sample, reserve_bytes=self.store.reserve_bytes,
                                                commissioning=self.commissioning)
            stamp = getattr(health_sample, 'acquired_ns', None)
            if type(stamp) is int and 0 <= stamp <= now_ns:
                if self._last_health_ns is not None and stamp < self._last_health_ns:
                    self.readiness = D2Readiness(False, 'unready', ('runtime_health_reordered',),
                                                  self.readiness.evidence_source)
                elif stamp == self._last_health_ns and health_sample != self._last_health_sample:
                    self.readiness = D2Readiness(False, 'unready', ('runtime_health_duplicate_conflict',),
                                                  self.readiness.evidence_source)
                else:
                    self._last_health_ns = stamp
                    self._last_health_sample = health_sample
            if not self.readiness.ready:
                self._trigger = self._start_armed = False
        control = None
        if not self.shutdown_reason:
            try:
                if input_error is not None:
                    raise RuntimeError(f'input reader failed: {input_error}')
                if inputs is not None:
                    self._last_inputs = inputs
                inputs = self._last_inputs
                if inputs is None:
                    if now_ns - self._started_ns > self.controls.max_age_ns:
                        raise ValueError('D2 controls are missing')
                else:
                    control = self.controls.update(now_ns, inputs)
                    self.selection = control.selection
                    if control.shutdown_requested:
                        self.request_shutdown('power_key_hold')
            except Exception as error:
                self._fail('controls_unavailable', error)
        self.battery.update(now_ns, battery_sample, battery_error)
        if self.battery.shutdown_reason:
            self.request_shutdown(self.battery.shutdown_reason)
        if shutdown_requested:
            self.request_shutdown()
        if self._orphan_backend is not None:
            try:
                self._orphan_backend.close()
                self._orphan_backend = None
            except Exception:
                pass  # retain unsafe ownership; surface failure in status
        if self.shutdown_reason:
            if self.controller is not None:
                self.controller.step(now_ns, None, trigger_pressed=False, shutdown_requested=True)
                self._collect()
            return self.status()

        active_before = self._active()
        warm_now = getattr(self.backend, 'warmed_up', True) if self.backend is not None else False
        current_ready = (warm_now is True and self.selection is not None
                         and self.selection == self.prepared_selection and self.battery.ready and self.readiness.ready)
        if not current_ready or not self._was_ready or active_before:
            # Readiness/saving/session recovery is an acquisition-time boundary.
            # A cached pre-recovery release cannot arm a delayed earlier press.
            self._release_after_ns = now_ns
            self._start_armed = False
        self._was_ready = current_ready and not active_before
        if not current_ready:
            self._start_armed = False
            if not active_before:
                self._trigger = False
        # A press while draining is consumed, never stored for the next take.
        if control is not None and control.run_edge:
            if self._trigger:
                self._trigger = False
            elif (not active_before and self._start_armed and not self._changing
                  and current_ready):
                self._trigger = True
            self._start_armed = False

        if (self.controller is not None and not active_before and not self._trigger
                and self.selection is not None and self.selection != self.prepared_selection):
            self._changing = True
        if self._changing:
            self._start_armed = False
            self.controller.step(now_ns, None, trigger_pressed=False, shutdown_requested=True)
            self._collect()
            if self.shutdown_reason:
                return self.status()
            if self.controller.safe_to_request_poweroff:
                self.controller = self.backend = None
                self.prepared_selection = None
                self._changing = False
            else:
                return self.status()
        if self.controller is None and self.selection is not None and self.battery.ready and self.readiness.ready:
            self._prepare(now_ns, self.selection)
        if self.shutdown_reason:
            return self.status()
        if self.controller is not None:
            warm = getattr(self.backend, 'warmed_up', True)
            if type(warm) is not bool:
                self._fail('backend_warmup_failed', ValueError('warmed_up must be boolean'))
                return self.status()
            if not warm and now_ns - self._prepared_ns >= 10_000_000_000:
                self._fail('backend_warmup_failed', TimeoutError('camera metadata did not settle within 10 seconds'))
                return self.status()
            qualified = (warm and self.selection is not None and self.selection == self.prepared_selection
                         and self.battery.ready and self.readiness.ready)
            selected = self.prepared_selection if active_before or qualified else None
            self.controller.step(now_ns, selected, trigger_pressed=self._trigger)
            self._collect()
            if active_before and not self._active():
                self._trigger = self._start_armed = False
                self._release_after_ns = now_ns
                self._was_ready = False
            elif (not active_before and not self._trigger and qualified and control is not None
                  and control.run_pressed is False and inputs is not None
                  and inputs.acquired_ns >= self._release_after_ns
                  and now_ns - self._prepared_ns >= 1_000_000):
                self._start_armed = True
        return self.status()

    def _active(self):
        return self.store.active is not None or (self.controller is not None and self.controller.state in (
            State.STARTING, State.RECORDING, State.STOPPING))

    def _collect(self):
        if self.controller.last_clip is not None:
            self.last_clip = self.controller.last_clip
        if self.controller.failure:
            self._fail('recorder_failed', RuntimeError(self.controller.failure))

    def status(self):
        if self.shutdown_reason:
            phase = 'stopped' if self.capture_safely_drained else 'shutting_down'
        elif self._changing:
            phase = 'applying_settings'
        elif self.controller is None:
            phase = 'checking'
        elif self.controller.state == State.READY and self._start_armed:
            phase = 'ready'
        elif self.controller.state in (State.STARTING, State.RECORDING, State.STOPPING):
            phase = {State.STARTING: 'starting', State.RECORDING: 'recording', State.STOPPING: 'saving'}[self.controller.state]
        else:
            phase = 'checking'
        if self.failure and phase == 'stopped':
            phase = 'fault_stopped'
        actual = self.controller.settings if self._active() and self.controller else self.prepared_selection
        battery = self.battery.last_sample
        return D2Status(phase,
                        self.selection.fps if self.selection else None,
                        self.selection.analogue_gain if self.selection else None,
                        actual.fps if actual else None,
                        actual.analogue_gain if actual else None,
                        self.selection != self.prepared_selection,
                        battery.millivolts if battery else None,
                        float(battery.percent) if battery else None,
                        self.battery.warning, self.shutdown_reason, self.failure,
                        str(self.last_clip) if self.last_clip else None,
                        self._simulated, self.readiness.state, self.readiness.reasons)


def picamera_backend_factory(*, display_size=(1024, 768)):
    """Explicit optional live factory; importing it never opens Pi hardware.

    No source-FPS override: D2 uses uniform 54->18 / 48->24 sampling. A fresh
    session for each changed selection fixes the old preview-control lock.
    """
    def create(settings):
        return PicameraEvfBackend(EvfPolicy(settings.fps, display_size=tuple(display_size)))
    return create
