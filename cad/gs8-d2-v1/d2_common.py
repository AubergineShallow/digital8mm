# SPDX-License-Identifier: MIT
"""GS8 D2: FDM constants and reusable CadQuery helpers (assembly coordinates, mm).

Numbers live in layout.py (FDM, PT, ...); this module re-exports the FDM constants and builds solids. Every helper
returns a cq.Solid (or a list of them for arrays) so callers can fuse/cut freely; wrap the final part in a
cq.Workplane for the MODULE CONTRACT.  Run heavy work through run_locked.py (see NOTES.md).

Helpers (all tested by test_common.py):
  box_solid(B), cyl_solid(CYL)                       layout dict -> solid
  pt_boss(top, axis, od, height, pilot_depth)        PT 3.0 boss + its pilot cut (pilot 2.5)
  counterbore(head_point, axis, d_cb, depth, d_clear, through)   cut solid for a screw head + shank
  snap_hook(root, hang, tooth_dir, length, t, w, tooth, land, lead_deg)   cantilever hook solid; snap_strain()
  keyhole_tongue(t), keyhole_slot(t)                 tongue solid (tub) / cut solid (base) from a layout TONGUES row
  dovetail(p0, p1, up, base_w, height, angle_deg, grow)   dovetail prism (rail; grow > 0 for the groove cut)
  vent_slots(box, slot_w, pitch, along, face)        list of slot cut solids (rounded ends)
  engrave(items, face_y, depth)                      cut solid for text, arcs, ticks, arrowheads on a +Y face
  bed_chamfer(wp, face_down, size)                   45 deg chamfer on the edges of the bed face
  teardrop(r, t0, t1, origin, axis, up)              horizontal-hole teardrop solid (45 deg roof)
  safe_fillet(wp, selector, r) / safe_chamfer        fillet that falls back to the unfilleted shape, with a note
  fuse_all(shapes), one_solid(shape)
"""
import math
import hashlib
from pathlib import Path

import cadquery as cq

import layout as L

FDM = L.FDM
MIN_WALL, MIN_WALL_LOADED, MIN_FEATURE = FDM['MIN_WALL'], FDM['MIN_WALL_LOADED'], FDM['MIN_FEATURE']
SLIDE, LOCATE, SEAM = FDM['SLIDE'], FDM['LOCATE'], FDM['SEAM']
MAX_OVERHANG_DEG, MAX_BRIDGE = FDM['MAX_OVERHANG_DEG'], FDM['MAX_BRIDGE']
ENGRAVE_DEPTH = FDM['ENGRAVE_DEPTH']
ENGRAVE_TEXT_GROW = FDM['ENGRAVE_TEXT_GROW']   # FIXER P1
SNAP_GUSSET = FDM['SNAP_GUSSET']               # FIXER P2
PT = L.PT
NOTES = []                       # helpers append fallbacks here (e.g. a fillet that failed); owners copy to NOTES.md

V = cq.Vector


def _v(t):
    return V(*[float(x) for x in t])


def _unit(t):
    n = math.sqrt(sum(x * x for x in t))
    return tuple(x / n for x in t)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


# ------------------------------------------------------------------------------------------- basics
def box_solid(b):
    """Solid from a layout B dict."""
    (x0, x1), (y0, y1), (z0, z1) = b['x'], b['y'], b['z']
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl_solid(c, use_r_in=False):
    """Solid (or tube if r_in and use_r_in) from a layout CYL dict."""
    ax = {'x': (1, 0, 0), 'y': (0, 1, 0), 'z': (0, 0, 1)}[c['axis']]
    a0, a1 = c['a']
    c0, c1 = c['c']
    p = {'x': (a0, c0, c1), 'y': (c0, a0, c1), 'z': (c0, c1, a0)}[c['axis']]
    s = cq.Solid.makeCylinder(c['r'], a1 - a0, _v(p), _v(ax))
    if use_r_in and c.get('r_in'):
        s = s.cut(cq.Solid.makeCylinder(c['r_in'], a1 - a0, _v(p), _v(ax)))
    return s


def cyl_along(r, t0, t1, origin, axis):
    ax = _unit(axis)
    p = tuple(origin[i] + ax[i] * t0 for i in range(3))
    return cq.Solid.makeCylinder(r, t1 - t0, _v(p), _v(ax))


def fuse_all(shapes):
    shapes = [s for s in shapes if s is not None]
    out = shapes[0]
    for s in shapes[1:]:
        out = out.fuse(s)
    return out.clean()


def one_solid(shape):
    """Largest solid of a shape (after booleans), as a cq.Solid."""
    sols = shape.Solids() if hasattr(shape, 'Solids') else [shape]
    return max(sols, key=lambda s: s.Volume())


def _local(origin, ex, ey, ez):
    """Transform from a local frame (ex, ey, ez unit, right-handed) to world."""
    pl = cq.Plane(origin=_v(origin), xDir=_v(ex), normal=_v(ez))
    return pl


def _prism(poly_uv, plane, depth0, depth1):
    """Extrude a closed (u, v) polygon on `plane` from normal offset depth0 to depth1 (depth1 > depth0)."""
    wp = cq.Workplane(plane).workplane(offset=depth0).polyline(poly_uv).close().extrude(depth1 - depth0)
    return wp.val()


# ------------------------------------------------------------------------------------------- screws
def pt_boss(top, axis, od=None, height=10.0, pilot_depth=None, pilot_d=None):
    """PT 3.0 boss: cylinder of `od` from `top` (the face the screw enters) along +axis by `height`; axis = screw
    advance direction. Pilot 2.5 from `top` to engage + tip reserve, with a 0.4 entry chamfer.
    Returns (boss_solid, pilot_cut)."""
    od = od or PT['boss_od']
    pilot_d = pilot_d or PT['pilot_d']
    pilot_depth = pilot_depth or (PT['engage_min'] + PT['tip_reserve'])
    ax = _unit(axis)
    boss = cyl_along(od / 2, 0.0, height, top, ax)
    pilot = cyl_along(pilot_d / 2, -0.05, pilot_depth, top, ax)
    cham = cq.Solid.makeCone(pilot_d / 2 + 0.4, pilot_d / 2, 0.4, _v(tuple(top[i] - ax[i] * 0.0 for i in range(3))), _v(ax))
    return boss, pilot.fuse(cham)


def counterbore(head_point, axis, d_cb=None, depth=6.0, d_clear=None, through=12.0):
    """Cut solid: counterbore of d_cb from head_point back (against axis) by `depth`, plus a clearance hole of
    d_clear forward (along axis) by `through`. axis = screw advance direction."""
    d_cb = d_cb or PT['cbore_d']
    d_clear = d_clear or PT['clear_d']
    ax = _unit(axis)
    cb = cyl_along(d_cb / 2, -depth - 0.05, 0.0, head_point, ax)
    hole = cyl_along(d_clear / 2, -0.01, through, head_point, ax)
    return cb.fuse(hole)


# ------------------------------------------------------------------------------------------- snaps
def snap_strain(t, deflection, length):
    """Max bending strain of a uniform rectangular cantilever: 1.5 t d / L^2."""
    return 1.5 * t * deflection / length ** 2


def snap_hook(root, hang, tooth_dir, length, t, w, tooth, land=0.4, lead_deg=45.0, gusset=0.0, ret_deg=0.0):
    """Cantilever snap hook. Local frame: a along `hang` (0 = root, length = tip), b along `tooth_dir`
    (beam b in [-t, 0], tooth b in [0, tooth]), c = a x b (width +-w/2). `root` = (a=0, b=0, c=0): the centre of
    the root edge of the beam's FRONT face (the face that carries the tooth). Catch face (perpendicular to hang)
    at a = length - tooth/tan(lead) - land, flat land, then the lead-in ramp to the tip."""
    ea, eb = _unit(hang), _unit(tooth_dir)
    ec = _cross(ea, eb)
    pl = cq.Plane(origin=_v(root), xDir=_v(ea), normal=_v(ec))       # u = a, v = b (plane y = normal x xDir = eb)
    ramp = tooth / math.tan(math.radians(lead_deg))
    a_c = length - ramp - land
    beam = _prism([(0, -t), (length, -t), (length, 0), (0, 0)], pl, -w / 2, w / 2)
    # FIXER r2: ret_deg > 0 slopes the catch face (a 45 deg return cams out on a straight pull; 0 = positive catch)
    a_r = a_c - tooth * math.tan(math.radians(ret_deg))
    tooth_s = _prism([(a_r, 0), (a_c, tooth), (a_c + land, tooth), (length, 0)], pl, -w / 2, w / 2)
    s = beam.fuse(tooth_s)
    if gusset > 0:   # FIXER P2: 45 deg root gussets on both faces (no sharp 90 deg root; prints as a 45 deg slope)
        g = gusset
        s = s.fuse(_prism([(-0.05, 0), (-0.05, g + 0.05), (g, 0)], pl, -w / 2, w / 2))
        s = s.fuse(_prism([(-0.05, -t), (g, -t), (-0.05, -t - g - 0.05)], pl, -w / 2, w / 2))
    return s.clean()


# ------------------------------------------------------------------------------------------- keyhole (base joint)
def keyhole_tongue(t, chamfer_minus_y=True):
    """Tub T-tongue (neck + head) from a layout TONGUES row; the -Y ends get a 45 deg chamfer (print on -Y)."""
    s = box_solid(t['neck']).fuse(box_solid(t['head']))
    if chamfer_minus_y:
        x0, x1 = t['head']['x']
        y0 = t['head']['y'][0]
        z0, z1 = t['head']['z'][0], t['neck']['z'][1]
        h = z1 - z0
        # wedge that removes the lower-y corner region so the -Y end face slopes 45 deg (grows from the floor)
        pl = cq.Plane(origin=V(x0 - 0.1, 0, 0), xDir=V(0, 1, 0), normal=V(1, 0, 0))
        wedge = _prism([(y0 - 0.01, z0 - 0.01), (y0 + h, z0 - 0.01), (y0 - 0.01, z1 - 0.01)], pl, 0, x1 - x0 + 0.2)
        s = s.cut(wedge)
    return s.clean()


def keyhole_slot(t):
    """Base cut: window + neck slot (through the 1.6 lips) + head pocket."""
    return fuse_all([box_solid(t['base_window']), box_solid(t['base_neck_slot']), box_solid(t['base_pocket'])])


# ------------------------------------------------------------------------------------------- dovetail
def dovetail(p0, p1, up, base_w, height, angle_deg=45.0, grow=0.0):
    """Dovetail prism from p0 to p1. Narrow face (base_w) on the mounting face at p0-p1, widening along `up` by
    2*height/tan(angle) (angle from the mounting face; 45 deg = printable). grow > 0 offsets every face outward
    (use SLIDE for the groove cut)."""
    ax = _unit(tuple(p1[i] - p0[i] for i in range(3)))
    eu = _unit(up)
    ew = _cross(eu, ax)
    lng = math.dist(p0, p1)
    k = height / math.tan(math.radians(angle_deg))
    g = grow
    poly = [(-base_w / 2 - g, -g), (base_w / 2 + g, -g), (base_w / 2 + k + g, height + g), (-base_w / 2 - k - g, height + g)]
    pl = cq.Plane(origin=_v(p0), xDir=_v(ew), normal=_v(ax))
    return _prism(poly, pl, -g, lng + g)


# ------------------------------------------------------------------------------------------- vents
def vent_slots(b, slot_w=2.0, pitch=3.4, along='z', face='+x', overshoot=0.3):
    """Rounded-end slots inside layout box b (cuts through the box's thin dimension, which `face` names).
    `along` = the slot length direction; slots repeat across the remaining in-plane direction."""
    thin = face[1]
    ax_i = 'xyz'.index(thin)
    along_i = 'xyz'.index(along)
    rep_i = ({0, 1, 2} - {ax_i, along_i}).pop()
    lo, hi = b['xyz'[rep_i]]
    n = int((hi - lo - slot_w) // pitch) + 1
    start = (lo + hi) / 2 - (n - 1) * pitch / 2
    a0, a1 = b['xyz'[along_i]]
    t0, t1 = b[thin][0] - overshoot, b[thin][1] + overshoot
    out = []
    for k in range(n):
        c = start + k * pitch
        r = slot_w / 2
        p = [0, 0, 0]
        p[rep_i] = c
        p[along_i] = a0 + r
        p[ax_i] = t0
        d = [0, 0, 0]
        d[ax_i] = 1
        cyl0 = cq.Solid.makeCylinder(r, t1 - t0, _v(p), _v(d))
        p2 = list(p)
        p2[along_i] = a1 - r
        cyl1 = cq.Solid.makeCylinder(r, t1 - t0, _v(p2), _v(d))
        lo3, hi3 = [0, 0, 0], [0, 0, 0]
        lo3[rep_i], hi3[rep_i] = c - r, c + r
        lo3[along_i], hi3[along_i] = a0 + r, a1 - r
        lo3[ax_i], hi3[ax_i] = t0, t1
        mid = cq.Solid.makeBox(hi3[0] - lo3[0], hi3[1] - lo3[1], hi3[2] - lo3[2], _v(lo3))
        out.append(fuse_all([cyl0, cyl1, mid]))
    return out


# ------------------------------------------------------------------------------------------- engraving (+Y face)
def _face_plane(face_y, x=0.0, z=0.0):
    """Plane on a +Y face, seen from +Y: u = -x (reader's right), v = +z, normal +Y."""
    return cq.Plane(origin=V(x, face_y + 0.05, z), xDir=V(-1, 0, 0), normal=V(0, 1, 0))


def _stroke(p0, p1, w):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    n = math.hypot(dx, dy)
    nx, ny = -dy / n * w / 2, dx / n * w / 2
    return [(p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny), (p1[0] - nx, p1[1] - ny), (p0[0] - nx, p0[1] - ny)]


def _uv(c, r, deg):
    """Point at angle deg (0 = up, + = clockwise seen from +Y, i.e. toward -X = +u) radius r about c=(x, z)."""
    a = math.radians(deg)
    return (-c[0] + r * math.sin(a), c[1] + r * math.cos(a))


def _grow_xz(sol, r, n=8):
    """FIXER P1: approximate a 2D outward offset of a +Y-face prism by r (union of n translated copies)."""
    if r <= 0:
        return sol
    cps = [sol] + [sol.translate(V(r * math.cos(2 * math.pi * i / n), 0, r * math.sin(2 * math.pi * i / n)))
                   for i in range(n)]
    out = cps[0]
    for c in cps[1:]:
        out = out.fuse(c)
    return out.clean()


def engraving_font():
    """Exact portable typeface; fail closed instead of silently accepting OS font substitution."""
    path = Path(__file__).resolve().parent / L.ENGRAVE['font_file']
    if not path.is_file():
        raise ValueError('required engraving font is missing: ' + str(path))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != L.ENGRAVE['font_sha256']:
        raise ValueError('engraving font hash mismatch: ' + str(path))
    return dict(family=L.ENGRAVE['font'], kind=L.ENGRAVE['font_kind'], path=str(path), sha256=digest)


def engrave(items, face_y=None, depth=None, font=None, grow=None):
    """Cut solids (list) for layout.ENGRAVE['items'] on the +Y face at face_y, `depth` deep (into -Y).
    Text glyphs grow by ENGRAVE_TEXT_GROW per side (FIXER P1) so bold strokes reach >= 0.8 at h 3.0."""
    font_record = engraving_font()
    if font is not None and font != font_record['family']:
        raise ValueError('engraving font override conflicts with the pinned layout font')
    font = font_record['family']
    grow = ENGRAVE_TEXT_GROW if grow is None else grow
    face_y = L.YL if face_y is None else face_y
    depth = ENGRAVE_DEPTH if depth is None else depth
    pl = _face_plane(face_y)
    d0, d1 = -(depth + 0.05), 0.0
    out = []
    for it in items:
        k = it['kind']
        if k == 'arc':
            c, r, (a0, a1), w = it['c'], it['r'], it['deg'], it['stroke']
            n = max(8, int(abs(a1 - a0) / 3))
            outer = [_uv(c, r + w / 2, a0 + (a1 - a0) * i / n) for i in range(n + 1)]
            inner = [_uv(c, r - w / 2, a0 + (a1 - a0) * i / n) for i in range(n + 1)][::-1]
            out.append(_prism(outer + inner, pl, d0, d1))
        elif k == 'ticks':
            c, (r1, r2), w = it['c'], it['r'], it['stroke']
            for a in it['deg']:
                out.append(_prism(_stroke(_uv(c, r1, a), _uv(c, r2, a), w), pl, d0, d1))
        elif k == 'arrowheads':
            c, r, (ln, half), w = it['c'], it['r'], it['size'], it['stroke']
            for a in it['deg']:
                s = 1.0 if a > 0 else -1.0
                p = _uv(c, r, a)
                back = _uv(c, r, a - s * math.degrees(ln / r))
                for side in (1.0, -1.0):
                    q = _uv(c, r + side * half, a - s * math.degrees(ln / r))
                    q = (back[0] + (q[0] - back[0]), back[1] + (q[1] - back[1]))
                    out.append(_prism(_stroke(q, p, w), pl, d0, d1))
        elif k == 'text':
            x, z = it['at']
            tp = _face_plane(face_y, x, z)
            wp = cq.Workplane(tp).workplane(offset=d1).text(it['text'], it['h'] / 0.72, d0, combine=False,
                                                              font=font, fontPath=font_record['path'], kind=font_record['kind'],
                                                              halign='center', valign='center')
            out.extend(_grow_xz(g, grow) for g in wp.solids().vals())
        else:
            raise ValueError('unknown engraving kind %r' % k)
    return out


# ------------------------------------------------------------------------------------------- print helpers
_SEL = {'-X': '<X', '+X': '>X', '-Y': '<Y', '+Y': '>Y', '-Z': '<Z', '+Z': '>Z'}


def bed_chamfer(wp, face_down, size=None):
    """45 deg chamfer on every edge of the bed face (the extreme face in the face_down direction)."""
    size = size or FDM['BED_CHAMFER']
    try:
        out = wp.faces(_SEL[face_down]).edges().chamfer(size)
        if out.val().isValid():
            return out
    except Exception as e:  # noqa: BLE001 - CAD kernel failures are data here
        NOTES.append('bed_chamfer(%s, %.2f) failed: %s' % (face_down, size, e))
        return wp
    NOTES.append('bed_chamfer(%s) produced an invalid solid; skipped' % face_down)
    return wp


def teardrop(r, t0, t1, origin, axis, up=(0, 0, 1)):
    """Horizontal hole with a 45 deg roof toward `up` (print up): cylinder + tangent triangle, apex r*sqrt(2)."""
    ax, eu = _unit(axis), _unit(up)
    ew = _cross(eu, ax)
    p0 = tuple(origin[i] + ax[i] * t0 for i in range(3))
    cylr = cq.Solid.makeCylinder(r, t1 - t0, _v(p0), _v(ax))
    s = r * math.cos(math.radians(45))
    pl = cq.Plane(origin=_v(p0), xDir=_v(ew), normal=_v(ax))
    roof = _prism([(-s, s), (s, s), (0.0, r * math.sqrt(2.0))], pl, 0.0, t1 - t0)
    tri = _prism([(-s, s), (s, s), (0.0, 0.0)], pl, 0.0, t1 - t0)
    return fuse_all([cylr, roof, tri])


def safe_fillet(wp, selector, r):
    """Fillet edges(selector) by r; on failure or an invalid result keep the input and note it."""
    try:
        out = wp.edges(selector).fillet(r)
        if out.val().isValid():
            return out
    except Exception as e:  # noqa: BLE001
        NOTES.append('fillet %s r%.2f failed: %s' % (selector, r, e))
        return wp
    NOTES.append('fillet %s r%.2f invalid; skipped' % (selector, r))
    return wp


def safe_chamfer(wp, selector, d):
    try:
        out = wp.edges(selector).chamfer(d)
        if out.val().isValid():
            return out
    except Exception as e:  # noqa: BLE001
        NOTES.append('chamfer %s %.2f failed: %s' % (selector, d, e))
        return wp
    NOTES.append('chamfer %s %.2f invalid; skipped' % (selector, d))
    return wp


def wp_of(shape):
    """Wrap a solid as a Workplane (MODULE CONTRACT return type)."""
    return cq.Workplane('XY').newObject([one_solid(shape)])


FACE_DOWN_ROT = {'-Z': (0, 0, 0), '+Z': (180, 0, 0), '+Y': (-90, 0, 0), '-Y': (90, 0, 0),
                 '+X': (0, 90, 0), '-X': (0, -90, 0)}     # (rx, ry, rz) deg applied in x, y, z order


def to_print_pose(shape, face_down):
    """Rotate a solid so `face_down` points -Z, then move it onto z = 0 at the origin (for STL / bed checks)."""
    rx, ry, rz = FACE_DOWN_ROT[face_down]
    s = shape
    for ang, ax in ((rx, (1, 0, 0)), (ry, (0, 1, 0)), (rz, (0, 0, 1))):
        if ang:
            s = s.rotate(V(0, 0, 0), _v(ax), ang)
    bb = s.BoundingBox()
    return s.translate(V(-bb.xmin, -bb.ymin, -bb.zmin))
