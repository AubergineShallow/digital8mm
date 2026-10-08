# SPDX-License-Identifier: MIT
"""Synthetic contact samples; no physical switches or encoder were tested."""
from dataclasses import replace
import unittest

from gs8_camera_evf.d2_controls import D2Controls, D2InputSample
from gs8_camera_evf.d2_power import D2BatteryPolicy, D2BatterySample, D2Shutdown, ShutdownActions, ShutdownPhase

MS = 1_000_000


def sample(ms, **changes):
    return replace(D2InputSample(ms * MS, True, False, 0, True, False), **changes)


class D2ControlsTests(unittest.TestCase):
    def test_physical_switch_mapping_silent_raw_clean_90_degrees(self):
        for high, fps in ((False, 24), (True, 18)):
            c = D2Controls()
            self.assertIsNone(c.update(0, sample(0, fps_high=high)).selection)
            s = c.update(10 * MS, sample(10, fps_high=high)).selection
            self.assertEqual((s.fps, s.shutter_angle, s.look, s.capture_format, s.audio), (fps, 90, 'clean', 'raw', False))

    def test_held_boot_button_never_generates_edge(self):
        c = D2Controls()
        for ms in range(0, 100, 10):
            self.assertFalse(c.update(ms * MS, sample(ms, run_high=False)).run_edge)
        c.update(100 * MS, sample(100))
        c.update(110 * MS, sample(110))
        c.update(120 * MS, sample(120, run_high=False))
        self.assertTrue(c.update(130 * MS, sample(130, run_high=False)).run_edge)
        self.assertFalse(c.update(140 * MS, sample(140, run_high=False)).run_edge)

    def test_bounce_and_cached_samples_do_not_qualify(self):
        c = D2Controls()
        c.update(0, sample(0))
        c.update(10 * MS, sample(10))
        for ms, high in ((11, False), (15, True), (16, False), (22, True), (23, False)):
            self.assertFalse(c.update(ms * MS, sample(ms, run_high=high)).run_edge)
        self.assertFalse(c.update(33 * MS, sample(23, run_high=False)).run_edge)
        self.assertTrue(c.update(33 * MS, sample(33, run_high=False)).run_edge)

    def test_switch_bounce_inhibits_and_gain_clamps_and_resets(self):
        c = D2Controls()
        c.update(0, sample(0))
        self.assertEqual(c.update(10 * MS, sample(10, encoder_position=10)).selection.analogue_gain, 8)
        self.assertIsNone(c.update(20 * MS, sample(20, fps_high=True, encoder_position=10)).selection)
        self.assertEqual(c.update(30 * MS, sample(30, fps_high=True, encoder_position=10)).selection.fps, 18)
        c.update(40 * MS, sample(40, fps_high=True, encoder_position=10, encoder_push_high=False))
        self.assertEqual(c.update(50 * MS, sample(50, fps_high=True, encoder_position=10,
                                                encoder_push_high=False)).selection.analogue_gain, 1)

    def test_encoder_wrap_is_one_step_and_large_jump_is_error(self):
        c = D2Controls()
        c.update(0, sample(0, encoder_position=2**31-1))
        self.assertEqual(c.update(10 * MS, sample(10, encoder_position=-(2**31))).selection.analogue_gain, 2)
        with self.assertRaisesRegex(ValueError, 'jumped'):
            c.update(20 * MS, sample(20, encoder_position=0))

    def test_power_requires_release_and_continuous_two_seconds(self):
        c = D2Controls()
        for ms in range(0, 2201, 10):
            self.assertFalse(c.update(ms * MS, sample(ms, power_pressed=True)).shutdown_requested)
        c.update(2210 * MS, sample(2210))
        for ms in range(2220, 4220, 10):
            self.assertFalse(c.update(ms * MS, sample(ms, power_pressed=True)).shutdown_requested)
        self.assertTrue(c.update(4220 * MS, sample(4220, power_pressed=True)).shutdown_requested)
        self.assertTrue(c.update(4230 * MS, sample(4230)).shutdown_requested)

    def test_short_power_press_and_autorepeat_equivalent_do_not_accumulate(self):
        c = D2Controls()
        for ms in range(0, 5000, 10):
            self.assertFalse(c.update(ms * MS, sample(ms, power_pressed=(ms % 1000 > 0))).shutdown_requested)

    def test_invalid_samples_fail_closed(self):
        bad = [sample(0, run_high=1), sample(0, encoder_position=True), sample(0, acquired_ns=-1),
               sample(0, encoder_position=2**31), sample(0, fps_high=None), sample(0, acquired_ns=1)]
        for value in bad:
            with self.subTest(value=value), self.assertRaises(ValueError):
                D2Controls().update(0, value)
        c = D2Controls()
        c.update(0, sample(0))
        with self.assertRaisesRegex(ValueError, 'gap'):
            c.update(101 * MS, sample(101))
        with self.assertRaisesRegex(ValueError, 'stale'):
            c.update(101 * MS, sample(0))


class D2BatteryTests(unittest.TestCase):
    def test_fresh_1s_qualifies_and_threshold_latches_immediately(self):
        p = D2BatteryPolicy(0)
        for ms in range(0, 1000, 100):
            p.update(ms * MS, D2BatterySample(ms * MS, 3900, 72.5))
            self.assertFalse(p.ready)
        p.update(1000 * MS, D2BatterySample(1000 * MS, 3900, 72.5))
        self.assertTrue(p.ready)
        p.update(1100 * MS, D2BatterySample(1100 * MS, 3300, 15))
        self.assertEqual(p.shutdown_reason, 'battery_low_voltage')
        p.update(1200 * MS, D2BatterySample(1200 * MS, 4100, 99))
        self.assertFalse(p.ready)

    def test_repeated_sample_cannot_qualify_or_hide_staleness(self):
        p = D2BatteryPolicy(0)
        s = D2BatterySample(0, 3900, 50)
        for ms in range(0, 501, 100):
            p.update(ms * MS, s)
            self.assertFalse(p.ready)
        p.update(501 * MS, s)
        self.assertEqual(p.shutdown_reason, 'battery_telemetry_stale_or_reordered')

    def test_absent_error_implausible_and_3s_samples_stop(self):
        for value in (float('nan'), float('inf'), -1, 101, True):
            p = D2BatteryPolicy(0)
            p.update(0, D2BatterySample(0, 3900, value))
            self.assertEqual(p.shutdown_reason, 'battery_telemetry_implausible')
        p = D2BatteryPolicy(0)
        p.update(0, D2BatterySample(0, 11100, 80))
        self.assertFalse(p.ready)
        self.assertIsNotNone(p.shutdown_reason)
        p = D2BatteryPolicy(0)
        p.update(501 * MS)
        self.assertEqual(p.shutdown_reason, 'battery_telemetry_missing')
        p = D2BatteryPolicy(0)
        p.update(0, error='I2C')
        self.assertEqual(p.shutdown_reason, 'battery_read_error')

    def test_voltage_warning_has_hysteresis(self):
        p = D2BatteryPolicy(0)
        for ms, voltage, warning in ((0, 3500, True), (100, 3550, True), (200, 3600, False)):
            p.update(ms * MS, D2BatterySample(ms * MS, voltage, 25))
            self.assertEqual(p.warning, warning)


class ShutdownTests(unittest.TestCase):
    def make_shutdown(self, fail=None):
        calls = []
        def action(name):
            def call():
                calls.append(name)
                if name == fail:
                    raise OSError('injected failure')
            return call
        names = ('hold_screen', 'close_store', 'sync_media', 'unmount_media', 'request_poweroff')
        return D2Shutdown(ShutdownActions(*(action(n) for n in names))), calls, names

    def test_hold_screen_then_wait_for_durable_capture_then_ordered_shutdown_once(self):
        s, calls, names = self.make_shutdown()
        s.advance(capture_safely_drained=True)
        self.assertEqual(calls, [])
        s.begin()
        s.begin()
        s.advance(capture_safely_drained=False)
        self.assertEqual(calls, ['hold_screen'])
        self.assertEqual(s.advance(capture_safely_drained=True), ShutdownPhase.POWEROFF_REQUESTED)
        s.advance(capture_safely_drained=True)
        self.assertEqual(calls, list(names))

    def test_any_failed_stage_blocks_remaining_actions_and_retry(self):
        for fail in ('hold_screen', 'close_store', 'sync_media', 'unmount_media', 'request_poweroff'):
            with self.subTest(fail=fail):
                s, calls, names = self.make_shutdown(fail)
                s.begin()
                s.advance(capture_safely_drained=True)
                s.advance(capture_safely_drained=True)
                self.assertEqual(s.phase, ShutdownPhase.FAILED)
                self.assertEqual(calls, list(names[:names.index(fail)+1]))

    def test_truthy_drain_is_not_explicit_confirmation(self):
        s, _, _ = self.make_shutdown()
        with self.assertRaises(ValueError):
            s.advance(capture_safely_drained=1)
