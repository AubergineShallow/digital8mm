# SPDX-License-Identifier: MIT
"""r7 C3 (SPEC-C3 section 4; BX-3, BX-11, BX-16): planted-fault regressions for checks.check_lead_access and the
sweep riders. Each case passes a modified copy of the layout and asserts the CORRECTED behaviour. 18 cases. The
rider and keeper cases use small synthetic solids (not the exported STEPs), so the file is independent of the build.
Run through run_locked.py (repo root):

  python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/test_r7_lead_access.py
"""
import copy
import os
import sys
import unittest
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import checks as CK  # noqa: E402
import layout as L  # noqa: E402


def ns(**over):
    """A copy of the layout namespace; the named tables are deep copies that the case may edit."""
    n = SimpleNamespace(**{k: getattr(L, k) for k in dir(L) if not k.startswith('__')})
    for k in ('PIGTAIL', 'KEEPOUTS', 'CABLES', 'COTS', 'FLOOR_HOLES', 'INSERTIONS'):
        setattr(n, k, copy.deepcopy(getattr(L, k)))
    for k, v in over.items():
        setattr(n, k, v)
    return n


def rows_of(lay):
    return {r['id']: r for r in CK.check_lead_access(lay)}


def cable(lay, cid):
    return next(c for c in lay.CABLES if c['id'] == cid)


def box_solid(b):
    import cadquery as cq
    return cq.Solid.makeBox(b[1] - b[0], b[3] - b[2], b[5] - b[4], cq.Vector(b[0], b[2], b[4]))


def gusset():
    """The tub's 45 deg lip gusset as a triangular prism along x (x -45..-30) through (y 26.8, z 2.5), (32.2, 2.5),
    (32.2, 7.9)."""
    import cadquery as cq
    return (cq.Workplane('YZ', origin=(-45.0, 0, 0)).polyline([(26.8, 2.5), (32.2, 2.5), (32.2, 7.9)]).close()
            .extrude(15.0).val())


def sweep_row(lay, rows, ins_id):
    return next(r for r in CK.check_sweeps(lay, rows, step_mm=2.0) if r['insertion'] == ins_id)


class LeadAccess(unittest.TestCase):
    def test_01_default_passes(self):
        r = rows_of(L)
        self.assertTrue(all(x['status'] == 'pass' for x in r.values()), [x for x in r.values() if x['status'] != 'pass'])
        # r7 fix-up (VERIFY-C3): the re-posed junction (flat on the pack top under the run button, female end -X,
        #   fuse beside) has room for the flexed exit bend at both ends (layout-only: to the bay walls)
        st = r['pigtail_store']
        self.assertEqual(st['exits']['status'], 'pass', st['exits'])
        self.assertTrue(all(e['clear_mm'] >= e['need_min_mm'] for e in st['exits']['ends'].values()), st['exits'])
        m = r['pigtail_xt30_mouth']
        self.assertAlmostEqual(m['face_out_mm'], 28.4, delta=0.05)
        self.assertEqual(m['required_len_mm'], 190)
        self.assertAlmostEqual(m['path_in_mm'], 38.9, delta=0.05)

    def test_02_r6_length_caught(self):
        n = ns()
        cable(n, 'pigtail')['length'] = 180
        m = rows_of(n)['pigtail_xt30_mouth']
        self.assertEqual(m['status'], 'fail')
        self.assertAlmostEqual(m['face_out_mm'], 10.4, delta=0.05)
        self.assertEqual(m['required_len_mm'], 190)

    def test_03_standoff_tie_caught(self):
        n = ns()
        n.PIGTAIL['tie']['at'] = (-9.5, 20.2, 12.0)
        m = rows_of(n)['pigtail_xt30_mouth']
        self.assertEqual(m['status'], 'fail')
        self.assertAlmostEqual(m['detour_mm'], 57.0, delta=0.1)
        self.assertAlmostEqual(m['face_out_mm'], -28.6, delta=0.1)

    def test_04_pads_moved_length_not_updated(self):
        n = ns()
        n.PIGTAIL['pad'] = dict(face='top', xy=(-91.0, -32.3))
        m = rows_of(n)['pigtail_xt30_mouth']
        self.assertEqual(m['status'], 'fail')
        self.assertAlmostEqual(m['face_out_mm'], -81.1, delta=0.05)
        cable(n, 'pigtail')['length'] = 310
        m = rows_of(n)['pigtail_xt30_mouth']
        self.assertEqual(m['status'], 'pass')
        self.assertAlmostEqual(m['face_out_mm'], 17.9, delta=0.05)

    def test_05_cut_rule_broken(self):
        r = rows_of(L)['pigtail_range']
        self.assertAlmostEqual(r['worst_face_out_mm'], 17.4, delta=0.05)
        self.assertEqual(r['l_cut_max_mm'], 310)
        n = ns()
        n.PIGTAIL['base_len'] = 180.0
        r = rows_of(n)['pigtail_range']
        self.assertEqual(r['status'], 'fail')
        self.assertLess(r['worst_face_out_mm'], 15.0)

    def test_06_no_hidden_credit(self):
        m = rows_of(L)['pigtail_xt30_mouth']
        self.assertEqual(m['housing_credit_mm'], 0.0)
        self.assertEqual(m['allowance_mm'], 20.0)
        n = ns()
        n.PIGTAIL['housing_credit'] = 16.0
        m2 = rows_of(n)['pigtail_xt30_mouth']
        self.assertEqual(m2['housing_credit_mm'], 16.0)            # a credit always shows in the row
        self.assertAlmostEqual(m2['face_out_mm'] - m['face_out_mm'], 16.0, delta=0.05)

    def test_07_coil_too_big(self):
        n = ns()
        n.PIGTAIL['od_range'] = (1.9, 3.5)
        self.assertEqual(rows_of(n)['pigtail_store']['status'], 'fail')

    def test_08_storage_squeezed(self):
        n = ns()
        n.KEEPOUTS['ko_xt30'] = dict(n.KEEPOUTS['ko_xt30'], y=(-8.0, 8.0))
        s = rows_of(n)['pigtail_store']
        self.assertEqual(s['status'], 'fail')
        self.assertIn('U-turn needs 19.2 > 16.0', s['error'])

    def test_09_pack_fouls_store(self):
        n = ns()
        b = n.COTS['pack']['box']
        n.COTS['pack']['box'] = dict(b, z=(b['z'][0], -30.0))
        s = rows_of(n)['pigtail_store']
        self.assertEqual(s['status'], 'fail')
        self.assertIn('pack top', s['error'])

    def test_10_lane_too_narrow(self):
        n = ns()
        cable(n, 'pigtail')['od'] = 2.6
        r = rows_of(n)['lane_pigtail_ko_pig_under']
        self.assertEqual(r['status'], 'fail')
        self.assertAlmostEqual(r['need_width_mm'], 5.2, places=2)

    def test_11_run_hole_back_to_r6(self):
        self.assertAlmostEqual(rows_of(L)['run_lead_window']['min_x_overlap_mm'], 3.5, places=2)
        n = ns()
        n.FLOOR_HOLES['run_lead'] = dict(n.FLOOR_HOLES['run_lead'], x=(-34.0, -28.0))
        r = rows_of(n)['run_lead_window']
        self.assertEqual(r['status'], 'fail')
        self.assertAlmostEqual(r['min_x_overlap_mm'], -4.0, places=2)

    def test_12_pack_lead_counted(self):
        s = rows_of(L)['pigtail_store']
        self.assertEqual(s['shared_mm'], 60)
        self.assertAlmostEqual(s['fill'], 0.149, delta=0.0006)     # r7 fix-up re-pose (was 0.176)
        n = ns()
        n.PIGTAIL['store'] = dict(n.PIGTAIL['store'], shared=())
        self.assertAlmostEqual(rows_of(n)['pigtail_store']['fill'], 0.100, delta=0.0006)   # (was 0.123)

    def test_13_store_overfull_with_pack_lead(self):
        n = ns()
        cable(n, 'pack_lead')['length'] = 150
        s = rows_of(n)['pigtail_store']
        self.assertEqual(s['status'], 'fail')
        self.assertGreater(s['fill'], n.PIGTAIL['store']['fill_max'])   # r7 fix-up re-pose: 0.223 (was > 0.25)

    def test_14_lane_drifts_into_run_lane(self):
        n = ns()
        n.KEEPOUTS['ko_pig_under'] = dict(n.KEEPOUTS['ko_pig_under'], x=(-39.5, -34.5))
        r = rows_of(n)['lane_separation']
        self.assertEqual(r['status'], 'fail')
        self.assertAlmostEqual(r['min_gap_mm'], 0.5, places=2)

    def test_15_wrap_back_under_keeper(self):
        n = ns()
        n.KEEPOUTS['ko_pig_wrap'] = dict(n.KEEPOUTS['ko_pig_wrap'], x=(-40.5, -35.5))
        r = rows_of(n)['pigtail_wrap_clear']
        self.assertEqual(r['status'], 'fail')
        self.assertGreater(r['max_volume_mm3'], 0.25)
        self.assertLess(r['max_volume_mm3'], 0.35)

    def test_16_base_passage_decoupled(self):
        self.assertEqual(L.base_run_passage(), dict(x=L.KEEPOUTS['ko_run_drop']['x'], y=L.KEEPOUTS['ko_run_drop']['y']))
        with open(os.path.join(HERE, 'printed_grip.py'), encoding='utf-8') as f:
            src = f.read()
        body = src[src.index('def _base_cuts'):]
        body = body[:body.index('\ndef ', 1)]
        self.assertIn('base_run_passage(', body)
        self.assertNotIn("FH['run_lead']", body)

    def test_17_rider_swept_and_declared(self):
        n = ns()
        n.KEEPOUTS['ko_pig_wrap'] = dict(n.KEEPOUTS['ko_pig_wrap'], y=(23.7, 30.0))
        r = sweep_row(n, {'tub': {'shape': gusset()}}, 'pi_in')
        h = [x for x in r['hits'] if x['moving'] == 'ko_pig_wrap']
        self.assertTrue(h and h[0]['max_volume_mm3'] > 0.5, r['hits'])
        r = sweep_row(L, {'tub': {'shape': gusset()}}, 'pi_in')       # y1 26.9: 0.1 clear at z 2.7
        self.assertEqual([x for x in r['hits'] if x['moving'] in ('ko_pig_wrap', 'ko_pig_under')], [])
        self.assertEqual(r['riders'], ['ko_pig_wrap', 'ko_pig_under'])
        n = ns()
        next(i for i in n.INSERTIONS if i['id'] == 'pi_in')['riders'] = ['ko_nope']
        r = sweep_row(n, {'tub': {'shape': gusset()}}, 'pi_in')
        self.assertEqual(r['status'], 'fail')
        self.assertIn('rider not in KEEPOUTS: ko_nope', r['errors'])

    def test_18_riders_are_later_obstacles(self):
        r = sweep_row(L, {'pi_keeper': {'shape': box_solid((-48.0, -38.0, 23.05, 31.9, 7.7, 15.6))}}, 'keeper_in')
        h = [x for x in r['hits'] if x['obstacle'] == 'carried:ko_pig_wrap']
        self.assertTrue(h, r['hits'])
        # sweeps sample the path, not the final pose (0.5 above it: 2.0 x 3.2 x 1.8 = 11.52; final 14.7 per SPEC-C3,
        #   which the keepouts check covers); either way far above the 0.5 mm3 tolerance
        self.assertGreater(h[0]['max_volume_mm3'], 0.5)
        self.assertAlmostEqual(h[0]['max_volume_mm3'], 11.52, delta=0.1)
        r = sweep_row(L, {'pi_keeper': {'shape': box_solid((-48.0, -41.0, 23.05, 31.9, 7.7, 15.6))}}, 'keeper_in')
        self.assertEqual([x for x in r['hits'] if x['obstacle'].startswith('carried:ko_pig')], [])


    def test_19_pigtail_drop(self):
        """r7 fix-up (VERIFY-C3): the G-W5 drop estimate caps d_board at 25 mm; STEPS[1] carries the stop branch; the
        xh-estimate pad (L_cut 295) is past it; an assumed pad there, or a step 1 without the stop, fails."""
        r = rows_of(L)
        d = r['pigtail_drop']
        self.assertEqual(d['status'], 'pass', d)
        self.assertAlmostEqual(d['d_board_max_mm'], 25.0, delta=0.01)
        self.assertAlmostEqual(d['assumed_pad_drop_v'], 0.141, delta=0.001)
        self.assertIn('xh estimate top (-85.0, -19.3)', r['pigtail_range']['drop_limited'])
        self.assertIn('G-W5', r['pigtail_range']['gate'])
        n = ns()
        n.PIGTAIL['pad'] = dict(n.PIGTAIL['pad'], xy=(-85.0, -19.3))
        self.assertEqual(rows_of(n)['pigtail_drop']['status'], 'fail')
        n2 = ns(STEPS=copy.deepcopy(L.STEPS))
        st1 = next(x for x in n2.STEPS if x['step'] == 1)
        st1['action'] = st1['action'].replace('stop: do not cut', 'cut anyway')
        self.assertEqual(rows_of(n2)['pigtail_drop']['status'], 'fail')

    def test_21_old_junction_pose_fails_exits(self):
        """r7 fix-up (VERIFY-C3): the r7 S4 pose (pair box x -63..-37 over the fuse, +X end 2.0 mm from the run button)
        fails the exits rule, so the store row cannot pass on it."""
        ex = CK._pigtail_store_exits(L, None, (-63.0, -37.0, -5.1, 5.1, -26.5, -14.8), 2.4)
        self.assertEqual(ex['status'], 'fail', ex)
        self.assertEqual(ex['ends']['+x']['nearest'], 'run_button')
        n = ns()
        n.COTS['xt30_pair'] = dict(n.COTS['xt30_pair'], box=dict(x=(-63.0, -37.0), y=(-5.1, 5.1), z=(-26.5, -14.8)))
        n.PIGTAIL['store'] = dict(n.PIGTAIL['store'], female_end='+x')
        self.assertNotEqual(rows_of(n)['pigtail_store']['status'], 'pass')

    def test_20_store_exits(self):
        """r7 fix-up (VERIFY-C3): a fill / U-turn failure still fails the store row (the exits gate never hides it);
        a pair box with room at both ends clears the exits."""
        n = ns()
        n.PIGTAIL['store'] = dict(n.PIGTAIL['store'], fill_max=0.10)
        self.assertEqual(rows_of(n)['pigtail_store']['status'], 'fail')
        ex = CK._pigtail_store_exits(L, None, (-60.0, -36.0, -5.1, 5.1, -36.0, -29.5), 2.4)
        self.assertEqual(ex['status'], 'pass', ex)


if __name__ == '__main__':
    unittest.main(verbosity=2)
