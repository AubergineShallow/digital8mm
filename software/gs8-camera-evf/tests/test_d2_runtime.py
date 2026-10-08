# SPDX-License-Identifier: MIT
"""D2 synthetic controls drive the real recorder/store lifecycle, no hardware."""
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from gs8_camera_evf.backends import SimulationBackend
from gs8_camera_evf.d2_controls import D2InputSample
from gs8_camera_evf.d2_power import D2BatterySample
from gs8_camera_evf.d2_runtime import D2Runtime
from gs8_camera_evf.storage import ClipStore, StorageError
from gs8_camera_evf.writer import InlineClipWriter

MS = 1_000_000


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory(prefix='gs8-d2-test-')
        self.store = ClipStore(Path(self.tmp.name), reserve_bytes=0)
        self.backends = []
        self.factory = self.make_backend
        self.runtime = D2Runtime(self.store, lambda settings: self.factory(settings), now_ns=0,
                                 wb_gains=(1.5, 1.25), writer_factory=InlineClipWriter)
        self.ms = -10
        self.inputs = D2InputSample(0, True, False, 0, True, False)
        self.voltage = 3900

    def tearDown(self):
        if self.runtime.backend is not None:
            self.runtime.backend.close()
        if self.store.active is not None:
            self.store.active.abandon()
        self.store.close()
        self.tmp.cleanup()

    def make_backend(self, settings):
        result = SimulationBackend()
        self.backends.append(result)
        return result

    def step(self, **changes):
        self.ms += 10
        self.inputs = replace(self.inputs, acquired_ns=self.ms * MS, **changes)
        return self.runtime.step(self.ms * MS, self.inputs, D2BatterySample(self.ms * MS, self.voltage, 80))

    def ticks(self, count, **changes):
        for _ in range(count):
            status = self.step(**changes)
        return status

    def ready(self):
        self.ticks(110)
        self.assertEqual(self.runtime.status().phase, 'ready')

    def press(self):
        self.ticks(3, run_high=False)

    def release(self):
        self.ticks(3, run_high=True)

    def start(self):
        self.press()
        self.release()
        self.ticks(10)
        self.assertEqual(self.runtime.status().phase, 'recording')

    def test_two_toggle_takes_release_does_not_stop(self):
        self.ready()
        for _ in range(2):
            self.start()
            self.press()
            self.assertEqual(self.runtime.status().phase, 'saving')
            self.release()
            self.ticks(20)
            self.assertEqual(self.runtime.status().phase, 'ready')
        manifests = list(Path(self.tmp.name).glob('*/manifest.json'))
        self.assertEqual(len(manifests), 2)
        for path in manifests:
            data = json.loads(path.read_text())
            self.assertEqual(data['status'], 'complete')
            self.assertTrue(data['simulated'])
        self.runtime.request_shutdown()
        self.step()
        self.assertTrue(self.runtime.capture_safely_drained)

    def test_press_held_at_boot_or_during_saving_never_restarts(self):
        self.ticks(120, run_high=False)
        self.assertIsNone(self.store.active)
        self.release()
        self.start()
        self.press()
        self.ticks(30, run_high=False)
        self.assertIsNone(self.store.active)
        self.release()
        self.start()

    def test_switch_and_gain_frozen_during_take_then_new_session(self):
        self.ready()
        self.start()
        self.ticks(4, fps_high=True, encoder_position=2)
        status = self.runtime.status()
        self.assertEqual((status.active_fps, status.active_gain), (24, 1))
        self.assertEqual((status.selected_fps, status.selected_gain, status.settings_pending), (18, 4, True))
        self.assertEqual(len(self.backends), 1)
        self.press()
        self.release()
        self.ticks(25)
        self.assertEqual(len(self.backends), 2)
        self.assertIsNone(self.backends[0].settings)
        self.assertEqual(self.runtime.status().phase, 'ready')
        self.start()
        self.assertEqual((self.runtime.controller.settings.fps, self.runtime.controller.settings.analogue_gain), (18, 4))

    def test_low_battery_uses_durable_drain_and_never_restarts(self):
        self.ready()
        self.start()
        self.voltage = 3300
        self.step()
        self.assertEqual(self.runtime.shutdown_reason, 'battery_low_voltage')
        self.assertFalse(self.runtime.capture_safely_drained)
        self.ticks(20)
        self.assertTrue(self.runtime.capture_safely_drained)
        data = json.loads((self.runtime.last_clip / 'manifest.json').read_text())
        self.assertEqual(data['status'], 'complete')
        self.voltage = 4100
        self.press()
        self.assertIsNone(self.store.active)

    def test_input_read_failure_while_recording_stops_cleanly(self):
        self.ready()
        self.start()
        self.runtime.step((self.ms + 1) * MS, input_error='device disconnected',
                          battery_sample=D2BatterySample((self.ms + 1) * MS, 3900, 80))
        self.ticks(20)
        self.assertTrue(self.runtime.capture_safely_drained)
        self.assertIn('controls_unavailable', self.runtime.failure)
        self.assertEqual(self.runtime.status().phase, 'fault_stopped')

    def test_storage_failure_blocks_new_takes_and_preserves_failed_evidence(self):
        self.ready()
        def failed_begin(*args, **kwargs):
            raise StorageError('injected full media')
        self.store.begin = failed_begin
        self.press()
        self.ticks(20)
        self.assertIsNotNone(self.runtime.failure)
        self.assertIsNone(self.store.active)
        self.assertFalse(self.runtime.capture_safely_drained)

    def test_unacknowledged_drain_never_becomes_safe(self):
        self.ready()
        self.start()
        self.runtime.backend.drained = lambda now: False
        self.runtime.request_shutdown()
        self.ticks(600)
        self.assertFalse(self.runtime.capture_safely_drained)
        self.assertIsNotNone(self.runtime.failure)

    def test_backend_close_failure_keeps_ownership(self):
        class Broken(SimulationBackend):
            def preflight(self, settings):
                raise RuntimeError('preflight failed')
            def close(self):
                raise RuntimeError('close failed')
        self.factory = lambda settings: Broken()
        self.ticks(110)
        self.assertIsNotNone(self.runtime.failure)
        self.assertFalse(self.runtime.capture_safely_drained)

    def test_no_backend_opened_until_battery_and_controls_qualify(self):
        self.ticks(100)
        self.assertEqual(self.backends, [])
        self.ticks(5)
        self.assertEqual(len(self.backends), 1)

    def test_power_key_hold_during_take_uses_same_drain(self):
        self.ready()
        self.start()
        self.ticks(202, power_pressed=True)
        self.assertEqual(self.runtime.shutdown_reason, 'power_key_hold')
        self.ticks(20)
        self.assertTrue(self.runtime.capture_safely_drained)

    def test_runtime_does_not_claim_hardware_qualification(self):
        self.ready()
        status = self.runtime.status().to_dict()
        self.assertTrue(status['simulation_only'])
        self.assertFalse(status['hardware_qualified'])

    def test_invalid_clock_and_shutdown_arguments(self):
        with self.assertRaises(ValueError):
            self.runtime.step(-1)
        with self.assertRaises(ValueError):
            self.runtime.step(0, shutdown_requested=1)

    def test_unready_press_and_pending_virtual_trigger_cannot_be_replayed(self):
        self.ready()
        self.runtime.backend.warmed_up = False
        self.press()
        self.runtime.backend.warmed_up = True
        self.ticks(3, run_high=False)
        self.assertIsNone(self.store.active)
        self.release()
        self.ticks(2, run_high=False)  # contact edge, virtual trigger not yet qualified
        self.runtime.backend.warmed_up = False
        self.step(run_high=False)
        self.runtime.backend.warmed_up = True
        self.ticks(3, run_high=False)
        self.assertIsNone(self.store.active)
        self.release()
        self.start()

    def test_idle_setup_gap_requalifies_without_replaying_held_inputs(self):
        self.ticks(101)  # preparation starts at 1 s
        self.assertTrue(self.runtime._post_prepare_resume)
        self.ms += 200
        status = self.step(run_high=False)
        self.assertIsNone(status.shutdown_reason)
        self.assertFalse(self.runtime.battery.ready)
        self.ticks(110, run_high=False)
        self.assertIsNone(self.store.active)
        self.release()
        self.start()

    def test_missing_sample_uses_last_acquisition_until_stale(self):
        self.ready()
        now = (self.ms + 1) * MS
        self.runtime.step(now, None, D2BatterySample(now, 3900, 80))
        self.assertIsNone(self.runtime.shutdown_reason)
        now = (self.ms + 101) * MS
        self.runtime.step(now, None, D2BatterySample(now, 3900, 80))
        self.assertEqual(self.runtime.shutdown_reason, 'controls_unavailable')

    def test_gap_during_take_is_not_forgiven(self):
        self.ready()
        self.start()
        self.ms += 200
        self.step()
        self.assertEqual(self.runtime.shutdown_reason, 'controls_unavailable')

    def test_session_close_failure_never_opens_second_backend(self):
        self.ready()
        original = self.runtime.backend.close
        def failed_close():
            raise OSError('injected preview close failure')
        self.runtime.backend.close = failed_close
        self.ticks(3, fps_high=True)
        self.assertEqual(len(self.backends), 1)
        self.assertIsNotNone(self.runtime.failure)
        self.assertFalse(self.runtime.capture_safely_drained)
        self.runtime.backend.close = original
        self.ticks(3)
        self.assertTrue(self.runtime.capture_safely_drained)
        self.assertEqual(len(self.backends), 1)

    def test_delayed_durable_writer_keeps_capture_unsafe(self):
        from concurrent.futures import Future
        class DelayedWriter(InlineClipWriter):
            def finish(self, *args):
                self.args = args
                self.later = Future()
                return self.later
            def complete(self):
                actual = super().finish(*self.args)
                self.later.set_result(actual.result())
        self.runtime.writer_factory = DelayedWriter
        self.ready()
        self.start()
        self.runtime.request_shutdown()
        self.ticks(15)
        self.assertFalse(self.runtime.capture_safely_drained)
        self.assertIsNotNone(self.store.active)
        self.runtime.controller._writer.complete()
        self.step()
        self.assertTrue(self.runtime.capture_safely_drained)

    def test_shutdown_screen_hook_precedes_backend_close_once(self):
        self.ready()
        calls = []
        self.runtime.shutdown_observer = lambda: calls.append('screen')
        original = self.runtime.backend.close
        def close():
            calls.append('close')
            original()
        self.runtime.backend.close = close
        self.runtime.request_shutdown()
        self.runtime.request_shutdown()
        self.step()
        self.assertEqual(calls, ['screen', 'close'])

    def test_backend_never_settles_times_out(self):
        self.ready()
        self.runtime.backend.warmed_up = False
        self.ticks(1100)
        self.assertEqual(self.runtime.shutdown_reason, 'backend_warmup_failed')

    def test_physical_mode_missing_readiness_never_opens_camera(self):
        self.runtime = D2Runtime(self.store, self.make_backend, now_ns=0, wb_gains=(1.5, 1.25),
                                 simulation_only=False, writer_factory=InlineClipWriter)
        self.ticks(120)
        self.assertEqual(self.backends, [])
        self.assertFalse(self.runtime.status().simulation_only)
        self.assertEqual(self.runtime.status().readiness_state, 'unready')
        self.assertIn('commissioning_evidence_missing_or_unverified', self.runtime.status().readiness_reasons)
        self.assertIsNone(self.runtime.shutdown_reason)

    def test_readiness_loss_drains_without_forcing_os_shutdown_or_restart(self):
        from gs8_camera_evf.backends import SIMULATION_SENSOR
        from gs8_camera_evf.d2_readiness import D2Commissioning, D2HealthSample
        class SyntheticPhysicalSchema(SimulationBackend):
            # Schema fixture only. It emits no pixels before the zero-frame take
            # is cancelled. No physical capture or qualified evidence is claimed.
            simulated = False
            def preflight(self, settings):
                return {**SIMULATION_SENSOR, 'simulated': False, 'synthetic_test_only': True}
        self.runtime = D2Runtime(self.store, lambda settings: SyntheticPhysicalSchema(), now_ns=0,
                                 wb_gains=(1.5, 1.25), simulation_only=False, writer_factory=InlineClipWriter,
                                 commissioning=D2Commissioning('synthetic-test-only', True, True))
        def physical_tick(ms, high, valid=True):
            self.ms = ms
            return self.runtime.step(ms * MS, D2InputSample(ms * MS, high, False, 0, True, False),
                                     D2BatterySample(ms * MS, 3900, 80),
                                     health_sample=D2HealthSample(ms * MS, 50, 0, 0, True, 10_000) if valid else None)
        for ms in range(0, 1100, 10):
            physical_tick(ms, True)
        physical_tick(1100, False)
        physical_tick(1110, False)
        physical_tick(1120, False)
        self.assertIsNotNone(self.store.active)
        physical_tick(1130, False, False)
        for ms in range(1140, 1400, 10):
            physical_tick(ms, False, False)
        self.assertIsNone(self.store.active)
        self.assertIsNone(self.runtime.shutdown_reason)
        self.assertFalse(self.runtime.capture_safely_drained)  # not an OS-shutdown authorization
        physical_tick(1400, False, True)
        physical_tick(1410, False, True)
        self.assertIsNone(self.store.active)  # held button never replays after readiness returns

    def test_fault_shutdown_screen_precedes_preview_close(self):
        self.ready()
        calls = []
        self.runtime.shutdown_observer = lambda: calls.append('screen')
        def failed_health():
            raise RuntimeError('injected preview fault')
        original = self.runtime.backend.close
        def close():
            calls.append('close')
            original()
        self.runtime.backend.check_health = failed_health
        self.runtime.backend.close = close
        self.step()
        self.assertEqual(calls[:2], ['screen', 'close'])
        self.assertIsNotNone(self.runtime.failure)

    def test_actual_picamera_adapter_reopens_idle_session_for_physical_switch(self):
        from test_evf import FakeCamera, preview
        from gs8_camera_evf.d2_readiness import D2Commissioning, D2HealthSample
        from gs8_camera_evf.evf import EvfPolicy, PicameraEvfBackend
        cameras = []
        owned = []
        clock = [0]
        def factory(settings):
            if cameras:
                self.assertTrue(cameras[-1].closed, 'old camera must close before opening another')
            camera = FakeCamera()
            cameras.append(camera)
            backend = PicameraEvfBackend(EvfPolicy(settings.fps), camera_factory=lambda: camera,
                                         preview_factory=preview, clock_ns=lambda: clock[0])
            owned.append(backend)
            return backend
        self.runtime = D2Runtime(self.store, factory, now_ns=0, wb_gains=(1.5, 1.25),
                                 simulation_only=False, commissioning=D2Commissioning('synthetic-test-only', True, True),
                                 writer_factory=InlineClipWriter)
        try:
            for ms in range(0, 1150, 10):
                clock[0] = ms * MS
                if cameras and cameras[-1].started:
                    for _ in range(60):
                        cameras[-1].frame()  # fake metadata only; no recording enabled
                self.runtime.step(ms * MS, D2InputSample(ms * MS, True, ms >= 1100, 0, True, False),
                                  D2BatterySample(ms * MS, 3900, 80),
                                  health_sample=D2HealthSample(ms * MS, 50, 0, 0, True, 10_000))
            self.assertEqual(len(cameras), 2)
            self.assertTrue(cameras[0].closed)
            self.assertFalse(cameras[1].closed)
            self.assertEqual(self.runtime.prepared_selection.fps, 18)
            self.assertEqual(cameras[1].config['controls']['FrameDurationLimits'], (18519, 18519))
            self.assertEqual(self.runtime.status().phase, 'ready')
        finally:
            for backend in owned:
                backend.close()

    def test_delayed_unready_press_requires_post_epoch_release(self):
        self.ready()
        self.runtime.backend.warmed_up = False
        self.step()
        released = self.inputs
        self.runtime.backend.warmed_up = True
        for now, acquired, high in ((1120, 1100, True), (1130, 1110, False),
                                     (1140, 1120, False), (1150, 1130, False)):
            status = self.runtime.step(now * MS, replace(released, acquired_ns=acquired * MS, run_high=high),
                                       D2BatterySample(now * MS, 3900, 80))
            self.assertIsNone(self.store.active)
            self.assertFalse(self.runtime._start_armed)
        self.ms = 1150
        self.inputs = replace(released, acquired_ns=1130 * MS, run_high=False)
        self.release()
        self.start()

    def test_cached_release_cannot_arm_after_drain_or_session_replacement(self):
        for change_session in (False, True):
            with self.subTest(change_session=change_session):
                # Each scenario uses a fresh store/runtime so no internal reset
                # can hide a previously consumed or queued press.
                with TemporaryDirectory() as tmp:
                    with ClipStore(Path(tmp), reserve_bytes=0) as store:
                        runtime = D2Runtime(store, lambda settings: SimulationBackend(), now_ns=0,
                                            wb_gains=(1.5, 1.25), writer_factory=InlineClipWriter)
                        def tick(now, acquired=None, high=True, fps_high=False):
                            acquired = now if acquired is None else acquired
                            return runtime.step(now * MS, D2InputSample(acquired * MS, high, fps_high, 0, True, False),
                                                D2BatterySample(now * MS, 3900, 80))
                        for ms in range(0, 1100, 10):
                            tick(ms)
                        for ms in range(1100, 1140, 10):
                            tick(ms, high=False)
                        for ms in range(1140, 1320, 10):
                            tick(ms, fps_high=change_session)
                        for ms in range(1320, 1360, 10):
                            tick(ms, high=False, fps_high=change_session)
                        # Released during saving, then only cached releases are
                        # delivered across durable completion/session change.
                        tick(1360, fps_high=change_session)
                        tick(1370, fps_high=change_session)
                        for ms in range(1380, 1450, 10):
                            tick(ms, acquired=1370, fps_high=change_session)
                        self.assertIsNone(store.active)
                        self.assertFalse(runtime._start_armed)
                        for now, acquired in ((1450, 1380), (1460, 1390), (1470, 1400)):
                            tick(now, acquired=acquired, high=False, fps_high=change_session)
                            self.assertIsNone(store.active)
                        runtime.request_shutdown()
                        tick(1480, fps_high=change_session)

    def test_older_healthy_runtime_sample_cannot_erase_newer_overheat(self):
        from gs8_camera_evf.d2_readiness import D2Commissioning, D2HealthSample
        self.runtime = D2Runtime(self.store, self.make_backend, now_ns=0, wb_gains=(1.5, 1.25),
                                 simulation_only=False, commissioning=D2Commissioning('test-only', True, True))
        self.runtime.step(100 * MS, D2InputSample(100 * MS, True, False, 0, True, False),
                          D2BatterySample(100 * MS, 3900, 80),
                          health_sample=D2HealthSample(100 * MS, 85, 0, 0, True, 10_000))
        self.runtime.step(110 * MS, D2InputSample(110 * MS, True, False, 0, True, False),
                          D2BatterySample(110 * MS, 3900, 80),
                          health_sample=D2HealthSample(90 * MS, 50, 0, 0, True, 10_000))
        self.assertFalse(self.runtime.readiness.ready)
        self.assertIn('runtime_health_reordered', self.runtime.readiness.reasons)

    def test_direct_runtime_rejects_post_incompatible_white_balance(self):
        with self.assertRaisesRegex(ValueError, '0.01..32'):
            D2Runtime(self.store, self.make_backend, now_ns=0, wb_gains=(33, 1.25))

    def test_duplicate_acquisition_cannot_replace_adverse_health_contents(self):
        from gs8_camera_evf.d2_readiness import D2Commissioning, D2HealthSample
        self.runtime = D2Runtime(self.store, self.make_backend, now_ns=0, wb_gains=(1.5, 1.25),
                                 simulation_only=False, commissioning=D2Commissioning('test-only', True, True))
        for now, temperature in ((100, 85), (110, 50)):
            self.runtime.step(now * MS, D2InputSample(now * MS, True, False, 0, True, False),
                              D2BatterySample(now * MS, 3900, 80),
                              health_sample=D2HealthSample(100 * MS, temperature, 0, 0, True, 10_000))
        self.assertFalse(self.runtime.readiness.ready)
        self.assertIn('runtime_health_duplicate_conflict', self.runtime.readiness.reasons)
        self.runtime.step(120 * MS, D2InputSample(120 * MS, True, False, 0, True, False),
                          D2BatterySample(120 * MS, 3900, 80),
                          health_sample=D2HealthSample(120 * MS, 50, 0, 0, True, 10_000))
        self.assertTrue(self.runtime.readiness.ready)
