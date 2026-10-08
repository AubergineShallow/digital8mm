# SPDX-License-Identifier: MIT
"""r5 step 1 (J7-R) owner test of the lens collar (printed_collar.py) with the tub, hood, panel and the COTS proxies.
Run through the lock:  .venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/test_collar.py
Writes out/_quick/test_collar.json (a working file, not a release output). Exit 1 if any row fails.

Checks (computed, CAD only; nothing printed or measured), per lens with a support (Kowa, Fujinon):
  - one valid solid inside the PARTS envelope, bed fit, keep-outs (incl. ko_lens_thumb_*) and non-mate COTS boxes;
  - print pose (face_down +X): no downward face steeper than 45 deg except the bed face, the horizontal washer-seat
    bridges (x 2.8) and the small horizontal s_c4 holes (dia <= 8, round);
  - feet coplanar on the tub face (x -2.7) and their 3.4 holes; cone seat, bore and front per collar_spec;
  - lens vs collar: 0 mm3 and 0.0 gap (cone contact), camera/adapter/tub/hood/panel clearances;
Kowa build (layout.LENS) only: straight-driver audit of s_c1..s_c4 at their steps (parts near J7 built here), the
sweeps camera_in / collar_on / lens_in / panel_on, the removals collar_off / camera_out, J7 CRITICAL_FEATURES.
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cadquery as cq  # noqa: E402
import numpy as np  # noqa: E402
import layout as L  # noqa: E402
import d2_common as dc  # noqa: E402
import build_d2 as B  # noqa: E402
import checks as C  # noqa: E402
import cots  # noqa: E402
import printed_collar as PC  # noqa: E402

V = cq.Vector
t0 = time.time()
res, bad = dict(), []
mates = {frozenset((a, b)) for a, b, _ in L.MATES}
ly, lz = L.LENS_AXIS


def box_ov(s, b):
    return round(s.intersect(dc.box_solid(b)).Volume(), 3)


def overhangs(s, front_x):
    """Downward faces in print (face_down +X: assembly +X is print-down) steeper than 45 deg, classified."""
    vs, ts = s.tessellate(0.02, 0.2)
    P = np.array([(v.x, v.y, v.z) for v in vs])
    T = np.array(ts)
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    area = np.linalg.norm(n, axis=1) / 2
    n = n / np.maximum(np.linalg.norm(n, axis=1)[:, None], 1e-12)
    cen = P[T].mean(axis=1)
    # 45 deg by construction (cone seat, bed chamfer); 1.5 deg allowance for the facet normals of tessellated cones
    down = (n[:, 0] > math.sin(math.radians(46.5))) & (cen[:, 0] < front_x - 0.05)
    s4 = next(x for x in L.SCREWS if x['id'] == 's_c4')['head_point']
    bridge = down & (n[:, 0] > 0.999) & (np.abs(cen[:, 0] - L.COLLAR['flange_x'][1]) < 0.01)
    hole = down & (np.hypot(cen[:, 0] - s4[0], cen[:, 1] - s4[1]) <= L.M3['insert']['bore_d'] / 2 + 0.05)
    other = down & ~bridge & ~hole
    return dict(bridge_mm2=round(float(area[bridge].sum()), 1), small_hole_mm2=round(float(area[hole].sum()), 1),
                other_mm2=round(float(area[other].sum()), 3),
                other_where=[[round(float(v), 1) for v in c] for c in cen[other][:6]])


def radial_hit(s, x, d, r0, r1, step=0.01):
    t = r0
    while t <= r1:
        if s.isInside(V(x, ly + d[0] * t, lz + d[1] * t), 1e-4):
            return round(t, 3)
        t += step
    return None


rows = dict(B.build_cots())
for pid in ('tub', 'hood', 'panel', 'lens_collar'):
    rows.update(B.build_printed(only=pid)[0])
res['build_s'] = round(time.time() - t0, 1)
dirs = [(math.cos(math.radians(a)), math.sin(math.radians(a))) for a in (0, 45, 90, 135, 225, 270, 315)]  # not -Y (slit)
for name in [n for n in L.LENSES if L.LENSES[n].get('support')]:
    cs = L.collar_spec(name)
    s = PC.build_part(L, 'lens_collar', lens=name).val()
    r = dict(spec=cs)
    bb = s.BoundingBox()
    env = L.PARTS['lens_collar']['envelope']
    r['valid'] = s.isValid() and len(s.Solids()) == 1
    r['bbox'] = [round(v, 3) for v in (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)]
    r['in_envelope'] = (bb.xmin >= env['x'][0] - 1e-3 and bb.xmax <= env['x'][1] + 1e-3 and bb.ymin >= env['y'][0] - 1e-3
                        and bb.ymax <= env['y'][1] + 1e-3 and bb.zmin >= env['z'][0] - 1e-3 and bb.zmax <= env['z'][1] + 1e-3)
    r['volume_mm3'] = round(s.Volume(), 1)
    r['mass_g'] = round(L.mass_g(s.Volume(), 'lens_collar'), 1)
    r['bed'] = C.check_bed(L, 'lens_collar', dc.to_print_pose(s, PC.PRINT['lens_collar']['face_down']))
    r['keepouts'] = {k: v for k, v in ((k, box_ov(s, b)) for k, b in L.KEEPOUTS.items()) if v}
    r['cots_boxes'] = {k: v for k, v in ((k, box_ov(s, c['box'])) for k, c in L.COTS.items()
                                         if c.get('box') and frozenset(('lens_collar', k)) not in mates) if v}
    r['print_overhangs'] = overhangs(s, cs['front_x'])
    feet = {}
    for k, (y, z) in L.COLLAR['feet'].items():
        f = s.intersect(dc.box_solid(L.B(-3.0, 0.0, y - 4.0, y + 4.0, z - 4.0, z + 4.0))).BoundingBox()
        hole = (k in L.COLLAR['bolted'] and not s.isInside(V(-1.2, y, z + 1.5), 1e-4)
                and s.isInside(V(-1.2, y, z + 1.9), 1e-4)) or (k not in L.COLLAR['bolted'] and s.isInside(V(-1.2, y, z), 1e-4))
        feet[k] = dict(x0=round(f.xmin, 3), d=round(f.ylen, 3), hole_or_solid_ok=hole)
    r['feet'] = feet
    xb = (cs['cone_x1'] + cs['front_x']) / 2
    r['bore_r'] = [radial_hit(s, xb, d, cs['bore_r'] - 0.5, cs['bore_r'] + 0.5) for d in dirs]
    r['seat_r_at_seat_x'] = [radial_hit(s, cs['seat_x'], d, cs['seat_r'] - 0.5, cs['seat_r'] + 0.5) for d in dirs]
    r['cone_r0'] = [radial_hit(s, (cs['rear_x'] + cs['cone_x0']) / 2, d, cs['cone_r0'] - 0.5, cs['cone_r0'] + 0.5)
                    for d in dirs]
    lens, _ = cots.lens_proxy(L, name)
    r['lens'] = dict(overlap_mm3=round(s.intersect(lens).Volume(), 4), gap=round(s.distance(lens), 3))
    r['thumb_keepout_gap'] = {k: round(s.distance(dc.box_solid(b)), 3) for k, b in L.KEEPOUTS.items()
                              if k.startswith('ko_lens_thumb')}
    others = {k: rows[k]['shape'] for k in ('tub', 'hood', 'panel', 'gs_camera', 'c_cs_adapter') if rows.get(k)}
    r['pairs'] = {k: dict(overlap_mm3=round(s.intersect(o).Volume(), 4), gap=round(s.distance(o), 3))
                  for k, o in others.items()}
    ok = (r['valid'] and r['in_envelope'] and r['bed']['status'] == 'pass' and not r['keepouts'] and not r['cots_boxes']
          and r['print_overhangs']['other_mm2'] <= 0.5
          and all(abs(f['x0'] - L.COLLAR['foot_x'][0]) <= 0.01 and abs(f['d'] - L.COLLAR['foot_d']) <= 0.02
                  and f['hole_or_solid_ok'] for f in feet.values())
          and all(v is not None and abs(v - cs['bore_r']) <= 0.03 for v in r['bore_r'])
          and all(v is not None and abs(v - cs['seat_r']) <= 0.03 for v in r['seat_r_at_seat_x'])
          and all(v is not None and abs(v - cs['cone_r0']) <= 0.03 for v in r['cone_r0'])
          and r['lens']['overlap_mm3'] <= 0.05 and r['lens']['gap'] <= 0.01
          and min(r['thumb_keepout_gap'].values() or [9.9]) > 0.0
          and all(p['overlap_mm3'] <= 0.05 for p in r['pairs'].values())
          and r['pairs']['tub']['gap'] <= 0.01 and r['pairs']['hood']['gap'] >= 0.25
          and r['pairs']['gs_camera']['gap'] >= 0.5 and r['pairs']['c_cs_adapter']['gap'] >= 0.5)
    r['ok'] = bool(ok)
    if not ok:
        bad.append('collar ' + name)
    res[name] = r
    print('COLLAR', name, 'ok' if ok else 'FAIL', json.dumps({k: r[k] for k in ('bbox', 'volume_mm3', 'mass_g', 'feet',
          'print_overhangs', 'lens', 'pairs', 'keepouts', 'cots_boxes')}), flush=True)
# ---- Kowa (layout.LENS) build: driver, sweeps, removals, critical features
drv = C.check_driver(L, rows, screw_ids=['s_c1', 's_c2', 's_c3', 's_c4'])
res['driver'] = drv
keep = [i for i in L.INSERTIONS if i['id'] in ('camera_in', 'collar_on', 'lens_in', 'panel_on')]
saved = L.INSERTIONS[:]
L.INSERTIONS[:] = keep
res['insertions'] = C.check_sweeps(L, rows)
L.INSERTIONS[:] = saved
mine = [r for r in L.REMOVALS if r['id'] in ('collar_off', 'camera_out')]
saved_r = L.REMOVALS[:]
L.REMOVALS[:] = mine
res['removals'], res['service_driver'] = C.check_removals(L, rows)
L.REMOVALS[:] = saved_r
J7 = next(j for j in L.CRITICAL_JOINTS if j['id'] == 'J7_camera')
crit = C.check_critical_features(L, rows)
res['critical_j7'] = [x for x in crit if x.get('id') in J7['required']]
for x in drv:
    print('DRV', x['screw'], x['status'], x['hits'], x['nearest'])
    if x['status'] != 'pass':
        bad.append('driver ' + x['screw'])
for x in res['insertions']:
    print('INS', x['insertion'], x['status'], [(h['moving'], h['obstacle'], h['max_volume_mm3'], h['at_offset'])
                                               for h in x['hits']], x['errors'][:2])
    if x['status'] != 'pass':
        bad.append('sweep ' + x['insertion'])
for x in res['removals'] + res['service_driver']:
    print('REM', x.get('removal', x.get('screw')), x['status'], x.get('hits'), x.get('errors', ''))
    if x['status'] != 'pass':
        bad.append('removal ' + str(x.get('removal', x.get('screw'))))
seen = set()
for x in res['critical_j7']:
    seen.add(x.get('id'))
    print('CRIT %-6s %-24s %s %s' % (x['status'], x.get('id', ''), x.get('measured_mm'), x.get('error') or ''))
    if x['status'] != 'pass':
        bad.append('critical ' + x.get('id', ''))
missing = [i for i in J7['required'] if i not in seen]
if missing:
    bad.append('critical missing ' + ', '.join(missing))
res['notes'] = dc.NOTES + PC.NOTES
res['bad'] = bad
res['total_s'] = round(time.time() - t0, 1)
od = os.path.join(HERE, 'out', '_quick')
os.makedirs(od, exist_ok=True)
with open(os.path.join(od, 'test_collar.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(res, f, indent=1, default=str)
print('R5 COLLAR', 'PASS' if not bad else 'FAIL: ' + '; '.join(bad), res['total_s'], 's')
sys.exit(1 if bad else 0)
