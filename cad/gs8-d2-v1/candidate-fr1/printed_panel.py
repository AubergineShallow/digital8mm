# SPDX-License-Identifier: MIT
"""GS8 D2 release layer: the satin-silver ASA dial panel (owner hood_panel).

One print, face (+Y) on the bed: the left wall with its R5 end corners (45 deg facet at the bed), the J2 top tongue
(5 teeth between the hood rail piers), 2 posts to the right wall (PT pilots for s_r1/s_r2, root gussets), 2 bosses for
the base screws s_b1/s_b2 (their tabs fill the tub lip notches), the encoder snap cradle (3 hooks) and bushing hole,
the 18/24 switch hole with its anti-rotation slot, the J3 locating ribs, the camera keeper finger, the EVF cap (spigot
clamp + OLED finger) and the engraved dial graphics and badge (0.4 deep in the bed face, paint-filled).
r2 R2: each end now meets the inner face with a 1.2 land square to it (END_LAND; the old R5 arc left a 64 deg feather
sampled 0.67), then the 45 deg facet; the EVF board +Y stop (layout.EVF_STOP) is a rib on the inner face (finding 6).
With the skirts gone (finding 3) the boss tabs are the visible, flush notch fillers.
Every number comes from layout.py unless a local constant below says otherwise (listed in NOTES.md).

MODULE CONTRACT (layout.py s10): build(layout) -> {'panel': Workplane}; PRINT; build_part(layout, 'panel').
"""
import math

import cadquery as cq

import d2_common as dc

V = cq.Vector
_PL = dc.L.PARTS['panel']
PRINT = {
    'panel': dict(
        face_down=_PL['face_down'],
        supports='none: every feature grows from the inner face (posts, bosses, tongue teeth, hooks, ribs, keeper, '
                 'EVF cap); the R5 end corners have a 45 deg facet at the bed; holes are vertical in print.',
        notes='ASA satin silver, 0.4 nozzle / 0.2 layer, 4 walls, 25 % gyroid. Smooth PEI or textured sheet for the '
              'face; engraving 0.4 deep is the first 2 layers. Paint-fill the engraving (step 2). Footprint '
              '150.3 x 94.4, height 65.4 (the posts). 5 mm brim on the face (ASA); the bed chamfer keeps the brim off '
              'the visible edge. Enclosure closed.'),
}
NOTES = []

# ------------------------------------------------------------------ local constants (see NOTES.md, hood_panel owner)
EPS = 0.5                     # features grow 0.5 into the wall for a clean fusion
POST_GUSSET = 4.0             # 45 deg root gussets on the x sides of each post
REAR_GUSSET = 3.5             # post_r's rear gusset stops 0.5 off the rear-wall inner face
KEEPER_GUSSET = (8.0, 12.0)   # x, y legs of the keeper root gusset (behind the finger, -X side)
LOCATE_FRONT_Z0 = 41.3        # front J3 rib starts 0.3 over the tub rib_l top (z 41): layout box z0 40 collided
RAIL_PIER_W, RAIL_SPANS = 3.0, 5   # same as printed_hood (the groove piers the teeth straddle)
TOOTH_CHAMFER = 0.4           # lead-in on the tongue-tooth tips
CRADLE = dict(t=1.6, tooth=0.65, land=0.4, lead=45.0, play=0.1, w_top=8.0, w_side=5.0, side_z=47.5)   # FIXER P2: reach 0.40
HOLE_CSK = 0.4                # 45 deg countersink of the bushing holes on the face (bed side)
CAP_U_X1 = -148.2             # EVF cap: U clamp from the cap rear to here; solid OLED finger from here to the front
END_LAND = 1.2                # r2 R2: land square to the inner face at each R5 end (MIN_WALL)


def rail_piers(L):
    """Pier x ranges in the J2 groove (identical to printed_hood.rail_piers)."""
    x0, x1 = L.HOOD_RAIL['box']['x']
    w, n = RAIL_PIER_W, RAIL_SPANS
    span = (x1 - x0 - (n + 1) * w) / n
    return [(round(x0 + k * (w + span), 4), round(x0 + k * (w + span) + w, 4)) for k in range(n + 1)]


def _pl_xy(z0):
    return cq.Plane(origin=V(0, 0, z0), xDir=V(1, 0, 0), normal=V(0, 0, 1))      # u = x, v = y, extrude +z


def _poly_xy(pts, z0, z1):
    return cq.Workplane(_pl_xy(z0)).polyline(pts).close().extrude(z1 - z0).val()


def _box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def _is_line(e, axis):
    if e.geomType() != 'LINE':
        return False
    d = e.endPoint() - e.startPoint()
    return abs({'x': d.x, 'y': d.y, 'z': d.z}[axis]) / max(d.Length, 1e-9) > 0.999


def _edge_op(shape, kind, size, edges, label):
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


def _hole(xc, zc, r, y0, y1, csk):
    """Through hole along Y plus a 45 deg countersink at y1 (the face)."""
    h = cq.Solid.makeCylinder(r, y1 - y0 + 0.2, V(xc, y0 - 0.1, zc), V(0, 1, 0))
    c = cq.Solid.makeCone(r, r + csk + 0.2, csk + 0.2, V(xc, y1 - csk, zc), V(0, 1, 0))
    return h.fuse(c)


# ------------------------------------------------------------------ wall
def _wall(L):
    """Panel wall y SPLIT..YL, z z_low..top, ends = the body R5 corners with a 45 deg facet at the bed face, plus
    the 2 boss blocks (their lower tabs fill the lip notches); 0.6 x 45 deg bed chamfer on the face outline."""
    P = L.PANEL
    z0, z1 = P['box']['z']
    rv, sp, yl = L.RV, L.SPLIT, L.YL
    cy = yl - rv
    s45 = math.sqrt(0.5)
    pts = []
    yland = sp + END_LAND                                  # r2 R2: 1.2 land square to the inner face
    dxl = math.sqrt(rv ** 2 - (yland - cy) ** 2)
    for cxc, sg in ((L.XT1 - rv, 1.0), (L.X_REAR + rv, -1.0)):
        q0 = (cxc + sg * dxl, sp)
        q1 = (cxc + sg * dxl, yland)
        p1 = (cxc + sg * rv * s45, cy + rv * s45)
        p2 = (p1[0] - sg * (yl - p1[1]), yl)
        pts.append((q0, q1, p1, p2))
    (f0, fq, f1, f2), (r0, rq, r1, r2) = pts
    wp = (cq.Workplane(_pl_xy(z0)).moveTo(*f0).lineTo(*fq).lineTo(*f1).lineTo(*f2).lineTo(*r2).lineTo(*r1)
          .lineTo(*rq).lineTo(*r0).close())
    s = wp.extrude(z1 - z0).val()
    bosses = [_box(b['x'][0], b['x'][1], b['y'][0], yl, b['z'][0], b['z'][1]) for b in L.PANEL_BOSSES.values()]
    s = s.fuse(*bosses).clean()
    bed = [e for e in s.Edges() if abs(e.Center().y - yl) < 0.02 and (
        _is_line(e, 'x') or (_is_line(e, 'z') and e.Center().z < z0 + 0.1))]
    return _edge_op(s, 'chamfer', dc.FDM['BED_CHAMFER'], bed, 'face bed edges')


def _posts(L):
    out = []
    sp = L.SPLIT
    for pid, b in L.PANEL_POSTS.items():
        (x0, x1), (y0, _), (z0, z1) = b['x'], b['y'], b['z']
        out.append(_box(x0, x1, y0, sp + EPS, z0, z1))
        g_rear = REAR_GUSSET if x0 - POST_GUSSET < L.X_RW_IN + 0.5 else POST_GUSSET
        out.append(_poly_xy([(x0, sp + EPS), (x0 - g_rear, sp + EPS), (x0 - g_rear, sp), (x0, sp - g_rear)], z0, z1))
        g = POST_GUSSET
        out.append(_poly_xy([(x1, sp + EPS), (x1, sp - g), (x1 + g, sp), (x1 + g, sp + EPS)], z0, z1))
    return out


def _keeper(L):
    k = L.CAM['keeper']
    sp = L.SPLIT
    gx, gy = KEEPER_GUSSET
    x0 = k['x'][0]
    fin = _box(x0, k['x'][1], k['y'][0], sp + EPS, k['z'][0], k['z'][1])
    gus = _poly_xy([(x0, sp + EPS), (x0 - gx, sp + EPS), (x0 - gx, sp), (x0, sp - gy)], k['z'][0], k['z'][1])
    return [fin, gus]


def _evf_cap(L):
    c = L.EVF['cap']
    yc, zc = L.EVF['axis']
    blk = _box(c['x'][0], c['x'][1], c['y'][0], L.SPLIT + EPS, c['z'][0], c['z'][1])
    u = cq.Solid.makeCylinder(L.EVF['cap_clamp_r'], CAP_U_X1 - c['x'][0] + 0.3, V(c['x'][0] - 0.3, yc, zc), V(1, 0, 0))
    return [blk.cut(u)]


def _evf_stop(L):
    """r2 R2 (finding 6): EVF board +Y stop, a rib from the inner face down to EVF_STOP['box'] y0 (gap 0.3 to the PCB
    +Y edge). It bears on the bare laminate edge only (no components, ZIF, HDMI or OLED flex in that box)."""
    b = L.EVF_STOP['box']
    return [_box(b['x'][0], b['x'][1], b['y'][0], L.SPLIT + EPS, b['z'][0], b['z'][1])]


def _ribs(L):
    out = []
    for i, b in enumerate(L.PANEL_LOCATE_RIBS):
        z0 = max(b['z'][0], LOCATE_FRONT_Z0) if i == 0 else b['z'][0]
        out.append(_box(b['x'][0], b['x'][1], b['y'][0], L.SPLIT + EPS, z0, b['z'][1]))
    return out


def _teeth(L):
    t = L.PANEL_TONGUE
    sl = dc.SLIDE
    piers = rail_piers(L)
    out = []
    for (_, a), (b, _) in zip(piers[:-1], piers[1:]):
        x0, x1 = max(a + sl, t['x'][0]), min(b - sl, t['x'][1])
        s = _box(x0, x1, t['y'][0], L.SPLIT + EPS, t['z'][0], t['z'][1])
        tip = [e for e in s.Edges() if abs(e.Center().y - t['y'][0]) < 0.02]
        out.append(_edge_op(s, 'chamfer', TOOTH_CHAMFER, tip, 'tooth tip'))
    return out


def _cradle(L):
    """Encoder snap cradle: one hook over the PCB top edge, two on its x edges low down (the bottom edge sits on
    ko_hdmi_run). Teeth catch the PCB back face (y0) with `play`; the bushing in its 7.5 hole locates the board."""
    E, C, sl = L.ENCODER, CRADLE, dc.SLIDE
    pcb = E['pcb']
    root_y = L.SPLIT + EPS
    a_c = root_y - (pcb['y'][0] - C['play'])
    length = a_c + C['land'] + C['tooth'] / math.tan(math.radians(C['lead']))
    hang = (0, -1, 0)
    xc = E['c'][0]
    spec = [((xc, root_y, pcb['z'][1] + sl), (0, 0, -1), C['w_top']),
            ((pcb['x'][0] - sl, root_y, C['side_z']), (1, 0, 0), C['w_side']),
            ((pcb['x'][1] + sl, root_y, C['side_z']), (-1, 0, 0), C['w_side'])]
    return [dc.snap_hook(r, hang, d, length, C['t'], w, C['tooth'], C['land'], C['lead'], gusset=dc.SNAP_GUSSET)
            for r, d, w in spec]


def _key_leads(L):
    """FR panel (owner fr-panel): 45 deg lead chamfers (layout PANEL_KEY['lead']) on the -Y end of each key block
    (both x edges and the bottom edge), so the keys find the lip notches and ride onto the floor on the -Y push."""
    c, e, out = L.PANEL_KEY['lead'], 0.1, []
    tri = [(-e, -e), (c + e, -e), (-e, c + e)]
    for b in L.PANEL_BOSSES.values():
        (x0, x1), y0, (z0, z1) = b['x'], b['y'][0], b['z']
        out.append(_poly_xy([(x0 + u, y0 + v) for u, v in tri], z0 - e, z1 + e))
        out.append(_poly_xy([(x1 - u, y0 + v) for u, v in tri], z0 - e, z1 + e))
        pl = cq.Plane(origin=V(x0 - e, 0, 0), xDir=V(0, 1, 0), normal=V(1, 0, 0))     # u = y, v = z, extrude +x
        out.append(cq.Workplane(pl).polyline([(y0 + u, z0 + v) for u, v in tri]).close().extrude(x1 - x0 + 2 * e).val())
    return out


def _frame(L):
    """FR panel-2 (owner fr-panel-2): bottom-edge stiffening frame on the inner face (layout PANEL_FRAME): bottom chord
    through both keys, diagonal tie key_b2 -> post_r, rear upright, front upright + link to post_f. All members grow
    from the inner face (-Y in assembly = up in the face-down print): no overhang, no support."""
    F, top, out = L.PANEL_FRAME, L.SPLIT + EPS, []
    for k in ('chord', 'rear', 'front', 'link'):
        b = F[k]
        out.append(_box(b['x'][0], b['x'][1], b['y'][0], top, b['z'][0], b['z'][1]))
    d = F['diag']
    (x0, z0), (x1, z1), h = d['p0'], d['p1'], d['w'] / 2.0
    ln = math.hypot(x1 - x0, z1 - z0)
    nx, nz = (z1 - z0) / ln * h, -(x1 - x0) / ln * h
    pts = [(x0 + nx, z0 + nz), (x1 + nx, z1 + nz), (x1 - nx, z1 - nz), (x0 - nx, z0 - nz)]
    pl = cq.Plane(origin=V(0, top, 0), xDir=V(1, 0, 0), normal=V(0, -1, 0))   # local (u, v) = (x, z), extrude -Y
    out.append(cq.Workplane(pl).polyline(pts).close().extrude(top - d['y0']).val())
    return out


def _cuts(L):
    sp, yl = L.SPLIT, L.YL
    E, S = L.ENCODER, L.SWITCH_1824
    cuts = [_hole(E['c'][0], E['c'][1], E['panel_hole_d'] / 2, sp - EPS, yl, HOLE_CSK),
            _hole(S['c'][0], S['c'][1], S['panel_hole_d'] / 2, sp - EPS, yl, HOLE_CSK)]
    ar = S['anti_rot']
    sw, sh, sd = ar['slot']
    if abs(ar['angle_deg']) > 1e-9:
        NOTES.append('anti-rotation slot angle %.1f not 0: slot drawn at 0 (12 o\'clock)' % ar['angle_deg'])
    xs, zs = L.pol(S['c'], ar['r'], 0.0)
    cuts.append(_box(xs - sw / 2, xs + sw / 2, sp - EPS - 0.1, sp + sd, zs - sh / 2, zs + sh / 2))
    for s in L.SCREWS:
        words = s['into'].split()                    # r2: 'tub keeper boss s_k1' (R1) has more than 2 words
        if words[0] != 'panel':
            continue
        key = words[-1]
        ax = s['axis']
        if key in L.PANEL_BOSSES:                    # screw up (+Z) into a boss from its bottom face
            b = L.PANEL_BOSSES[key]
            top = (s['tip'][0], s['tip'][1], b['z'][0])
            depth = s['tip'][2] - b['z'][0] + L.PT['tip_reserve']
        else:                                        # screw along +Y into a post from its right-wall end
            b = L.PANEL_POSTS[key]
            top = (s['tip'][0], b['y'][0], s['tip'][2])
            depth = s['tip'][1] - b['y'][0] + L.PT['tip_reserve']
        cuts.append(dc.pt_boss(top, ax, pilot_depth=depth)[1])
    cuts += dc.engrave(L.ENGRAVE['items'], face_y=yl)
    return cuts


def build_part(layout, part_id='panel'):
    if part_id != 'panel':
        raise KeyError(part_id)
    L = layout
    del NOTES[:]
    s = _wall(L)
    adds = _posts(L) + _keeper(L) + _evf_cap(L) + _evf_stop(L) + _ribs(L) + _teeth(L) + _cradle(L)
    s = s.fuse(*adds).clean()
    s = s.cut(*_cuts(L)).clean()
    if getattr(L, 'FR', {}).get('panel'):              # FR panel: keys key_b1/key_b2 get their lead chamfers
        s = s.cut(*_key_leads(L)).clean()
        s = s.fuse(*_frame(L)).clean()                 # FR panel-2: bottom-edge stiffening frame (after the leads)
    sol = dc.one_solid(s)
    if len(s.Solids()) != 1:
        NOTES.append('panel boolean left %d solids; kept the largest' % len(s.Solids()))
    if not sol.isValid():
        NOTES.append('panel solid reports invalid')
    return dc.wp_of(sol)


def build(layout):
    return {'panel': build_part(layout, 'panel')}
