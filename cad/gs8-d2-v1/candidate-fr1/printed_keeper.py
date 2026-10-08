# SPDX-License-Identifier: MIT
"""GS8 D2 r2: the removable Pi keeper (owner: tub / R1, REVIEW finding 1). MODULE CONTRACT in layout.py.

Replaces r1's 4 floor snap hooks (no release access; removing the stack broke the tub). The stack still sits and
locates on its 4 floor bosses (kit screw heads in the boss pockets); this rigid keeper only stops it lifting:
  - 4 fingers at the r1 hook stations (layout PI_KEEPER fingers kf1..kf4): underside 0.1 above the X1203 top, tip
    0.65 over the board edge, face 0.25 off the edge (no positioning load); tip 1.6 thick with a 45 deg back;
  - USB arm (runs under the stick-guide rail), bridge over the panel bosses (z >= 12.5), port bar;
  - 2 x PT 3.0 x 12 PH1 (s_k1 in a 7.0 counterbore, s_k2 on a spot-face notch across the bar) into 2 tub bosses.
Print: top face (z 15.6) on the bed (face_down +Z); every finger back is 45 deg in print; no supports.
Insertion = layout INSERTIONS 'keeper_in'; removal = its exact reverse (REMOVALS 'keeper_out').
"""
import cadquery as cq

import d2_common as dc

V = cq.Vector

PRINT = {
    'pi_keeper': dict(
        face_down='+Z',
        supports='none',
        notes='Top face (z 15.6) on the bed; 4 perimeters, 40 % gyroid (the fingers are solid: 1.6 tip). The s_k2 '
              'spot-face notch bridges 7.0 at 1.3 above the bed; the s_k1 counterbore is a bed-face recess. Finger '
              'backs print at 45 deg. Black ASA.'),
}
if dc.L.FR['keeper']:                                    # FR keeper: no s_k1 counterbore; the tongue tip is on the bed
    PRINT['pi_keeper']['notes'] = (
        'Top face (z 15.6) on the bed; 4 perimeters, 40 % gyroid (the fingers are solid: 1.6 tip). FR1: one screw '
        '(s_k2 spot-face notch bridges 7.0 at 1.3 above the bed); the arm-end tongue (8 x 5.8) prints flat with a '
        '0.6 bed-face chamfer at its tip. Finger backs print at 45 deg. Black ASA.')


def _bx(b):
    return dc.box_solid(b)


def _prism_xz(pts, y0, y1):
    """Polygon in (x, z), extruded along +Y from y0 to y1."""
    pl = cq.Plane(origin=V(0, y0, 0), xDir=V(1, 0, 0), normal=V(0, 1, 0))
    # this plane maps local (u, v) -> world (u, ?, v)? normal +Y with xDir +X gives zDir = +Y, yDir = Z x X... check:
    # yDir = normal x xDir = (0,1,0) x (1,0,0) = (0,0,-1): local v -> world -Z, so negate v.
    return cq.Workplane(pl).polyline([(u, -w) for u, w in pts]).close().extrude(y1 - y0).val()


def _prism_yz(pts, x0, x1):
    """Polygon in (y, z), extruded along +X from x0 to x1."""
    pl = cq.Plane(origin=V(x0, 0, 0), xDir=V(0, 1, 0), normal=V(1, 0, 0))   # yDir = X x Y = +Z
    return cq.Workplane(pl).polyline(pts).close().extrude(x1 - x0).val()


def _fingers(L):
    K = L.PI_KEEPER
    zt = L.PI['x1203_z'][1] + K['gap_z']                 # 7.7
    zb = K['under_z'] + 0.45                             # finger block top, merged into the body (underside 9.8)
    t, w, fb = K['tip_t'], K['finger_w'], K['finger_block']
    out = []
    for f in K['fingers']:
        a = f['at']
        if f['edge'] == 'usb':
            e = L.PI['x'][0]                             # board edge x -91
            face, tip = e - K['gap_xy'], e + K['reach']  # -91.25, -90.35
            out.append(_bx(L.B(face - fb, face + 0.01, a - w / 2, a + w / 2, zt, zb)))
            out.append(_prism_xz([(face - 0.01, zt), (tip, zt), (tip, zt + t), (face - 0.01, zt + t + (tip - face) + 0.01)],
                                 a - w / 2, a + w / 2))
        else:
            e = L.PI['y'][1]                             # board edge y 23.7
            face, tip = e + K['gap_xy'], e - K['reach']  # 23.95, 23.05
            out.append(_bx(L.B(a - w / 2, a + w / 2, face - 0.01, face + fb, zt, zb)))
            out.append(_prism_yz([(face + 0.01, zt), (face + 0.01, zt + t + (face - tip) + 0.01), (tip, zt + t), (tip, zt)],
                                 a - w / 2, a + w / 2))
    return out


def build_part(layout, part_id='pi_keeper'):
    L = layout
    assert part_id == 'pi_keeper', part_id
    K = L.PI_KEEPER
    body = _bx(K['arm']).fuse(_bx(K['bridge']), _bx(K['bar']), *_fingers(L)).clean()
    if L.FR['keeper']:                                   # FR keeper: full-depth -Y tongue into the tub keyed seat;
        t, c = K['tongue'], K['tongue_chamfer']          # 45 deg lead-in at the tip (top edge = bed-face chamfer)
        (y0, y1), (z0, z1) = t['y'], t['z']
        body = body.fuse(_prism_yz([(y1, z0), (y0 + c, z0), (y0, z0 + c), (y0, z1 - c), (y0 + c, z1), (y1, z1)],
                                   *t['x'])).clean()
    cuts = []
    for sid, b in K['bosses'].items():
        x, y = b['c']
        cuts.append(dc.cyl_along(L.PT['clear_d'] / 2, -0.1, K['head_z'] - K['under_z'] + 0.2, (x, y, K['head_z'] + 0.1),
                                 (0, 0, -1)))
        if sid == 's_k1':                                # counterbore in the wide arm
            cuts.append(dc.cyl_along(K['cbore_d'] / 2, -0.1, K['top_z'] - K['head_z'] + 0.1, (x, y, K['top_z'] + 0.1),
                                     (0, 0, -1)))
        else:                                            # spot-face notch across the narrow port bar
            n = K['notch_x'] / 2
            cuts.append(_bx(L.B(x - n, x + n, K['bar']['y'][0] - 0.1, K['bar']['y'][1] + 0.1, K['head_z'], K['top_z'] + 0.1)))
    body = body.cut(*cuts).clean()
    return cq.Workplane('XY').newObject([dc.one_solid(body)])


def build(layout):
    return {'pi_keeper': build_part(layout, 'pi_keeper')}
