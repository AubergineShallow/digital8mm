# SPDX-License-Identifier: MIT
"""r7 integration cases (PLAN s2/s6): one carried-box routine, one reach margin, the MATE_POSES coverage rule, the
category count. Fast (no part geometry). Cases whose data lands in a later r7 slot (MATE_POSES rows: S3 / S4) skip
until it exists. Run through run_locked.py (repo root):

  python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/test_r7_integration.py
"""
import json
import os
import sys
import unittest
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import manifold3d as m3  # noqa: E402
import checks as CK  # noqa: E402
import layout as L  # noqa: E402
import audit_cloud_release as A  # noqa: E402


def assert_coverage_ok(tc, cov):
    """Every coverage row passes, except that until SPEC-C3 (S4) adds its xt30 MATE_POSES row the P1-5 rule must
    fail on exactly (pigtail, pack_in): BX-3 is still open then, and the rule is what flags it."""
    for r in cov:
        if r['id'] == 'mate_poses' and not any(m.get('cable') == 'pigtail' for m in getattr(L, 'MATE_POSES', [])):
            tc.assertEqual(r['missing'], ['pigtail/pack_in'], r)
            tc.assertEqual(r['errors'], [], r)
        else:
            tc.assertEqual(r['status'], 'pass', r)


class Integration(unittest.TestCase):
    def test_one_routine_plug_and_rider(self):
        """A carried plug and a rider in the same insertion, one call: against a 'cable' keep-out the plug is soft
        (<= CARRY_SOFT_MM, listed) and the rider is hard (a hit); against a 'plug' keep-out both are hard."""
        cab = (0.0, 10.0, 0.0, 10.0, 0.0, 0.8)                 # 0.8 thick in z
        plg = (0.0, 10.0, 0.0, 10.0, 5.0, 6.0)                  # disjoint at offset 0
        cboxes = [('p_x', (2.0, 4.0, 2.0, 4.0, 0.0, 3.0), 'plug', set()),
                  ('ko_r', (6.0, 8.0, 6.0, 8.0, 0.0, 3.0), 'rider', set())]
        targets = [('ko_c', CK._bb_cube(m3, cab), cab), ('ko_p', CK._bb_cube(m3, plg), plg)]
        worst, soft = CK._carried_sweep(L, m3, cboxes, [(0.0, 0.0, 0.0), (0.0, 0.0, 2.5)], targets,
                                        {'ko_c': 'cable', 'ko_p': 'plug'})
        self.assertIn(('ko_r', 'ko_c'), worst)                  # rider: hard against a cable keep-out
        self.assertNotIn(('p_x', 'ko_c'), worst)                # plug: soft against a cable keep-out
        self.assertEqual([(s['carried'], s['keepout'], s['ok']) for s in soft], [('p_x', 'ko_c', True)])
        self.assertAlmostEqual(soft[0]['penetration_mm'], 0.8, places=3)
        self.assertIn(('p_x', 'ko_p'), worst)                   # plug: hard against a plug keep-out
        self.assertIn(('ko_r', 'ko_p'), worst)

    def test_reach_margin_equals_c3_allowance(self):
        for length in (150, 200, 250, 310):
            self.assertAlmostEqual(CK.reach_margin(L, length), max(10.0, 0.10 * length), places=6)

    def test_carried_lists_follow_plugs(self):
        """Every rigid boxed plug mated before an insertion that moves its end is in that insertion's carried set."""
        names = {i['id']: [c[0] for c in CK.carry_boxes(L, i, n)] for n, i in enumerate(L.INSERTIONS)}
        self.assertEqual(names['camera_in'], ['p_fpc_cam'])
        self.assertIn('p_qt_enc', names['panel_on'])
        self.assertNotIn('p_hdmi_evf', names['evf_pair_in'])    # r7 order: the HDMI is mated after the slide
        cov = CK._mate_coverage_rows(L, {p['id']: p for p in L.PLUGS})
        assert_coverage_ok(self, cov)

    @unittest.skipUnless(getattr(L, 'MATE_POSES', None), 'MATE_POSES lands in S3 (SPEC-C2)')
    def test_mate_poses_rule(self):
        """P1-5 (lands with S3): deleting MATE_POSES usb_5v_evf fails mate_paths coverage naming (usb_5v,
        evf_pair_in); the real layout requires exactly the rows it has (plus C3's xt30 row until S4 lands)."""
        self.assertTrue(any(r.get('inline_of') == 'usb_5v' or r.get('id') == 'usb_5v_evf' for r in L.MATE_POSES))
        plugs = {p['id']: p for p in L.PLUGS}
        r = CK._mate_pose_coverage_row(L, plugs)
        self.assertEqual(sorted(r['required']), sorted(['usb_5v/evf_pair_in', 'fpc/camera_in', 'qt/panel_on',
                                                        'fps_lead/panel_on', 'pigtail/pack_in']))
        ns = SimpleNamespace(**{k: getattr(L, k) for k in dir(L) if not k.startswith('__')})
        ns.MATE_POSES = [m for m in L.MATE_POSES if m['id'] != 'usb_5v_evf']
        r = CK._mate_pose_coverage_row(ns, plugs)
        self.assertEqual(r['status'], 'fail')
        self.assertIn('usb_5v/evf_pair_in', r['missing'])
        ns.MATE_POSES = list(L.MATE_POSES) + [dict(id='bad', cable='qt', plug='p_fpc_cam', insertion='panel_on')]
        r = CK._mate_pose_coverage_row(ns, plugs)
        self.assertIn('bad: plug p_fpc_cam is not a PLUGS id of qt', r['errors'])

    @unittest.skipUnless(any(m.get('id') == 'xt30' for m in getattr(L, 'MATE_POSES', [])), 'xt30 lands in S4 (SPEC-C3)')
    def test_xt30_row_required_and_one_model(self):
        """P3-1 (S4): deleting MATE_POSES xt30 fails mate_paths coverage naming (pigtail, pack_in); the xt30 row takes
        its slack from the lead_access pigtail model (_pigtail_face_out - face_out_min: one length model, one number)."""
        plugs = {p['id']: p for p in L.PLUGS}
        self.assertEqual(CK._mate_pose_coverage_row(L, plugs)['status'], 'pass')
        ns = SimpleNamespace(**{k: getattr(L, k) for k in dir(L) if not k.startswith('__')})
        ns.MATE_POSES = [m for m in L.MATE_POSES if m['id'] != 'xt30']
        r = CK._mate_pose_coverage_row(ns, plugs)
        self.assertEqual(r['status'], 'fail')
        self.assertEqual(r['missing'], ['pigtail/pack_in'])
        mp = next(m for m in L.MATE_POSES if m['id'] == 'xt30')
        self.assertEqual(mp['reach'], 'pigtail')
        mouth = next(x for x in CK.check_lead_access(L) if x['id'] == 'pigtail_xt30_mouth')
        fo = CK._pigtail_face_out(L)
        self.assertAlmostEqual(mouth['face_out_mm'], round(fo['face_out_mm'], 1), places=6)
        self.assertAlmostEqual(fo['face_out_mm'] - L.PIGTAIL['face_out_min'], 13.4, delta=0.05)

    def test_category_registered(self):
        """mate_paths is expected by the release audit; a build summary that carries it has one row per expected
        category (len(order) + mass_com)."""
        self.assertIn('mate_paths', A.EXPECTED_CATEGORIES)
        cj = os.path.join(HERE, 'out', 'checks.json')
        if not os.path.exists(cj):
            self.skipTest('no out/checks.json')
        with open(cj, encoding='utf-8') as f:
            summ = json.load(f).get('summary') or []
        names = [s['check'] for s in summ]
        if 'mate_paths' not in names:
            self.skipTest('out/ is a pre-r7 release (no mate_paths row yet)')
        self.assertEqual(set(names), set(A.EXPECTED_CATEGORIES))
        self.assertEqual(len(names), len(A.EXPECTED_CATEGORIES))

    def test_r7_registrations_match_audit(self):
        """r7 fix-up (VERIFY-C4): every r7 category build_d2 registers (INFO_NEUTRAL_R7 .add/.update lines) is in
        the release audit's EXPECTED_CATEGORIES. roll_catch was registered in build_d2 only, which would have failed
        `audit_cloud_release.py --final-release` on the first release that carried it."""
        import re
        with open(os.path.join(HERE, 'build_d2.py'), encoding='utf-8') as f:
            src = f.read()
        names = set()
        for m in re.finditer(r"INFO_NEUTRAL_R7\.(?:add|update)\((.*)\)", src):
            names.update(re.findall(r"'([a-z_0-9]+)'", m.group(1)))
        self.assertTrue({'mate_paths', 'roll_catch', 'handling', 'lead_access'} <= names, names)
        self.assertEqual(sorted(names - set(A.EXPECTED_CATEGORIES)), [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
