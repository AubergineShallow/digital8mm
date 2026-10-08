# SPDX-License-Identifier: MIT
"""Smoke test of every d2_common helper on layout numbers (one call each). Run through the lock:
    .venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/test_common.py
Writes out/test_common.json (volume, validity, bbox per helper). Exit 1 if any helper fails."""
import json
import os
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import layout as L  # noqa: E402
import d2_common as dc  # noqa: E402


def rec(name, fn):
    t = time.time()
    try:
        r = fn()
        shapes = r if isinstance(r, (list, tuple)) else [r]
        shapes = [s.val() if hasattr(s, 'val') else s for s in shapes]
        vol = sum(s.Volume() for s in shapes)
        ok = all(s.isValid() for s in shapes) and vol > 0
        bb = shapes[0].BoundingBox()
        return dict(helper=name, ok=ok, n=len(shapes), volume_mm3=round(vol, 3), s=round(time.time() - t, 2),
                    bbox0=[round(v, 2) for v in (bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax)])
    except Exception as e:  # noqa: BLE001
        return dict(helper=name, ok=False, error='%s: %s' % (type(e).__name__, e), trace=traceback.format_exc()[-600:])


s = L.SCREWS[0]
t = L.TONGUES[0]
hk = L.HOOD_HOOKS[0]
H = L.HOOK
tests = [
    ('box_solid', lambda: dc.box_solid(L.TUB_BOX)),
    ('cyl_solid(tube)', lambda: dc.cyl_solid(L.HOOD['turret'], use_r_in=True)),
    ('pt_boss', lambda: list(dc.pt_boss((s['head_point'][0], s['head_point'][1], 2.6), (0, 0, 1), height=9.4))),
    ('counterbore', lambda: dc.counterbore(s['head_point'], s['axis'], depth=6.0, through=4.6)),
    ('snap_hook(hood hk1)', lambda: dc.snap_hook((hk['x'], L.Y_RW_IN + H['ledge'] + L.FDM['SLIDE'], L.ZT1), (0, 0, -1),
                                                 (0, -1, 0), H['length'], H['t'], H['w'], H['tooth'], H['land'])),
    ('snap_strain', lambda: dc.box_solid(L.B(0, 1, 0, 1, 0, max(1e-3, dc.snap_strain(H['t'], 0.55, H['length']))))),
    ('keyhole_tongue', lambda: dc.keyhole_tongue(t)),
    ('keyhole_slot', lambda: dc.keyhole_slot(t)),
    ('dovetail(rail)', lambda: dc.dovetail((-110.0, 35.2, -4.5), (-1.5, 35.2, -4.5), (0, -1, 0), 2.0, 1.2)),
    ('dovetail(groove)', lambda: dc.dovetail((-110.0, 35.2, -4.5), (-1.5, 35.2, -4.5), (0, -1, 0), 2.0, 1.2,
                                             grow=L.FDM['SLIDE'])),
    ('vent_slots(out_band)', lambda: dc.vent_slots(L.VENTS['out_band']['box'], 2.0, 3.4, 'z', '+x')),
    ('vent_slots(inlet_roof)', lambda: dc.vent_slots(L.VENTS['inlet_roof']['box'], 2.0, 3.6, 'y', '+z')),
    ('engrave(all items)', lambda: dc.engrave(L.ENGRAVE['items'])),
    ('teardrop', lambda: dc.teardrop(5.0, 0.0, 2.5, (-12.0, -35.0, 60.0), (0, 1, 0), up=(0, 0, 1))),
    ('bed_chamfer', lambda: dc.bed_chamfer(dc.wp_of(dc.box_solid(L.B(-140.0, -10.0, 34.0, 35.6, -8.0, 8.0))), '+Y')),
    ('safe_fillet(bad r falls back)', lambda: dc.safe_fillet(dc.wp_of(dc.box_solid(L.B(0, 2, 0, 2, 0, 2))), '|Z', 5.0)),
    ('safe_fillet(ok)', lambda: dc.safe_fillet(dc.wp_of(dc.box_solid(L.B(0, 20, 0, 20, 0, 5))), '|Z', 2.0)),
    ('to_print_pose(-Y)', lambda: dc.to_print_pose(dc.box_solid(L.TUB_BOX), '-Y')),
]
res = [rec(n, f) for n, f in tests]
strain = dc.snap_strain(H['t'], 0.55, H['length'])
out = dict(revision=L.REVISION, results=res, hood_hook_strain=round(strain, 4), helper_notes=dc.NOTES,
           all_ok=all(r['ok'] for r in res))
os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
with open(os.path.join(HERE, 'out', 'test_common.json'), 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=1)
for r in res:
    print('%-32s %s %s' % (r['helper'], 'ok ' if r['ok'] else 'FAIL', r.get('volume_mm3', r.get('error'))))
print('notes:', dc.NOTES)
print('ALL OK' if out['all_ok'] else 'SOME FAILED')
sys.exit(0 if out['all_ok'] else 1)
