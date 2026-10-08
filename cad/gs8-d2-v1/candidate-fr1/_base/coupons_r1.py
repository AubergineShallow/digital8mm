# SPDX-License-Identifier: MIT
"""GS8 D2 r2 (R1, finding 1): Pi-keeper retention coupon set, cut from the real part solids like make_coupons.py.

    .venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/coupons_r1.py [--out DIR]

FIXER r2 (verifier M-V-MPS-7): the set now covers the WHOLE keeper (r2 R1 cut only the port bar):
  coupon-pi-keeper-tub    tub floor + right-wall strip, x -106..-5.3, z 0..10: both keeper bosses (s_k1, s_k2) and all
                          4 Pi floor bosses with their head pockets; prints right wall down (-Y), like the tub
  coupon-pi-keeper-part   the whole printed pi_keeper (arm, bridge, bar, kf1-kf4, s_k1 counterbore, s_k2 spot face)
  coupon-pi-keeper-x1203  1.6 flat X1203 stand-in (full footprint, 4 x dia 2.75 holes); flat on the bed
  coupon-pi-keeper-pi     1.6 flat Pi 5 stand-in (full footprint, 4 x dia 2.75 holes); flat on the bed
                          The 2 plates are assembled with the REAL X1203 kit (4 standoffs, 8 M2.5 x 5): the 4 kit screw
                          heads sit in the 4 tub head pockets exactly as in the camera, and kf1/kf2 pass under the Pi
                          plate in the +X 1.2 step. Coupon-only dummy stack: no electronics at risk.
Writes DIR/stl/coupons/coupon-pi-keeper-*.stl and DIR/coupons-r1-manifest.json (DIR default: out). Nothing here is
printed or measured.
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
GATE = ('G-KEEP-1 (whole keeper): 5 full service cycles, each: keeper in along the stated path (-Y 60 at +0.5, +X 1.2 '
        'under the Pi lip, down 0.5) by hand with the plate seated, s_k1 and s_k2 driven to head contact at 0.35-0.5 '
        'N m, then both out and the keeper out by the exact reverse. Pass: no spin-out or boss crack at either boss; '
        'feeler gap between each of the 4 finger undersides and the plate 0.05-0.3; plate lifted at its middle with 20 '
        'N for 60 s: no crack or whitening at any finger root, permanent set <= 0.2; kf1/kf2 pass under the Pi lip '
        'without contact. Proposed criteria; not run.')


def _box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def _cut(pid, box):
    mod = __import__(L.PARTS[pid]['module'][:-3])
    sh = mod.build_part(L, pid)
    s = (sh.val() if hasattr(sh, 'val') else sh).copy().intersect(_box(*box))
    sols = s.Solids()
    return max(sols, key=lambda x: x.Volume()) if sols else None


def coupons():
    K = L.PI_KEEPER
    tub = _cut('tub', (K['arm']['x'][0] - 1.0, L.X_FW_IN - 0.1, L.YR, L.YL, 0.0, K['boss_top'] + 0.2))
    mod = __import__(L.PARTS['pi_keeper']['module'][:-3])                     # the whole keeper
    sh = mod.build_part(L, 'pi_keeper')
    part = (sh.val() if hasattr(sh, 'val') else sh).copy()
    (px0, px1), (py0, py1) = L.PI['x'], L.PI['y']

    def plate(z0, z1):                                                        # flat stand-in board, 4 kit-screw holes
        b = _box(px0, px1, py0, py1, z0, z1)
        for hx, hy in L.PI['holes']:
            b = b.cut(cq.Solid.makeCylinder(1.375, z1 - z0 + 0.2, V(hx, hy, z0 - 0.1), V(0, 0, 1)))
        return b
    return [('coupon-pi-keeper-tub', tub, L.PARTS['tub']['face_down'], 1,
             'tub floor: keeper bosses s_k1 + s_k2, 4 Pi bosses + head pockets, lip gusset'),
            ('coupon-pi-keeper-part', part, L.PARTS['pi_keeper']['face_down'], 1, 'the whole pi_keeper (6.7 g est.)'),
            ('coupon-pi-keeper-x1203', plate(*L.PI['x1203_z']), '-Z', 1, '1.6 X1203 stand-in, with the real kit'),
            ('coupon-pi-keeper-pi', plate(*L.PI['pcb_z']), '-Z', 1, '1.6 Pi 5 stand-in on the kit standoffs')]


def main():
    out_dir = os.path.join(HERE, 'out')
    if '--out' in sys.argv:
        out_dir = os.path.abspath(sys.argv[sys.argv.index('--out') + 1])
    stl_dir = os.path.join(out_dir, 'stl', 'coupons')
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
        man.append(dict(id=cid, face_down=fd, qty=qty, gate='G-KEEP-1', note=note, valid=bool(pose.isValid()),
                        bbox=[round(b.xlen, 1), round(b.ylen, 1), round(b.zlen, 1)], volume_mm3=round(pose.Volume(), 1),
                        mass_g=round(pose.Volume() * L.FDM['ASA_DENSITY'], 1), stl='stl/coupons/%s.stl' % cid))
        print('%-24s %-3s %s %s' % (cid, fd, man[-1]['bbox'], man[-1]['valid']))
    with open(os.path.join(out_dir, 'coupons-r1-manifest.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(dict(revision=L.REVISION, gate=GATE, note='cut from the built parts; nothing printed or measured',
                       coupons=man), f, indent=1)


if __name__ == '__main__':
    main()
