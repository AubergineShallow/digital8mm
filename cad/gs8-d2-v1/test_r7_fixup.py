# SPDX-License-Identifier: MIT
"""r7 fix-up regressions (2026-10-09, after the adversarial verifiers VERIFY-C1..C5). Fast unless noted: layout-only
rules and text lints. Run through run_locked.py (repo root):

  python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/test_r7_fixup.py
"""
import copy
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import checks as CK  # noqa: E402
import layout as L  # noqa: E402


def lay(**over):
    ns = SimpleNamespace(**{k: getattr(L, k) for k in dir(L) if not k.startswith('__')})
    for k, v in over.items():
        setattr(ns, k, v)
    return ns


def tmpfile(text, suffix):
    fd, p = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, 'w', encoding='utf-8') as fh:
        fh.write(text)
    return p


class LensText(unittest.TestCase):
    """VERIFY-C4: the published guide carried the BX-4 instruction while the lint stayed green, and no step turned the
    camera back off the tab catch before s_c4."""

    def test_real_tree_clean(self):
        bad, have = CK.lens_hold_lint(L)
        self.assertTrue(have)
        self.assertEqual(bad, [])
        self.assertEqual(CK.lens_turn_back_lint(L), [])

    def test_guide_source_regression_fails(self):
        g = tmpfile("X = ('never force a stuck thread against the '\n     'roll fin: take the panel off and hold the "
                    "metal mount instead.')\nY = 'Hold the camera by its metal lens mount (housing)'\n", '.py')
        try:
            bad, _ = CK.lens_hold_lint(L, guide_paths=[g])
        finally:
            os.remove(g)
        phrases = {p for _, p in bad}
        self.assertIn('hold the metal mount', phrases)
        self.assertIn('against the roll fin', phrases)
        self.assertIn('hold the camera by its metal lens mount', phrases)

    def test_assembly_phrase_split_over_lines_fails(self):
        a = tmpfile('Intro.\n\nThen hold the camera by its metal\nlens mount with two fingers.\n', '.md')
        try:
            bad, have = CK.lens_hold_lint(L, assembly_path=a)
        finally:
            os.remove(a)
        self.assertTrue(have)
        self.assertIn('hold the camera by its metal lens mount', {p for _, p in bad})

    def test_turn_back_required_before_s_c4(self):
        steps = copy.deepcopy(L.STEPS)
        st8 = next(s for s in steps if s['step'] == 8)
        st8['action'] = st8['action'].replace(L.LENS_TURN_BACK, 'leave lens and camera as they are')
        probs = CK.lens_turn_back_lint(lay(STEPS=steps))
        self.assertEqual(len(probs), 1, probs)
        self.assertIn('lens_in', probs[0])
        st8['action'] = st8['action'] + ' Then ' + L.LENS_TURN_BACK + '.'     # after the snug: still a fail
        self.assertEqual(len(CK.lens_turn_back_lint(lay(STEPS=steps))), 1)


class Minors(unittest.TestCase):
    def test_header_housings_complete(self):
        """VERIFY-C2 minor: dropping every QT housing used to pass header_housings; rule (f) fails it."""
        ok = [r for r in CK.check_header_housings(L) if r.get('kind') == 'completeness']
        self.assertEqual({r['cable'] for r in ok}, set(L.HDR_USED_PINS))
        self.assertTrue(all(r['status'] == 'pass' for r in ok), ok)
        ns = lay(HEADER_HOUSINGS=[h for h in L.HEADER_HOUSINGS if h[0] != 'qt'])
        r = next(x for x in CK.check_header_housings(ns) if x.get('kind') == 'completeness' and x['cable'] == 'qt')
        self.assertEqual(r['status'], 'fail')
        self.assertIn('[1, 3, 5, 6]', r['error'])

    def test_service_pliers_disjoint_from_slab_finger(self):
        """VERIFY-C1 minor: the service pliers shank corridor and the slab-backing fingertip box never overlap."""
        acc = {a['id']: a for a in L.ACCESS}
        p = CK.box_bb(acc['acc_hdmi_evf_pliers_svc']['box'])
        f = CK.box_bb(acc['acc_evf_slab_back']['box'])
        self.assertEqual(acc['acc_hdmi_evf_pliers_svc']['state'], acc['acc_evf_slab_back']['state'])
        self.assertFalse(CK.bb_overlap(p, f), (p, f))
        self.assertLessEqual(p[5], f[4] - 1.0)


class RestRules(unittest.TestCase):
    """VERIFY-C5: the s_r1 driver handle reached past the hood-roof rest plane, and 'base-down' tips at about 6 deg;
    rest_pose had neither rule."""

    def test_driver_plane_needs_overhang(self):
        s = dict(id='s_x', head_point=(-31.5, -32.4, 85.5), axis=(0, 1, 0))
        ext_of = lambda k, sg: -35.2                                         # noqa: E731
        r = CK._rest_driver_row(L, s, 2, 1, 100.0, ext_of, None)
        self.assertEqual(r['status'], 'fail', r)                             # handle 85.5 + 15 + allowance > 100
        self.assertLess(r['clearance_min'], 0)
        ov = dict(face='-Y', edge_mm=20.0)
        self.assertEqual(CK._rest_driver_row(L, s, 2, 1, 100.0, ext_of, ov)['status'], 'pass')
        s2 = dict(s, head_point=(-31.5, 10.0, 85.5))                          # handle starts inside the edge
        self.assertEqual(CK._rest_driver_row(L, s2, 2, 1, 100.0, ext_of, ov)['status'], 'fail')
        s3 = dict(s, head_point=(-66.5, -32.4, 47.5))                         # s_r2-like: clear without overhang
        self.assertEqual(CK._rest_driver_row(L, s3, 2, 1, 100.0, ext_of, None)['status'], 'pass')

    def test_stability_tall_narrow_fails_wide_passes(self):
        import cadquery as cq
        fake = SimpleNamespace(PARTS={'body': {}}, mass_g=lambda v, i: v * 1e-3, LENSES={})
        tall = {'body': cq.Solid.makeBox(48.0, 30.0, 280.0, cq.Vector(-24.0, -15.0, 0.0))}
        r = CK._rest_stability_row(fake, {}, tall, ['body'], 2, -1, 0.0)    # CoM 140 up, half-width 15: 6.1 deg
        self.assertEqual(r['status'], 'fail', r)
        self.assertAlmostEqual(r['worst']['tip_deg'], 6.12, delta=0.1)
        wide = {'body': cq.Solid.makeBox(150.0, 70.0, 100.0, cq.Vector(-75.0, -35.0, 0.0))}
        self.assertEqual(CK._rest_stability_row(fake, {}, wide, ['body'], 2, -1, 0.0)['status'], 'pass')

    def test_layout_rows(self):
        rp = {r['id']: r for r in L.REST_POSES}
        self.assertEqual(rp['base_down_8']['support'], 'hand')
        self.assertEqual(rp['base_down_10']['support'], 'hand')
        self.assertIn('s_r1', rp['hood_down']['overhang']['for_screws'])
        self.assertIn('s_r1', rp['hood_down_s7']['overhang']['for_screws'])
        st8 = next(s for s in L.STEPS if s['step'] == 8)['action']
        self.assertIn('within about 20 mm of the edge', st8)
        self.assertIn('never stand it on its', st8)


if __name__ == '__main__':
    unittest.main(verbosity=2)
