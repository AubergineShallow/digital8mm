# SPDX-License-Identifier: MIT
"""GS8 D2 candidate FR1, joint hood = 'yslide' (owner fr-hood): rough coupon pairs for the rigid slide keys.

    .venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-fr1/coupons_fr_hood.py [--out DIR]

Cut from the real yslide part solids (this script forces D2_FR=hood=yslide), like coupons_r1.py:
  coupon-fr-hood-tub-yk1    tub right-wall strip x -60..-30 with the yk1 tab (prints right wall down, -Y, like the tub)
  coupon-fr-hood-hood-yk1   hood band strip with the yk1 staple (roof down, +Z, like the hood)
  coupon-fr-hood-tub-yk3    tub front-wall corner y 12..32 with the yk3 45 deg ledge (-Y down)
  coupon-fr-hood-hood-yk3   hood band + front-plate strip with the yk3 dovetail toe (+Z down): the plate is the end
                            embrace that stops the 45 deg cam-out, so the pair tests the real retention path
Writes DIR/stl/coupons-fr/coupon-fr-hood-*.stl and DIR/coupons-fr-hood-manifest.json (DIR default: out).
Nothing here is printed, sliced or measured.
"""
import json
import os
import sys

os.environ['D2_FR'] = 'hood=yslide'
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cadquery as cq  # noqa: E402

import d2_common as dc  # noqa: E402
import layout as L  # noqa: E402

V = cq.Vector
GATE = ('G-YSLIDE-1 (proposed, not run): print both coupon pairs in the production profile and orientation. (1) Fit: '
        'drop the hood coupon %.1f mm off its place, push it home by hand: no binding over the slide, slide force '
        '<= 10 N, it stops on the wall. (2) Play: lift play at each key <= 0.3 mm (feeler). (3) Retention: with the '
        'slide blocked (clamp the coupon at its home position, as the panel tongue / camera ring do in the camera), '
        'pull the band 40 N straight up for 60 s at each key: no crack or whitening at the tab root, staple bar, '
        'toe root or ledge root; permanent set <= 0.2 mm. (4) 10 on/off cycles, then repeat (2) and (3). Proposed '
        'criteria; not run.' % L.HOOD_YSLIDE['dy'])


def _box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


_CACHE = {}


def _cut(pid, box):
    if pid not in _CACHE:
        mod = __import__(L.PARTS[pid]['module'][:-3])
        sh = mod.build_part(L, pid)
        _CACHE[pid] = (sh.val() if hasattr(sh, 'val') else sh).copy()
    s = _CACHE[pid].copy().intersect(_box(*box))
    sols = s.Solids()
    return max(sols, key=lambda x: x.Volume()) if sols else None


def coupons():
    assert L.FR['hood'] == 'yslide', L.FR_STATE
    k = {h['id']: h for h in L.HOOD_HOOKS}
    x1 = k['yk1']['x']
    y3 = k['yk3']['y']
    fd_t, fd_h = L.PARTS['tub']['face_down'], L.PARTS['hood']['face_down']
    return [
        ('coupon-fr-hood-tub-yk1', _cut('tub', (x1 - 15, x1 + 15, L.YR, L.Y_RW_IN + 6.0, 80.0, L.ZT1)), fd_t,
         'tub right-wall strip with the yk1 tab (flat catch)'),
        ('coupon-fr-hood-hood-yk1', _cut('hood', (x1 - 15, x1 + 15, L.HOOD['y'][0], L.Y_RW_IN + 14.0, 84.0, L.H)), fd_h,
         'hood band strip with the yk1 staple'),
        ('coupon-fr-hood-tub-yk3', _cut('tub', (L.X_FW_IN - 8.0, L.XT1, y3 - 10.0, y3 + 10.0, 80.0, L.ZT1)), fd_t,
         'tub front-wall corner with the yk3 45 deg ledge'),
        ('coupon-fr-hood-hood-yk3', _cut('hood', (L.X_FW_IN - 10.0, L.X_FRONT, y3 - 10.0, y3 + 10.0, 84.0, L.H)), fd_h,
         'hood band + front-plate strip with the yk3 toe (plate = end embrace)'),
    ]


def main():
    out_dir = os.path.join(HERE, 'out')
    if '--out' in sys.argv:
        out_dir = os.path.abspath(sys.argv[sys.argv.index('--out') + 1])
    stl_dir = os.path.join(out_dir, 'stl', 'coupons-fr')
    os.makedirs(stl_dir, exist_ok=True)
    man = []
    for cid, s, fd, note in coupons():
        if s is None:
            man.append(dict(id=cid, error='empty cut'))
            print(cid, 'EMPTY')
            continue
        pose = dc.to_print_pose(s, fd)
        pose.exportStl(os.path.join(stl_dir, cid + '.stl'), 0.03, 0.2)
        b = pose.BoundingBox()
        man.append(dict(id=cid, face_down=fd, qty=1, gate='G-YSLIDE-1', note=note, valid=bool(pose.isValid()),
                        bbox=[round(b.xlen, 1), round(b.ylen, 1), round(b.zlen, 1)], volume_mm3=round(pose.Volume(), 1),
                        mass_g=round(pose.Volume() * L.FDM['ASA_DENSITY'], 1), stl='stl/coupons-fr/%s.stl' % cid))
        print('%-26s %-3s %s %s' % (cid, fd, man[-1]['bbox'], man[-1]['valid']))
    with open(os.path.join(out_dir, 'coupons-fr-hood-manifest.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(dict(revision=L.REVISION, fr_state=L.FR_STATE, gate=GATE,
                       note='cut from the built yslide parts; nothing printed, sliced or measured', coupons=man), f, indent=1)


if __name__ == '__main__':
    main()
