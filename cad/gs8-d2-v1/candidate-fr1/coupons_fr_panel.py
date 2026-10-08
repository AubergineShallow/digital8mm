# SPDX-License-Identifier: MIT
"""GS8 D2 FR1 candidate (EXPLORATORY), fr-panel: coupon set for the panel bottom-edge keys (s_b1/s_b2 deleted).

    D2_FR=panel .venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py --max-wait-min 4 -- \
        cad/gs8-d2-v1/candidate-fr1/coupons_fr_panel.py [--out DIR]

Cut from the real FR part solids (like coupons_r1.py), so it refuses to run unless layout.FR['panel'] is on:
  coupon-frp-tub-lip     tub floor + left lip + 45 deg gusset, x -113..-83: both key notches and the lip web; prints
                         like the tub (-Y down)
  coupon-frp-panel-keys  panel bottom strip, same x: key_b1 + key_b2 (lead chamfers), the panel-2 chord web between
                         them and the stub of the diagonal tie, wall up to z 18; prints
                         face down (+Y), like the panel
Writes DIR/stl/coupons-fr/coupon-frp-*.stl and DIR/coupons-fr-panel-manifest.json (DIR default: candidate-fr1/out).
Nothing here is printed or measured.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cadquery as cq  # noqa: E402

import d2_common as dc  # noqa: E402
import layout as L  # noqa: E402

V = cq.Vector
GATE = ('G-FRP-1 (panel keys, proposed, not run): (a) coupon fit: the panel-keys coupon slides onto the tub-lip coupon '
        'along -Y by hand, both keys pass the notches (0.3 side play) and seat on the floor (feeler 0.05-0.2 under each '
        'key), tabs flush with the lip face +-0.2; 10 on/off cycles, no whitening at a key root. (b) full parts: panel '
        'on, s_r1 + s_r2 at 0.35-0.5 N m; seam gap at the lip line at x -91/-105 <= 0.3 unloaded; with 2 N and 5 N '
        'pulled outward (+Y) at the bottom edge between the keys, gap <= 0.5 / 1.0 and full return on release; record '
        'the panel bow (feeler on a flat plate) before assembly. (c) fr-panel-2 frame (A2): the same pull also at the '
        'front bottom corner (x -8) and at the EVF cap (x -148, z 78); record each opening against the ESTIMATE '
        '(JOINT-panel.md s. 11: 0.06 mm/N between the keys, 0.47 at the front corner, 0.05 at the EVF cap); any '
        'whitening or crack at a frame member root (chord, diagonal tie, uprights) after 10 panel on/off cycles fails.')
X0, X1 = -113.0, -83.0


def _box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def _cut(pid, box):
    mod = __import__(L.PARTS[pid]['module'][:-3])
    sh = mod.build_part(L, pid)
    s = (sh.val() if hasattr(sh, 'val') else sh).copy().intersect(_box(*box))
    sols = s.Solids()
    return max(sols, key=lambda x: x.Volume()) if sols else None


def coupons():
    tub = _cut('tub', (X0, X1, 18.0, L.YL + 0.1, 0.0, L.LIP['z'][1] + 0.1))
    panel = _cut('panel', (X0, X1, 23.5, L.YL + 0.1, 2.0, 18.0))
    return [('coupon-frp-tub-lip', tub, L.PARTS['tub']['face_down'], 1,
             'tub floor + lip + gusset with both key notches and the lip web (x %.0f..%.0f)' % (X0, X1)),
            ('coupon-frp-panel-keys', panel, L.PARTS['panel']['face_down'], 1,
             'panel bottom strip with key_b1 + key_b2, their lead chamfers and the panel-2 chord web, wall to z 18')]


def main():
    if not L.FR.get('panel'):
        sys.exit('coupons_fr_panel.py: run with D2_FR=panel (or all); layout.FR_STATE = %s' % L.FR_STATE)
    out_dir = os.path.join(HERE, 'out')
    if '--out' in sys.argv:
        out_dir = os.path.abspath(sys.argv[sys.argv.index('--out') + 1])
    stl_dir = os.path.join(out_dir, 'stl', 'coupons-fr')
    os.makedirs(stl_dir, exist_ok=True)
    man = []
    for cid, s, fd, qty, note in coupons():
        if s is None:
            man.append(dict(id=cid, error='empty cut'))
            print(cid, 'EMPTY')
            continue
        pose = dc.to_print_pose(s, fd)
        pose.exportStl(os.path.join(stl_dir, cid + '.stl'), 0.03, 0.2)
        b = pose.BoundingBox()
        man.append(dict(id=cid, face_down=fd, qty=qty, gate='G-FRP-1', note=note, valid=bool(pose.isValid()),
                        bbox=[round(b.xlen, 1), round(b.ylen, 1), round(b.zlen, 1)], volume_mm3=round(pose.Volume(), 1),
                        mass_g=round(pose.Volume() * L.FDM['ASA_DENSITY'], 1), stl='stl/coupons-fr/%s.stl' % cid))
        print('%-24s %-3s %s %s' % (cid, fd, man[-1]['bbox'], man[-1]['valid']))
    with open(os.path.join(out_dir, 'coupons-fr-panel-manifest.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(dict(revision=L.REVISION, fr_state=L.FR_STATE, gate=GATE,
                       note='cut from the built FR parts; nothing printed or measured', coupons=man), f, indent=1)


if __name__ == '__main__':
    main()
