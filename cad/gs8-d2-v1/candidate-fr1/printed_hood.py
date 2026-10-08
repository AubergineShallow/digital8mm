# SPDX-License-Identifier: MIT
"""GS8 D2 release layer: the black ASA hood (owner hood_panel).

One print: the roof band, the front plate with the 60 mm lens turret, the eyepiece housing behind the rear face,
the plunger well (flange channel + pocket + opening + raised guard rim), the microSD slot, the front exhaust slots,
the roof inlet slots over the blower, 4 snap hooks (J1), the J2 rail block (groove for the panel tongue) and a roof
stiffening rib. Every number comes from layout.py (passed in as `layout`) unless a local constant below says
otherwise; each local constant is explained and listed in NOTES.md (hood_panel owner).

MODULE CONTRACT (layout.py s10): build(layout) -> {'hood': Workplane}; PRINT; build_part(layout, 'hood').
Print: roof (+Z) on the bed. Supports: the turret's upper half and the eyepiece-housing window sill only.
"""
import math

import cadquery as cq

import d2_common as dc

V = cq.Vector
_PL = dc.L.PARTS['hood']
PRINT = {
    'hood': dict(
        face_down=_PL['face_down'],
        supports='tree supports from the bed at 2 places only: (1) the upper half of the lens turret (8.5 mm '
                 'overhang off the front plate); (2) the +Y lower strip of the eyepiece housing under its window '
                 '(the window runs the full housing length, so the strip starts mid-air; support from outside, '
                 'y > 35). Everything else is self-supporting: housing interior = 45 deg flanks + 15.2 mm bridge; '
                 'J2 groove lip = 21 mm bridges between 6 piers; all holes in the plate are bridged <= 14.2 mm; '
                 'the lens bore is a truncated teardrop (13.1 mm flat).',
        notes='ASA black, 0.4 nozzle / 0.2 layer, 4 walls, 25 % gyroid. Roof on the bed (0.6 x 45 deg bed chamfer, '
              '3.0 x 45 deg front-top chamfer). Hooks, rail block and rib grow upward. Remove the 2 tree supports; '
              'deburr the hook teeth and the groove mouth. Footprint 178.7 x 67.3, height 99.7. 5 mm brim on the roof '
              '(ASA, long flat first layer); enclosure closed, no part-cooling fan above 20 %.'),
}
NOTES = []

# ------------------------------------------------------------------ local constants (not interfaces; see NOTES.md)
FRONT_TOP_CHAMFER = 3.0       # 45 deg, front-top edge (concept fillet 5.0; no fillet on the bed face)
HOUSING_TOP_CHAMFER = 3.0     # 45 deg housing top corners (R6 bottom corners as the concept; top = bed face)
HOUSING_RIM_CHAMFER = 0.8     # open (eye) end outer rim
PLATE_EDGE_R = 1.4            # plate front vertical edges (concept er 1.4)
PLATE_FOOT_R = 1.5            # plate front-bottom edge (concept 1.8, plate is 2.5 thick)
RAIL_BACK_Y = 23.9            # rail block back face (layout box 25.5 left a 0.25 web behind the groove)
RAIL_PIER_W, RAIL_SPANS = 3.0, 5   # piers turn the groove lip into 21 mm bridges (panel tongue = 5 teeth)
RIB = (-132.0, -10.0, 8.4, 10.0, 94.3)   # roof rib x0, x1, y0, y1, z0 (to the band)
EDGE_FLANGE = dict(t=1.6, z0=94.3, end_gap=0.5, hook_gap=6.0)   # down-turned right-edge flange (roof stiffness,
#                                  warp control); stops 0.5 off the front/rear wall inner faces and 6 off each hook axis
GUARD = dict(w=1.2, h=1.0, chamfer=0.8)  # raised guard rim round the plunger opening
BORE_FLAT = 1.0               # truncated-teardrop flat below the lens bore (print roof toward -Z)
BORE_CHAMFER = 0.5            # turret front bore edge
TURRET_R_FILLET = (0.8, 0.6)  # step edge (r 30 at x 6), front edge (r 28.5 at x 8.5): concept er 0.8 / 0.6
EPS = 0.5                     # fusion overlap into the band / plate


def rail_piers(L):
    """Pier x ranges in the J2 groove (keep in step with printed_panel.rail_piers)."""
    x0, x1 = L.HOOD_RAIL['box']['x']
    w, n = RAIL_PIER_W, RAIL_SPANS
    span = (x1 - x0 - (n + 1) * w) / n
    return [(round(x0 + k * (w + span), 4), round(x0 + k * (w + span) + w, 4)) for k in range(n + 1)]


# ------------------------------------------------------------------ small geometry helpers
def _pl_xz(y1):
    return cq.Plane(origin=V(0, y1, 0), xDir=V(1, 0, 0), normal=V(0, -1, 0))     # u = x, v = z, extrude -y


def _pl_yz(x0):
    return cq.Plane(origin=V(x0, 0, 0), xDir=V(0, 1, 0), normal=V(1, 0, 0))      # u = y, v = z, extrude +x


def _poly(plane, pts, depth):
    return cq.Workplane(plane).polyline(pts).close().extrude(depth).val()


def _path(plane, segs, depth):
    wp = cq.Workplane(plane)
    for s in segs:
        if s[0] == 'm':
            wp = wp.moveTo(*s[1])
        elif s[0] == 'l':
            wp = wp.lineTo(*s[1])
        else:
            wp = wp.threePointArc(s[1], s[2])
    return wp.close().extrude(depth).val()


def _box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def _is_line(e, axis):
    if e.geomType() != 'LINE':
        return False
    d = e.endPoint() - e.startPoint()
    return abs({'x': d.x, 'y': d.y, 'z': d.z}[axis]) / max(d.Length, 1e-9) > 0.999


def _pick(shape, axis=None, tol=0.02, **at):
    out = []
    for e in shape.Edges():
        if axis and not _is_line(e, axis):
            continue
        c = e.Center()
        if all(abs(getattr(c, k) - v) < tol for k, v in at.items()):
            out.append(e)
    return out


def _edge_op(shape, kind, size, edges, label):
    """Fillet or chamfer `edges`; keep the input (and note it) if the kernel fails or the result is invalid."""
    if not edges:
        NOTES.append('%s %s: no edges selected; skipped' % (kind, label))
        return shape
    try:
        out = shape.fillet(size, edges) if kind == 'fillet' else shape.chamfer(size, None, edges)
        if out.isValid():
            return out
        NOTES.append('%s %s %.2f: invalid result; skipped' % (kind, label, size))
    except Exception as e:  # noqa: BLE001 - kernel failures are data here
        NOTES.append('%s %s %.2f failed: %s' % (kind, label, size, str(e)[:80]))
    return shape


# ------------------------------------------------------------------ features
def _shell(L):
    """Band + front plate (one L profile, extruded over the hood width) + the eyepiece-housing outer prism,
    with the plate edge rounds, the housing rim chamfer and the 0.6 bed chamfers on the roof face."""
    H = L.HOOD
    y0, y1 = H['y']
    bx0 = H['band_x'][0]
    zb0, zb1 = H['band_z']
    px0, px1 = H['plate_x']
    pz0 = H['plate_z'][0]
    fc = FRONT_TOP_CHAMFER
    prof = [(bx0, zb0), (px0, zb0), (px0, pz0), (px1, pz0), (px1, zb1 - fc), (px1 - fc, zb1), (bx0, zb1)]
    body = _poly(_pl_xz(y1), prof, y1 - y0)
    body = _edge_op(body, 'fillet', PLATE_FOOT_R, _pick(body, 'y', x=px1, z=pz0), 'plate foot')
    edges = [e for e in body.Edges() if _is_line(e, 'z') and abs(e.Center().x - px1) < 0.05]
    body = _edge_op(body, 'fillet', PLATE_EDGE_R, edges, 'plate vertical edges')

    hb = H['housing']
    (hx0, hx1), (hy0, hy1), (hz0, hz1) = hb['x'], hb['y'], hb['z']
    r, c = H['housing_r'], HOUSING_TOP_CHAMFER
    s45 = math.sqrt(0.5)
    segs = [('m', (hy0 + r, hz0)), ('l', (hy1 - r, hz0)),
            ('a', (hy1 - r + r * s45, hz0 + r - r * s45), (hy1, hz0 + r)),
            ('l', (hy1, hz1 - c)), ('l', (hy1 - c, hz1)), ('l', (hy0 + c, hz1)), ('l', (hy0, hz1 - c)),
            ('l', (hy0, hz0 + r)), ('a', (hy0 + r - r * s45, hz0 + r - r * s45), (hy0 + r, hz0))]
    hous = _path(_pl_yz(hx0), segs, hx1 - hx0)
    hous = _edge_op(hous, 'chamfer', HOUSING_RIM_CHAMFER, [e for e in hous.Edges() if abs(e.Center().x - hx0) < 0.02],
                    'housing rim')
    s = body.fuse(hous).clean()
    bed = (_pick(s, 'x', y=y1, z=zb1) + _pick(s, 'x', y=y0, z=zb1) + _pick(s, 'y', x=bx0, z=zb1))
    return _edge_op(s, 'chamfer', dc.FDM['BED_CHAMFER'], bed, 'roof bed edges')


def _housing_cuts(L):
    """Interior (45 deg flanks tangent to the 1.25 radial clearance circle, 15.2 bridge, top-corner gussets) and the
    +Y window (x full; sill at the flank top so the corner stays 135 deg)."""
    H = L.HOOD
    hb = H['housing']
    (hx0, hx1), (hy0, hy1), (hz0, hz1) = hb['x'], hb['y'], hb['z']
    w, wt = H['housing_wall'], H['housing_top_wall']
    yc, zc = L.EYE_AXIS
    rc = L.EVF['barrel']['r'] + L.EVF['diopter_clear']           # 20.5 clearance circle
    zf = hz0 + w                                                 # 56.6 inner floor
    k = rc * math.sqrt(2.0)                                      # tangent lines y +- z = const
    yl = (yc + zc - k) - zf                                      # left flank meets the floor (y + z = yc + zc - k)
    yr = zf - (zc - yc - k)                                      # right flank (z - y = zc - yc - k)
    yi0, yi1, zi1 = hy0 + w, hy1 - w, hz1 - wt
    gl, gr = 10.0, 7.0                                           # top-corner gusset legs (>= 1.3 off the circle)
    inner = [(yl, zf), (yr, zf), (yi1, yi1 + (zc - yc - k)), (yi1, zi1 - gr), (yi1 - gr, zi1),
             (yi0 + gl, zi1), (yi0, zi1 - gl), (yi0, (yc + zc - k) - yi0)]
    cav = _poly(_pl_yz(hx0 - 1.0), inner, hx1 - hx0 + 1.0)
    win = H['housing_window']
    ysill = win['z'][0] - (zc - yc - k)                          # flank reaches the sill height here (33.0)
    window = _box(hx0 - 1.0, hx1, ysill, hy1 + 0.5, win['z'][0], win['z'][1])
    return [cav, window]


def _turret(L):
    t, tb = L.HOOD['turret'], L.HOOD['turret_b']
    yc, zc = t['c']
    a = cq.Solid.makeCylinder(t['r'], t['a'][1] - t['a'][0] + EPS, V(t['a'][0] - EPS, yc, zc), V(1, 0, 0))
    b = cq.Solid.makeCylinder(tb['r'], tb['a'][1] - tb['a'][0], V(tb['a'][0], yc, zc), V(1, 0, 0))
    s = a.fuse(b).clean()
    step = [e for e in s.Edges() if e.geomType() == 'CIRCLE' and abs(e.Center().x - t['a'][1]) < 0.02
            and abs(e.radius() - t['r']) < 0.02]
    s = _edge_op(s, 'fillet', TURRET_R_FILLET[0], step, 'turret step')
    front = [e for e in s.Edges() if e.geomType() == 'CIRCLE' and abs(e.Center().x - tb['a'][1]) < 0.02]
    return _edge_op(s, 'fillet', TURRET_R_FILLET[1], front, 'turret front')


def _bore_tool(L):
    """Lens bore through the plate and turret: dia 36.5 + truncated teardrop toward -Z + front chamfer."""
    t = L.HOOD['turret']
    r = t['r_in']
    yc, zc = t['c']
    x0, x1 = L.HOOD['plate_x'][0] - 0.3, L.HOOD['turret_b']['a'][1] + 0.3
    cyl = cq.Solid.makeCylinder(r, x1 - x0, V(x0, yc, zc), V(1, 0, 0))
    s = r * math.sqrt(0.5)
    d = r + BORE_FLAT
    hw = 2 * s - d
    drop = _poly(_pl_yz(x0), [(yc - s, zc - s), (yc + s, zc - s), (yc + hw, zc - d), (yc - hw, zc - d)], x1 - x0)
    xf = L.HOOD['turret_b']['a'][1]
    cone = cq.Solid.makeCone(r, r + BORE_CHAMFER + 0.3, BORE_CHAMFER + 0.3, V(xf - BORE_CHAMFER, yc, zc), V(1, 0, 0))
    return dc.fuse_all([cyl, drop, cone])


def _hooks(L):
    Hk, sl = L.HOOK, dc.SLIDE
    out = []
    for h in L.HOOD_HOOKS:
        n = h['normal']
        if h['wall'] == 'right':
            face = (h['x'], h['y_face'], L.ZT1)
        else:
            face = (h['x_face'], h['y'], L.ZT1)
        off = Hk['ledge'] + sl
        root = (face[0] + n[0] * off, face[1] + n[1] * off, L.ZT1 + EPS)
        out.append(dc.snap_hook(root, (0, 0, -1), tuple(-v for v in n), Hk['length'] + EPS, Hk['t'], Hk['w'],
                                Hk['tooth'], Hk['land'], Hk['lead_deg'], gusset=dc.SNAP_GUSSET,
                                ret_deg=h.get('ret_deg', 0.0)))      # FIXER r2: hk3/hk4 45 deg return
    return out


def _yslide_keys(L):
    """FR hood=yslide (fr-hood): rigid integral keys in place of the 4 snap hooks. Right wall (yk1/yk2): a STAPLE =
    2 legs from the band + a bar bridged between them (print: 6.5 bridge) that closes under the tub tab; the bar top
    is the flat catch face. Front/rear walls (yk3/yk4): a leg + a 45 deg dovetail TOE toward the wall (print: the toe
    top grows out of the leg at 45 deg)."""
    Y = L.HOOD_YSLIDE
    tb, st, to = Y['tab'], Y['staple'], Y['toe']
    out = []
    for h in L.HOOD_HOOKS:
        if h['kind'] == 'staple':
            x, yf = h['x'], h['y_face']
            hi = tb['w'] / 2 + st['side_gap']
            ho = hi + st['leg_t']
            y0, y1 = yf + st['wall_gap'], yf + st['wall_gap'] + st['depth']
            zb1 = tb['z'][0] - st['play']
            zb0 = zb1 - st['bar_t']
            bar = _box(x - ho, x + ho, y0, y1, zb0, zb1)
            legs = [_box(x - ho, x - hi, y0, y1, zb1 - 0.01, L.ZT1 + EPS),
                    _box(x + hi, x + ho, y0, y1, zb1 - 0.01, L.ZT1 + EPS)]
            out.append(bar.fuse(*legs).clean())
        else:
            xf, nx, s = h['x_face'], h['normal'][0], h['y']
            ut, ul = to['tip_gap'], to['tip_gap'] + to['e']
            zb = to['z0'] - to['tip_t']
            uz = [(ut, zb), (ul + to['leg_t'], zb), (ul + to['leg_t'], L.ZT1 + EPS), (ul, L.ZT1 + EPS),
                  (ul, to['z0'] + (ul - ut)), (ut, to['z0'])]
            pts = [(xf + nx * u, z) for u, z in uz]
            if nx < 0:
                pts = pts[::-1]
            ya, yb = s + to['y'][0], s + to['y'][1]
            out.append(_poly(_pl_xz(yb), pts, yb - ya))
    return out


def _screw1_boss(L):
    """FR hood=screw1 (fr-hood): PT boss for s_h1 under the band: a D section (flat-sided web from the band down to the
    axis, round underneath; print: the round half is on top, no overhang) + its blind pilot (returned separately)."""
    s1 = L.HOOD_SCREW1
    x, z, r = s1['x'], s1['z'], s1['boss_od'] / 2
    y0 = s1['boss_y0']
    y1 = y0 + s1['pilot_depth'] + s1['floor']
    web = _box(x - r, x + r, y0, y1, z, L.ZT1 + EPS)
    cyl = cq.Solid.makeCylinder(r, y1 - y0, V(x, y0, z), V(0, 1, 0))
    pilot = cq.Solid.makeCylinder(L.PT['pilot_d'] / 2, s1['pilot_depth'] + 0.3, V(x, y0 - 0.3, z), V(0, 1, 0))
    return web.fuse(cyl).clean(), pilot


def _rail(L):
    R = L.HOOD_RAIL
    (x0, x1), (_, y1), (z0, z1) = R['box']['x'], R['box']['y'], R['box']['z']
    g = R['groove']
    blk = _box(x0, x1, RAIL_BACK_Y, y1, z0, z1 + EPS)
    groove = _box(x0 - 1, x1 + 1, g['y'][0], y1 + 1, g['z'][0], g['z'][1])
    s = blk.cut(groove)
    piers = [_box(a, b, g['y'][0] - 0.2, y1, g['z'][0] - 0.2, g['z'][1] + 0.2) for a, b in rail_piers(L)]
    return s.fuse(*piers).clean()


def _guard(L):
    o = L.PLUNGER['hood_opening']
    gw, gh = GUARD['w'], GUARD['h']
    x0 = L.X_FRONT
    rim = _box(x0 - EPS, x0 + gh, o['y'][0] - gw, o['y'][1] + gw, o['z'][0] - gw, o['z'][1] + gw)
    rim = rim.cut(_box(x0 - 1, x0 + gh + 1, o['y'][0], o['y'][1], o['z'][0], o['z'][1]))
    outer = [e for e in rim.Edges() if abs(e.Center().x - (x0 + gh)) < 0.02 and (
        abs(e.Center().y - (o['y'][0] - gw)) < 0.02 or abs(e.Center().y - (o['y'][1] + gw)) < 0.02 or
        abs(e.Center().z - (o['z'][0] - gw)) < 0.02 or abs(e.Center().z - (o['z'][1] + gw)) < 0.02)]
    return _edge_op(rim, 'chamfer', GUARD['chamfer'], outer, 'guard rim')


def _edge_flange(L):
    """Down-turned flange along the band's right edge (y from the band edge inward), interrupted at hk1/hk2 so
    the hook beams keep their full free length."""
    F = EDGE_FLANGE
    y0 = L.HOOD['y'][0]
    xa, xb = L.X_RW_IN + F['end_gap'], L.X_FW_IN - F['end_gap']
    cuts = sorted((h['x'] - F['hook_gap'], h['x'] + F['hook_gap']) for h in L.HOOD_HOOKS if h['wall'] == 'right')
    if L.FR['hood'] == 'screw1':                   # FR hood screw1: the flange stops either side of pad_h1
        s1 = L.HOOD_SCREW1
        cuts = sorted(cuts + [(s1['x'] - s1['flange_gap'], s1['x'] + s1['flange_gap'])])
    segs, x = [], xa
    for a, b in cuts:
        segs.append((x, a))
        x = b
    segs.append((x, xb))
    return [_box(a, b, y0, y0 + F['t'], F['z0'], L.ZT1 + EPS) for a, b in segs if b - a > 2.0]


def _plate_cuts(L):
    """Plunger flange channel (open at the plate foot: the flange enters as the hood drops) + pocket, the finger
    opening (through the guard rim), the microSD slot, the exhaust slots and the roof inlet slots."""
    P = L.PLUNGER
    pk, op = P['hood_pocket'], P['hood_opening']
    x0, x1 = L.HOOD['plate_x']
    pky0 = pk['y'][0]
    if L.FR['hood'] == 'yslide':                   # FR hood: the flange enters the channel at the +dy drop offset
        pky0 -= L.HOOD_YSLIDE['dy']
    cuts = [_box(pk['x'][0] - 0.3, pk['x'][1], pky0, pk['y'][1], L.HOOD['plate_z'][0] - 0.5, pk['z'][1]),
            _box(op['x'][0] - 0.1, x1 + GUARD['h'] + 0.5, op['y'][0], op['y'][1], op['z'][0], op['z'][1])]
    sd = L.SD_SLOT
    cuts.append(_box(x0 - 0.3, x1 + 0.3, sd['y'][0], sd['y'][1], sd['z'][0], sd['z'][1]))
    for k in ('out_band', 'out_corner', 'inlet_roof'):
        v = L.VENTS[k]
        assert v['part'] == 'hood'
        cuts += dc.vent_slots(v['box'], v['slot_w'], v['pitch'], v['slot_along'], v['face'])
    return cuts


def build_part(layout, part_id='hood'):
    if part_id != 'hood':
        raise KeyError(part_id)
    L = layout
    del NOTES[:]
    s = _shell(L)
    s = s.cut(*_housing_cuts(L))
    adds = [_turret(L), _rail(L), _guard(L), _box(RIB[0], RIB[1], RIB[2], RIB[3], RIB[4], L.ZT1 + EPS)]
    if L.FR['hood'] == 'yslide':                   # FR hood (fr-hood): rigid keys instead of the 4 snap hooks
        adds += _yslide_keys(L) + _edge_flange(L)
    else:
        adds += _hooks(L) + _edge_flange(L)
    st = getattr(L, 'HOOD_STACK_STOP', None)       # FIXER r2 (M-V-MPS-4): far-side stack stop (post + fin from the roof)
    if st is not None:
        for b in (st['post'], st['fin']):
            adds.append(_box(b['x'][0], b['x'][1], b['y'][0], b['y'][1], b['z'][0], b['z'][1]))
    late = []
    if L.FR['hood'] == 'screw1':                   # FR hood screw1: s_h1 boss + blind pilot
        boss, pilot = _screw1_boss(L)
        adds.append(boss)
        late.append(pilot)
    s = s.fuse(*adds).clean()
    s = s.cut(_bore_tool(L), *_plate_cuts(L), *late).clean()
    sol = dc.one_solid(s)
    if len(s.Solids()) != 1:
        NOTES.append('hood boolean left %d solids; kept the largest' % len(s.Solids()))
    if not sol.isValid():
        NOTES.append('hood solid reports invalid')
    return dc.wp_of(sol)


def build(layout):
    return {'hood': build_part(layout, 'hood')}
