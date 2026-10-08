# SPDX-License-Identifier: MIT
"""GS8 D2: print-test coupons (PRINT-GUIDE s6), cut from the real part solids (FIXER P-P11).

    .venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/make_coupons.py [--out DIR]

Each coupon is the exact intersection of a built part with a box round one feature (so it carries the same pilot,
hook, tongue or slot geometry as the part), posed as its parent part prints. r2 R2 adds the base-edge stack
(no skirts), cap retention and EVF-stop coupons; the Pi hook coupon is gone with the hooks (R1: coupons_r1.py). Two coupons are made directly: the knob
D-bore ladder (KNOB_BORE_OFFSET -0.05..+0.15 radial) and the clearance comb (LOCATE / SLIDE / SEAM). Writes
out/stl/coupons/*.stl and out/coupons-manifest.json. Nothing here is printed or measured.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cadquery as cq  # noqa: E402

import d2_common as dc  # noqa: E402
import layout as L  # noqa: E402

V = cq.Vector
OUT = os.path.join(HERE, 'out', 'stl', 'coupons')


def _box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


_CACHE = {}


def _part(pid):
    if pid not in _CACHE:                        # r2 R2: build each part once (the panel alone takes ~100 s)
        mod = __import__(L.PARTS[pid]['module'][:-3])
        sh = mod.build_part(L, pid)
        _CACHE[pid] = sh.val() if hasattr(sh, 'val') else sh
    return _CACHE[pid]


def _cut(pid, box):
    s = _part(pid).copy().intersect(_box(*box))
    sols = s.Solids()
    return max(sols, key=lambda x: x.Volume()) if sols else None


def d_bore_ladder():
    """5 discs per shaft: dia 14 x 6, D bore = shaft + offset (radial), n notches on the rim = step index."""
    out = []
    for shaft, (d, f) in (('enc', (6.0, 4.5)), ('sw', (6.35, 4.8))):
        for i, off in enumerate((-0.05, 0.0, 0.05, 0.10, 0.15)):
            x0 = i * 17.0
            disc = cq.Solid.makeCylinder(7.0, 6.0, V(x0, 0, 0))
            r = d / 2 + off
            flat = (f - d / 2) + off                       # centre to the flat
            bore = cq.Solid.makeCylinder(r, 6.2, V(x0, 0, -0.1)).intersect(_box(x0 - r - 1, x0 + r + 1, -r - 1, flat, -0.2, 6.3))
            disc = disc.cut(bore)
            for k in range(i + 1):                         # index notches on the rim (+X side)
                a = math.radians(-40 + 20 * k)
                disc = disc.cut(_box(-0.5, 0.5, -0.5, 0.5, 4.5, 6.1).translate(V(x0 + 7.0 * math.cos(a), 7.0 * math.sin(a), 0)))
            out.append(disc)
        yield 'knob_bore_ladder_%s' % shaft, dc.fuse_all(out), '-Z', 1, 'G-KNOB (sets FDM KNOB_BORE_OFFSET)', \
            'D %.2f/%.2f; offsets -0.05, 0, +0.05, +0.10, +0.15 radial = 1..5 rim notches' % (d, f)
        out = []


def clearance_comb():
    pegs = _box(0, 30, 0, 8, 0, 2.0)
    holes = _box(0, 30, 12, 20, 0, 3.0)
    for i, c in enumerate((L.FDM['LOCATE'], L.FDM['SLIDE'], L.FDM['SEAM'])):
        x = 3 + i * 9.5
        pegs = pegs.fuse(_box(x, x + 5, 1.5, 6.5, 2.0, 8.0))
        holes = holes.cut(_box(x - c, x + 5 + c, 13.5 - c, 18.5 + c, -0.1, 3.1))
        holes = holes.cut(_box(x + 1, x + 4, 19.0, 20.1, 2.4, 3.1))   # i+1 marks: one slot per comb tooth
    return pegs.fuse(holes)


def coupons():
    hk = next(h for h in L.HOOD_HOOKS if h['id'] == 'hk1')
    t = L.TONGUES[0]
    xt = (t['head']['x'][0] + t['head']['x'][1]) / 2
    pb = L.PANEL_POSTS['post_f']
    bb = L.PANEL_BOSSES['boss_b1']
    cradle_x = L.ENCODER['c'][0]
    h3 = next(h for h in L.HOOD_HOOKS if h['id'] == 'hk3')
    sb = next(s for s in L.SCREWS if s['id'] == 's_b1')
    xe0, xe1 = sb['head_point'][0] - 9.0, sb['head_point'][0] + 7.0      # -100 .. -84 (clear of tongue_r at -83)
    pcb_top = L.ENCODER['pcb']['z'][1]
    rows = [
        ('pt_boss_post', 'panel', (pb['x'][0] - 0.5, pb['x'][1] + 0.5, pb['y'][0] - 0.1, -17.0, pb['z'][0] - 0.5, pb['z'][1] + 0.5),
         3, 'G-PT-1', 's_r post: pilot along print-up (strong case)'),
        ('pt_boss_bottom', 'panel', (bb['x'][0] - 0.5, bb['x'][1] + 0.5, bb['y'][0] - 0.1, L.YL + 0.1, bb['z'][0] - 0.1, bb['z'][1] + 2.0),
         3, 'G-PT-1', 's_b boss with its panel-wall patch: pilot horizontal in print (weak case)'),
        # r2 R2: pi_hook row dropped (R1 deleted the Pi floor hooks; R1's keeper coupon is in coupons_r1.py)
        ('board_edge_plate', None, None, 2, 'G-SNAP-2', '30 x 14 x 1.6 plate standing in for the encoder PCB edge'),
        ('hood_hook', 'hood', (hk['x'] - 7.0, hk['x'] + 7.0, hk['y_face'] - 0.5, hk['y_face'] + 5.0, L.ZT1 - L.HOOK['length'] - 1.0, L.H),
         1, 'G-SNAP-2', 'hk1 with its band patch'),
        ('hood_ledge', 'tub', (hk['x'] - 7.0, hk['x'] + 7.0, L.YR, hk['y_face'] + 1.2, L.HOOK['catch_z'] - 6.0, L.ZT1),
         1, 'G-SNAP-2', 'hk1 catch ledge with its right-wall patch and the dia 1.6 release hole (pin hold-open test)'),
        # FIXER r2 (M-V-MPS-2): the 45 deg return hook hk3 and its sloped ledge (cam-out on a straight pull)
        ('hood_hook_ret', 'hood', (h3['x_face'] - 5.0, h3['x_face'] + 0.5, h3['y'] - 7.0, h3['y'] + 7.0,
                                   L.ZT1 - L.HOOK['length'] - 1.0, L.H),
         1, 'G-SNAP-2', 'hk3 (45 deg return catch) with its band patch'),
        ('hood_ledge_ret', 'tub', (h3['x_face'] - 1.2, L.XT1, h3['y'] - 7.0, h3['y'] + 7.0, L.HOOK['catch_z'] - 6.0, L.ZT1),
         1, 'G-SNAP-2', 'hk3 sloped catch ledge with its front-wall patch'),
        ('encoder_cradle_hook', 'panel', (cradle_x - 6.0, cradle_x + 6.0, 22.0, L.YL, pcb_top - 1.0, pcb_top + 3.6),
         1, 'G-SNAP-2', 'top cradle hook with its panel-wall patch; test on the 1.6 plate'),
        ('tongue', 'tub', (xt - 6.0, xt + 6.0, -21.0, 2.0, t['head']['z'][0] - 0.1, L.T),
         1, 'J4 record', 'tongue_f, 20 mm incl. the -Y wing (needs its paint-on support, as in the tub)'),
        ('keyhole_slot', 'base_grip', (xt - 8.5, xt + L.BASE_SLIDE + 8.5, -21.0, 2.0, -6.0, 0.0),
         1, 'J4 record', 'base window + pocket for tongue_f, 20 mm: drop in, slide 10, no rock'),
        # r2 R2 (findings 2, 3, 6): revised base edge (no skirts), cap retention, EVF board +Y stop
        ('base_edge_base', 'base_grip', (xe0, xe1, 18.0, L.BASE['y'][1] + 0.1, L.BASE['z'][0] - 0.1, 0.1),
         1, 'G-PANEL-1', 'base edge at s_b1 (counterbore, plain side face); stack with base_edge_tub + base_edge_panel'),
        ('base_edge_tub', 'tub', (xe0, xe1, 18.0, L.YL + 0.1, 0.0, 8.0),
         1, 'G-PANEL-1', 'tub floor + lip with the boss_b1 notch; the panel coupon sits on its end face'),
        ('base_edge_panel', 'panel', (xe0, xe1, 23.5, L.YL + 0.1, 2.5, 16.0),
         1, 'G-PANEL-1, G-PT-1', 'boss_b1 + notch tab + wall patch: one PT 3.0 x 12 through the 3 coupons; tab '
         'flush in the notch (seam 0.3), 5 open/close cycles with the PH1 only'),
        ('cap_retention_grip', 'base_grip', (L.GRIP['x'][0] - 1.0, L.GRIP['x'][1] + 1.0, -16.0, 16.0, -110.1, -100.0),
         1, 'G-CAP-1', 'grip foot: cap grooves, 45 deg lips, detent dimples, heel strap bar'),
        ('cap_retention_cap', 'cap', (L.CAP['box']['x'][0] - 0.1, L.CAP['box']['x'][1] + 0.1, -15.1, 15.1,
                                      L.CAP['box']['z'][0] - 0.1, L.CAP['box']['z'][1] + 0.1),
         1, 'G-CAP-1', 'the whole cap: 20 slide cycles, detent click and hold, pull-down 20 N on the keys'),
        ('evf_stop_tub', 'tub', (L.X_REAR - 0.1, -134.0, L.YR - 0.1, L.SPLIT, 60.0, 96.0),   # rails hang on the right wall
         1, 'G-EVF-2, G-EVF-1', 'rear-right corner: rear wall, EVF board rails, OLED cell; its rear-wall end face registers the panel coupon'),
        ('evf_stop_panel', 'panel', (L.X_REAR - 0.1, -134.0, 27.5, L.YL + 0.1, 60.0, 96.0),
         1, 'G-EVF-2, G-EVF-1', 'rear end land + EVF cap clamp + board +Y stop rib: with the real board, gap '
         '0.1-0.5 at the stop, no shuttle on the HDMI plug; spigot clamp on the real eyepiece'),
    ]
    for cid, pid, box, qty, gate, note in rows:
        if pid is None:
            yield cid, _box(0, 30, 0, 14, 0, 1.6), '-Z', qty, gate, note
            continue
        s = _cut(pid, box)
        if s is None:
            print('coupon %s: empty cut' % cid)
            continue
        yield cid, s, L.PARTS[pid]['face_down'], qty, gate, note + ' (cut from %s)' % pid
    yield from d_bore_ladder()
    yield 'clearance_comb', clearance_comb(), '-Z', 1, 'profile tuning', 'pegs 5 x 5 and holes +0.15 / +0.25 / +0.30 per side (1-3 marks)'


def main():
    global OUT
    man_dir = os.path.join(HERE, 'out')
    if '--out' in sys.argv:                      # r2 R2: test into another folder (out/ keeps the release set)
        man_dir = os.path.abspath(sys.argv[sys.argv.index('--out') + 1])
        OUT = os.path.join(man_dir, 'stl', 'coupons')
    os.makedirs(OUT, exist_ok=True)
    man = []
    for cid, s, fd, qty, gate, note in coupons():
        pose = dc.to_print_pose(s, fd)
        path = os.path.join(OUT, cid + '.stl')
        pose.exportStl(path, 0.03, 0.2)
        b = pose.BoundingBox()
        man.append(dict(id=cid, face_down=fd, qty=qty, gate=gate, note=note, valid=bool(pose.isValid()),
                        bbox=[round(b.xlen, 1), round(b.ylen, 1), round(b.zlen, 1)], volume_mm3=round(pose.Volume(), 1),
                        mass_g=round(pose.Volume() * L.FDM['ASA_DENSITY'], 1), stl='stl/coupons/%s.stl' % cid))
        print('%-22s %-4s x%d %s' % (cid, fd, qty, man[-1]['bbox']))
    with open(os.path.join(man_dir, 'coupons-manifest.json'), 'w') as f:
        json.dump(dict(revision=L.REVISION, note='cut from the built parts; nothing printed or measured', coupons=man), f, indent=1)
    print('%d coupons, %.0f g ASA at 100 %%' % (len(man), sum(m['mass_g'] * m['qty'] for m in man)))


if __name__ == '__main__':
    main()
