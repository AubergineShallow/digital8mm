# SPDX-License-Identifier: MIT
"""GS8 D2 r5: the lens collar (owner: tub; J7-R float, R5-BRIEF choices 3-5, judge 3 s6.3). MODULE CONTRACT in layout.py.

One collar per lens that has a `support` band (layout.LENSES; the build uses layout.LENS, collar_spec(name) gives the
per-lens numbers). It clamps the lens on its FIXED band and sets the lens's axial position on a 45 deg cone seat; the
camera (housing, BFAR, adapter, PCB, cover) hangs on the lens and touches no printed part in service. Features:
  - body: disc r 30 (the old turret's look), x 0.3 (0.3 in front of the hood plate) .. front (Kowa 8.6 = 2.6 behind
    the focus ring; never more than first moving segment - 2.0);
  - rear bore: a >= 1.6 mm axial cylindrical land removes the unused thin cone feather; its 45 deg seat datum is unchanged;
  - bore = band d + 0.3 (diametral) from the cone to the front; 45 deg cone from (cone_x0, cone_r0) to (cone_x1,
    bore_r): the band's chamfered rear edge seats at C_FLANGE_X + x0 (Kowa x 2.8, r 20.7);
  - 3 ear lobes (TL, TR, LL; r 5.0 hulled to the body) with a dia 7.5 counterbore from the front to the washer seat
    x 2.8, M3 clearance 3.4 through the ear and its foot; 4 feet dia 7.6 x -2.7..+0.3 through the hood holes (dia 8.6)
    onto the tub outer face (datum x -2.7); LR is a solid compression foot;
  - slit 2.0 (z 59..61) on the -Y side, bore to the lug tips, full length; external pinch lugs x 1.0..front inside
    |y| <= 35 (upper z 61..66, lower z 50..59): s_c4 (M3 x 16 + washer) straight down through the upper lug into an
    M3 L 5.7 heat-set insert pressed into the lower lug from below; the body above the upper lug is trimmed to
    y >= -27.8 so the dia 6.5 audit bit clears;
  - 0.6 x 45 deg bed chamfer on the outer edges of the front (+X) face (bed face); no fillets there.
Print: front face (+X) on the bed (face_down '+X'); feet, ears and lugs grow -X; the cone prints as a 45 deg inward
step; the washer seats have 0.2 mm PRINT-only membranes across their central holes; clear the three 3.4 holes
before assembly, leaving the seat planes untouched; no supports. ASA (PC if G-W11 finds > 50 C at the camera).
"""
import math

import cadquery as cq

import d2_common as dc

V = cq.Vector
PRINT = {
    'lens_collar': dict(
        face_down='+X',
        supports='none',
        notes='Front face (+X) on the bed; 100 % infill (small part), 4 perimeters minimum. The 45 deg cone seat is '
              'an inward step in print. The STL includes one 0.2 mm sacrificial bridge layer across each anchor hole '
              '(washer plane x 2.8): clear only the three 3.4 mm holes by hand before assembly; keep the washer '
              'seat planes flat. STEP and assembly checks describe the cleared, finished part. The M3 holes '
              'and the dia 4.0 lug insert bore are horizontal holes under 8 mm (round). Heat-set the M3 L 5.7 insert '
              'into the lower lug from below at the bench (flush -0.1). Do not post-process the cone seat or the '
              'foot ends (datums). ASA black; PC if gate G-W11 finds the camera zone above 50 C.'),
}
NOTES = []


def _box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def _cylx(r, x0, x1, y, z):
    return cq.Solid.makeCylinder(r, x1 - x0, V(x0, y, z), V(1, 0, 0))


def _prism_yz(pts, x0, x1):
    """Closed (y, z) polygon extruded along +X from x0 to x1."""
    pl = cq.Plane(origin=V(x0, 0, 0), xDir=V(0, 1, 0), normal=V(1, 0, 0))   # local v = +Z
    return cq.Workplane(pl).polyline(pts).close().extrude(x1 - x0).val()


def _rev_x(pts_xr, ly, lz):
    """Closed (x, r) profile revolved about the lens axis."""
    return cq.Workplane('XY').polyline(pts_xr).close().revolve(360.0, (0, 0, 0), (1, 0, 0)).val().translate(V(0, ly, lz))


def _hull_web(c1, R, c2, r, x0, x1):
    """Quadrilateral between the external tangent points of circle (c1, R) and circle (c2, r) in the yz plane:
    body cylinder + ear cylinder + this web = their exact convex hull."""
    d = math.dist(c1, c2)
    u = ((c2[0] - c1[0]) / d, (c2[1] - c1[1]) / d)
    v = (-u[1], u[0])
    th = math.acos((R - r) / d)
    pts = []
    for sg in (1.0, -1.0):
        n = (u[0] * math.cos(th) + sg * v[0] * math.sin(th), u[1] * math.cos(th) + sg * v[1] * math.sin(th))
        pts.append(((c1[0] + R * n[0], c1[1] + R * n[1]), (c2[0] + r * n[0], c2[1] + r * n[1])))
    (a1, b1), (a2, b2) = pts
    return _prism_yz([a1, b1, b2, a2], x0, x1)


def _outer_bed_chamfer(sol, size, upper_lug_top):
    """0.6 x 45 deg chamfer on the OUTER wire of the bed face (+X); the counterbore circles keep square edges (a
    chamfer on both sides of their 1.25 ear wall would leave a knife edge)."""
    try:
        f = max((f for f in sol.Faces() if f.geomType() == 'PLANE' and f.normalAt().x > 0.999),
                key=lambda f: f.Center().x * 1e3 + f.Area())
        # Keep the complete upper-lug washer bearing plane. Chamfering this edge
        # consumes the washer's support at its forward rim (review A1).
        edges = [e for e in f.outerWire().Edges()
                 if not (abs(e.BoundingBox().zmin - upper_lug_top) < 1e-6
                         and abs(e.BoundingBox().zmax - upper_lug_top) < 1e-6)]
        out = sol.chamfer(size, None, edges)
        if out.isValid():
            return out
        NOTES.append('collar bed chamfer invalid; skipped')
    except Exception as e:  # noqa: BLE001 - kernel failures are data
        NOTES.append('collar bed chamfer failed: %s' % str(e)[:80])
    return sol


def build_part(layout, part_id='lens_collar', lens=None):
    """The collar for `lens` (default layout.LENS), assembly frame, final pose."""
    L = layout
    assert part_id == 'lens_collar', part_id
    del NOTES[:]
    cs = L.collar_spec(lens or L.LENS)
    if cs is None:
        raise ValueError('lens %s has no support band: no collar (R5-BRIEF choice 3)' % (lens or L.LENS))
    if not cs['rear_entry_feasible']:
        raise ValueError('lens %s needs a different rear-entry design before a collar can be built' % (lens or L.LENS))
    C, M = L.COLLAR, L.M3
    ly, lz = L.LENS_AXIS
    x0, xf = cs['rear_x'], cs['front_x']
    R, re = C['body_r'], C['ear_r']
    adds = [_cylx(R, x0, xf, ly, lz)]
    for k in C['bolted']:                                   # ear lobes hulled to the body, full length
        y, z = C['feet'][k]
        adds += [_cylx(re, x0, xf, y, z), _hull_web((ly, lz), R, (y, z), re, x0, xf)]
    fx0, fx1 = C['foot_x']
    for y, z in C['feet'].values():                         # feet through the hood holes onto the tub face
        adds.append(_cylx(C['foot_d'] / 2, fx0, fx1 + 0.05, y, z))
    lg = C['lug']
    lx0 = lg['x'][0]
    for z0, z1 in (lg['upper_z'], lg['lower_z']):           # external pinch lugs (merged into the body)
        rear = lg['upper_x0'] if (z0, z1) == lg['upper_z'] else lx0
        adds.append(_box(rear, xf, lg['y_out'], ly - (R - 6.0), z0, z1))
    body = adds[0].fuse(*adds[1:]).clean()
    cuts = [_rev_x([(x0 - 0.1, 0.0), (x0 - 0.1, cs['cone_r0']), (cs['cone_x0'], cs['cone_r0']),
                    (cs['cone_x1'], cs['bore_r']), (xf + 0.1, cs['bore_r']), (xf + 0.1, 0.0)], ly, lz)]
    sw = C['slit']['w']
    cuts.append(_box(fx0 - 0.1, xf + 0.1, lg['y_out'] - 1.0, ly, lz - sw / 2, lz + sw / 2))     # -Y slit
    seat = C['flange_x'][1]
    for k in C['bolted']:                                   # clearance through foot + flange, counterbore to the seat
        y, z = C['feet'][k]
        cuts.append(_cylx(C['hole_d'] / 2, fx0 - 0.1, seat + 0.05, y, z))
        cuts.append(_cylx(C['cbore_d'] / 2, seat, xf + 0.1, y, z))
    s4 = next(s for s in L.SCREWS if s['id'] == 's_c4')
    hx, hy, hz = s4['head_point']
    ins = s4['insert']
    zi0, zi1 = ins['z'][0] - ins['flush'], ins['z'][1] + 0.2           # insert bore = insert + 0.2 (from the bottom)
    cuts.append(cq.Solid.makeCylinder(M['clear_d'] / 2, lg['upper_z'][1] + 0.1 - zi1 + 0.05, V(hx, hy, zi1 - 0.05),
                                      V(0, 0, 1)))
    cuts.append(cq.Solid.makeCylinder(ins['bore_d'] / 2, zi1 - zi0 + 0.1, V(hx, hy, zi0 - 0.1), V(0, 0, 1)))
    cuts.append(_box(fx0 - 0.1, xf + 0.1, lg['y_out'] - 5.0, lg['bit_relief_y'], lg['upper_z'][1], lz + 20.0))
    sol = body.cut(*cuts)
    cl = sol.clean()
    if cl.isValid():
        sol = cl
    sol = dc.one_solid(sol)
    if len(body.cut(*cuts).Solids()) != 1:
        NOTES.append('collar boolean left several solids; kept the largest')
    sol = _outer_bed_chamfer(sol, dc.FDM['BED_CHAMFER'], lg['upper_z'][1])
    return cq.Workplane('XY').newObject([dc.one_solid(sol)])



def prepare_print(layout, part_id, finished_shape):
    """Return print stock separately from finished geometry; never put membranes in assembly checks.

    At +X-down print, the first washer-seat layer is a complete bridge disk. Only the
    central 3.4 mm hole is filled, within the finished plate thickness, so clearing
    that hole restores the exact finished seat position and screw engagement.
    """
    assert part_id == 'lens_collar', part_id
    C = layout.COLLAR
    t, seat = C['bridge_membrane_t'], C['flange_x'][1]
    if not 0.0 < t <= 0.3:
        raise ValueError('collar membrane must be one declared 0.2 mm-class layer')
    sh = finished_shape.val() if hasattr(finished_shape, 'val') else finished_shape
    disks = [_cylx(C['hole_d'] / 2 + 0.1, seat - t, seat, *C['feet'][k]) for k in C['bolted']]
    prepared = sh.fuse(*disks).clean()
    added = prepared.Volume() - sh.Volume()
    expected = len(disks) * math.pi * (C['hole_d'] / 2) ** 2 * t
    if not prepared.isValid() or len(prepared.Solids()) != 1 or abs(added - expected) > 0.02:
        raise ValueError('invalid collar print stock or membrane volume mismatch')
    if sh.cut(prepared).Volume() > 0.001:
        raise ValueError('print preparation removed finished material')
    return dict(shape=prepared, added_volume_mm3=round(added, 6),
                membrane_count=len(disks), membrane_thickness_mm=t,
                cleared_hole_d_mm=C['hole_d'],
                postprocess='Clear the three anchor holes to 3.4 mm by hand after printing; remove loose debris; '
                            'do not alter washer seat planes, cone or foot datums. Confirm flat washers at G-COL-1.',
                assembled_geometry='STEP and every assembly/clearance check use the finished shape after clearing')


def build(layout):
    return {'lens_collar': build_part(layout, 'lens_collar')}
