# SPDX-License-Identifier: MIT
"""Host pixel/layout regressions, not hardware or eyepiece qualification."""
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import itertools
import subprocess
import sys
import unittest
from gs8_camera_evf.d2_presentation import (
    AMBER, BLACK, CANVAS_SIZE, FONT, HEADER_HEIGHT, FOOTER_HEIGHT, MUTED, RED, WHITE,
    Label, Rect, present_shutdown, present_status, preview_rect, rasterize, text_width, validate_layout)
from gs8_camera_evf.d2_runtime import D2Status

BASE = D2Status('ready', 24, 1.0, 24, 1.0, False, 3920, 76, False, None, None,
                None, True, 'simulation_unqualified', ())
PHASES = ('checking', 'ready', 'starting', 'recording', 'saving', 'applying_settings',
          'shutting_down', 'stopped', 'fault_stopped')
REASONS = ('commissioning_evidence_missing_or_unverified', 'runtime_health_invalid_or_stale',
           'soc_temperature_c_outside_limit', 'throttled_bits_outside_limit', 'usb_resets_outside_limit',
           'media_writable_outside_limit', 'free_bytes_outside_limit', 'unknown_' + 'X' * 4000)


def label(view, key):
    return next(item for item in view.labels if item.key == key)


class PresentationStateTests(unittest.TestCase):
    def test_phases_are_distinct_without_colour(self):
        expected = ('CHECKING', 'READY', 'STARTING', 'REC', 'SAVING', 'APPLYING',
                    'SHUTTING DOWN', 'CAPTURE STOPPED', 'FAULT STOPPED')
        for phase, title in zip(PHASES, expected):
            view = present_status(replace(BASE, phase=phase))
            self.assertEqual(label(view, 'phase').text, title)
            self.assertIn('SIMULATION', view.text)
            self.assertIn('UNQUALIFIED', view.text)

    def test_recording_active_and_next_values_never_swap(self):
        view = present_status(replace(BASE, phase='recording', selected_fps=18,
                                      selected_gain=4, active_gain=2, settings_pending=True))
        self.assertEqual(label(view, 'phase').text, 'REC')
        self.assertEqual(label(view, 'active_settings').text, 'ACTIVE 24 FPS  GAIN 2X')
        self.assertEqual(label(view, 'pending_settings').text, 'NEXT 18 FPS  GAIN 4X')
        self.assertIn('PRESS RUN TO STOP', view.text)
        self.assertIsNotNone(view.preview_rect)

    def test_all_phases_fps_and_gain_combinations_fit(self):
        for phase, fps, selected, gain, selected_gain in itertools.product(
                PHASES, (18, 24), (18, 24), (1, 2, 4, 8), (1, 2, 4, 8)):
            with self.subTest(phase=phase, fps=fps, selected=selected, gain=gain, next_gain=selected_gain):
                view = present_status(replace(BASE, phase=phase, active_fps=fps, selected_fps=selected,
                                              active_gain=gain, selected_gain=selected_gain, settings_pending=True))
                validate_layout(view)
                self.assertIn(f'ACTIVE {fps} FPS  GAIN {gain}X', view.text)
                self.assertIn(f'NEXT {selected} FPS  GAIN {selected_gain}X', view.text)

    def test_no_pending_label_without_pending_change(self):
        view = present_status(BASE)
        self.assertNotIn('NEXT', view.text)
        self.assertEqual(label(view, 'action').text, 'PRESS RUN TO RECORD')

    def test_unresolved_pending_selector_keeps_valid_active_preview(self):
        for phase, fps, gain, warning in itertools.product(
                ('starting', 'recording', 'saving'), (18, 24), (1, 2, 4, 8), (False, True)):
            with self.subTest(phase=phase, fps=fps, gain=gain, warning=warning):
                view = present_status(replace(BASE, phase=phase, active_fps=fps, active_gain=gain,
                                              selected_fps=None, selected_gain=None, settings_pending=True,
                                              battery_warning=warning))
                self.assertEqual(view.preview_rect, preview_rect())
                self.assertIn(f'ACTIVE {fps} FPS  GAIN {gain}X', view.text)
                self.assertIn('NEXT -- FPS  GAIN --', view.text)
                self.assertNotIn('settings_unknown', view.notice_codes)
                self.assertNotIn('CHECK READINESS', view.text)
                self.assertNotIn('RELEASE RUN', view.text)
                if warning:
                    self.assertIn('LOW CELL', view.text)
                validate_layout(view)

    def test_unresolved_selector_is_not_an_exception_outside_an_active_take(self):
        for phase in ('checking', 'ready', 'applying_settings', 'shutting_down', 'stopped', 'fault_stopped'):
            view = present_status(replace(BASE, phase=phase, selected_fps=None, selected_gain=None,
                                          settings_pending=True))
            self.assertIsNone(view.preview_rect)
            self.assertIn('SETTINGS UNKNOWN', view.text)
            self.assertNotEqual(label(view, 'phase').text, 'READY')

    def test_partial_or_malformed_pending_values_still_require_attention(self):
        for fps, gain in ((None, 1), (18, None), ('18', None), (None, False), (0, 1), (18, 0),
                          (30, 4), (18, float('nan')), (True, None), (None, 'pending')):
            view = present_status(replace(BASE, phase='recording', selected_fps=fps,
                                          selected_gain=gain, settings_pending=True))
            self.assertIsNone(view.preview_rect)
            self.assertIn('SETTINGS UNKNOWN', view.text)

    def test_pending_selector_never_excuses_invalid_active_values(self):
        for field, value in (('active_fps', None), ('active_fps', True), ('active_fps', 30),
                             ('active_gain', None), ('active_gain', False), ('active_gain', 3),
                             ('active_gain', float('inf'))):
            view = present_status(replace(BASE, phase='recording', selected_fps=None, selected_gain=None,
                                          settings_pending=True, **{field: value}))
            self.assertIsNone(view.preview_rect)
            self.assertIn('SETTINGS UNKNOWN', view.text)

    def test_pending_selector_requires_explicit_pending_flag(self):
        for pending in (False, 0, 1, None, 'true'):
            view = present_status(replace(BASE, phase='recording', selected_fps=None,
                                          selected_gain=None, settings_pending=pending))
            self.assertIsNone(view.preview_rect)
            self.assertIn('SETTINGS UNKNOWN', view.text)

    def test_pending_selector_never_hides_fault_battery_or_readiness_failures(self):
        changes = (
            ({'shutdown_reason': 'controls_unavailable'}, 'INPUT LOST'),
            ({'failure': 'controls_unavailable: input reader failed'}, 'INPUT LOST'),
            ({'failure': 'recorder_failed: storage failure'}, 'FAULT'),
            ({'shutdown_reason': 'battery_telemetry_stale_or_reordered'}, 'BATTERY DATA LOST'),
            ({'shutdown_reason': 'battery_low_voltage'}, 'LOW CELL'),
            ({'battery_millivolts': None}, 'BATTERY UNKNOWN'),
            ({'battery_percent': None}, 'BATTERY UNKNOWN'),
            ({'readiness_state': 'degraded', 'readiness_reasons': ('media_writable_outside_limit',)}, 'NOT READY'),
            ({'readiness_state': 'unready'}, 'NOT READY'),
            ({'readiness_reasons': ('runtime_health_invalid_or_stale',)}, 'HEALTH DATA'),
            ({'failure': 1}, 'STATUS INVALID'),
            ({'hardware_qualified': True}, 'HARDWARE CLAIM UNVERIFIED'),
        )
        for change, expected in changes:
            with self.subTest(change=change):
                view = present_status(replace(BASE, phase='recording', selected_fps=None, selected_gain=None,
                                              settings_pending=True, **change))
                self.assertIsNone(view.preview_rect)
                self.assertIn(expected, view.text)

    def test_low_cell_warning_preserves_framing_in_every_routine_state(self):
        for phase in ('ready', 'recording', 'saving', 'applying_settings'):
            view = present_status(replace(BASE, phase=phase, battery_warning=True,
                                          battery_millivolts=3450, battery_percent=8))
            self.assertIn('LOW CELL', view.text)
            self.assertEqual(view.preview_rect, preview_rect())
            self.assertIn('3.450V', view.text)
            validate_layout(view)

    def test_low_cell_stop_is_not_just_a_warning(self):
        view = present_status(replace(BASE, phase='shutting_down', battery_warning=False,
                                      shutdown_reason='battery_low_voltage', battery_millivolts=3300))
        for text in ('LOW CELL', 'SHUTTING DOWN', 'KEEP POWER CONNECTED'):
            self.assertIn(text, view.text)
        self.assertIsNone(view.preview_rect)

    def test_input_loss_and_failure_are_both_visible(self):
        view = present_status(replace(BASE, phase='shutting_down', shutdown_reason='controls_unavailable',
                                      failure='controls_unavailable: RuntimeError: disconnected'))
        self.assertIn('INPUT LOST', view.text)
        self.assertIn('FAULT', view.text)
        self.assertTrue({'input_lost', 'fault'} <= set(view.notice_codes))

    def test_every_battery_data_failure_suppresses_cached_numbers(self):
        for reason in ('battery_read_error', 'battery_telemetry_missing', 'battery_telemetry_stale_or_reordered',
                       'battery_telemetry_implausible', 'battery_telemetry_gap', 'battery_clock_regression'):
            view = present_status(replace(BASE, phase='shutting_down', shutdown_reason=reason))
            self.assertIn('BATTERY DATA LOST', view.text)
            self.assertEqual(label(view, 'battery').text, '1S --V --%')
            self.assertNotIn('3.920', view.text)
            self.assertNotIn('76%', view.text)

    def test_missing_battery_fields_are_unknown_and_not_ready(self):
        for field in ('battery_millivolts', 'battery_percent'):
            view = present_status(replace(BASE, **{field: None}))
            self.assertEqual(label(view, 'phase').text, 'NOT READY')
            self.assertIn('BATTERY UNKNOWN', view.text)
            self.assertIn('--', label(view, 'battery').text)
            self.assertIsNone(view.preview_rect)

    def test_bad_numeric_telemetry_never_overflows_or_becomes_zero(self):
        for value in (False, True, -1, 5000, 10**10000, '76', float('nan'), float('inf')):
            view = present_status(replace(BASE, battery_millivolts=value, battery_percent=value))
            self.assertEqual(label(view, 'battery').text, '1S --V --%')
            self.assertIn('BATTERY UNKNOWN', view.text)
            validate_layout(view)

    def test_valid_battery_extremes_and_real_zero_soc(self):
        for mv, soc in itertools.product((2500, 3300, 4350), (0, 0.5, 99.5, 100)):
            view = present_status(replace(BASE, battery_millivolts=mv, battery_percent=soc))
            self.assertNotIn('BATTERY UNKNOWN', view.text)
            validate_layout(view)
        self.assertIn('0%', present_status(replace(BASE, battery_percent=0)).text)

    def test_all_readiness_categories_are_visible_at_once(self):
        view = present_status(replace(BASE, phase='checking', simulation_only=False,
                                      readiness_state='degraded', readiness_reasons=REASONS))
        for text in ('NOT READY', 'BENCH CHECKS', 'HEALTH DATA', 'HEAT', 'THROTTLE', 'USB', 'MEDIA', 'STORAGE', 'OTHER CHECK'):
            self.assertIn(text, view.text)
        self.assertEqual(sum(key == 'readiness_reason' for key, _ in view.diagnostics), len(REASONS))
        self.assertIsNone(view.preview_rect)
        validate_layout(view)

    def test_duplicate_reason_categories_keep_exact_diagnostics(self):
        reasons = ('media_writable_missing', 'media_writable_outside_limit')
        view = present_status(replace(BASE, readiness_state='unready', readiness_reasons=reasons))
        self.assertEqual(view.notice_codes.count('readiness_media'), 1)
        self.assertEqual([v for k, v in view.diagnostics if k == 'readiness_reason'], list(reasons))

    def test_contradictory_ready_snapshot_never_displays_ready(self):
        for change in ({'readiness_state': 'unready'}, {'readiness_reasons': ('media_writable_missing',)},
                       {'failure': 'disk failure'}, {'shutdown_reason': 'operator_shutdown'},
                       {'selected_fps': None}, {'selected_gain': None}, {'active_fps': None}, {'active_gain': None}):
            self.assertNotEqual(label(present_status(replace(BASE, **change)), 'phase').text, 'READY')

    def test_bad_phase_fails_visibly(self):
        for phase in ('ready\nREC', 'r' * 9000, None, {}, 12):
            view = present_status(replace(BASE, phase=phase))
            self.assertEqual(label(view, 'phase').text, 'STATUS UNKNOWN')
            self.assertIn('STATUS INVALID', view.text)
            self.assertIsNone(view.preview_rect)

    def test_bad_boolean_flags_fail_closed(self):
        for field in ('settings_pending', 'simulation_only', 'battery_warning', 'hardware_qualified'):
            view = present_status(replace(BASE, **{field: 1}))
            self.assertEqual(label(view, 'phase').text, 'STATUS UNKNOWN')
            self.assertIsNone(view.preview_rect)

    def test_malformed_failure_shutdown_and_readiness_types_fail_closed(self):
        for change in ({'failure': 1}, {'shutdown_reason': []}, {'readiness_reasons': ['media_writable_missing']},
                       {'readiness_reasons': (3,)}):
            view = present_status(replace(BASE, **change))
            self.assertEqual(label(view, 'phase').text, 'STATUS UNKNOWN')
            self.assertIn('STATUS INVALID', view.text)
            self.assertIsNone(view.preview_rect)

    def test_long_or_bad_settings_never_enter_pixels(self):
        for value in (None, True, 'X' * 9000, float('nan'), float('inf'), 10**90, -8):
            view = present_status(replace(BASE, selected_fps=value, selected_gain=value,
                                          active_fps=value, active_gain=value, settings_pending=True))
            self.assertIn('FPS  GAIN --', view.text)
            self.assertIn('NEXT -- FPS  GAIN --', view.text)
            self.assertIn('SETTINGS UNKNOWN', view.text)
            validate_layout(view)

    def test_long_unicode_exception_and_clip_path_stay_out_of_pixels(self):
        detail = 'recorder_failed: <script>\nUSB/../../file\x00 ' + '长' * 9000
        view = present_status(replace(BASE, phase='fault_stopped', failure=detail, clip='/PRIVATE/' + 'long' * 9000))
        for text in ('<script>', 'PRIVATE', '长'):
            self.assertNotIn(text, view.text)
        self.assertIn(('failure', detail), view.diagnostics)
        self.assertIn('FAULT', view.text)
        validate_layout(view)

    def test_dense_fault_page_keeps_all_critical_categories(self):
        view = present_status(replace(BASE, phase='fault_stopped', settings_pending=True,
                                      selected_fps=None, battery_millivolts=None,
                                      shutdown_reason='battery_low_voltage', failure='controls_unavailable: ' + 'E' * 9000,
                                      hardware_qualified=True, readiness_state='degraded', readiness_reasons=REASONS))
        for text in ('INPUT LOST', 'LOW CELL', 'FAULT', 'BATTERY UNKNOWN', 'SETTINGS UNKNOWN', 'HARDWARE CLAIM UNVERIFIED',
                     'NOT READY', 'BENCH CHECKS', 'MEDIA', 'HEALTH DATA', 'HEAT', 'THROTTLE', 'USB', 'STORAGE', 'OTHER CHECK'):
            self.assertIn(text, view.text)
        self.assertEqual(len(view.notice_codes), 15)
        validate_layout(view)
        self.assertEqual(len(rasterize(view)), 1024 * 768 * 4)

    def test_maximum_sixteen_notice_categories_fit_at_once(self):
        view = present_status(replace(BASE, phase='fault_stopped', simulation_only=1,
                                      selected_fps=None, battery_millivolts=None,
                                      shutdown_reason='battery_low_voltage', failure='controls_unavailable: error',
                                      hardware_qualified=True, readiness_state='degraded', readiness_reasons=REASONS))
        self.assertEqual(len(view.notice_codes), 16)
        self.assertIn('STATUS INVALID', view.text)
        for code in view.notice_codes:
            self.assertTrue(any(item.key == 'notice_' + code for item in view.labels))
        validate_layout(view)

    def test_simulation_and_unqualified_labels_are_permanent(self):
        for phase, simulation in itertools.product(PHASES, (False, True)):
            view = present_status(replace(BASE, phase=phase, simulation_only=simulation,
                                          readiness_state='simulation_unqualified' if simulation else 'reported_limits_pass'))
            self.assertIn('UNQUALIFIED', label(view, 'qualification').text)
            self.assertEqual('SIMULATION' in view.text, simulation)
        view = present_status(replace(BASE, hardware_qualified=True))
        self.assertIn('UNQUALIFIED', label(view, 'qualification').text)
        self.assertIn('HARDWARE CLAIM UNVERIFIED', view.text)
        self.assertEqual(label(view, 'phase').text, 'NOT READY')

    def test_stopped_or_poweroff_request_never_means_safe_removal(self):
        for phase, reason in itertools.product(('shutting_down', 'stopped', 'fault_stopped'),
                                               ('operator_shutdown', 'poweroff_requested', 'battery_low_voltage')):
            view = present_status(replace(BASE, phase=phase, shutdown_reason=reason))
            self.assertIn('KEEP POWER CONNECTED', view.text)
            self.assertIn('OS HALT IS NOT CONFIRMED', view.text)
            self.assertIsNone(view.preview_rect)
            for bad in ('SAFE TO REMOVE', 'POWER OFF COMPLETE', 'HALTED', 'REMOVE BATTERY'):
                self.assertNotIn(bad, view.text)

    def test_generic_shutdown_requires_no_old_snapshot(self):
        for simulation in (False, True):
            view = present_shutdown(simulation_only=simulation)
            self.assertEqual(label(view, 'phase').text, 'SHUTTING DOWN')
            self.assertEqual(label(view, 'battery').text, '1S --V --%')
            self.assertIn('STOP REQUESTED', view.text)
            self.assertIn('OS HALT IS NOT CONFIRMED', view.text)
            self.assertNotIn('READY', view.text)
            self.assertIsNone(view.preview_rect)
        for bad in (None, 1, 'false'):
            with self.assertRaises(ValueError):
                present_shutdown(simulation_only=bad)

    def test_no_invented_timers_audio_menus_or_storage_estimates(self):
        for phase in PHASES:
            view = present_status(replace(BASE, phase=phase))
            for invented in ('00:00', 'MIN LEFT', 'FPS MENU', 'AUDIO', 'SHUTTER', 'WB', 'CLIP'):
                self.assertNotIn(invented, view.text)

    def test_status_is_not_mutated(self):
        before = BASE.to_dict()
        first = present_status(BASE)
        self.assertEqual(before, BASE.to_dict())
        self.assertEqual(first, present_status(BASE))


class PresentationPixelTests(unittest.TestCase):
    def test_native_canvas_exact_full_sensor_aspect_and_area(self):
        rect = preview_rect()
        self.assertEqual(rect, Rect(57, 48, 910, 680))
        self.assertEqual(rect.width * 1088, rect.height * 1456)
        self.assertGreater(rect.width * rect.height / (1024 * 768), 0.78)
        self.assertEqual(HEADER_HEIGHT + FOOTER_HEIGHT, 88)
        self.assertEqual(preview_rect((1456, 1088)), rect)
        self.assertEqual(preview_rect((728, 544)), rect)

    def test_wrong_aspect_or_bad_source_is_rejected(self):
        for size in ((1024, 768), (1920, 1080), (0, 0), (728, 543), (True, 544), ('728', 544), (728,), None):
            with self.subTest(size=size), self.assertRaises(ValueError):
                present_status(BASE, source_size=size)

    def test_all_preview_pixels_transparent_everything_else_opaque(self):
        view = present_status(replace(BASE, phase='recording', settings_pending=True,
                                      selected_fps=18, selected_gain=8, battery_warning=True))
        pixels = rasterize(view)
        self.assertIsInstance(pixels, bytes)
        self.assertEqual(len(pixels), 1024 * 768 * 4)
        rect = view.preview_rect
        for y in range(768):
            row = pixels[y * 1024 * 4:(y + 1) * 1024 * 4]
            expected = (b'\xff' * rect.x + b'\0' * rect.width + b'\xff' * (1024 - rect.right)
                        if rect.y <= y < rect.bottom else b'\xff' * 1024)
            self.assertEqual(row[3::4], expected, f'row {y}')
            if rect.y <= y < rect.bottom:
                self.assertEqual(row[rect.x * 4:rect.right * 4], b'\0' * rect.width * 4)

    def test_shutdown_and_fault_pages_are_opaque(self):
        for view in (present_shutdown(simulation_only=True), present_status(replace(BASE, phase='fault_stopped')),
                     present_status(replace(BASE, readiness_state='unready'))):
            self.assertEqual(rasterize(view)[3::4], b'\xff' * (1024 * 768))

    def test_pixels_are_deterministic(self):
        for phase in PHASES:
            view = present_status(replace(BASE, phase=phase))
            self.assertEqual(rasterize(view), rasterize(view))

    def test_font_and_recording_glyph_pixel_geometry(self):
        for character, rows in FONT.items():
            self.assertEqual(len(rows), 7, character)
            self.assertTrue(all(0 <= row < 32 for row in rows), character)
        view = present_status(replace(BASE, phase='recording'))
        pixels = rasterize(view)
        first = label(view, 'phase')
        for row, bits in enumerate(FONT['R']):
            for column in range(5):
                x, y = first.x + column * first.scale, first.y + row * first.scale
                self.assertEqual(pixels[(y * 1024 + x) * 4:(y * 1024 + x + 1) * 4],
                                 bytes(RED if bits & 1 << (4 - column) else BLACK))

    def test_colours_have_high_numeric_contrast_on_black(self):
        def luminance(colour):
            rgb = [c / 255 for c in colour[:3]]
            linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
            return sum(c * weight for c, weight in zip(linear, (0.2126, 0.7152, 0.0722)))
        for colour in (WHITE, MUTED, RED, AMBER):
            self.assertGreater((luminance(colour) + 0.05) / 0.05, 4.5)

    def test_clipping_preview_cover_and_overlap_reject(self):
        view = present_status(BASE)
        for extra in (Label('bad', 'CLIPPED', 1000, 0, 3), Label('bad', 'IMAGE', 100, 100, 3),
                      Label('bad', 'OVERLAP', 24, 6, 3), Label('bad', 'LEFT', -1, 0, 3)):
            with self.assertRaises(ValueError):
                rasterize(replace(view, labels=view.labels + (extra,)))

    def test_unsupported_canvas_glyphs_scales_and_duplicate_keys_reject(self):
        view = present_status(BASE)
        with self.assertRaises(ValueError):
            rasterize(replace(view, canvas_size=(1920, 1080)))
        with self.assertRaises(ValueError):
            rasterize(replace(view, labels=view.labels + (view.labels[0],)))
        for text in ('', 'lowercase', '\n', 'é'):
            with self.assertRaises(ValueError):
                text_width(text, 2)
        for scale in (0, 7, 1.5, True):
            with self.assertRaises(ValueError):
                text_width('READY', scale)

    def test_missing_required_status_labels_are_rejected(self):
        view = present_status(BASE)
        for key in ('phase', 'qualification', 'battery', 'active_settings', 'action'):
            with self.assertRaises(ValueError):
                rasterize(replace(view, labels=tuple(item for item in view.labels if item.key != key)))

    def test_missing_critical_notice_is_rejected(self):
        view = present_status(replace(BASE, phase='shutting_down', shutdown_reason='controls_unavailable',
                                      failure='controls_unavailable: disconnected'))
        for code in view.notice_codes:
            with self.assertRaises(ValueError):
                rasterize(replace(view, labels=tuple(item for item in view.labels if item.key != 'notice_' + code)))

    def test_no_site_packages_or_hardware_imports_needed(self):
        root = str(Path(__file__).resolve().parents[1])
        script = f'''import sys
sys.path.insert(0, {root!r})
from gs8_camera_evf.d2_presentation import present_shutdown, rasterize
assert len(rasterize(present_shutdown(simulation_only=True))) == 3145728
for name in ('picamera2', 'gpiod', 'evdev', 'smbus2', 'PIL', 'numpy', 'gs8_camera_evf.d2_runtime'):
    assert name not in sys.modules, name
'''
        result = subprocess.run([sys.executable, '-S', '-c', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class RuntimePresentationIntegrationTests(unittest.TestCase):
    def test_real_runtime_one_tick_selector_settling_record_save_and_stop(self):
        from gs8_camera_evf.backends import SimulationBackend
        from gs8_camera_evf.d2_controls import D2InputSample
        from gs8_camera_evf.d2_power import D2BatterySample
        from gs8_camera_evf.d2_runtime import D2Runtime
        from gs8_camera_evf.storage import ClipStore
        from gs8_camera_evf.writer import InlineClipWriter
        with TemporaryDirectory(prefix='d2-presentation-') as directory:
            store = ClipStore(Path(directory), reserve_bytes=0)
            runtime = D2Runtime(store, lambda _: SimulationBackend(), now_ns=0,
                                wb_gains=(1.5, 1.25), writer_factory=InlineClipWriter)
            now = -10_000_000
            inputs = D2InputSample(0, True, False, 0, True, False)
            phases = set()
            def ticks(count, **changes):
                nonlocal now, inputs
                for _ in range(count):
                    now += 10_000_000
                    inputs = replace(inputs, acquired_ns=now, **changes)
                    status = runtime.step(now, inputs, D2BatterySample(now, 3900, 80))
                    view = present_status(status)
                    validate_layout(view)
                    phases.add(status.phase)
                return view
            try:
                self.assertEqual(label(ticks(110), 'phase').text, 'READY')
                ticks(3, run_high=False)
                self.assertEqual(label(ticks(13, run_high=True), 'phase').text, 'REC')
                settling = ticks(1, fps_high=True, encoder_position=2)
                status = runtime.status()
                self.assertEqual(status.phase, 'recording')
                self.assertEqual((status.active_fps, status.active_gain), (24, 1))
                self.assertIsNone(status.selected_fps)
                self.assertIsNone(status.selected_gain)
                self.assertTrue(status.settings_pending)
                self.assertIsNone(status.failure)
                self.assertIsNone(status.shutdown_reason)
                self.assertEqual(settling.preview_rect, preview_rect())
                self.assertEqual(label(settling, 'phase').text, 'REC')
                self.assertIn('ACTIVE 24 FPS  GAIN 1X', settling.text)
                self.assertIn('NEXT -- FPS  GAIN --', settling.text)
                self.assertIn('PRESS RUN TO STOP', settling.text)
                self.assertNotIn('CHECK READINESS', settling.text)
                self.assertNotIn('RELEASE RUN', settling.text)
                pending = ticks(3, fps_high=True, encoder_position=2)
                self.assertIn('ACTIVE 24 FPS  GAIN 1X', pending.text)
                self.assertIn('NEXT 18 FPS  GAIN 4X', pending.text)
                self.assertIn('SAVING', ticks(3, run_high=False).text)
                saving_settling = ticks(1, fps_high=False)
                self.assertEqual(runtime.status().phase, 'saving')
                self.assertIsNone(runtime.status().selected_fps)
                self.assertIsNone(runtime.status().selected_gain)
                self.assertTrue(runtime.status().settings_pending)
                self.assertEqual(saving_settling.preview_rect, preview_rect())
                self.assertEqual(label(saving_settling, 'phase').text, 'SAVING')
                self.assertIn('ACTIVE 24 FPS  GAIN 1X', saving_settling.text)
                self.assertIn('NEXT -- FPS  GAIN --', saving_settling.text)
                self.assertIn('KEEP POWER CONNECTED', saving_settling.text)
                self.assertNotIn('CHECK READINESS', saving_settling.text)
                ticks(2, fps_high=True)
                resumed = ticks(30, run_high=True)
                self.assertEqual(label(resumed, 'phase').text, 'READY')
                self.assertIn('ACTIVE 18 FPS  GAIN 4X', resumed.text)
                self.assertNotIn('NEXT', resumed.text)
                runtime.request_shutdown()
                stopped = ticks(20)
                self.assertIn('CAPTURE STOPPED', stopped.text)
                self.assertIn('OS HALT IS NOT CONFIRMED', stopped.text)
                self.assertTrue(runtime.capture_safely_drained)
                self.assertTrue({'checking', 'ready', 'recording', 'saving', 'stopped'} <= phases)
            finally:
                if runtime.backend is not None:
                    runtime.backend.close()
                if store.active is not None:
                    store.active.abandon()
                store.close()

    def test_real_input_loss_during_recording_or_saving_settling_hides_preview(self):
        from gs8_camera_evf.backends import SimulationBackend
        from gs8_camera_evf.d2_controls import D2InputSample
        from gs8_camera_evf.d2_power import D2BatterySample
        from gs8_camera_evf.d2_runtime import D2Runtime
        from gs8_camera_evf.storage import ClipStore
        from gs8_camera_evf.writer import InlineClipWriter
        for phase in ('recording', 'saving'):
            with self.subTest(phase=phase), TemporaryDirectory(prefix='d2-input-loss-presentation-') as directory:
                store = ClipStore(Path(directory), reserve_bytes=0)
                runtime = D2Runtime(store, lambda _: SimulationBackend(), now_ns=0,
                                    wb_gains=(1.5, 1.25), writer_factory=InlineClipWriter)
                now = -10_000_000
                inputs = D2InputSample(0, True, False, 0, True, False)
                def ticks(count, **changes):
                    nonlocal now, inputs
                    for _ in range(count):
                        now += 10_000_000
                        inputs = replace(inputs, acquired_ns=now, **changes)
                        result = runtime.step(now, inputs, D2BatterySample(now, 3900, 80))
                    return result
                try:
                    self.assertEqual(ticks(110).phase, 'ready')
                    ticks(3, run_high=False)
                    self.assertEqual(ticks(13, run_high=True).phase, 'recording')
                    if phase == 'saving':
                        self.assertEqual(ticks(3, run_high=False).phase, 'saving')
                    settling = ticks(1, fps_high=True)
                    self.assertEqual(settling.phase, phase)
                    self.assertIsNone(settling.selected_fps)
                    self.assertIsNone(settling.selected_gain)
                    self.assertEqual(present_status(settling).preview_rect, preview_rect())
                    now += 10_000_000
                    failure = runtime.step(now, input_error='injected disconnected input reader',
                                           battery_sample=D2BatterySample(now, 3900, 80))
                    self.assertEqual(failure.shutdown_reason, 'controls_unavailable')
                    view = present_status(failure)
                    self.assertIsNone(view.preview_rect)
                    self.assertIn('INPUT LOST', view.text)
                    self.assertIn('FAULT', view.text)
                    self.assertIn('KEEP POWER CONNECTED', view.text)
                    stopped = ticks(20)
                    self.assertEqual(stopped.phase, 'fault_stopped')
                    self.assertIsNone(present_status(stopped).preview_rect)
                    self.assertTrue(runtime.capture_safely_drained)
                finally:
                    if runtime.backend is not None:
                        runtime.backend.close()
                    if store.active is not None:
                        store.active.abandon()
                    store.close()

if __name__ == '__main__':
    unittest.main()
