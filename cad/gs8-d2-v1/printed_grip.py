# SPDX-License-Identifier: MIT
"""GS8 D2 printed parts, owner grip_small (r2: R2): black ASA base + grip (one print) and the battery cap.

MODULE CONTRACT (layout.MODULE_CONTRACT): build(layout) -> {part_id: Workplane} for base_grip and cap
(r2 R2: the skirts are gone), in ASSEMBLY coordinates (X forward, Y left, Z up; mm); PRINT at module level; build_part(layout, part_id).

Owner design choices (the layout fixes the envelopes and the interface positions; these are internal joints):
- r2 R2 (finding 3): the 2 skirts and the J5 dovetail joint are ELIMINATED. The base side faces are plain (no groove,
  no barb dimple); the tub lip notches are filled flush by the panel boss tabs, so the panel comes off along +Y with
  4 PH1 screws out and nothing else (NOTES.md "r2 R2 options"). The base stays a separate print on the J4 keyholes.
- J6 cap -> grip: the cap carries 2 keys INSIDE the bay (web 1.6 at y +-10.65..12.25, 0.65 clear of the 20 mm pack;
  head 1.0 into a groove in each side wall with a 45 deg lower face, so the cap hangs on 45 deg lips 1.6 thick).
  The grooves end at x -60 (closed stop, key rear contact) and run out forward through 2 notches at the front
  corners, so the cap slides +X to open. Detent: a 0.35 bump on each key tip clicks into a 0.3 dimple near the
  rear (the free bottom edge of each side wall flexes 0.1 as it passes).
  r2 R2: key top -106.5 -> -105.9 (groove top -105.65), so the 45 deg head is 1.4 at its tip (was 0.8) and the
  detent bump is 1.2 tall in z (was 0.6); every retention section is >= 1.2 (CRITICAL_FEATURES in layout.py).
- J13 run button: the switch drops straight into a cradle (shelf + rear stop + 45 deg side guides) under the
  base opening; its red cap presses on through the dia 13.6 hole from the front (teardrop roof toward -Z, the print
  top). The rear stop takes the press load. The base opening is shaped to the switch, run-lead and pigtail
  passages (all inside layout.BASE_OPENING), which leaves base over the rear stop.
"""
import math

import cadquery as cq

import d2_common as dc

V = cq.Vector
SQ2 = math.sqrt(2.0)

CAP_KEY = dict(web_y=(10.65, 12.25), head_y=13.25, head_low_z=-108.3, top_z=-105.8, rear_x=-60.0,   # r2 R2
               groove_top_z=-105.55, groove_y=13.5, bump=0.35, bump_x=-57.0, bump_z=(-107.2, -106.0), dimple_y=13.75,
               # FIXER r2: key top and groove top +0.1 (head tip 1.65 at the probe, hook class 1.6)
               pocket=dict(inset=5.0, half_w=8.5, floor=3.0, r=4.0))
# r2 R2: dimple_y 13.8 -> 13.75 keeps the detent arm (side-wall strip outside the groove) 1.25 at the dimple
CRADLE = dict(shelf_t=1.6, rear_t=1.6, rear_top_z=-20.2, guide_t=1.6, guide_top_z=-20.5, pad_boss_t=0.75)
# rear stop top -20.2: above the cap axis (z -21, the press line) and below the XT30 pair box (z -20..-14.8)
# pad boss: 0.75 on the front-wall inner face behind the 1.5 deep run pad, so the wall there is 1.75 (not 1.0)
JUNCTION_FILLET = 3.0
HEEL_CHAMFER = 1.0

_FD = {pid: dc.L.PARTS[pid]['face_down'] for pid in ('base_grip', 'cap')}
PRINT = {
    'base_grip': dict(
        face_down=_FD['base_grip'],
        supports='none. Prints upside down (base top on the bed): keyhole lips are the first 1.6 mm, the head '
                 'pockets bridge 18.5 (x), the nut-pocket ceiling bridges 11.4 round the dia 6.6 hole, the run-button '
                 'shelf and rear stop bridge 25 between the bay walls, the heel strap slots bridge 13, the dia 13.6 run '
                 'hole has a 45 deg teardrop roof, the cap grooves have 45 deg faces.',
        notes='ASA black, 4 perimeters, 25 % gyroid; 40 % modifier meshes 8 mm round the 3 counterbores and the nut '
              'pocket (r4: out/stl/modifiers/base_grip__mod_*.stl, load at their exported position). '
              'Brim 5 mm (102 mm tall column on a 70 x 116 base). Clean the keyhole lips and the cap grooves with a '
              'file; test-slide the cap before assembly.'),
    'cap': dict(face_down=_FD['cap'], supports='none (key heads 45 deg; detent bumps 0.35 proud, 1.2 tall)',
                notes='ASA black, bottom (thumb grooves + open arrow) on the bed; 100 % or 6 perimeters.'),
}


# ----------------------------------------------------------------------------------------------- small helpers
def _xz_prism(poly, y0, y1):
    """Prism from an (x, z) polygon, over y0..y1."""
    pl = cq.Plane(origin=V(0, y1, 0), xDir=V(1, 0, 0), normal=V(0, -1, 0))
    return dc._prism(poly, pl, 0.0, y1 - y0)


def _yz_prism(poly, x0, x1):
    """Prism from a (y, z) polygon, over x0..x1."""
    pl = cq.Plane(origin=V(x0, 0, 0), xDir=V(0, 1, 0), normal=V(1, 0, 0))
    return dc._prism(poly, pl, 0.0, x1 - x0)


def _xy_prism(poly, z0, z1):
    """Prism from an (x, y) polygon, over z0..z1."""
    pl = cq.Plane(origin=V(0, 0, z0), xDir=V(1, 0, 0), normal=V(0, 0, 1))
    return dc._prism(poly, pl, 0.0, z1 - z0)


def _box(x0, x1, y0, y1, z0, z1):
    return dc.box_solid(dict(x=(x0, x1), y=(y0, y1), z=(z0, z1)))


def _rbox(x0, x1, y0, y1, z0, z1, r=0.0):
    """Box with its vertical (Z) edges rounded by r."""
    wp = cq.Workplane('XY').box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))
    if r > 0:
        wp = wp.edges('|Z').fillet(r)
    return wp.val()


def _wp(s):
    return cq.Workplane('XY').newObject([s])


def _sorted(a, b):
    return (a, b) if a <= b else (b, a)


# ----------------------------------------------------------------------------------------------- base_grip
def _base_body(L):
    """Slab (5 mm front chamfer, bed chamfers) + grip column (er 9, heel chamfer) + R3 web fillet."""
    BS, G = L.BASE, L.GRIP
    (x0, x1), (y0, y1), (z0, z1) = BS['x'], BS['y'], BS['z']
    ch, bc = BS['front_chamfer'], L.FDM['BED_CHAMFER']
    rear_ch = 1.0
    slab = _xz_prism([(x0 + rear_ch, z0), (x1 - ch, z0), (x1, z0 + ch), (x1, z1 - bc), (x1 - bc, z1),
                      (x0 + bc, z1), (x0, z1 - bc), (x0, z0 + rear_ch)], y0, y1)
    slab_wp = _wp(slab)
    for yy in (y0, y1):
        sel = cq.selectors.BoxSelector((x0 - 1, yy - 0.1, z1 - 0.05), (x1 + 1, yy + 0.1, z1 + 0.05))
        slab_wp = dc.safe_chamfer(slab_wp, sel, bc)
    (gx0, gx1), (gy0, gy1), gz0 = G['x'], G['y'], G['z'][0]
    col = _wp(_rbox(gx0, gx1, gy0, gy1, gz0, z0 + 0.1, G['er']))
    col = dc.safe_chamfer(col, '<Z', HEEL_CHAMFER)
    body = slab_wp.val().fuse(col.val()).clean()
    sel = cq.selectors.BoxSelector((gx0 - 0.5, gy0 - 0.5, z0 - 0.05), (gx1 + 0.5, gy1 + 0.5, z0 + 0.05))
    return dc.safe_fillet(_wp(body), sel, JUNCTION_FILLET).val()


def _cradle(L):
    """Run-button cradle inside the bay: shelf + rear stop (bridges between the bay walls) + 45 deg side guides."""
    RB, SL, bay = L.RUN_BTN, L.FDM['SLIDE'], L.GRIP['bay']
    bx0 = RB['body']['x'][0]
    by0, by1 = RB['body']['y']
    bz0 = RB['body']['z'][0]
    c = CRADLE
    rx1 = bx0 - SL                          # rear stop front face (-35.25)
    rx0 = rx1 - c['rear_t']
    ya, yb = bay['y'][0] - 0.1, bay['y'][1] + 0.1
    shelf = _box(rx0, bay['x'][1] + 0.1, ya, yb, bz0 - c['shelf_t'], bz0)
    rear = _box(rx0, rx1, ya, yb, bz0 - c['shelf_t'], c['rear_top_z'])
    G = L.GRIP
    p = RB['pad']
    xw = G['x'][1] - G['wall']               # front-wall inner face (-25.5)
    boss = _box(xw - c['pad_boss_t'], xw + 0.1, p['y'][0] - 2.3, p['y'][1] + 2.3, p['z'][0] - 1.0, p['z'][1] + 1.0)
    # r2 R2: y +-7.0 -> +-8.3: the dia 13.6 run hole (r 6.8) left 0.2 slivers of boss beside it (trial screen 0.33)
    # r2 R2: the pad boss now runs 1.0 above the pad recess top (was to the bay top -9.9): the front wall at the
    # recess top was 1.0 (z -9.9..-7); the base opening stops at the boss face (_base_cuts) so it is not cut away
    parts = [shelf, rear, boss]
    run = c['guide_top_z'] - bz0            # 7.5: the guide top drops 45 deg toward the front
    for g0, g1 in ((by1 + SL, by1 + SL + c['guide_t']), (by0 - SL - c['guide_t'], by0 - SL)):
        parts.append(_xz_prism([(rx1 - 0.05, bz0 - 0.05), (rx1 - 0.05, c['guide_top_z']), (rx1 + run, bz0 - 0.05)], g0, g1))
    return dc.fuse_all(parts)


def _cap_groove_cuts(L):
    """Cap-key grooves in the bay side walls (closed at the rear, out through the front) + front notches + dimples."""
    k, SL, G = CAP_KEY, L.FDM['SLIDE'], L.GRIP
    gz0 = G['z'][0]
    xf = G['x'][1] + 3.0
    cuts = []

    def zl(y):                              # lower 45 deg face of the groove (key face offset 0.25 normal)
        return k['head_low_z'] + (y - k['web_y'][1]) - SL * SQ2
    for sg in (1.0, -1.0):
        ya, yb = k['web_y'][1] - 0.05, k['groove_y']
        poly = [(sg * ya, zl(ya)), (sg * yb, zl(yb)), (sg * yb, k['groove_top_z']), (sg * ya, k['groove_top_z'])]
        cuts.append(_yz_prism(poly, k['rear_x'], xf))
        # front-corner exit (r2 R2): the web passage runs from the bottom only inside the bay face (y 12.5); the head
        # rides its own 45 deg groove; forward of xc the corner strip outside the groove would be under 1.2, so the
        # corner is cut out to the outside there (was a 0.5-1.0 feather, trial screen 1.17)
        n0, n1 = _sorted(sg * (k['web_y'][0] - SL), sg * G['bay']['y'][1])
        cuts.append(_box(-33.0, xf, n0, n1, gz0 - 0.5, k['groove_top_z']))           # web passage
        cy0 = G['y'][1] - G['er']                                                   # corner centre y (6.0)
        dy = k['groove_y'] + L.FDM['MIN_WALL'] - cy0                                # 8.7 (strip >= 1.2)
        xc = G['x'][1] - G['er'] + math.sqrt(max(0.0, G['er'] ** 2 - dy ** 2))      # -29.70
        m0, m1 = _sorted(sg * (k['web_y'][0] - SL), sg * (G['y'][1] + 1.0))
        cuts.append(_box(xc, xf, m0, m1, gz0 - 0.5, k['groove_top_z']))             # corner cut-out
        d0, d1 = _sorted(sg * (k['groove_y'] - 0.1), sg * k['dimple_y'])
        half = 0.9 + SL
        cuts.append(_box(k['bump_x'] - half, k['bump_x'] + half, d0, d1, k['bump_z'][0] - SL, k['top_z'] + 0.1))
    return cuts


def _base_cuts(L):
    BS, G, RB, SL = L.BASE, L.GRIP, L.RUN_BTN, L.FDM['SLIDE']
    (gx0, gx1), gz0 = G['x'], G['z'][0]
    bay = G['bay']
    cuts = _cap_groove_cuts(L)
    p = RB['pad']                           # run-button pad, recessed; the cut also clears the web fillet above it
    cuts.append(_box(gx1 - p['depth'], gx1 + JUNCTION_FILLET + 1.0, p['y'][0], p['y'][1], p['z'][0], p['z'][1]))
    S = L.STRAP                             # 2 heel slots (rear wall), 2 base slots + webbing recess on the base top
    for b in S['lower_slots']:
        cuts.append(_box(b['x'][0] - 1.0, b['x'][1] + 1.0, b['y'][0], b['y'][1], b['z'][0], b['z'][1]))
    for b in S['upper_slots']:
        cuts.append(_box(b['x'][0], b['x'][1], b['y'][0], b['y'][1], b['z'][0] - 0.5, b['z'][1] + 0.5))
    r = S['upper_recess']
    cuts.append(_box(r['x'][0], r['x'][1], r['y'][0], r['y'][1], r['z'][0], r['z'][1] + 0.5))
    cuts += [dc.keyhole_slot(t) for t in L.TONGUES]          # J4 windows, neck slots, head pockets
    for s in L.SCREWS:                      # s_b1 / s_b2: dia 7 x 6 counterbore + dia 3.4 through the 2.0 under the head
        if s['head_part'] == 'base_grip':
            cz = s['cbore']['z']
            cuts.append(dc.counterbore(s['head_point'], s['axis'], d_cb=s['cbore']['d'], depth=cz[1] - cz[0],
                                       d_clear=L.PT['clear_d'], through=BS['z'][1] - s['head_point'][2] + 0.1))
    T = L.TRIPOD                            # hex pocket from the top, dia 6.6 hole + 0.7 entry chamfer
    ac = T['pocket_af'] / math.cos(math.radians(30))
    cuts.append(cq.Workplane('XY').workplane(offset=T['nut_z'][0]).center(T['x'], T['y'])
                .polygon(6, ac).extrude(BS['z'][1] - T['nut_z'][0] + 0.1).val())
    cuts.append(cq.Solid.makeCylinder(T['hole_d'] / 2, T['nut_z'][0] - BS['z'][0] + 0.2,
                                      V(T['x'], T['y'], BS['z'][0] - 0.1)))
    cuts.append(cq.Solid.makeCone(T['hole_d'] / 2 + 0.8, T['hole_d'] / 2, 0.8, V(T['x'], T['y'], BS['z'][0] - 0.1)))
    O, FH = L.BASE_OPENING, L.FLOOR_HOLES   # opening shaped to the switch drop, run-lead and pigtail passages
    bx0, (by0, by1) = RB['body']['x'][0], RB['body']['y']
    rects = [(bx0 - SL, gx1 - G['wall'] - CRADLE['pad_boss_t'], by0 - SL, by1 + SL),   # r2 R2: stop at the pad boss
             (FH['run_lead']['x'][0], FH['run_lead']['x'][1], FH['run_lead']['y'][0], FH['run_lead']['y'][1]),
             (FH['pigtail']['x'][0], FH['pigtail']['x'][1], FH['pigtail']['y'][0], FH['pigtail']['y'][1])]
    for xa, xb_, ya, yb in rects:
        xa, xb_ = max(xa, O['x'][0]), min(xb_, O['x'][1])
        ya, yb = max(ya, O['y'][0]), min(yb, O['y'][1])
        cuts.append(_box(xa, xb_, ya, yb, bay['z'][1] - 0.5, O['z'][1] + 0.5))
    return cuts


def build_base_grip(L):
    G, RB = L.GRIP, L.RUN_BTN
    s = _base_body(L)
    bay = G['bay']                          # battery bay: walls 2.5 all round (inner corner r = er - wall)
    s = s.cut(_rbox(bay['x'][0], bay['x'][1], bay['y'][0], bay['y'][1], G['z'][0] - 0.5, bay['z'][1],
                    G['er'] - G['wall']))
    s = s.fuse(_cradle(L)).clean()
    s = s.cut(dc.fuse_all(_base_cuts(L))).clean()
    cy, cz = RB['cap']['c']                 # run hole through the front wall, teardrop roof toward -Z (print up)
    x_in = G['x'][1] - G['wall'] - CRADLE['pad_boss_t']
    s = s.cut(dc.teardrop(RB['wall_hole_d'] / 2, x_in - 0.6, G['x'][1] + 0.6, (0.0, cy, cz),
                          (1, 0, 0), up=(0, 0, -1))).clean()
    return dc.one_solid(s)


# ----------------------------------------------------------------------------------------------- cap
def build_cap(L):
    """Battery door: R9 plate, top pocket, 2 keys (web + 45 deg head) with detent bumps, thumb grooves, arrow."""
    C, k = L.CAP, CAP_KEY
    (x0, x1), (y0, y1), (z0, _) = C['box']['x'], C['box']['y'], C['box']['z']
    z1 = min(C['box']['z'][1], L.GRIP['z'][0] - 0.1)
    # plate top 0.1 under the grip heel (-110.1), also if the envelope grows up to hold the keys
    wp = _wp(_rbox(x0, x1, y0, y1, z0, z1, C['er']))
    wp = dc.bed_chamfer(wp, L.PARTS['cap']['face_down'])
    wp = dc.safe_chamfer(wp, '>Z', 0.5)
    s = wp.val()
    pk = k['pocket']
    s = s.cut(_rbox(x0 + pk['inset'], x1 - pk['inset'], -pk['half_w'], pk['half_w'], z0 + pk['floor'], z1 + 0.1, pk['r']))
    outline = _rbox(x0, x1, y0, y1, z1 - 0.2, k['top_z'] + 0.1, C['er'])
    wy0, wy1 = k['web_y']
    hz = k['head_low_z']
    hy = k['head_y']
    for sg in (1.0, -1.0):
        poly = [(sg * wy0, z1 - 0.05), (sg * wy1, z1 - 0.05), (sg * wy1, hz), (sg * hy, hz + (hy - wy1)),
                (sg * hy, k['top_z']), (sg * wy0, k['top_z'])]
        # FIXER P7/A-F6: end the key flat 1.2 inside the R9 front corner (the outline intersect left a 0.38 feather)
        er = C['er']
        dy = max(0.0, hy - (y1 - er))
        x_end = x1 - er + math.sqrt(max(0.0, er * er - dy * dy)) - L.FDM['MIN_WALL'] if dy > 0 else x1 + 1.0
        key = _yz_prism(poly, k['rear_x'], x_end).intersect(outline)
        bx, b = k['bump_x'], k['bump']
        bump = _xy_prism([(bx - 0.5 - b - 0.05, sg * (hy - 0.05)), (bx - 0.5, sg * (hy + b)), (bx + 0.5, sg * (hy + b)),
                          (bx + 0.5 + b + 0.05, sg * (hy - 0.05))], k['bump_z'][0], k['bump_z'][1])
        s = s.fuse(key).fuse(bump)
    cuts = [_box(xg - 0.6, xg + 0.6, -9.0, 9.0, z0 - 0.1, z0 + 0.5) for xg in (x0 + 5.0, x0 + 7.5, x0 + 10.0)]
    ax = (x0 + x1) / 2 + 6.0                # open arrow (+X), engraved 0.5 in the bottom
    cuts.append(_box(ax - 9.0, ax - 3.5, -0.6, 0.6, z0 - 0.1, z0 + 0.5))
    cuts.append(_xy_prism([(ax - 4.0, -3.0), (ax + 0.5, 0.0), (ax - 4.0, 3.0)], z0 - 0.1, z0 + 0.5))
    s = s.cut(dc.fuse_all(cuts)).clean()
    return dc.one_solid(s)


# ----------------------------------------------------------------------------------------------- contract
_BUILDERS = {'base_grip': build_base_grip, 'cap': build_cap}   # r2 R2: skirt_l / skirt_r eliminated (finding 3)


def build_part(layout, part_id):
    return dc.wp_of(_BUILDERS[part_id](layout))


def build(layout):
    return {pid: build_part(layout, pid) for pid in _BUILDERS}
