# SPDX-License-Identifier: MIT
"""Pure-Python datum input regressions. Synthetic values are never hardware measurements.

Run: python3 -B test_datum_inputs.py. No CAD is imported, built, exported or evaluated.
"""
import copy
import json
import unittest
from unittest.mock import patch

import layout as L


class DatumInputValidation(unittest.TestCase):
    def camera(self, **optics):
        cam = copy.deepcopy(L.CAM)
        cam['optics'].update(optics)
        return cam

    def assert_camera_invalid(self, cam):
        with patch.object(L, 'CAM', cam):
            datum = L.cam_datum_chain()
            self.assertEqual(datum['status'], 'fail', datum)
            self.assertTrue(datum['input_errors'], datum)
            rows = L.self_check()
            self.assertTrue(any(r['check'] == 'camera datum inputs valid' and not r['ok'] for r in rows), rows)
            json.dumps(L.engineering_diagnostics(), allow_nan=False)
            json.dumps(rows, allow_nan=False)

    def test_unknown_optional_inputs_stay_unknown(self):
        d = L.engineering_diagnostics()
        self.assertEqual(d['camera_datum']['status'], 'unconfirmed')
        self.assertIsNone(d['camera_datum']['derived_s_mm'])
        self.assertIsNone(d['camera_datum']['sensor_plane_x_mm'])
        self.assertEqual(d['encoder_push']['status'], 'unconfirmed')
        self.assertIsNone(d['encoder_push']['required_travel_mm'])
        json.dumps(d, allow_nan=False)

    def test_partial_optical_input_does_not_close_datum(self):
        with patch.object(L, 'CAM', self.camera(sensor_height_above_pcb_mm=0.2)):
            d = L.cam_datum_chain()
        self.assertEqual(d['status'], 'unconfirmed')
        self.assertIsNotNone(d['sensor_plane_x_mm'])
        self.assertIsNone(d['derived_s_mm'])
        self.assertIsNone(d['expected_flange_to_sensor_mm'])

    def test_camera_rejects_nonfinite_types_and_negative_numbers(self):
        fields = ('c_mount_flange_mm', 'stack_tolerance_mm', 'sensor_height_above_pcb_mm', 'filter_focus_shift_mm',
                  's_measured_mm', 'c_flange_to_cover_s0_mm', 'c_flange_to_cover_set_mm')
        for field in fields:
            for value in (-1.0, float('nan'), float('inf'), float('-inf'), True, False, '1.0', [], {}):
                with self.subTest(field=field, value=value):
                    self.assert_camera_invalid(self.camera(**{field: value}))

    def test_required_positive_camera_values_reject_zero_or_missing(self):
        for field in ('c_mount_flange_mm', 'stack_tolerance_mm'):
            for value in (0.0, None):
                with self.subTest(field=field, value=value):
                    self.assert_camera_invalid(self.camera(**{field: value}))
        for field in ('c_flange_to_cover_s0_mm', 'c_flange_to_cover_set_mm'):
            with self.subTest(field=field):
                self.assert_camera_invalid(self.camera(**{field: 0.0}))

    def test_measured_stack_dimensions_used_by_chain_are_validated(self):
        for part, dimension in (('adapter', 'ff'), ('bfar', 't'), ('housing', 'depth'), ('pcb', 't'), ('cover', 't')):
            for value in (0.0, -1.0, float('nan'), float('inf'), True, '1.0', None):
                with self.subTest(part=part, dimension=dimension, value=value):
                    cam = self.camera(sensor_height_above_pcb_mm=0.0, filter_focus_shift_mm=0.274)
                    cam[part][dimension] = value
                    previous = cam['s_nom']
                    L._resolve_camera_nominal(cam)
                    self.assertEqual(cam['s_nom'], previous)
                    self.assert_camera_invalid(cam)

    def test_negative_sensor_cannot_cancel_filter_shift(self):
        self.assert_camera_invalid(self.camera(sensor_height_above_pcb_mm=-0.1, filter_focus_shift_mm=0.374))

    def test_infinite_tolerance_cannot_accept_negative_stack(self):
        self.assert_camera_invalid(self.camera(c_flange_to_cover_s0_mm=-100.0, stack_tolerance_mm=float('inf')))

    def test_nominal_resolution_accepts_valid_measured_range_including_zero(self):
        for value in (0.0, 1.5, 3.0):
            cam = self.camera(s_measured_mm=value)
            L._resolve_camera_nominal(cam)
            self.assertEqual(cam['s_nom'], value)
            self.assertTrue(cam['status']['s_nom'].startswith('measured'))

    def test_invalid_measurements_never_replace_nominal_geometry(self):
        for value in (-1.0, 4.0, float('nan'), float('inf'), True, '1.0'):
            with self.subTest(value=value):
                cam = self.camera(s_measured_mm=value)
                previous = cam['s_nom']
                L._resolve_camera_nominal(cam)
                self.assertEqual(cam['s_nom'], previous)
                self.assertIn('invalid supplied', cam['status']['s_nom'])
                self.assert_camera_invalid(cam)

    def test_optical_resolution_closes_valid_synthetic_chain(self):
        cam = self.camera(sensor_height_above_pcb_mm=0.0, filter_focus_shift_mm=0.274)
        L._resolve_camera_nominal(cam)
        with patch.object(L, 'CAM', cam):
            d = L.cam_datum_chain()
        self.assertAlmostEqual(cam['s_nom'], 1.25)
        self.assertEqual(d['datum_residual_mm'], 0.0)
        self.assertEqual(d['status'], 'computed from supplied inputs')

    def test_derived_pose_outside_travel_and_overflow_fail_closed(self):
        for height, shift in ((4.0, 0.0), (1e308, 1e308)):
            cam = self.camera(sensor_height_above_pcb_mm=height, filter_focus_shift_mm=shift)
            previous = cam['s_nom']
            L._resolve_camera_nominal(cam)
            self.assertEqual(cam['s_nom'], previous)
            self.assert_camera_invalid(cam)

    def test_measured_pose_and_complete_optical_chain_must_agree(self):
        cam = self.camera(s_measured_mm=1.0, sensor_height_above_pcb_mm=0.0, filter_focus_shift_mm=0.274)
        L._resolve_camera_nominal(cam)
        with patch.object(L, 'CAM', cam):
            d = L.cam_datum_chain()
            rows = L.self_check()
        self.assertEqual(d['status'], 'fail')
        self.assertTrue(any(r['check'] == 'camera supplied optical datum closes' and not r['ok'] for r in rows))

    def test_direct_stack_mismatch_is_visible_in_diagnostics(self):
        with patch.object(L, 'CAM', self.camera(c_flange_to_cover_s0_mm=25.24)):
            d = L.cam_datum_chain()
        self.assertEqual(d['status'], 'fail')
        self.assertEqual(d['direct_stack'][0]['status'], 'fail')

    def test_explicit_sample_and_travel_limits_are_validated(self):
        for value in (-0.1, 3.1, float('nan'), float('inf'), True, '1.0'):
            with self.subTest(sample=value):
                d = L.cam_datum_chain(s=value)
                self.assertEqual(d['status'], 'fail')
                json.dumps(d, allow_nan=False)
                cam = self.camera()
                cam['s_nom'] = value
                self.assert_camera_invalid(cam)
        for limits in ((1.0, 0.0), (0.0, float('inf')), (-1.0, 3.0), (0.0,), None):
            with self.subTest(limits=limits):
                cam = self.camera()
                cam['s_range'] = limits
                self.assert_camera_invalid(cam)

    def test_encoder_rejects_bad_travel_and_allowance(self):
        for key in ('required_travel_mm', 'running_allowance_mm'):
            bad = (-1.0, float('nan'), float('inf'), float('-inf'), True, False, '0.1', [], {})
            bad += (0.0,) if key == 'required_travel_mm' else (None,)
            for value in bad:
                with self.subTest(key=key, value=value):
                    encoder = copy.deepcopy(L.ENCODER)
                    encoder['push'].update(required_travel_mm=0.1, running_allowance_mm=0.05)
                    encoder['push'][key] = value
                    with patch.object(L, 'ENCODER', encoder):
                        d = L.encoder_push_clearance()
                        rows = L.self_check()
                        self.assertEqual(d['status'], 'fail', d)
                        self.assertTrue(d['input_errors'])
                        self.assertTrue(any(r['check'] == 'encoder push inputs valid' and not r['ok'] for r in rows))
                        json.dumps(L.engineering_diagnostics(), allow_nan=False)
                        json.dumps(rows, allow_nan=False)

    def test_unknown_stroke_does_not_mask_invalid_allowance(self):
        encoder = copy.deepcopy(L.ENCODER)
        encoder['push'].update(required_travel_mm=None, running_allowance_mm=-1.0)
        with patch.object(L, 'ENCODER', encoder):
            self.assertEqual(L.encoder_push_clearance()['status'], 'fail')

    def test_valid_encoder_arithmetic_is_separate_from_bench_readiness(self):
        encoder = copy.deepcopy(L.ENCODER)
        encoder['push'].update(required_travel_mm=0.1, running_allowance_mm=0.05)
        with patch.object(L, 'ENCODER', encoder):
            d = L.encoder_push_clearance()
        self.assertEqual(d['status'], 'pass')
        self.assertIn('no push-readiness claim', d['gate'])

    def test_engineering_prying_diagnostic_is_json_safe_and_fails_invalid_input(self):
        for value in (None, 0.99, float('nan'), float('inf'), True, '2'):
            with self.subTest(value=value):
                lm = dict(L.LOAD_MODEL, anchor_prying_factor=value)
                with patch.object(L, 'LOAD_MODEL', lm):
                    d = L.engineering_diagnostics()
                self.assertEqual(d['lens_clamp_model']['status'], 'fail')
                self.assertIsNone(d['lens_clamp_model']['prying_factor'])
                json.dumps(d, allow_nan=False)


if __name__ == '__main__':
    unittest.main(verbosity=2)
