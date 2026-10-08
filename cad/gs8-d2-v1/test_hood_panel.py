# SPDX-License-Identifier: MIT
"""Owner test of printed_hood.py + printed_panel.py (hood_panel owner). Run through the lock:
    .venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/test_hood_panel.py [hood|panel]
Reports per part: validity, solid count, volume, mass (layout.mass_g), bbox vs envelope, print-pose dims and bed fit,
overlap volume with every keep-out and every non-mate COTS box, hood/panel overlap. Writes out/test_hood_panel.json."""
import importlib
import json
import os
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import cadquery as cq  # noqa: E402

import layout as L  # noqa: E402
import d2_common as dc  # noqa: E402

which = sys.argv[1:] or ['hood', 'panel']
MOD = {'hood': 'printed_hood', 'panel': 'printed_panel'}
mates = {(a, b) for a, b, _ in L.MATES} | {(b, a) for a, b, _ in L.MATES}


def ovl(a, b):
    try:
        return a.intersect(b).Volume()
    except Exception:  # noqa: BLE001
        return -1.0


res, shapes = {}, {}
for pid in which:
    t = time.time()
    r = dict(part=pid)
    try:
        m = importlib.import_module(MOD[pid])
        wp = m.build_part(L, pid)
        s = wp.val()
        shapes[pid] = s
        bb = s.BoundingBox()
        env = L.PARTS[pid]['envelope']
        r.update(valid=s.isValid(), solids=len(wp.solids().vals()), volume_mm3=round(s.Volume(), 1),
                 mass_g=round(L.mass_g(s.Volume(), pid), 1), face_down=m.PRINT[pid]['face_down'],
                 bbox=[round(v, 3) for v in (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)],
                 envelope=[env['x'][0], env['x'][1], env['y'][0], env['y'][1], env['z'][0], env['z'][1]])
        r['outside_envelope'] = {k: round(d, 3) for k, d in (
            ('x-', env['x'][0] - bb.xmin), ('x+', bb.xmax - env['x'][1]), ('y-', env['y'][0] - bb.ymin),
            ('y+', bb.ymax - env['y'][1]), ('z-', env['z'][0] - bb.zmin), ('z+', bb.zmax - env['z'][1])) if d > 1e-3}
        pp = dc.to_print_pose(s, m.PRINT[pid]['face_down']).BoundingBox()
        dims = (round(pp.xlen, 2), round(pp.ylen, 2), round(pp.zlen, 2))
        r['print_dims'] = dims
        r['bed_fit'] = {k: (dims[0] <= X and dims[1] <= Y or dims[0] <= Y and dims[1] <= X) and dims[2] <= Z
                        for k, (X, Y, Z) in L.PRINT_BEDS.items()}
        r['keepout_overlap'] = {k: round(v, 3) for k, v in
                                ((k, ovl(s, dc.box_solid(b))) for k, b in L.KEEPOUTS.items()) if abs(v) > 1e-3}
        r['cots_box_overlap'] = {k: round(v, 3) for k, v in
                                 ((k, ovl(s, dc.box_solid(c['box']))) for k, c in L.COTS.items()
                                  if c.get('box') and (pid, k) not in mates) if abs(v) > 1e-3}
        r['notes'] = list(getattr(m, 'NOTES', []))
    except Exception as e:  # noqa: BLE001
        r.update(error='%s: %s' % (type(e).__name__, e), trace=traceback.format_exc()[-1500:])
    r['s'] = round(time.time() - t, 1)
    res[pid] = r
if len(shapes) == 2:
    res['hood_panel_overlap_mm3'] = round(ovl(shapes['hood'], shapes['panel']), 4)
    # panel_on (step 8): the panel moves -Y from +70 with the hood in place; 1 mm steps
    sw = [round(ovl(shapes['hood'], shapes['panel'].translate(cq.Vector(0, d, 0))), 4) for d in range(1, 71)]
    res['panel_on_sweep_vs_hood_max_mm3'] = max(sw)
if 'hood' in shapes:
    # hood_on (step 5): the hood drops -Z with the plunger (stem + flange) already in the front-wall hole
    pl = dc.fuse_all([dc.box_solid(L.PLUNGER['stem']), dc.box_solid(L.PLUNGER['flange'])])
    sw = [round(ovl(shapes['hood'].translate(cq.Vector(0, 0, d)), pl), 4) for d in range(0, 61, 2)]
    res['hood_on_sweep_vs_plunger_max_mm3'] = max(sw)
    # eyepiece_in (step 6): barrel + spigot move +X from -30 through the housing
    ep = dc.fuse_all([dc.cyl_solid(L.EVF['barrel']), dc.cyl_solid(L.EVF['spigot'])])
    sw = [round(ovl(shapes['hood'], ep.translate(cq.Vector(-d, 0, 0))), 4) for d in range(0, 31, 2)]
    res['eyepiece_in_sweep_vs_hood_max_mm3'] = max(sw)
    # r5 (J7-R): r4's ring / cs_ring / c_adapter cylinders (wrong camera model) are replaced by the real proxies: the
    # BFAR and camera body at s 0 / nominal / max, the C-CS adapter and both lenses: 0 mm3 against the hood.
    import math
    import cots
    h = shapes['hood']
    r5 = {}
    bb = h.BoundingBox()
    r5['no_turret'] = dict(hood_xmax=round(bb.xmax, 3), ok=bb.xmax <= L.HOOD_BOX['x'][1] + 1e-3 and bb.xmax <= 1.0 + 1e-3)
    sv = (L.CAM['s_range'][0], L.CAM['s_nom'], L.CAM['s_range'][1])
    cam = {s: cots.gs_camera_parts(L, s) for s in sv}
    solids = {'adapter': cots.c_cs_adapter(L, None)}
    solids.update({'lens_' + n: cots.lens_proxy(L, n)[0] for n in L.LENSES})
    solids.update({'%s_s%s' % (k, s): cam[s][k] for s in sv for k in ('bfar', 'body')})
    r5['proxies_vs_hood_mm3'] = {k: round(ovl(h, v), 4) for k, v in solids.items()}
    r5['proxies_ok'] = not any(r5['proxies_vs_hood_mm3'].values())
    r5['roll_fin_to_cover'] = {str(s): round(h.distance(cam[s]['body']), 3) for s in sv}
    r5['roll_fin_ok'] = min(r5['roll_fin_to_cover'].values()) >= 0.6
    # foot-hole rings: point-in-solid rays in the plate (x -0.1 and -2.4), 36 directions, 0.05 steps; ring >= 1.2
    hr = L.HOOD['foot_holes']['d'] / 2
    rings = {}
    for k, (y0, z0) in L.COLLAR['feet'].items():
        loc = h.intersect(dc.box_solid(L.B(-2.7, 0.2, y0 - 14.0, y0 + 14.0, z0 - 14.0, z0 + 14.0)))
        best = 99.0
        for x in (-0.1, -2.4):
            for j in range(36):
                a = 2 * math.pi * j / 36
                t, st = hr - 0.6, None
                while t < hr + 8.0:
                    isin = loc.isInside(cq.Vector(x, y0 + math.cos(a) * t, z0 + math.sin(a) * t), 1e-4)
                    if isin and st is None:
                        st = t
                    elif st is not None and not isin:
                        best = min(best, t - st)
                        break
                    t += 0.05
        rings[k] = round(best, 2)
    r5['foot_hole_rings_mm'] = rings
    r5['foot_hole_rings_ok'] = min(rings.values()) >= L.HOOD['foot_holes']['ring_min'] - 0.05
    res['r5_hood'] = r5
if 'panel' in shapes:      # r5: keeper finger = rear catch, >= 0.5 behind the cover at s 0 and s_max
    import cots
    kp = {str(s): round(shapes['panel'].distance(cots.gs_camera_parts(L, s)['body']), 3)
          for s in (L.CAM['s_range'][0], L.CAM['s_nom'], L.CAM['s_range'][1])}
    res['r5_panel'] = dict(keeper_to_cover=kp, ok=min(kp.values()) >= 0.5 - 1e-3)
os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
with open(os.path.join(HERE, 'out', 'test_hood_panel_%s.json' % '_'.join(which)), 'w', encoding='utf-8') as f:
    json.dump(res, f, indent=1)
print(json.dumps(res, indent=1))
for pid in which:
    if pid in shapes and len(sys.argv) > 2:
        cq.exporters.export(cq.Workplane().add(dc.to_print_pose(shapes[pid], res[pid]['face_down'])),
                            os.path.join(HERE, 'out', 'owner_%s.stl' % pid))
# r5: exit 1 if an r5 row fails (hood: no turret, proxies 0 mm3, fin >= 0.6, rings >= 1.2; panel: keeper >= 0.5) or a
# part failed to build
_r5h = res.get('r5_hood')
_bad = [pid for pid in which if 'error' in res.get(pid, {})]
if _r5h is not None and not (_r5h['no_turret']['ok'] and _r5h['proxies_ok'] and _r5h['roll_fin_ok'] and
                             _r5h['foot_hole_rings_ok']):
    _bad.append('r5_hood')
if 'r5_panel' in res and not res['r5_panel']['ok']:
    _bad.append('r5_panel')
print('R5 HOOD/PANEL', 'FAIL ' + ', '.join(_bad) if _bad else 'PASS')
sys.exit(1 if _bad else 0)
