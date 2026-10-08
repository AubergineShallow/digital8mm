# SPDX-License-Identifier: MIT
"""FR keeper (fr-keeper role) stand-alone probe of the FR1 keyed-seat keeper with the tub and the COTS proxies.
Run through ../run_locked.py with D2_FR=keeper (or none for the region baseline). Writes
out/_keeper-probe/test_fr_keeper-<FR>.json (a working file, not a release output). Computed CAD only; nothing printed.
Covers: solids/envelope/bed, keeper pairs + seat-region occupancy (what else is in the seat volume), keep-outs,
sweeps pi_in + keeper_in, driver audit of the keeper screws, removals keeper_out + pi_out, tongue-in-seat gaps, the
boss audit and the tub/keeper CRITICAL_FEATURES (with FR_JOINTS required ids)."""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import layout as L  # noqa: E402
import d2_common as dc  # noqa: E402
import build_d2 as B  # noqa: E402
import checks as C  # noqa: E402

SEAT = L.B(-106.85, -95.15, -32.45, -27.0, 2.55, 18.75)      # FR seat volume above the floor / off the right wall
t0 = time.time()
rows = dict(B.build_cots())
for pid in ('tub', 'pi_keeper'):
    rows.update(B.build_printed(only=pid)[0])
res = dict(fr=L.FR_STATE, build_s=round(time.time() - t0, 1))
for pid in ('tub', 'pi_keeper'):
    s = rows[pid]['shape']
    bb = s.BoundingBox()
    env = L.PARTS[pid]['envelope']
    res[pid] = dict(valid=s.isValid(), volume_mm3=round(s.Volume(), 1), mass_g=round(L.mass_g(s.Volume(), pid), 2),
                    bbox=[round(v, 3) for v in (bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax)],
                    in_envelope=all((bb.xmin >= env['x'][0] - 1e-3, bb.xmax <= env['x'][1] + 1e-3,
                                     bb.ymin >= env['y'][0] - 1e-3, bb.ymax <= env['y'][1] + 1e-3,
                                     bb.zmin >= env['z'][0] - 1e-3, bb.zmax <= env['z'][1] + 1e-3)),
                    bed=C.check_bed(L, pid, dc.to_print_pose(s, L.PARTS[pid]['face_down'])))
seat = dc.box_solid(SEAT)
res['seat_region'] = {o: round(C.common(r['shape'], seat)[0], 3) for o, r in rows.items()
                      if r.get('shape') is not None and C.common(r['shape'], seat)[0] > 1e-6}
res['seat_region_keepouts'] = [k for k, b in L.KEEPOUTS.items() if C.common(seat, dc.box_solid(b))[0] > 1e-6]
res['seat_region_gaps'] = {}
for o in ('x1203', 'x1203_kit', 'pi5', 'cooler'):
    if o in rows:
        res['seat_region_gaps'][o] = round(seat.distance(rows[o]['shape']), 3)
k = rows['pi_keeper']['shape']
pairs = {}
for o in ('tub', 'x1203', 'x1203_kit', 'pi5', 'cooler', 's_k1', 's_k2'):
    sh = rows.get(o, {}).get('shape')
    if sh is None:
        continue
    v, _ = C.common(k, sh)
    pairs[o] = dict(overlap_mm3=round(v, 4), gap_mm=round(k.distance(sh), 3))
res['keeper_pairs'] = pairs
if L.FR['keeper']:                                  # tongue-in-seat gaps (x sides, z jaws, tip): local boxes
    P = L.PI_KEEPER['pocket']
    tub_loc = rows['tub']['shape'].intersect(dc.box_solid(L.B(-108, -94, -31, -26, 2.6, 18.7)))
    tg = k.intersect(dc.box_solid(L.B(-106, -96, -30.5, -26.5, 9.0, 16.0)))
    res['tongue_seat_min_gap'] = round(tg.distance(tub_loc), 3)
    res['tongue_seat_overlap'] = round(C.common(tg, tub_loc)[0], 4)
res['keeper_keepout_overlaps'] = {kid: round(C.common(k, dc.box_solid(b))[0], 4) for kid, b in L.KEEPOUTS.items()
                                  if C.common(k, dc.box_solid(b))[0] > 1e-6}
res['tub_pi_pairs'] = {o: round(C.common(rows['tub']['shape'], rows[o]['shape'])[0], 4)
                       for o in ('x1203', 'x1203_kit', 'pi5', 'cooler') if o in rows}
kids = [s['id'] for s in L.SCREWS if 'pi_keeper' in s['joins']]
keep = [i for i in L.INSERTIONS if i['id'] in ('pi_in', 'keeper_in')]
saved = L.INSERTIONS[:]
L.INSERTIONS[:] = keep
res['insertions'] = C.check_sweeps(L, rows, step_mm=1.0)
L.INSERTIONS[:] = saved
res['driver_step4'] = C.check_driver(L, rows, screw_ids=kids)
mine = [r for r in L.REMOVALS if r['id'] in ('keeper_out', 'pi_out')]
saved_r = L.REMOVALS[:]
L.REMOVALS[:] = mine
try:
    res['removals'], res['service_driver'] = C.check_removals(L, rows, step_mm=1.0)
except Exception as e:  # noqa: BLE001
    res['removals'], res['service_driver'] = 'error: %s' % e, []
L.REMOVALS[:] = saved_r
res['bosses'] = [b for b in C.check_bosses(L, rows) if b['screw'] in kids]
crit = C.check_critical_features(L, rows)
res['critical'] = [x for x in crit if x.get('part') in ('tub', 'pi_keeper')]
req = [i for j in getattr(L, 'FR_JOINTS', []) if j['id'].startswith('J9') for i in j['required']]
got = {x.get('id'): x.get('status') for x in res['critical']}
res['fr_joint_required'] = {i: got.get(i, 'MISSING') for i in req}
res['total_s'] = round(time.time() - t0, 1)
od = os.path.join(HERE, 'out', '_keeper-probe')
os.makedirs(od, exist_ok=True)
tag = 'keeper' if L.FR['keeper'] else 'none'
with open(os.path.join(od, 'test_fr_keeper-%s.json' % tag), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(res, f, indent=1, default=str)
for k2 in ('fr', 'build_s', 'tub', 'pi_keeper', 'seat_region', 'seat_region_keepouts', 'seat_region_gaps',
           'keeper_pairs', 'tongue_seat_min_gap', 'tongue_seat_overlap', 'keeper_keepout_overlaps', 'tub_pi_pairs'):
    print(k2, json.dumps(res.get(k2), default=str))
for x in res['insertions']:
    print('INS', x['insertion'], x['status'], [(h['moving'], h['obstacle'], h['max_volume_mm3'], h['at_offset'])
                                               for h in x['hits']], x['errors'][:2])
for x in res['driver_step4']:
    print('DRV', x['screw'], x['status'], x['hits'], x['nearest'])
if isinstance(res['removals'], str):
    print('REM', res['removals'])
else:
    for x in res['removals'] + res['service_driver']:
        print('REM', x.get('removal', x.get('screw')), x['status'], x.get('hits'), x.get('errors', ''))
for b in res['bosses']:
    print('BOSS', b.get('screw'), b.get('status'), {kk: v for kk, v in b.items() if 'mm' in kk})
for x in res['critical']:
    print('CRIT %-6s %-28s %s %s' % (x['status'], x.get('id', ''), x.get('measured_mm', x.get('values')),
                                     x.get('error') or ''))
print('REQ', res['fr_joint_required'])
print('total', res['total_s'], 's')
