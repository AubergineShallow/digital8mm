# SPDX-License-Identifier: MIT
"""GS8 D2: the satin-silver ASA tub (owner: tub). MODULE CONTRACT in layout.py.

One print, right wall on the bed (face_down -Y, print-up = assembly +Y). Open to the left (+Y) above the lip and open
at the top (the hood band seats on the wall tops z 97.3). Walls: rear, right, floor, full front wall, left lip.

Carries (layout joint in brackets):
  floor   4 Pi bosses (OD 9.0, head pockets) [J9], 2 Pi-keeper PT bosses [J9, R1 r2], run-lead + pigtail holes, 2 s_b clearance holes,
          2 keyhole T-tongues [J4], left lip + 2 boss notches + a 45 deg lip gusset (print support for the lip) [J3]
  front   r5 J7-R: lip (dia 32.4) + BFAR counterbore (dia 37.5) teardrops, 3 M3 insert bosses for the lens collar
          (no pins, no seat: the camera floats) [J7], rib_l (rib_r only if it clears the Pi drop
          path; with the current layout it does not), plunger hole (+ flange recess if needed) [J10], microSD slot,
          exhaust windows (band + corner) [J14], hood catch ledge hk3 [J1]
  rear    EVF bore 29.3 (teardrop) + -Y half-collar (the saddle), OLED cell + window, EVF board slot (2 rails grown
          from the right wall) [J8], stick scoop + guide [J11], hood catch ledge hk4
  right   2 PT pads + counterbores (s_r1, s_r2) [s4], exhaust + X1203 vent slots [J14], hood catch ledges hk1, hk2

Print-driven shape choices (all inside TUB_BOX; see NOTES.md, tub owner):
  - the -Y body corners get a 45 deg flat where the R5 meets the bed (no fillet on the bed face);
  - every floor/wall feature either grows from the right wall (bed) or has its -Y faces at 45 deg, except the two
    T-tongue -Y wings (2 paint-on supports, below);
  - R1 r2: the 4 Pi floor hooks are deleted (finding 1); the 2 keeper bosses are teardrop prisms with the chin
    toward -Y (print down); s_k2's chin apex stops 0.25 off the X1203 edge (y 23.95), its +Y side is clipped at
    the panel seam (y 31.9) and merges into the lip gusset below z 7.6;
  - rib_l is a 45 deg gusset from the front wall to the panel plane (y 24.1..32.2), notched for the panel locate rib;
  - the T-tongue -Y wings face the bed (undercut): 2 small paint-on supports (PRINT); r5: the lens collar is its own
    part (printed_collar.py) bolted to 3 insert bosses here (teardrop profiles, apex -Y = print down);
  - no exhaust baffle wall: BAFFLE lies over the Pi PCB edge (x <= -6.0), any wall there blocks the stack drop.
Tests: test_tub.py (volume, envelope, beds, keep-outs, COTS boxes), sweep_tub.py (insertions vs the tub alone).
"""
import math

import cadquery as cq

import d2_common as dc

V = cq.Vector
SQ2 = math.sqrt(2.0)

PRINT = {
    'tub': dict(
        face_down='-Y',
        supports='2 small paint-on supports under the -Y wings of the 2 keyhole T-tongue heads (each about 7.8 x 1.6, about 17 mm above the bed, '
                 'the T undercut cannot face the bed); nothing else',
        notes='Right wall on the bed; 4 perimeters, 25 % gyroid; 40 % infill modifier meshes (r4: load all 7, r5: 10 with s_c1..s_c3 round the insert bosses; '
              'out/stl/modifiers/tub__mod_*.stl at their exported position: 8 mm round every PT pilot, including the 2 s_r '
              'counterbore pads where the screw heads bear). Brim 5 mm (ASA warp on a 151 x 101 footprint). Bridges: window/slot tops <= 20 mm, the '
              'Ø7 counterbore shoulders, the cell -Y wall (13.9), the scoop roof (20). Teardrop bores 29.3, r5 lip 32.4 and BFAR counterbore 37.5 '
              'open toward +Y (print up). r5: 3 M3 heat-set inserts (bench, before step 3) flush -0.1 from the front face; '
              '3 insert bosses grow -X from the front wall with 45 deg undersides (LL: 3.3 x 2.4 flat chin, bridged). R1 r2: the 2 Pi-keeper bosses are teardrop prisms with the chin down '
              '(s_k2 has a 1.0 flat at its apex); their 40 % modifiers are tub__mod_s_k1/s_k2.'),
}

PLANES = {'xy': ((0, 0, 1), (1, 0, 0), (0, 0, 1)), 'yz': ((1, 0, 0), (0, 1, 0), (1, 0, 0)),
          'xz': ((0, 1, 0), (1, 0, 0), (0, -1, 0))}


def _prism(pts, key, a0, a1):
    """Closed polygon extruded between a0 and a1 along the third axis.
    key 'xy': pts (x, y), along Z;  'yz': pts (y, z), along X;  'xz': pts (x, z), along Y."""
    ax, xd, nm = PLANES[key]
    o = a1 if key == 'xz' else a0          # the xz plane's normal is -Y, so start at a1
    org = tuple(o * c for c in ax)
    pl = cq.Plane(origin=V(*org), xDir=V(*xd), normal=V(*nm))
    return cq.Workplane(pl).polyline(pts).close().extrude(a1 - a0).val()


def _bx(L, x0, x1, y0, y1, z0, z1):
    return dc.box_solid(L.B(x0, x1, y0, y1, z0, z1))


def _cyl(r, p0, axis, length):
    return cq.Solid.makeCylinder(r, length, V(*p0), V(*axis))


# ----------------------------------------------------------------------------------------------- shell
def _shell(L):
    """Rounded outer body (R5 vertical edges, 45 deg flats at the bed), minus the cavity and the panel zone."""
    x0, x1, y0, y1, h = L.X_REAR, L.XT1, L.YR, L.YL, L.ZT1
    outer = (cq.Workplane('XY').box(x1 - x0, y1 - y0, h, centered=False).translate((x0, y0, 0))
             .edges('|Z').fillet(L.RV).val())
    s = L.RV / SQ2
    tris = []
    for cxr, sgn in ((x0 + L.RV, -1.0), (x1 - L.RV, 1.0)):      # rear-right and front-right corner centres
        p45 = (cxr + sgn * s, y0 + L.RV - s)
        xb = p45[0] - sgn * (p45[1] - y0)                        # 45 deg line from p45 down to the bed plane
        tris.append(_prism([(cxr, y0), (xb, y0), p45], 'xy', 0.0, h))
    outer = outer.fuse(*tris).clean()
    cav = (cq.Workplane('XY').box(L.X_FW_IN - L.X_RW_IN, L.SPLIT - L.Y_RW_IN, h, centered=False)
           .translate((L.X_RW_IN, L.Y_RW_IN, L.T)).edges('|Z').edges('<Y').fillet(0.5).val())   # r0.5: Pi corner
    zone = _bx(L, x0 - 1, x1 + 1, L.SPLIT, y1 + 1, L.LIP['z'][1], h + 1)   # the panel's place above the lip
    return outer.cut(cav, zone).clean()


# ----------------------------------------------------------------------------------------------- floor (J3, J4, J9)
# R1 r2 (REVIEW finding 1): r1's 4 Pi floor snap hooks (_pi_hook, hook_t, hook_root_z, pi_hook_strain, their floor
# reliefs) are DELETED: no release access, removal broke the tub. The stack sits and locates on the 4 Pi bosses; the
# removable printed keeper (printed_keeper.py) holds it down on 2 PT 3.0 x 12 into the 2 bosses below.
def _keeper_boss(L, b):
    """Keeper PT boss: teardrop prism (chin toward -Y = print down, 45 deg flanks), optionally an obround along X and
    clipped at clip_y (panel side), from the floor to PI_KEEPER boss_top; returns (boss, pilot cut)."""
    K = L.PI_KEEPER
    (cx, cy), r, o = b['c'], b['r'], b['obround']
    z0, z1 = L.T - 0.05, K['boss_top']
    s = r / SQ2
    parts = [_cyl(r, (cx - o / 2, cy, z0), (0, 0, 1), z1 - z0), _cyl(r, (cx + o / 2, cy, z0), (0, 0, 1), z1 - z0),
             _prism([(cx - o / 2 - s, cy - s), (cx + o / 2 + s, cy - s)] +
                    ([(cx + o / 2, cy - r * SQ2), (cx - o / 2, cy - r * SQ2)] if o > 0 else [(cx, cy - r * SQ2)]),
                    'xy', z0, z1)]
    if o > 0:
        parts.append(_bx(L, cx - o / 2, cx + o / 2, cy - r, cy + r, z0, z1))
    boss = parts[0].fuse(*parts[1:]).clean()
    if b.get('clip_y') is not None or b.get('chin_y') is not None:   # FIXER r2: chin_y cuts the teardrop apex flat
        y_lo = b['chin_y'] if b.get('chin_y') is not None else cy - 2 * r
        y_hi = b['clip_y'] if b.get('clip_y') is not None else cy + 2 * r
        boss = boss.intersect(_bx(L, cx - r - o - 1, cx + r + o + 1, y_lo, y_hi, z0 - 0.1, z1 + 0.1))
    _, pilot = dc.pt_boss((cx, cy, z1), (0, 0, -1), od=2 * r, height=z1 - z0, pilot_depth=z1 - K['pilot_bottom_z'])
    return boss, pilot


def _floor(L):
    adds, cuts, late = [], [], []
    PB = L.PI_BOSS
    od = max(PB['od'], PB['head_pocket_d'] + 2 * dc.MIN_WALL_LOADED)   # 8.8: a 7.0 boss leaves a 0.7 pocket wall
    for (x, y) in L.PI['holes']:
        boss = dc.teardrop(od / 2, L.T - 0.05, PB['z'][1], (x, y, 0.0), (0, 0, 1), up=(0, -1, 0))
        adds.append(boss.intersect(_bx(L, x - 9, x + 9, L.YR + 0.5, y + 9, 0, PB['z'][1] + 1)))   # chin stays inside
        cuts.append(_cyl(PB['head_pocket_d'] / 2, (x, y, PB['z'][1] - PB['head_pocket_depth']), (0, 0, 1),
                         PB['head_pocket_depth'] + 0.1))
    for b in L.PI_KEEPER['bosses'].values():                       # R1 r2: keeper bosses (the hooks are gone)
        boss, pilot = _keeper_boss(L, b)
        adds.append(boss)
        cuts.append(pilot)
    J = getattr(L, 'J4_LOCK', None)                                # FIXER r2: J4 base lock boss (s_j, from below)
    if J is not None:
        (jx, jy), jr = J['c'], J['od'] / 2
        adds.append(dc.teardrop(jr, L.T - 0.05, J['top'], (jx, jy, 0.0), (0, 0, 1), up=(0, -1, 0)))
        sj = next(s for s in L.SCREWS if s['id'] == J['screw'])
        cuts.append(dc.pt_boss((jx, jy, 0.0), (0, 0, 1), pilot_depth=sj['tip'][2] + L.PT['tip_reserve'])[1])
    for b in L.FLOOR_HOLES.values():
        cuts.append(_bx(L, *b['x'], *b['y'], -0.1, L.T + 0.1))
    for s in L.SCREWS:
        if tuple(s['axis']) == (0, 0, 1) and s['into'].split()[0] == 'panel':   # s_b1, s_b2 pass the floor
            cuts.append(_cyl(L.PT['clear_d'] / 2, (s['head_point'][0], s['head_point'][1], -0.1), (0, 0, 1), L.T + 0.2))
    for t in L.TONGUES:
        adds.append(dc.keyhole_tongue(t, chamfer_minus_y=False))      # the helper's 45 deg end leaves a 0.6 feather
                                                                       # and still floats: -Y wings are supported
    # lip gusset: 45 deg support under the left lip (the lip is a 5.4 mm ledge in print)
    zl = L.LIP['z'][1]
    adds.append(_prism([(L.SPLIT - (zl - L.T), L.T - 0.05), (L.SPLIT + 0.01, L.T - 0.05), (L.SPLIT + 0.01, zl)],
                       'yz', L.X_RW_IN - 0.05, L.X_FW_IN + 0.05))
    se = dc.SEAM
    for n in L.LIP_NOTCHES:                                             # panel bosses pass here (lip + gusset)
        cuts.append(_bx(L, *n['x'], L.SPLIT - (zl - L.T) - 1.0, L.YL + 0.1, L.T, zl + 0.1))
    ko = L.KEEPOUTS['ko_run_floor']                                     # run lead to the panel side
    cuts.append(_bx(L, ko['x'][0] - se, ko['x'][1] + se, L.SPLIT - (zl - L.T) - 1.0, L.SPLIT + 0.01, L.T, zl + 0.1))
    return adds, cuts, late


# ----------------------------------------------------------------------------------------------- hood catch ledges (J1)
def _ledge(L, hk):
    """Catch ledge on a wall inner face: 0.8 proud, catch face (underside) at catch_z, 45 deg top chamfer; on the
    front and rear walls the -Y end is 45 deg (print). Length = hook w + 2."""
    H = L.HOOK
    zc, e, h = H['catch_z'], H['ledge'], H['ledge_h']
    half = H['w'] / 2 + 1.0
    # FIXER r2: a 45 deg return hook (hk3/hk4) gets a matching sloped underside, parallel to the tooth's catch face at
    # a normal gap of `play` (z(u) = tooth top + play / cos(ret) + (u - u_tip) tan(ret), u = distance in from the wall)
    ret = math.radians(hk.get('ret_deg', 0.0))
    u_tip = e + L.FDM['SLIDE'] - H['tooth']
    if ret > 0:
        zu = lambda u: H['tooth_top_z'] + H['play'] / math.cos(ret) + (u - u_tip) * math.tan(ret)   # noqa: E731
        z_in, z_out = zu(-0.05), zu(e)
    else:
        z_in = z_out = zc
    if hk['wall'] == 'right':
        f, s = hk['y_face'], hk['x']
        return _prism([(f - 0.05, z_in), (f + e, z_out), (f + e, zc + h - e), (f - 0.05, zc + h + 0.05)], 'yz',
                      s - half, s + half)
    f, s = hk['x_face'], hk['y']
    n = hk['normal'][0]                                     # +1 rear wall (inward +X), -1 front wall (inward -X)
    led = _prism([(f - 0.05 * n, z_in), (f + e * n, z_out), (f + e * n, zc + h - e), (f - 0.05 * n, zc + h + 0.05)],
                 'xz', s - half, s + half)
    y0 = s - half
    cham = _prism([(f, y0), (f + (e + 0.2) * n, y0 + e + 0.2), (f + (e + 0.2) * n, y0 - 0.1), (f, y0 - 0.1)], 'xy',
                  zc - 0.1, zc + h + 0.2)
    return led.cut(cham)


# ----------------------------------------------------------------------------------------------- front wall (J7, J10, J14)
def _insert_boss(L, b):
    """r5 (J7-R): lens-collar anchor boss on the front-wall inner face, x -7.6..-5.2 (judge 3 Pi-drop rule), OD 8. Outer
    profile = teardrop with the apex toward -Y (print down: 45 deg underside); LL: chin cut flat at chin_y (0.3 off the
    pi5 COTS box, a 3.3 x 2.4 flat bridged from the wall as the s_k2 chin). Cuts: M3 heat-set insert bore dia 4.0 from
    the OUTER face (x -2.7) to x -6.9 (insert 4.0 + 0.2), then the M3 clearance dia 3.4 through to x -7.6."""
    (y, z), r = b['c'], b['od'] / 2
    x0, x1 = b['x']
    boss = dc.teardrop(r, 0.0, x1 + 0.05 - x0, (x0, y, z), (1, 0, 0), up=(0, -1, 0))
    if b.get('chin_y') is not None:
        boss = boss.intersect(_bx(L, x0 - 0.1, x1 + 0.1, b['chin_y'], y + r + 1.0, z - 2 * r, z + 2 * r))
    bx0, bx1 = b['bore_x']                     # (-2.7, -6.9): from the outer face inward
    bore = _cyl(L.M3['insert']['bore_d'] / 2, (bx0 + 0.1, y, z), (-1, 0, 0), bx0 + 0.1 - bx1)
    clear = _cyl(L.M3['clear_d'] / 2, (bx1 + 0.05, y, z), (-1, 0, 0), bx1 + 0.05 - b['clear_x'][1] + 0.2)
    return boss, [bore, clear]


def _front(L):
    adds, cuts = [], []
    C = L.CAM
    fw = L.X_FW_IN
    ly, lz = L.LENS_AXIS
    # r5 (J7-R, judge 3 s6.4): r4's dia 36.5 seat bore + 2 pins are replaced by the lip (dia 32.4, land x -3.9..-2.7)
    # and the counterbore round the BFAR head (dia 37.5, x -5.3..-3.9); both teardrops open toward +Y (print up).
    # The camera floats: the BFAR face stands lip_gap 0.5 behind the lip (a catch, never a seat).
    cb0, cb1 = C['cb_x']
    cuts.append(dc.teardrop(C['lip_d'] / 2, 0.0, L.XT1 + 0.2 - cb0, (cb0, ly, lz), (1, 0, 0), up=(0, 1, 0)))
    cuts.append(dc.teardrop(C['cb_d'] / 2, 0.0, cb1 - cb0, (cb0, ly, lz), (1, 0, 0), up=(0, 1, 0)))
    for b in getattr(L, 'TUB_INSERT_BOSSES', {}).values():     # r5: 3 lens-collar insert bosses (TL, TR, LL)
        boss, bc = _insert_boss(L, b)
        adds.append(boss)
        cuts.extend(bc)
    rl = L.RIBS['rib_l']                       # 45 deg gusset from the front wall, widened to the panel plane
    x0, y0 = rl['x'][0], rl['y'][0]
    adds.append(_prism([(fw + 0.05, y0), (fw + 0.05, L.SPLIT), (x0, L.SPLIT), (x0, y0 + (fw - x0))], 'xy',
                       rl['z'][0] - 0.05, rl['z'][1]))
    pr = L.PANEL_LOCATE_RIBS[0]                # notch for the panel's front locate rib (LOCATE all round)
    lo = dc.LOCATE
    if pr['z'][0] - lo < rl['z'][1]:           # (layout 41.3 > rib top 41: no notch needed)
        cuts.append(_bx(L, pr['x'][0] - lo, fw, pr['y'][0] - lo, L.SPLIT + 0.1, pr['z'][0] - lo, rl['z'][1] + 0.1))
    rr = L.RIBS.get('rib_r')                   # built only if it clears the Pi stack's vertical drop path (J9)
    px, py = L.COTS['pi5']['box']['x'], L.COTS['pi5']['box']['y']
    if rr is None:
        pass                                   # INTEGRATOR T3: rib_r deleted from the layout
    elif not (rr['x'][0] < px[1] + dc.SLIDE and rr['y'][1] > py[0] - dc.SLIDE):
        adds.append(_bx(L, rr['x'][0], fw + 0.05, rr['y'][0] - 0.05, rr['y'][1], rr['z'][0], rr['z'][1]))
    else:
        dc.NOTES.append('rib_r omitted: x %.1f..%.1f / y %.1f..%.1f lies in the Pi stack drop path (pi5 box x <= %.2f, '
                        'y >= %.1f); see NOTES.md interface request' % (rr['x'][0], rr['x'][1], rr['y'][0], rr['y'][1],
                                                                     px[1], py[0]))
    for b in (L.PLUNGER['tub_hole'], L.SD_SLOT):
        cuts.append(_bx(L, fw - 0.1, L.XT1 + 0.1, *b['y'], *b['z']))
    PL = L.PLUNGER                             # flange stop face = flange rear - travel; recess the outer face if
    stop = PL['flange']['x'][0] - PL['travel'] # it lies inside the wall (grip_small request 3: flange -2.5 -> 0.4)
    if stop < L.XT1 - 0.01:                    # recess = flange footprint + SEAM (the hood pocket is a channel now)
        fl, se = PL['flange'], dc.SEAM
        cuts.append(_bx(L, stop, L.XT1 + 0.1, fl['y'][0] - se, fl['y'][1] + se, fl['z'][0] - se, fl['z'][1] + se))
    for k in ('out_band', 'out_corner'):       # one window each behind the hood slot fields
        w = L.VENTS[k]['tub_window']
        cuts.append(_bx(L, fw - 1.0, L.XT1 + 0.1, *w['y'], *w['z']))
    return adds, cuts


# ----------------------------------------------------------------------------------------------- rear wall (J8, J11)
def _rear(L):
    adds, cuts = [], []
    E = L.EVF
    ey, ez = E['axis']
    rw, rb = L.X_RW_IN, E['bore_d'] / 2
    sp_end = E['spigot']['a'][1]                                  # -149.5
    cuts.append(dc.teardrop(rb, -0.1, L.T + 0.1, (L.X_REAR, ey, ez), (1, 0, 0), up=(0, 1, 0)))
    # FIXER r2: the bore's teardrop roof (apex y ey + rb sqrt2 = 36.7) runs out through the panel seam plane (y 32.2)
    # and left a 45 deg feather in the rear wall end face (screen sample 0.25 at z 82.6). Notch the end face MIN_WALL
    # deep wherever that wedge is thinner than MIN_WALL (|z - ez| < 5.7); behind the hood housing front plate.
    hz = ey + rb * SQ2 - (L.SPLIT - dc.MIN_WALL)
    if hz > 0:
        cuts.append(_bx(L, L.X_REAR - 0.1, L.X_RW_IN + 0.1, L.SPLIT - dc.MIN_WALL, L.SPLIT + 0.1, ez - hz, ez + hz))
    c = E['collar']                                               # -Y half-collar = the saddle
    col = _bx(L, rw - 0.05, c['x'][1], c['y'][0], c['y'][1], *c['z']).cut(
        _cyl(rb, (rw - 0.2, ey, ez), (1, 0, 0), c['x'][1] - rw + 0.4))
    x1, y0 = c['x'][1], c['y'][0]
    adds.append(col)
    adds.append(_prism([(rw - 0.05, y0 - (x1 - rw)), (x1, y0 + 0.01), (rw - 0.05, y0 + 0.01)], 'xy', *c['z']))  # 45 deg chin
    # OLED cell: front ledge plate (with the window), top/bottom walls and web all grown from the right wall
    P = E['oled_cell']['pocket']
    wl = dc.MIN_WALL_LOADED
    xp0 = sp_end + 0.1                                            # 0.1 off the spigot end
    z0, z1 = P['z'][0] - wl, P['z'][1] + wl
    yb = L.Y_RW_IN - 0.05
    adds.append(_bx(L, xp0, P['x'][0], yb, P['y'][1], z0, z1))                       # ledge plate (display datum)
    adds.append(_bx(L, rw - 0.05, xp0 + 0.05, yb, c['y'][0], z0, z1))               # web to the rear wall
    for za, zb in ((z0, P['z'][0]), (P['z'][1], z1)):
        adds.append(_bx(L, xp0, P['x'][1], yb, P['y'][1], za, zb))                   # cell bottom / top walls
    adds.append(_bx(L, xp0, P['x'][1], P['y'][0] - wl, P['y'][0], z0, z1))          # cell -Y wall (bridge)
    wy, wz = E['oled_cell']['window']
    cuts.append(_bx(L, xp0 - 0.1, P['x'][0] + 0.1, ey - wy / 2, ey + wy / 2, ez - wz / 2, ez + wz / 2))
    # EVF board slot: 2 rails from the right wall; PCB edges in 2.1 grooves; bottom rail gapped for the HDMI plug
    bs = E['board_slot']
    px0, px1 = E['board_pcb_x']
    xc, g = (px0 + px1) / 2, bs['groove_w'] / 2
    wm = dc.MIN_WALL + 0.1                                        # 1.3: walls clear of the 1.2 screen
    rx0, rx1 = xc - g - wm, xc + g + wm
    yend = E['board']['y'][1] + 0.5
    zf, zcl = bs['bottom_z'] - dc.SLIDE, bs['top_z'] + dc.SLIDE
    dep, body = bs['groove_depth'], 2.25
    adds.append(_bx(L, rx0, rx1, yb, yend, zf - body, zf + dep))
    adds.append(_bx(L, rx0, rx1, yb, yend, zcl - dep, zcl + 1.25))   # top 94.0: 0.3 under the hood's right-edge lip
    cuts.append(_bx(L, xc - g, xc + g, bs['stop_y'], yend + 0.1, zf, zf + dep + 0.1))
    cuts.append(_bx(L, xc - g, xc + g, bs['stop_y'], yend + 0.1, zcl - dep - 0.1, zcl))
    for g0, g1 in bs['bottom_rail_gaps']:                         # -X part out of the plug's way; +X spine stays
        # FIXER r2 (verifier M-V-MPS-3): the gap and the -X groove wall end stand 1.0 clear of the receptacle and plug
        # (was 0.0 / 0.3, the same as the PCB's own -Y stop gap): the PCB edge at the groove end is the only -Y stop
        g0, g1 = g0 - bs.get('gap_clear', 0.0), g1 + bs.get('gap_clear', 0.0)
        cuts.append(_bx(L, rx0 - 0.1, px1, g0, g1, zf - body - 0.1, zf + dep + 0.1))
        # the board's own HDMI receptacle (lower edge, -X face) sweeps y +45 -> g0..g1 as the board slides in:
        # no -X groove wall beyond g0 (the PCB edge rests on the groove floor; the +X wall and top groove locate it)
        cuts.append(_bx(L, rx0 - 0.1, xc - g + 0.01, g0, yend + 0.1, zf, zf + dep + 0.1))
        cuts.append(_prism([(px1, g1), (rx0 - 0.1, g1 + (px1 - rx0 + 0.1)), (rx0 - 0.1, g1 - 0.1), (px1, g1 - 0.1)],
                           'xy', zf - body - 0.1, zf + dep + 0.1))
        pc = bs.get('plug_x_clear', 0.0)              # FIXER r2: +X spine 0.6 off the plug envelope below the groove
        if pc > 0:
            cuts.append(_bx(L, px1 - 0.01, px1 + pc, g0, g1, zf - body - 0.1, zf + 0.1))
            adds.append(_bx(L, rx1 - 0.01, rx1 + pc + 0.05, g0, g1, zf - body, zf + dep))
    zr = bs.get('zif_relief', 0.0)                    # FIXER r2: top rail -X wall underside relieved over the ZIF
    if zr > 0:
        by0 = E['board']['y'][0]
        cuts.append(_bx(L, rx0 - 0.1, xc - g + 0.01, by0 + 5.0, by0 + 20.0, zcl - dep - 0.1, zcl - dep + zr))
    sw = L.COTS['switch_1824']['box']                             # +X wall stops short of the 18/24 switch box
    cuts.append(_bx(L, xc + g - 0.01, rx1 + 0.1, sw['y'][0] - dc.SEAM, yend + 0.1, zf - body - 0.1, zf + dep + 0.1))
    ko = L.KEEPOUTS['ko_5v_end']                                  # the 5 V lead end passes the rail's +X wall
    cuts.append(_bx(L, ko['x'][0] - dc.SEAM, rx1 + 0.1, yb - 0.1, ko['y'][1] + dc.SEAM, zf, zf + dep + 0.1))
    # stick: rear scoop (10 deep, 45 deg corners) + sleeve channel + stick channel + floor rail with a 45 deg lip
    S, G = L.SCOOP, L.STICK_GUIDE
    sy, sz = L.STICK['axis']
    (hy1, hz1), (hy2, hz2) = G['sleeve_section'], G['stick_section']
    xs = G['sleeve_until_x']
    x5v = L.KEEPOUTS['ko_5v_up']['x'][0] - 0.5                    # channel ends before the 5 V riser
    adds.append(_bx(L, rw - 0.05, xs, yb, S['y'][1] + wl, S['z'][0] - wl, S['z'][1] + wl))
    a0, a1 = S['y']
    b0, b1 = S['z']
    k = 4.0
    cuts.append(_prism([(a0 + k, b0), (a1 - k, b0), (a1, b0 + k), (a1, b1 - k), (a1 - k, b1), (a0 + k, b1),
                        (a0, b1 - k), (a0, b0 + k)], 'yz', L.X_REAR - 0.1, S['x'][1]))
    cuts.append(_bx(L, S['x'][1] - 0.1, xs + 0.05, sy - hy1, sy + hy1, sz - hz1, sz + hz1))
    cuts.append(_bx(L, rw + 1.5, xs + 0.1, L.Y_RW_IN + 1.5, S['y'][0] - wl, S['z'][0], S['z'][1]))   # lightening
    adds.append(_bx(L, xs - 0.05, x5v, yb, sy + hy2 + wm, sz - hz2 - wm, sz + hz2 + wm))
    cuts.append(_bx(L, xs - 0.1, x5v + 0.1, sy - hy2, sy + hy2, sz - hz2, sz + hz2))
    cuts.append(_bx(L, xs - 0.1, x5v + 0.1, L.Y_RW_IN + 1.5, sy - hy2 - wm, sz - hz2, sz + hz2))
    zr = sz - hz2
    yl = sy + hy2 + 2.05
    adds.append(_bx(L, x5v - 0.05, G['x'][1], yb, yl, zr - wm, zr))
    adds.append(_prism([(sy + hy2, zr - 0.05), (yl, zr - 0.05), (yl, zr + 2.05)], 'yz', x5v - 0.05, G['x'][1]))
    return adds, cuts


# ----------------------------------------------------------------------------------------------- right wall (s4, J14)
def _right(L):
    adds, cuts = [], []
    for p in L.RIGHT_WALL_PADS.values():
        adds.append(_cyl(p['d'] / 2, (p['c'][0], p['y'][0] - 0.05, p['c'][1]), (0, 1, 0), p['y'][1] - p['y'][0] + 0.05))
    pad_top = max(p['y'][1] for p in L.RIGHT_WALL_PADS.values())
    for s in L.SCREWS:
        if tuple(s['axis']) == (0, 1, 0):
            hp = s['head_point']
            cb = s['cbore']
            cuts.append(dc.counterbore(hp, s['axis'], d_cb=cb['d'], depth=hp[1] - cb['y'][0], d_clear=L.PT['clear_d'],
                                       through=pad_top - hp[1] + 0.2))
    for k in ('out_wall', 'x1203'):
        v = L.VENTS[k]
        cuts.extend(dc.vent_slots(v['box'], v['slot_w'], v['pitch'], v['slot_along'], v['face']))
    return adds, cuts


# ----------------------------------------------------------------------------------------------- assembly of the part
def build_part(layout, part_id='tub'):
    L = layout
    assert part_id == 'tub', part_id
    body = _shell(L)
    adds, cuts, late = [], [], []
    for fn in (_floor, _front, _rear, _right):
        r = fn(L)
        adds += r[0]
        cuts += r[1]
        if len(r) > 2:
            late += r[2]
    adds += [_ledge(L, hk) for hk in L.HOOD_HOOKS]
    R = L.HOOD_RELEASE                                       # FIXER r2: release holes (hold-open pins) for hk1/hk2
    for hk in L.HOOD_HOOKS:
        if hk.get('release_hole') and hk['wall'] == 'right':
            cuts.append(_cyl(R["hole_d"] / 2, (hk["x"], L.YR - 0.1, R["z"]), (0, 1, 0), L.Y_RW_IN - L.YR + 0.3))  # vertical in print
    body = body.fuse(*adds).clean()
    body = body.cut(*cuts)                     # no clean() here: it breaks the teardrop/collar faces (OCC)
    if late:                                   # (r1: the Pi hooks went in here; R1 r2 deleted them)
        body = body.fuse(*late)
    cl = body.clean()
    if cl.isValid():
        body = cl
    wp = cq.Workplane('XY').newObject([dc.one_solid(body)])
    try:                                       # 45 deg bed chamfer on the straight bed-face edges (along X)
        out = wp.faces('<Y').edges('|X').chamfer(dc.FDM['BED_CHAMFER'])
        if out.val().isValid():
            wp = out
        else:
            dc.NOTES.append('tub bed chamfer invalid; skipped')
    except Exception as e:  # noqa: BLE001 - kernel failures are data
        dc.NOTES.append('tub bed chamfer failed: %s' % e)
    return wp


def build(layout):
    return {'tub': build_part(layout, 'tub')}
