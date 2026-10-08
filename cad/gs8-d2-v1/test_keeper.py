# SPDX-License-Identifier: MIT
"""R1 r2 stand-alone check of the Pi keeper (printed_keeper.py) with the tub (printed_tub.py) and the COTS proxies.
Run through run_locked.py. Writes out/_quick/test_keeper.json (a working file, not a release output).

Checks (computed, CAD only; nothing printed or measured): valid single solids, envelopes, bed fit in print pose,
keeper/tub and keeper/COTS overlap and gaps, keep-outs, the step-4 insertions pi_in + keeper_in (and later
insertions that meet the keeper, with the parts built here), the straight-driver audit of s_k1/s_k2 at step 4, the
removals keeper_out + pi_out (service state, with the parts built here) and the R1 CRITICAL_FEATURES entries.
"""
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

t0 = time.time()
rows = dict(B.build_cots())
for pid in ('tub', 'pi_keeper'):
    rows.update(B.build_printed(only=pid)[0])
res = dict(build_s=round(time.time() - t0, 1))
for pid in ('tub', 'pi_keeper'):
    s = rows[pid]['shape']
    bb = s.BoundingBox()
    env = L.PARTS[pid]['envelope']
    pp = dc.to_print_pose(s, L.PARTS[pid]['face_down'])
    res[pid] = dict(valid=s.isValid(), stub=rows[pid].get('stub'), volume_mm3=round(s.Volume(), 1),
                    mass_g=round(L.mass_g(s.Volume(), pid), 1),
                    bbox=[round(v, 3) for v in (bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax)],
                    in_envelope=all((bb.xmin >= env['x'][0] - 1e-3, bb.xmax <= env['x'][1] + 1e-3,
                                     bb.ymin >= env['y'][0] - 1e-3, bb.ymax <= env['y'][1] + 1e-3,
                                     bb.zmin >= env['z'][0] - 1e-3, bb.zmax <= env['z'][1] + 1e-3)),
                    bed=C.check_bed(L, pid, pp))
k = rows['pi_keeper']['shape']
pairs = {}
for o in ('tub', 'x1203', 'x1203_kit', 'pi5', 'cooler', 's_k1', 's_k2'):
    sh = rows.get(o, {}).get('shape')
    if sh is None:
        continue
    v, _ = C.common(k, sh)
    try:
        d = k.distance(sh)
    except Exception as e:  # noqa: BLE001
        d = 'err %s' % e
    pairs[o] = dict(overlap_mm3=round(v, 4), gap_mm=d if isinstance(d, str) else round(d, 3))
res['keeper_pairs'] = pairs
ko = {}
for kid, b in L.KEEPOUTS.items():
    v, _ = C.common(k, dc.box_solid(b))
    if v > 1e-6:
        ko[kid] = round(v, 4)
res['keeper_keepout_overlaps'] = ko
res['tub_pi_pairs'] = {o: round(C.common(rows['tub']['shape'], rows[o]['shape'])[0], 4)
                       for o in ('x1203', 'x1203_kit', 'pi5', 'cooler') if o in rows}
keep = [i for i in L.INSERTIONS if i['id'] in ('pi_in', 'keeper_in')]
saved = L.INSERTIONS[:]
L.INSERTIONS[:] = keep
res['insertions'] = C.check_sweeps(L, rows)
L.INSERTIONS[:] = saved
res['driver_step4'] = C.check_driver(L, rows, screw_ids=['s_k1', 's_k2'])
mine = [r for r in L.REMOVALS if r['id'] in ('keeper_out', 'pi_out')]
saved_r = L.REMOVALS[:]
L.REMOVALS[:] = mine
try:
    res['removals'], res['service_driver'] = C.check_removals(L, rows)
except Exception as e:  # noqa: BLE001
    res['removals'] = 'error: %s' % e
L.REMOVALS[:] = saved_r
res['bosses'] = [b for b in C.check_bosses(L, rows) if b['screw'] in ('s_k1', 's_k2')]
for b in res['bosses']:
    print('BOSS', b)
if '--thin' in sys.argv:
    res['thin_wall'] = {pid: C.thin_wall(L, pid, rows[pid]['shape'], loaded_boxes=C.loaded_boxes(L, pid))
                        for pid in ('pi_keeper', 'tub')}
    for pid, tw in res['thin_wall'].items():
        print('THIN', pid, {k2: v for k2, v in tw.items() if not isinstance(v, (list, dict))})
crit = C.check_critical_features(L, rows)
res['critical'] = [x for x in crit if x.get('part') in ('tub', 'pi_keeper')]
res['notes'] = dc.NOTES
res['total_s'] = round(time.time() - t0, 1)
od = os.path.join(HERE, 'out', '_quick')
os.makedirs(od, exist_ok=True)
with open(os.path.join(od, 'test_keeper.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(res, f, indent=1, default=str)
short = {k2: res[k2] for k2 in ('build_s', 'tub', 'pi_keeper', 'keeper_pairs', 'keeper_keepout_overlaps', 'tub_pi_pairs')}
print(json.dumps(short, indent=1, default=str))
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
for x in res['critical']:
    print('CRIT %-6s %-30s %s %s' % (x['status'], x.get('id', ''), x.get('measured_mm', x.get('structural_entries')),
                                     x.get('error') or ''))
print('total', res['total_s'], 's')
