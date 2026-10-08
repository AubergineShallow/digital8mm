# SPDX-License-Identifier: MIT
"""grip_small owner self-test (not a release check): build printed_grip + printed_small on their own and report
validity, volume, mass, bbox vs envelope, print-pose dims vs both beds, keep-out and COTS-box overlaps, the local
pair interferences and the base_on / cap_on insertion sweeps (r2 R2: the skirts are eliminated). Writes out/grip_small_test.json.

  .venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/test_grip_small.py [part ...]
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import cadquery as cq  # noqa: E402

import d2_common as dc  # noqa: E402
import layout as L  # noqa: E402
import printed_grip  # noqa: E402
import printed_small  # noqa: E402

V = cq.Vector


def inter(a, b):
    try:
        return round(a.intersect(b).Volume(), 3)
    except Exception as e:  # noqa: BLE001
        return 'error: %s' % e


def main(only):
    res, parts = dict(parts={}, pairs={}, sweeps={}), {}
    mates = {frozenset((a, b)) for a, b, _ in L.MATES}
    for mod in (printed_grip, printed_small):
        for pid in mod._BUILDERS:
            if only and pid not in only:
                continue
            t = time.time()
            wp = mod.build_part(L, pid)
            s = wp.val()
            parts[pid] = s
            bb = s.BoundingBox()
            env = L.PARTS[pid]['envelope']
            lo = dict(x=bb.xmin, y=bb.ymin, z=bb.zmin)
            hi = dict(x=bb.xmax, y=bb.ymax, z=bb.zmax)
            over = {k: round(max(env[k][0] - lo[k], hi[k] - env[k][1], 0.0), 3) for k in 'xyz'}
            fd = mod.PRINT[pid]['face_down']
            pb = dc.to_print_pose(s, fd).BoundingBox()
            dims = (round(pb.xlen, 2), round(pb.ylen, 2), round(pb.zlen, 2))
            beds = {n.split()[0]: bool(((dims[0] <= X and dims[1] <= Y) or (dims[0] <= Y and dims[1] <= X)) and dims[2] <= Z)
                    for n, (X, Y, Z) in L.PRINT_BEDS.items()}
            ko = {}
            for kid, kb in L.KEEPOUTS.items():
                if L.boxes_overlap(env, kb):
                    v = inter(s, dc.box_solid(kb))
                    if v != 0.0:
                        ko[kid] = v
            cots = {}
            for cid, c in L.COTS.items():
                if c.get('box') and L.boxes_overlap(env, c['box']):
                    v = inter(s, dc.box_solid(c['box']))
                    if v != 0.0:
                        cots[cid] = dict(v=v, mate=frozenset((pid, cid)) in mates)
            vol = s.Volume()
            res['parts'][pid] = dict(
                valid=s.isValid(), solids=len(wp.solids().vals()), volume_mm3=round(vol, 1),
                mass_g=round(L.mass_g(vol, pid), 1), mass_g_100pct=round(vol * (L.TPU_DENSITY if pid == 'eyecup' else L.FDM['ASA_DENSITY']), 1),
                bbox=[round(v, 3) for v in (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)],
                envelope_overflow=over, face_down=fd, print_dims=dims, beds=beds, keepout_overlap=ko,
                cots_box_overlap=cots, s=round(time.time() - t, 1))
            print(pid, res['parts'][pid])
    probes = {   # (point, expected inside) feature probes
        'base_grip': [((-47, 0, -60), False, 'bay'), ((-47, 13.75, -60), True, 'side wall'),
                      ((-25.0, 4, -32), True, 'front wall behind pad'), ((-26.0, 0, -33), True, 'pad boss'),
                      ((-24.0, 0, -21), False, 'run hole'), ((-24.0, 0, -29.5), False, 'teardrop roof'),
                      ((-30, 10, -28.3), True, 'shelf'), ((-36, 10, -22), True, 'rear stop'),
                      ((-33, 7.0, -26), True, 'side guide'), ((-13, 15, -2.7), False, 'tongue_f pocket'),
                      ((-18, 16, -0.8), True, 'tongue_f lip'), ((-8, 16, -0.8), False, 'tongue_f window'),
                      ((-91, 27.85, -5), False, 's_b1 cbore'), ((-91, 27.85, -1), False, 's_b1 hole'),
                      ((-91, 30.35, -1), True, 's_b1 head seat'), ((-107, 0, -3), False, 'nut pocket'),
                      ((-107, 4.5, -7), True, 'nut bearing wall'), ((-50, 34.5, -4.2), True, 'base side L (no groove, r2)'),
                      ((-50, 34.5, -7.5), True, 'under groove L'), ((-50, -34.5, -4.2), True, 'base side R (no groove, r2)'),
                      ((-45, 13.0, -107), False, 'cap groove'), ((-45, 14.3, -107), True, 'behind cap groove'),
                      ((-45, 12.8, -109.2), True, 'cap groove lip'), ((-30, 0, -5), False, 'base opening'),
                      ((-40, 2, -5), True, 'base over rear stop'), ((-76.5, -27, -4), False, 'strap slot'),
                      ((-79.25, -27, -1), False, 'strap recess'), ((-70, -7, -100.5), True, 'heel strap bar'),
                      ((-70, -7, -104), False, 'heel strap slot'), ((-47, 15.5, -8.3), True, 'web fillet')],
        'cap': [((-45, 0, -114), True, 'floor'), ((-45, 0, -111), False, 'pocket'), ((-45, 11.4, -108), True, 'key web'),
                ((-45, 12.8, -107.0), True, 'key head'), ((-66, 0, -115.8), False, 'thumb groove')],
    }
    res['probes'] = {}
    for pid, lst in probes.items():
        if pid in parts:
            bad = [(lab, pt, exp) for pt, exp, lab in lst if parts[pid].isInside(V(*pt)) != exp]
            res['probes'][pid] = dict(n=len(lst), failed=bad)
    print('probes', res['probes'])
    b = parts.get('base_grip')
    if b is not None:
        for pid in ('skirt_l', 'skirt_r', 'cap'):
            if pid in parts:
                res['pairs']['base_grip/' + pid] = inter(b, parts[pid])
        for t in L.TONGUES:
            tg = dc.keyhole_tongue(t)
            res['pairs']['base_grip/' + t['id']] = inter(b, tg)
            sw = []
            for d in ((-10, 0, -15), (-10, 0, -6), (-10, 0, -2), (-10, 0, 0), (-7, 0, 0), (-4, 0, 0), (-1, 0, 0)):
                sw.append((d, inter(b.translate(V(*d)), tg)))
            res['sweeps']['base_on/' + t['id']] = sw
        if 'cap' in parts:
            res['sweeps']['cap_on'] = [(dx, inter(b, parts['cap'].translate(V(dx, 0, 0))))
                                       for dx in (52.0, 40.0, 25.0, 12.0, 4.0, 1.0)]
        for pid in ('skirt_l', 'skirt_r'):
            if pid in parts:
                res['sweeps'][pid] = [(dx, inter(b, parts[pid].translate(V(dx, 0, 0))))
                                      for dx in (-60.0, -10.0, -4.0, -2.0, -1.0)]
    if os.environ.get('GS_PAIRS'):          # optional: against the other owners' modules that exist now
        import importlib.util
        others = {}
        for fn in ('printed_tub.py', 'printed_hood.py', 'printed_panel.py'):
            path = os.path.join(HERE, fn)
            if os.path.exists(path):
                spec = importlib.util.spec_from_file_location(fn[:-3], path)
                m = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(m)
                for oid, owp in m.build(L).items():
                    others[oid] = owp.val()
        for pid, s in parts.items():
            for oid, o in others.items():
                if L.boxes_overlap(L.PARTS[pid]['envelope'], L.PARTS[oid]['envelope'], -1.0):
                    res['pairs']['%s/%s' % (pid, oid)] = inter(s, o)
        if 'panel' in others and 'skirt_l' in parts:
            res['sweeps']['panel_on_vs_skirt_l'] = [(dy, inter(parts['skirt_l'], others['panel'].translate(V(0, dy, 0))))
                                                    for dy in (12.0, 6.0, 3.0, 1.0, 0.0)]
            # option (a): skirt_l slides +X into the base AFTER the panel (step 8)
            res['sweeps']['skirt_l_after_panel'] = [
                (dx, inter(parts['skirt_l'].translate(V(dx, 0, 0)), others['panel'].fuse(others.get('hood', others['panel']))))
                for dx in (-150.0, -100.0, -50.0, -20.0, -5.0, 0.0)]
    print('pairs', res['pairs'])
    print('sweeps', res['sweeps'])
    print('notes', dc.NOTES)
    res['notes'] = dc.NOTES
    os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
    with open(os.path.join(HERE, 'out', 'grip_small_test.json'), 'w') as f:
        json.dump(res, f, indent=1, default=str)


if __name__ == '__main__':
    main(sys.argv[1:])
