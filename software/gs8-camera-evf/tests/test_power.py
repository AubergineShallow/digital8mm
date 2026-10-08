# SPDX-License-Identifier: MIT
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
from types import SimpleNamespace
import time
import unittest
from unittest.mock import Mock, patch

from gs8_camera_evf import hardware_cli
from gs8_camera_evf.power import (BatteryGuard, BatteryPolicy, BatterySample,
                                 Ina260Hwmon, request_os_poweroff, step_with_battery)

MS = 1_000_000


class PowerTests(unittest.TestCase):
    def sample(self, policy, ms, voltage=11400):
        policy.update(ms * MS, BatterySample(ms * MS, voltage, 2500))

    def test_full_3s_pack_is_accepted_and_old_2s_is_rejected(self):
        policy = BatteryPolicy(0)
        for ms in range(0, 1100, 100):
            self.sample(policy, ms, 13050)
        self.assertTrue(policy.ready)
        self.assertIsNone(policy.shutdown_reason)
        policy = BatteryPolicy(0)
        self.sample(policy, 0, 8400)
        self.assertEqual(policy.shutdown_reason, 'battery_critical_voltage')

    def test_unqualified_battery_inhibits_new_take(self):
        from test_controller import camera, BASE
        with camera() as (controller, backend, store):
            policy = BatteryPolicy(0)
            for ms, pressed in [(0, False), (25, False), (50, True), (75, True)]:
                step_with_battery(controller, ms * MS, BASE, trigger_pressed=pressed, policy=policy)
            self.assertIsNone(store.active)
            self.assertEqual(backend.starts, [])

    def test_requires_continuous_start_voltage_and_new_samples(self):
        policy = BatteryPolicy(0)
        for ms in range(0, 1000, 100):
            self.sample(policy, ms)
            self.assertFalse(policy.ready)
        self.sample(policy, 1000)
        self.assertTrue(policy.ready)
        policy = BatteryPolicy(0)
        self.sample(policy, 0)
        policy.update(500 * MS, BatterySample(0, 11400, 2500))
        self.assertFalse(policy.ready)
        policy.update(501 * MS, BatterySample(0, 11400, 2500))
        self.assertEqual(policy.shutdown_reason, 'battery_monitor_stale_or_reordered')

    def test_low_voltage_dwell_resets_but_latched_stop_does_not(self):
        policy = BatteryPolicy(0)
        for ms in range(0, 900, 100):
            self.sample(policy, ms, 10490)
        self.assertIsNone(policy.shutdown_reason)
        self.sample(policy, 900, 10800)
        for ms in range(1000, 2000, 100):
            self.sample(policy, ms, 10500)
        self.assertIsNone(policy.shutdown_reason)
        self.sample(policy, 2000, 10500)
        self.assertEqual(policy.shutdown_reason, 'battery_low_voltage')
        self.sample(policy, 2100, 13050)
        self.assertEqual(policy.shutdown_reason, 'battery_low_voltage')
        self.assertFalse(policy.ready)

    def test_critical_voltage_and_warning_hysteresis(self):
        policy = BatteryPolicy(0)
        for ms, voltage, warning in [(0, 10800, True), (100, 10950, True), (200, 11100, False)]:
            self.sample(policy, ms, voltage)
            self.assertEqual(policy.warning, warning)
        self.sample(policy, 300, 10200)
        self.assertEqual(policy.shutdown_reason, 'battery_critical_voltage')

    def test_missing_error_future_reordered_and_implausible_samples(self):
        scenarios = [
            (501 * MS, None, None), (100 * MS, None, 'OSError'),
            (100 * MS, BatterySample(101 * MS, 11400, 0), None),
            (100 * MS, BatterySample(100 * MS, 14000, 0), None),
            (100 * MS, BatterySample(100 * MS, float('nan'), 0), None),
            (100 * MS, BatterySample(100 * MS, 11400, -500), None),
        ]
        for now, sample, error in scenarios:
            with self.subTest(now=now, sample=sample, error=error):
                policy = BatteryPolicy(0)
                policy.update(now, sample, error)
                self.assertIsNotNone(policy.shutdown_reason)
        policy = BatteryPolicy(0)
        self.sample(policy, 100)
        policy.update(200 * MS, BatterySample(50 * MS, 11400, 0))
        self.assertIsNotNone(policy.shutdown_reason)
        policy = BatteryPolicy(0)
        self.sample(policy, 100)
        self.sample(policy, 99)
        self.assertEqual(policy.shutdown_reason, 'monitor_clock_regression')

    def test_missing_samples_cannot_accumulate_dwell(self):
        policy = BatteryPolicy(0)
        self.sample(policy, 0, 10350)
        self.sample(policy, 1000, 10350)
        self.assertEqual(policy.shutdown_reason, 'battery_monitor_gap')

    def test_hwmon_identity_units_and_slow_conversion_rejected(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            values = {'name': 'ina260', 'update_interval': '35',
                      'in1_input': '11380', 'curr1_input': '2300'}
            for name, value in values.items():
                (root / name).write_text(value)
            sample = Ina260Hwmon(root).read()
            self.assertEqual((sample.millivolts, sample.milliamps), (11380, 2300))
            (root / 'update_interval').write_text('2253')
            with self.assertRaises(ValueError):
                Ina260Hwmon(root).read()
            (root / 'name').write_text('ina219')
            with self.assertRaises(ValueError):
                Ina260Hwmon(root).read()

    def test_blocked_reader_does_not_block_stop_decision(self):
        release = Event()
        reader = Mock()
        reader.read.side_effect = lambda: (release.wait(5), BatterySample(time.monotonic_ns(), 11400, 0))[1]
        guard = BatteryGuard(reader)
        try:
            guard.policy.started_ns -= 600 * MS
            self.assertEqual(guard.poll().shutdown_reason, 'battery_monitor_missing')
        finally:
            release.set()
            guard.close()

    def test_poweroff_refuses_unconfirmed_drain_and_uses_no_force(self):
        runner = Mock()
        for value in (False, None, 1):
            with self.assertRaises(RuntimeError):
                request_os_poweroff(safe_to_poweroff=value, runner=runner)
        runner.assert_not_called()
        request_os_poweroff(safe_to_poweroff=True, runner=runner)
        runner.assert_called_once_with(['systemctl', 'poweroff'], check=True, timeout=10)

    def invoke_wrapper(self, safe=True, reason='battery_low_voltage', enabled=True, error=None):
        guard = Mock()
        guard.policy.shutdown_reason = reason
        args = SimpleNamespace(battery_hwmon=Path('/sys/devices/mock'), battery_poweroff=enabled)
        events = []
        guard.close.side_effect = lambda: events.append('monitor_closed')
        def inner(*args):
            events.append('capture_cleanup')
            if error:
                raise error
            return 0, safe
        with patch.object(Path, 'resolve', return_value=args.battery_hwmon), \
             patch.object(hardware_cli, 'BatteryGuard', return_value=guard), \
             patch.object(hardware_cli, '_run', side_effect=inner), \
             patch.object(hardware_cli, 'request_os_poweroff') as poweroff:
            poweroff.side_effect = lambda **kwargs: (events.append('os_request'),
                request_os_poweroff(**kwargs, runner=Mock()))
            if error:
                with self.assertRaises(type(error)):
                    hardware_cli.run(args)
                poweroff.assert_not_called()
            elif not safe and enabled and reason:
                with self.assertRaises(RuntimeError):
                    hardware_cli.run(args)
            else:
                hardware_cli.run(args)
                self.assertEqual(poweroff.called, bool(reason and enabled))
        self.assertEqual(events[:2], ['capture_cleanup', 'monitor_closed'])
        return events

    def test_cli_requests_os_halt_only_after_successful_cleanup(self):
        self.assertEqual(self.invoke_wrapper(), ['capture_cleanup', 'monitor_closed', 'os_request'])
        self.invoke_wrapper(error=RuntimeError('backend close failed'))
        self.invoke_wrapper(safe=False)
        self.invoke_wrapper(reason=None)
        self.invoke_wrapper(enabled=False)

    def test_cli_requires_monitor_for_poweroff(self):
        with self.assertRaises(ValueError):
            hardware_cli.run(SimpleNamespace(battery_hwmon=None, battery_poweroff=True))

    def test_low_battery_waits_for_real_controller_drain_and_commit(self):
        from test_controller import camera, start_take, first_frame, tick, saved_manifest
        with camera() as (controller, backend, store):
            start_take(controller)
            first_frame(controller, backend)
            policy = BatteryPolicy(100 * MS)
            self.sample(policy, 120, 10200)
            from test_controller import BASE
            step_with_battery(controller, 120 * MS, BASE, trigger_pressed=False, policy=policy)
            self.assertFalse(controller.safe_to_request_poweroff)
            runner = Mock()
            with self.assertRaises(RuntimeError):
                request_os_poweroff(safe_to_poweroff=controller.safe_to_request_poweroff, runner=runner)
            runner.assert_not_called()
            backend.drain_ack = True
            tick(controller, 140, False, shutdown=True)
            self.assertTrue(controller.safe_to_request_poweroff)
            self.assertEqual(saved_manifest(controller)['status'], 'complete')
            self.assertTrue((controller.last_clip / 'commit.json').is_file())


if __name__ == '__main__':
    unittest.main()
