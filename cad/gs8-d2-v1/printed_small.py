# SPDX-License-Identifier: MIT
"""GS8 D2 printed parts, owner grip_small: the small parts.

  plunger       black ASA power plunger (no light pipe; no LED indicators, 2026-10-05): stem 11 x 6, stop flange, nib on the Pi
                button, engraved power symbol on the finger face
  knob_exp      exposure knob dia 28, 60-tooth knurl, D bore 6.0/4.5 (encoder shaft), bushing recess
  knob_fps      18/24 knob dia 20, 40-tooth knurl, D bore 6.35/4.8, nut recess dia 16, engraved index on the flat
  eyecup        TPU 95A cup, 15 deg flare to dia 46 (33.6 proud of the rear face), 3.0 sleeve with 0.3 grip on the
                eyepiece eye-end body, 45 deg inner lip
  stick_sleeve  satin-silver ASA sleeve on the SSD stick end (slider lock + pull), 0.8 walls (layout section)

MODULE CONTRACT (layout.MODULE_CONTRACT): build(layout) -> {part_id: Workplane} in ASSEMBLY coordinates; PRINT at
module level; build_part(layout, part_id).
"""
import math

import cadquery as cq

import d2_common as dc

V = cq.Vector

KNOB = {   # owner choices: core radius, knurl tooth height, knurl band insets (bottom, top), chamfers (bottom, top)
    'knob_exp': dict(teeth=60, tooth_h=0.6, band=(1.2, 0.8), chamfer=(1.0, 0.6), bore_clear=0.1, flat_clear=0.05,
                     recess_r=5.75, top_ring=(8.5, 9.3)),
    'knob_fps': dict(teeth=32, tooth_h=0.6, band=(1.0, 0.8), chamfer=(0.8, 0.6), bore_clear=0.1, flat_clear=0.05,
                     index=dict(r=(3.6, 8.4), w=1.2, depth=0.6)),
}
ENGRAVE_D = dc.ENGRAVE_DEPTH

_IDS = ('plunger', 'knob_exp', 'knob_fps', 'eyecup', 'stick_sleeve')
_FD = {pid: dc.L.PARTS[pid]['face_down'] for pid in _IDS}
PRINT = {
    'plunger': dict(face_down=_FD['plunger'], supports='none (finger face + flange on the bed, stem and nib rise)',
                    notes='ASA black (the hood spool), 100 % infill, no top pattern on the finger face. Paint-fill '
                          'the power symbol white.'),
    'knob_exp': dict(face_down=_FD['knob_exp'], supports='none (top face on the bed, knurl vertical, recess open up)',
                     notes='ASA black, 100 %. Press onto the D shaft; the shaft end sits 0.2 below the top face. '
                           'Pressed on at bench step 2 with the encoder board backed by a thumb (ASSEMBLY step 2); '
                           'never pressed on in the closed body.'),   # r7 C5 (BX-5): text only, STL unchanged
    'knob_fps': dict(face_down=_FD['knob_fps'], supports='none (top face on the bed, knurl vertical, recess open up)',
                     notes='ASA black, 100 %. Paint-fill the index. The index is on the D-flat side.'),
    'eyecup': dict(face_down=_FD['eyecup'], supports='none (sleeve end on the bed; 15 deg flare, 45 deg inner lip)',
                   notes='TPU 95A, 100 %, 20 mm/s, no retraction tuning needed. Stretch over the eye-end body.'),
    'stick_sleeve': dict(face_down=_FD['stick_sleeve'], supports='none (end face on the bed, walls vertical)',
                         notes='ASA satin silver, 2 perimeters (0.8 walls = layout section), 0.1 mm first layer care. '
                               'Press onto the stick end with the slider out.'),
}


# ----------------------------------------------------------------------------------------------- helpers
def _xz_prism(poly, y0, y1):
    pl = cq.Plane(origin=V(0, y1, 0), xDir=V(1, 0, 0), normal=V(0, -1, 0))
    return dc._prism(poly, pl, 0.0, y1 - y0)


def _yz_prism(poly, x0, x1):
    pl = cq.Plane(origin=V(x0, 0, 0), xDir=V(0, 1, 0), normal=V(1, 0, 0))
    return dc._prism(poly, pl, 0.0, x1 - x0)


def _wp(s):
    return cq.Workplane('XY').newObject([s])


def _arc_band(c, r0, r1, a0, a1, n=24):
    """(u, v) polygon of an annular band about c from angle a0 to a1 (deg, 0 = +v, positive toward +u)."""
    pts = []
    for r, rng in ((r1, range(n + 1)), (r0, range(n, -1, -1))):
        for i in rng:
            a = math.radians(a0 + (a1 - a0) * i / n)
            pts.append((c[0] + r * math.sin(a), c[1] + r * math.cos(a)))
    return pts


def _d_poly(c, r, flat_off, n_dir, segs=48):
    """(x, z) polygon of a D: circle radius r about c, cut by a flat at distance flat_off along unit n_dir."""
    nx, nz = n_dir
    tx, tz = -nz, nx
    t0 = math.acos(max(-1.0, min(1.0, flat_off / r)))
    pts = []
    for i in range(segs + 1):
        t = t0 + (2 * math.pi - 2 * t0) * i / segs
        pts.append((c[0] + r * (math.cos(t) * nx + math.sin(t) * tx), c[1] + r * (math.cos(t) * nz + math.sin(t) * tz)))
    return pts


def _bore_spec(s):
    """'D 6.0/4.5' -> (shaft dia, across-flat)."""
    a, b = s.split()[1].split('/')
    return float(a), float(b)


# ----------------------------------------------------------------------------------------------- plunger
def build_plunger(L):
    P = L.PLUNGER
    st, fl, nb = P['stem'], P['flange'], P['nib']
    stem = dc.safe_fillet(_wp(dc.box_solid(st)), '|X', 0.5).val()
    flange = dc.safe_fillet(_wp(dc.box_solid(fl)), '|X', 0.8).val()
    (ny, nz), r = nb['c'], nb['r']
    nib = cq.Solid.makeCylinder(r, nb['a'][1] - nb['a'][0] + 0.05, V(nb['a'][0], ny, nz), V(1, 0, 0))
    s = stem.fuse(flange).fuse(nib).clean()
    s = dc.bed_chamfer(_wp(s), L.PARTS['plunger']['face_down'], 0.3).val()
    # engraved power symbol on the finger face (x = stem front), centred on the plunger axis
    xf = st['x'][1]
    c = P['axis']
    sym = [_yz_prism(_arc_band(c, 1.55, 2.25, 40.0, 320.0), xf - ENGRAVE_D, xf + 0.1),
           _yz_prism([(c[0] - 0.35, c[1] + 0.3), (c[0] + 0.35, c[1] + 0.3), (c[0] + 0.35, c[1] + 2.7),
                      (c[0] - 0.35, c[1] + 2.7)], xf - ENGRAVE_D, xf + 0.1)]
    return dc.one_solid(s.cut(dc.fuse_all(sym)).clean())


# ----------------------------------------------------------------------------------------------- knobs
def build_knob(L, pid):
    K, o = L.KNOBS[pid], KNOB[pid]
    cxz = K['c']
    y0, y1 = K['y']
    R = K['d'] / 2.0
    rc = R - o['tooth_h']
    core = _wp(cq.Solid.makeCylinder(rc, y1 - y0, V(cxz[0], y0, cxz[1]), V(0, 1, 0)))
    core = dc.safe_chamfer(core, cq.selectors.BoxSelector((cxz[0] - R, y1 - 0.05, cxz[1] - R),
                                                         (cxz[0] + R, y1 + 0.05, cxz[1] + R)), o['chamfer'][1])
    core = dc.safe_chamfer(core, cq.selectors.BoxSelector((cxz[0] - R, y0 - 0.05, cxz[1] - R),
                                                         (cxz[0] + R, y0 + 0.05, cxz[1] + R)), o['chamfer'][0])
    n = o['teeth']
    p = 360.0 / n
    pts = []
    for i in range(n):
        a = i * p
        for rr, f in ((rc - 0.1, 0.0), (R, 0.15), (R, 0.55), (rc - 0.1, 0.7)):   # tip 0.4 p, root 0.7 p
            t = math.radians(a + f * p)
            pts.append((cxz[0] + rr * math.cos(t), cxz[1] + rr * math.sin(t)))
    knurl = _xz_prism(pts, y0 + o['band'][0], y1 - o['band'][1])
    s = core.val().fuse(knurl).clean()
    # underside recess: encoder bushing (+ nut) / switch nut; never bottoms on the bushing (0.25)
    if pid == 'knob_exp':
        bu = L.ENCODER['bushing']
        rr, depth = o['recess_r'], bu['a'][1] + L.FDM['SLIDE'] - y0
    else:
        bu = L.SWITCH_1824['bushing']
        rr = K['nut_recess'][0] / 2.0
        depth = max(K['nut_recess'][1], bu['a'][1] + L.FDM['SLIDE'] - y0)
    cuts = [cq.Solid.makeCylinder(rr, depth + 0.1, V(cxz[0], y0 - 0.1, cxz[1]), V(0, 1, 0))]
    # D bore, through to the top (the shaft end is at or past the top face)
    d, f = _bore_spec(K['bore'])
    off = L.FDM['KNOB_BORE_OFFSET']        # FIXER P10: radial growth over the shaft; the D-bore ladder coupon sets it
    rb = d / 2.0 + off
    flat = (f - d / 2.0) + off
    a = math.radians(K.get('index_deg', 0.0))
    n_dir = (-math.sin(a), math.cos(a))     # layout pol(): 0 = up (+z), + = clockwise seen from +Y (toward -x)
    cuts.append(_xz_prism(_d_poly(cxz, rb, flat, n_dir), y0 + depth - 0.05, y1 + 0.1))
    if 'index' in o:                        # engraved index on the top (bed) face, on the D-flat side
        ix = o['index']
        tx, tz = -n_dir[1], n_dir[0]
        w = ix['w'] / 2
        q = [(cxz[0] + n_dir[0] * r_ + tx * sw * w, cxz[1] + n_dir[1] * r_ + tz * sw * w)
             for r_, sw in ((ix['r'][0], -1), (ix['r'][1], -1), (ix['r'][1], 1), (ix['r'][0], 1))]
        cuts.append(_xz_prism(q, y1 - ix['depth'], y1 + 0.1))
    if 'top_ring' in o:                     # decorative ring on the top face (paint-fill optional)
        r0, r1 = o['top_ring']
        ring = cq.Solid.makeCylinder(r1, ENGRAVE_D + 0.1, V(cxz[0], y1 - ENGRAVE_D, cxz[1]), V(0, 1, 0)).cut(
            cq.Solid.makeCylinder(r0, ENGRAVE_D + 0.1, V(cxz[0], y1 - ENGRAVE_D, cxz[1]), V(0, 1, 0)))
        cuts.append(ring)
    return dc.one_solid(s.cut(dc.fuse_all(cuts)).clean())


# ----------------------------------------------------------------------------------------------- eyecup
def build_eyecup(L):
    E = L.EYECUP
    ax_y, ax_z = L.EYE_AXIS
    xb = E['box']['x']                      # lip x .. sleeve end x
    sl = E['sleeve']
    x_lip, x_end = xb[0], xb[1]
    x_face = sl['x'][0]                     # eyepiece eye-end face (-174.3)
    ri, ro = sl['r_in'], sl['r_in'] + sl['wall']
    r_lip, wall = E['r_lip'], 2.0
    flare = math.tan(math.radians(15.0))
    x_c0 = x_face - 0.5                     # cup starts 0.5 ahead of the eye-end face
    r_lip_out = ro + (x_c0 - x_lip) * flare
    r_lip_out = min(r_lip_out, r_lip)
    lip_in = r_lip_out - wall
    lip_r = ri - 2.05                       # inner lip radius (45 deg underside from the sleeve bore)
    x_lt = x_face - 2.05                    # rear end of the lip's flat tip (r = lip_r)
    x_l6 = x_lt - 1.2                       # eye-side face of the lip: a 1.2 flat tip, no knife edge
    r_l6 = lip_in - (x_l6 - x_lip) * flare
    prof = [(x_end, ri), (x_end, ro), (x_c0, ro), (x_lip, r_lip_out), (x_lip, lip_in), (x_l6, r_l6),
            (x_l6, lip_r), (x_lt, lip_r), (x_face, ri)]
    pl = cq.Plane(origin=V(0, ax_y, ax_z), xDir=V(1, 0, 0), normal=V(0, -1, 0))
    wp = cq.Workplane(pl).polyline(prof).close().revolve(360.0, (0, 0, 0), (1, 0, 0))
    wp = dc.safe_fillet(wp, cq.selectors.BoxSelector((x_lip - 0.1, ax_y - 30, ax_z - 30), (x_lip + 0.1, ax_y + 30, ax_z + 30)), 0.8)
    return dc.one_solid(wp.val())


# ----------------------------------------------------------------------------------------------- stick sleeve
def build_stick_sleeve(L):
    S, B = L.STICK_SLEEVE, L.STICK['body']
    b = S['box']
    outer = dc.safe_fillet(_wp(dc.box_solid(b)), '|X', 1.2)
    outer = dc.bed_chamfer(outer, L.PARTS['stick_sleeve']['face_down'], 0.4)
    cav = dict(x=(B['x'][0], b['x'][1] + 0.1), y=B['y'], z=B['z'])
    cav = dc.safe_fillet(_wp(dc.box_solid(cav)), '|X', 0.8).val()
    return dc.one_solid(outer.val().cut(cav).clean())


# ----------------------------------------------------------------------------------------------- contract
_BUILDERS = {'plunger': build_plunger, 'knob_exp': lambda L: build_knob(L, 'knob_exp'),
             'knob_fps': lambda L: build_knob(L, 'knob_fps'), 'eyecup': build_eyecup,
             'stick_sleeve': build_stick_sleeve}


def build_part(layout, part_id):
    return dc.wp_of(_BUILDERS[part_id](layout))


def build(layout):
    return {pid: build_part(layout, pid) for pid in _BUILDERS}
