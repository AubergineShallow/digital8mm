# SPDX-License-Identifier: MIT
"""r7 C2 regressions (SPEC-C2 s4 + Plan edits P2-1..P2-6): BX-2 (QT lead mated with the panel 60 mm off: reach,
oriented hand envelope, out_of, tail), BX-10 (header housings), the lead stow, the cable_routes plug-point rule and
the sweeps `stowed` field / carried QT plug. 13 cases. Planted faults use a copy of the layout namespace (never the
module). Cases 6, 9 and 13 need solids: they use the COTS proxies built in-process plus synthetic boxes (no part
STEPs), so they run in a few seconds. Run through run_locked.py (repo root):

  python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/test_r7_c2_mate_reach.py
"""
import copy
import os
import sys
import unittest
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_d2 as B  # noqa: E402
import checks as CK  # noqa: E402
import d2_common as dc  # noqa: E402
import layout as L  # noqa: E402

_COTS = {}


def cots_rows():
    if not _COTS:
        _COTS.update(dict(B.build_cots()))
    return _COTS


def lay(**over):
    """A copy of the layout namespace; registries deep-copied."""
    ns = SimpleNamespace(**{k: getattr(L, k) for k in dir(L) if not k.startswith('__')})
    for k in ('PLUGS', 'KEEPOUTS', 'INSERTIONS', 'CABLES', 'KEEPOUT_KIND', 'ACCESS', 'MATES', 'REMOVALS', 'COTS',
              'ENCODER', 'PLUG', 'MATE_POSES', 'HEADER_HOUSINGS', 'HDR_HOUSING', 'HAND_ENVELOPES'):
        setattr(ns, k, copy.deepcopy(getattr(L, k)))
    for k, v in over.items():
        setattr(ns, k, v)
    return ns


def cable(ns, cid):
    return next(c for c in ns.CABLES if c['id'] == cid)


def mpose(ns, mid):
    return next(m for m in ns.MATE_POSES if m['id'] == mid)


def row_of(rows, key, val):
    return next(r for r in rows if r.get(key) == val)


def with_parts(ns, extra, from_step=8):
    """ns.present_at also lists the synthetic parts in `extra` from `from_step` on."""
    f = L.present_at
    ns.present_at = lambda s, _f=f: list(_f(s)) + (list(extra) if s >= from_step else [])
    return ns


def box_row(b):
    return dict(shape=dc.box_solid(dict(x=(b[0], b[1]), y=(b[2], b[3]), z=(b[4], b[5]))), kind='printed', stub=False)


class C2Fast(unittest.TestCase):
    def test_01_real_layout(self):
        mr = CK.check_mate_reach(L)
        st = {r['id']: r['status'] for r in mr}
        self.assertEqual(st['qt_enc'], 'pass')
        self.assertEqual(st['fps_ph'], 'pass')
        self.assertEqual(st['fpc_cam'], 'pass')
        self.assertEqual(st['oled_flex'], 'info')
        self.assertEqual(st['usb_5v_evf'], 'pass')
        q = row_of(mr, 'id', 'qt_enc')
        self.assertAlmostEqual(q['slack_mm'], 35.2, delta=0.05)
        self.assertAlmostEqual(q['out_of_mm'], 36.85, delta=0.05)
        f = row_of(mr, 'id', 'fps_ph')
        self.assertAlmostEqual(f['r1_mm'] + f['r2_mm'], 88.6, delta=0.1)
        self.assertAlmostEqual(f['d_mm'], 60.2, delta=0.05)
        self.assertAlmostEqual(row_of(mr, 'id', 'fpc_cam')['slack_mm'], 108.2, delta=0.5)
        u = row_of(mr, 'id', 'usb_5v_evf')
        self.assertGreaterEqual(u['r1_mm'], u['d_mm'])
        self.assertAlmostEqual(u['junction_out_mm'], 28.8, delta=0.05)
        cs = CK.check_cable_stow(L)
        hh = CK.check_header_housings(L)
        self.assertTrue(all(r['status'] in ('pass', 'info') for r in cs + hh), [r for r in cs + hh
                                                                                if r['status'] == 'fail'])
        s = row_of(cs, 'stow', 'ko_lead_stow')
        self.assertAlmostEqual(s['demand_mm3'], 2288, delta=1)
        self.assertAlmostEqual(s['capacity_mm3'], 2542, delta=1)
        for k, rr in (('mate_reach', mr), ('cable_stow', cs), ('header_housings', hh)):
            self.assertEqual(B.summarize(k, rr, info_neutral=True)['status'], 'pass', k)

    def test_02_bx2_short_lead(self):
        ns = lay()
        c = cable(ns, 'qt')
        c['length'], c['length_range'] = 150, None
        r = row_of(CK.check_mate_reach(ns), 'id', 'qt_enc')
        self.assertEqual(r['status'], 'fail')
        self.assertEqual(r['margin'], 15.0)
        self.assertAlmostEqual(r['slack_mm'], -45.8, delta=0.05)

    def test_03_pose_off_path(self):
        ns = lay()
        mpose(ns, 'qt_enc')['disp'] = (0, 80.0, 0)
        r = row_of(CK.check_mate_reach(ns), 'id', 'qt_enc')
        self.assertEqual(r['status'], 'fail')
        self.assertIn('not on the insertion path', r['error'])

    def test_04_stow_overfull(self):
        ns = lay()
        cable(ns, 'qt')['length_range'] = (240, 400)
        r = row_of(CK.check_cable_stow(ns), 'stow', 'ko_lead_stow')
        self.assertEqual(r['status'], 'fail')
        self.assertAlmostEqual(r['demand_mm3'], 3334, delta=2)
        self.assertIn('capacity', r['error'])

    def test_05_stow_over_blower(self):
        ns = lay()
        ns.KEEPOUTS['ko_lead_stow'] = L.B(-84.0, -44.0, -10.0, 3.0, 43.0, 75.0)
        r = row_of(CK.check_cable_stow(ns), 'stow', 'ko_lead_stow')
        self.assertEqual(r['status'], 'fail')
        self.assertEqual(len(r['problems']), 1, r['problems'])
        self.assertIn('blower', r['problems'][0])
        self.assertAlmostEqual(r['capacity_mm3'], 4160, delta=1)

    def test_06_hand_blocked(self):
        ns = with_parts(lay(), ['syn_cube'])
        rows = {'syn_cube': box_row((-99.0, -89.0, 76.0, 86.0, 52.0, 62.0))}   # inside the +60 hand box
        r = row_of(CK.check_mate_reach(ns, rows), 'id', 'qt_enc')
        self.assertEqual(r['status'], 'fail')
        self.assertIn('syn_cube', [h['obstacle'] for h in r['hand_hits']])
        self.assertIn('hand envelope hits syn_cube', r['error'])

    def test_07_housings(self):
        ns = lay()
        ns.HEADER_HOUSINGS = [h for h in ns.HEADER_HOUSINGS if h[0] != 'run_lead'] + [('run_lead', '1x3', (35, 37, 39))]
        r = row_of(CK.check_header_housings(ns), 'cable', 'run_lead')
        self.assertEqual(r['status'], 'fail')
        self.assertIn('unused pin(s) [35]', r['error'])
        self.assertIn("illegal housing type '1x3'", r['error'])
        ns = lay()
        ns.COTS['cooler']['box'] = dict(ns.COTS['cooler']['box'], y=(-26.0, ns.COTS['cooler']['box']['y'][1]))
        rr = CK.check_header_housings(ns)
        bad = [r for r in rr if r['status'] == 'fail']
        self.assertTrue(bad)
        self.assertTrue(all(r['cots_nearest'] == 'cooler' for r in bad))
        self.assertAlmostEqual(min(r['cots_gap_mm'] for r in bad), 0.23, delta=0.01)

    def test_08_plug_point_rule(self):
        ns = lay()
        c = cable(ns, 'qt')
        c['via'] = [k for k in c['via'] if k not in ('ko_qt_tail', 'ko_qt_plug')]
        r = row_of(CK.check_cable_routes(ns), 'cable', 'qt')
        self.assertEqual(r['status'], 'fail')
        self.assertAlmostEqual(r['plug_point_mm'], 13.1, delta=0.05)
        self.assertLessEqual(r['end_gap_mm'], CK.ROUTE_END_TOL)       # the old end-part test alone still passes
        self.assertEqual(len(r['problems']), 1, r['problems'])

    def test_09_carried_qt_plug(self):
        """P2-1: the QT plug mated before panel_on rides with the panel set (PLUGS, one carried-box routine)."""
        syn = (-80.0, -76.0, 40.0, 44.0, 52.0, 60.0)
        rows = dict(cots_rows(), syn_ob=box_row(syn))
        res = {}
        for when in ('before', 'after'):
            ns = with_parts(lay(), ['syn_ob'])
            ins = next(i for i in ns.INSERTIONS if i['id'] == 'panel_on')
            ins['moving'] = ['encoder']
            ins.pop('stowed', None)
            ns.INSERTIONS = [ins]
            next(p for p in ns.PLUGS if p['id'] == 'p_qt_enc')['mated'] = (when, 'panel_on')
            res[when] = CK.check_sweeps(ns, rows, 2.0)[0]
        hb = [h for h in res['before']['hits'] if h['obstacle'] == 'syn_ob']
        self.assertEqual(res['before']['status'], 'fail')
        self.assertEqual([h['moving'] for h in hb], ['p_qt_enc'])
        self.assertEqual(res['after']['status'], 'pass', res['after']['hits'])

    def test_10_bx2_pose_long_lead(self):
        ns = lay()
        mpose(ns, 'qt_enc')['disp'] = (0, 20.0, 0)
        r = row_of(CK.check_mate_reach(ns), 'id', 'qt_enc')
        self.assertAlmostEqual(r['slack_mm'], 73.0, delta=0.05)
        self.assertEqual(r['status'], 'fail')
        self.assertAlmostEqual(r['hand_box'][2], 31.85, delta=0.01)
        self.assertEqual(len(r['problems']), 1, r['problems'])
        self.assertIn('short of', r['problems'][0])

    def test_11_run_leads_narrow(self):
        ns = lay()
        ns.KEEPOUTS['ko_run_leads'] = dict(ns.KEEPOUTS['ko_run_leads'], x=(-63.0, ns.KEEPOUTS['ko_run_leads']['x'][1]))
        rr = CK.check_header_housings(ns)
        bad = [r for r in rr if r['status'] == 'fail']
        self.assertEqual([r['pins'] for r in bad], [[39]])
        self.assertAlmostEqual(bad[0]['top_outside_mm'], 0.83, delta=0.01)

    def test_12_encoder_moved(self):
        ns = lay()
        ns.ENCODER['c'] = (-58.0, ns.ENCODER['c'][1])
        self.assertAlmostEqual(CK._plug_point(ns, ('qt_socket', 0))[0], -74.15, places=6)
        r = row_of(CK.check_cable_routes(ns), 'cable', 'qt')
        self.assertEqual(r['status'], 'fail')
        self.assertAlmostEqual(r['plug_point_mm'], 1.55, delta=0.01)

    def test_13_stowed_field(self):
        mover = (-100.0, -90.0, 15.0, 20.5, 50.0, 60.0)
        rows = dict(cots_rows(), syn_mv=box_row(mover))
        res = {}
        for stowed in (True, False):
            ns = with_parts(lay(), ['syn_mv'])
            ins = next(i for i in ns.INSERTIONS if i['id'] == 'panel_on')
            ins['moving'] = ['encoder', 'switch_1824', 'syn_mv']
            if not stowed:
                ins.pop('stowed', None)
            ns.INSERTIONS = [ins]
            res[stowed] = CK.check_sweeps(ns, rows, 2.0)[0]
        self.assertEqual(res[True]['status'], 'fail')
        self.assertIn(('syn_mv', 'ko_lead_stow'), [(h['moving'], h['obstacle']) for h in res[True]['hits']])
        self.assertEqual(res[False]['status'], 'pass', res[False]['hits'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
