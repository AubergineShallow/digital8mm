# SPDX-License-Identifier: MIT
# Copyright (c) 2026 GS8 contributors
"""Contact mapping, failure detection and debounce tests; no hardware required."""

from dataclasses import FrozenInstanceError, replace
from itertools import product
import unittest

from gs8_camera_evf.controls import ControlError, ControlSelection, Debouncer, decode_contacts


OPEN_DIRECT = {
    "ENC_N": True,
    "LOOK_FILM_N": True,
    "LOOK_PXL_N": True,
    "AUDIO_ON_N": True,
}
# 18 fps / 180 degrees / gain 1x / 5600 K. Bit 7 is left high here.
BASE_A = 0xAE
BASE_B = 0xDF


class ContactDecoderTests(unittest.TestCase):
    def test_known_header_sample(self):
        self.assertEqual(
            decode_contacts(BASE_A, BASE_B, OPEN_DIRECT),
            ControlSelection(18, 180, 1.0, "5600", "raw", "clean", False),
        )

    def test_all_128_absolute_settings_and_bit7_independence(self):
        fps_choices = ((18, 0), (24, 1))
        shutter_choices = ((90, 2), (144, 3), (180, 4), (216, 5))
        gain_choices = ((1.0, "A", 6), (2.0, "B", 0), (4.0, "B", 1), (8.0, "B", 2))
        wb_choices = (("3200", 3), ("4300", 4), ("5600", 5), ("custom", 6))
        count = 0
        for fps, sh, gain, wb in product(
            fps_choices, shutter_choices, gain_choices, wb_choices
        ):
            a = 0x7F & ~(1 << fps[1]) & ~(1 << sh[1])
            b = 0x7F & ~(1 << wb[1])
            if gain[1] == "A":
                a &= ~(1 << gain[2])
            else:
                b &= ~(1 << gain[2])
            expected = ControlSelection(fps[0], sh[0], gain[0], wb[0], "raw", "clean", False)
            for a7, b7 in product((0, 0x80), repeat=2):
                self.assertEqual(decode_contacts(a | a7, b | b7, OPEN_DIRECT), expected)
            count += 1
        self.assertEqual(count, 128)

    def test_every_other_lower_seven_bit_combination_is_rejected(self):
        accepted = 0
        for a, b in product(range(128), repeat=2):
            low_a, low_b = (~a) & 0x7F, (~b) & 0x7F
            counts = (
                (low_a & 0x03).bit_count(),
                (low_a & 0x3C).bit_count(),
                (low_a & 0x40).bit_count() + (low_b & 0x07).bit_count(),
                (low_b & 0x78).bit_count(),
            )
            if counts == (1, 1, 1, 1):
                decode_contacts(a, b, OPEN_DIRECT)
                accepted += 1
            else:
                with self.assertRaises(ControlError):
                    decode_contacts(a, b, OPEN_DIRECT)
        self.assertEqual(accepted, 128)

    def test_gain_transition_between_banks_is_not_a_default_gain(self):
        # Break-before-make: 1x on A6 opens before 2x on B0 closes.
        with self.assertRaisesRegex(ControlError, "GAIN.*0"):
            decode_contacts(BASE_A | 0x40, BASE_B, OPEN_DIRECT)
        # A split snapshot or make-before-break can show both contacts closed.
        with self.assertRaisesRegex(ControlError, "GAIN.*2"):
            decode_contacts(BASE_A, BASE_B & ~0x01, OPEN_DIRECT)
        self.assertEqual(
            decode_contacts(BASE_A | 0x40, BASE_B & ~0x01, OPEN_DIRECT).analogue_gain,
            2.0,
        )

    def test_unplugged_fps_shutter_gain_or_wb_is_invalid(self):
        for a, b, group in (
            (BASE_A | 0x03, BASE_B, "FPS"),
            (BASE_A | 0x3C, BASE_B, "SHUTTER"),
            (BASE_A | 0x40, BASE_B | 0x07, "GAIN"),
            (BASE_A, BASE_B | 0x78, "WB"),
        ):
            with self.subTest(group=group), self.assertRaisesRegex(ControlError, group):
                decode_contacts(a, b, OPEN_DIRECT)
        with self.assertRaises(ControlError):
            decode_contacts(0xFF, 0xFF, OPEN_DIRECT)

    def test_direct_states_and_active_low_polarities(self):
        for enc, film, pxl, audio in product((False, True), repeat=4):
            direct = dict(zip(OPEN_DIRECT, (enc, film, pxl, audio)))
            if not film and not pxl:
                with self.assertRaisesRegex(ControlError, "LOOK"):
                    decode_contacts(BASE_A, BASE_B, direct)
                continue
            actual = decode_contacts(BASE_A, BASE_B, direct)
            self.assertEqual(actual.capture_format, "raw" if enc else "encoded")
            self.assertEqual(actual.look, "film" if not film else "pxl" if not pxl else "clean")
            self.assertEqual(actual.audio, not audio)

    def test_missing_inputs_and_non_boolean_levels_are_rejected(self):
        for name in OPEN_DIRECT:
            missing = dict(OPEN_DIRECT)
            del missing[name]
            with self.subTest(name=name), self.assertRaisesRegex(ControlError, name):
                decode_contacts(BASE_A, BASE_B, missing)
            for value in (0, 1, "high", None):
                malformed = dict(OPEN_DIRECT, **{name: value})
                with self.assertRaises(ControlError):
                    decode_contacts(BASE_A, BASE_B, malformed)

    def test_bad_port_samples_are_rejected(self):
        for value in (-1, 256, True, False, 174.0, "174", None):
            with self.assertRaises(ControlError):
                decode_contacts(value, BASE_B, OPEN_DIRECT)
            with self.assertRaises(ControlError):
                decode_contacts(BASE_A, value, OPEN_DIRECT)
        with self.assertRaises(ControlError):
            decode_contacts(BASE_A, BASE_B, None)

    def test_extra_gpio_values_do_not_affect_selection(self):
        expected = decode_contacts(BASE_A, BASE_B, OPEN_DIRECT)
        self.assertEqual(
            decode_contacts(BASE_A, BASE_B, dict(OPEN_DIRECT, WB_SET_N=False, TRIGGER_N=False)),
            expected,
        )

    def test_selection_is_immutable(self):
        selected = decode_contacts(BASE_A, BASE_B, OPEN_DIRECT)
        with self.assertRaises(FrozenInstanceError):
            selected.fps = 24


class DebouncerTests(unittest.TestCase):
    def setUp(self):
        self.a = decode_contacts(BASE_A, BASE_B, OPEN_DIRECT)
        self.b = replace(self.a, fps=24)

    def test_default_stable_interval_and_nanosecond_boundary(self):
        d = Debouncer()
        self.assertIsNone(d.update(self.a, 1_000_000))
        self.assertIsNone(d.update(self.a, 20_999_999))
        self.assertEqual(d.update(self.a, 21_000_000), self.a)
        self.assertEqual(d.update(self.a, 21_000_000), self.a)

    def test_valid_bounce_restarts_timer_without_returning_old_selection(self):
        d = Debouncer()
        self.assertIsNone(d.update(self.a, 0))
        self.assertEqual(d.update(self.a, 20_000_000), self.a)
        self.assertIsNone(d.update(self.b, 21_000_000))
        self.assertIsNone(d.update(self.a, 25_000_000))
        self.assertIsNone(d.update(self.b, 30_000_000))
        self.assertIsNone(d.update(self.b, 49_999_999))
        self.assertEqual(d.update(self.b, 50_000_000), self.b)

    def test_invalid_sample_immediately_discards_accepted_and_pending_states(self):
        d = Debouncer()
        d.update(self.a, 0)
        self.assertEqual(d.update(self.a, 20_000_000), self.a)
        self.assertIsNone(d.update(None, 21_000_000))
        self.assertIsNone(d.update(None, 40_000_000))
        self.assertIsNone(d.update(self.a, 41_000_000))
        self.assertIsNone(d.update(self.a, 60_999_999))
        self.assertEqual(d.update(self.a, 61_000_000), self.a)
        self.assertIsNone(d.update(self.b, 62_000_000))
        self.assertIsNone(d.update(None, 80_000_000))
        self.assertIsNone(d.update(self.b, 90_000_000))
        self.assertIsNone(d.update(self.b, 109_999_999))
        self.assertEqual(d.update(self.b, 110_000_000), self.b)

    def test_backwards_timestamp_rejection_does_not_mutate_state(self):
        d = Debouncer()
        d.update(self.a, 10_000_000)
        with self.assertRaisesRegex(ControlError, "backwards"):
            d.update(None, 9_000_000)
        self.assertEqual(d.update(self.a, 30_000_000), self.a)

    def test_equal_timestamp_adds_no_time(self):
        d = Debouncer()
        for _ in range(100):
            self.assertIsNone(d.update(self.a, 123))
        self.assertEqual(d.update(self.a, 20_000_123), self.a)

    def test_custom_and_zero_intervals(self):
        d = Debouncer(stable_ms=35)
        self.assertIsNone(d.update(self.a, 0))
        self.assertIsNone(d.update(self.a, 34_999_999))
        self.assertEqual(d.update(self.a, 35_000_000), self.a)
        immediate = Debouncer(stable_ms=0)
        self.assertEqual(immediate.update(self.a, 0), self.a)
        self.assertEqual(immediate.update(self.b, 0), self.b)
        self.assertIsNone(immediate.update(None, 0))

    def test_invalid_timing_and_sample_types(self):
        for value in (-1, True, 1.5, "20", None):
            with self.assertRaises(ControlError):
                Debouncer(stable_ms=value)
        d = Debouncer()
        for value in (-1, True, 1.5, "20", None):
            with self.assertRaises(ControlError):
                d.update(self.a, value)
        with self.assertRaises(ControlError):
            d.update("not a selection", 0)
        self.assertIsNone(d.update(self.a, 0))


if __name__ == "__main__":
    unittest.main()

