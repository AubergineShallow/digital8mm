# SPDX-License-Identifier: MIT
"""Stand-alone check of printed_tub.py (run through run_locked.py). Writes out/test_tub.json."""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cadquery as cq  # noqa: E402
import layout as L  # noqa: E402
import d2_common as dc  # noqa: E402
import printed_tub as T  # noqa: E402

t0 = time.time()
wp = T.build(L)['tub']
s = wp.val()
tb = time.time() - t0
bb = s.BoundingBox()
env = L.PARTS['tub']['envelope']
vol = s.Volume()
res = dict(valid=s.isValid(), n_solids=len(wp.solids().vals()), volume_mm3=round(vol, 1),
           mass_g=round(L.mass_g(vol, 'tub'), 1), mass_100pct_g=round(vol * L.FDM['ASA_DENSITY'], 1),
           bbox=[round(v, 3) for v in (bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax)], build_s=round(tb, 1))
res['in_envelope'] = (bb.xmin >= env['x'][0] - 1e-3 and bb.xmax <= env['x'][1] + 1e-3 and bb.ymin >= env['y'][0] - 1e-3
                      and bb.ymax <= env['y'][1] + 1e-3 and bb.zmin >= env['z'][0] - 1e-3 and bb.zmax <= env['z'][1] + 1e-3)
pp = dc.to_print_pose(s, T.PRINT['tub']['face_down']).BoundingBox()
res['print_bbox'] = [round(pp.xlen, 2), round(pp.ylen, 2), round(pp.zlen, 2)]
res['beds'] = {k: (sorted([pp.xlen, pp.ylen])[1] <= max(v[:2]) and min(pp.xlen, pp.ylen) <= min(v[:2]) and pp.zlen <= v[2])
               for k, v in L.PRINT_BEDS.items()}


def ov(box):
    try:
        return round(s.intersect(dc.box_solid(box)).Volume(), 3)
    except Exception as e:  # noqa: BLE001
        return 'err %s' % e


res['keepouts'] = {k: ov(b) for k, b in L.KEEPOUTS.items()}
res['keepouts'] = {k: v for k, v in res['keepouts'].items() if v != 0}
mates = {frozenset((a, b)) for a, b, _ in L.MATES}
res['cots_box_overlaps'] = {}
for cid, c in L.COTS.items():
    if c.get('box') and frozenset(('tub', cid)) not in mates:
        v = ov(c['box'])
        if v:
            res['cots_box_overlaps'][cid] = v
res['pi_hooks'] = 'deleted (R1 r2): removable pi_keeper on s_k1/s_k2, see printed_keeper.py'
res['keeper_bosses'] = {k: dict(c=b['c'], r=b['r'], top=L.PI_KEEPER['boss_top']) for k, b in L.PI_KEEPER['bosses'].items()}
res['notes'] = dc.NOTES
with open(os.path.join(HERE, 'out', 'test_tub.json'), 'w', encoding='utf-8') as f:
    json.dump(res, f, indent=1)
print(json.dumps(res, indent=1))
if '--stl' in sys.argv:
    cq.exporters.export(cq.Workplane().add(dc.to_print_pose(s, '-Y')), os.path.join(HERE, 'out', 'tub_test.stl'))
