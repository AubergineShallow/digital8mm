# SPDX-License-Identifier: MIT
"""Cloud-copy refinements: postprocessed/print-stock contract and unmeasured datums.
Run only through run_locked.py. No measurement, slicer or physical gate is closed here.
"""
import copy
import math
import unittest
from unittest.mock import patch

import cadquery as cq
import layout as L
import printed_collar as PC
import build_d2 as B
import cots
import checks
import printed_small as PS

V = cq.Vector


class MechanicalRefinements(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.collars = {n: PC.build_part(L, 'lens_collar', n).val() for n in L.LENSES}

    def test_washer_flat_support_with_float_and_margin(self):
        lug = L.COLLAR['lug']
        x, y, z = lug['screw_x'], lug['screw_y'], lug['upper_z'][1]
        r = L.M3['washer']['d'] / 2 + lug['washer_float'] + lug['washer_edge_min']
        footprint = cq.Solid.makeCylinder(r, 0.05, V(x, y, z - 0.05), V(0, 0, 1))
        hole = cq.Solid.makeCylinder(L.M3['clear_d'] / 2 + 0.01, 0.2, V(x, y, z - 0.1), V(0, 0, 1))
        footprint = footprint.cut(hole)
        for name, sh in self.collars.items():
            self.assertLess(footprint.cut(sh).Volume(), 0.002, name)

    def test_washer_has_free_seat_at_every_float_extreme(self):
        lug = L.COLLAR['lug']
        f = lug['washer_float']
        for name, sh in self.collars.items():
            for dx, dy in ((0, 0), (f, 0), (-f, 0), (0, f), (0, -f)):
                washer = cq.Solid.makeCylinder(L.M3['washer']['d'] / 2, L.M3['washer']['t'],
                    V(lug['screw_x'] + dx, lug['screw_y'] + dy, lug['upper_z'][1]), V(0, 0, 1))
                self.assertLess(washer.intersect(sh).Volume(), 0.001, (name, dx, dy))

    def test_print_stock_is_exactly_three_removable_membranes(self):
        for name, sh in self.collars.items():
            prep = PC.prepare_print(L, 'lens_collar', sh)
            ps = prep['shape']
            self.assertTrue(ps.isValid(), name)
            self.assertEqual(len(ps.Solids()), 1, name)
            expected = 3 * math.pi * (L.COLLAR['hole_d'] / 2) ** 2 * L.COLLAR['bridge_membrane_t']
            self.assertAlmostEqual(ps.Volume() - sh.Volume(), expected, places=4)
            self.assertLess(sh.cut(ps).Volume(), 0.001)
            clears = []
            for k in L.COLLAR['bolted']:
                y, z = L.COLLAR['feet'][k]
                clears.append(cq.Solid.makeCylinder(L.COLLAR['hole_d'] / 2, 30, V(-10, y, z), V(1, 0, 0)))
            cleared = ps.cut(*clears)
            self.assertLess(cleared.cut(sh).Volume() + sh.cut(cleared).Volume(), 0.001, name)

    def test_print_stock_rejects_invalid_layer(self):
        bad = copy.deepcopy(L.COLLAR)
        bad['bridge_membrane_t'] = 0.0
        with patch.object(L, 'COLLAR', bad), self.assertRaises(ValueError):
            PC.prepare_print(L, 'lens_collar', self.collars[L.LENS])

    def test_build_rows_keep_finished_and_print_shapes_separate(self):
        rows, _ = B.build_printed(only='lens_collar')
        row = rows['lens_collar']
        self.assertFalse(row['stub'])
        self.assertGreater(row['print_shape'].Volume(), row['shape'].Volume())
        self.assertEqual(row['print_preparation']['membrane_count'], 3)
        self.assertEqual(row['print_preparation']['cleared_hole_d_mm'], 3.4)

    def test_control_shaft_bores_align_in_displayed_pose(self):
        for angle in (0.0, 45.0, -45.0, 90.0):
            knobs = copy.deepcopy(L.KNOBS)
            knobs['knob_fps']['index_deg'] = angle
            with patch.object(L, 'KNOBS', knobs):
                knob = PS.build_part(L, 'knob_fps').val()
                switch = cots.switch_1824(L, L.COTS['switch_1824'])
                rows = {'knob_fps': {'shape': knob}, 'switch_1824': {'shape': switch}}
                result = checks.check_mate_overlap(L, rows)
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0]['status'], 'pass', (angle, result))
                self.assertLess(result[0]['volume_mm3'], 0.001)
        encoder = cots.encoder(L, L.COTS['encoder'])
        knob = PS.build_part(L, 'knob_exp').val()
        result = checks.check_mate_overlap(L, {'knob_exp': {'shape': knob}, 'encoder': {'shape': encoder}})
        self.assertEqual(result[0]['status'], 'pass', result)

    def test_wrong_shaft_pose_is_not_hidden_by_press_mate(self):
        # Old bug: shaft is flat-up while the knob represents a 45-degree state.
        knobs = copy.deepcopy(L.KNOBS)
        knobs['knob_fps']['index_deg'] = 0.0
        with patch.object(L, 'KNOBS', knobs):
            wrong_switch = cots.switch_1824(L, L.COTS['switch_1824'])
        knob = PS.build_part(L, 'knob_fps').val()
        result = checks.check_mate_overlap(L, {'knob_fps': {'shape': knob}, 'switch_1824': {'shape': wrong_switch}})
        self.assertEqual(result[0]['status'], 'fail', result)
        self.assertGreater(result[0]['volume_mm3'], 8.0)

    def test_unknown_sensor_values_remain_unknown(self):
        d = L.cam_datum_chain()
        self.assertEqual(d['status'], 'unconfirmed')
        self.assertIsNone(d['sensor_plane_x_mm'])
        self.assertIsNone(d['derived_s_mm'])
        self.assertAlmostEqual(d['c_flange_to_pcb_front_mm'], 17.8)

    def test_supplied_optical_datum_detects_inconsistency(self):
        cam = copy.deepcopy(L.CAM)
        cam['optics'].update(sensor_height_above_pcb_mm=0.7, filter_focus_shift_mm=0.37)
        with patch.object(L, 'CAM', cam):
            self.assertNotEqual(L.cam_datum_chain()['datum_residual_mm'], 0)
            self.assertTrue(any(not c['ok'] for c in L.self_check() if c['check'] == 'camera supplied optical datum closes'))

    def test_supplied_direct_stack_detects_keeper_risk(self):
        cam = copy.deepcopy(L.CAM)
        cam['optics']['c_flange_to_cover_s0_mm'] = L.C_FLANGE_X - L.cam_cover_rear(0) + 0.8
        with patch.object(L, 'CAM', cam):
            self.assertTrue(any(not c['ok'] for c in L.self_check() if c['check'].startswith('camera direct stack agrees')))

    def test_encoder_unknown_stroke_is_not_pass(self):
        d = L.encoder_push_clearance()
        self.assertEqual(d['status'], 'unconfirmed')
        self.assertIsNone(d['required_travel_mm'])
        self.assertAlmostEqual(d['first_contact_travel_mm'], 0.2)

    def test_encoder_supplied_stroke_can_fail_and_pass(self):
        encoder = copy.deepcopy(L.ENCODER)
        encoder['push']['required_travel_mm'] = 0.1  # synthetic fault/control value, not hardware data
        with patch.object(L, 'ENCODER', encoder):
            self.assertEqual(L.encoder_push_clearance()['status'], 'fail')
            self.assertTrue(any(not c['ok'] for c in L.self_check() if c['check'] == 'encoder measured push has running clearance'))
            encoder['push']['running_allowance_mm'] = 0.05
            self.assertEqual(L.encoder_push_clearance()['status'], 'pass')


if __name__ == '__main__':
    unittest.main(verbosity=2)
