# SPDX-License-Identifier: MIT
"""r7 C4 (BX-4) planted-fault regressions for the hood tab catch and check_roll_catch (SPEC-C4 4.4, cases 1-10 and
13; 11 = BX-15 and 12 = BX-8 come with those sub-steps). Style of test_r3_regressions.py: each case copies the layout
into a namespace with one planted fault and asserts the named failure channel; case 13 is the positive control on
the real layout. The hood is rebuilt in-process from the current layout; every other printed part comes from the
release STEPs in out/step/parts (the camera region does not depend on the other r7 clusters), COTS from
build_d2.build_cots(). Planted hoods replace the tines by plain tab_catch_boxes() of the faulted layout (no
chamfers): they test the checker's channels, not the tine detail. Fault runs use s = 0 only (the release build runs
the full j7_s_values set); the positive control uses s 0 / s_nom / s_max.

Run (repo root): python3 cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/test_r7_c4.py [--out FILE.json]
"""
import copy
import json
import os
import sys
import time
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import cadquery as cq  # noqa: E402

import build_d2 as B  # noqa: E402
import checks as CK  # noqa: E402
import layout as L  # noqa: E402

T0 = time.time()
RES = {}
FAIL = []


def log(*a):
    print('[test_r7_c4 %6.1f s]' % (time.time() - T0), *a, flush=True)


def lay(**over):
    """The layout as a namespace with some attributes replaced (functions keep reading the module where they must)."""
    ns = SimpleNamespace(**{k: getattr(L, k) for k in dir(L) if not k.startswith('__')})
    for k, v in over.items():
        setattr(ns, k, v)
    return ns


def hood_dict(**tc):
    h = copy.deepcopy(L.HOOD)
    if tc.get('_remove'):
        h.pop('tab_catch', None)
    else:
        h['tab_catch'].update(tc)
    return h


def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def load_rows():
    rows = dict(B.build_cots())
    sd = os.path.join(HERE, 'out', 'step', 'parts')
    for pid in L.PARTS:
        pth = os.path.join(sd, pid + '.step')
        if pid == 'hood' or not os.path.exists(pth):
            rows[pid] = B.build_printed(only=pid)[0][pid]
        else:
            sh = B.as_shape(cq.importers.importStep(pth))
            rows[pid] = dict(shape=sh, kind='printed', stub=False, module=L.PARTS[pid]['module'], print={})
    return rows


def tine_zone():
    """Solids covering the real tines, their lead-in and both root gussets (cut them out of the hood)."""
    tc, out = L.HOOD['tab_catch'], []
    for b in L.tab_catch_boxes(L):
        out.append(box(b['x'][0] - 0.05, b['x'][1] + 0.05, b['y'][0] - 0.05, b['y'][1] + 0.05, b['z'][0] - 0.05,
                       L.ZT1 - 1e-3))
        if b['kind'] == 'web':
            yi = b['side'] * b['y_in']
            yo = b['side'] * (b['y_in'] + tc['t'])
            for y0, y1 in (sorted((yi, yi - b['side'] * (tc['root_chamfer'] + 0.05))),
                           sorted((yo, yo + b['side'] * (tc['root_chamfer'] + 0.05)))):
                out.append(box(b['x'][0] - 0.05, b['x'][1] + 0.05, y0, y1, L.ZT1 - tc['root_chamfer'] - 0.05,
                               L.ZT1 - 1e-3))
    return out


def hood_variant(rows, Lx):
    h = rows['hood']['shape']
    for z in tine_zone():
        h = h.cut(z)
    try:
        bx = Lx.tab_catch_boxes(Lx)
    except ValueError:
        bx = []
    for b in bx:
        h = h.fuse(box(b['x'][0], b['x'][1], b['y'][0], b['y'][1], b['z'][0], b['z'][1]))
    return dict(rows, hood=dict(rows['hood'], shape=h.clean()))


def items(res, item):
    return [r for r in res if r.get('item') == item]


def case(name, fn):
    t = time.time()
    try:
        ok, info = fn()
    except Exception as e:  # noqa: BLE001
        import traceback
        ok, info = False, 'raised: %s\n%s' % (e, traceback.format_exc(limit=4))
    RES[name] = dict(ok=bool(ok), info=info, seconds=round(time.time() - t, 1))
    log('%-44s %s %s' % (name, 'PASS' if ok else 'FAIL', '' if ok else str(info)[:300]))
    if not ok:
        FAIL.append(name)


S0 = (0.0,)


def main():
    out_path = os.path.join(HERE, 'out', 'test_r7_c4.json')
    if '--out' in sys.argv:
        out_path = sys.argv[sys.argv.index('--out') + 1]
    rows = load_rows()
    log('rows loaded (%d)' % len(rows))

    def c1():   # r6 roll fin + webs back on the hood: PCB/cover meets the hood before metal
        fin = [box(-23.5, -19.5, -22.8, -20.55, 41.0, L.ZT1 + 0.5), box(-23.5, -19.5, -27.6, -22.8, 44.5, 48.5),
               box(-23.5, -19.5, -27.6, -22.8, 75.0, 79.0)]
        h = rows['hood']['shape']
        for f in fin:
            h = h.fuse(f)
        res = CK.check_roll_catch(L, dict(rows, hood=dict(rows['hood'], shape=h)), s_values=S0)
        fc = items(res, 'first_contact')
        hits = [c['pcb_cover_deg'] for r in fc for c in r['cases'] if 'hood' in c['pcb_cover_to']]
        return (any(r['status'] == 'fail' for r in fc) and hits and min(hits) < 1.0,
                dict(pcb_cover_on_hood_min_deg=min(hits) if hits else None, spec=0.70))

    def c2():   # tab catch removed: no metal catch within scan_deg; PCB/cover first at the cooler box
        L2 = lay(HOOD=hood_dict(_remove=True))
        res = CK.check_roll_catch(L2, hood_variant(rows, L2), s_values=S0)
        fc = items(res, 'first_contact')
        err = ' '.join(r.get('error', '') for r in fc)
        pc = [c['pcb_cover_deg'] for r in fc for c in r['cases'] if 'box:cooler' in c['pcb_cover_to']]
        geo = items(res, 'tab_catch_geometry')[0]['status']
        return ('no metal catch within' in err and geo == 'fail' and pc,
                dict(cooler_box_min_deg=min(pc) if pc else None, spec=10.22, geometry_row=geo))

    def c3():   # gap 0.5: the level window at the worst offset < J7_RUNNING
        L3 = lay(HOOD=hood_dict(gap=0.5))
        res = CK.check_roll_catch(L3, hood_variant(rows, L3), s_values=S0)
        w = items(res, 'window')
        return (all(r['status'] == 'fail' for r in w) and min(r['worst_gap'] for r in w) < CK.J7_RUNNING,
                dict(worst_gap=[r['worst_gap'] for r in w]))

    def c4():   # gap 0.4: j7_float body lateral < 0.5 to the hood
        L4 = lay(HOOD=hood_dict(gap=0.4))
        res = CK.check_j7_float(L4, hood_variant(rows, L4), s_values=S0)
        bad = [r for r in res if r.get('mover') == 'body' and r['status'] == 'fail'
               and 'hood' in r.get('offending_obstacles', [])]
        return bool(bad), dict(min_lateral=[r.get('min_lateral') for r in bad])

    def sweep_fail(Lx, only, ins_id, obstacle):
        res = CK.check_sweeps(Lx, hood_variant(rows, Lx), step_mm=2.0, only=only)
        r = next(x for x in res if x.get('insertion') == ins_id)
        names = json.dumps(r.get('hits', [])) + json.dumps(r.get('errors', []))
        return r['status'] == 'fail' and obstacle in names, dict(status=r['status'], hits=str(r.get('hits'))[:300])

    def c5():   # tine x (-16.0, -8.2): camera_in (BFAR head / PCB at the entry offset) meets the hood
        return sweep_fail(lay(HOOD=hood_dict(x=(-16.0, -8.2))), 'gs_camera', 'camera_in', 'hood')

    def c6():   # z0 76.5: camera_in (adapter in the 2 mm-high traverse) meets the hood
        return sweep_fail(lay(HOOD=hood_dict(z0=76.5)), 'gs_camera', 'camera_in', 'hood')

    def c7():   # tine x (-14.5, -7.5): hood_on meets the TL/TR tub insert bosses
        return sweep_fail(lay(HOOD=hood_dict(x=(-14.5, -7.5))), 'hood', 'hood_on', 'tub')

    def c8():   # cooler box 1 mm taller: the one-head variants fail; the declared row still passes
        cots_ = copy.deepcopy(L.COTS)
        b = cots_['cooler']['box']
        b['z'] = (b['z'][0], b['z'][1] + 1.0)
        res = CK.check_roll_catch(lay(COTS=cots_), rows, s_values=S0)
        un = items(res, 'first_contact_unconfirmed')
        dec = items(res, 'first_contact')
        pc = [c['pcb_cover_deg'] for r in un for c in r['cases'] if 'box:cooler' in c['pcb_cover_to']]
        return (any(r['status'] == 'fail' for r in un) and all(r['status'] == 'pass' for r in dec) and pc,
                dict(cooler_box_min_deg=min(pc) if pc else None, spec_about=6.4,
                     declared=[r['status'] for r in dec]))

    def c9():   # head_side '+Y' without bare_y: tab_catch_boxes raises, the geometry row fails
        L9 = lay(HOOD=hood_dict(head_side='+Y', bare_y=None))
        try:
            L9.tab_catch_boxes(L9)
            raised = False
        except ValueError:
            raised = True
        res = CK.check_roll_catch(L9, rows, s_values=S0)
        geo = items(res, 'tab_catch_geometry')[0]
        return raised and geo['status'] == 'fail', dict(raised=raised, row=geo.get('error'))

    def c10():  # hold deleted from lens_in; LATCH_FREE['lens'] back to the r5 text: lens_hold + lint fail
        ins = [dict(i) for i in L.INSERTIONS]
        for i in ins:
            if i['id'] == 'lens_in':
                i.pop('hold', None)
        lf = dict(L.LATCH_FREE)
        lf['lens'] = ('r5: loosen s_c4 one turn (straight PH1 from above), unscrew the lens by hand (the camera turns '
                      'with it until its cover meets the hood roll fin; with the panel off, hold the cover)')
        res = CK.check_roll_catch(lay(INSERTIONS=ins, LATCH_FREE=lf), rows, s_values=S0)
        lh = {r.get('record'): r for r in items(res, 'lens_hold')}
        lint = items(res, 'lens_hold_lint')[0]
        return (lh['lens_in']['status'] == 'fail' and 'no hold' in lh['lens_in'].get('error', '')
                and lh['lens_off']['status'] == 'pass' and lint['status'] == 'fail'
                and 'cover meets' in lint.get('error', '') and 'LATCH_FREE[lens]' in lint.get('error', ''),
                dict(lens_in=lh['lens_in'].get('error'), lint=lint.get('error')))

    def c13():  # positive control: every row passes; centred first contact 3.22 +-0.05 deg
        sv = (L.CAM['s_range'][0], L.CAM['s_nom'], L.CAM['s_range'][1])
        res = CK.check_roll_catch(L, rows, s_values=sv)
        bad = [r for r in res if r['status'] not in ('pass', 'info')]
        cen = [r['centred_deg'] for r in items(res, 'first_contact')]
        tim = items(res, 'timing')[0]
        return (not bad and cen and all(abs(c - 3.22) <= 0.05 for c in cen),
                dict(failing=[(r.get('item'), r.get('error')) for r in bad][:4], centred_deg=cen,
                     window=[(r['centred_gap'], r['worst_gap']) for r in items(res, 'window')],
                     axial=items(res, 'axial_engagement')[0].get('min_overlap'),
                     tine=items(res, 'tine_strength')[0].get('sigma_MPa'), seconds=tim['seconds']))

    for nm, fn in (('13_positive_control', c13), ('1_roll_fin_readded', c1), ('2_tab_catch_removed', c2),
                   ('3_gap_0.5_window', c3), ('4_gap_0.4_j7_float', c4), ('5_tine_x_-16_camera_in', c5),
                   ('6_z0_76.5_camera_in', c6), ('7_tine_x_-7.5_hood_on', c7), ('8_cooler_box_unconfirmed', c8),
                   ('9_head_side_without_bare_y', c9), ('10_lens_hold_and_lint', c10)):
        case(nm, fn)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(dict(cases=RES, failed=FAIL, seconds=round(time.time() - T0, 1)), f, indent=1, default=str)
    print('TEST_R7_C4', 'FAIL ' + ', '.join(FAIL) if FAIL else 'ALL OK (%d cases)' % len(RES))
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())
