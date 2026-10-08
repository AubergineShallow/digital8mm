# SPDX-License-Identifier: MIT
"""FR1 keeper (fr-keeper role): rough coupons for the keyed-seat Pi keeper (one PT screw), cut from the real FR part
solids like coupons_r1.py. Run through ../run_locked.py with D2_FR=keeper (refuses otherwise).

  coupon-fr-keeper-seat     tub corner block x -110..-92, y -35..-20, z 0..19.5: right wall, floor, keyed seat
                            (pocket, ledge, side walls, jaw). Prints like the tub (right wall down).
  coupon-fr-keeper-stub     keeper arm end x -106..-90, y -30..-15: tongue + kf1 finger (top face down, as the part).
  coupon-fr-keeper-tub      tub floor strip with the seat + the s_k2 boss + 4 Pi bosses (the whole-keeper rig).
  coupon-fr-keeper-part     the whole FR keeper.
  coupon-fr-keeper-x1203 / -pi   1.6 flat board stand-ins (as coupons_r1.py), for the whole-keeper cycle test.

Writes DIR/stl/coupons-fr/coupon-fr-keeper-*.stl and DIR/coupons-fr-keeper-manifest.json (DIR default: out).
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
GATE = ('G-KEEP-1r (FR1 keyed-seat keeper; replaces G-KEEP-1 for this candidate). (a) seat + stub: 20 insert/withdraw '
        'cycles of the stub tongue into the seat along -Y 3 by hand; feeler play at the tongue: z 0.1-0.4 total, x '
        '0.1-0.4 total; no whitening at the ledge root or side walls; the tongue stops 0.15 short of the pocket back (the 0.15 tip '
        'gap; r4, audit 2026-10-05-r3: was misstated as 0.25) with no binding over the 45 deg lead-in. Then the stub tip pulled up with 20 N for 60 s: permanent set <= 0.1, no crack. '
        '(b) whole keeper on the tub strip with the two board stand-ins and the real kit: 5 full service cycles along '
        'the stated path (-Y 60 at +0.5 and -1.2, down 0.5, +X 1.2, -Y 3), s_k2 to head contact at 0.35-0.5 N m; '
        'finger-underside gap to the X1203 plate 0.05-0.3 at all 4 fingers with s_k2 tight; X1203 plate lifted at its '
        'middle with 20 N: kf1/kf2 gap growth <= 0.25, no crack; the keeper cannot be rotated about s_k2 by hand. '
        'Proposed criteria; not run.')


def _box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def _part(pid):
    mod = __import__(L.PARTS[pid]['module'][:-3])
    sh = mod.build_part(L, pid)
    return (sh.val() if hasattr(sh, 'val') else sh).copy()


def _cut(sh, *boxes):
    b = _box(*boxes[0])
    for o in boxes[1:]:
        b = b.fuse(_box(*o))
    sols = sh.copy().intersect(b).Solids()
    return max(sols, key=lambda x: x.Volume()) if sols else None


def coupons():
    K = L.PI_KEEPER
    tub, kp = _part('tub'), _part('pi_keeper')
    (px0, px1), (py0, py1) = L.PI['x'], L.PI['y']

    def plate(z0, z1):
        b = _box(px0, px1, py0, py1, z0, z1)
        for hx, hy in L.PI['holes']:
            b = b.cut(cq.Solid.makeCylinder(1.375, z1 - z0 + 0.2, V(hx, hy, z0 - 0.1), V(0, 0, 1)))
        return b
    sx, sy = K['seat']['x'], K['seat']['y']
    corner = (sx[0] - 3.0, sx[1] + 3.0, L.YR, sy[1] + 7.0, 0.0, K['seat']['z'][1] + 0.75)
    tub_fd, kp_fd = L.PARTS['tub']['face_down'], L.PARTS['pi_keeper']['face_down']
    return [('coupon-fr-keeper-seat', _cut(tub, corner), tub_fd, 2, 'tub corner: right wall, floor, keyed seat'),
            ('coupon-fr-keeper-stub', _cut(kp, (-106.0, -90.0, -30.0, -15.0, 7.0, 16.0)), kp_fd, 2,
             'keeper arm end: tongue + kf1 finger'),
            ('coupon-fr-keeper-tub', _cut(tub, (K['arm']['x'][0] - 3.0, L.X_FW_IN - 0.1, L.YR, L.YL, 0.0,
                                                K['boss_top'] + 0.2), corner), tub_fd, 1,
             'tub floor strip: seat, s_k2 boss, 4 Pi bosses + head pockets, lip gusset'),
            ('coupon-fr-keeper-part', kp, kp_fd, 1, 'the whole FR pi_keeper'),
            ('coupon-fr-keeper-x1203', plate(*L.PI['x1203_z']), '-Z', 1, '1.6 X1203 stand-in, with the real kit'),
            ('coupon-fr-keeper-pi', plate(*L.PI['pcb_z']), '-Z', 1, '1.6 Pi 5 stand-in on the kit standoffs')]


def main():
    if not L.FR['keeper']:
        sys.exit('coupons_fr_keeper.py: run with D2_FR=keeper (or a selection that includes keeper)')
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
        man.append(dict(id=cid, face_down=fd, qty=qty, gate='G-KEEP-1r', note=note, valid=bool(pose.isValid()),
                        bbox=[round(b.xlen, 1), round(b.ylen, 1), round(b.zlen, 1)], volume_mm3=round(pose.Volume(), 1),
                        mass_g=round(pose.Volume() * L.FDM['ASA_DENSITY'], 1), stl='stl/coupons-fr/%s.stl' % cid))
        print('%-24s %-3s %s %s' % (cid, fd, man[-1]['bbox'], man[-1]['valid']))
    with open(os.path.join(out_dir, 'coupons-fr-keeper-manifest.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(dict(revision=L.REVISION, fr=L.FR_STATE, gate=GATE,
                       note='cut from the built FR parts; nothing printed or measured', coupons=man), f, indent=1)


if __name__ == '__main__':
    main()
