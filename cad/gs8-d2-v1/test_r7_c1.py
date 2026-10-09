# SPDX-License-Identifier: MIT
"""r7 C1 regressions (SPEC-C1 4.4 + PLAN s6): BX-1 (mated EVF HDMI plug carried by the pair slide), C-16, BX-7 (foam
pad rides with the pair), BX-9 (5 V junction tuck corridor), the carried-box rule (hard/soft classes, fixed-end
plugs), mate_paths (plug_in, access, coverage) and evf_restraint support_span. 12 cases. Planted faults use a copy of
the layout namespace (never the module); geometry comes from the part STEPs in out/step/parts (the last release) and
the COTS proxies built in-process. Run through run_locked.py (repo root):

  python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/test_r7_c1.py
"""
import copy
import os
import sys
import unittest
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import cadquery as cq  # noqa: E402
import build_d2 as B  # noqa: E402
import checks as CK  # noqa: E402
import layout as L  # noqa: E402

STEP_DIR = os.path.join(HERE, 'out', 'step', 'parts')
_ROWS = {}


def rows():
    """COTS proxies + printed parts from the release part STEPs (rebuilt in-process when a STEP is missing)."""
    if not _ROWS:
        r = dict(B.build_cots())
        for pid in L.PARTS:
            pth = os.path.join(STEP_DIR, pid + '.step')
            if os.path.exists(pth):
                sh = B.as_shape(cq.importers.importStep(pth))
                r[pid] = dict(shape=sh, kind='printed', stub=False, module=L.PARTS[pid]['module'], print={})
            else:
                r[pid] = B.build_printed(only=pid)[0][pid]
        _ROWS.update(r)
    return _ROWS


def lay(max_step=None, **over):
    """A copy of the layout namespace; registries deep-copied; INSERTIONS cut to steps <= max_step (same order)."""
    ns = SimpleNamespace(**{k: getattr(L, k) for k in dir(L) if not k.startswith('__')})
    for k in ('PLUGS', 'KEEPOUTS', 'INSERTIONS', 'CABLES', 'KEEPOUT_KIND', 'ACCESS', 'MATES', 'REMOVALS'):
        setattr(ns, k, copy.deepcopy(getattr(L, k)))
    if max_step is not None:
        ns.INSERTIONS = [i for i in ns.INSERTIONS if i['step'] <= max_step]
    for k, v in over.items():
        setattr(ns, k, v)
    return ns


def plug(ns, pid):
    return next(p for p in ns.PLUGS if p['id'] == pid)


_BASE = {}


def base():
    """check_sweeps on the real layout (2 mm), computed once."""
    if not _BASE:
        _BASE.update({r['insertion']: r for r in CK.check_sweeps(L, rows(), 2.0)})
    return _BASE


def sweep_row(ns, ins_id, step_mm=2.0):
    return next(r for r in CK.check_sweeps(ns, rows(), step_mm) if r['insertion'] == ins_id)


class C1Fast(unittest.TestCase):
    def test_coverage_missing_plug(self):
        ns = lay()
        ns.PLUGS = [p for p in ns.PLUGS if not (p['cable'] == 'hdmi' and p['end'] == 'evf_board')]
        cov = CK._mate_coverage_rows(ns, {p['id']: p for p in ns.PLUGS})
        r = next(x for x in cov if x['id'] == 'plugs_per_cable_end')
        self.assertEqual(r['status'], 'fail')
        self.assertIn('hdmi/evf_board', r['gaps'])

    def test_coverage_count(self):
        self.assertEqual(len(L.PLUGS), 20)
        pairs = sorted((c, e) for c, ends in L.CABLE_ENDS.items() for e in ends)
        self.assertEqual(sorted((p['cable'], p['end']) for p in L.PLUGS), pairs)
        cov = CK._mate_coverage_rows(L, {p['id']: p for p in L.PLUGS})
        # r7 C2 (S3): the P1-5 'mate_poses' row fails on (pigtail, pack_in) until SPEC-C3 (S4) adds its xt30 row
        pend = not any(m.get('cable') == 'pigtail' for m in getattr(L, 'MATE_POSES', []))
        self.assertTrue(all(x['status'] == 'pass' or (pend and x['id'] == 'mate_poses'
                                                      and x['missing'] == ['pigtail/pack_in']) for x in cov), cov)
        ns = lay()
        ns.PLUGS = [p for p in ns.PLUGS if p['id'] != 'p_pack_xt30']
        cov = CK._mate_coverage_rows(ns, {p['id']: p for p in ns.PLUGS})
        r = next(x for x in cov if x['id'] == 'plugs_per_cable_end')
        self.assertEqual(r['status'], 'fail')
        self.assertIn('pack_lead/xt30_pair', r['gaps'])

    def test_pad_moves_with_pair(self):
        ins = {i['id']: i for i in L.INSERTIONS}
        self.assertIn('foam_pad', ins['evf_pair_in']['moving'])
        evf_out = next(r for r in L.REMOVALS if r['id'] == 'evf_out')
        self.assertIn('foam_pad', evf_out['moving'])
        self.assertNotIn('foam_pad', evf_out['off'])
        self.assertNotIn('eyepiece', evf_out['off'])       # stricter service row (SPEC-C1 3.2-8)
        self.assertEqual(evf_out.get('unplug'), ['p_hdmi_evf'])
        for row in (base()['eyepiece_in'], base()['evf_pair_in']):
            self.assertNotIn('foam_pad', row['obstacles'])

    def test_mate_overlap_row_kept(self):
        self.assertIn(('hmx039', 'foam_pad', 'contact'), L.MATES)
        ns = lay(MATES=[('hmx039', 'foam_pad', 'contact')])
        out = CK.check_mate_overlap(ns, rows())
        self.assertTrue(any(set(x['pair']) == {'hmx039', 'foam_pad'} for x in out), out)


class C1Geo(unittest.TestCase):
    @property
    def base(self):
        return base()

    def test_bx1_plug_carried_fails(self):
        ns = lay(max_step=6)
        plug(ns, 'p_hdmi_evf')['mated'] = ('before', 'evf_pair_in')       # the r6 order: HDMI mated on the bench
        r = sweep_row(ns, 'evf_pair_in')
        self.assertEqual(r['status'], 'fail')
        self.assertIn('p_hdmi_evf', r['carried'])
        h = [x for x in r['hits'] if x['moving'] == 'p_hdmi_evf' and x['obstacle'] == 'tub']
        self.assertEqual(len(h), 1, r['hits'])
        self.assertTrue(60.0 <= h[0]['max_volume_mm3'] <= 66.0, h)
        self.assertAlmostEqual(h[0]['where'][1], 18.0, delta=0.15)     # manifold bbox (min xyz, max xyz)
        self.assertAlmostEqual(h[0]['where'][4], 28.5, delta=0.15)

    def test_r7_order_passes(self):
        r = self.base['evf_pair_in']
        self.assertEqual(r['status'], 'pass', r['hits'])
        self.assertEqual(r['carried'], [])
        self.assertTrue(all(f['max_volume_mm3'] == 0.0 for x in self.base.values() for f in x['fixed_end_obstacles']))
        mp = CK.check_mate_paths(L, rows(), sweep_rows=list(self.base.values()))
        pi = next(x for x in mp if x['kind'] == 'plug_in' and x['id'] == 'p_hdmi_evf')
        self.assertEqual(pi['status'], 'pass', pi['hits'])
        # r7 C2 (S3): the P1-5 'mate_poses' row fails on (pigtail, pack_in) until SPEC-C3 (S4) adds its xt30 row
        pend = not any(m.get('cable') == 'pigtail' for m in getattr(L, 'MATE_POSES', []))
        self.assertTrue(all(x['status'] == 'pass' or (pend and x.get('id') == 'mate_poses'
                                                      and x['missing'] == ['pigtail/pack_in']) for x in mp),
                        [x for x in mp if x['status'] != 'pass'])

    def test_soft_limit(self):
        ns = lay(max_step=7)
        b = ns.KEEPOUTS['ko_fpc_stiff']
        ns.KEEPOUTS['ko_fpc_stiff'] = dict(b, z=(b['z'][0] - 1.5, b['z'][1]))
        r = sweep_row(ns, 'camera_in')
        self.assertEqual(r['status'], 'fail')
        self.assertTrue(any(h['moving'] == 'p_fpc_cam' and 'soft contact' in (h.get('error') or '') for h in r['hits']),
                        r['hits'])
        base = self.base['camera_in']
        self.assertEqual(base['status'], 'pass')
        self.assertEqual([s['keepout'] for s in base['soft_contacts']], ['ko_hdmi_run'])
        self.assertAlmostEqual(base['soft_contacts'][0]['penetration_mm'], 0.75, delta=0.05)

    def _t_fix(self, kind):
        ns = lay(max_step=8)
        ns.KEEPOUTS['ko_t'] = L.B(-80.0, -77.0, 26.0, 26.8, 55.0, 59.0)
        ns.CABLES.append(dict(id='t_fix', via=['ko_t'], steps=(4,), ends=('pi5', 'tub'), length=100))
        ns.KEEPOUT_KIND['ko_t'] = kind
        return sweep_row(ns, 'panel_on')

    def test_hard_plug_keepout(self):
        r = self._t_fix('plug')
        self.assertEqual(r['status'], 'fail')
        h = [x for x in r['hits'] if x['moving'] == 'p_qt_enc' and x['obstacle'] == 'ko_t']
        self.assertTrue(h and abs(h[0]['max_volume_mm3'] - 9.6) < 0.5, r['hits'])
        r = self._t_fix('cable')
        self.assertEqual(r['status'], 'pass', r['hits'])
        s = [x for x in r['soft_contacts'] if x['keepout'] == 'ko_t']
        self.assertTrue(s and abs(s[0]['penetration_mm'] - 0.8) < 0.05, r['soft_contacts'])

    def test_fixed_end_obstacle(self):
        ns = lay(max_step=6)
        ns.KEEPOUTS['ko_hdmi_pi'] = L.B(-142.0, -139.0, 40.0, 44.0, 70.0, 80.0)
        r = sweep_row(ns, 'evf_pair_in')
        self.assertEqual(r['status'], 'fail')
        fx = {f['keepout']: f for f in r['fixed_end_obstacles']}
        self.assertIn('ko_hdmi_pi', fx)
        self.assertGreater(fx['ko_hdmi_pi']['max_volume_mm3'], 0.5)
        self.assertNotIn('ko_hdmi_pi', r['keepouts'])      # not an active cable keep-out: only the fixed-end rule

    def test_push_room(self):
        ns = lay()
        plug(ns, 'p_hdmi_evf')['stroke'] = 8.0
        mp = CK.check_mate_paths(ns, rows())
        a = next(x for x in mp if x['id'] == 'acc_hdmi_evf_push')
        self.assertEqual(a['status'], 'pass', a)
        self.assertEqual(a['push_method'], 'push_stick')
        self.assertAlmostEqual(a['push_height_mm'], 8.0, places=2)
        w = next(x for x in mp if x['id'] == 'acc_hdmi_evf_push_well')
        self.assertEqual((w['status'], w['push_method']), ('pass', 'fingertip'), w)

    def test_plug_path_needs_drop(self):
        """r7 fix-up (VERIFY-C1 minor): the in-situ plug path with only a 6 mm drop under the slab fails on the plug
        head (its own regression, independent of the sweeps coverage)."""
        ns = lay()
        plug(ns, 'p_hdmi_evf')['path'] = [(0, 30.0, -6.0), (0, 0, -6.0), (0, 0, 0)]
        r = next(x for x in CK.check_mate_paths(ns, rows()) if x.get('kind') == 'plug_in' and x['id'] == 'p_hdmi_evf')
        self.assertEqual(r['status'], 'fail', r)
        ok = next(x for x in CK.check_mate_paths(L, rows()) if x.get('kind') == 'plug_in' and x['id'] == 'p_hdmi_evf')
        self.assertEqual(ok['status'], 'pass', ok)

    def test_push_well_open_no_floor_lever(self):
        """r7 fix-up (VERIFY-C1): the tub top at z 36 is only the stick-guide block (y < 10.8); the well beyond is
        open to the tub floor, so the push fallback comes straight up from the well (computed clear) and the step text
        names no floor-edge lever."""
        mp = CK.check_mate_paths(L, rows())
        w = next(x for x in mp if x['id'] == 'acc_hdmi_evf_push_well')
        self.assertEqual(w['status'], 'pass', w)
        self.assertLessEqual(w['boxes'][0][4], 3.5)          # down to the tub floor: there is no z-36 floor there
        self.assertGreaterEqual(w['push_height_mm'], L.FINGERTIP_MM)
        st6 = next(s for s in L.STEPS if s['step'] == 6)
        txt = (st6['action'] + ' ' + st6['tool']).lower()
        for bad in ('floor edge', 'as a lever', 'push lever', 'on the floor with its tip'):
            self.assertNotIn(bad, txt)
        self.assertIn('open well', txt)
        rr = dict(rows())                                      # a solid planted in the well fails the row
        blk = cq.Solid.makeBox(4.0, 4.0, 4.0, cq.Vector(-141.0, 18.0, 20.0))
        rr['microsd'] = dict(rr['microsd'], shape=B.as_shape(rr['microsd']['shape']).fuse(blk))
        w2 = next(x for x in CK.check_mate_paths(L, rr) if x['id'] == 'acc_hdmi_evf_push_well')
        self.assertEqual(w2['status'], 'fail', w2)

    def test_access_blocked(self):
        rr = dict(rows())
        blk = cq.Solid.makeBox(2.0, 2.0, 2.0, cq.Vector(-141.0, 25.0, 50.0))
        rr['microsd'] = dict(rr['microsd'], shape=B.as_shape(rr['microsd']['shape']).fuse(blk))
        mp = CK.check_mate_paths(L, rr)
        a = next(x for x in mp if x['id'] == 'acc_hdmi_evf_hand')
        self.assertEqual(a['status'], 'fail')
        self.assertTrue(any(h['obstacle'] == 'microsd' for h in a['hits']), a['hits'])

    def test_support_span_cut(self):
        rr = dict(rows())
        tub = B.as_shape(rr['tub']['shape'])
        for x0, x1 in ((-140.05, -136.8), (-136.81, -136.2)):     # SPEC-C1 s2 cut B
            tub = tub.cut(cq.Solid.makeBox(x1 - x0, 10.6, 3.95, cq.Vector(x0, 18.0, 61.4)))
        rr['tub'] = dict(rr['tub'], shape=tub)
        out = {r['direction']: r for r in CK.check_evf_restraint(L, rr)}
        self.assertEqual(out['support_span_prepanel']['status'], 'fail')
        self.assertEqual(out['support_span_final']['status'], 'fail')
        for d in ('+X', '-X', '+Y', '-Y', '+Z', '-Z'):
            self.assertEqual(out[d]['status'], 'pass', out[d])


if __name__ == '__main__':
    unittest.main(verbosity=2)
