# SPDX-License-Identifier: MIT
"""GS8 D2: assembly checks (SPEC.md section 6). Pure functions over a row table; build_d2.py calls them.

rows: {id: dict(shape=cq.Shape (assembly frame, final pose), kind='printed'|'cots'|'hardware', stub=bool, ...)}
Every check returns dict(check=..., status='pass'|'fail'|'stub'|'info', ...). 'stub' means a printed module is not
written yet and its envelope box stands in: the result is computed but cannot pass. Only computed checks say pass;
purchased parts are proxies; nothing is printed, bought or measured.
"""
import math

import cadquery as cq
import numpy as np

import d2_common as dc

V = cq.Vector
VOL_TOL = 0.05            # mm3, exact OCP boolean (SPEC s6.1)
SWEEP_TOL = 0.5           # mm3, mesh boolean on tessellations (tolerance 0.05 mm)
CARRY_SOFT_MM = 1.0       # r7 C1: a carried rigid plug may press a 'cable' keep-out (flexible bundle) this deep
MESH_TOL, MESH_ANG = 0.05, 0.2

# Cable ends as COTS ids (derived from layout.CABLES frm/to text; see NOTES.md interface request).
CABLE_ENDS = {'fpc': ('pi5', 'gs_camera'), 'hdmi': ('pi5', 'evf_board'), 'usb_5v': ('pi5', 'evf_board'),
              'oled_flex': ('hmx039', 'evf_board'), 'qt': ('encoder', 'pi5'), 'run_lead': ('run_button', 'pi5'),
              'fps_lead': ('switch_1824', 'pi5'), 'pigtail': ('x1203', 'xt30_pair'), 'pack_lead': ('pack', 'xt30_pair')}


def _r(x, n=3):
    return None if x is None else round(float(x), n)


def bb_tuple(shape):
    b = shape.BoundingBox()
    return (b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax)


def bb_overlap(a, b, m=0.0):
    return a[0] < b[1] + m and b[0] < a[1] + m and a[2] < b[3] + m and b[2] < a[3] + m and a[4] < b[5] + m and b[4] < a[5] + m


def box_bb(b):
    return (b['x'][0], b['x'][1], b['y'][0], b['y'][1], b['z'][0], b['z'][1])


def common(a, b):
    """Exact OCP boolean common; returns (volume, shape or None)."""
    try:
        c = a.intersect(b)
        v = c.Volume()
        return v, (c if v > 1e-9 else None)
    except Exception as e:     # noqa: BLE001
        return float('nan'), str(e)


# ------------------------------------------------------------------------------------------- mates
def mate_table(L):
    t = {}
    for a, b, kind in L.MATES:
        t[frozenset((a, b))] = kind
    return t


def screw_pierces(L):
    """{screw id: set of part ids it is allowed to pierce} = joins + the part named first in 'into'."""
    out = {}
    for s in L.SCREWS:
        out[s['id']] = set(s['joins']) | {s['into'].split()[0]}
    return out


# ------------------------------------------------------------------------------------------- 1. interference
def check_interference(L, rows):
    mates = mate_table(L)
    pierce = screw_pierces(L)
    ids = [i for i in rows if rows[i].get('shape') is not None]
    bbs = {i: bb_tuple(rows[i]['shape']) for i in ids}
    out = []
    for n, a in enumerate(ids):
        for b in ids[n + 1:]:
            if not bb_overlap(bbs[a], bbs[b]):
                continue
            kind = mates.get(frozenset((a, b)))
            sa, sb = a.startswith('s_'), b.startswith('s_')
            if (sa and b in pierce[a]) or (sb and a in pierce[b]):
                continue                                   # PT screw in its pilot (exempt by id prefix s_)
            if sa and sb:
                continue
            allowed = None
            if kind is not None:
                if kind.startswith('interference'):
                    allowed = float(kind.split()[1])
                else:
                    continue                               # contact / slide / clearance / press / thread: excluded
            v, cs = common(rows[a]['shape'], rows[b]['shape'])
            stub = rows[a].get('stub') or rows[b].get('stub')
            row = dict(pair=[a, b], mate=kind, volume_mm3=_r(v, 4))
            if isinstance(cs, str):
                row.update(status='fail', error=cs)
            elif allowed is not None:
                # thin-layer depth estimate: 2 V / A (a crush layer of thickness t over footprint S has V = S t,
                # A ~ 2 S); exact enough to tell a 0.1 crush from a real clash
                depth = 0.0 if cs is None else 2.0 * v / max(1e-9, cs.Area())
                row.update(allowed_depth=allowed, depth=_r(depth), method='depth = 2 V / A of the common solid')
                row['status'] = 'pass' if depth <= allowed + VOL_TOL else 'fail'
            else:
                row['status'] = 'pass' if v <= VOL_TOL else 'fail'
                if cs is not None:
                    row['where'] = [_r(x, 2) for x in bb_tuple(cs)]
            if stub:
                row['status'] = 'stub'
            if row['status'] != 'pass' or allowed is not None:
                out.append(row)
            else:
                out.append(dict(pair=[a, b], status='pass', volume_mm3=row['volume_mm3']))
    return out


def check_mate_overlap(L, rows):
    """Declared contact / slide / clearance mates may touch but not overlap: volume <= VOL_TOL (SPEC s6.1 excludes
    them from check 1; this is the stricter companion check). The two control-knob D bores have positive
    nominal clearance even though actual printed retention is coupon-fit ('press'); their proxies must not overlap."""
    out = []
    for a, b, kind in L.MATES:
        k = kind.split()[0]
        nominal_control = frozenset((a, b)) in (frozenset(('knob_exp', 'encoder')),
                                                frozenset(('knob_fps', 'switch_1824')))
        if k not in ('contact', 'slide', 'clearance') and not nominal_control:
            continue
        if rows.get(a, {}).get('shape') is None or rows.get(b, {}).get('shape') is None:
            continue
        if not bb_overlap(bb_tuple(rows[a]['shape']), bb_tuple(rows[b]['shape'])):
            out.append(dict(pair=[a, b], mate=kind, volume_mm3=0.0, status='pass'))
            continue
        v, cs = common(rows[a]['shape'], rows[b]['shape'])
        row = dict(pair=[a, b], mate=kind, volume_mm3=_r(v, 4))
        row['status'] = 'pass' if v <= VOL_TOL else 'fail'
        if cs is not None and not isinstance(cs, str):
            row['where'] = [_r(x, 2) for x in bb_tuple(cs)]
        if rows[a].get('stub') or rows[b].get('stub'):
            row['status'] = 'stub'
        out.append(row)
    return out


# ------------------------------------------------------------------------------------------- 2. clearance zones
def clearance_zones(L):
    """(name, part a, part b, zone box (x0,x1,y0,y1,z0,z1), stated clearance)."""
    Z = []
    hk = L.HOOK
    zlo, zhi = L.ZT1 - hk['length'] - 3.5, L.ZT1 - 0.5
    for h in L.HOOD_HOOKS:
        half = hk['w'] / 2 + 1.5
        if h['wall'] == 'right':
            zb = (h['x'] - half, h['x'] + half, h['y_face'] - 0.5, h['y_face'] + 4.0, zlo, zhi)
        elif h['wall'] == 'front':
            zb = (h['x_face'] - 4.0, h['x_face'] + 0.5, h['y'] - half, h['y'] + half, zlo, zhi)
        else:
            zb = (h['x_face'] - 0.5, h['x_face'] + 4.0, h['y'] - half, h['y'] + half, zlo, zhi)
        Z.append(('J1 hook %s to ledge' % h['id'], 'hood', 'tub', zb, hk['play']))
    g = L.HOOD_RAIL['box']
    Z.append(('J2 panel tongue in hood groove', 'hood', 'panel',
              (g['x'][0] - 1, g['x'][1] + 1, g['y'][0] - 0.5, L.SPLIT - 0.1, g['z'][0] - 0.5, L.ZT1 - 0.05), L.SL))
    for t in L.TONGUES:
        p = t['base_pocket']
        Z.append(('J4 %s in base pocket' % t['id'], 'tub', 'base_grip',
                  (p['x'][0] - 1, p['x'][1] + 1, p['y'][0] - 1, p['y'][1] + 1, p['z'][0] - 0.5, -0.05), L.SL))
    ly, lz = L.LENS_AXIS
    # r5 step 1 (J7-R; minimum change to keep checks.py running: CAM 'wall_bore_d'/'ring' and HOOD 'turret_b' are gone).
    #     The 2 "camera ring in tub/hood bore" zones (premise: a dia 36 ring in dia 36.5 bores, wrong camera model) are
    #     replaced by the real-stack equivalents of judge 3 s6.9: BFAR in the tub counterbore (stated = lip gap 0.5, the
    #     axial catch; radial 0.75), adapter in the tub lip (0.825), adapter in the hood plate bore (2.875).
    C = L.CAM
    rc = C['cb_d'] / 2 + 0.5
    Z.append(('J7 BFAR in tub counterbore', 'gs_camera', 'tub',
              (C['cb_x'][0] - 0.25, C['lip_x'] + 0.3, ly - rc, ly + rc, lz - rc, lz + rc), C['lip_gap']))
    rl = C['lip_d'] / 2 + 1.0
    Z.append(('J7 adapter in tub lip', 'c_cs_adapter', 'tub',
              (C['lip_x'] + 0.05, L.XT1 - 0.05, ly - rl, ly + rl, lz - rl, lz + rl),
              round(C['lip_d'] / 2 - C['adapter']['d'] / 2, 4)))
    rb = L.HOOD['bore_d'] / 2 + 1.0
    Z.append(('J7 adapter in hood plate bore', 'c_cs_adapter', 'hood',
              (L.HOOD['plate_x'][0] + 0.05, L.HOOD['plate_x'][1] - 0.05, ly - rb, ly + rb, lz - rb, lz + rb),
              round(L.HOOD['bore_d'] / 2 - C['adapter']['d'] / 2, 4)))
    hb = L.HOOD['housing']
    Z.append(('J8 eyepiece barrel in housing', 'eyepiece', 'hood', box_bb(hb), L.EVF['diopter_clear']))
    K = getattr(L, 'PI_KEEPER', None)
    if K is not None and 'pi_keeper' in L.PARTS:      # FIXER r2 (M-V-MPS-8): panel bosses slide under the keeper bridge
        bb = K['bridge']
        Z.append(('J9 keeper bridge over panel bosses', 'pi_keeper', 'panel',
                  (bb['x'][0], bb['x'][1], bb['y'][0], bb['y'][1], bb['z'][0] - 1.0, bb['z'][0] + 1.0), L.SL))
    pb = L.PI_BUTTON
    Z.append(('J10 plunger nib to Pi button', 'plunger', 'pi5',
              (pb['x_face'] - 0.6, L.PLUNGER['nib']['a'][1] + 0.2, pb['y'] - 3.0, pb['y'] + 3.0, 18.0, 24.5),
              L.PLUNGER['nib']['a'][0] - pb['x_face']))
    return Z


def check_clearances(L, rows):
    out = []
    for name, a, b, zb, stated in clearance_zones(L):
        row = dict(check=name, pair=[a, b], zone=[_r(x, 2) for x in zb], stated=stated, need=_r(0.9 * stated))
        if a not in rows or b not in rows or rows[a].get('shape') is None or rows[b].get('shape') is None:
            row.update(status='n/a', error='partner not in this run')
            out.append(row)
            continue
        zs = cq.Solid.makeBox(zb[1] - zb[0], zb[3] - zb[2], zb[5] - zb[4], V(zb[0], zb[2], zb[4]))
        pa, pb_ = rows[a]['shape'].intersect(zs), rows[b]['shape'].intersect(zs)
        if pa.Volume() < 1e-6 or pb_.Volume() < 1e-6:
            row.update(status='stub' if (rows[a].get('stub') or rows[b].get('stub')) else 'fail',
                       error='feature absent in zone (%s %.3f, %s %.3f mm3)' % (a, pa.Volume(), b, pb_.Volume()))
            out.append(row)
            continue
        v, _ = common(pa, pb_)
        d = 0.0 if v > VOL_TOL else pa.distance(pb_)
        row.update(min_gap=_r(d), overlap_mm3=_r(v, 4))
        row['status'] = 'pass' if d >= 0.9 * stated - 1e-6 else 'fail'
        if rows[a].get('stub') or rows[b].get('stub'):
            row['status'] = 'stub'
        out.append(row)
    return out


# ------------------------------------------------------------------------------------------- 3. keep-outs
def check_keepouts(L, rows):
    out = []
    for pid, r in rows.items():
        if r.get('kind') != 'printed' or r.get('shape') is None:
            continue
        sbb = bb_tuple(r['shape'])
        for kid, kb in L.KEEPOUTS.items():
            if not bb_overlap(sbb, box_bb(kb), -1e-6):
                continue
            v, _ = common(r['shape'], dc.box_solid(kb))
            st = 'pass' if v <= VOL_TOL else ('stub' if r.get('stub') else 'fail')
            out.append(dict(part=pid, keepout=kid, volume_mm3=_r(v, 4), status=st))
    return out


# ------------------------------------------------------------------------------------------- 3b. cable routes (r4)
ROUTE_PASSAGE = 1.0          # consecutive route boxes must share a patch >= this in 2 axes (no gap, no edge touch)
ROUTE_END_TOL = 1.0          # each chain end box must reach (gap <= this) one of the cable's two end parts
ROUTE_ALLOWANCE = (10.0, 0.10)   # service allowance: max(10 mm, 10 % of the cable length)


def _ko(b):
    return [b['x'][0], b['x'][1], b['y'][0], b['y'][1], b['z'][0], b['z'][1]]


def _box_gap(a, b):
    """Largest axis gap between 2 boxes (<= 0 = they touch or overlap)."""
    return max(max(a[2 * i], b[2 * i]) - min(a[2 * i + 1], b[2 * i + 1]) for i in range(3))


def check_cable_routes(L):
    """r4 (wiring maturity): every cable in L.CABLES with a route ('via' keep-out chain) is checked on the boxes alone:
    (a) each pair of consecutive boxes overlaps with a passage >= ROUTE_PASSAGE in 2 axes; (b) the first and last box
    reach the cable's two end parts (CABLE_ENDS, COTS boxes) within ROUTE_END_TOL; (c) an ESTIMATED route length (a
    polyline from the first box centre through the centres of the box-to-box overlaps to the last box centre, plus half
    the largest dimension of each end box) plus a service allowance is within the cable length. Bend radius is NOT
    checked here (the boxes do not carry the cable's path inside them): it stays with the bench gates (G-HDMI,
    MEASURED-PARTS). A direct plug-to-plug lead (no via) is 'info'."""
    out = []
    for c in registry(L, 'CABLES'):
        via = list(c.get('via') or [])
        row = dict(cable=c['id'], length_mm=c['length'], via=via)
        if not via:
            out.append(dict(row, status='info', note='direct plug-to-plug lead, no modelled route (%s)'
                            % ' - '.join(c.get('ends') or ())))
            continue
        missing = [k for k in via if k not in L.KEEPOUTS]
        if missing:
            out.append(dict(row, status='fail', error='route boxes not in KEEPOUTS: ' + ', '.join(missing)))
            continue
        bs = [_ko(L.KEEPOUTS[k]) for k in via]
        probs = []
        for (ka, a), (kb, b) in zip(zip(via, bs), zip(via[1:], bs[1:])):
            ov = [min(a[2 * i + 1], b[2 * i + 1]) - max(a[2 * i], b[2 * i]) for i in range(3)]
            if min(ov) < -1e-6:
                probs.append('%s -> %s: gap %.2f mm' % (ka, kb, -min(ov)))
            elif sorted(ov)[1] < ROUTE_PASSAGE - 1e-6:
                probs.append('%s -> %s: passage only %.2f x %.2f mm' % (ka, kb, sorted(ov)[1], sorted(ov)[2]))
        est = _route_polyline(L, via)[0]
        allow = max(ROUTE_ALLOWANCE[0], ROUTE_ALLOWANCE[1] * c['length'])
        # r7 C2 (SPEC-C2 3.2-2): plug-point rule. A cable with a MATE_POSES plug point (W, or far for an inline row) must
        #     end its chain at that point, not only at the end part's (whole-board) COTS box.
        ppd = None
        for mp in getattr(L, 'MATE_POSES', None) or []:
            if mp.get('cable') != c['id'] or mp.get('both_moving') or not (mp.get('W') or mp.get('far')):
                continue
            pp = _plug_point(L, mp.get('W') or mp.get('far'))
            d = _pt_box_dist(pp, bs[-1])
            ppd = d if ppd is None else max(ppd, d)
            if d > ROUTE_END_TOL + 1e-9:
                probs.append('last box %s ends %.2f mm from the %s plug point %s (> %.1f)'
                             % (via[-1], d, mp['id'], [_r(x, 2) for x in pp], ROUTE_END_TOL))
        if est + allow > c['length'] + 1e-6:
            probs.append('estimated route %.1f + allowance %.1f > cable length %d mm' % (est, allow, c['length']))
        ends = [e for e in (c.get('ends') or ()) if (L.COTS.get(e) or {}).get('box')]
        end_gap = None
        if len(ends) != 2:
            probs.append('end parts with a box: %s (need 2)' % ends)
        else:
            e0, e1 = (_ko(L.COTS[e]['box']) for e in ends)
            end_gap = min(max(_box_gap(bs[0], e0), _box_gap(bs[-1], e1)),
                          max(_box_gap(bs[0], e1), _box_gap(bs[-1], e0)))
            if end_gap > ROUTE_END_TOL:
                probs.append('chain ends %.1f mm from its end parts %s' % (end_gap, ', '.join(ends)))
        row.update(est_route_mm=_r(est, 1), allowance_mm=_r(allow, 1), slack_mm=_r(c['length'] - est - allow, 1),
                   end_gap_mm=None if end_gap is None else _r(end_gap, 2), problems=probs,
                   status='fail' if probs else 'pass', estimate=True)
        if ppd is not None:
            row['plug_point_mm'] = _r(ppd, 2)          # r7 C2
        if probs:
            row['error'] = '; '.join(probs)
        out.append(row)
    return out


# ------------------------------------------------------------------------------------------- 3c. mating poses (r7 C2)
STOW_FILL = 0.25             # r7 C2: usable fraction of a stow box for a folded lead bundle (design value; G-QT-1)
STOW_BLOWER_MIN = 2.0        # r7 C2: plan distance of a stow box from the cooler blower footprint
STOW_INFO_HOME = {'fpc': 'ko_fpc_loop S-fold by design (home check: cable_routes fpc fold row, SPEC-C4; P2-6)',
                  'hdmi': 'ko_hdmi_coil'}
MATE_POSE_TOL = 0.01         # r7 C2: a mating pose must lie on its insertion's path polyline within this
TAIL_D = 3.0                 # r7 C2: lead tail tested as a dia 3 cylinder from the anchor point to the plug


def _route_polyline(L, via, end_point=None):
    """r7 C2 (SPEC-C2 3.2-1): the cable_routes length estimate. end_point None: first box centre -> centres of the
    box-to-box overlaps -> last box centre, plus half the largest dimension of each end box (the r4 estimate, exact).
    With a point: the polyline ends at the point of the last box nearest to it (clamp) instead of adding its half.
    -> (length, points, last-box point)"""
    bs = [_ko(L.KEEPOUTS[k]) for k in via]
    pts = [[(bs[0][2 * i] + bs[0][2 * i + 1]) / 2 for i in range(3)]]
    for a, b in zip(bs, bs[1:]):
        pts.append([(max(a[2 * i], b[2 * i]) + min(a[2 * i + 1], b[2 * i + 1])) / 2 for i in range(3)])

    def half(b):
        return max(b[1] - b[0], b[3] - b[2], b[5] - b[4]) / 2
    if end_point is None:
        last = [(bs[-1][2 * i] + bs[-1][2 * i + 1]) / 2 for i in range(3)]
        tail = half(bs[0]) + half(bs[-1])
    else:
        last = [min(max(end_point[i], bs[-1][2 * i]), bs[-1][2 * i + 1]) for i in range(3)]
        tail = half(bs[0])
    pts.append(last)
    return sum(math.dist(p, q) for p, q in zip(pts, pts[1:])) + tail, pts, tuple(last)


def _pt_box_dist(p, b):
    """Distance from point p to box b = (x0, x1, y0, y1, z0, z1)."""
    return math.sqrt(sum(max(b[2 * i] - p[i], 0.0, p[i] - b[2 * i + 1]) ** 2 for i in range(3)))


def _plug_point(L, spec):
    """r7 C2: a MATE_POSES plug point. Numbers as given; ('qt_socket', i): wire exit W of the SH plug in encoder socket
    i (the layout.qt_plug_point formula on L.ENCODER / L.PLUG, so moved data moves it); ('switch_lugs',): (SWITCH_1824
    c x, body a0, c z)."""
    if isinstance(spec[0], str):
        if spec[0] == 'qt_socket':
            e = L.ENCODER
            q, pl = e['qt_socket'], L.PLUG['jst_sh_4']
            i = spec[1] if len(spec) > 1 else 0
            return (e['c'][0] + q['dx'][i] - q['w'] / 2 - pl['len'], (q['y0'] + e['pcb']['y'][0]) / 2, e['c'][1])
        if spec[0] == 'switch_lugs':
            sw = L.SWITCH_1824
            return (sw['c'][0], sw['body']['a'][0], sw['c'][1])
        raise ValueError('unknown plug point %r' % (spec,))
    return tuple(float(x) for x in spec)


def _on_path(path, d, tol=MATE_POSE_TOL):
    for a, b in zip(path, path[1:]):
        ab = [b[i] - a[i] for i in range(3)]
        n2 = sum(x * x for x in ab)
        t = 0.0 if n2 == 0 else max(0.0, min(1.0, sum((d[i] - a[i]) * ab[i] for i in range(3)) / n2))
        if math.dist(d, [a[i] + ab[i] * t for i in range(3)]) <= tol:
            return True
    return False


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _hand_box(rear, axis, row, env):
    """r7 C2: hand envelope (a, t, r): a behind `rear` along -axis, t along axis x row, r along row, centred on the
    line; returned as the axis-aligned box of its corners (exact for axis-aligned axis/row, larger otherwise)."""
    a, t, r = env
    nrm = math.sqrt(sum(x * x for x in axis)) or 1.0
    ax = [x / nrm for x in axis]
    th = _cross(ax, row)
    cs = [[rear[i] - sa * a * ax[i] + st * t * th[i] + sr * r * row[i] for i in range(3)]
          for sa in (0.0, 1.0) for st in (-0.5, 0.5) for sr in (-0.5, 0.5)]
    return tuple(f(c[i] for c in cs) for i in range(3) for f in (min, max))


def _out_of_mm(box, out_of):
    """(signed axis, plane, margin): how far the whole box lies beyond plane + margin on that side (>= 0 holds)."""
    sgn, ax = out_of[0][0], 'xyz'.index(out_of[0][1])
    return (box[2 * ax] - out_of[1] - out_of[2]) if sgn == '+' else (out_of[1] - out_of[2] - box[2 * ax + 1])


def _pose_targets(L, rows, n, disp, exclude, cache):
    """r7 C2: parts present at insertion n's step (later same-step movers absent), its moving set displaced by disp:
    COTS parts as their boxes, printed parts and screws as their shapes (only when rows is given).
    -> [(id, manifold, bbox)]"""
    import manifold3d as m3
    ins = L.INSERTIONS[n]
    later = set()
    for o in L.INSERTIONS[n + 1:]:
        if o['step'] == ins['step']:
            later |= set(o['moving'])
    mv = set(ins['moving'])
    out = []
    for i in L.present_at(ins['step']):
        if i in later or i in exclude:
            continue
        d = tuple(disp) if i in mv else (0.0, 0.0, 0.0)
        cb = (L.COTS.get(i) or {}).get('box')
        if cb is not None:
            b = box_bb(cb)
        elif rows is not None and (rows.get(i) or {}).get('shape') is not None:
            b = bb_tuple(rows[i]['shape'])
        else:
            continue
        b = (b[0] + d[0], b[1] + d[0], b[2] + d[1], b[3] + d[1], b[4] + d[2], b[5] + d[2])
        if cb is not None:
            out.append((i, _bb_cube(m3, b), b))
            continue
        if i not in cache:
            cache[i] = manifold_of(rows[i]['shape'])
        out.append((i, cache[i].translate(list(d)), b))
    return out


def _tail_manifold(p0, p1, d=TAIL_D):
    import manifold3d as m3
    import numpy as np
    u = np.array(p1, float) - np.array(p0, float)
    h = float(np.linalg.norm(u))
    if h < 1e-6:
        return None
    u /= h
    e1 = np.cross(u, [1.0, 0, 0] if abs(u[0]) < 0.9 else [0, 1.0, 0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(u, e1)
    mat = np.column_stack([e1, e2, u, np.array(p0, float)])
    return m3.Manifold.cylinder(h, d / 2, d / 2, 16).transform(mat)


def _hits_of(m, mbb, targets, tol=SWEEP_TOL):
    out = []
    for o, om, obb in targets:
        if not bb_overlap(mbb, obb, -1e-6):
            continue
        v = (m ^ om).volume()
        if v > tol:
            out.append(dict(obstacle=o, volume_mm3=_r(v, 2)))
    return out


def check_mate_reach(L, rows=None, cache=None):
    """r7 C2 (SPEC-C2 3.2-3 + Plan edits P2-1/P2-4/P2-5): one row per MATE_POSES entry. Pose on the insertion path;
    reach with checks.reach_margin (plug rows: length_min - fixed - tail - margin >= 0; inline rows: r1 + r2 >= d and
    the junction window midpoint >= junction_out beyond the opening); an oriented hand envelope and a dia 3 tail path
    against every part present in the mating pose (COTS boxes always, printed shapes when rows is given; <= SWEEP_TOL);
    the whole hand box beyond the opening (out_of). Sub-results named in a row's `info` are reported, not failed."""
    import manifold3d as m3
    cache = {} if cache is None else cache
    cab = {c['id']: c for c in L.CABLES}
    out = []
    for mp in getattr(L, 'MATE_POSES', None) or []:
        row = dict(id=mp['id'], cable=mp.get('cable'), step=mp.get('step'), insertion=mp.get('insertion'),
                   estimate=True)
        n = _ins_index(L, mp.get('insertion'))
        if mp.get('both_moving'):
            out.append(dict(row, status='info', note='both ends ride in one moving set'))
            continue
        if n is None or mp.get('cable') not in cab:
            out.append(dict(row, status='fail', error='unknown insertion or cable'))
            continue
        if mp.get('reach') == 'pigtail':
            fn = globals().get('_pigtail_mate_row')       # SPEC-C3 (S4) owns the pigtail reach model
            if fn is None:
                out.append(dict(row, status='fail', error='pigtail reach model missing (SPEC-C3 / S4)'))
                continue
            out.append(fn(L, mp, row, rows, cache))
            continue
        ins, c = L.INSERTIONS[n], cab[mp['cable']]
        disp = tuple(float(x) for x in mp['disp'])
        probs, info = [], []
        if not _on_path(ins['path'], disp):
            probs.append('mate pose %s not on the insertion path of %s' % (list(disp), ins['id']))
        lmin = (c.get('length_range') or (c['length'],))[0]
        m = reach_margin(L, lmin)
        via = list(c.get('via') or [])
        if mp.get('anchor') not in via:
            out.append(dict(row, status='fail', error='anchor %s not in the %s via' % (mp.get('anchor'), c['id'])))
            continue
        sub = via[:via.index(mp['anchor']) + 1]
        inline = bool(mp.get('inline_of') or mp.get('inline'))
        pt = _plug_point(L, mp['far'] if inline else mp['W'])
        ptd = tuple(pt[i] + disp[i] for i in range(3))
        fixed, _pts, apt = _route_polyline(L, sub, end_point=ptd)
        row.update(pose=list(disp), length_min=lmin, margin=_r(m, 1), fixed_mm=_r(fixed, 1),
                   anchor=mp['anchor'], anchor_pt=[_r(x, 2) for x in apt])
        row_ax = mp.get('row', (0, 0, 1))
        hb2 = None                                       # r7 fix-up: the far-side pinch of a two-hand inline mate
        if inline:
            pig = float(mp['pigtail']) if 'pigtail' in mp else float(c.get('pigtail') or 0.0)
            r1 = lmin - fixed - m
            r2 = max(0.0, pig - reach_margin(L, pig)) if pig > 0 else 0.0
            d = math.dist(apt, ptd)
            t0, t1 = max(0.0, d - r2), min(d, r1)
            u = [(ptd[i] - apt[i]) / d for i in range(3)] if d > 1e-9 else [0.0, 1.0, 0.0]
            mid_t = (t0 + t1) / 2
            mid = tuple(apt[i] + u[i] * mid_t for i in range(3))
            op = mp.get('opening', ('+y', L.SPLIT))
            jo = _out_of_mm((mid[0], mid[0], mid[1], mid[1], mid[2], mid[2]), (op[0], op[1], 0.0))
            row.update(r1_mm=_r(r1, 1), r2_mm=_r(r2, 1), pigtail_mm=pig, d_mm=_r(d, 1),
                       window=[[_r(apt[i] + u[i] * t0, 1) for i in range(3)], [_r(apt[i] + u[i] * t1, 1)
                                                                              for i in range(3)]],
                       window_mid=[_r(x, 1) for x in mid], junction_out_mm=_r(jo, 1),
                       slack_mm=_r(r1 + r2 - d, 1))
            if r1 < 0 or r1 + r2 < d - 1e-9:
                probs.append('junction cannot be reached: r1 %.1f + r2 %.1f < d %.1f' % (r1, r2, d))
            elif jo < mp.get('junction_out', 15.0) - 1e-9:
                probs.append('junction window midpoint %.1f beyond the opening < %.1f'
                             % (jo, mp.get('junction_out', 15.0)))
            hb = _hand_box(tuple(mid[i] + u[i] * L.HAND_ENVELOPES[mp['hand']][0] / 2 for i in range(3)), u, row_ax,
                           L.HAND_ENVELOPES[mp['hand']])
            tail_to = mid
            if mp.get('hand2'):
                # r7 fix-up (VERIFY-C2): an inline pair is mated with two hands, one pinch per housing: the body-side
                #   pinch lies behind the junction J (toward the anchor), the far-side pinch ahead of it. J is the
                #   window point nearest the midpoint at which the body-side pinch is wholly beyond the opening.
                e2 = L.HAND_ENVELOPES[mp['hand2']]
                jt = None
                tt = mid_t
                while tt <= t1 + 1e-9:
                    jp = tuple(apt[i] + u[i] * tt for i in range(3))
                    if _out_of_mm(_hand_box(jp, u, row_ax, e2), mp['out_of']) >= -1e-9:
                        jt = tt
                        break
                    tt += 0.5
                jt = t1 if jt is None else jt
                jp = tuple(apt[i] + u[i] * jt for i in range(3))
                hb_near = _hand_box(jp, u, row_ax, e2)
                hb_far = _hand_box(tuple(jp[i] + u[i] * e2[0] for i in range(3)), u, row_ax, e2)
                hb = hb_near
                hb2 = hb_far
                row.update(junction_at=[_r(x, 1) for x in jp], hand2=mp['hand2'])
                tail_to = jp
        else:
            tail = math.dist(apt, ptd)
            slack = lmin - fixed - tail - m
            row.update(tail_mm=_r(tail, 1), slack_mm=_r(slack, 1))
            if slack < -1e-9:
                probs.append('lead short by %.1f mm in the mating pose (L %d, fixed %.1f, tail %.1f, margin %.1f)'
                             % (-slack, lmin, fixed, tail, m))
            hb = _hand_box(ptd, mp['axis'], row_ax, L.HAND_ENVELOPES[mp['hand']])
            tail_to = ptd
        ex = {mp['end']}
        tg = _pose_targets(L, rows, n, disp, ex, cache)
        hh = _hits_of(_bb_cube(m3, hb), hb, tg)
        oo = _out_of_mm(hb, mp['out_of'])
        if hb2 is not None:
            hh = hh + _hits_of(_bb_cube(m3, hb2), hb2, tg)
            oo = min(oo, _out_of_mm(hb2, mp['out_of']))
            row['hand_box2'] = [_r(x, 2) for x in hb2]
        tm = _tail_manifold(apt, tail_to)
        th = [] if tm is None else _hits_of(tm, tuple(f(apt[i], tail_to[i]) + s * TAIL_D / 2 for i in range(3)
                                                      for f, s in ((min, -1), (max, 1))), tg)
        row.update(hand=mp['hand'], hand_box=[_r(x, 2) for x in hb], hand_hits=hh, out_of=list(mp['out_of']),
                   out_of_mm=_r(oo, 2), tail_hits=th, targets=len(tg), shapes=rows is not None)
        for nm, bad, msg in (('hand', hh, 'hand envelope hits %s' % ', '.join(h['obstacle'] for h in hh)),
                             ('out_of', oo < -1e-9, 'hand envelope %.2f mm short of %s' % (-oo, mp['out_of'])),
                             ('tail', th, 'tail path blocked by %s' % ', '.join(h['obstacle'] for h in th))):
            if bad:
                (info if nm in (mp.get('info') or ()) else probs).append(msg)
        if info:
            row.update(info_only=info, gate=mp.get('gate'))
        if probs:
            row['error'] = '; '.join(probs)
        out.append(dict(row, problems=probs, status='fail' if probs else 'pass'))
    return out


# ------------------------------------------------------------------------------------------- 3d. lead access (r7 C3)
LEAD_CLEAR_TOL = 0.01        # r7 C3: pigtail_wrap_clear volume tolerance (a 0.5 mm keeper sliver is < SWEEP_TOL)
LEAD_WINDOW_STEP = 0.5       # r7 C3: run_lead_window sampling along base_on


def _pig_cable(L):
    return next(c for c in L.CABLES if c['id'] == 'pigtail')


def _pigtail_path(L):
    """r7 C3 (SPEC-C3 3.2-1): W_top = (Wx, Wy + w_top_dy, ko_pig_wrap z1) -> the overlap centres of the via boxes from
    the first box to ko_pig_drop (the cable_routes polyline points, _route_polyline) -> the hole top (centre of
    FLOOR_HOLES['pigtail'], z = ko_pig_drop z1). -> (path_in length, points)"""
    P, K = L.PIGTAIL, L.KEEPOUTS
    via = list(_pig_cable(L)['via'])
    sub = via[:via.index('ko_pig_drop') + 1]
    wx, wy = P['wrap_entry']
    fh = L.FLOOR_HOLES['pigtail']
    pts = ([(wx, wy + P['w_top_dy'], K[sub[0]]['z'][1])] + [tuple(p) for p in _route_polyline(L, sub)[1][1:-1]]
           + [((fh['x'][0] + fh['x'][1]) / 2, (fh['y'][0] + fh['y'][1]) / 2, K['ko_pig_drop']['z'][1])])
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:])), pts


def _pt_seg_dist(p, a, b):
    ab = [b[i] - a[i] for i in range(3)]
    n2 = sum(x * x for x in ab)
    t = 0.0 if n2 == 0 else max(0.0, min(1.0, sum((p[i] - a[i]) * ab[i] for i in range(3)) / n2))
    return math.dist(p, [a[i] + ab[i] * t for i in range(3)])


def _pigtail_face_out(L, pad=None, length=None):
    """r7 C3 (SPEC-C3 3.2-1, Plan edits P3-1/P3-2): the ONE pigtail length model (lead_access rows 1-3 and the xt30
    MATE_POSES row). face_out = L - reach_margin(L) - d_board - path_in - drop - detour + housing_credit: how far the
    XT30 wire end (housing not credited) comes out of the grip mouth with the service allowance kept. d_board: top
    face |x - Wx| + |y - Wy|; underside Manhattan(pad, hole centre) - path_in (min 0). detour: 2 x the distance from
    the tie point to the route polyline (pad, W_top, ..., hole top); tie at='pad' gives 0."""
    P = L.PIGTAIL
    pad = P['pad'] if pad is None else pad
    Lc = float(_pig_cable(L)['length'] if length is None else length)
    path_in, pts = _pigtail_path(L)
    drop = pts[-1][2] - L.GRIP['bay']['z'][0]
    (wx, wy), (x, y) = P['wrap_entry'], pad['xy']
    top = pad.get('face', 'top') == 'top'
    d_board = abs(x - wx) + abs(y - wy) if top else max(0.0, abs(x - pts[-1][0]) + abs(y - pts[-1][1]) - path_in)
    at = (P.get('tie') or {}).get('at', 'pad')
    if isinstance(at, str):
        if at != 'pad':
            raise ValueError('PIGTAIL tie at %r: use \'pad\' or an (x, y, z) point' % (at,))
        detour = 0.0
    else:
        poly = [(x, y, L.PI['x1203_z'][1] if top else L.PI['x1203_z'][0])] + list(pts)
        detour = 2.0 * min(_pt_seg_dist(at, a, b) for a, b in zip(poly, poly[1:]))
    credit = float(P.get('housing_credit') or 0.0)
    allow = reach_margin(L, Lc)
    taut = Lc - d_board - path_in - drop - detour + credit
    return dict(length_mm=Lc, face_out_mm=taut - allow, taut_mm=taut, allowance_mm=allow, d_board_mm=d_board,
                path_in_mm=path_in, drop_mm=drop, detour_mm=detour, housing_credit_mm=credit)


def _pigtail_required_len(L, pad=None):
    """Smallest cut_round step whose face_out >= face_out_min (None if none up to 5 m)."""
    P = L.PIGTAIL
    for k in range(1, int(5000 / P['cut_round']) + 1):
        if _pigtail_face_out(L, pad, k * P['cut_round'])['face_out_mm'] >= P['face_out_min'] - 1e-9:
            return k * P['cut_round']
    return None


def _pigtail_pad_samples(L):
    """The 4 X1203 corners on both faces, the cots.py XH header estimate and the assumed pad (10 samples)."""
    P = L.PIGTAIL
    R = P['pad_range']
    out = [('%s (%.1f, %.1f)' % (f, x, y), dict(face=f, xy=(x, y))) for f in R['faces'] for x in R['x'] for y in R['y']]
    if R.get('xh'):
        out.append(('xh estimate top (%.1f, %.1f)' % tuple(R['xh']), dict(face='top', xy=tuple(R['xh']))))
    out.append(('assumed pad', dict(P['pad'])))
    return out


def _pigtail_mate_row(L, mp, row, rows, cache):
    """r7 C3 (SPEC-C3 3.2, Plan edit P3-1): the xt30 MATE_POSES row. Slack = _pigtail_face_out(L, pad) -
    face_out_min (one length model, one number with lead_access pigtail_xt30_mouth). Plus: the pose on the insertion
    path; the pose puts W at least out_of margin beyond the mouth; the hand box (both housings held: it spans a from
    W along the draw-out axis `axis`, t along axis x row, r along row) against every part present in the pose (COTS
    boxes always, printed shapes when rows is given; <= SWEEP_TOL) and wholly beyond the mouth (out_of); the dia 3 tail
    path from the anchor to W."""
    import manifold3d as m3
    n = _ins_index(L, mp['insertion'])
    ins, P, c = L.INSERTIONS[n], L.PIGTAIL, _pig_cable(L)
    disp = tuple(float(x) for x in mp['disp'])
    probs, info = [], []
    if not _on_path(ins['path'], disp):
        probs.append('mate pose %s not on the insertion path of %s' % (list(disp), ins['id']))
    fo = _pigtail_face_out(L)
    slack = fo['face_out_mm'] - P['face_out_min']
    via = list(c.get('via') or [])
    if mp.get('anchor') not in via:
        return dict(row, status='fail', error='anchor %s not in the %s via' % (mp.get('anchor'), c['id']))
    W = _plug_point(L, mp['W'])
    ptd = tuple(W[i] + disp[i] for i in range(3))
    # the length model drops vertically from the hole centre (SPEC-C3 3.2-1: drop = hole top to the mouth plane), so the
    #   tail starts on that line at the anchor box bottom, not at the generic clamp corner of the anchor box
    fh, ab = L.FLOOR_HOLES['pigtail'], box_bb(L.KEEPOUTS[mp['anchor']])
    apt = tuple(min(max(v, ab[2 * i]), ab[2 * i + 1]) for i, v in
                enumerate(((fh['x'][0] + fh['x'][1]) / 2, (fh['y'][0] + fh['y'][1]) / 2, ab[4])))
    pose_out = _out_of_mm((ptd[0], ptd[0], ptd[1], ptd[1], ptd[2], ptd[2]), mp['out_of'])
    row.update(pose=list(disp), reach='pigtail', model='_pigtail_face_out (= lead_access pigtail_xt30_mouth)',
               length_mm=fo['length_mm'], face_out_mm=_r(fo['face_out_mm'], 1), face_out_min=P['face_out_min'],
               slack_mm=_r(slack, 1), allowance_mm=_r(fo['allowance_mm'], 1), d_board_mm=_r(fo['d_board_mm'], 1),
               detour_mm=_r(fo['detour_mm'], 1), housing_credit_mm=fo['housing_credit_mm'], anchor=mp['anchor'],
               anchor_pt=[_r(x, 2) for x in apt], W_pose=[_r(x, 2) for x in ptd], tail_mm=_r(math.dist(apt, ptd), 1),
               pose_out_mm=_r(pose_out, 2))
    if slack < -1e-9:
        probs.append('pigtail XT30 comes only %.1f mm out of the mouth (< %.1f): L %.0f, d_board %.1f, detour %.1f'
                     % (fo['face_out_mm'], P['face_out_min'], fo['length_mm'], fo['d_board_mm'], fo['detour_mm']))
    if pose_out < -1e-9:
        probs.append('mate pose puts W %.2f mm short of %s' % (-pose_out, mp['out_of']))
    hb = _hand_box(ptd, tuple(-a for a in mp['axis']), mp.get('row', (1, 0, 0)), L.HAND_ENVELOPES[mp['hand']])
    # `hang` (part on its own lead, not rigid during the mate): the part is lowered along z until its top clears the
    #   hand box, stays a target there, and its lead must span from the end part's lead side to it with the margin
    hg = mp.get('hang')
    tg = _pose_targets(L, rows, n, disp, {mp['end']} | ({hg['part']} if hg else set()), cache)
    if hg:
        hbox = box_bb(L.COTS[hg['part']]['box'])
        extra = min(0.0, hb[4] - (hbox[5] + disp[2]))
        hd = (disp[0], disp[1], disp[2] + extra)
        hbb = (hbox[0] + hd[0], hbox[1] + hd[0], hbox[2] + hd[1], hbox[3] + hd[1], hbox[4] + hd[2], hbox[5] + hd[2])
        tg.append((hg['part'], _bb_cube(m3, hbb), hbb))
        eb = box_bb(L.COTS[mp['end']]['box'])
        lx = eb[1] if hg.get('lead_end') == '+x' else eb[0]       # r7 fix-up: the pack lead (male) end of the pair
        lp = (lx + disp[0], (eb[2] + eb[3]) / 2 + disp[1], (eb[4] + eb[5]) / 2 + disp[2])
        near = tuple(min(max(lp[i], hbb[2 * i]), hbb[2 * i + 1]) if i < 2 else hbb[5] for i in range(3))
        hl = next(c_['length'] for c_ in L.CABLES if c_['id'] == hg['cable'])
        need = math.dist(lp, near) + reach_margin(L, hl)
        row.update(hang=dict(part=hg['part'], cable=hg['cable'], lowered_mm=_r(-extra, 2), lead_mm=hl,
                             need_mm=_r(need, 1), slack_mm=_r(hl - need, 1)))
        if need > hl + 1e-9:
            probs.append('%s cannot hang below the hand on its %s: needs %.1f > %d mm' % (hg['part'], hg['cable'], need,
                                                                                         hl))
    hh = _hits_of(_bb_cube(m3, hb), hb, tg)
    oo = _out_of_mm(hb, mp['out_of'])
    tm = _tail_manifold(apt, ptd)
    th = [] if tm is None else _hits_of(tm, tuple(f(apt[i], ptd[i]) + s * TAIL_D / 2 for i in range(3)
                                                  for f, s in ((min, -1), (max, 1))), tg)
    row.update(hand=mp['hand'], hand_box=[_r(x, 2) for x in hb], hand_hits=hh, out_of=list(mp['out_of']),
               out_of_mm=_r(oo, 2), tail_hits=th, targets=len(tg), shapes=rows is not None)
    for nm, bad, msg in (('hand', hh, 'hand envelope hits %s' % ', '.join(h['obstacle'] for h in hh)),
                         ('out_of', oo < -1e-9, 'hand envelope %.2f mm short of %s' % (-oo, mp['out_of'])),
                         ('tail', th, 'tail path blocked by %s' % ', '.join(h['obstacle'] for h in th))):
        if bad:
            (info if nm in (mp.get('info') or ()) else probs).append(msg)
    if info:
        row.update(info_only=info, gate=mp.get('gate'))
    if probs:
        row['error'] = '; '.join(probs)
    return dict(row, problems=probs, status='fail' if probs else 'pass')


def _keeper_standin(L):
    """Fast stand-in for the pi_keeper solid near the port edge: the bar plus the port finger blocks (kf3/kf4)."""
    K, e = L.PI_KEEPER, L.PI['y'][1]
    out = [box_bb(K['bar'])]
    for f in K['fingers']:
        if f['edge'] == 'port':
            out.append((f['at'] - K['finger_w'] / 2, f['at'] + K['finger_w'] / 2, e - K['reach'],
                        e + K['gap_xy'] + K['finger_block'], L.PI['x1203_z'][1] + K['gap_z'], K['under_z'] + 0.45))
    return out


def _pigtail_store_exits(L, rows, pb, od):
    """r7 fix-up (VERIFY-C3): clear length beyond each x end of the stored XT30 pair box pb, within its (y, z) section,
    to the nearest solid present at step 10 (run_button and pack boxes; base_grip solid when rows is given, else the
    GRIP bay walls). Required: PIGTAIL bend flex_r_od x od + od (+ rigid exit >= 0, unknown: G-MP-PACK)."""
    P = L.PIGTAIL
    need = P['bend']['flex_r_od'] * od + od
    bay = box_bb(L.GRIP['bay'])
    res = {}
    for end, sgn in (('+x', 1), ('-x', -1)):
        x_end = pb[1] if sgn > 0 else pb[0]
        best, who = (bay[1] - x_end) if sgn > 0 else (x_end - bay[0]), 'bay wall'
        for cid in ('run_button', 'pack'):
            b = box_bb(L.COTS[cid]['box'])
            if b[2] < pb[3] and pb[2] < b[3] and b[4] < pb[5] and pb[4] < b[5]:
                d = (b[0] - x_end) if sgn > 0 else (x_end - b[1])
                if -1e-9 <= d < best:
                    best, who = d, cid
        sh = (rows or {}).get('base_grip', {}).get('shape') if rows else None
        if sh is not None:
            lo = [x_end if sgn > 0 else x_end - 30.0, pb[2], pb[4]]
            hi = [x_end + 30.0 if sgn > 0 else x_end, pb[3], pb[5]]
            try:
                c = sh.intersect(cq.Solid.makeBox(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2], V(*lo)))
                if c.Volume() > 0.05:
                    bb = c.BoundingBox()
                    d = (bb.xmin - x_end) if sgn > 0 else (x_end - bb.xmax)
                    if d < best:
                        best, who = max(0.0, d), 'base_grip'
            except Exception:  # noqa: BLE001
                pass
        res[end] = dict(clear_mm=_r(best, 2), nearest=who, need_min_mm=_r(need, 2))
    bad = ['%s end %.1f mm to %s < %.1f' % (e, v['clear_mm'], v['nearest'], need) for e, v in res.items()
           if v['clear_mm'] < need - 1e-9]
    allow = min(v['clear_mm'] - v['need_min_mm'] for v in res.values())
    return dict(ends=res, rigid_exit='unknown (G-MP-PACK), lower bound 0', rigid_allow_mm=_r(allow, 2),
                gate='G-MP-PACK: the rigid solder-cup / heat-shrink length beyond each XT30 housing must be <= '
                     'rigid_allow_mm (measure; else re-pose)', status='fail' if bad else 'pass',
                **({'error': '; '.join(bad)} if bad else {}))


def _pigtail_drop_v(L, l_cut):
    """r7 fix-up (VERIFY-C3): WIRING s4 drop estimate (the G-W5 model) at L_cut: 2 conductors x (L_cut + pack lead) of
    18 AWG + fuse cold + XT30 pair, at the peak current."""
    D = L.PIGTAIL['drop']
    lead = next(c['length'] for c in L.CABLES if c['id'] == 'pack_lead')
    r_mohm = D['mohm_per_m'] * 2 * (l_cut + lead) / 1000.0 + L.PIGTAIL_FUSE['cold_mohm'] + D['xt30_mohm']
    return D['i_peak_a'] * r_mohm / 1000.0


def _pigtail_drop_limit(L):
    """Largest d_board (0.5 mm steps) whose rounded L_cut keeps the drop estimate <= the limit."""
    P = L.PIGTAIL
    d, best = 0.0, None
    while d <= 400.0:
        cut = math.ceil((P['base_len'] + d) / P['cut_round'] - 1e-9) * P['cut_round']
        if _pigtail_drop_v(L, cut) <= P['drop']['limit_v'] + 1e-12:
            best = d
        else:
            break
        d += 0.5
    return dict(d_board_max_mm=best if best is not None else -1.0)


def _pigtail_drop_row(L, smp, dl):
    """pigtail_drop: the assumed pad (PIGTAIL['pad'], Q2) must meet the G-W5 drop estimate, and STEPS[1] must carry
    the stop branch at the computed d_board limit (pads farther from W are never cut to length)."""
    P = L.PIGTAIL
    D = P['drop']
    d0 = _pigtail_face_out(L)['d_board_mm']
    cut0 = math.ceil((P['base_len'] + d0) / P['cut_round'] - 1e-9) * P['cut_round']
    v0 = _pigtail_drop_v(L, cut0)
    lim = dl['d_board_max_mm']
    st1 = next((s for s in L.STEPS if s['step'] == 1), {}).get('action', '')
    need = 'more than %d mm, stop: do not cut' % int(math.floor(lim + 1e-9))
    rows_ = [dict(pad=s['pad'], d_board_mm=s['d_board_mm'], l_cut_mm=s['l_cut_mm'],
                  drop_v=_r(_pigtail_drop_v(L, s['l_cut_mm']), 3),
                  verdict='ok' if s['d_board_mm'] <= lim + 1e-9 else 'stop at step 1 (G-W2)') for s in smp]
    pr = []
    if lim < 0:
        pr.append('no pad position meets the %.2f V limit' % D['limit_v'])
    if v0 > D['limit_v'] + 1e-12:
        pr.append('assumed pad: drop %.3f V > %.2f V at L_cut %.0f' % (v0, D['limit_v'], cut0))
    if need.lower() not in ' '.join(st1.split()).lower():
        pr.append('STEPS[1] lacks the stop branch "%s"' % need)
    return dict(id='pigtail_drop', kind='drop', cable='pigtail', model=D['src'], i_peak_a=D['i_peak_a'],
                limit_v=D['limit_v'], assumed_pad_l_cut_mm=cut0, assumed_pad_drop_v=_r(v0, 3),
                d_board_max_mm=lim, l_cut_max_ok_mm=math.ceil((P['base_len'] + lim) / P['cut_round'] - 1e-9)
                * P['cut_round'], samples=rows_, gate=D['gate'], estimate=True,
                status='fail' if pr else 'pass', **({'error': '; '.join(pr)} if pr else {}))


def check_lead_access(L, rows=None):
    """r7 C3 (SPEC-C3 3.2, BX-3/BX-11/BX-16): pigtail_xt30_mouth (face_out with the allowance, required_len),
    pigtail_range (cut rule over the credible pad range), pigtail_store (fold above the pack: fill with the shared
    leads, U-turn, pack/cap, side gaps info), lane_<cable>_<box> + lane_separation (taped lanes under the stack),
    run_lead_window (threading window along base_on) and pigtail_wrap_clear (keeper vs the lanes grown by form_tol, at
    the final pose and along keeper_in; the keeper solid when rows is given, else the bar + port finger stand-in)."""
    P, K = L.PIGTAIL, L.KEEPOUTS
    fmin = P['face_out_min']
    cab = {c['id']: c for c in L.CABLES}
    pig = cab['pigtail']
    out = []
    # 1. mouth
    fo = _pigtail_face_out(L)
    req = _pigtail_required_len(L)
    r = dict(id='pigtail_xt30_mouth', kind='reach', cable='pigtail', pad=dict(P['pad']), tie=dict(P['tie']),
             face_out_min=fmin, required_len_mm=req, estimate=True, **{k: _r(v, 1) for k, v in fo.items()})
    r['status'] = 'pass' if fo['face_out_mm'] >= fmin - 1e-9 else 'fail'
    if r['status'] == 'fail':
        r['error'] = 'XT30 face out %.1f < %.1f mm (L %.0f; required %s)' % (fo['face_out_mm'], fmin, fo['length_mm'],
                                                                           req)
    out.append(r)
    # 2. pad range with the cut rule
    smp = []
    for name, pad in _pigtail_pad_samples(L):
        d = _pigtail_face_out(L, pad)['d_board_mm']
        raw = P['base_len'] + d
        cut = math.ceil(raw / P['cut_round'] - 1e-9) * P['cut_round']
        smp.append(dict(pad=name, d_board_mm=_r(d, 1), l_raw=raw, l_cut_mm=cut,
                        face_out_raw_mm=_r(_pigtail_face_out(L, pad, raw)['face_out_mm'], 2),
                        face_out_cut_mm=_r(_pigtail_face_out(L, pad, cut)['face_out_mm'], 2)))
    worst = min(smp, key=lambda s: s['face_out_raw_mm'])
    lmax = max(s['l_cut_mm'] for s in smp)
    r = dict(id='pigtail_range', kind='reach', cable='pigtail', base_len=P['base_len'], samples=len(smp),
             worst_pad=worst['pad'], worst_face_out_mm=_r(worst['face_out_raw_mm'], 1),
             worst_face_out_cut_mm=_r(worst['face_out_cut_mm'], 1), l_cut_max_mm=lmax, stock_mm=P['stock_len'],
             rows=[{k: v for k, v in s.items() if k != 'l_raw'} for s in smp], face_out_min=fmin, estimate=True)
    pr = []
    if worst['face_out_raw_mm'] < fmin - 1e-9:
        pr.append('cut rule leaves %.1f mm out at %s (< %.1f)' % (worst['face_out_raw_mm'], worst['pad'], fmin))
    if lmax > P['stock_len'] + 1e-9:
        pr.append('L_cut %.0f > stock %.0f mm' % (lmax, P['stock_len']))
    # r7 fix-up (VERIFY-C3): the cut rule's reach holds over the whole pad range, but G-W5 does not; the samples
    #   past the drop limit are named here with the gate, and pigtail_drop (below) enforces the step-1 stop branch
    dl = _pigtail_drop_limit(L)
    r['drop_limited'] = [s['pad'] for s in smp if s['d_board_mm'] > dl['d_board_max_mm'] + 1e-9]
    if r['drop_limited']:
        r['gate'] = 'G-W2 / G-W5: pads past d_board %.1f mm stop at step 1 (pigtail_drop)' % dl['d_board_max_mm']
    out.append(dict(r, status='fail' if pr else 'pass', **({'error': '; '.join(pr)} if pr else {})))
    out.append(_pigtail_drop_row(L, smp, dl))
    # 3. store above the pack
    S = P['store']
    path_in, pts = _pigtail_path(L)
    zb, pb = box_bb(K[S['zone']]), box_bb(L.COTS['xt30_pair']['box'])
    fx = pb[0] if S.get('female_end') == '-x' else pb[1]          # r7 fix-up: the pigtail enters the female end
    d_fin = math.dist(pts[-1], (fx, (pb[2] + pb[3]) / 2, (pb[4] + pb[5]) / 2))
    stored = [s['l_cut_mm'] - s['l_raw'] + P['base_len'] - path_in - d_fin for s in smp]
    bound = P['base_len'] + P['cut_round'] - path_in - d_fin      # the 5 mm rounding bounds every pad (stricter)
    od, cores = P['od_range'][1], int(pig.get('cores', 2))
    shared = sum(cab[s]['length'] for s in S.get('shared') or () if s in cab)
    vz = _box_vol(zb, zb) - _box_vol(zb, pb)
    fill = (max(stored + [bound]) + shared) * cores * math.pi / 4 * od ** 2 / vz
    width = zb[3] - zb[2]
    uneed = 2 * S['bend_r_od'] * od + 2 * cores * od
    bay, pk, cap = box_bb(L.GRIP['bay']), box_bb(L.COTS['pack']['box']), box_bb(L.CAP['box'])
    inside = all(bay[2 * i] - 1e-9 <= zb[2 * i] and zb[2 * i + 1] <= bay[2 * i + 1] + 1e-9 for i in range(3))
    gaps = dict(y0=_r(pk[2] - bay[2], 2), y1=_r(bay[3] - pk[3], 2), x0=_r(pk[0] - bay[0], 2), x1=_r(bay[1] - pk[1], 2))
    pr = []
    if fill > S['fill_max'] + 1e-9:
        pr.append('store fill %.3f > %.2f' % (fill, S['fill_max']))
    if uneed > width + 1e-9:
        pr.append('U-turn needs %.1f > %.1f mm' % (uneed, width))
    if not inside:
        pr.append('%s not inside GRIP bay' % S['zone'])
    if pk[5] > zb[4] + 1e-9:
        pr.append('pack top %.1f above %s z0 %.1f' % (pk[5], S['zone'], zb[4]))
    if _box_vol(cap, zb) > 1e-9:
        pr.append('cap overlaps %s' % S['zone'])
    out.append(dict(id='pigtail_store', kind='store', cable='pigtail', zone=S['zone'], d_fin_mm=_r(d_fin, 1),
                    stored_mm=[_r(min(stored), 1), _r(max(stored), 1)], stored_bound_mm=_r(bound, 1),
                    shared=list(S.get('shared') or ()), shared_mm=shared, od_max=od, cores=cores,
                    zone_free_mm3=_r(vz, 0), fill=_r(fill, 3), fill_max=S['fill_max'], u_turn_need_mm=_r(uneed, 2),
                    u_turn_width_mm=_r(width, 2), u_turn_margin_mm=_r(width - uneed, 2),
                    free_section_mm=[_r(zb[1] - zb[0], 1), _r(width, 1), _r(pb[4] - zb[4], 1)],
                    pack_top=pk[5], zone_z0=zb[4], side_gaps_info=gaps,
                    loop_can_enter=sorted(k for k, v in gaps.items() if v >= od), estimate=True,
                    status='fail' if pr else 'pass', **({'error': '; '.join(pr)} if pr else {})))
    # r7 fix-up (VERIFY-C3): exits of the stored junction. Along the pair axis (x), the clear length beyond each end
    #   within the pair cross-section must hold the flexed exit bend (flex_r_od x od + od) plus the rigid solder-cup /
    #   heat-shrink length (unknown: lower bound 0, gate G-MP-PACK). Until the junction is re-posed this is OPEN: the
    #   row is marked with the gate (status 'info', never a plain pass); a fill / U-turn failure above still fails.
    ex = _pigtail_store_exits(L, rows, pb, od)
    srow = out[-1]
    srow['exits'] = ex
    if srow['status'] == 'pass' and ex['status'] != 'pass':
        srow.update(status='info', gate='G-MP-PACK (junction exits; re-pose open, VERIFY-C3)',
                    open='junction exits blocked: %s' % ex['error'])
    # 4. lanes + separation
    hmax = L.PI['x1203_z'][0] - L.FLOOR_Z[1]
    tol = P['form_tol']
    lanes = [(c, k) for c in L.CABLES for k in c.get('lanes') or []]
    for c, k in lanes:
        if k not in K:
            out.append(dict(id='lane_%s_%s' % (c['id'], k), kind='lane', status='fail', error='%s not in KEEPOUTS' % k))
            continue
        b = box_bb(K[k])
        w, h = min(b[1] - b[0], b[3] - b[2]), b[5] - b[4]
        nw, nh = int(c.get('cores', 1)) * c['od'], c['od'] + 0.5
        pr = [m for bad, m in ((w < nw - 1e-9, 'width %.2f < %.2f' % (w, nw)),
                               (h < nh - 1e-9, 'height %.2f < %.2f' % (h, nh)),
                               (h > hmax + 1e-9, 'height %.2f > %.2f under the X1203' % (h, hmax))) if bad]
        out.append(dict(id='lane_%s_%s' % (c['id'], k), kind='lane', cable=c['id'], box=k, width_mm=_r(w, 2),
                        need_width_mm=_r(nw, 2), height_mm=_r(h, 2), need_height_mm=_r(nh, 2), max_height_mm=_r(hmax, 2),
                        status='fail' if pr else 'pass', **({'error': '; '.join(pr)} if pr else {})))
    sep, near = [], None
    for c, k in lanes:
        if k not in K:
            continue
        for c2 in L.CABLES:
            if c2['id'] == c['id'] or min(c2['steps']) > max(c['steps']):
                continue
            for k2 in sorted(set(c2.get('via') or []) | set(c2.get('lanes') or [])):
                if k2 not in K:
                    continue
                g = _box_gap(box_bb(K[k]), box_bb(K[k2]))
                if near is None or g < near[0]:
                    near = (g, k, k2)
                if g < tol - 1e-9:
                    sep.append('%s (%s) to %s (%s): %.2f < %.1f' % (k, c['id'], k2, c2['id'], g, tol))
    out.append(dict(id='lane_separation', kind='lane', min_gap_mm=None if near is None else _r(near[0], 2),
                    nearest=None if near is None else [near[1], near[2]], form_tol=tol, problems=sep,
                    status='fail' if sep else 'pass', **({'error': '; '.join(sep)} if sep else {})))
    # 5. run-lead threading window along base_on
    run = cab['run_lead']
    bo = next((i for i in L.INSERTIONS if i['id'] == 'base_on'), None)
    rp, fh = L.base_run_passage(), L.FLOOR_HOLES['run_lead']
    ox, oy, at = None, None, None
    for a, b in zip(bo['path'], bo['path'][1:]) if bo else ():
        if abs(a[2]) > 1e-9 or abs(b[2]) > 1e-9:
            continue
        m = max(1, int(math.ceil(math.dist(a, b) / LEAD_WINDOW_STEP)))
        for j in range(m + 1):
            p = [a[i] + (b[i] - a[i]) * j / m for i in range(3)]
            x_ = min(rp['x'][1] + p[0], fh['x'][1]) - max(rp['x'][0] + p[0], fh['x'][0])
            y_ = min(rp['y'][1] + p[1], fh['y'][1]) - max(rp['y'][0] + p[1], fh['y'][0])
            if ox is None or x_ < ox:
                ox, at = x_, [_r(v, 2) for v in p]
            oy = y_ if oy is None else min(oy, y_)
    ny = int(run.get('cores', 1)) * run.get('od', 0.0)
    pr = []
    if ox is None:
        pr.append('base_on has no z-0 segment')
    else:
        if ox < L.RUN_WINDOW_MIN - 1e-9:
            pr.append('x overlap %.2f < RUN_WINDOW_MIN %.1f at base offset %s' % (ox, L.RUN_WINDOW_MIN, at))
        if oy < ny - 1e-9:
            pr.append('y overlap %.2f < %.2f' % (oy, ny))
    out.append(dict(id='run_lead_window', kind='thread', cable='run_lead', passage=rp, hole=dict(fh),
                    min_x_overlap_mm=None if ox is None else _r(ox, 2), at_offset=at, window_min=L.RUN_WINDOW_MIN,
                    min_y_overlap_mm=None if oy is None else _r(oy, 2), need_y_mm=_r(ny, 2),
                    status='fail' if pr else 'pass', **({'error': '; '.join(pr)} if pr else {})))
    # 6. keeper vs the pigtail lanes grown by form_tol in x
    ki = next((i for i in L.INSERTIONS if 'pi_keeper' in i['moving']), None)
    poses = [(0.0, 0.0, 0.0)] + (list(_path_points(ki['path'], LEAD_WINDOW_STEP)) if ki else [])
    grown = []
    for k in ['ko_pig_wrap'] + [x for x in pig.get('lanes') or [] if x != 'ko_pig_wrap']:
        b = box_bb(K[k])
        grown.append((k, (b[0] - tol, b[1] + tol) + tuple(b[2:])))
    shp = (rows or {}).get('pi_keeper', {}).get('shape') if rows else None
    worst = (0.0, None, None)
    if shp is not None:
        import manifold3d as m3
        km, kb = manifold_of(shp), bb_tuple(shp)
        for k, g in grown:
            gm = _bb_cube(m3, g)
            for p in poses:
                if not bb_overlap((kb[0] + p[0], kb[1] + p[0], kb[2] + p[1], kb[3] + p[1], kb[4] + p[2], kb[5] + p[2]),
                                  g, -1e-6):
                    continue
                v = (gm ^ km.translate(list(p))).volume()
                if v > worst[0]:
                    worst = (v, k, p)
    else:
        for k, g in grown:
            for p in poses:
                v = sum(_box_vol(g, (s[0] + p[0], s[1] + p[0], s[2] + p[1], s[3] + p[1], s[4] + p[2], s[5] + p[2]))
                        for s in _keeper_standin(L))
                if v > worst[0]:
                    worst = (v, k, p)
    st = 'pass' if worst[0] <= LEAD_CLEAR_TOL + 1e-12 else 'fail'
    out.append(dict(id='pigtail_wrap_clear', kind='clear', boxes=[k for k, _g in grown], grown_x_mm=tol,
                    keeper='solid' if shp is not None else 'stand-in (bar + kf3/kf4)', poses=len(poses),
                    max_volume_mm3=_r(worst[0], 3), worst_box=worst[1],
                    at_offset=None if worst[2] is None else [_r(x, 2) for x in worst[2]], tol_mm3=LEAD_CLEAR_TOL,
                    status=st, **({'error': 'keeper in the grown %s: %.3f mm3 > %.2f' % (worst[1], worst[0],
                                                                                        LEAD_CLEAR_TOL)}
                                  if st == 'fail' else {})))
    return out


def check_cable_stow(L):
    """r7 C2 (SPEC-C2 3.2-4): spare = length_max + pigtail - final-pose route estimate (no allowance deducted). Per stow
    box: sum(spare x pi/4 od^2 + junction) <= STOW_FILL x volume; joined to a route box of every naming cable
    (passage >= ROUTE_PASSAGE); no overlap with a COTS box present at the last step; >= STOW_BLOWER_MIN from the blower
    footprint in plan. Routed cables without a stow get an info row with their spare."""
    last = max(s['step'] for s in L.STEPS)
    est = {r['cable']: r.get('est_route_mm') for r in check_cable_routes(L) if r.get('est_route_mm') is not None}
    out, by_box = [], {}
    for c in L.CABLES:
        if not c.get('via') or c['id'] not in est:
            continue
        lmax = (c.get('length_range') or (None, c['length']))[1]
        spare = lmax + float(c.get('pigtail') or 0.0) - est[c['id']]
        if c.get('stow'):
            by_box.setdefault(c['stow'], []).append((c, spare))
        else:
            out.append(dict(kind='spare', cable=c['id'], spare_mm=_r(spare, 1), status='info',
                            home=STOW_INFO_HOME.get(c['id'], 'no named home (follow-up: give it a stow box)')))
    bl = box_bb(L.COTS['cooler']['features']['blower'])
    for k, cs in sorted(by_box.items()):
        probs = []
        if k not in L.KEEPOUTS:
            out.append(dict(kind='stow', stow=k, status='fail', error='stow box not in KEEPOUTS'))
            continue
        sb = box_bb(L.KEEPOUTS[k])
        vol = (sb[1] - sb[0]) * (sb[3] - sb[2]) * (sb[5] - sb[4])
        per = []
        for c, spare in cs:
            sec = math.pi / 4 * float(c['od']) ** 2
            per.append(dict(cable=c['id'], spare_mm=_r(spare, 1), od=c['od'], section_mm2=_r(sec, 2),
                            junction_mm3=c.get('junction_mm3', 0.0), demand_mm3=_r(spare * sec + c.get('junction_mm3', 0.0), 1)))
            joined = False
            for v in c['via']:
                b = box_bb(L.KEEPOUTS[v])
                ov = [min(sb[2 * i + 1], b[2 * i + 1]) - max(sb[2 * i], b[2 * i]) for i in range(3)]
                if min(ov) >= -1e-6 and sorted(ov)[1] >= ROUTE_PASSAGE - 1e-6:
                    joined = True
                    per[-1].setdefault('joined_to', v)
            if not joined:
                probs.append('%s not joined to a route box of %s' % (k, c['id']))
        demand = sum(p_['demand_mm3'] for p_ in per)
        cap = STOW_FILL * vol
        if demand > cap + 1e-6:
            probs.append('demand %.0f mm3 > capacity %.0f mm3 (%.2f x %.0f)' % (demand, cap, STOW_FILL, vol))
        cots_hits = [i for i in L.present_at(last) if (L.COTS.get(i) or {}).get('box') is not None
                     and _box_vol(sb, box_bb(L.COTS[i]['box'])) > 1e-6]
        if cots_hits:
            probs.append('overlaps COTS %s' % ', '.join(cots_hits))
        bd = math.hypot(max(bl[0] - sb[1], 0.0, sb[0] - bl[1]), max(bl[2] - sb[3], 0.0, sb[2] - bl[3]))
        if bd < STOW_BLOWER_MIN - 1e-9:
            probs.append('%.1f mm from the blower footprint in plan (< %.1f)' % (bd, STOW_BLOWER_MIN))
        out.append(dict(kind='stow', stow=k, cables=per, demand_mm3=_r(demand, 0), capacity_mm3=_r(cap, 0),
                        volume_mm3=_r(vol, 0), fill=STOW_FILL, cots_overlap=cots_hits, blower_mm=_r(bd, 1),
                        problems=probs, estimate=True, status='fail' if probs else 'pass',
                        **({'error': '; '.join(probs)} if probs else {})))
    return out


def header_pin_xy(L, n):
    """r7 C2: header pin n (1..40) centre (x, y): pin 1 at the gpio +X end - 1.27, odd row = PI['header_rows_y'][1]."""
    g = L.COTS['pi5']['features']['gpio']
    return (g['x'][1] - 1.27 - L.HDR_HOUSING['pitch'] * ((n - 1) // 2), L.PI['header_rows_y'][n % 2])


def header_housing_boxes(L, sec=None):
    """r7 C2: one box per HEADER_HOUSINGS entry (section `sec`, default the class maximum; length the class maximum)."""
    h = L.HDR_HOUSING
    s = max(h['sec']) if sec is None else sec
    z0 = h['seat_z']
    out = []
    for cab, typ, pins in L.HEADER_HOUSINGS:
        xy = [header_pin_xy(L, p) for p in pins]
        out.append(((cab, typ, tuple(pins)), (min(p[0] for p in xy) - s / 2, max(p[0] for p in xy) + s / 2,
                                              min(p[1] for p in xy) - s / 2, max(p[1] for p in xy) + s / 2,
                                              z0, z0 + max(h['length']))))
    return out


def check_header_housings(L, rows=None):
    """r7 C2 (SPEC-C2 3.2-5): (a) type '1', or '1x2' on 2 used adjacent pins; (b) gap >= min_gap to every COTS box
    present at the last step except pi5; (c) shape distance >= min_gap to every printed part present then (rows);
    (d) the part above the pi5 box top inside the cable's header-end route box; (e) no mutual overlap (class minimum
    section)."""
    h = L.HDR_HOUSING
    last = max(s['step'] for s in L.STEPS)
    pres = L.present_at(last)
    pitch, mg = h['pitch'], h['min_gap']
    pi_top = box_bb(L.COTS['pi5']['box'])[5]
    gb = box_bb(L.COTS['pi5']['features']['gpio'])
    boxes = header_housing_boxes(L)
    small = dict(header_housing_boxes(L, sec=min(h['sec'])))
    cab = {c['id']: c for c in L.CABLES}
    out = []
    for (cn, typ, pins), b in boxes:
        probs = []
        used = set((getattr(L, 'HDR_USED_PINS', {}) or {}).get(cn, ()))
        unused = [p for p in pins if p not in used]
        if unused:
            probs.append('covers unused pin(s) %s' % unused)
        if typ == '1':
            if len(pins) != 1:
                probs.append("type '1' with %d pins" % len(pins))
        elif typ == '1x2':
            ok = len(pins) == 2 and ((pins[0] % 2 == pins[1] % 2 and abs(pins[0] - pins[1]) == 2)
                                     or (min(pins) % 2 == 1 and abs(pins[0] - pins[1]) == 1))
            if not ok:
                probs.append("type '1x2' on non-adjacent pins %s" % (pins,))
        else:
            probs.append('illegal housing type %r (only 1 or 1x2)' % typ)
        cg = sorted(((_box_gap(_ko(L.COTS[i]['box']), list(b)), i) for i in pres if i != 'pi5'
                     and (L.COTS.get(i) or {}).get('box') is not None))
        cmin = cg[0] if cg else (None, None)
        if cmin[0] is not None and cmin[0] < mg - 1e-9:
            probs.append('gap %.2f to COTS %s < %.1f' % (cmin[0], cmin[1], mg))
        pg = []
        if rows is not None:
            hs = dc.box_solid(dict(x=(b[0], b[1]), y=(b[2], b[3]), z=(b[4], b[5])))
            for i in pres:
                if i not in getattr(L, 'PARTS', {}) or (rows.get(i) or {}).get('shape') is None:
                    continue
                if _box_gap(list(bb_tuple(rows[i]['shape'])), list(b)) > 3.0:
                    continue
                d = rows[i]['shape'].distance(hs)
                pg.append((d, i))
                if d < mg - 1e-9:
                    probs.append('distance %.2f to %s < %.1f' % (d, i, mg))
        pg.sort()
        c = cab.get(cn) or {}
        via = list(c.get('via') or [])
        hdr_box = min((v for v in via[:1] + via[-1:]), key=lambda v: _box_gap(_ko(L.KEEPOUTS[v]), list(gb))) \
            if via else None
        above = None
        if b[5] > pi_top + 1e-9:
            if hdr_box is None:
                probs.append('no route box for the part above the pi5 box')
            else:
                kb = box_bb(L.KEEPOUTS[hdr_box])
                ub = (b[0], b[1], b[2], b[3], max(b[4], pi_top), b[5])
                above = max(max(kb[2 * i] - ub[2 * i], ub[2 * i + 1] - kb[2 * i + 1], 0.0) for i in range(3))
                if above > 1e-6:
                    probs.append('top %.2f mm outside %s' % (above, hdr_box))
        sb = small[(cn, typ, tuple(pins))]
        ov = [k for k, o in small.items() if k != (cn, typ, tuple(pins)) and _box_vol(sb, o) > 1e-9]
        if ov:
            probs.append('overlaps housing(s) %s' % ['%s %s' % (k[0], k[2]) for k in ov])
        out.append(dict(cable=cn, type=typ, pins=list(pins), box=[_r(x, 2) for x in b],
                        cots_gap_mm=None if cmin[0] is None else _r(cmin[0], 2), cots_nearest=cmin[1],
                        printed_gap_mm=_r(pg[0][0], 2) if pg else None, printed_nearest=pg[0][1] if pg else None,
                        route_box=hdr_box, top_outside_mm=None if above is None else _r(above, 2),
                        problems=probs, estimate=True, status='fail' if probs else 'pass',
                        **({'error': '; '.join(probs)} if probs else {})))
    # r7 fix-up (VERIFY-C2 minor) rule (f): every used header pin of every cable has exactly one housing
    have = {}
    for cn, _t, pins in getattr(L, 'HEADER_HOUSINGS', []):
        for p in pins:
            have.setdefault(cn, []).append(p)
    for cn, used in sorted((getattr(L, 'HDR_USED_PINS', {}) or {}).items()):
        got = have.get(cn, [])
        miss = sorted(set(used) - set(got))
        dup = sorted({p for p in got if got.count(p) > 1})
        pr = (['used pin(s) %s without a housing' % miss] if miss else []) + (
            ['pin(s) %s in more than one housing' % dup] if dup else [])
        out.append(dict(cable=cn, kind='completeness', used=list(used), housed=sorted(got), status='fail' if pr else
                        'pass', **({'error': '; '.join(pr)} if pr else {})))
    return out


# ------------------------------------------------------------------------------------------- 4. bed fit
def check_bed(L, pid, shape_print):
    bb = shape_print.BoundingBox()
    dims = (bb.xlen, bb.ylen, bb.zlen)
    res = {}
    ok_all = True
    for bed, (BX, BY, BZ) in L.PRINT_BEDS.items():
        ok = dims[2] <= BZ and ((dims[0] <= BX and dims[1] <= BY) or (dims[0] <= BY and dims[1] <= BX))
        res[bed] = ok
        ok_all &= ok
    return dict(part=pid, print_bbox=[_r(x, 2) for x in dims], beds=res, status='pass' if ok_all else 'fail')


# ------------------------------------------------------------------------------------------- meshes
def mesh_of(shape, tol=MESH_TOL, ang=MESH_ANG):
    """(V float64 (n,3), F int (m,3)) with duplicate vertices merged (1e-5 grid)."""
    vs, ts = shape.tessellate(tol, ang)
    Vx = np.array([(v.x, v.y, v.z) for v in vs], dtype=np.float64).reshape(-1, 3)
    F = np.array(ts, dtype=np.int64).reshape(-1, 3)
    if len(Vx) == 0:
        return Vx, F
    key = np.round(Vx / 1e-5).astype(np.int64)
    _, idx, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    Vm = Vx[idx]
    Fm = inv.reshape(-1)[F]
    keep = (Fm[:, 0] != Fm[:, 1]) & (Fm[:, 1] != Fm[:, 2]) & (Fm[:, 0] != Fm[:, 2])
    return Vm, Fm[keep]


def manifold_of(shape):
    return manifold_of_tol(shape, MESH_TOL, MESH_ANG)


def manifold_of_tol(shape, tol, ang):
    import manifold3d as m3
    Vm, Fm = mesh_of(shape, tol, ang)
    if len(Fm) == 0:
        return None
    mesh = m3.Mesh(vert_properties=np.ascontiguousarray(Vm, np.float32), tri_verts=np.ascontiguousarray(Fm, np.uint32))
    man = m3.Manifold(mesh)
    if man.is_empty():
        mesh.merge()
        man = m3.Manifold(mesh)
    return None if man.is_empty() else man


# ------------------------------------------------------------------------------------------- 5. thin-wall screen
def _ray_hits(Vm, Fm, O, D, chunk=None, max_len=6.0):
    """Nearest positive hit distance along D (unit) for rays O, up to max_len (Moller-Trumbore, numpy). Rays are
    processed in spatial chunks against only the triangles near them. No hit within max_len -> inf."""
    v0, v1, v2 = Vm[Fm[:, 0]], Vm[Fm[:, 1]], Vm[Fm[:, 2]]
    e1, e2 = v1 - v0, v2 - v0
    tmin = np.minimum(np.minimum(v0, v1), v2)
    tmax = np.maximum(np.maximum(v0, v1), v2)
    out = np.full(len(O), np.inf)
    order = np.lexsort(np.floor(O / 6.0).T[::-1])
    chunk = chunk or 64
    for s in range(0, len(O), chunk):
        idx = order[s:s + chunk]
        lo = O[idx].min(axis=0) - max_len
        hi = O[idx].max(axis=0) + max_len
        sel = np.nonzero(np.all(tmax >= lo, axis=1) & np.all(tmin <= hi, axis=1))[0]
        if len(sel) == 0:
            continue
        for s2 in range(0, len(sel), 40000):
            tri = sel[s2:s2 + 40000]
            o, d = O[idx][:, None, :], D[idx][:, None, :]
            E1, E2, P0 = e1[tri][None], e2[tri][None], v0[tri][None]
            p = np.cross(d, E2)
            det = np.einsum('ijk,ijk->ij', p, np.broadcast_to(E1, p.shape))
            ok = np.abs(det) > 1e-12
            inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
            tv = o - P0
            u = np.einsum('ijk,ijk->ij', tv, p) * inv
            q = np.cross(tv, np.broadcast_to(E1, tv.shape))
            v = np.einsum('ijk,ijk->ij', np.broadcast_to(d, q.shape), q) * inv
            t = np.einsum('ijk,ijk->ij', np.broadcast_to(E2, q.shape), q) * inv
            hit = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9) & (t > 1e-4) & (t <= max_len)
            t = np.where(hit, t, np.inf).min(axis=1)
            out[idx] = np.minimum(out[idx], t)
    return out


def thin_wall(L, pid, shape, n=1500, loaded_boxes=(), seed=7):
    """Ray-thickness screen: sample points on the surface (area-weighted), shoot inward along -normal, thickness =
    first exit. Pass: area share under MIN_WALL <= 2 % and under MIN_FEATURE <= 0.5 %, and in loaded zones (bosses,
    posts, pads, hooks) the share under MIN_WALL_LOADED <= 2 %."""
    Vm, Fm = mesh_of(shape, tol=0.08, ang=0.3)
    if len(Fm) == 0:
        return dict(part=pid, status='fail', error='empty mesh')
    a, b, c = Vm[Fm[:, 0]], Vm[Fm[:, 1]], Vm[Fm[:, 2]]
    cr = np.cross(b - a, c - a)
    area = np.linalg.norm(cr, axis=1) / 2
    good = area > 1e-9
    nrm = np.zeros_like(cr)
    nrm[good] = cr[good] / (2 * area[good, None])
    if np.einsum('ij,ij->i', a, cr).sum() < 0:   # orientation: outward normals give positive signed volume
        nrm = -nrm
    rng = np.random.default_rng(seed)
    pick = rng.choice(len(Fm), size=n, p=area / area.sum())
    r1, r2 = rng.random(n), rng.random(n)
    flip = r1 + r2 > 1
    r1[flip], r2[flip] = 1 - r1[flip], 1 - r2[flip]
    P = a[pick] + r1[:, None] * (b[pick] - a[pick]) + r2[:, None] * (c[pick] - a[pick])
    N = nrm[pick]
    th_n = _ray_hits(Vm, Fm, P - N * 1e-3, -N)
    # wall thickness = max over a 30 deg cone of inward rays of (hit distance x cos tilt): a plate of thickness t gives
    # t for every ray, while ridges, knurl teeth and knife edges give the depth of the body behind them (so they are
    # not read as thin walls). th_n (the plain normal ray) is kept for the report.
    ref = np.where(np.abs(N[:, 0:1]) < 0.9, np.array([[1.0, 0, 0]]), np.array([[0, 1.0, 0]]))
    U = np.cross(N, ref)
    U /= np.linalg.norm(U, axis=1)[:, None]
    W = np.cross(N, U)
    th = np.where(np.isfinite(th_n), th_n, 6.0)      # nothing within 6 mm: at least 6 thick
    ct, st = math.cos(math.radians(30.0)), math.sin(math.radians(30.0))
    for k in range(6):
        ph = math.radians(60.0 * k)
        Dk = -N * ct + (U * math.cos(ph) + W * math.sin(ph)) * st
        dk = _ray_hits(Vm, Fm, P - N * 1e-3, Dk)
        th = np.maximum(th, np.where(np.isfinite(dk), dk, 6.0) * ct)
    fin = np.isfinite(th)
    th_f = th[fin]
    P_f = P[fin]
    mw, mf, ml = L.FDM['MIN_WALL'], L.FDM['MIN_FEATURE'], L.FDM['MIN_WALL_LOADED']
    declared = getattr(L, 'THIN_OK', {}).get(pid)          # layout-accepted exception: dict(min=, reason=)
    if declared:      # dict(min=wall threshold, loaded_min=optional loaded-zone threshold, reason=str)
        mw = max(mf, float(declared.get('min', mw)))
        ml = max(mf, float(declared.get('loaded_min', ml)))
    share = lambda m: float(m.sum()) / max(1, len(th_f))   # noqa: E731
    s_wall, s_feat = share(th_f < mw - 0.05), share(th_f < mf - 0.05)
    inl = np.zeros(len(P_f), bool)
    for bx in loaded_boxes:
        inl |= ((P_f[:, 0] >= bx[0]) & (P_f[:, 0] <= bx[1]) & (P_f[:, 1] >= bx[2]) & (P_f[:, 1] <= bx[3]) &
                (P_f[:, 2] >= bx[4]) & (P_f[:, 2] <= bx[5]))
    # r2 R3: no loaded samples -> None (not 0.0): an empty zone set is not evidence of adequate thickness
    s_load = float((th_f[inl] < ml - 0.05).sum()) / max(1, inl.sum()) if inl.any() else None
    order = np.argsort(th_f)[:6]
    ok = s_wall <= 0.02 and s_feat <= 0.005 and (s_load is None or s_load <= 0.02)
    thn = np.where(np.isfinite(th_n), th_n, 6.0)
    return dict(declared_exception=declared, wall_threshold=mw, normal_ray=dict(p1=_r(np.percentile(thn, 1)) if len(thn) else None,
                                share_below_min_wall=_r(float((thn < mw - 0.05).mean()) if len(thn) else 0.0, 4)),
                part=pid, samples=int(len(th_f)), min=_r(th_f.min()) if len(th_f) else None,
                p1=_r(np.percentile(th_f, 1)) if len(th_f) else None, p5=_r(np.percentile(th_f, 5)) if len(th_f) else None,
                share_below_min_wall=_r(s_wall, 4), share_below_min_feature=_r(s_feat, 4),
                loaded_samples=int(inl.sum()), share_loaded_below_1_6=_r(s_load, 4), loaded_zones=len(loaded_boxes),
                role='secondary screen (share-based); local thickness is gated by critical_features',
                thinnest=[dict(t=_r(th_f[i]), at=[_r(x, 1) for x in P_f[i]]) for i in order],
                below_min_wall=[dict(t=_r(th_f[i]), at=[_r(x, 2) for x in P_f[i]])      # r2 R3: for classification
                                for i in np.argsort(th_f)[:200] if th_f[i] < mw - 0.05],
                status='pass' if ok else 'fail',
                method='wall = max over a 30 deg cone of inward rays of hit x cos tilt (7 rays, tessellation 0.08 mm)')


def loaded_boxes(L, pid):
    """Zones where walls must be >= 1.6 (bosses, posts, pads, hooks, lips) for part pid."""
    Z = []
    if pid == 'panel':
        Z += [box_bb(b) for b in list(L.PANEL_BOSSES.values()) + list(L.PANEL_POSTS.values())]
        Z.append(box_bb(L.PANEL_TONGUE))
    if pid == 'tub':
        for p in L.RIGHT_WALL_PADS.values():
            Z.append((p['c'][0] - 6, p['c'][0] + 6, L.YR, p['y'][1], p['c'][1] - 6, p['c'][1] + 6))
        for (hx, hy) in L.PI['holes']:
            Z.append((hx - 3.5, hx + 3.5, hy - 3.5, hy + 3.5, L.T, L.PI_BOSS['z'][1]))
        Z.append(box_bb(L.LIP))
        for k, zb in snap_zones(L).items():          # Pi floor hooks (beam above the floor relief)
            if k.startswith('pih'):
                Z.append((zb[0], zb[1], zb[2], zb[3], L.T, L.PI_HOOK['catch_z'] - 0.3))
    if pid == 'hood':     # hook beams only: from just above the tooth top to the band underside
        for zb in clearance_zones(L)[:4]:
            b = zb[3]
            Z.append((b[0], b[1], b[2], b[3], L.HOOK['tooth_top_z'] + 0.3, b[5]))
        Z.append(box_bb(L.HOOD_RAIL['box']))         # groove lips (J2)
    # r5 (judge 3 s6.9): the collar insert bosses (tub) and the collar feet / pinch lugs (lens_collar) carry the lens
    for b in (getattr(L, 'TUB_INSERT_BOSSES', None) or {}).values() if pid == 'tub' else ():
        r = b['od'] / 2
        Z.append((b['x'][0], b['x'][1], b['c'][0] - r, b['c'][0] + r, b['c'][1] - r, b['c'][1] + r))
    if pid == 'lens_collar':
        C = L.COLLAR
        r = C['foot_d'] / 2
        Z += [(C['foot_x'][0], C['foot_x'][1], y - r, y + r, z - r, z + r) for y, z in C['feet'].values()]
        lg = C['lug']
        front = max(c['front_x'] for c in (L.collar_spec(n) for n in L.LENSES) if c)
        Z.append((lg['x'][0], front if lg['x'][1] is None else lg['x'][1], lg['y_out'], lg['bit_relief_y'],
                  lg['lower_z'][0], lg['upper_z'][1]))
    return Z


# ------------------------------------------------------------------------------------------- 6. straight driver
def check_driver(L, rows, screw_ids=None, audit_set_of=None, context=None):
    """Straight-driver audit. r2 (R3): screw_ids / audit_set_of(screw id) -> ids let the service-path check audit a
    screw in the SERVICE state (removal context) instead of its build step."""
    out = []
    D = L.DRIVER
    audit = audit_set_of or L.screw_audit_set
    for s in L.SCREWS:
        if screw_ids is not None and s['id'] not in screw_ids:
            continue
        hp, ax = s['head_point'], s['axis']
        bit = dc.cyl_along(D['bit_d'] / 2, -D['bit_len'], 0.0, hp, ax)
        handle = dc.cyl_along(D['handle_d'] / 2, -D['bit_len'] - D['handle_len'], -D['bit_len'], hp, ax)
        hits, stub = [], False
        for pid in audit(s['id']):
            r = rows.get(pid)
            if r is None or r.get('shape') is None:
                continue
            for nm, tool in (('bit', bit), ('handle', handle)):
                if not bb_overlap(bb_tuple(r['shape']), bb_tuple(tool)):
                    continue
                v, cs = common(r['shape'], tool)
                if v > VOL_TOL:
                    hits.append(dict(part=pid, tool=nm, volume_mm3=_r(v, 3), stub=bool(r.get('stub'))))
                    stub |= bool(r.get('stub'))
        clear = {}
        # r5 (brief choice 8): the audit applies to every kind; the head height comes from the screw's kind (PT / M3)
        hh = (getattr(L, 'M3', None) or L.PT)['head_h'] if s.get('kind', 'PT') == 'M3' else L.PT['head_h']
        bit_back = dc.cyl_along(D['bit_d'] / 2, -D['bit_len'], -hh - 0.1, hp, ax)   # behind the head
        for nm, tool in (('bit', bit_back), ('handle', handle)):   # nearest present solid (within 15 mm of the tool)
            tb = bb_tuple(tool)
            best = None
            for pid in audit(s['id']):
                r = rows.get(pid)
                if r is None or r.get('shape') is None or not bb_overlap(bb_tuple(r['shape']), tb, 15.0):
                    continue
                try:
                    d = r['shape'].distance(tool)
                except Exception:  # noqa: BLE001
                    continue
                if best is None or d < best[0]:
                    best = (d, pid)
            clear[nm] = None if best is None else dict(gap=_r(best[0], 2), part=best[1])
        st = 'pass' if not hits else ('stub' if all(h['stub'] for h in hits) else 'fail')
        out.append(dict(nearest=clear, screw=s['id'], step=s['step'], axis=list(ax), head_point=list(hp), bit=[D['bit_d'], D['bit_len']],
                        handle=[D['handle_d'], D['handle_len']], audit_set=audit(s['id']), hits=hits,
                        status=st, **({} if context is None else dict(context=context))))
    return out


# ------------------------------------------------------------------------------------------- 7. insertion sweeps
def snap_zones(L):
    z = {}
    for zb in clearance_zones(L)[:4]:
        z[zb[0].split()[2]] = zb[3]
    for h in L.PI_HOOKS:
        ax, v = h['face']
        if ax == 'x':
            z[h['id']] = (v - 4.0, v + 2.0, h['at'] - 5.0, h['at'] + 5.0, 0.0, 10.5)
        else:
            z[h['id']] = (h['at'] - 5.0, h['at'] + 5.0, v - 2.0, v + 4.0, 0.0, 10.5)
    if 'skirt_l' in L.PARTS and getattr(L, 'SKIRT_JOINT', None):   # r2 (R3): skb zones only while the skirts exist
        sj, bx = L.SKIRT_JOINT, L.BASE    # J5 skirt barbs (INTEGRATOR): the barb rides the groove floor for its last mm
        gz, xb = sj['groove_z'], sj['barb']['x']
        z['skb_l'] = (bx['x'][0] - 2.0, xb + 3.0, bx['y'][1] - 3.0, bx['y'][1] + 0.5, gz[0] - 0.5, gz[1] + 0.5)
        z['skb_r'] = (bx['x'][0] - 2.0, xb + 3.0, bx['y'][0] - 0.5, bx['y'][0] + 3.0, gz[0] - 0.5, gz[1] + 0.5)
    for k, zb in (getattr(L, 'SNAP_ZONES_EXTRA', None) or {}).items():   # r2: R1/R2 latch zones, dict id -> B() box
        z[k] = box_bb(zb)
    return z


def _path_points(path, step=2.0):
    pts = []
    for p0, p1 in zip(path[:-1], path[1:]):
        d = math.dist(p0, p1)
        n = max(1, int(math.ceil(d / step)))
        for i in range(n):
            f = i / n
            pts.append(tuple(p0[k] + (p1[k] - p0[k]) * f for k in range(3)))
    last = path[-2]
    d = math.dist(last, path[-1])
    for e in (1.0, 0.5):                                    # close approach before the final pose
        if d > e:
            pts.append(tuple(path[-1][k] + (last[k] - path[-1][k]) * e / d for k in range(3)))
    return pts


def reach_margin(L, length):
    """r7 (PLAN s2): the one lead-reach allowance, shared by mate_reach and lead_access: max(MATE_MARGIN,
    ROUTE_ALLOWANCE[0], ROUTE_ALLOWANCE[1] x length) (= SPEC-C3's allowance(L) with ROUTE_ALLOWANCE (10, 0.10))."""
    return max(getattr(L, 'MATE_MARGIN', ROUTE_ALLOWANCE[0]), ROUTE_ALLOWANCE[0], ROUTE_ALLOWANCE[1] * length)


def _ins_seq(L, ins_id):
    for n, i in enumerate(L.INSERTIONS):
        if i['id'] == ins_id:
            return (i['step'], float(n))
    return None


def plug_seq(L, mated):
    """r7 C1: sort key of a PLUGS `mated` moment: ('bench', s) -> (s, -1); ('before'|'after', J) -> J -+ 0.5."""
    kind, ref = mated
    if kind == 'bench':
        return (ref, -1.0)
    s = _ins_seq(L, ref)
    if s is None:
        return None
    return (s[0], s[1] + (-0.5 if kind == 'before' else 0.5))


def _plug_box(L, p):
    b = p.get('box')
    if b is None:
        return None
    return box_bb(L.KEEPOUTS[b]) if isinstance(b, str) else box_bb(b)


def _plug_name(p):
    return p['box'] if isinstance(p.get('box'), str) else p['id']


def carried_plugs(L, ins, n=None, removal=False):
    """r7 C1 (s4.1): rigid boxed PLUGS whose end moves with `ins` and that are mated before it. For a removal the
    service state has every plug mated: carried unless the plug is in rem['unplug']."""
    out = []
    for p in getattr(L, 'PLUGS', []) or []:
        if not (p.get('rigid') and p.get('box') and p['end'] in ins['moving']):
            continue
        if removal:
            if p['id'] not in (ins.get('unplug') or []):
                out.append(p)
            continue
        sq, si = plug_seq(L, p['mated']), (ins['step'], float(n))
        if sq is not None and sq < si:
            out.append(p)
    return out


def fixed_end_plugs(L, ins, n=None, removal=False, present=()):
    """r7 C1 (s4.1, second half of the defect class): for every cable with exactly one end moved by `ins`, the rigid
    boxed plug at the other (fixed) end stays a hard obstacle when it is mated at that moment (and its part present)."""
    out = []
    mv = set(ins['moving'])
    ends_of = getattr(L, 'CABLE_ENDS', None) or CABLE_ENDS
    for cab, ends in ends_of.items():
        moved = [e for e in ends if e in mv]
        if len(moved) != 1:
            continue
        fixed = [e for e in ends if e not in mv]
        for p in getattr(L, 'PLUGS', []) or []:
            if p['cable'] != cab or p['end'] not in fixed or not p.get('box') or p['end'] not in present:
                continue
            if removal:
                ok = p['id'] not in (ins.get('unplug') or [])
            else:
                sq = plug_seq(L, p['mated'])
                ok = sq is not None and sq < (ins['step'], float(n))
            if ok:
                out.append(p)
    return out


def _bb_cube(m3, b):
    return m3.Manifold.cube([b[1] - b[0], b[3] - b[2], b[5] - b[4]]).translate([b[0], b[2], b[4]])


def keepout_kind_of(L, k):
    """r7 C1: 'plug' (rigid connector body) or 'cable' (default) per layout.KEEPOUT_KIND."""
    return (getattr(L, 'KEEPOUT_KIND', None) or {}).get(k, 'cable')


def _own_via(L, cable_id):
    for c in L.CABLES:
        if c['id'] == cable_id:
            s = c.get('stow')      # r7 C2: `stow` is one KEEPOUTS id (a str), not a list
            return set(c.get('via') or []) | ({s} if isinstance(s, str) else set(s or []))
    return set()


def carry_boxes(L, ins, n=None, removal=False):
    """r7 (PLAN s2): the carried boxes of one insertion (or removal): rigid boxed PLUGS (kind 'plug') and C3 `riders`
    (kind 'rider', taped lead lanes). Each ignores its own cable's route and stow boxes and itself.
    -> [(name, bbox, kind, exclude set)]"""
    out = []
    for p in carried_plugs(L, ins, n, removal=removal):
        out.append((p['id'], _plug_box(L, p), 'plug', _own_via(L, p['cable']) | {_plug_name(p)}))
    for k in ins.get('riders') or []:
        if k not in L.KEEPOUTS:      # r7 C3: check_sweeps fails the row ('rider not in KEEPOUTS')
            continue
        own = set()
        for c in L.CABLES:
            if k in (c.get('via') or []):
                own |= _own_via(L, c['id'])
        out.append((k, box_bb(L.KEEPOUTS[k]), 'rider', own | {k}))
    return out


def _carried_sweep(L, m3, cboxes, pts, targets, kinds):
    """r7 (PLAN s2): ONE carried-box routine. cboxes: [(name, bb, kind 'plug'|'rider', exclude set)]; targets:
    [(id, manifold, bb)]; kinds: id -> 'solid' | 'plug' | 'cable'. kind 'plug' is hard against solids and 'plug'
    keep-outs and soft (<= CARRY_SOFT_MM, smallest extent of the overlap box) against 'cable' keep-outs; kind
    'rider' is hard against everything. Returns (worst hard hits {(name, o): (v, p, bbox)}, soft contacts)."""
    worst, soft = {}, {}
    for name, cb, ckind, excl in cboxes:
        cm = _bb_cube(m3, cb)
        for o, om, obb in targets:
            if o in excl or om is None:
                continue
            for p in pts:
                sbb = (cb[0] + p[0], cb[1] + p[0], cb[2] + p[1], cb[3] + p[1], cb[4] + p[2], cb[5] + p[2])
                if not bb_overlap(sbb, obb, -1e-6):
                    continue
                inter = cm.translate(list(p)) ^ om
                v = inter.volume()
                if v <= 1e-9:
                    continue
                ib = inter.bounding_box()
                if ckind == 'plug' and kinds.get(o) == 'cable':
                    pen = min(ib[3] - ib[0], ib[4] - ib[1], ib[5] - ib[2])
                    if pen > soft.get((name, o), (0.0,))[0]:
                        soft[(name, o)] = (pen, v, p)
                    continue
                if v > SWEEP_TOL and v > worst.get((name, o), (0.0,))[0]:
                    worst[(name, o)] = (v, p, [_r(x, 1) for x in ib])
    soft_rows = [dict(carried=n_, keepout=o, penetration_mm=_r(pen, 3), volume_mm3=_r(v, 2),
                      at_offset=[_r(x, 1) for x in p], limit_mm=CARRY_SOFT_MM, ok=pen <= CARRY_SOFT_MM + 1e-6)
                 for (n_, o), (pen, v, p) in sorted(soft.items())]
    return worst, soft_rows


def check_sweeps(L, rows, step_mm=2.0, only=None):
    import manifold3d as m3
    mates = mate_table(L)
    zones = snap_zones(L)
    man_cache = {}

    def man(i):
        if i not in man_cache:
            man_cache[i] = manifold_of(rows[i]['shape']) if rows.get(i, {}).get('shape') is not None else None
        return man_cache[i]

    out = []
    carried_final = {}      # r7: step -> [(name, final bbox)] of carried boxes already home (PLAN s2, C3's rule)
    for n, ins in enumerate(L.INSERTIONS):
        if only is not None and only not in ins['moving'] and only not in L.present_at(ins['step']):
            carried_final.setdefault(ins['step'], []).extend((nm, cb) for nm, cb, _k, _e in carry_boxes(L, ins, n))
            continue
        later = set()
        for o in L.INSERTIONS[n + 1:]:
            if o['step'] == ins['step']:
                later |= set(o['moving'])
        moving = [m for m in ins['moving'] if m in rows]
        obst = [i for i in L.present_at(ins['step']) if i not in ins['moving'] and i not in later
                and not i.startswith('s_') and i in rows]
        snap_boxes = [zb for k, zb in zones.items() if k in ins.get('snaps', [])]
        allowed_snap = [m3.Manifold.cube([zb[1] - zb[0], zb[3] - zb[2], zb[5] - zb[4]]).translate([zb[0], zb[2], zb[4]])
                        for k, zb in zones.items() if k in ins.get('snaps', [])]
        active_ko = []
        before = set(L.present_at(ins['step'] - 1))
        for cab in L.CABLES:      # a cable is in the body once one of its ends is (and it was plugged earlier)
            ends = set(cab.get('ends') or CABLE_ENDS.get(cab['id'], ()))
            if min(cab['steps']) < ins['step'] and (ends & before) and not (ends & set(ins['moving'])):
                active_ko += [k for k in cab['via'] if k not in ins.get('ignore', [])]
                if cab.get('stow') and cab['stow'] not in ins.get('ignore', []):   # r7 C2 (SPEC-C2 3.2-6c)
                    active_ko.append(cab['stow'])
        hits, worst, stub, err = [], {}, False, []
        pts = _path_points(ins['path'], step_mm)
        # r7 C1 (PLAN s2): fixed-end rigid plugs stay hard obstacles; carried boxes of earlier same-step insertions are
        #     final-pose obstacles; both are extra box targets for the part movers and for the carried boxes
        here = set(L.present_at(ins['step'])) - later
        fixed = fixed_end_plugs(L, ins, n, present=here)
        xbox = {}
        for p in fixed:
            nm = _plug_name(p)
            if nm not in active_ko:
                xbox[nm] = _plug_box(L, p)
        for nm, cb in carried_final.get(ins['step'], []):
            xbox['carried:' + nm] = cb
        hdr_on = []        # r7 C2 (SPEC-C2 3.2-6d): header housings are obstacles once their header plug is mated
        if getattr(L, 'HEADER_HOUSINGS', None) and 'pi5' in here and 'pi5' not in ins['moving']:
            hp = {p['cable']: p for p in getattr(L, 'PLUGS', []) or [] if p['end'] == 'pi5'}
            for (hc, _t, pins), hb in header_housing_boxes(L):
                sq = plug_seq(L, hp[hc]['mated']) if hc in hp else None
                if sq is not None and sq < (ins['step'], float(n)):
                    xbox['hdr:%s:%s' % (hc, '/'.join(str(x) for x in pins))] = hb
                    hdr_on.append('hdr:%s:%s' % (hc, '/'.join(str(x) for x in pins)))
        box_def = dict(L.KEEPOUTS)
        box_def.update({k: dict(x=(b[0], b[1]), y=(b[2], b[3]), z=(b[4], b[5])) for k, b in xbox.items()})
        xtargets = [(k, _bb_cube(m3, b), b) for k, b in sorted(xbox.items())]
        # r7 C2 (SPEC-C2 3.2-6b): a stow box filled during this insertion is an obstacle for the moving set (part
        #     movers and carried boxes) at path points no further than its waypoint from the final pose
        stw = [(k, float(f), _bb_cube(m3, box_bb(L.KEEPOUTS[k])), box_bb(L.KEEPOUTS[k]))
               for k, f in sorted((ins.get('stowed') or {}).items())]
        for mv in moving:
            for k, f, km, kb in stw:
                mm_ = man(mv)
                if mm_ is None:
                    continue
                mbb_ = bb_tuple(rows[mv]['shape'])
                for p in pts:
                    if math.sqrt(sum(x * x for x in p)) > f + 1e-9:
                        continue
                    sbb = (mbb_[0] + p[0], mbb_[1] + p[0], mbb_[2] + p[1], mbb_[3] + p[1], mbb_[4] + p[2], mbb_[5] + p[2])
                    if not bb_overlap(sbb, kb, -1e-6):
                        continue
                    v = (mm_.translate(list(p)) ^ km).volume()
                    if v > SWEEP_TOL and v > worst.get((mv, k), (0, None))[0]:
                        worst[(mv, k)] = (v, p, [])
        for mv in moving:
            mm = man(mv)
            if mm is None:
                err.append('no manifold mesh for %s (exact OCP fallback used)' % mv)
            mbb = bb_tuple(rows[mv]['shape'])
            targets = [(o, man(o), bb_tuple(rows[o]['shape'])) for o in obst]
            kind_skip = {o for o in obst if (mates.get(frozenset((mv, o))) or '').split(' ')[0] in
                         ('press', 'thread', 'interference')}
            targets += [(k, m3.Manifold.cube([b['x'][1] - b['x'][0], b['y'][1] - b['y'][0], b['z'][1] - b['z'][0]])
                         .translate([b['x'][0], b['y'][0], b['z'][0]]), box_bb(b))
                        for k, b in ((k, L.KEEPOUTS[k]) for k in sorted(set(active_ko)))]
            targets += xtargets
            for o, om, obb in targets:
                if o in kind_skip:
                    continue
                exact = mm is None or om is None
                if om is None and o in rows:
                    err.append('no manifold mesh for %s (exact OCP fallback used)' % o)
                for p in pts:
                    sbb = (mbb[0] + p[0], mbb[1] + p[0], mbb[2] + p[1], mbb[3] + p[1], mbb[4] + p[2], mbb[5] + p[2])
                    if not bb_overlap(sbb, obb, -1e-6):
                        continue
                    if exact:
                        osh = rows[o]['shape'] if o in rows else dc.box_solid(box_def[o])
                        inter = rows[mv]['shape'].translate(V(*p)).intersect(osh)
                        try:
                            v0 = inter.Volume()
                        except Exception:  # noqa: BLE001 - null result = no overlap
                            v0 = 0.0
                        if v0 > 1e-9:
                            for zb in snap_boxes:
                                try:
                                    inter = inter.cut(cq.Solid.makeBox(zb[1] - zb[0], zb[3] - zb[2], zb[5] - zb[4],
                                                                       V(zb[0], zb[2], zb[4])))
                                except Exception:  # noqa: BLE001
                                    break
                        try:
                            v = inter.Volume() if v0 > 1e-9 else 0.0
                        except Exception:  # noqa: BLE001
                            v = 0.0
                        ibb = list(bb_tuple(inter)) if v > 1e-9 else []
                    else:
                        inter = mm.translate(list(p)) ^ om
                        for z in allowed_snap:
                            inter = inter - z
                        v = inter.volume()
                        ibb = list(inter.bounding_box()) if v > 1e-9 else []
                    if v > SWEEP_TOL:
                        key = (mv, o)
                        if v > worst.get(key, (0, None))[0]:
                            worst[key] = (v, p, [_r(x, 1) for x in ibb])
                        stub |= bool(rows[mv].get('stub') or (o in rows and rows[o].get('stub')))
        for (mv, o), (v, p, bbx) in worst.items():
            hits.append(dict(moving=mv, obstacle=o, max_volume_mm3=_r(v, 2), at_offset=[_r(x, 1) for x in p],
                             where=bbx, stub=bool(rows[mv].get('stub') or (o in rows and rows[o].get('stub')))))
        # r7 C1 (PLAN s2, SPEC-C1 4.1): the carried boxes (rigid plugs mated earlier whose end moves; C3 riders)
        cbx = carry_boxes(L, ins, n)
        err += ['rider not in KEEPOUTS: %s' % k for k in ins.get('riders') or [] if k not in L.KEEPOUTS]   # r7 C3
        ctargets =[(o, man(o), bb_tuple(rows[o]['shape'])) for o in obst]
        ctargets += [(k, _bb_cube(m3, box_bb(L.KEEPOUTS[k])), box_bb(L.KEEPOUTS[k])) for k in sorted(set(active_ko))]
        ctargets += xtargets
        kinds = {o: 'solid' for o in obst}
        kinds.update({k: keepout_kind_of(L, k) for k in set(active_ko)})
        kinds.update({k: 'plug' for k in xbox})
        cworst, soft_rows = _carried_sweep(L, m3, cbx, pts, ctargets, kinds)
        for k, f, km, kb in stw:       # r7 C2: the stow box against the carried boxes from its waypoint on
            sw_, ss_ = _carried_sweep(L, m3, cbx, [p for p in pts if math.sqrt(sum(x * x for x in p)) <= f + 1e-9],
                                      [(k, km, kb)], {k: keepout_kind_of(L, k)})
            cworst.update(sw_)
            soft_rows += ss_
        for (nm, o), (v, p, bbx) in cworst.items():
            hits.append(dict(moving=nm, obstacle=o, max_volume_mm3=_r(v, 2), at_offset=[_r(x, 1) for x in p],
                             where=bbx, carried=True, stub=bool(o in rows and rows[o].get('stub'))))
        for s in soft_rows:
            if not s['ok']:
                hits.append(dict(moving=s['carried'], obstacle=s['keepout'], max_volume_mm3=s['volume_mm3'],
                                 at_offset=s['at_offset'], carried=True, stub=False,
                                 error='soft contact %.2f mm > CARRY_SOFT_MM %.1f' % (s['penetration_mm'],
                                                                                     CARRY_SOFT_MM)))
        carried_final.setdefault(ins['step'], []).extend((nm, cb) for nm, cb, _k, _e in cbx)
        fx = []
        for p in fixed:
            nm = _plug_name(p)
            vs = [h['max_volume_mm3'] for h in hits if h['obstacle'] == nm]
            fx.append(dict(plug=p['id'], keepout=nm, max_volume_mm3=max(vs) if vs else 0.0))
        hard_err = [e for e in err if 'fallback' not in e]
        st = 'pass' if not hits and not hard_err else ('stub' if hits and all(h['stub'] for h in hits) and not hard_err
                                                      else 'fail')
        out.append(dict(insertion=ins['id'], step=ins['step'], moving=ins['moving'], obstacles=obst,
                        keepouts=sorted(set(active_ko)), snaps=ins.get('snaps', []), positions=len(pts), hits=hits,
                        carried=[c[0] for c in cbx], soft_contacts=[s for s in soft_rows if s['ok']],
                        fixed_end_obstacles=fx, stowed=list(ins.get('stowed') or []), header_housings=hdr_on,
                        riders=list(ins.get('riders') or []),
                        errors=err, status=st, method='manifold3d mesh boolean, tessellation 0.05 mm, tol %.1f mm3'
                        % SWEEP_TOL))
    return out


# ------------------------------------------------------------------------------------------- 7b. mate paths (r7 C1)
def _ins_index(L, ins_id):
    return next((n for n, i in enumerate(L.INSERTIONS) if i['id'] == ins_id), None)


def _moment(L, rows, after=None, state=None, screws=True):
    """r7 C1: (ids present with a shape, step, removal or None) at a moment: after=<insertion id> (its step, its movers
    home, later same-step movers absent) or state='service:<REMOVALS id>' (service state, moving set still in place)."""
    if state:
        rem = next(r for r in registry(L, 'REMOVALS') if r['id'] == state.split(':', 1)[1])
        ids = service_context(L, rows, rem) + [m for m in rem['moving'] if m in rows]
        step = max(s['step'] for s in L.STEPS)
    else:
        n = _ins_index(L, after)
        ins = L.INSERTIONS[n]
        step = ins['step']
        later = set()
        for o in L.INSERTIONS[n + 1:]:
            if o['step'] == step:
                later |= set(o['moving'])
        ids = [i for i in L.present_at(step) if i not in later]
        rem = None
    ids = [i for i in ids if i in rows and rows[i].get('shape') is not None and (screws or not i.startswith('s_'))]
    return ids, step, rem


def _moment_keepouts(L, ids, step):
    """Cable keep-outs active at a moment: cables plugged by then with an end present."""
    out = set()
    for cab in L.CABLES:
        ends = set(cab.get('ends') or CABLE_ENDS.get(cab['id'], ()))
        if min(cab['steps']) <= step and (ends & set(ids)):
            out |= set(cab['via'])
    return out


def _box_vol(a, b):
    d = [min(a[2 * i + 1], b[2 * i + 1]) - max(a[2 * i], b[2 * i]) for i in range(3)]
    return d[0] * d[1] * d[2] if min(d) > 0 else 0.0


def _solid_hits(m3, man, rows, ids, cb, tol=SWEEP_TOL):
    cm, out = _bb_cube(m3, cb), []
    for o in ids:
        if not bb_overlap(cb, bb_tuple(rows[o]['shape']), -1e-6):
            continue
        om = man(o)
        if om is None:
            out.append(dict(obstacle=o, error='no manifold mesh'))
            continue
        v = (cm ^ om).volume()
        if v > tol:
            out.append(dict(obstacle=o, volume_mm3=_r(v, 2)))
    return out


def check_mate_paths(L, rows, sweep_rows=None, step_mm=1.0):
    """r7 C1 (SPEC-C1 4.2 + Plan edits P1-4/P1-6/P1-9): plug_in (in-situ plug paths), access (hand/tool corridors)
    and coverage (PLUGS per cable end, carried lists, ACCESS ignores). Pass = 0 mm3 (SWEEP_TOL) everywhere."""
    import manifold3d as m3
    cache = {}

    def man(i):
        if i not in cache:
            cache[i] = manifold_of(rows[i]['shape'])
        return cache[i]

    plugs = {p['id']: p for p in getattr(L, 'PLUGS', []) or []}
    out = []
    for p in plugs.values():                                   # 1. plug_in
        if not p.get('path'):
            continue
        kind, ref = p['mated']
        ids, step, _ = _moment(L, rows, after=ref if kind == 'after' else None, screws=False) if kind == 'after' \
            else (None, None, None)
        if ids is None:
            out.append(dict(kind='plug_in', id=p['id'], status='fail', error='in-situ path needs mated (after, J)'))
            continue
        body, head, stroke = _plug_box(L, p), (box_bb(p['head']) if p.get('head') else None), p.get('stroke', 0.0)
        own = _own_via(L, p['cable'])
        hard_ko = sorted(k for k in _moment_keepouts(L, ids, step) if keepout_kind_of(L, k) == 'plug' and k not in own)
        pts = _path_points(p['path'], step_mm) + [tuple(p['path'][-1])]
        worst = {}
        for nm, bb in (('body', body), ('head', head)):
            if bb is None:
                continue
            for q in pts:
                sb = (bb[0] + q[0], bb[1] + q[0], bb[2] + q[1], bb[3] + q[1], bb[4] + q[2], bb[5] + q[2])
                mating = nm == 'head' and math.dist(q, p['path'][-1]) <= stroke + 1e-9
                tids = [o for o in ids if not (mating and o == p['end'])]
                for h in _solid_hits(m3, man, rows, tids, sb):
                    if h.get('volume_mm3', 0) > worst.get((nm, h['obstacle']), (0,))[0] or 'error' in h:
                        worst[(nm, h['obstacle'])] = (h.get('volume_mm3', 0), q, h.get('error'))
                for k in hard_ko:
                    v = _box_vol(sb, box_bb(L.KEEPOUTS[k]))
                    if v > VOL_TOL and v > worst.get((nm, k), (0,))[0]:
                        worst[(nm, k)] = (_r(v, 2), q, None)
        hits = [dict(part=nm, obstacle=o, max_volume_mm3=v, at_offset=[_r(x, 1) for x in q], error=e)
                for (nm, o), (v, q, e) in sorted(worst.items())]
        eb = bb_tuple(rows[p['end']]['shape']) if p['end'] in rows else None
        out.append(dict(kind='plug_in', id=p['id'], cable=p['cable'], end=p['end'], moment=list(p['mated']),
                        path=[list(x) for x in p['path']], stroke=stroke, positions=len(pts) * (2 if head else 1),
                        obstacles=ids, hard_keepouts=hard_ko, hits=hits,
                        final_gap_to_end=None if eb is None else _r(_box_gap(body, eb), 3),
                        head_top_lowest=None if head is None else _r(head[5] + min(q[2] for q in p['path']), 2),
                        status='fail' if hits else 'pass'))
    out += _mate_access_rows(L, rows, plugs, man, m3)          # 2. access
    out += _mate_coverage_rows(L, plugs, sweep_rows)           # 3. coverage
    return out


def _mate_access_rows(L, rows, plugs, man, m3):
    """r7 C1: every ACCESS corridor is empty at its moment (parts present then + active cable keep-outs - ignore)."""
    out = []
    fmm = getattr(L, 'FINGERTIP_MM', 9.0)
    for a in getattr(L, 'ACCESS', []) or []:
        row = dict(kind='access', id=a['id'], moment=a.get('after') or a.get('state'), tool=a.get('tool', ''),
                   ignore=list(a.get('ignore') or []))
        try:
            ids, step, _ = _moment(L, rows, after=a.get('after'), state=a.get('state'))
        except (StopIteration, TypeError, IndexError):
            out.append(dict(row, status='fail', error='unknown moment'))
            continue
        boxes = [box_bb(b) for b in (a.get('boxes') or [a['box']])]
        if a.get('push_of'):
            p = plugs.get(a['push_of'])
            if p is None or _plug_box(L, p) is None:
                out.append(dict(row, status='fail', error='push_of plug %s missing' % a['push_of']))
                continue
            z1 = _plug_box(L, p)[4] - p.get('stroke', 0.0)
            boxes = [(b[0], b[1], b[2], b[3], b[4], z1) for b in boxes]
            row['push_height_mm'] = _r(z1 - boxes[0][4], 2)
            row['fingertip_mm'] = fmm
            row['push_method'] = 'fingertip' if z1 - boxes[0][4] >= fmm - 1e-9 else 'push_stick'
        kos = sorted(k for k in _moment_keepouts(L, ids, step) if k not in (a.get('ignore') or []))
        hits = []
        for b in boxes:
            if b[5] - b[4] <= 0:
                hits.append(dict(obstacle='(no room)', error='corridor height <= 0'))
                continue
            hits += _solid_hits(m3, man, rows, ids, b)
            hits += [dict(obstacle=k, volume_mm3=_r(_box_vol(b, box_bb(L.KEEPOUTS[k])), 2)) for k in kos
                     if _box_vol(b, box_bb(L.KEEPOUTS[k])) > VOL_TOL]
        out.append(dict(row, boxes=[[_r(x, 2) for x in b] for b in boxes], present=ids, keepouts=kos, hits=hits,
                        status='fail' if hits else 'pass'))
    return out


def _mate_coverage_rows(L, plugs, sweep_rows=None):
    """r7 C1: one PLUGS entry per CABLE_ENDS (cable, end); boxes and mate moments exist; every carried plug shows in
    its insertion's sweeps row; every ACCESS ignore has a sequence reason (P1-9)."""
    ce = getattr(L, 'CABLE_ENDS', None) or CABLE_ENDS
    pairs = [(c, e) for c, ends in ce.items() for e in ends]
    have = {}
    for p in plugs.values():
        have.setdefault((p['cable'], p['end']), []).append(p['id'])
    gaps = ['%s/%s' % ce_ for ce_ in pairs if len(have.get(ce_, [])) != 1]
    extra = ['%s (%s/%s)' % (i, c, e) for (c, e), v in have.items() if (c, e) not in pairs for i in v]
    ins_ids = {i['id'] for i in L.INSERTIONS}
    bad = []
    for p in plugs.values():
        if isinstance(p.get('box'), str) and p['box'] not in L.KEEPOUTS:
            bad.append('%s: box %s not in KEEPOUTS' % (p['id'], p['box']))
        k, ref = p['mated']
        if (k == 'bench' and ref not in {s['step'] for s in L.STEPS}) or (k != 'bench' and ref not in ins_ids) \
                or k not in ('bench', 'before', 'after'):
            bad.append('%s: mated %r unknown' % (p['id'], p['mated']))
    out = [dict(kind='coverage', id='plugs_per_cable_end', n=len(pairs), covered=len(pairs) - len(gaps), gaps=gaps,
                extra=extra, errors=bad, status='fail' if (gaps or extra or bad) else 'pass')]
    srow = {r['insertion']: r for r in (sweep_rows or []) if 'insertion' in r}
    miss = []
    for m, ins in enumerate(L.INSERTIONS):
        names = srow[ins['id']].get('carried', []) if ins['id'] in srow else [c[0] for c in carry_boxes(L, ins, m)]
        for p in plugs.values():
            if p.get('rigid') and p.get('box') and p['end'] in ins['moving']:
                sq = plug_seq(L, p['mated'])
                if sq is not None and sq < (ins['step'], float(m)) and p['id'] not in names:
                    miss.append('%s not carried by %s' % (p['id'], ins['id']))
    out.append(dict(kind='coverage', id='carried_lists', source='sweeps rows' if srow else 'carry_boxes',
                    missing=miss, status='fail' if miss else 'pass'))
    ign = []
    rems = {r['id']: r for r in registry(L, 'REMOVALS')}
    for a in getattr(L, 'ACCESS', []) or []:
        st = a.get('state')
        unplug = set((rems.get(st.split(':', 1)[1]) or {}).get('unplug') or []) if st else set()
        for k in a.get('ignore') or []:
            if k == a.get('dest'):
                continue
            ok = False
            for c in L.CABLES:
                if k not in (c.get('via') or []):
                    continue
                for p in plugs.values():
                    if p['cable'] == c['id'] and ((not st and tuple(p['mated']) == ('after', a.get('after')))
                                                  or (st and p['id'] in unplug)):
                        ok = True
            if not ok:
                ign.append('%s ignores %s without a sequence reason' % (a['id'], k))
    out.append(dict(kind='coverage', id='access_ignores', n=sum(len(a.get('ignore') or []) for a in
                                                                getattr(L, 'ACCESS', []) or []),
                    errors=ign, status='fail' if ign else 'pass'))
    out.append(_mate_pose_coverage_row(L, plugs))
    return out


def _mate_pose_coverage_row(L, plugs):
    """r7 (PLAN s2, Plan edit P1-5, lands with SPEC-C2): for every insertion J and every cable with exactly one end E
    moved by J, if the plug at E and the plug (or inline junction) at the other end are both mated before J, a
    MATE_POSES row for (cable, J) must exist. Rows whose both ends move are 'info' (not required). Every MATE_POSES
    row names an existing PLUGS id of its cable (or inline_of=<its cable>)."""
    ce = getattr(L, 'CABLE_ENDS', None) or CABLE_ENDS
    mps = getattr(L, 'MATE_POSES', None) or []
    have = {(m.get('cable'), m.get('insertion')) for m in mps}
    need, missing, info = [], [], []
    for n, ins in enumerate(L.INSERTIONS):
        mv, si = set(ins['moving']), (ins['step'], float(n))
        for cab, ends in ce.items():
            moved = [e for e in ends if e in mv]
            if len(moved) == 2:
                info.append('%s/%s' % (cab, ins['id']))
                continue
            if len(moved) != 1:
                continue
            other = [e for e in ends if e not in mv]
            pe = [p for p in plugs.values() if p['cable'] == cab and p['end'] == moved[0]]
            po = [p for p in plugs.values() if p['cable'] == cab and other and p['end'] == other[0]]
            seqs = [plug_seq(L, p['mated']) for p in pe + po]
            if pe and po and all(s is not None and s < si for s in seqs):
                need.append('%s/%s' % (cab, ins['id']))
                if (cab, ins['id']) not in have:
                    missing.append('%s/%s' % (cab, ins['id']))
    bad = []
    for m in mps:
        if m.get('plug'):
            p = plugs.get(m['plug'])
            if p is None or p['cable'] != m.get('cable'):
                bad.append('%s: plug %s is not a PLUGS id of %s' % (m.get('id'), m['plug'], m.get('cable')))
        elif m.get('inline_of') != m.get('cable'):
            bad.append('%s: names neither a plug nor inline_of=%s' % (m.get('id'), m.get('cable')))
    return dict(kind='coverage', id='mate_poses', required=need, missing=missing, both_moving=sorted(set(info)),
                errors=bad, status='fail' if (missing or bad) else 'pass',
                **({'error': 'no MATE_POSES row for ' + ', '.join(missing)} if missing else {}))


# ------------------------------------------------------------------------------------------- 8. mass and CoM
def mass_com(L, rows, lens_row):
    """Total mass and CoM; printed = volume x density x infill; COTS = listed masses at the proxy centroid."""
    tm, mx = 0.0, np.zeros(3)
    items = []
    for i, r in rows.items():
        if i == 'lens':
            continue
        if r.get('shape') is None:
            continue
        sh = r['shape']
        if r['kind'] == 'printed':
            m = L.mass_g(sh.Volume(), i)
        else:
            m = r.get('mass') or 0.0
        c = r.get('com') or (lambda cc: (cc.x, cc.y, cc.z))(cq.Shape.centerOfMass(sh))
        tm += m
        mx += m * np.array(c)
        items.append(dict(id=i, mass_g=_r(m, 2), com=[_r(x, 1) for x in c], stub=bool(r.get('stub'))))
    lm, lc = lens_row['mass'], lens_row['com']
    tm += lm
    mx += lm * np.array(lc)
    items.append(dict(id='lens', mass_g=lm, com=[_r(x, 1) for x in lc], name=lens_row['name']))
    com = mx / tm
    return dict(total_g=_r(tm, 1), com=[_r(x, 2) for x in com], lens=lens_row['name'],
                com_ahead_of_grip_axis=_r(com[0] - L.GRIP['axis_x'], 2),
                com_above_grip_top=_r(com[2] - L.GRIP['top_z'], 2), items=items,
                note='cables and solder not included; COTS masses are listing/estimate values at proxy centroids')


# ------------------------------------------------------------------------------------------- FIXER P1: groove width
def _raster_faces(faces, px):
    """Rasterise planar +Y faces (x, z) at px mm/pixel; returns a bool image (PIL polygon fill of the triangles)."""
    from PIL import Image, ImageDraw
    tri = []
    for f in faces:
        vs, ts = f.tessellate(0.02, 0.2)
        P = [(v.x, v.z) for v in vs]
        tri += [[P[i] for i in t] for t in ts]
    if not tri:
        return None
    xs = [p[0] for t in tri for p in t]
    zs = [p[1] for t in tri for p in t]
    x0, z0 = min(xs) - 1.0, min(zs) - 1.0
    W, H = int((max(xs) - x0 + 1.0) / px) + 1, int((max(zs) - z0 + 1.0) / px) + 1
    im = Image.new('1', (W, H), 0)
    dr = ImageDraw.Draw(im)
    for t in tri:
        dr.polygon([((p[0] - x0) / px, (p[1] - z0) / px) for p in t], fill=1)
    return np.array(im, dtype=bool)


def _morph(img, r_px, op):
    pad = r_px + 2
    a = np.pad(img, pad)
    out = np.ones_like(a) if op == 'erode' else np.zeros_like(a)
    for dy in range(-r_px, r_px + 1):
        for dx in range(-r_px, r_px + 1):
            if dx * dx + dy * dy > r_px * r_px:
                continue
            sh = np.roll(np.roll(a, dy, 0), dx, 1)
            out = (out & sh) if op == 'erode' else (out | sh)
    return out[pad:-pad, pad:-pad]


def check_engrave(L, px=0.04):
    """Groove width of every engraved glyph/stroke at the face plane: share of its area removed by a morphological
    opening with a disk of dia ENGRAVE_MIN_STROKE (= area narrower than the stroke). Pass: share <= ENGRAVE_MAX_THIN_SHARE
    for every glyph. Sectioned on the cutter solids (prisms normal to the face, so the bed-layer outline is the same)."""
    E, F = L.ENGRAVE, L.FDM
    mn, lim = F['ENGRAVE_MIN_STROKE'], F['ENGRAVE_MAX_THIN_SHARE']
    r_px = max(1, int(round(mn / 2 / px)))
    out = []
    for it in E['items']:
        worst, n = 0.0, 0
        for so in dc.engrave([it], face_y=E['face_y']):
            fs = [f for f in so.Faces() if abs(abs(f.normalAt().y) - 1.0) < 1e-6]
            if not fs:
                continue
            ytop = max(f.Center().y for f in fs)
            img = _raster_faces([f for f in fs if f.Center().y > ytop - 0.01], px)
            if img is None or not img.any():
                continue
            opened = _morph(_morph(img, r_px, 'erode'), r_px, 'dilate') & img
            worst = max(worst, 1.0 - opened.sum() / img.sum())
            n += 1
        out.append(dict(item=it['id'], kind=it['kind'], glyphs=n, worst_thin_share=_r(worst, 3), min_stroke=mn,
                        limit=lim, status='pass' if n and worst <= lim else 'fail'))
    return out


# ------------------------------------------------------------------------------------------- FIXER P5: PT bosses
def _own_copy(x):
    sh = x.val() if hasattr(x, 'val') else x
    return sh.copy()


def check_bosses(L, rows):
    """Solid-measured PT boss geometry along every SCREWS axis (local exact intersect, fine mesh, rays): pilot dia
    (2.5 +-0.05), pilot depth from the boss entry (>= engage + tip reserve), wall round the pilot (>= (boss_od_min -
    pilot)/2 = 2.25) and material under the head on the counterbore shoulder (>= MIN_WALL_LOADED 1.6).
    r5 (brief choice 8): kind PT only; the M3 screws (heat-set inserts) are measured by check_inserts."""
    PT, out = L.PT, []
    for s in L.SCREWS:
        if s.get('kind', 'PT') != 'PT':
            continue
        ax = np.array(s['axis'], float)
        hp, tp = np.array(s['head_point'], float), np.array(s['tip'], float)
        into = s['into'].split()[0]
        ref = np.array([1.0, 0, 0]) if abs(ax[0]) < 0.9 else np.array([0, 1.0, 0])
        u = np.cross(ax, ref); u /= np.linalg.norm(u)
        w = np.cross(ax, u)
        lo, hi = np.minimum(hp, tp + ax * 3) - 6, np.maximum(hp, tp + ax * 3) + 6
        row = dict(screw=s['id'], into=into, head_part=s['head_part'])
        try:
            box = cq.Solid.makeBox(*(hi - lo), V(*lo))
            loc = _own_copy(rows[into]['shape']).intersect(box)   # copy: a fine mesh on shared faces broke manifold_of
            Vm, Fm = mesh_of(loc, tol=0.01, ang=0.1)
            dirs = np.array([u * math.cos(a) + w * math.sin(a) for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)])
            # entry: rays parallel to the axis at r 2.0 (inside the boss, outside the pilot)
            O = np.array([hp + d * 2.0 for d in dirs])
            entry = float(np.nanmin(_ray_hits(Vm, Fm, O, np.tile(ax, (len(O), 1)), max_len=30.0)))
            bottom = float(_ray_hits(Vm, Fm, hp[None], ax[None], max_len=40.0)[0])
            depth = bottom - entry
            dias, walls, wall_at = [], [], []
            # FIXER r2 (verifier M-V-MPS-1): the wall is sampled over 5..95 % of the depth (7 levels; r2 took 30/50/70 %
            # and missed s_k2's 1.75 wall over the top 2 mm); the pilot diameter from the 35/50/65 % levels
            for f in np.linspace(0.05, 0.95, 7):
                c = hp + ax * (entry + f * (bottom - entry))
                rr = _ray_hits(Vm, Fm, np.tile(c, (len(dirs), 1)), dirs, max_len=5.0)
                if 0.3 < f < 0.7:
                    dias.append(2 * float(np.mean(rr)))
                wl = _ray_hits(Vm, Fm, c + dirs * (rr[:, None] + 1e-3), dirs, max_len=10.0)
                walls.append(float(np.min(wl)))
                wall_at.append([_r(float(x), 2) for x in c])
            hv = _own_copy(rows[s['head_part']]['shape']).intersect(box)
            Vh, Fh = mesh_of(hv, tol=0.02, ang=0.2)
            rh = (PT['clear_d'] / 2 + PT['cbore_d'] / 2) / 2
            O = np.array([hp - ax * 0.3 + d * rh for d in dirs[::3]])
            h1 = _ray_hits(Vh, Fh, O, np.tile(ax, (len(O), 1)), max_len=3.0)
            under = _ray_hits(Vh, Fh, O + ax * (h1[:, None] + 1e-3), np.tile(ax, (len(O), 1)), max_len=20.0)
            under_min = float(np.min(under))
            need_depth = s['engage'] + PT['tip_reserve']
            wall_need = (PT['boss_od_min'] - PT['pilot_d']) / 2     # policy: boss OD >= 7.0 -> wall >= 2.25
            ok = (abs(np.mean(dias) - PT['pilot_d']) <= 0.05 and depth >= need_depth - 0.05 and
                  min(walls) >= wall_need - 0.05 and under_min >= L.FDM['MIN_WALL_LOADED'] - 0.05)
            row.update(pilot_dia=_r(np.mean(dias)), pilot_depth=_r(depth), pilot_depth_min=_r(need_depth),
                       wall_min=_r(min(walls)), wall_need=_r(wall_need), under_head_min=_r(under_min),
                       wall_levels=[_r(w) for w in walls], wall_level_at=wall_at,
                       status='pass' if ok else 'fail')
        except Exception as e:  # noqa: BLE001
            row.update(status='fail', error=str(e)[:200])
        if rows.get(into, {}).get('stub') or rows.get(s['head_part'], {}).get('stub'):   # r2 R3: stub partner
            row['status'] = 'stub'
        out.append(row)
    return out


# =========================================================================================== r2 (R3) rectification
# Finding 2: CRITICAL_FEATURES (deterministic B-rep sections), finding 6: EVF board restraint, findings 1/3: service
# (removal) sweeps + service-state driver audit, section views. Registries: layout.py section 9b (NOTES "r2 R3 API").
REGISTRIES_BY_ID = ('CRITICAL_FEATURES', 'REMOVALS', 'SECTIONS', 'CRITICAL_JOINTS')


def registry(L, name):
    """A layout registry list; CRITICAL_FEATURES / REMOVALS / SECTIONS / CRITICAL_JOINTS entries are de-duplicated by id (last wins,
    first position kept). r6 (audit 2026-10-06 L5): a duplicate id is never silent: duplicate_ids() lists it and
    check_critical_features FAILs it (owners move a probe with layout.replace_feature, in place)."""
    items = list(getattr(L, name, []) or [])
    if name in REGISTRIES_BY_ID:
        d = {}
        for it in items:
            d[it['id']] = it
        return list(d.values())
    return items


def duplicate_ids(L):
    """r6 (L5): {registry: [ids defined more than once]} over REGISTRIES_BY_ID (empty when every id is unique)."""
    out = {}
    for name in REGISTRIES_BY_ID:
        seen, dup = set(), []
        for it in getattr(L, name, []) or []:
            if it['id'] in seen and it['id'] not in dup:
                dup.append(it['id'])
            seen.add(it['id'])
        if dup:
            out[name] = dup
    return out


def _solids(shape):
    return [shape] if shape.ShapeType() == 'Solid' else list(shape.Solids())


def chord(shape, p, d):
    """Entry-to-exit length of the line through p along unit d inside the solid containing p (OCP
    IntCurvesFace_ShapeIntersector on the B-rep; BRepClass3d classifier for 'inside'). Returns (t, w_in, w_out, why)."""
    from OCP.BRepClass3d import BRepClass3d_SolidClassifier
    from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
    from OCP.TopAbs import TopAbs_IN, TopAbs_ON
    from OCP.gp import gp_Dir, gp_Lin, gp_Pnt
    host = None
    for so in _solids(shape):
        st = BRepClass3d_SolidClassifier(so.wrapped, gp_Pnt(*p), 1e-6).State()
        if st == TopAbs_IN:
            host = so
            break
        if st == TopAbs_ON:
            return None, None, None, 'origin on the surface'
    if host is None:
        return None, None, None, 'origin outside the material'
    it = IntCurvesFace_ShapeIntersector()
    it.Load(host.wrapped, 1e-7)
    it.Perform(gp_Lin(gp_Pnt(*p), gp_Dir(*d)), -1.0e3, 1.0e3)
    if not it.IsDone():
        return None, None, None, 'intersector failed'
    ws = [it.WParameter(i) for i in range(1, it.NbPnt() + 1)]
    lo = max([w for w in ws if w < -1e-9], default=None)
    hi = min([w for w in ws if w > 1e-9], default=None)
    if lo is None or hi is None:
        return None, None, None, 'no bracketing faces'
    return hi - lo, lo, hi, None


def feature_class(L, f):
    """FIXER r2 (M-V-MPS-6): (class, required mm, error). required = max(entry min_mm, class floor); a structural entry
    with no class, or a gated class (flexure) without a FEATURE_GATES gate, is an error (FAIL)."""
    import re
    floors = getattr(L, 'FEATURE_CLASS_MIN', None)
    if not floors:
        return None, f.get('min_mm'), None
    cls = f.get('cls')
    if cls is None:
        cls = next((c for pat, c in getattr(L, 'FEATURE_CLASS_RULES', []) if re.search(pat, f['id'])), None)
    if not f.get('structural', True):
        return cls, f.get('min_mm'), None
    if cls not in floors:
        return cls, f.get('min_mm'), 'no feature class for %s (FEATURE_CLASS_RULES)' % f['id']
    if cls in getattr(L, 'FEATURE_CLASS_GATED', ()) and not (getattr(L, 'FEATURE_GATES', {}) or {}).get(f['id']):
        return cls, f.get('min_mm'), 'class %s needs a named physical gate (FEATURE_GATES)' % cls
    return cls, max(float(f.get('min_mm') or 0.0), floors[cls]), None


def feature_offsets(f):
    """Signed offsets along the span axis (0.0 = the nominated origin). r3 checks (audit s3): the origin is ALWAYS
    measured, also when an even span count would step over it."""
    if not f.get('span'):
        return [0.0], None
    n, step, ax = f['span']
    ax = np.array(ax, float)
    ax /= np.linalg.norm(ax)
    offs = [round((k - (n - 1) / 2.0) * step, 6) for k in range(int(n))]
    if not any(abs(s) < 1e-9 for s in offs):
        offs.append(0.0)
    return sorted(offs, key=lambda s: (abs(s) > 1e-9, s)), ax


def check_critical_features(L, rows):
    """Finding 2 + r3 checks (audit 2026-10-05 s3). Every CRITICAL_FEATURES entry is measured on the built solid:
    the nominated origin is always measured and must lie in material (else FAIL: stale origin); every span ray must
    hit the solid unless its offset is listed in expect_outside=dict(offsets=[...], why=...) (on the entry, or in
    L.EXPECT_OUTSIDE[id] for an entry generated in another block; an unexpected miss FAILs,
    a listed offset that is in material or not on the span FAILs as a stale declaration); structural < class floor
    FAILs. Gated classes (flexures) report 'info' with their physical gate, never an ordinary pass. Then
    check_joint_coverage (CRITICAL_JOINTS: every required feature of every load-carrying joint) and, as a secondary
    rule, >= 1 structural entry per LOAD_BEARING_PARTS member."""
    out = []
    for reg, ids in duplicate_ids(L).items():     # r6 (L5): an id overwritten by a later entry hides the earlier probe
        out.append(dict(kind='registry', id='duplicate_ids', registry=reg, duplicates=ids, status='fail',
                        error='%s defines id(s) %s more than once (last wins would silently drop a probe); move a '
                              'probe with layout.replace_feature' % (reg, ', '.join(ids))))
    feats = registry(L, 'CRITICAL_FEATURES')
    gates_of = getattr(L, 'FEATURE_GATES', {}) or {}
    for f in feats:
        pid = f['part']
        row = dict(kind='feature', id=f['id'], part=pid, min_mm=f.get('min_mm'), structural=bool(f.get('structural', True)),
                   origin=list(f['origin']), direction=list(f['direction']), note=f.get('note', ''))
        cls, need, cls_err = feature_class(L, f)                 # FIXER r2 (M-V-MPS-6): class floor, not the literal
        row.update(cls=cls, entry_min_mm=f.get('min_mm'), min_mm=need)
        gate = gates_of.get(f['id'])
        if gate:
            row['gate'] = gate + ' (physical, not run)'
        r = rows.get(pid)
        if pid not in L.PARTS:
            row.update(status='info', note='part not in PARTS (removed): entry not measured; ' + row['note'])
            out.append(row)
            continue
        if r is None or r.get('shape') is None:
            row.update(status='fail', error='part %s not built' % pid)
            out.append(row)
            continue
        d = np.array(f['direction'], float)
        d /= np.linalg.norm(d)
        o = np.array(f['origin'], float)
        offs, ax = feature_offsets(f)
        exp = f.get('expect_outside') or (getattr(L, 'EXPECT_OUTSIDE', {}) or {}).get(f['id']) or {}
        exp_offs = [float(x) for x in exp.get('offsets', [])]
        decl_err = []
        if exp and not exp.get('why'):
            decl_err.append('expect_outside without a reason (why)')
        decl_err += ['expect_outside offset %g is not a span ray' % e for e in exp_offs
                     if not any(abs(e - s) < 1e-6 for s in offs) or abs(e) < 1e-9]
        vals, centre_err, best, outside_ok, outside_bad, exp_inside = [], None, None, [], [], []
        for s in offs:
            p = o + (ax * s if ax is not None else 0.0)
            t, w0, w1, why = chord(r['shape'], tuple(float(x) for x in p), tuple(float(x) for x in d))
            listed = abs(s) > 1e-9 and any(abs(s - e) < 1e-6 for e in exp_offs)
            if t is None:
                if abs(s) < 1e-9:
                    centre_err = why
                elif listed:
                    outside_ok.append(s)
                else:
                    outside_bad.append('%g (%s)' % (s, why))
                continue
            if listed:
                exp_inside.append(s)
            vals.append(round(t, 3))
            if best is None or t < best[0]:
                best = (t, p + d * w0, p + d * w1)
        decl_err += ['expect_outside offset %g is in material (stale declaration)' % s for s in exp_inside]
        row.update(rays=len(offs), offsets=offs, rays_outside=len(outside_ok) + len(outside_bad),
                   expected_outside=outside_ok, values=vals,
                   measured_mm=None if not vals else round(min(vals), 3),
                   entry=None if best is None else [_r(x, 2) for x in best[1]],
                   exit=None if best is None else [_r(x, 2) for x in best[2]],
                   method='OCP IntCurvesFace_ShapeIntersector chord through origin (B-rep, exact)')
        if exp:
            row['expect_outside_why'] = exp.get('why')
        if r.get('stub'):
            row.update(status='stub', note='measured on the stub envelope (meaningless); ' + row['note'])
        elif centre_err is not None:
            row.update(status='fail', error='stale origin: ' + centre_err)
        elif outside_bad:
            row.update(status='fail', error='unexpected missing ray(s) at offset ' + ', '.join(outside_bad) +
                       ' (list intended ones in expect_outside)')
        elif decl_err:
            row.update(status='fail', error='; '.join(decl_err))
        elif not row['structural']:
            row['status'] = 'info'
        elif cls_err:
            row.update(status='fail', error=cls_err)
        elif row['measured_mm'] < need - 1e-3:
            row['status'] = 'fail'
        elif cls in getattr(L, 'FEATURE_CLASS_GATED', ()):
            row.update(status='info', exception='gated exception: %.3f >= class floor %.2f but acceptance rests on %s '
                       '(physical, not run); not an ordinary %.1f structural pass' % (
                           row['measured_mm'], need, gate, L.FDM['MIN_WALL_LOADED']))
        else:
            row['status'] = 'pass'
        out.append(row)
    out += check_joint_coverage(L, out)
    for pid in registry(L, 'LOAD_BEARING_PARTS'):          # secondary rule (r2)
        if pid not in L.PARTS:
            out.append(dict(kind='coverage', part=pid, status='info', note='not in PARTS (part removed): no entry needed'))
            continue
        n = sum(1 for f in feats if f['part'] == pid and f.get('structural', True))
        out.append(dict(kind='coverage', part=pid, structural_entries=n, status='pass' if n else 'fail',
                        error=None if n else 'missing coverage: load-bearing part has no structural entry'))
    for e in registry(L, 'NONSTRUCTURAL_EXCEPTIONS'):
        out.append(dict(e, kind='exception', status='info'))
    return out


def check_joint_coverage(L, feat_rows):
    """r3 checks (audit s3): every CRITICAL_JOINTS entry dict(id, parts, required=[feature ids], note) passes only if
    each required feature exists, was measured on a part of that joint and passed (a gated exception counts only with
    its named physical gate, listed); a LOAD_BEARING_PARTS member in no joint, or no CRITICAL_JOINTS at all, FAILs."""
    out = []
    joints = registry(L, 'CRITICAL_JOINTS')
    by_id = {r['id']: r for r in feat_rows if r.get('kind') == 'feature'}
    gates_of = getattr(L, 'FEATURE_GATES', {}) or {}
    lb = [p for p in registry(L, 'LOAD_BEARING_PARTS') if p in L.PARTS]
    if not joints:
        return [dict(kind='joint', id='CRITICAL_JOINTS', status='fail' if lb else 'info',
                     error='no CRITICAL_JOINTS registry: joint coverage cannot be shown' if lb else None)]
    for j in joints:
        parts = list(j.get('parts', []))
        row = dict(kind='joint', id=j['id'], parts=parts, required=list(j.get('required', [])), note=j.get('note', ''))
        if parts and not any(p in L.PARTS for p in parts):
            out.append(dict(row, status='info', note='parts removed: ' + row['note']))
            continue
        probs, gated, stub = [], {}, False
        if not row['required']:
            probs.append('no required features listed')
        for fid in row['required']:
            r = by_id.get(fid)
            if r is None:
                probs.append('%s: missing entry' % fid)
            elif r['part'] not in parts:
                probs.append('%s: on part %s, not a part of this joint' % (fid, r['part']))
            elif r['status'] == 'stub':
                stub = True
            elif r['status'] == 'fail':
                probs.append('%s: %s' % (fid, r.get('error') or 'below its floor'))
            elif r.get('measured_mm') is None:
                probs.append('%s: not measured' % fid)
            elif r['status'] == 'info':
                if gates_of.get(fid):
                    gated[fid] = gates_of[fid] + ' (physical, not run)'
                else:
                    probs.append('%s: non-structural / informational without a named physical gate' % fid)
            elif r['status'] != 'pass':                    # r3 fix-baseline V-L2: only a measured pass is accepted
                probs.append('%s: status %r' % (fid, r['status']))
        row.update(gated_exceptions=gated, problems=probs,
                   status='fail' if probs else ('stub' if stub else ('info' if gated else 'pass')))
        if probs:
            row['error'] = '; '.join(probs)
        elif gated and not stub:    # r3 fix-baseline V-L1: a joint resting on a physical gate is not a computed pass
            row['exception'] = ('coverage complete; acceptance of %d feature(s) rests on %s (physical, not run)'
                                % (len(gated), ', '.join(sorted({gates_of[f] for f in gated}))))
        out.append(row)
    # r3 fix-baseline V-M3: the baseline joint ids are a fixed list (REQUIRED_JOINT_IDS); deleting a joint entry together
    # with its probes FAILs unless a fork joint (FR_JOINTS merged into CRITICAL_JOINTS) names it in `replaces`.
    req_ids = getattr(L, 'REQUIRED_JOINT_IDS', None)
    if req_ids is None:
        if lb:
            out.append(dict(kind='joint', id='REQUIRED_JOINT_IDS', status='fail',
                            error='no REQUIRED_JOINT_IDS registry: a deleted joint entry could not be detected'))
    else:
        have = {j['id'] for j in joints}
        # r4 (audit 2026-10-05-r3, logic issue 3): only a replacement that is itself a CRITICAL_JOINTS entry and was
        # validated above (a measured pass, or full coverage resting on a named physical gate) can stand in for a
        # required joint. An FR_JOINTS declaration that never reached CRITICAL_JOINTS waives nothing.
        valid = {r['id'] for r in out if r.get('kind') == 'joint' and not r.get('problems') and r.get('required')
                 and (r['status'] == 'pass' or (r['status'] == 'info' and r.get('gated_exceptions')))}
        repl = {x for j in joints if j['id'] in valid for x in (j.get('replaces') or [])}
        unvalidated = {x: j['id'] for j in registry(L, 'FR_JOINTS') if j['id'] not in valid
                       for x in (j.get('replaces') or [])}
        for jid in req_ids:
            if jid not in have and jid not in repl:
                why = 'required joint %s is not in CRITICAL_JOINTS and no validated joint replaces it' % jid
                if jid in unvalidated:
                    why += ' (%s declares the replacement but is not a validated CRITICAL_JOINTS entry)' % unvalidated[jid]
                out.append(dict(kind='joint', id=jid, status='fail', error=why))
    for p in lb:
        if not any(p in j.get('parts', []) for j in joints):
            out.append(dict(kind='joint', id='part:' + p, status='fail',
                            error='load-bearing part %s is in no CRITICAL_JOINTS entry' % p))
    return out


# ------------------------------------------------------------------------------------------- finding 6: EVF restraint
DIRS6 = {'+X': (1, 0, 0), '-X': (-1, 0, 0), '+Y': (0, 1, 0), '-Y': (0, -1, 0), '+Z': (0, 0, 1), '-Z': (0, 0, -1)}


def _crop_manifold(shape, bb, pad):
    lo = np.array([bb[0], bb[2], bb[4]]) - pad
    hi = np.array([bb[1], bb[3], bb[5]]) + pad
    loc = _own_copy(shape).intersect(cq.Solid.makeBox(*(hi - lo), V(*lo)))
    try:
        if loc.Volume() < 1e-6:
            return None
    except Exception:  # noqa: BLE001
        return None
    return manifold_of(loc)


def _first_contact(mv, ob, d, tmax, coarse=0.1, tol=0.02):
    """Smallest translation t in (0, tmax] along d at which the mesh-boolean overlap of mv and ob grows by > tol mm3
    over its t = 0 value (bracket at `coarse`, then 8 bisections). None: no contact within tmax."""
    v0 = (mv ^ ob).volume()

    def hit(t):
        return (mv.translate([d[0] * t, d[1] * t, d[2] * t]) ^ ob).volume() - v0 > tol

    t_prev, t = 0.0, coarse
    while t <= tmax + 1e-9:
        if hit(t):
            lo, hi = t_prev, t
            for _ in range(8):
                mid = (lo + hi) / 2
                lo, hi = (lo, mid) if hit(mid) else (mid, hi)
            return hi
        t_prev, t = t, t + coarse
    return None


def _evf_board_zones(L):
    """Named sub-volumes of the board proxy (same formulas as cots.evf_board): PCB, components, HDMI receptacle, ZIF."""
    c = L.COTS['evf_board']
    b = c['box']
    px0, px1 = c['features']['pcb_x']
    return {'hdmi receptacle': (b['x'][0], px0, 4.0, 17.0, b['z'][0], b['z'][0] + 4.0),
            'ZIF (OLED flex)': (px0 - 2.0, px0, b['y'][0] + 6.0, b['y'][0] + 19.0, b['z'][1] - 5.6, b['z'][1] - 1.6),
            'components': (b['x'][0] + 1.6, px0, b['y'][0] + 2.0, b['y'][1] - 2.0, b['z'][0] + 5.0, b['z'][1] - 2.0),
            'pcb': (px0, px1, b['y'][0], b['y'][1], b['z'][0], b['z'][1])}


def check_evf_restraint(L, rows):
    """Finding 6. For +-X, +-Y, +-Z: gap from the EVF board (final pose) to the first arresting surface (translation
    sweep of the board mesh against each arresting part, manifold3d boolean, tessellation 0.05). gap <= limit passes;
    a larger gap, or no stop within max_travel, FAILs (flagged). The contact region is classed by board sub-volume, so
    a stop bearing on a connector or the ZIF shows."""
    import manifold3d as m3
    R = L.EVF_RESTRAINT
    br = rows.get(R['part'])
    if br is None or br.get('shape') is None:
        return [dict(direction='all', status='fail', error='board not built')]
    bm = manifold_of(br['shape'])
    bb = bb_tuple(br['shape'])
    obs = {}
    for a in R['arrest']:
        if rows.get(a, {}).get('shape') is not None:
            obs[a] = _crop_manifold(rows[a]['shape'], bb, R['max_travel_mm'] + 1.0)
    zones = _evf_board_zones(L)

    def cube(z):
        return m3.Manifold.cube([z[1] - z[0], z[3] - z[2], z[5] - z[4]]).translate([z[0], z[2], z[4]])
    # FIXER r2 (verifier M-V-MPS-3): the micro-HDMI plug envelope rides with the board (it is in the receptacle), and
    # the first contact is found per board zone: a connector, ZIF or plug zone that touches within the PCB's own first
    # contact + 0.2 FAILs (the stop must be the PCB, not a connector)
    zm = {k: bm ^ cube(z) for k, z in zones.items()}
    pk = (getattr(L, 'KEEPOUTS', {}) or {}).get('ko_hdmi_evf')
    mv = bm
    if pk is not None:
        pz = (pk['x'][0], pk['x'][1], pk['y'][0], pk['y'][1], pk['z'][0], pk['z'][1])
        zm['hdmi plug'] = cube(pz)
        mv = bm + zm['hdmi plug']
    conn_zones = ('hdmi receptacle', 'ZIF (OLED flex)', 'hdmi plug')
    out = []
    for name, d in DIRS6.items():
        best = None
        for a, om in obs.items():
            if om is None:
                continue
            t = _first_contact(mv, om, d, R['max_travel_mm'])
            if t is not None and (best is None or t < best[0]):
                best = (t, a)
        row = dict(direction=name, limit_mm=R['limit_mm'], arresting=None if best is None else best[1],
                   gap_mm=None if best is None else _r(best[0], 2))
        per_zone = {}
        if best is not None:
            lim = best[0] + 0.3
            for k, m in zm.items():
                tz = None
                for a, om in obs.items():
                    if om is None or m.volume() < 1e-9:
                        continue
                    t = _first_contact(m, om, d, lim, coarse=0.05)
                    if t is not None and (tz is None or t < tz[0]):
                        tz = (t, a)
                per_zone[k] = None if tz is None else dict(gap_mm=_r(tz[0], 2), on=tz[1])
            row['first_contact_by_zone'] = per_zone
            t_pcb = per_zone.get('pcb')
            t_pcb = None if t_pcb is None else t_pcb['gap_mm']
            conn = {k: v['gap_mm'] for k, v in per_zone.items()
                    if k in conn_zones and v is not None and (t_pcb is None or v['gap_mm'] <= t_pcb + 0.2 + 1e-6)}
            if conn:
                row['connector_stop'] = conn
        if best is not None:
            tt = best[0] + 0.05
            inter = mv.translate([d[0] * tt, d[1] * tt, d[2] * tt]) ^ obs[best[1]]
            if inter.volume() > 1e-9:
                ib = inter.bounding_box()
                cb = (ib[0] - d[0] * tt, ib[3] - d[0] * tt, ib[1] - d[1] * tt, ib[4] - d[1] * tt,
                      ib[2] - d[2] * tt, ib[5] - d[2] * tt)          # contact region back in the board's frame
                row['contact_bbox'] = [_r(x, 2) for x in cb]
                back = inter.translate([-d[0] * tt, -d[1] * tt, -d[2] * tt])     # contact solid in the board frame
                vt = max(1e-12, back.volume())
                share = {k: (back ^ m3.Manifold.cube([z[1] - z[0], z[3] - z[2], z[5] - z[4]])
                             .translate([z[0], z[2], z[4]])).volume() / vt for k, z in zones.items()}
                row['bears_on'] = [k for k, v in share.items() if v > 1e-3]
                row['contact_share'] = {k: _r(v, 3) for k, v in share.items() if v > 1e-3}
                bad = {k: v for k, v in share.items() if k in ('hdmi receptacle', 'ZIF (OLED flex)') and v >= 0.10}
                if bad:     # a stop must bear on a component-free PCB region (brief, finding 6): flagged for the bench
                    row['flag'] = 'contact on %s (%s of the contact volume, proxy envelopes): verify on the real board' % (
                        ', '.join(bad), ', '.join('%.0f %%' % (100 * v) for v in bad.values()))
        if best is None:
            row.update(status='fail', error='no arresting surface within %.1f mm' % R['max_travel_mm'])
        else:
            row['status'] = 'pass' if best[0] <= R['limit_mm'] + 1e-6 else 'fail'
            if row['status'] == 'fail':
                row['error'] = 'gap %.2f > limit %.2f' % (best[0], R['limit_mm'])
            elif row.get('connector_stop'):
                row.update(status='fail', error='connector/plug zone within PCB first contact + 0.2: %s' % (
                    ', '.join('%s %.2f' % kv for kv in row['connector_stop'].items())))
        if br.get('stub') or (best is not None and rows[best[1]].get('stub')):
            row['status'] = 'stub'
        out.append(row)
    out += _support_span_rows(L, rows, obs, zones, R, br)      # r7 C1 (SPEC-C1 4.3)
    return out


SUPPORT_END_MM = 3.0    # r7 C1: a supported 1 mm slice must lie within this of each y end of the PCB


def _support_span_rows(L, rows, obs, zones, R, br):
    """r7 C1 (SPEC-C1 4.3): -Z support span under the PCB lower edge. The PCB zone's lower 1.0 band in 1.0 mm y
    slices; a slice is supported when its -Z first contact (translation, mesh boolean) is <= limit_mm. Pass: a
    supported slice within SUPPORT_END_MM of EACH y end, for the final arrest set and the pre-panel set (panel off:
    steps 6-8 and every panel-off service)."""
    import manifold3d as m3
    pz = zones['pcb']
    lim = R['limit_mm']
    y0, y1 = pz[2], pz[3]
    nsl = max(1, int(round(y1 - y0)))
    slices = [(y0 + i * (y1 - y0) / nsl, y0 + (i + 1) * (y1 - y0) / nsl) for i in range(nsl)]
    out = []
    for name, drop in (('support_span_final', ()), ('support_span_prepanel', ('panel',))):
        arrest = [a for a in R['arrest'] if a not in drop and obs.get(a) is not None]
        sup, gaps = [], []
        for a0, a1 in slices:
            cm = m3.Manifold.cube([pz[1] - pz[0], a1 - a0, 1.0]).translate([pz[0], a0, pz[4]])
            best = None
            for a in arrest:
                t = _first_contact(cm, obs[a], (0, 0, -1), lim + 0.4)
                if t is not None and (best is None or t < best[0]):
                    best = (t, a)
            gaps.append([_r(a0, 2), _r(a1, 2), None if best is None else _r(best[0], 2), None if best is None
                         else best[1]])
            if best is not None and best[0] <= lim + 1e-6:
                sup.append((a0, a1))
        lo_ok = any(a0 <= y0 + SUPPORT_END_MM + 1e-6 for a0, _a1 in sup)
        hi_ok = any(a1 >= y1 - SUPPORT_END_MM - 1e-6 for _a0, a1 in sup)
        row = dict(direction=name, limit_mm=lim, arrest=arrest, band_z=[pz[4], pz[4] + 1.0], slice_mm=1.0,
                   end_window_mm=SUPPORT_END_MM, supported=[[_r(a, 2), _r(b, 2)] for a, b in sup], slices=gaps,
                   gap_mm=min((g[2] for g in gaps if g[2] is not None), default=None),
                   status='pass' if (lo_ok and hi_ok) else 'fail')
        if row['status'] == 'fail':
            row['error'] = 'no supported slice within %.1f mm of the %s end' % (
                SUPPORT_END_MM, ' and '.join(e for e, ok in (('-Y', lo_ok), ('+Y', hi_ok)) if not ok))
        if br.get('stub') or any(rows.get(a, {}).get('stub') for a in arrest):
            row['status'] = 'stub'
        out.append(row)
    return out


# ------------------------------------------------------------------------------------------- findings 1/3: service sweeps
def final_ids(L):
    return L.present_at(max(s['step'] for s in L.STEPS))


def removal_path(L, rem):
    """Waypoints in INSERTION order (out .. (0, 0, 0)); the position set is the same as the removal path's."""
    if rem.get('reverse_of'):
        ins = next(i for i in L.INSERTIONS if i['id'] == rem['reverse_of'])
        return list(ins['path'])
    return list(reversed(rem['path']))


def service_context(L, rows, rem):
    gone = set(rem['moving']) | set(rem.get('off', [])) | set(rem.get('unscrew', []))   # unscrewed = out before the move
    return [i for i in final_ids(L) if i not in gone and i in rows and rows[i].get('shape') is not None]


SERVICE_GEOMETRY_ONLY = ('clearance with the cap and pack fitted; geometry only: electronic service still requires '
                         'shutdown, pack removal and XT30 disconnection first (ASSEMBLY s7 P1-P4)')


def check_removals(L, rows, step_mm=2.0):
    """Service-path sweeps: each REMOVALS entry moves its set from the final pose out along its path, against the
    service state (everything after the last step, minus `off` and the moving set; remaining screws included).
    Overlap is allowed only inside the named `release` zones (a stated tool deflects a latch there). Mesh boolean as in
    check_sweeps. Returns (sweep rows, service-state driver rows for `unscrew`)."""
    import manifold3d as m3
    zones = snap_zones(L)
    mates = mate_table(L)
    cache = {}

    def man(i):
        if i not in cache:
            cache[i] = manifold_of(rows[i]['shape'])
        return cache[i]

    out, drv = [], []
    for rem in registry(L, 'REMOVALS'):
        ctx = service_context(L, rows, rem)
        rel = []
        for z in rem.get('release', []):
            zb = zones.get(z) if isinstance(z, str) else box_bb(z)
            if zb is not None:
                rel.append(m3.Manifold.cube([zb[1] - zb[0], zb[3] - zb[2], zb[5] - zb[4]]).translate([zb[0], zb[2], zb[4]]))
        missing = [m for m in rem['moving'] if m not in rows or rows[m].get('shape') is None]
        pts = _path_points(removal_path(L, rem), step_mm)
        worst, err = {}, []
        targets = [(o, man(o), bb_tuple(rows[o]['shape'])) for o in ctx]
        targets += [(k, m3.Manifold.cube([b['x'][1] - b['x'][0], b['y'][1] - b['y'][0], b['z'][1] - b['z'][0]])
                     .translate([b['x'][0], b['y'][0], b['z'][0]]), box_bb(b))
                    for k, b in ((k, L.KEEPOUTS[k]) for k in rem.get('keepouts', []))]
        # r7 C1 (SPEC-C1 4.1 via reverse_of): fixed-end rigid plugs (mated in service unless in `unplug`) are hard
        #     obstacles for the movers and the carried boxes
        fixed = fixed_end_plugs(L, rem, removal=True, present=set(ctx) | set(rem['moving']))
        xbox = {_plug_name(p): _plug_box(L, p) for p in fixed if _plug_name(p) not in rem.get('keepouts', [])}
        xtargets = [(k, _bb_cube(m3, b), b) for k, b in sorted(xbox.items())]
        targets += xtargets
        for mv in [m for m in rem['moving'] if m not in missing]:
            mm = man(mv)
            mbb = bb_tuple(rows[mv]['shape'])
            for o, om, obb in targets:
                if (mates.get(frozenset((mv, o))) or '').split(' ')[0] in ('press', 'thread', 'interference'):
                    continue
                if mm is None or om is None:
                    err.append('no manifold mesh for %s / %s' % (mv, o))
                    continue
                for p in pts:
                    sbb = (mbb[0] + p[0], mbb[1] + p[0], mbb[2] + p[1], mbb[3] + p[1], mbb[4] + p[2], mbb[5] + p[2])
                    if not bb_overlap(sbb, obb, -1e-6):
                        continue
                    inter = mm.translate(list(p)) ^ om
                    for z in rel:
                        inter = inter - z
                    v = inter.volume()
                    if v > SWEEP_TOL and v > worst.get((mv, o), (0.0,))[0]:
                        worst[(mv, o)] = (v, p, [_r(x, 1) for x in inter.bounding_box()])
        hits = [dict(moving=mv, obstacle=o, max_volume_mm3=_r(v, 2), at_offset=[_r(x, 1) for x in p], where=w)
                for (mv, o), (v, p, w) in worst.items()]
        # r7 C1: carried boxes (rigid plugs still mated on the moving set, i.e. not in rem['unplug']) against the
        #     service state, its stated keep-outs and the service-state cable keep-outs (soft/hard classes as in sweeps)
        cbx = carry_boxes(L, rem, removal=True)
        svc_ko = set(rem.get('keepouts', []))
        for cab in L.CABLES:
            ends = set(cab.get('ends') or CABLE_ENDS.get(cab['id'], ()))
            if (ends & set(ctx)) and not (ends & set(rem['moving'])):
                svc_ko |= set(cab['via'])
        ctargets = [t for t in targets if t[0] in ctx] + xtargets
        ctargets += [(k, _bb_cube(m3, box_bb(L.KEEPOUTS[k])), box_bb(L.KEEPOUTS[k])) for k in sorted(svc_ko)]
        kinds = {o: 'solid' for o in ctx}
        kinds.update({k: keepout_kind_of(L, k) for k in svc_ko})
        kinds.update({k: 'plug' for k in xbox})
        cworst, soft_rows = _carried_sweep(L, m3, cbx, pts, ctargets, kinds) if cbx else ({}, [])
        for (nm, o), (v, p, w) in cworst.items():
            hits.append(dict(moving=nm, obstacle=o, max_volume_mm3=_r(v, 2), at_offset=[_r(x, 1) for x in p],
                             where=w, carried=True))
        for s in soft_rows:
            if not s['ok']:
                hits.append(dict(moving=s['carried'], obstacle=s['keepout'], max_volume_mm3=s['volume_mm3'],
                                 at_offset=s['at_offset'], carried=True,
                                 error='soft contact %.2f mm > CARRY_SOFT_MM %.1f' % (s['penetration_mm'],
                                                                                     CARRY_SOFT_MM)))
        fx = []
        for p in fixed:
            nm = _plug_name(p)
            vs = [h['max_volume_mm3'] for h in hits if h['obstacle'] == nm]
            fx.append(dict(plug=p['id'], keepout=nm, max_volume_mm3=max(vs) if vs else 0.0))
        stub = any(rows.get(i, {}).get('stub') for i in list(rem['moving']) + ctx)
        st = 'fail' if (hits or err or missing) else 'pass'
        if st == 'fail' and stub and not err and not missing:
            st = 'stub'
        out.append(dict(removal=rem['id'], moving=rem['moving'], off=rem.get('off', []), context=ctx,
                        release=[z if isinstance(z, str) else 'box' for z in rem.get('release', [])],
                        tool=rem.get('tool', ''), note=rem.get('note', ''), positions=len(pts), hits=hits,
                        unplug=list(rem.get('unplug') or []), carried=[c[0] for c in cbx],
                        soft_contacts=[s for s in soft_rows if s['ok']], fixed_end_obstacles=fx,
                        errors=err + (['moving part(s) not built: ' + ', '.join(missing)] if missing else []),
                        status=st, method='manifold3d mesh boolean, tessellation 0.05 mm, tol %.1f mm3; service state'
                        % SWEEP_TOL))
        geo_only = None
        if any(p in ctx for p in ('pack', 'xt30_pair')):    # r3 checks (audit s1): a fitted-pack path is geometry only
            geo_only = getattr(L, 'SERVICE_GEOMETRY_ONLY_NOTE', SERVICE_GEOMETRY_ONLY)
            out[-1]['scope'] = geo_only
        if rem.get('unscrew'):
            ids_ctx = [i for i in ctx if not i.startswith('s_')]
            d0 = len(drv)
            drv += check_driver(L, rows, screw_ids=set(rem['unscrew']), audit_set_of=lambda _s, c=ids_ctx: c,
                                context='service: ' + rem['id'])
            if geo_only:
                for x in drv[d0:]:
                    x['scope'] = geo_only
    for sd in getattr(L, 'SERVICE_DRIVER', []) or []:      # r6 (B-11): screws turned without a REMOVALS move
        ctx = [i for i in sd['context'] if i in rows]
        drv += check_driver(L, rows, screw_ids=set(sd['unscrew']), audit_set_of=lambda _s, c=ctx: c,
                            context='service: ' + sd['id'])
    return out, drv


def unclassified_thin_spots(L, thin_rows, radius=2.5):
    """Informational (finding 2): thin-wall screen samples under the wall threshold on LOAD_BEARING_PARTS that lie more
    than `radius` from every CRITICAL_FEATURES origin/span of that part and every NONSTRUCTURAL_EXCEPTIONS 'at' point.
    The share rule no longer hides them: each needs an owner decision (structural entry, or named exception)."""
    lb = set(registry(L, 'LOAD_BEARING_PARTS'))
    anchors = {}
    for f in registry(L, 'CRITICAL_FEATURES'):
        o = np.array(f['origin'], float)
        pts = [o]
        if f.get('span'):
            n, step, ax = f['span']
            ax = np.array(ax, float) / np.linalg.norm(ax)
            pts = [o + ax * (k - (n - 1) / 2.0) * step for k in range(int(n))]
        anchors.setdefault(f['part'], []).extend((p, f['id']) for p in pts)
    for e in registry(L, 'NONSTRUCTURAL_EXCEPTIONS'):
        if e.get('at') is not None:
            pts = [e['at']] + list(e.get('also_at', []))          # FIXER r2: a long feature names several points
            anchors.setdefault(e['part'], []).extend((np.array(a, float), 'exception ' + e['id']) for a in pts)
    out = []
    for t in thin_rows:
        pid = t.get('part')
        if pid not in lb or not t.get('below_min_wall'):
            continue
        groups = []
        for smp in t['below_min_wall']:
            p = np.array(smp['at'], float)
            near = [(float(np.linalg.norm(p - a)), i) for a, i in anchors.get(pid, [])]
            near = min(near) if near else (float('inf'), None)
            if near[0] <= radius:
                continue
            g = next((g for g in groups if np.linalg.norm(np.array(g['at']) - p) <= radius), None)
            if g is None:
                groups.append(dict(part=pid, at=smp['at'], t_min=smp['t'], samples=1, wall_threshold=t.get('wall_threshold'),
                                   nearest_entry=near[1], status='info',
                                   note='unclassified: owner adds a structural CRITICAL_FEATURES entry or a named '
                                        'NONSTRUCTURAL_EXCEPTIONS entry with at=(x, y, z)'))
            else:
                g['samples'] += 1
                if smp['t'] < g['t_min']:
                    g['t_min'], g['at'] = smp['t'], smp['at']
        out += groups
    return out


SERVICE_REQUIRED = [('Pi stack', 'pi5'), ('panel opening', 'panel')]     # review findings 1 and 3


def removal_coverage(L):
    """A modelled removal path must exist for each SERVICE_REQUIRED item (missing coverage FAILs)."""
    rems = registry(L, 'REMOVALS')
    out = []
    for name, key in SERVICE_REQUIRED + list(getattr(L, 'SERVICE_REQUIRED_EXTRA', [])):
        ids = [r['id'] for r in rems if key in r['moving']]
        out.append(dict(removal='coverage: ' + name, paths=ids, status='pass' if ids else 'fail',
                        error=None if ids else 'no REMOVALS entry moves %s' % key))
    # FIXER r2 (M-V-MPS-2): every non-screw part a REMOVALS entry takes 'off' needs its own REMOVALS path or a stated
    # latch-free reason (LATCH_FREE); a part put 'off' by fiat with a latch is a FAIL
    lf = getattr(L, 'LATCH_FREE', {}) or {}
    moved = {m for r in rems for m in r['moving']}
    screws = {s['id'] for s in L.SCREWS}
    offs = sorted({o for r in rems for o in r.get('off', []) if o not in screws})
    bad = [o for o in offs if o not in moved and o not in lf]
    out.append(dict(removal='coverage: parts taken off', parts=offs, own_path=[o for o in offs if o in moved],
                    latch_free={o: lf[o] for o in offs if o in lf and o not in moved},
                    status='fail' if bad else 'pass',
                    error=('no REMOVALS path and no LATCH_FREE reason: ' + ', '.join(bad)) if bad else None))
    return out


# ------------------------------------------------------------------------------------------- r7 C5 handling
# r7 C5 (BX-5, BX-13; SPEC-C5 3.2, Plan edits P5-4/P5-5): how every 'press' mate is reacted (PRESS_FITS), and how the
# body rests while screws are driven once a snap-retained target carries a pressed part (REST_POSES).
HANDLING_DISP = 0.3           # mm: the target is moved this far along the press axis
HANDLING_RIGID_MIN = 0.5      # mm3: displaced overlap outside the snap zones that makes a rigid backing
HANDLING_SNAP_MAX = 0.05      # mm3: a 'snap' target may show no more than this outside its snap zones (final state)
HANDLING_ZONE_MIN = 0.05      # mm3: ... and at least this inside them (the snap teeth exist)
HANDLING_BACKING_LEN = 60.0   # mm: backing (thumb) column length beyond the target, along the press axis
REST_TOUCH_MM = 0.5           # parts within this of the rest-face extreme touch the rest surface
LAND_SLAB, LAND_PANEL_SLAB, LAND_MIN_MM2, LAND_PANEL_FRAC, LAND_GAP_MAX = 0.25, 0.2, 100.0, 0.9, 0.30
REST_STOP_ALLOWED = ('panel', 'hood', 'tub')
_HAX = {'X': 0, 'Y': 1, 'Z': 2}


def _hsolid(lo, hi):
    return cq.Solid.makeBox(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2], V(*lo))


def _hface(face):
    """'+Z' -> (axis index 2, sign +1)."""
    return _HAX[face[1].upper()], (1 if face[0] == '+' else -1)


def _bb_gap(a, b):
    """Largest axis separation of two bb tuples (> 0: apart by that much; <= 0: the boxes overlap)."""
    return max(max(b[2 * k] - a[2 * k + 1], a[2 * k] - b[2 * k + 1]) for k in range(3))


def _first_add(L, pid):
    return next((s['step'] for s in L.STEPS if pid in s.get('adds', [])), None)


# r7 fix-up (VERIFY-C5): two physical rules for every REST_POSES row whose support is not 'hand'.
#   driver plane: the straight driver (L.DRIVER: bit, then the handle + REST_HAND_ALLOW_MM of fingers round it) on each
#   screw of the pose stays on the body side of the rest plane, or the part that crosses it lies beyond the bench edge
#   that the row declares (overhang=dict(face, edge_mm): that body face within edge_mm of the edge).
#   stability: the pose's centre of mass (printed volume x density, COTS listed masses, every built lens) projects
#   inside the hull of the lowest REST_FOOT_MM of the touching parts with a tip angle >= REST_TIP_MIN_DEG.
REST_HAND_ALLOW_MM = 10.0     # estimate: fingers wrapped round the driver handle, beyond its radius
REST_FOOT_MM = 1.0            # the contact footprint is the lowest 1 mm of the parts on the rest surface
REST_TIP_MIN_DEG = 10.0       # design choice: a bench nudge must not tip a pose the procedure leaves unattended
REST_DRIVER_STEP = 0.5        # mm along the driver axis


def _rest_driver_row(L, s, k, sg, E, ext_of, ov):
    """Driver envelope of screw s against the rest plane (axis k, sign sg, extreme E). -> dict."""
    D = L.DRIVER
    h, a = s['head_point'], s['axis']
    n = math.sqrt(sum(x * x for x in a))
    a = [x / n for x in a]
    perp = math.sqrt(max(0.0, 1.0 - a[k] ** 2))
    worst, bad = None, []
    lim = sg * E
    ok_out = None
    if ov:
        ko, so = _hface(ov['face'])
        perp_o = math.sqrt(max(0.0, 1.0 - a[ko] ** 2))
        ok_out = so * ext_of(ko, so) + ov['edge_mm']
    t, tmax = 0.0, D['bit_len'] + D['handle_len']
    while t <= tmax + 1e-9:
        r = D['bit_d'] / 2 if t <= D['bit_len'] else D['handle_d'] / 2 + REST_HAND_ALLOW_MM
        p = [h[i] - t * a[i] for i in range(3)]
        v = sg * p[k] + r * perp
        clr = lim - v
        if worst is None or clr < worst[0]:
            worst = (clr, t)
        if clr < -1e-9:
            if not ov or so * p[ko] - r * perp_o < ok_out - 1e-9:
                bad.append(t)
        t += REST_DRIVER_STEP
    return dict(screw=s['id'], clearance_min=_r(worst[0], 2), at_t=_r(worst[1], 1), crossing=bool(worst[0] < 0),
                overhang=ov, status='fail' if bad else 'pass',
                **({'error': 'driver %s crosses the rest plane at t %.1f..%.1f mm from the head%s'
                             % (s['id'], bad[0], bad[-1], '' if not ov else ' inside the declared bench edge')}
                   if bad else {}))


def _hull2(pts):
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts
    cr = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])   # noqa: E731
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cr(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


def _hull_margin(hull, q):
    """Signed distance of q inside a CCW hull (> 0 inside; min over the edges)."""
    if len(hull) < 3:
        return -1e9
    m = 1e9
    for i in range(len(hull)):
        a, b = hull[i], hull[(i + 1) % len(hull)]
        ex, ey = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(ex, ey)
        if ln < 1e-12:
            continue
        m = min(m, (ex * (q[1] - a[1]) - ey * (q[0] - a[0])) / ln)
    return m


def _pose_mass_items(L, rows, P, ids):
    """[(id, mass_g, com)] for the parts present (rows when built, else the solids: printed by volume, COTS by the
    listed mass at the solid centroid) + one entry per built lens set ('lens' present). Massless ids are skipped."""
    out, lens = [], []
    for i in ids:
        if i == 'lens':
            continue
        r = (rows or {}).get(i) or {}
        sh = r.get('shape') if r.get('shape') is not None else P.get(i)
        if sh is None:
            continue
        printed = (r.get('kind') == 'printed') or (not r and i in getattr(L, 'PARTS', {}))
        if not printed:
            m = r.get('mass') if r else (getattr(L, 'COTS', {}).get(i) or {}).get('mass')
            if not m:
                continue
        key = id(sh)                                  # the same solid object -> same volume and centroid (cache)
        if key not in _MASS_CACHE or _MASS_CACHE[key][0] is not sh:
            cc = cq.Shape.centerOfMass(sh) if not r.get('com') else None
            _MASS_CACHE[key] = (sh, sh.Volume() if printed else None,
                                tuple(r['com']) if r.get('com') else (cc.x, cc.y, cc.z))
        _s, vol, c = _MASS_CACHE[key]
        if printed:
            m = L.mass_g(vol, i)
        out.append((i, float(m), tuple(c)))
    if 'lens' in ids:
        import cots
        for name in L.LENSES:
            if name not in _LENS_CACHE:
                _s, d = cots.lens_proxy(L, name)
                _LENS_CACHE[name] = (float(d['mass']), tuple(d['com']))
            lens.append((name,) + _LENS_CACHE[name])
    return out, lens


_MASS_CACHE, _LENS_CACHE = {}, {}


def _rest_stability_row(L, rows, P, ids, k, sg, E):
    """CoM projection vs the hull of the lowest REST_FOOT_MM of the parts on the rest surface (axis k, sign sg)."""
    o = [j for j in range(3) if j != k]
    pts, foot = [], []
    for i in ids:
        if i not in P:
            continue
        bb = bb_tuple(P[i])
        e = bb[2 * k + (1 if sg > 0 else 0)]
        if sg * (E - e) > REST_FOOT_MM:
            continue
        lo, hi = [bb[0] - 1, bb[2] - 1, bb[4] - 1], [bb[1] + 1, bb[3] + 1, bb[5] + 1]
        lo[k], hi[k] = (E - REST_FOOT_MM, E + 1.0) if sg > 0 else (E - 1.0, E + REST_FOOT_MM)
        try:
            sl = P[i].intersect(_hsolid(lo, hi))
            vs, _t = sl.tessellate(0.05, 0.2)
        except Exception:  # noqa: BLE001
            continue
        if vs:
            foot.append(i)
            pts += [(round((v.x, v.y, v.z)[o[0]], 3), round((v.x, v.y, v.z)[o[1]], 3)) for v in vs]
    hull = _hull2(pts)
    items, lens = _pose_mass_items(L, rows, P, ids)
    base_m = sum(m for _, m, _ in items)
    base_mx = [sum(m * c[j] for _, m, c in items) for j in range(3)]
    cases = lens or [(None, 0.0, (0.0, 0.0, 0.0))]
    res = []
    for name, lm, lc in cases:
        M = base_m + lm
        com = [(base_mx[j] + lm * lc[j]) / M for j in range(3)] if M > 0 else [0.0, 0.0, 0.0]
        q = (com[o[0]], com[o[1]])
        mg = _hull_margin(hull, q)
        hgt = abs(E - com[k])
        tip = math.degrees(math.atan2(mg, hgt)) if mg > -1e8 else -90.0
        res.append(dict(lens=name, mass_g=_r(M, 1), com=[_r(x, 2) for x in com], height=_r(hgt, 1),
                        margin=_r(mg, 2), tip_deg=_r(tip, 2)))
    worst = min(res, key=lambda r: r['tip_deg'])
    ok = bool(hull) and worst['tip_deg'] >= REST_TIP_MIN_DEG - 1e-9
    return dict(foot_parts=sorted(foot), hull_pts=len(hull), cases=res, tip_min_deg=REST_TIP_MIN_DEG,
                worst=worst, status='pass' if ok else 'fail',
                **({} if ok else {'error': 'unstable rest: tip at %.1f deg (lens %s) < %.1f; declare support=\'hand\' '
                                          'or change the pose' % (worst['tip_deg'], worst['lens'], REST_TIP_MIN_DEG)}))


def _handling_parts(L, rows, parts_of):
    if parts_of is None:
        return {i: r['shape'] for i, r in rows.items() if r.get('shape') is not None}
    return dict(parts_of(L) if callable(parts_of) else parts_of)


def _press_volumes(T, d, P, ids, zones):
    """Per id: (rest overlap, displaced overlap) of target T with P[id], each split (outside, inside) the zone solids."""
    Tm = T.translate(V(*d))
    bm = bb_tuple(Tm)
    out, err = {}, []
    for i in ids:
        if not bb_overlap(bb_tuple(P[i]), bm, 0.1):
            continue
        vals = []
        for S in (T, Tm):
            v, s = common(S, P[i])
            if v != v:
                err.append('%s: %s' % (i, s))
                v, s = 0.0, None
            z = 0.0
            if s is not None:
                for zb in zones:
                    zv, _ = common(s, zb)
                    z += 0.0 if zv != zv else zv
            vals.append((v - z, z))
        out[i] = vals
    return out, err


def check_handling(L, rows, parts_of=None):
    """r7 C5 (SPEC-C5 3.2). Rows: press_cover (every MATES 'press' row has exactly one PRESS_FITS row), press_fit (the
    declared retention is computed: the target is moved HANDLING_DISP along the press axis; displaced overlap minus
    rest overlap, split by SNAP_TOOTH_ZONES, against the final state ('snap': nothing but the teeth may back it) and
    against the parts present at the press ('rigid'); plus the sequence rules), snap_basis (the in-use load cap of a
    snap row: push uncommissioned, G-ENC-1 not below release_min_N, knob land on the panel), rest_pose (REST_POSES),
    rest_cover (every screw driven once a snap row's pressed part is in the body has a pose) and info rows
    (REST_FORBIDDEN touching sets). parts_of: {id: solid} or callable(L) (tests); default: rows shapes (printed solids
    and COTS proxy solids, never a COTS bbox)."""
    P = _handling_parts(L, rows, parts_of)
    PF = list(getattr(L, 'PRESS_FITS', []))
    out = []
    key = lambda a, b: tuple(sorted((a, b)))                                   # noqa: E731
    mates = [key(a, b) for a, b, k in L.MATES if k == 'press']
    have = [key(r['part'], r['onto']) for r in PF]
    missing = sorted({m for m in mates if have.count(m) != 1})
    stray = sorted({h for h in have if h not in mates})
    out.append(dict(kind='press_cover', id='press_cover', press_mates=len(mates), press_fits=len(PF),
                    missing=[list(m) for m in missing], stray=[list(s) for s in stray],
                    status='fail' if (missing or stray) else 'pass',
                    **({'error': 'press mates without exactly one PRESS_FITS row: %s; PRESS_FITS rows naming no press '
                                 'mate: %s' % (missing, stray)} if (missing or stray) else {})))
    final = set(final_ids(L))
    step_of = {s['step']: s for s in L.STEPS}
    snaps = [r for r in PF if r.get('retention') == 'snap']
    for r in PF:
        part, tgt, ret, where = r['part'], r['onto'], r.get('retention'), r.get('where')
        st = step_of.get(r.get('step'), {})
        row = dict(kind='press_fit', id='press_fit %s' % part, part=part, onto=tgt, retention=ret, where=where,
                   step=r.get('step'))
        errs = []
        bench = list(st.get('bench', [])) if st.get('in_body') is False else []
        if where == 'bench':
            present = set(bench)
        else:
            present = set(L.present_at(r.get('step'))) if st else set()
        snap_tgts = {x['onto'] for x in PF if x.get('retention') == 'snap'}
        if where == 'body' and ret not in ('rigid', 'held'):
            errs.append("a press made in the body must be 'rigid' or 'held', not %r" % ret)
        if ret in ('snap', 'rigid'):
            if tgt not in P or part not in P:
                errs.append('no solid for %s' % sorted({tgt, part} - set(P)))
            elif not r.get('axis'):
                errs.append('no press axis')
            else:
                d = tuple(HANDLING_DISP * a for a in r['axis'])
                riders = {x['part'] for x in PF if x['onto'] == tgt}
                excl = {part, tgt} | riders
                ids = sorted(i for i in P if i not in excl and (i in final or i in present))
                zones = [_hsolid(*[tuple(L.SNAP_TOOTH_ZONES[z][a][j] for a in 'xyz') for j in (0, 1)])
                         for z in r.get('snap_zones', [])]
                vols, verr = _press_volumes(P[tgt], d, P, ids, zones)
                errs += ['boolean failed: %s' % e for e in verr]
                rig = lambda pick: sum(max(0.0, v[1][0] - v[0][0]) for i, v in vols.items() if pick(i))   # noqa: E731
                v_rigid_final, v_rigid_press = rig(lambda i: i in final), rig(lambda i: i in present)
                v_zone = sum(max(0.0, v[1][1] - v[0][1]) for i, v in vols.items() if i in final)
                rest = {i: _r(v[0][0] + v[0][1], 3) for i, v in vols.items() if v[0][0] + v[0][1] > VOL_TOL}
                by_part = {i: _r(max(0.0, v[1][0] - v[0][0]), 3) for i, v in vols.items()
                           if v[1][0] - v[0][0] > VOL_TOL}
                row.update(V_rigid=_r(v_rigid_final, 3), V_rigid_press=_r(v_rigid_press, 3), V_zone=_r(v_zone, 3),
                           rest_overlap=rest, rigid_by_part=by_part, disp_mm=HANDLING_DISP, press_set=sorted(present))
                if ret == 'rigid' and v_rigid_press < HANDLING_RIGID_MIN:
                    errs.append('declared rigid but nothing present at the press backs the target (V_rigid %.3f < '
                                '%.2f mm3)' % (v_rigid_press, HANDLING_RIGID_MIN))
                if ret == 'snap':
                    if v_rigid_final >= HANDLING_SNAP_MAX:
                        errs.append('declared snap but backed: update PRESS_FITS (V_rigid %.3f mm3 outside the snap '
                                    'zones, %s)' % (v_rigid_final, by_part))
                    if v_zone <= HANDLING_ZONE_MIN:
                        errs.append('declared snap but no snap tooth engages (V_zone %.3f mm3)' % v_zone)
        if ret == 'snap':
            fa_p, fa_t = _first_add(L, part), _first_add(L, tgt)
            row.update(enters_body_step=fa_p, target_enters_step=fa_t)
            if not (where == 'bench' and st.get('in_body') is False and part in bench and tgt in bench
                    and fa_p is not None and fa_p == fa_t):
                errs.append('snap-retained target pressed in the body (press must be at a bench step whose bench list '
                            'holds %s and %s, the part entering the body with its target; first adds: %s / %s)'
                            % (part, tgt, fa_p, fa_t))
            movers = [e['id'] for e in list(L.INSERTIONS) + list(L.REMOVALS) if tgt in e.get('moving', [])]
            nc = [e['id'] for e in list(L.INSERTIONS) + list(L.REMOVALS)
                  if tgt in e.get('moving', []) and part not in e.get('moving', [])]
            row.update(carried_by=movers)
            if nc:
                errs.append('pressed part not carried with its target: %s' % nc)
            if tgt in P and part in P and r.get('axis') and r.get('backing_axis_d'):
                k = max(range(3), key=lambda j: abs(r['axis'][j]))
                sg = 1 if r['axis'][k] > 0 else -1
                tb, pb = bb_tuple(P[tgt]), bb_tuple(P[part])
                c = [(pb[2 * j] + pb[2 * j + 1]) / 2 for j in range(3)]
                start = tb[2 * k + 1] if sg > 0 else tb[2 * k]
                c[k] = start
                dv = [0.0, 0.0, 0.0]
                dv[k] = float(sg)
                col = cq.Solid.makeCylinder(r['backing_axis_d'] / 2, HANDLING_BACKING_LEN, V(*c), V(*dv))
                blocked = {}
                for i in bench:
                    if i == tgt or i not in P or not bb_overlap(bb_tuple(P[i]), bb_tuple(col)):
                        continue
                    v, _ = common(col, P[i])
                    if v != v or v > VOL_TOL:
                        blocked[i] = _r(v, 3)
                row.update(backing_column=dict(d=r['backing_axis_d'], start=_r(start, 3), length=HANDLING_BACKING_LEN,
                                               blocked=blocked))
                if blocked:
                    errs.append('backing access: the %.0f mm column behind the target holds %s mm3 of bench parts'
                                % (r['backing_axis_d'], blocked))
        elif ret == 'held':
            hs = r.get('holders') or []
            bad = [h for h in hs if h not in present or not any(
                key(a, b) == key(h, tgt) and k == 'contact' for a, b, k in L.MATES)]
            row.update(holders=hs)
            if not hs or bad:
                errs.append('held: holders not present at the press or without a contact mate to %s: %s'
                            % (tgt, bad or 'none listed'))
        elif ret == 'hand':     # P5-5: two loose parts pressed in the hands at the bench, nothing else
            fa_p, fa_t = _first_add(L, part), _first_add(L, tgt)
            if not (where == 'bench' and fa_p == r.get('step') and fa_t == r.get('step')
                    and part not in snap_tgts and tgt not in snap_tgts):
                errs.append("'hand' needs where='bench', both parts entering at the row's step (loose, not in the body)"
                            " and neither a snap target (first adds %s / %s)" % (fa_p, fa_t))
        elif ret != 'rigid':
            errs.append('unknown retention %r' % ret)
        row['status'] = 'fail' if errs else 'pass'
        if errs:
            row['error'] = '; '.join(errs)
        out.append(row)
    # ---- snap_basis: the in-use load cap of each snap row
    for r in snaps:
        part, tgt = r['part'], r['onto']
        data = getattr(L, tgt.upper(), None) or {}
        req = (data.get('push') or {}).get('required_travel_mm')
        row = dict(kind='snap_basis', id='snap_basis %s' % part, part=part, onto=tgt, required_travel_mm=req,
                   release_N=r.get('release_N'), release_min_N=r.get('release_min_N'))
        errs = []
        if req is not None:
            errs.append('push commissioned: firm pushes load the cradle hooks; build the contingency back-stop (%s) '
                        'and re-declare the row rigid' % r.get('contingency'))
        if r.get('release_N') is not None and r['release_N'] < r.get('release_min_N', 0.0):
            errs.append('G-ENC-1 below %.0f N (%.1f N): build the contingency (%s)'
                        % (r['release_min_N'], r['release_N'], r.get('contingency')))
        land_on = r.get('land_on', 'panel')
        ax = r.get('axis') or (0, 0, 0)
        if tuple(ax) != (0, -1, 0) or part not in P or land_on not in P:
            errs.append('land not measurable (Y-axis press with %s and %s solids needed)' % (part, land_on))
        else:
            kb = bb_tuple(P[part])
            y0 = kb[2] if ax[1] < 0 else kb[3]
            sg = 1 if ax[1] < 0 else -1          # into the knob from its land face
            lo, hi = (kb[0] - 1, min(y0, y0 + sg * LAND_SLAB), kb[4] - 1), (kb[1] + 1, max(y0, y0 + sg * LAND_SLAB), kb[5] + 1)
            a_land = common(P[part], _hsolid(lo, hi))[0] / LAND_SLAB
            g_p = sg * (y0 - L.YL)
            lo2, hi2 = (lo[0], min(y0, y0 + sg * LAND_PANEL_SLAB), lo[2]), (hi[0], max(y0, y0 + sg * LAND_PANEL_SLAB), hi[2])
            v2, s2 = common(P[part], _hsolid(lo2, hi2))
            a_panel = 0.0
            if s2 is not None and not isinstance(s2, str):
                dy = -sg * (g_p + 0.05 + LAND_PANEL_SLAB) if sg > 0 else -sg * (g_p + 0.05)
                a_panel = max(0.0, common(s2.translate(V(0, dy, 0)), P[land_on])[0]) / LAND_PANEL_SLAB
            row.update(A_land=_r(a_land, 1), A_panel=_r(a_panel, 1), gP=_r(g_p, 3), land_on=land_on,
                       rule='A_land >= %.0f mm2, A_panel >= %.1f A_land, gP <= %.2f' % (LAND_MIN_MM2, LAND_PANEL_FRAC,
                                                                                    LAND_GAP_MAX))
            if not (a_land == a_land and a_land >= LAND_MIN_MM2 and a_panel >= LAND_PANEL_FRAC * a_land
                    and g_p <= LAND_GAP_MAX):
                errs.append('knob land lost: A_land %.1f mm2, A_panel %.1f mm2, gP %.3f (needs >= %.0f, >= %.1f x '
                            'A_land, <= %.2f)' % (a_land, a_panel, g_p, LAND_MIN_MM2, LAND_PANEL_FRAC, LAND_GAP_MAX))
        row['status'] = 'fail' if errs else 'pass'
        if errs:
            row['error'] = '; '.join(errs)
        out.append(row)
    # ---- rest poses (BX-13)
    forbid = {r['part'] for r in PF} | {r['onto'] for r in PF if r.get('retention') == 'snap'} | {
        'lens', 'eyepiece', 'eyecup'}
    rems = {e['id']: e for e in L.REMOVALS}

    def pose_set(rp):
        if rp.get('removal'):
            rem = rems.get(rp['removal'])
            if rem is None:
                return None
            gone = set(rem.get('off', [])) | set(rp.get('remove_first', []))
            return [i for i in final_ids(L) if i not in gone]
        return list(L.present_at(rp['step']))

    def touching(ids, face):
        k, sg = _hface(face)
        ext = {i: bb_tuple(P[i])[2 * k + (1 if sg > 0 else 0)] for i in ids if i in P}
        if not ext:
            return None, {}, None, None
        E = max(ext.values()) if sg > 0 else min(ext.values())
        t = {i: _r(e, 3) for i, e in ext.items() if sg * (E - e) <= REST_TOUCH_MM}
        rest = {i: e for i, e in ext.items() if i not in t}
        nxt = (max(rest, key=lambda i: sg * rest[i]) if rest else None)
        return E, t, nxt, (_r(sg * (E - rest[nxt]), 3) if nxt else None)

    for rp in getattr(L, 'REST_POSES', []):
        ids = pose_set(rp)
        row = dict(kind='rest_pose', id='rest_pose %s' % rp['id'], down=rp['down'], screws=rp.get('screws', []),
                   step=rp.get('step'), removal=rp.get('removal'))
        errs = []
        if ids is None:
            errs.append('unknown removal %r' % rp.get('removal'))
            ids = []
        miss = sorted(i for i in ids if i not in P)
        if miss:
            errs.append('no solid for present ids %s' % miss)
        E, t, nxt, margin = touching(ids, rp['down'])
        row.update(extreme=_r(E, 3), touching=t, next_part=nxt, margin=margin)
        bad = sorted(set(t) & forbid)
        if bad:
            errs.append('rests on %s (a pressed part, a snap target, the lens, the eyepiece or the eyecup)' % bad)
        # r7 fix-up (VERIFY-C5): driver plane + static stability unless the row is hand-held
        row['support'] = rp.get('support')
        if rp.get('support') != 'hand' and E is not None:
            k_, sg_ = _hface(rp['down'])
            ext_of = lambda kk, ss: max(bb_tuple(P[i])[2 * kk + 1] for i in ids if i in P) if ss > 0 else \
                min(bb_tuple(P[i])[2 * kk] for i in ids if i in P)                        # noqa: E731
            scr = {s['id']: s for s in L.SCREWS}
            ov = rp.get('overhang')
            drows = [_rest_driver_row(L, scr[sid], k_, sg_, E, ext_of,
                                      ov if ov and sid in ov.get('for_screws', [sid]) else None)
                     for sid in rp.get('screws', []) if sid in scr]
            row['driver_plane'] = drows
            errs += [d['error'] for d in drows if d['status'] == 'fail']
            stab = _rest_stability_row(L, rows, P, ids, k_, sg_, E)
            row['stability'] = stab
            if stab['status'] == 'fail':
                errs.append(stab['error'])
        stop = rp.get('stop')
        if stop and E is not None:
            fk, fs = _hface(stop['face'])
            dk, ds = _hface(rp['down'])
            ok = [j for j in range(3) if j not in (fk, dk)][0]
            plane = L.YL if fk == 1 else None
            if plane is None or fs < 0:
                errs.append('stop slab implemented for the +Y face only')
            else:
                lo, hi = [0.0] * 3, [0.0] * 3
                lo[fk], hi[fk] = plane - 0.01, plane + HANDLING_BACKING_LEN
                lo[dk], hi[dk] = (E - stop['band_mm'], E) if ds > 0 else (E, E + stop['band_mm'])
                lo[ok], hi[ok] = stop['x']
                slab = _hsolid(lo, hi)
                sb = bb_tuple(slab)
                intr, bear, gaps = {}, [], {}
                lo_b = list(lo)
                lo_b[fk] = plane - 0.05
                bslab = _hsolid(lo_b, hi)
                for i in ids:
                    if i not in P:
                        continue
                    pb = bb_tuple(P[i])
                    if i in REST_STOP_ALLOWED:
                        if bb_overlap(pb, bb_tuple(bslab)) and common(P[i], bslab)[0] > VOL_TOL:
                            bear.append(i)
                        continue
                    if i in KNOB_IDS or i == 'eyepiece':
                        gaps[i] = _r(_bb_gap(pb, sb), 3)
                    if bb_overlap(pb, sb):
                        v, _ = common(P[i], slab)
                        if v != v or v > VOL_TOL:
                            intr[i] = _r(v, 3)
                row.update(stop=dict(slab=[_r(x, 3) for x in sb], intruders=intr, bearing=sorted(bear),
                                     clearance=gaps, band_mm=stop['band_mm'], x=list(stop['x'])))
                if intr:
                    errs.append('stop slab entered by %s (only %s may take the block)' % (intr, REST_STOP_ALLOWED))
                if not bear:
                    errs.append('no part reaches the face plane within 0.05 under the block (no bearing)')
        row['status'] = 'fail' if errs else 'pass'
        if errs:
            row['error'] = '; '.join(errs)
        out.append(row)
    # ---- rest_cover: every screw driven once a snap row's pressed part is in the body, and every screw unscrewed by
    #      a removal that moves a snap target, has a matching pose
    need, have_p = {}, set()
    for r in snaps:
        fa = _first_add(L, r['part'])
        for s in L.SCREWS:
            if fa is not None and s['step'] >= fa:
                need.setdefault(('step', s['step'], s['id']), 'driven at step %d' % s['step'])
        for e in L.REMOVALS:
            if r['onto'] in e.get('moving', []):
                for sid in e.get('unscrew', []):
                    need.setdefault(('removal', e['id'], sid), 'unscrewed by %s' % e['id'])
    for rp in getattr(L, 'REST_POSES', []):
        for sid in rp.get('screws', []):
            have_p.add(('removal', rp['removal'], sid) if rp.get('removal') else ('step', rp.get('step'), sid))
    unc = sorted('%s (%s)' % (k[2], v) for k, v in need.items() if k not in have_p)
    out.append(dict(kind='rest_cover', id='rest_cover', required=sorted('%s:%s:%s' % k for k in need),
                    uncovered=unc, status='fail' if unc else 'pass',
                    **({'error': 'screws without a REST_POSES row: %s' % unc} if unc else {})))
    # ---- info: what touches each forbidden face at steps 8-10
    for face, why in getattr(L, 'REST_FORBIDDEN', {}).items():
        for stp in (8, 9, 10):
            E, t, nxt, margin = touching(L.present_at(stp), face)
            out.append(dict(kind='rest_forbidden', id='rest_forbidden %s step %d' % (face, stp), face=face, step=stp,
                            touching=t, extreme=_r(E, 3), why=why, status='info'))
    return out


KNOB_IDS = ('knob_exp', 'knob_fps')


def check_release_access(L, rows):
    """FIXER r2 (M-V-MPS-2): straight-pin hold-open release. For each RELEASE_ACCESS entry a pin cylinder (pin_d) runs
    from `start` along `axis` to the tooth face + push. Pass: exact overlap <= VOL_TOL with every built part except the
    hook's own part, and the pin really meets that tooth (overlap > VOL_TOL at the push depth); beam strain at that
    push (1.5 t d / a^2, a = root to the land centre, x SNAP_KT) within HOOK max_strain."""
    out = []
    H = L.HOOK
    for a in getattr(L, 'RELEASE_ACCESS', []) or []:
        ax = np.array(a['axis'], float)
        p0 = np.array(a['start'], float)
        tip = np.array(a['tooth_face'], float) + ax * a['push']
        length = float(np.dot(tip - p0, ax))
        pin = cq.Solid.makeCylinder(a['pin_d'] / 2, length, V(*p0), V(*ax))
        hits, own = {}, None
        for pid, r in rows.items():
            if r.get('shape') is None:
                continue
            if not bb_overlap(bb_tuple(pin), bb_tuple(r['shape']), 0.05):
                continue
            v, _ = common(pin, r['shape'])
            if pid == a['part']:
                own = v
            elif v != v or v > VOL_TOL:
                hits[pid] = v if v != v else _r(v, 4)
        a_land = H['length'] - H['tooth'] / math.tan(math.radians(H['lead_deg'])) - H['land'] / 2
        e = 1.5 * H['t'] * a['push'] / a_land ** 2
        ok = not hits and own is not None and own > VOL_TOL and e * L.FDM['SNAP_KT'] <= H['max_strain']
        out.append(dict(id=a['id'], hook=a['hook'], tool=a['tool'], pin_d=a['pin_d'], push_mm=a['push'],
                        pin_length=_r(length, 2), overlap_other=hits,
                        overlap_tooth_mm3=None if own is None else _r(own, 4),
                        strain_nominal=_r(e, 4), strain_with_kt=_r(e * L.FDM['SNAP_KT'], 4),
                        strain_limit=H['max_strain'], status='pass' if ok else 'fail',
                        method='exact OCP common of the pin cylinder with each built part (final pose, hood fitted)'))
    return out


# ------------------------------------------------------------------------------------------- section views
def section_lines(shape, axis, at, n_curve=24):
    """B-rep section of shape by the plane axis = at (OCP BRepAlgoAPI_Section) -> list of 2D polylines in the two
    remaining axes (order x, y, z)."""
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
    from OCP.gp import gp_Dir, gp_Pln, gp_Pnt
    k = 'xyz'.index(axis)
    p, nrm = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
    p[k], nrm[k] = float(at), 1.0
    sec = BRepAlgoAPI_Section(shape.wrapped, gp_Pln(gp_Pnt(*p), gp_Dir(*nrm)), False)
    sec.Approximation(True)
    sec.Build()
    if not sec.IsDone():
        return []
    keep = [i for i in range(3) if i != k]
    lines = []
    for e in cq.Shape.cast(sec.Shape()).Edges():
        m = 2 if e.geomType() == 'LINE' else n_curve
        pts = [e.positionAt(t).toTuple() for t in np.linspace(0.0, 1.0, m)]
        lines.append([(q[keep[0]], q[keep[1]]) for q in pts])
    return lines


def _cli(argv=None):
    """Quick R3 checks without the full build: builds the printed modules (all, or --parts) + COTS, runs the selected
    r2 checks and prints them. Writes out/_quick/r3-quick.json (a working file, not a release output)."""
    import argparse
    import json
    import os
    import build_d2 as B
    import layout as L
    ap = argparse.ArgumentParser()
    ap.add_argument('--critical', action='store_true')
    ap.add_argument('--evf', action='store_true')
    ap.add_argument('--removals', action='store_true')
    ap.add_argument('--parts', help='comma list of printed ids to build (default: all)')
    a = ap.parse_args(argv)
    prow = {}
    if a.parts:
        for pid in a.parts.split(','):
            prow.update(B.build_printed(only=pid)[0])
    else:
        prow = B.build_printed()[0]
    rows = dict(B.build_cots(), **prow)
    res = {}
    if a.critical:
        res['critical_features'] = check_critical_features(L, rows)
        for x in res['critical_features']:
            print('%-6s %-9s %-30s %-10s %s %s' % (x['status'], x['kind'], x.get('id', ''), x['part'],
                                                  x.get('measured_mm', x.get('structural_entries', '')),
                                                  x.get('error') or ''))
    if a.evf:
        res['evf_restraint'] = check_evf_restraint(L, rows)
        for x in res['evf_restraint']:
            print('%-6s %-3s gap %s (%s) bears on %s' % (x['status'], x['direction'], x.get('gap_mm'),
                                                         x.get('arresting'), x.get('bears_on')))
    if a.removals:
        res['removals'], res['service_driver'] = check_removals(L, rows)
        for x in res['removals'] + res['service_driver']:
            print(x['status'], x.get('removal', x.get('screw')), x.get('hits'), x.get('errors', ''))
    qd = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', '_quick')
    os.makedirs(qd, exist_ok=True)
    with open(os.path.join(qd, 'r3-quick.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(res, f, indent=1, default=str)
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(_cli())


# ------------------------------------------------------------------------------------------- FIXER r2: stack retention
def _hull2(pts):
    pts = sorted(set(map(tuple, pts)))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


def _inside_margin(hull, p):
    """Signed distance from p to the nearest edge of a CCW convex hull (> 0 inside)."""
    d = []
    for i in range(len(hull)):
        a, b = np.array(hull[i], float), np.array(hull[(i + 1) % len(hull)], float)
        e = b - a
        n = np.array([-e[1], e[0]]) / np.linalg.norm(e)
        d.append(float(np.dot(np.array(p, float) - a, n)))
    return min(d)


def _max_lift(ret, bosses, target):
    """Max rigid-plane lift z = a + b x + c y at `target` with z(ret_i) <= g_i and z(boss_k) >= 0 (vertex
    enumeration of the 3-variable LP; None = unbounded)."""
    import itertools
    rows, rhs = [], []
    for (x, y), g in ret:
        rows.append([1.0, x, y]); rhs.append(g)
    for (x, y) in bosses:
        rows.append([-1.0, -x, -y]); rhs.append(0.0)
    A, bvec = np.array(rows), np.array(rhs)
    obj = np.array([1.0, target[0], target[1]])
    best = None
    for tri in itertools.combinations(range(len(A)), 3):
        M = A[list(tri)]
        if abs(np.linalg.det(M)) < 1e-9:
            continue
        v = np.linalg.solve(M, bvec[list(tri)])
        if np.all(A @ v <= bvec + 1e-7):
            z = float(obj @ v)
            best = z if best is None else max(best, z)
    # unbounded if a feasible direction raises the target: test d with A d <= 0 and obj d > 0 on a coarse sphere
    for th in np.linspace(0, np.pi, 19):
        for ph in np.linspace(0, 2 * np.pi, 37):
            d = np.array([np.cos(th), np.sin(th) * np.cos(ph) / 50.0, np.sin(th) * np.sin(ph) / 50.0])
            if np.all(A @ d <= 1e-9) and obj @ d > 1e-6:
                return None
    return best


def check_stack_retention(L, rows):
    """FIXER r2 (verifier M-V-MPS-4). The Pi stack (pi5, x1203, kit, cooler) sits on its 4 boss pockets; the keeper
    fingers (gap_z) and the hood stack stop (gap) only limit lift. Pass: (1) the stack CoM in plan lies inside the hull
    of the retention points; (2) the measured gap at the hood post is 0.1-0.3 (exact distance); (3) the largest rigid
    lift at any of the 4 boss pockets that the retention gaps allow (LP over small rigid motions) is <= pocket depth -
    0.5, so every kit head keeps >= 0.5 in its pocket."""
    K, S = L.PI_KEEPER, getattr(L, 'HOOD_STACK_STOP', None)
    pts = []
    for f in K['fingers']:
        p = (L.PI['x'][0], f['at']) if f['edge'] == 'usb' else (f['at'], L.PI['y'][1])
        pts.append((p, K['gap_z']))
    if S is not None:
        pts.append((tuple(S['head']), S['gap']))
    ids = S['stack'] if S else ['pi5', 'x1203', 'x1203_kit', 'cooler']
    m, mx, my = 0.0, 0.0, 0.0
    for i in ids:
        r = rows.get(i, {})
        sh = r.get('shape')
        mass = r.get('mass') or (L.COTS.get(i, {}) or {}).get('mass') or 0.0
        if sh is None or not mass:
            continue
        c = (sh.val() if hasattr(sh, 'val') else sh).Center()
        m, mx, my = m + mass, mx + mass * c.x, my + mass * c.y
    com = (mx / m, my / m) if m else None
    hull = _hull2([p for p, _ in pts])
    margin = None if com is None or len(hull) < 3 else _inside_margin(hull, com)
    gap = None
    if S is not None and rows.get('hood', {}).get('shape') is not None and rows.get('x1203_kit', {}).get('shape') is not None:
        hb, (hx, hy) = S['post'], S['head']
        hz = S['head_top_z']
        h = _own_copy(rows['hood']['shape']).intersect(cq.Solid.makeBox(
            hb['x'][1] - hb['x'][0] + 2, hb['y'][1] - hb['y'][0] + 2, 3.0, V(hb['x'][0] - 1, hb['y'][0] - 1, hz)))
        k = _own_copy(rows['x1203_kit']['shape']).intersect(cq.Solid.makeBox(6.0, 6.0, 3.0, V(hx - 3, hy - 3, hz - 2.5)))
        try:
            gap = float(h.distance(k)) if h.Volume() > 1e-6 and k.Volume() > 1e-6 else None
        except Exception:  # noqa: BLE001
            gap = None
    lifts = {}
    for (bx, by) in L.PI['holes']:
        lifts['(%.1f, %.1f)' % (bx, by)] = _max_lift(pts, [h for h in L.PI['holes'] if h != (bx, by)], (bx, by))
    allow = L.PI_BOSS['head_pocket_depth'] - 0.5
    ok_lift = all(v is not None and v <= allow + 1e-6 for v in lifts.values())
    ok_gap = S is None or (gap is not None and 0.1 - 1e-3 <= gap <= 0.3 + 1e-3)
    ok = margin is not None and margin > 0 and ok_lift and ok_gap
    return [dict(check='stack retention', retention_points=[[_r(p[0], 1), _r(p[1], 1), g] for p, g in pts],
                 stack_com_xy=None if com is None else [_r(com[0], 1), _r(com[1], 1)],
                 com_inside_hull_margin_mm=None if margin is None else _r(margin, 1),
                 post_gap_mm=None if gap is None else _r(gap, 3), post_gap_window=[0.1, 0.3],
                 max_lift_at_bosses_mm={k: (None if v is None else _r(v, 3)) for k, v in lifts.items()},
                 lift_allowed_mm=allow, status='pass' if ok else 'fail',
                 method='CoM from proxy solids x listed masses; convex hull; exact OCP distance; LP vertex enumeration '
                        'over small rigid motions (z = a + b x + c y) with boss contacts z >= 0 and retention z <= gap')]


# =========================================================================================== r5 (J7-R) lens support
# R5-BRIEF choices 8-10, judge 3 s6.9 / s11, judge 1 s6.4. The lens collar carries the lens on its fixed band and sets
# its axial position on the 45 deg cone; the camera (body, BFAR, adapter) hangs on the lens and touches no chassis part;
# the tub lip, hood tab catch (r7 C4; was the roll fin) and panel keeper are catches with gaps. LOAD_MODEL (layout) holds the load estimates until
# G-COL-1 / G-CAM-2. 'info' rows with a `warn` text are the brief's WARNs (they neither pass nor block a category).
J7_FLOAT_RULES = {        # r5 (judge 3 s6.9): min gaps, mm. lateral = obstacle material level with the mover (inside its
    #  x range); axial = obstacle material in the mover's y/z shadow, ahead of or behind it; overall = plain minimum,
    #  floor = the smaller stated rule (a diagonal gap below both FAILs too)
    'body': dict(lateral=0.5, axial=0.4),      # housing + tab + lock-screw heads (both sides) + PCB + cover
    'bfar': dict(lateral=0.6, axial=0.4),      # BFAR head (+ exposed thread at s > 0): counterbore radial, lip axial
    'adapter': dict(lateral=0.6, axial=None),  # C-CS adapter (rides with the lens): lip and plate bore, radial
}
J7_FLOAT_EXCLUDE = ('gs_camera', 'c_cs_adapter', 'lens')   # the hanging unit itself; the camera's FPC has no solid
J7_TOL = 1e-3             # numeric tolerance on a stated gap (OCP distance noise), never a rule change
J7_REACH = 6.0            # obstacles farther than this from every mover are not measured (they cannot set a minimum)


def _mk_box(lo, hi):
    return cq.Solid.makeBox(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2], V(*lo))


def _crop(shape, lo, hi):
    """r5: exact local crop of shape to the box lo..hi (own copy, see check_bosses); None if nothing is inside."""
    if any(h - l <= 1e-6 for l, h in zip(lo, hi)):
        return None
    try:
        c = _own_copy(shape).intersect(_mk_box(lo, hi))
        return c if c.Volume() > 1e-6 else None
    except Exception:  # noqa: BLE001
        return None


def _dist(a, b):
    return None if b is None else float(a.distance(b))


def _float_gaps(m, ob):
    """r5: overlap and min gaps (overall / lateral / axial, J7_FLOAT_RULES) of mover m to the obstacle piece ob."""
    v, _ = common(m, ob)
    if v != v or v > VOL_TOL:                  # nan = boolean failure: treated as a clash, never as a pass
        return dict(overlap_mm3=_r(v, 4), overall=0.0, lateral=0.0, axial=0.0)
    b, e, F = bb_tuple(m), 0.05, J7_REACH
    lat = _crop(ob, (b[0] + e, b[2] - F, b[4] - F), (b[1] - e, b[3] + F, b[5] + F))
    axl = [_crop(ob, (b[0] - F, b[2] + e, b[4] + e), (b[0], b[3] - e, b[5] - e)),
           _crop(ob, (b[1], b[2] + e, b[4] + e), (b[1] + F, b[3] - e, b[5] - e))]
    ax = [d for d in (_dist(m, o) for o in axl) if d is not None]
    return dict(overlap_mm3=_r(v, 4), overall=_r(_dist(m, ob)), lateral=_r(_dist(m, lat)),
                axial=_r(min(ax)) if ax else None)


def _float_row(name, s, m, obstacles, rule):
    """r5: one mover at one s against the cropped obstacles -> row with per-obstacle gaps and the minima."""
    per, worst, over = {}, dict(overall=None, lateral=None, axial=None), []
    mb = bb_tuple(m)
    for oid, ob in obstacles.items():
        if ob is None or not bb_overlap(mb, bb_tuple(ob), J7_REACH):
            continue
        g = _float_gaps(m, ob)
        per[oid] = g
        if g['overlap_mm3'] is None or g['overlap_mm3'] != g['overlap_mm3'] or g['overlap_mm3'] > VOL_TOL:
            over.append(oid)
        for k in worst:
            if g[k] is not None and (worst[k] is None or g[k] < worst[k][0]):
                worst[k] = (g[k], oid)
    floor = min(x for x in rule.values() if x is not None)
    probs = ['overlaps %s' % o for o in over]
    # Retain every offending partner, not just the worst gap: a closer stub must not hide a second, real fault.
    offending = set(over)
    for k, need in (('lateral', rule['lateral']), ('axial', rule['axial']), ('overall', floor)):
        if need is not None:
            offending.update(oid for oid, g in per.items() if g[k] is not None and g[k] < need - J7_TOL)
        if need is not None and worst[k] is not None and worst[k][0] < need - J7_TOL:
            probs.append('%s gap %.3f to %s < %.2f' % (k, worst[k][0], worst[k][1], need))
    mins = {'min_' + k: (None if worst[k] is None else dict(gap=worst[k][0], to=worst[k][1])) for k in worst}
    row = dict(kind='j7_float', mover=name, s=s, rule=dict(rule, overall=floor), per_obstacle=per,
               offending_obstacles=sorted(offending),
               status='fail' if probs else 'pass', **mins)
    if not per:
        probs.append('no obstacle within %.1f mm: the float is not measured' % J7_REACH)
        row['status'] = 'fail'
    if probs:
        row['error'] = '; '.join(probs)
    return row


J7_S_STEP = 0.25         # r6 (audit 2026-10-06 L2): back-focus samples <= 0.25 apart over the whole s_range (+ s_nom)
J7_LENS_GAP = 0.5        # r6 (L4): lens to every part but its collar, the adapter and the camera (the hanging unit)
J7_RUNNING = 0.1         # r6 (X2): least lateral running clearance left after the declared centring stack


def j7_s_values(L, step=J7_S_STEP):
    """r6 (L2): s_range sampled at <= step (both ends included) plus s_nom. A clash between two samples of the old
    0 / nominal / max set passed (planted at s 2.0); the BFAR head is only 1.2 long against 3.0 of travel."""
    lo, hi = (float(v) for v in L.CAM['s_range'])
    n = max(1, int(math.ceil((hi - lo) / step - 1e-9)))
    vals = {round(lo + (hi - lo) * i / n, 6) for i in range(n + 1)}
    vals.add(round(float(L.CAM['s_nom']), 6))
    return tuple(sorted(vals))


def _centring_rows(L, out):
    """r6 (audit 2026-10-06 X2): the float gaps are measured with the collar bore exactly on the lip axis. Subtract the
    declared lateral centring stack (COLLAR['gauge'], with the centring gauge) and, for obstacles on the hood, the
    hood-to-tub location (HOOD_TO_TUB_LATERAL); FAIL below J7_RUNNING. The stack without the gauge is reported."""
    g = L.COLLAR.get('gauge') or {}
    hood_tol = getattr(L, 'HOOD_TO_TUB_LATERAL', 0.25)
    worst = {}
    for r in out:
        if r.get('mover') not in ('body', 'bfar', 'adapter'):
            continue
        for oid, gp in (r.get('per_obstacle') or {}).items():
            if gp.get('lateral') is None:
                continue
            k = (r['mover'], oid)
            if k not in worst or gp['lateral'] < worst[k][0]:
                worst[k] = (gp['lateral'], r.get('s'))
    stack = g.get('centring_worst_mm')
    bare = (g.get('stack_without_gauge') or {}).get('worst_mm')
    rows = []
    for (mv, oid), (gap, s) in sorted(worst.items()):
        extra = hood_tol if oid == 'hood' else 0.0
        left = None if stack is None else gap - stack - extra
        ok = left is not None and left >= J7_RUNNING - J7_TOL
        rows.append(dict(kind='j7_float', mover='centring', item='lateral_stack', of=mv, obstacle=oid, s=s,
                         lateral_gap=_r(gap), stack_mm=stack, hood_to_tub_mm=extra or None,
                         remaining_mm=None if left is None else _r(left),
                         remaining_without_gauge_mm=None if bare is None else _r(gap - bare - extra),
                         rule='remaining >= %.2f' % J7_RUNNING, status='pass' if ok else 'fail',
                         **({} if ok else {'error': 'centring stack %s leaves %s mm lateral to %s (need >= %.2f)'
                                                    % (stack, None if left is None else _r(left), oid, J7_RUNNING)})))
    if not rows:
        rows.append(dict(kind='j7_float', mover='centring', item='lateral_stack', status='fail',
                         error='no lateral gap measured (the float is not measured): the centring stack cannot be '
                               'checked'))
    return rows


def check_j7_float(L, rows, s_values=None, parts_of=None):
    """r5 (J7-R, judge 3 s6.9; a J7 required check): over the BFAR screw-out range (r6, L2: every J7_S_STEP plus s_nom)
    the camera body and BFAR (cots.gs_camera_parts at s) and the C-CS adapter keep the J7_FLOAT_RULES gaps to every
    printed part, COTS proxy and screw of the final state except the hanging unit itself (J7_FLOAT_EXCLUDE). The lens
    overlaps nothing but the collar, keeps >= J7_LENS_GAP to every other part (r6, L4) and never overlaps the camera.
    A missing lens solid is a FAIL row, never a skipped one (r6, L3). r6 (X2): the lateral gaps less the declared
    centring stack keep >= J7_RUNNING. parts_of(L, s) replaces cots.gs_camera_parts (tests). Per-s minima are rows."""
    import cots
    parts_of = parts_of or cots.gs_camera_parts
    s_values = tuple(s_values if s_values is not None else j7_s_values(L))
    cams = {s: parts_of(L, s) for s in s_values}
    ad = rows.get('c_cs_adapter', {}).get('shape') or cots.c_cs_adapter(L, None)
    mv = [bb_tuple(cams[s][k]) for s in s_values for k in ('body', 'bfar')] + [bb_tuple(ad)]
    lo = tuple(min(b[2 * i] for b in mv) - J7_REACH for i in range(3))
    hi = tuple(max(b[2 * i + 1] for b in mv) + J7_REACH for i in range(3))
    zone = (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])
    obs = {i: _crop(r['shape'], lo, hi) for i, r in rows.items()
           if i not in J7_FLOAT_EXCLUDE and r.get('shape') is not None and bb_overlap(bb_tuple(r['shape']), zone)}
    out = [_float_row(nm, s, cams[s][nm], obs, J7_FLOAT_RULES[nm]) for s in s_values for nm in ('body', 'bfar')]
    out.append(_float_row('adapter', None, ad, obs, J7_FLOAT_RULES['adapter']))
    out += _centring_rows(L, out)
    lens = rows.get('lens', {}).get('shape')
    if lens is None:          # r6 (L3): the lens rows are part of the check; their absence is a fault
        out.append(dict(kind='j7_float', mover='lens', s=None,
                        status='stub' if rows.get('lens', {}).get('stub') else 'fail',
                        error='lens solid not provided: lens overlap, lens gap and lens-vs-camera rows not measured'))
    else:                     # the lens overlaps nothing but the collar (judge 3 s6.9)
        hits, gaps = {}, {}
        lb = bb_tuple(lens)
        for i, r in rows.items():
            if i in ('lens', 'lens_collar', 'gs_camera', 'c_cs_adapter') or r.get('shape') is None:
                continue
            if not bb_overlap(lb, bb_tuple(r['shape']), J7_LENS_GAP + 0.5):
                continue
            v, _ = common(lens, r['shape'])
            if v != v or v > VOL_TOL:
                hits[i] = _r(v, 4)
                gaps[i] = 0.0
                continue
            # r6 (L4): a 0-gap contact is a second support path for the floating unit, not a pass
            lo2 = tuple(lb[2 * k] - J7_LENS_GAP - 1.0 for k in range(3))
            hi2 = tuple(lb[2 * k + 1] + J7_LENS_GAP + 1.0 for k in range(3))
            piece = _crop(r['shape'], lo2, hi2)
            if piece is not None:
                gaps[i] = _r(float(lens.distance(piece)), 4)
        out.append(dict(kind='j7_float', mover='lens', s=None, overlaps=hits, status='fail' if hits else 'pass',
                        rule='lens overlaps nothing but lens_collar (<= %.2f mm3)' % VOL_TOL,
                        **({'error': 'lens overlaps %s' % sorted(hits)} if hits else {})))
        near = {i: g for i, g in gaps.items() if g < J7_LENS_GAP - J7_TOL}
        out.append(dict(kind='j7_float', mover='lens', item='min_gap', s=None, gaps=gaps,
                        rule='lens >= %.2f to every part but lens_collar, c_cs_adapter and gs_camera' % J7_LENS_GAP,
                        status='fail' if near else 'pass', offending_obstacles=sorted(near),
                        **({'error': 'lens within %.2f of %s' % (J7_LENS_GAP, near)} if near else {})))
        for s in s_values:    # one hanging unit, but the lens rear cell must not clash with the camera at any s
            v = max(common(lens, cams[s][k])[0] for k in ('body', 'bfar'))
            ok = v == v and v <= VOL_TOL
            out.append(dict(kind='j7_float', mover='lens_vs_camera', s=s, overlap_mm3=_r(v, 4),
                            status='pass' if ok else 'fail',
                            **({} if ok else {'error': 'lens rear overlaps the camera at s %.2f' % s})))
    for r in out:             # Only faults caused entirely by stub obstacles can be attributed to stubs.
        offenders = r.get('offending_obstacles', list(r.get('overlaps', {})))
        if r['status'] == 'fail' and offenders and all(rows.get(p, {}).get('stub') for p in offenders):
            r['status'] = 'stub'
    return out


# =========================================================================================== r7 C4 (BX-4) roll catch
RC_VOL = 1e-5             # mm3: overlap growth over the 0-deg value that counts as contact (mesh boolean)
RC_MESH = 0.01            # mm: mover tessellation (the head-disc top sets the contact; 0.05 would cost ~0.008 deg)
RC_TAB_PAD = 0.5          # mm: a metal contact is 'on the tab catch' inside tab_catch_boxes() + this pad


def _rc_matrix(deg, c, off):
    """r7 C4: 3x4 matrix p -> R(p - c) + c + off (rotation about the x axis through c, then the case offset)."""
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    R = np.array([[1.0, 0.0, 0.0], [0.0, ca, -sa], [0.0, sa, ca]])
    c = np.asarray(c, float)
    return np.hstack([R, (c + np.asarray(off, float) - R @ c)[:, None]])


def _rc_bbo(a, b):
    return all(a[i] <= b[i + 3] and b[i] <= a[i + 3] for i in range(3))     # manifold boxes (min xyz, max xyz)


class _RCScan:
    """r7 C4: first contact of a mover (manifold, built on the nominal axis c0) rotated about the x axis through
    c0 + off against obstacle pieces [(id, manifold, box)]: coarse `step` up to `tmax`, then bisection to `tol`."""
    def __init__(self, obs, step, tmax, tol):
        self.obs, self.step, self.tmax, self.tol, self.n = obs, step, tmax, tol, 0

    def _hits(self, mv, c0, off, deg, base):
        m = mv.transform(_rc_matrix(deg, c0, off))
        mb = m.bounding_box()
        out = []
        for k, (pid, om, ob) in enumerate(self.obs):
            if not _rc_bbo(mb, ob):
                continue
            inter = m ^ om
            self.n += 1
            v = inter.volume()
            if v - base[k] > RC_VOL + 1e-6 * base[k]:
                out.append((pid, inter))
        return out

    def first(self, mv, c0, off, dirn, tmax=None):
        tmax = self.tmax if tmax is None else tmax
        m0 = mv.transform(_rc_matrix(0.0, c0, off))
        mb0 = m0.bounding_box()
        base = [(m0 ^ om).volume() if _rc_bbo(mb0, ob) else 0.0 for _, om, ob in self.obs]
        prev, a = 0.0, self.step
        while a <= tmax + 1e-9:
            h = self._hits(mv, c0, off, dirn * a, base)
            if h:
                lo, hi = prev, a
                while hi - lo > self.tol:
                    mid = (lo + hi) / 2
                    hm = self._hits(mv, c0, off, dirn * mid, base)
                    if hm:
                        hi, h = mid, hm
                    else:
                        lo = mid
                return round(hi, 3), h
            prev, a = a, a + self.step
        return None, []


def _rc_assembly_text(path=None):
    """r7 C4: ASSEMBLY.md hand-written lines (outside the generated <!-- BEGIN:x --> .. <!-- END:x --> blocks, which
    make_tables regenerates from STEPS: STEPS is linted directly and make_tables --check catches a stale block)."""
    import os
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ASSEMBLY.md')
    if not os.path.exists(path):
        return None
    out, gen = [], False
    with open(path, encoding='utf-8') as fh:
        for n, line in enumerate(fh, 1):
            if line.startswith('<!-- BEGIN:'):
                gen = True
            elif line.startswith('<!-- END:'):
                gen = False
            elif not gen:
                out.append(('ASSEMBLY.md:%d' % n, line))
    return out


def _rc_guide_text(paths=None):
    """r7 fix-up (VERIFY-C4): every string literal (implicit concatenations joined by the parser) of the hand-written
    guide sources guide/guide_steps.py and guide/build_guide.py, which the published guide is built from."""
    import ast
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    out = []
    for p in paths or [os.path.join(here, 'guide', 'guide_steps.py'), os.path.join(here, 'guide', 'build_guide.py')]:
        if not os.path.exists(p):
            continue
        with open(p, encoding='utf-8') as fh:
            tree = ast.parse(fh.read())
        out += [('%s:%d' % (os.path.basename(p), n.lineno), n.value) for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    return out


def _rc_paragraphs(lines):
    """r7 fix-up: join hard-wrapped hand-written lines into paragraphs (whitespace collapsed) so that a phrase split
    over a line break is still matched; the paragraph keeps its first line's label."""
    out, cur, lab = [], [], None
    for w, t in lines:
        if t.strip():
            lab = lab or w
            cur.append(t.strip())
        elif cur:
            out.append((lab, ' '.join(' '.join(cur).split())))
            cur, lab = [], None
    if cur:
        out.append((lab, ' '.join(' '.join(cur).split())))
    return out


def lens_turn_back_lint(L):
    """r7 fix-up (VERIFY-C4): for every INSERTIONS record with a `hold` (the lens thread is reacted by the tab catch),
    the action text of its step turns lens and camera back off the catch (L.LENS_TURN_BACK) before s_c4 is snugged:
    otherwise the camera is clamped resting on a tine and the J7-R float is defeated. -> list of problems."""
    phrase = getattr(L, 'LENS_TURN_BACK', None)
    probs = []
    for r in L.INSERTIONS:
        if not r.get('hold'):
            continue
        st = next((s for s in L.STEPS if s['step'] == r['step']), None)
        txt = (st or {}).get('action', '').lower()
        snug = txt.find('snug s_c4')
        tb = txt.find(phrase.lower()) if phrase else -1
        if snug < 0:
            probs.append('STEPS[%s]: no "snug s_c4" for hold record %s' % (r['step'], r['id']))
        elif tb < 0 or tb > snug:
            probs.append('STEPS[%s]: no turn-back sentence ("%s") before "snug s_c4" (record %s)'
                         % (r['step'], phrase, r['id']))
    return probs


def lens_hold_lint(L, assembly_path=None, guide_paths=None):
    """r7 C4 (SPEC-C4 4.1, from design A): STEPS, LATCH_FREE, the ASSEMBLY.md hand-written text (per line and per
    joined paragraph) and the guide sources' string literals (r7 fix-up) contain none of LENS_HOLD_FORBIDDEN
    (case-insensitive) -> list of (where, phrase); None for a missing ASSEMBLY.md."""
    texts = [('STEPS[%s].%s' % (st.get('step'), k), st[k]) for st in L.STEPS for k in ('name', 'tool', 'action')
             if isinstance(st.get(k), str)]
    texts += [('LATCH_FREE[%s]' % k, v) for k, v in L.LATCH_FREE.items() if isinstance(v, str)]
    asm = _rc_assembly_text(assembly_path)
    texts += asm or []
    texts += _rc_paragraphs(asm or [])
    texts += _rc_guide_text(guide_paths)
    bad = sorted({(w, p) for w, t in texts for p in getattr(L, 'LENS_HOLD_FORBIDDEN', ())
                  if p.lower() in ' '.join(t.split()).lower()})
    return bad, asm is not None


def check_roll_catch(L, rows, s_values=None, parts_of=None, assembly_path=None):
    """r7 C4 (BX-4, SPEC-C4 4.1; J7 family). A lens thread is turned with nobody holding the camera: the camera
    (cots.gs_camera_parts 'metal' = housing + tab + heads, 'pcb_cover' = PCB + cover) turns about its own axis,
    displaced by the case offset, until it meets something. For every s of j7_s_values, offsets (dy, dz) in
    {0, +-lat} (lat = COLLAR gauge centring_worst_mm + HOOD_TO_TUB_LATERAL) and, for records with a `hold`, the
    lens-out sag (0 / +-lat, -sag; sag = (cb_d - BFAR d) / 2), both directions, against every final-state solid
    (printed, COTS, screws; the hanging unit excluded) and every COTS box (mesh booleans, coarse step + bisection):
    first_contact: metal lands on the hood tab catch first, PCB/cover >= metal + margin_deg (or never within scan_deg);
    first_contact_unconfirmed (head_side 'both' only): one-head variants '+Y' / '-Y', margin_unconfirmed_deg;
    window: metal to hood (exact OCP distance) at +-window_deg in the final state >= window_gap centred and
    >= J7_RUNNING at the worst offset; tine_strength (estimate): F = torque / least contact radius, cantilever from
    the lowest contact z to the band; axial_engagement: head (bare side: tab) x-overlap with the tine >= axial_min at
    lip +lip_gap / final / keeper; lens_hold: every INSERTIONS / REMOVALS record moving 'lens' has a `hold` whose
    feature exists and whose first_contact rows pass, plus the LENS_HOLD_FORBIDDEN text lint."""
    import time as _time
    import cots
    t_start = _time.time()
    P = L.ROLL_CATCH
    parts_of = parts_of or cots.gs_camera_parts
    out = []
    tc = L.HOOD.get('tab_catch') or {}
    side = tc.get('head_side', 'both')
    try:
        tcb = L.tab_catch_boxes(L)
        geo_err = None if tcb else "HOOD has no tab_catch: nothing reacts the lens thread through metal"
    except ValueError as e:
        tcb, geo_err = [], 'tab_catch_boxes: %s' % e
    out.append(dict(kind='roll_catch', item='tab_catch_geometry', boxes=len(tcb), head_side=side,
                    bare_y=tc.get('bare_y'), gap=tc.get('gap'), status='fail' if geo_err else 'pass',
                    **({'error': geo_err} if geo_err else {})))
    cw = (L.COLLAR.get('gauge') or {}).get('centring_worst_mm')
    lat = round(cw + getattr(L, 'HOOD_TO_TUB_LATERAL', 0.25), 4) if cw is not None else 0.0
    sag = round((L.CAM['cb_d'] - L.CAM['bfar']['d']) / 2, 4)
    if cw is None:
        out.append(dict(kind='roll_catch', item='offsets', status='fail',
                        error='COLLAR gauge centring_worst_mm not declared: the lateral case offset is unknown'))
    recs = [('INSERTIONS', r) for r in L.INSERTIONS if 'lens' in r.get('moving', [])]
    recs += [('REMOVALS', r) for r in registry(L, 'REMOVALS') if 'lens' in r.get('moving', [])]
    holds = [r for _, r in recs if r.get('hold')]
    cases = [(0.0, 0.0, False), (lat, 0.0, False), (-lat, 0.0, False), (0.0, lat, False), (0.0, -lat, False)]
    if holds:
        cases += [(0.0, -sag, True), (lat, -sag, True), (-lat, -sag, True)]
    s_values = tuple(s_values if s_values is not None else j7_s_values(L))
    variants = ['declared'] + (['+Y', '-Y'] if side == 'both' else [])
    c0 = (0.0, float(L.LENS_AXIS[0]), float(L.LENS_AXIS[1]))
    cams = {}
    for s in s_values:
        for v in variants:
            hs = side if v == 'declared' else v
            cams[(s, v)] = parts_of(L, s) if hs == 'both' else parts_of(L, s, head_side=hs)
    if any('metal' not in p or 'pcb_cover' not in p for p in cams.values()):
        out.append(dict(kind='roll_catch', item='camera_parts', status='fail',
                        error="gs_camera_parts gives no 'metal' / 'pcb_cover' sub-solids: the roll is not measured"))
        return out
    # obstacles: final-state solids + COTS boxes, cropped to the zone the turning camera can reach
    bbs = [bb_tuple(p[k]) for p in cams.values() for k in ('metal', 'pcb_cover')]
    rmax = max(math.hypot(y - c0[1], z - c0[2]) for b in bbs for y in (b[2], b[3]) for z in (b[4], b[5]))
    rr = rmax + lat + max(lat, sag) + 1.0
    lo = (min(b[0] for b in bbs) - 1.0, c0[1] - rr, c0[2] - rr)
    hi = (max(b[1] for b in bbs) + 1.0, c0[1] + rr, c0[2] + rr)
    zone = (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])
    src = {i: r['shape'] for i, r in rows.items()
           if i not in J7_FLOAT_EXCLUDE and r.get('shape') is not None and bb_overlap(bb_tuple(r['shape']), zone)}
    for k, c in L.COTS.items():
        b = c.get('box') if isinstance(c, dict) else None
        if b and k not in J7_FLOAT_EXCLUDE and k in rows:
            bt = box_bb(b)
            if bb_overlap(bt, zone):
                src['box:' + k] = _mk_box((bt[0], bt[2], bt[4]), (bt[1], bt[3], bt[5]))
    obs = []
    for oid, shp in sorted(src.items()):
        piece = _crop(shp, lo, hi)
        mf = None if piece is None else manifold_of(piece)
        if mf is None:
            continue
        for pc in mf.decompose():
            obs.append((oid, pc, pc.bounding_box()))
    scan = _RCScan(obs, P['step_deg'], P['scan_deg'], P['tol'])
    mesh = {k: {m: manifold_of_tol(p[m], RC_MESH, MESH_ANG) for m in ('metal', 'pcb_cover')} for k, p in cams.items()}

    def on_catch(pid, pt):
        return pid == 'hood' and any(all(b[a][0] - RC_TAB_PAD <= pt[i] <= b[a][1] + RC_TAB_PAD
                                         for i, a in enumerate('xyz')) for b in tcb)

    def contact(h, off):
        res = []
        for pid, inter in h:
            bb = inter.bounding_box()
            pt = tuple((bb[i] + bb[i + 3]) / 2 for i in range(3))
            res.append(dict(to=pid, at=[_r(x, 2) for x in pt], on_tab_catch=on_catch(pid, pt),
                            r=_r(math.hypot(pt[1] - c0[1] - off[1], pt[2] - c0[2] - off[2]), 3),
                            lever=_r(abs(pt[2] - c0[2] - off[2]), 3), z_low=_r(bb[2], 3)))
        return res

    fc_rows, contacts = [], []
    for s in s_values:
        pcb_res = {}
        for dy, dz, hold in cases:
            for dirn in (1, -1):
                pcb_res[(dy, dz, dirn)] = scan.first(mesh[(s, 'declared')]['pcb_cover'], c0, (0.0, dy, dz), dirn)
        for v in variants:
            margin = P['margin_deg'] if v == 'declared' else P['margin_unconfirmed_deg']
            res, errs = [], []
            for dy, dz, hold in cases:
                off = (0.0, dy, dz)
                for dirn in (1, -1):
                    am, hm = scan.first(mesh[(s, v)]['metal'], c0, off, dirn)
                    ap, hp = pcb_res[(dy, dz, dirn)]
                    cm, cp = contact(hm, off), contact(hp, off)
                    contacts += [dict(c, variant=v, s=s) for c in cm]
                    case = dict(dy=dy, dz=dz, dir=dirn, lens_out=hold, metal_deg=am,
                                metal_to=sorted({c['to'] for c in cm}), pcb_cover_deg=ap,
                                pcb_cover_to=sorted({c['to'] for c in cp}),
                                margin_deg=None if am is None or ap is None else _r(ap - am, 3))
                    tag = 's %.2f dy %+.2f dz %+.2f dir %+d' % (s, dy, dz, dirn)
                    if am is None:
                        errs.append('%s: no metal catch within %.1f deg (PCB/cover first: %s at %s)'
                                    % (tag, P['scan_deg'], case['pcb_cover_to'] or 'nothing', ap))
                    elif not cm or not all(c['on_tab_catch'] for c in cm):
                        errs.append('%s: metal first meets %s at %.2f deg, not the hood tab catch'
                                    % (tag, [(c['to'], c['at']) for c in cm], am))
                    if ap is not None and (am is None or ap < am + margin - 1e-9):
                        errs.append('%s: PCB/cover meets %s at %.2f deg before metal + %.1f (metal %s)'
                                    % (tag, case['pcb_cover_to'], ap, margin, am))
                    res.append(case)
            ms = [c['metal_deg'] for c in res if c['metal_deg'] is not None]
            mg = [c['margin_deg'] for c in res if c['margin_deg'] is not None]
            row = dict(kind='roll_catch', item='first_contact' if v == 'declared' else 'first_contact_unconfirmed',
                       variant=v, s=s, metal_min_deg=min(ms) if ms else None, metal_max_deg=max(ms) if ms else None,
                       centred_deg=next((c['metal_deg'] for c in res if c['dy'] == 0 and c['dz'] == 0
                                         and c['dir'] == 1), None),
                       pcb_cover_min_deg=min((c['pcb_cover_deg'] for c in res if c['pcb_cover_deg'] is not None),
                                             default=None),
                       min_margin_deg=min(mg) if mg else None, rule_margin_deg=margin, cases=res,
                       lateral_offset=lat, sag=sag, status='fail' if errs else 'pass')
            if v != 'declared':
                row.update(gate='G-CAM-1', note='hood is print-blocked until G-CAM-1 (PRINT_PREREQS)')
            if errs:
                row['error'] = '; '.join(errs[:6]) + ('; ... %d more' % (len(errs) - 6) if len(errs) > 6 else '')
            fc_rows.append(row)
    out += fc_rows
    # window: exact OCP distance metal -> hood at +-window_deg, final state (camera on the lens, no sag)
    hood = rows.get('hood', {}).get('shape')
    for s in s_values:
        metal = cams[(s, 'declared')]['metal']
        if hood is None:
            out.append(dict(kind='roll_catch', item='window', s=s, status='fail', error='no hood solid'))
            continue
        mb = bb_tuple(metal)
        pad = 3.0 + 2 * lat
        piece = _crop(hood, (mb[0] - pad, mb[2] - pad, mb[4] - pad), (mb[1] + pad, mb[3] + pad, mb[5] + pad))
        gaps = {}
        for dy, dz, hold in cases:
            if hold:
                continue
            for sg in (1, -1):
                ax = V(0, c0[1] + dy, c0[2] + dz)
                mr = metal.translate(V(0, dy, dz)).rotate(ax, ax + V(1, 0, 0), sg * P['window_deg'])
                gaps[(dy, dz, sg)] = _r(float(mr.distance(piece)), 3) if piece is not None else None
        g0 = [g for (dy, dz, _), g in gaps.items() if dy == 0 and dz == 0 and g is not None]
        ga = [g for g in gaps.values() if g is not None]
        ok = bool(g0) and min(g0) >= P['window_gap'] - J7_TOL and min(ga) >= J7_RUNNING - J7_TOL
        out.append(dict(kind='roll_catch', item='window', s=s, window_deg=P['window_deg'],
                        centred_gap=min(g0) if g0 else None, worst_gap=min(ga) if ga else None,
                        rule='centred >= %.2f, worst offset >= %.2f' % (P['window_gap'], J7_RUNNING),
                        gaps={'%+.2f/%+.2f/%+d' % k: g for k, g in gaps.items()}, status='pass' if ok else 'fail',
                        **({} if ok else {'error': 'level window +-%.1f deg: metal to hood %s centred / %s worst'
                                                    % (P['window_deg'], min(g0) if g0 else None,
                                                       min(ga) if ga else None)})))
    # tine strength (estimate): least contact radius over every first-contact pose, cantilever to the band
    webs = [b for b in tcb if b['kind'] == 'web']
    fls = [b for b in tcb if b['kind'] == 'flange']
    cts = [c for c in contacts if c['on_tab_catch']]
    if webs and fls and cts:
        w, f = webs[0], fls[0]
        bw, h, bf, hf_ = (w['x'][1] - w['x'][0]) - (f['x'][1] - f['x'][0]), tc['t'], f['x'][1] - f['x'][0], \
            tc['flange']['dy']
        parts = [(bw, h, 0.0), (bf, hf_, 0.0)]          # (width in x, depth in y, y0 from the inner face)
        A = sum(b * d for b, d, _ in parts)
        yc = sum(b * d * (y0 + d / 2) for b, d, y0 in parts) / A
        I = sum(b * d ** 3 / 12 + b * d * (y0 + d / 2 - yc) ** 2 for b, d, y0 in parts)
        Z = I / max(yc, max(d for _, d, _ in parts) - yc)
        # the tine faces are y-normal (tab_catch_boxes), so the contact force is along y and its moment arm about the
        #     camera axis is |dz| of the contact point (<= its radius: the conservative choice)
        r_min = min(c['r'] for c in cts)
        lever = min(c['lever'] for c in cts)
        z_low = max(min(c['z_low'] for c in cts), w['z'][0])
        F = P['design_torque_Nm'] / (lever / 1000.0)
        arm = L.ZT1 - z_low
        sig = F * arm / Z
        dfl = F * arm ** 3 / (3 * P['E_MPa'] * I)
        ok = sig <= P['tine_sigma_max_MPa'] and dfl <= P['tine_defl_max']
        out.append(dict(kind='roll_catch', item='tine_strength', estimate=True, torque_Nm=P['design_torque_Nm'],
                        contact_r_min=_r(r_min, 2), lever_min=_r(lever, 2), contact_z_low=_r(z_low, 2),
                        F_N=_r(F, 1), arm_mm=_r(arm, 2), I_mm4=_r(I, 1), Z_mm3=_r(Z, 1),
                        sigma_MPa=_r(sig, 2), deflection_mm=_r(dfl, 3),
                        rule='sigma <= %.1f MPa, deflection <= %.2f' % (P['tine_sigma_max_MPa'], P['tine_defl_max']),
                        note='E %.0f MPa assumed (ASA, across the layers: hood prints band-down); cantilever from a '
                             'rigid root: the hood roof compliance at the root is NOT modelled (r7 fix-up, VERIFY-C4), '
                             'so G-CAM-2 records the roll at the catch under fingertip torque; G-CAM-2 checks the '
                             'roots after 5 swaps' % P['E_MPa'], status='pass' if ok else 'fail',
                        **({} if ok else {'error': 'tine sigma %.1f MPa / deflection %.3f over the limit' % (sig, dfl)})))
    else:
        out.append(dict(kind='roll_catch', item='tine_strength', status='fail',
                        error='no tab-catch contact measured: the tine load is not estimated'))
    # axial engagement: head envelope (bare side: tab) x-overlap with the tine x span, lip / final / keeper states
    T, cam = L.CAM['tab'], L.CAM
    if webs:
        tx0, tx1 = webs[0]['x']
        ax_rows, worst = [], None
        for v in variants:
            hs = side if v == 'declared' else v
            for s in s_values:
                hf = L.cam_hf_x(s)
                xs = hf - T['screw_dx']
                states = {'lip': cam['lip_gap'], 'final': 0.0,
                          'keeper': -(L.cam_cover_rear(s) - cam['keeper']['x'][1])}
                for nm in ('+Y', '-Y'):
                    head = hs in ('both', nm)
                    m0, m1 = (xs - T['head_d'] / 2, xs + T['head_d'] / 2) if head else (hf - T['depth'], hf)
                    for st_, dx in states.items():
                        ov = min(m1 + dx, tx1) - max(m0 + dx, tx0)
                        ax_rows.append((v, s, nm, st_, _r(ov, 3)))
                        if worst is None or ov < worst[4]:
                            worst = (v, s, nm, st_, ov)
        ok = worst[4] >= P['axial_min'] - 1e-9
        out.append(dict(kind='roll_catch', item='axial_engagement', min_overlap=_r(worst[4], 3),
                        at=dict(variant=worst[0], s=worst[1], side=worst[2], state=worst[3]),
                        rule='overlap >= %.1f' % P['axial_min'], n=len(ax_rows), status='pass' if ok else 'fail',
                        **({} if ok else {'error': 'head / tab x-overlap with the tine %.2f < %.1f at %s'
                                                    % (worst[4], P['axial_min'], worst[:4])})))
    # lens_hold (class check) + text lint
    fc_ok = all(r['status'] == 'pass' for r in fc_rows if r['item'] == 'first_contact') and bool(fc_rows)
    final = set(final_ids(L))
    if not recs:
        out.append(dict(kind='roll_catch', item='lens_hold', status='fail',
                        error='no INSERTIONS / REMOVALS record moves the lens: the lens hold is not checked'))
    for reg, r in recs:
        probs = []
        hold = r.get('hold')
        if not hold:
            probs.append('no hold: the lens thread torque is reacted by something nothing computes')
        elif hold != 'hood_tab_catch':
            probs.append('unknown hold %r (only hood_tab_catch is computed)' % hold)
        else:
            if not tcb:
                probs.append('hold feature missing (%s)' % (geo_err or 'no tab_catch_boxes'))
            here = set(L.present_at(r['step'])) if reg == 'INSERTIONS' else (
                final - set(r.get('moving', [])) - set(r.get('off', [])))
            if 'hood' not in here:
                probs.append('hood not present at %s' % r['id'])
            if not fc_ok:
                probs.append('first_contact rows fail')
        out.append(dict(kind='roll_catch', item='lens_hold', record=r['id'], registry=reg, hold=hold,
                        status='fail' if probs else 'pass', **({'error': '; '.join(probs)} if probs else {})))
    bad, have_asm = lens_hold_lint(L, assembly_path)
    probs = (['%s: "%s"' % (w, p) for w, p in bad] + ([] if have_asm else ['ASSEMBLY.md not found: not linted'])
             + lens_turn_back_lint(L))                                     # r7 fix-up (VERIFY-C4)
    out.append(dict(kind='roll_catch', item='lens_hold_lint', phrases=list(getattr(L, 'LENS_HOLD_FORBIDDEN', ())),
                    scope='STEPS, LATCH_FREE, ASSEMBLY.md hand-written text (lines + paragraphs), guide sources '
                          '(string literals); turn-back before s_c4 for hold records', hits=len(bad),
                    status='fail' if probs else 'pass', **({'error': '; '.join(probs[:8])} if probs else {})))
    out.append(dict(kind='roll_catch', item='timing', status='info', seconds=_r(_time.time() - t_start, 1),
                    booleans=scan.n, obstacle_pieces=len(obs), s_values=len(s_values), cases=len(cases),
                    variants=variants))
    return out


class _Hits:
    """r5: exact line / B-rep crossings (OCP IntCurvesFace_ShapeIntersector, loaded once per shape): sorted, de-duplicated
    W parameters of p + W d inside lo..hi. No mesh: radii and walls are B-rep exact."""
    def __init__(self, shape):
        from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
        self.it = IntCurvesFace_ShapeIntersector()
        self.it.Load(shape.wrapped, 1e-7)

    def __call__(self, p, d, lo=-1.0e3, hi=1.0e3):
        from OCP.gp import gp_Dir, gp_Lin, gp_Pnt
        self.it.Perform(gp_Lin(gp_Pnt(*map(float, p)), gp_Dir(*map(float, d))), lo, hi)
        if not self.it.IsDone():
            return None
        out = []
        for w in sorted(self.it.WParameter(i) for i in range(1, self.it.NbPnt() + 1)):
            if not out or w - out[-1] > 1e-6:
                out.append(w)
        return out


def _first(ws, after=1e-6):
    return next((w for w in (ws or []) if w > after), None)


def _all_lenses(L):
    return list(L.LENSES) + [n for n in (getattr(L, 'LENSES_DATA_ONLY', None) or {}) if n not in L.LENSES]


def _is_zoom(d):
    return ('zoom' in d['name'].lower() or any('zoom' in str(sg[3]).lower() for sg in d['segments'])
            or any(t.get('ring') == 'zoom' for t in d.get('thumb_screws') or []))


def _clamped(cs):
    """r5: clamped band length: band from its cone seat to min(band end, collar front), mm."""
    return max(0.0, min(cs['band'][1], cs['front_x']) - max(cs['band'][0], cs['seat_x']))


def check_lens_support(L, rows=None, collars=None, lens_shapes=None, measured=None, require_collars=None):
    """r5 (J7-R, integrity review F1), every LENSES and LENSES_DATA_ONLY entry: any lens without a `support` band
    FAILs, regardless of mass, because the collar is the only anchor; the band is fixed (no moving segment over it); the
    clamped length >= band_min (a zoom: zoom_band_min); bore - band 0.2..0.4 diametral; collar front <= first moving
    segment - front_gap_min; the band lies in the collar (>= 0.2 behind the front unless the front sits at the moving-
    ring limit) and its rear edge on the cone (seat x = C_FLANGE_X + x0). Built collars (collars {lens: shape}, the
    build's lens_collar for L.LENS) are measured: lens seated on the cone (0 mm3, gap <= 0.01), bore and seat radii by
    exact rays, 0 mm3 against that lens's ko_lens_thumb boxes. WARN (info) unless the band status is 'measured'.
    r6 (audit 2026-10-06 L3): every lens in require_collars (the build passes all of LENSES) whose collar solid is
    absent is a FAIL row ('stub' if the collar module is a stub), never silently unmeasured; a call without geometry
    (require_collars None) checks the specification only. r6 (L6): 'measured' clears the WARN only with a current passing G-LENS
    record (measured={'G-LENS': True} from the build's evidence); 'measured' without one FAILs."""
    import cots
    LM, rows = L.LOAD_MODEL, rows or {}
    collar_stub = bool((rows.get('lens_collar') or {}).get('stub'))
    collars, lens_shapes = dict(collars or {}), dict(lens_shapes or {})
    if L.LENS not in collars and (rows.get('lens_collar') or {}).get('shape') is not None:
        collars[L.LENS] = rows['lens_collar']['shape']
    if L.LENS not in lens_shapes and (rows.get('lens') or {}).get('shape') is not None:
        lens_shapes[L.LENS] = rows['lens']['shape']
    ly, lz = L.LENS_AXIS
    out = []
    for name in _all_lenses(L):
        d = L.lens_spec(name)
        base = dict(kind='lens_support', lens=name, data_only=name not in L.LENSES, mass_g=d['mass'])

        def row(item, ok, **kw):
            r = dict(base, item=item, status='pass' if ok else 'fail', **kw)
            if not ok:
                r.setdefault('error', '%s: %s' % (name, item))
            out.append(r)
        sp = d.get('support')
        if not sp:
            row('support', False,
                note='J7-R: the lens collar is the only anchor; every lens requires a fixed support band',
                error='%s (%.0f g) has no support band: camera and lens have no J7-R anchor' % (name, d['mass']))
            continue
        row('support', True, support=dict(sp))
        cs = L.collar_spec(name)
        x0, x1 = d['support_abs']['x0'], d['support_abs']['x1']
        mv = [lab for _, a, b, lab, _m in d['moving_abs'] if a < x1 - 1e-6 and b > x0 + 1e-6]
        row('band_fixed', not mv, band=[_r(x0), _r(x1)], moving_over_band=mv)
        zoom = _is_zoom(d)
        need_len = LM['zoom_band_min'] if zoom else LM['band_min']
        row('band_length', _clamped(cs) >= need_len - 1e-6, clamped_mm=_r(_clamped(cs)), need_mm=need_len, zoom=zoom)
        dia = 2 * cs['bore_r'] - cs['band_d']
        row('bore_clearance', 0.2 - 1e-6 <= dia <= 0.4 + 1e-6, diametral=_r(dia, 4), window=[0.2, 0.4])
        fm = cs['first_moving_x']
        lim = None if fm is None else fm - L.COLLAR['front_gap_min']
        row('collar_front', lim is None or cs['front_x'] <= lim + 1e-6, front_x=cs['front_x'],
            limit=None if lim is None else _r(lim, 4))
        at_lim = lim is not None and abs(cs['front_x'] - lim) <= 1e-6
        row('band_in_collar', x0 - cs['rear_x'] >= 0.2 - 1e-6 and (x1 <= cs['front_x'] - 0.2 + 1e-6 or at_lim),
            rear_margin=_r(x0 - cs['rear_x']), front_margin=_r(cs['front_x'] - x1), front_at_moving_limit=at_lim)
        row('seat_x', abs(cs['seat_x'] - (L.C_FLANGE_X + sp['x0'])) <= 1e-6 and
            cs['cone_x0'] - 1e-6 <= cs['seat_x'] <= cs['cone_x1'] + 1e-6, seat_x=cs['seat_x'],
            cone=[cs['cone_x0'], cs['cone_x1']])
        entry_need = max(L.COLLAR['rear_bore_land_min'], L.FDM['MIN_WALL_LOADED'])
        if name in L.LENSES:
            row('rear_entry_plan', cs['rear_entry_feasible'] and cs['rear_bore_land_mm'] >= entry_need - 1e-6,
                land_mm=cs['rear_bore_land_mm'], required_mm=entry_need,
                note='cylindrical rear entry removes the free cone feather without moving the fixed-band seat')
        elif not cs['rear_entry_feasible']:
            out.append(dict(base, item='rear_entry_plan', status='info',
                warn='%s is data-only: its rear band position needs a separate entry design; no printable collar is approved' % name,
                available_to_seat_mm=_r(cs['seat_x'] - cs['rear_x']), required_land_mm=entry_need))
        col = collars.get(name)
        if col is None and name in (require_collars or ()) and cs['rear_entry_feasible']:
            out.append(dict(base, item='collar_solid', status='stub' if collar_stub else 'fail',
                            error='%s: no collar solid was provided, so lens_seated, bore_measured, seat_measured, '
                                  'rear_entry_measured and thumb_keepouts are not measured' % name))
        if col is not None and name in L.LENSES:
            lens = lens_shapes.get(name) or cots.lens_proxy(L, name)[0]
            v, _ = common(lens, col)
            gap = float(lens.distance(col)) if v == v and v <= VOL_TOL else 0.0
            row('lens_seated', v == v and v <= VOL_TOL and gap <= 0.01, overlap_mm3=_r(v, 4), gap=_r(gap, 4),
                note='the band rear edge chamfer rests on the 45 deg cone (contact, no overlap)')
            H = _Hits(col)
            dirs = [(0.0, math.cos(a), math.sin(a)) for a in np.radians(np.arange(0.0, 360.0, 22.5))
                    if abs(math.degrees(a) % 360.0 - 180.0) > 35.0]     # skip the -Y slit (180 deg = -Y)
            xm = (cs['cone_x1'] + min(cs['front_x'], x1)) / 2

            def radii(x):
                return [_first(H((x, ly, lz), dd, 0.0, 60.0)) for dd in dirs]
            rb = [r_ for r_ in radii(xm) if r_ is not None]
            dm = 2 * float(np.mean(rb)) - cs['band_d'] if len(rb) == len(dirs) else None
            row('bore_measured', dm is not None and 0.2 - 1e-3 <= dm <= 0.4 + 1e-3 and
                max(rb) - min(rb) <= 2e-3, at_x=_r(xm), r_mean=_r(np.mean(rb), 4) if rb else None,
                diametral=None if dm is None else _r(dm, 4), rays=len(rb), of=len(dirs))
            rs = [r_ for r_ in radii(cs['seat_x']) if r_ is not None]
            row('seat_measured', len(rs) == len(dirs) and max(abs(r_ - cs['seat_r']) for r_ in rs) <= 1e-3,
                at_x=cs['seat_x'], r_mean=_r(np.mean(rs), 4) if rs else None, seat_r=cs['seat_r'])
            # Measure the ACTUAL bore boundary, not only the intended radius: a planted old feather
            # otherwise looks thick when sampled farther out at the corrected radius.
            rear_x = cs['rear_x'] + 0.01
            entry_radii = radii(rear_x)
            entry_chords = []
            for dd, rr in zip(dirs, entry_radii):
                if rr is None:
                    continue
                p = (rear_x, ly + dd[1] * (rr + 0.03), lz + dd[2] * (rr + 0.03))
                t, _, _, why = chord(col, p, (1, 0, 0))
                if why is None and t is not None:
                    entry_chords.append(t)
            row('rear_entry_measured', len(entry_chords) == len(dirs) and
                min(entry_chords, default=0.0) >= entry_need - 1e-3 and
                all(rr is not None and abs(rr - cs['cone_r0']) <= 1e-3 for rr in entry_radii),
                measured_min_mm=_r(min(entry_chords)) if entry_chords else None, required_mm=entry_need,
                actual_rear_radii_mm=[_r(rr, 4) for rr in entry_radii], expected_radius_mm=cs['cone_r0'],
                rays=len(entry_chords), of=len(dirs), at_x=rear_x,
                note='exact axial chords 0.03 mm into the actual rear bore edge; excludes only the declared split')
            kos = L.lens_thumb_keepouts(name)
            if kos:
                vk = {k: _r(common(col, dc.box_solid(b))[0], 4) for k, b in kos.items()}
                row('thumb_keepouts', all(x == x and x <= VOL_TOL for x in vk.values()), overlap_mm3=vk)
            else:
                out.append(dict(base, item='thumb_keepouts', status='info',
                                note='no thumb screws listed for this lens ([unconfirmed], G-LENS)'))
        if sp.get('status') == 'measured':      # r6 (L6): the evidence record, not the string, clears the WARN
            g_lens = bool((measured or {}).get('G-LENS'))
            row('status', g_lens, band_status=sp['status'], g_lens_record='current pass' if g_lens else 'none',
                **({} if g_lens else {'error': '%s band status is measured, but G-LENS has no current recorded '
                                               'pass (evidence/README.md)' % name}))
        else:
            out.append(dict(base, item='status', status='info', band_status=sp.get('status'),
                            warn='%s support band is %r, not measured: G-LENS' % (name, sp.get('status'))))
    return out


def check_collar_gauge(L, rows, gauge, travel=40.0, step_mm=1.0):
    """r6 (audit 2026-10-06 X2): the collar centring gauge (printed_collar.centring_gauge) at step 7, camera not yet in.
    Seated, it touches the tub only on the lip edge and the collar only on its bore-entry chamfer (<= VOL_TOL, gap
    <= 0.01 to both) and keeps >= 0.5 from the hood; its -X insertion from +travel meets nothing on the way (manifold
    boolean <= SWEEP_TOL); the straight driver (DRIVER bit and handle) for every s_c1..s_c3 clears it (<= VOL_TOL).
    Rows join the lens_support category (item 'centring_gauge')."""
    import manifold3d as m3
    base = dict(kind='lens_support', item='centring_gauge', lens=L.LENS)
    if gauge is None:
        return [dict(base, status='fail', error='no centring gauge solid was built')]
    out = []
    for pid, need in (('tub', None), ('lens_collar', None), ('hood', 0.5)):
        r = rows.get(pid) or {}
        sh = r.get('shape')
        if sh is None:
            out.append(dict(base, part=pid, status='stub' if r.get('stub') else 'fail', error='%s not built' % pid))
            continue
        v, _ = common(gauge, sh)
        gap = float(gauge.distance(sh)) if v == v and v <= VOL_TOL else 0.0
        ok = v == v and v <= VOL_TOL and (gap <= 0.01 if need is None else gap >= need - J7_TOL)
        out.append(dict(base, part=pid, overlap_mm3=_r(v, 4), gap=_r(gap, 4),
                        rule='seated on it (contact, no overlap)' if need is None else 'gap >= %.1f' % need,
                        status='pass' if ok else 'fail',
                        **({} if ok else {'error': 'gauge vs %s: overlap %s mm3, gap %s' % (pid, _r(v, 4), _r(gap, 4))})))
    mg = manifold_of(gauge)
    hits = {}
    for pid in ('tub', 'hood', 'lens_collar'):
        sh = (rows.get(pid) or {}).get('shape')
        mo = manifold_of(sh) if sh is not None else None
        if mo is None or mg is None:
            continue
        for k in range(1, int(round(travel / step_mm)) + 1):
            v = (mg.translate([k * step_mm, 0.0, 0.0]) ^ mo).volume()
            if v > SWEEP_TOL:
                hits[pid] = max(hits.get(pid, 0.0), _r(v, 2))
    ok = mg is not None and not hits
    out.append(dict(base, part='insertion', path='-X %.0f to the seated pose in %.1f steps' % (travel, step_mm),
                    hits=hits, status='pass' if ok else 'fail',
                    **({} if ok else {'error': 'gauge insertion meets %s' % (hits or 'nothing measurable (no mesh)')})))
    D = L.DRIVER
    drv = {}
    for s in L.SCREWS:
        if s['id'] not in ('s_c1', 's_c2', 's_c3'):
            continue
        hp = V(*s['head_point'])
        up = V(*[-a for a in s['axis']])                       # the driver stands opposite the driving direction
        bit = cq.Solid.makeCylinder(D['bit_d'] / 2, D['bit_len'], hp, up)
        handle = cq.Solid.makeCylinder(D['handle_d'] / 2, D['handle_len'], hp + up * D['bit_len'], up)
        drv[s['id']] = _r(max(common(gauge, bit)[0], common(gauge, handle)[0]), 4)
    ok = len(drv) == 3 and all(v == v and v <= VOL_TOL for v in drv.values())
    out.append(dict(base, part='driver', overlap_mm3=drv, rule='the s_c1..s_c3 driver (bit + handle) clears the gauge',
                    status='pass' if ok else 'fail', **({} if ok else {'error': 'driver meets the gauge: %s' % drv})))
    return out


def check_lens_clamp(L, rows=None, collars=None):
    """r5 (judge 3 s6.9, judge 1 s6.4 items 3-5): from LOAD_MODEL. Anchor polygon TL-TR-LR-LL encloses the lens axis
    with >= polygon_edge_min to every edge (FAIL otherwise). Per lens with a support: pinch F = pinch_N x pinch_relax,
    M_sep = (pi/6) F L (L = clamped band length) against the static moment about the clamped band centre (lens, camera,
    adapter; |lever| sum, conservative): FAIL below sep_safety x static, WARN (info) below shock_g x static; the aim at
    the tub face (wall_deg_per_Nm upper value) WARNs above aim_max_deg at shock_g. Anchor screening excludes the LR
    compression foot, solves the three-bolt axial/moment reactions, and bounds each reaction under simultaneous
    shock_g axial load and arbitrary-direction bending (sum of absolute mass lever moments), multiplied by the
    provisional anchor_prying_factor >= 1. WARN above anchor_N; retain the old signed-moment/height estimate only for
    comparison. This is a conservative screening assumption, not a proven safety factor or physical validation
    (G-COL-1, G-CAM-2). Invalid factors or degenerate bolt statics FAIL closed."""
    LM, rows, collars = L.LOAD_MODEL, rows or {}, dict(collars or {})
    if L.LENS not in collars and (rows.get('lens_collar') or {}).get('shape') is not None:
        collars[L.LENS] = rows['lens_collar']['shape']
    ly, lz = L.LENS_AXIS
    C, g, k_lo, k_hi = L.COLLAR, LM['g'], LM['wall_deg_per_Nm'][0], LM['wall_deg_per_Nm'][1]
    order = ('TL', 'TR', 'LR', 'LL')
    hull = _hull2([C['feet'][k] for k in order])
    margin = _inside_margin(hull, (ly, lz)) if len(hull) >= 3 else -1.0
    bolted = _hull2([C['feet'][k] for k in C['bolted']])
    out = [dict(kind='lens_clamp', item='anchor_polygon', order=list(order), margin_mm=_r(margin),
                need_mm=LM['polygon_edge_min'],
                bolted_only_margin_mm=_r(_inside_margin(bolted, (ly, lz))) if len(bolted) >= 3 else None,
                note='the 3 bolted anchors alone do not enclose the axis; the LR compression foot closes the polygon',
                status='pass' if margin >= LM['polygon_edge_min'] - 1e-6 else 'fail',
                **({} if margin >= LM['polygon_edge_min'] - 1e-6 else
                   {'error': 'lens axis %.2f from the anchor polygon edge (need >= %.1f inside)'
                             % (margin, LM['polygon_edge_min'])}))]
    # r6 (audit 2026-10-06 L7): the polygon closes only through the compression-only LR foot. While the bolt preload
    #     holds, prying is screened by the three-bolt anchor_model below (LR inactive); if the preload relaxes (M1: no
    #     spring, ASA creep), the bolted triangle alone must hold the axis. Report it as a WARN row, never a silent pass.
    if len(bolted) >= 3:
        bm = _inside_margin(bolted, (ly, lz))
        out.append(dict(kind='lens_clamp', item='anchor_polygon_bolted', bolted=list(C['bolted']), margin_mm=_r(bm),
                        status='info' if bm < 0.0 else 'pass',
                        **({'warn': 'the bolted anchors %s alone leave the lens axis %.1f mm outside their triangle: '
                                    'the axis is enclosed only through the compression foot LR, so preload loss '
                                    '(audit 2026-10-06 M1, G-COL-1 creep) lets the collar pry'
                                    % ('/'.join(C['bolted']), -bm)} if bm < 0.0 else {})))
    factor = LM.get('anchor_prying_factor')
    anchor_model = dict(kind='lens_clamp', item='anchor_model', bolted=list(C['bolted']),
                        compression_foot_active=False, prying_factor=factor,
                        axial_shock_g=LM['shock_g'], bending_shock_g=LM['shock_g'], simultaneous_loads=True,
                        model=LM.get('anchor_model', 'three bolted anchors, LR inactive; provisional load bound'),
                        note='screening assumptions only; insert pull-out, preload retention and prying need G-COL-1 / G-CAM-2',
                        status='pass')
    try:
        if isinstance(factor, bool) or not isinstance(factor, (int, float)) or not math.isfinite(factor) or factor < 1.0:
            raise ValueError('anchor_prying_factor must be a finite number >= 1.0')
        if len(C['bolted']) != 3 or len(set(C['bolted'])) != 3:
            raise ValueError('anchor statics require exactly three distinct bolted anchors')
        # Force/moment equilibrium: [sum(R), sum((y-ly)R), sum((z-lz)R)] = [N, Mz, -My].
        # Coordinates in metres give coefficients in N/N and N/(N m); sign does not affect the magnitude bound.
        matrix = np.array([[1.0, (C['feet'][k][0] - ly) / 1000.0, (C['feet'][k][1] - lz) / 1000.0]
                           for k in C['bolted']], float).T
        if not np.isfinite(matrix).all() or np.linalg.matrix_rank(matrix) != 3:
            raise ValueError('bolted-anchor statics are degenerate or nonfinite')
        coefficients = np.linalg.solve(matrix, np.eye(3))
        if not np.isfinite(coefficients).all():
            raise ValueError('bolted-anchor reaction coefficients are nonfinite')
        anchor_model['reaction_coefficients'] = {
            k: dict(axial_N_per_N=_r(float(a), 6), bending_N_per_Nm=[_r(float(b), 6), _r(float(c), 6)])
            for k, (a, b, c) in zip(C['bolted'], coefficients)}
    except (KeyError, TypeError, ValueError, np.linalg.LinAlgError) as e:
        anchor_model.update(status='fail', error=str(e))
        # Invalid inputs must still produce a serializable failure row (never NaN/Infinity in the receipt).
        anchor_model.update(prying_factor=None, requested_prying_factor=repr(factor))
    out.append(anchor_model)
    if anchor_model['status'] == 'fail':
        return out
    cam = (rows.get('gs_camera') or {}).get('shape')
    x_cam = (cq.Shape.centerOfMass(cam).x if cam is not None else
             (L.cam_hf_x(L.CAM['s_nom']) + L.cam_cover_rear(L.CAM['s_nom'])) / 2)
    m_cam, m_ad = L.COTS['gs_camera']['mass'], L.COTS['c_cs_adapter']['mass']
    x_ad = (L.CS_FLANGE_X + L.C_FLANGE_X) / 2
    x_w = L.XT1                                          # collar feet bear on the tub outer face
    z_top = max(C['feet'][k][1] for k in C['bolted'])
    lever = (z_top - min(z for _, z in C['feet'].values())) / 1000.0
    F = LM['pinch_N'] * LM['pinch_relax']
    for name in _all_lenses(L):
        d = L.lens_spec(name)
        cs = L.collar_spec(name)
        if cs is None:
            continue                                     # check_lens_support FAILs every lens without a band
        col = collars.get(name)
        if col is not None:
            m_col, x_col = L.mass_g(col.Volume(), 'lens_collar'), cq.Shape.centerOfMass(col).x
        else:
            m_col, x_col = C['mass_est_g'], (cs['rear_x'] + cs['front_x']) / 2
        Lc = _clamped(cs)
        xc = (max(cs['band'][0], cs['seat_x']) + min(cs['band'][1], cs['front_x'])) / 2
        items = [(d['mass'], d['com'][0]), (m_cam, x_cam), (m_ad, x_ad)]
        m_st = g * sum(m / 1000.0 * abs(x - xc) / 1000.0 for m, x in items)
        m_sep = math.pi / 6.0 * F * Lc / 1000.0
        m_wall = g * sum(m / 1000.0 * (x - x_w) / 1000.0 for m, x in items + [(m_col, x_col)])
        aim5 = LM['shock_g'] * abs(m_wall) * k_hi
        t5_nominal = LM['shock_g'] * abs(m_wall) / lever if lever > 0.0 else None
        supported = items + [(m_col, x_col)]
        axial5 = LM['shock_g'] * g * sum(m for m, _ in supported) / 1000.0
        bend5 = LM['shock_g'] * g * sum(m / 1000.0 * abs(x - x_w) / 1000.0 for m, x in supported)
        reactions = {k: factor * (abs(a) * axial5 + math.hypot(b, c) * bend5)
                     for k, (a, b, c) in zip(C['bolted'], coefficients)}
        t5 = max(reactions.values())
        fails, warns = [], []
        if m_sep < LM['sep_safety'] * m_st:
            fails.append('M_sep %.3f N m < %.1f x static %.3f N m' % (m_sep, LM['sep_safety'], m_st))
        if m_sep < LM['shock_g'] * m_st:
            warns.append('M_sep %.3f N m < the %.0f g moment %.3f N m (the lens rocks elastically in the collar at a '
                         'knock; aim only, recovers)' % (m_sep, LM['shock_g'], LM['shock_g'] * m_st))
        if aim5 > LM['aim_max_deg']:
            warns.append('aim at %.0f g %.3f deg > %.2f deg' % (LM['shock_g'], aim5, LM['aim_max_deg']))
        if t5 > LM['anchor_N']:
            warns.append('bolted-anchor bound at %.0f g %.1f N (prying x %.2f, LR inactive) > %.0f N relaxed'
                         % (LM['shock_g'], t5, factor, LM['anchor_N']))
        r = dict(kind='lens_clamp', item='clamp', lens=name, data_only=name not in L.LENSES,
                 geometry_status='production profile' if cs['rear_entry_feasible'] else
                     'data-only load comparison; rear-entry design is infeasible and no collar may be exported', pinch_N=F,
                 clamped_mm=_r(Lc), band_centre_x=_r(xc), M_sep_Nm=_r(m_sep, 4), M_static_Nm=_r(m_st, 4),
                 M_shock_Nm=_r(LM['shock_g'] * m_st, 4), ratio_static=_r(m_sep / m_st if m_st else float('inf'), 2),
                 M_wall_static_Nm=_r(m_wall, 4), aim_static_deg=[_r(abs(m_wall) * k_lo, 4), _r(abs(m_wall) * k_hi, 4)],
                 aim_shock_deg=_r(aim5, 4), anchor_tension_shock_N=_r(t5, 1),
                 anchor_tension_nominal_shock_N=_r(t5_nominal, 1), anchor_prying_factor=factor,
                 anchor_reactions_shock_N={k: _r(float(v), 3) for k, v in reactions.items()},
                 anchor_axial_shock_N=_r(axial5, 4), anchor_bending_shock_bound_Nm=_r(bend5, 4),
                 anchor_compression_foot_active=False, anchor_model_provisional=True, collar_g=_r(m_col, 1),
                 masses=dict(lens=d['mass'], camera=m_cam, adapter=m_ad, collar=_r(m_col, 1)),
                 status='fail' if fails else ('info' if warns else 'pass'), src=LM['src'])
        if fails:
            r['error'] = '; '.join(fails)
        if warns:
            r['warn'] = '; '.join(warns)
        out.append(r)
    return out


def _frame(ax):
    ax = np.array(ax, float)
    ref = np.array([1.0, 0, 0]) if abs(ax[0]) < 0.9 else np.array([0, 1.0, 0])
    u = np.cross(ax, ref)
    u /= np.linalg.norm(u)
    return ax, u, np.cross(ax, u)


def _void_interval(ws, t):
    """r5: (a, b) = the crossing params bracketing t on a line whose crossings are ws (None = open to infinity)."""
    return max((w for w in ws if w < t), default=None), min((w for w in ws if w > t), default=None)


def screw_length_tol(length):
    """r6 (B-3): ISO 4759-1 product grade A screw length tolerance js15 (half of IT15) for nominal length l, mm."""
    for upper, it15 in ((3.0, 0.40), (6.0, 0.48), (10.0, 0.58), (18.0, 0.70), (30.0, 0.84), (50.0, 1.00)):
        if length <= upper:
            return it15 / 2
    return 1.20 / 2


def check_inserts(L, rows):
    """r5 (brief choice 8, judge 3 s6.9): kind M3 screws into heat-set inserts, measured on the solids by exact rays:
    insert bore dia = insert bore_d +-0.1; bore open at one end and deep >= insert length + 0.2; wall round the bore
    >= MIN_WALL_LOADED over the insert span; insert span engaged >= M3 engage_min; the tip in a void (no bottoming,
    tip + 0.2 clear); under the washer >= MIN_WALL_LOADED; the head part's clearance hole >= clear_d - 0.05.
    r6 (audit 2026-10-06 B-3): the per-line local depth must meet the same insert + 0.2 need as the face depth (it was
    compared with insert + flush only), and the tip stays in a void at its ISO 4759-1 js15 length tolerance."""
    M3, out = L.M3, []
    for s in L.SCREWS:
        if s.get('kind') != 'M3':
            continue
        ins = s['insert']
        row = dict(kind='insert', screw=s['id'], insert_part=ins['part'], head_part=s['head_part'], spec=ins['spec'])
        try:
            ax, u, w = _frame(s['axis'])
            hp, tp = np.array(s['head_point'], float), np.array(s['tip'], float)
            i = int(np.argmax(np.abs(ax)))
            k = 'xyz'[i]
            t0, t1 = sorted(((ins[k][0] - hp[i]) * ax[i], (ins[k][1] - hp[i]) * ax[i]))
            t_tip = float(np.dot(tp - hp, ax))
            P = rows[ins['part']]['shape']
            lo = np.minimum(hp, hp + ax * (t1 + 8.0)) - 9.0
            hi = np.maximum(hp, hp + ax * (t1 + 8.0)) + 9.0
            Pc = _crop(P, tuple(lo), tuple(hi))
            H = _Hits(Pc)
            dirs = [u * math.cos(a) + w * math.sin(a) for a in np.radians(np.arange(0.0, 360.0, 30.0))]
            rb = ins['bore_d'] / 2
            r_in, r_wall = (M3['clear_d'] / 2 + rb) / 2, rb + 0.4          # 1.85 (in the bore), 2.4 (in the wall)
            tm = (t0 + t1) / 2
            # bore: on 4 lines parallel to the axis at r 1.85 the void round the insert middle is open at one end
            # (the insert goes in there) and closed at the other (bore bottom / step to the clearance hole); lines at
            # r 2.4 (in the wall) give the boss face at the open end. depth = closed end - face plane (the face crossing
            # nearest the open side: an edge chamfer that recedes the face locally is not the face); local = per line.
            ends, entries, opens = [], [], []
            for dd in dirs[::3]:
                a, b = _void_interval(H(hp + dd * r_in, ax) or [], tm)
                ws2 = H(hp + dd * r_wall, ax) or []
                if (a is None) == (b is None):
                    ends.append(None)
                    entries.append(None)
                    continue
                head_open = a is None
                opens.append('head side' if head_open else 'tip side')
                ends.append(b if head_open else a)
                cand = [x for x in ws2 if (x <= tm if head_open else x >= tm)]
                entries.append(min(cand, key=lambda x: abs(x - (t0 if head_open else t1))) if cand else None)
            ok_lines = None not in ends and None not in entries and len(set(opens)) == 1
            if ok_lines:
                sg = 1.0 if opens[0] == 'head side' else -1.0
                face = min(entries) if sg > 0 else max(entries)
                depth = (min(ends) - face) if sg > 0 else (face - max(ends))
                local = min(sg * (e - f_) for e, f_ in zip(ends, entries))
            else:
                depth = local = None
            dias, walls = [], []
            for f in (0.05, 0.25, 0.5, 0.75, 0.95):
                c = hp + ax * (t0 + f * (t1 - t0))
                for dd in dirs:
                    ws = H(c, dd, 0.0, 30.0) or []
                    if len(ws) >= 2:
                        if 0.25 <= f <= 0.75:
                            dias.append(2 * ws[0])
                        walls.append((ws[1] - ws[0], [_r(x, 2) for x in c], [_r(x, 3) for x in dd]))
                    else:
                        walls.append((0.0, [_r(x, 2) for x in c], [_r(x, 3) for x in dd]))
            wmin = min(walls, key=lambda x: x[0])
            walls = [x[0] for x in walls]
            need_d = ins['length'] + 0.2
            engage = min(t_tip, t1) - t0
            from OCP.BRepClass3d import BRepClass3d_SolidClassifier
            from OCP.TopAbs import TopAbs_IN
            from OCP.gp import gp_Pnt

            def solid_at(p):
                return any(BRepClass3d_SolidClassifier(so.wrapped, gp_Pnt(*map(float, p)), 1e-6).State() == TopAbs_IN
                           for so in _solids(Pc))
            len_tol = screw_length_tol(s.get('length', 0.0))
            tip_void = not solid_at(tp) and not solid_at(tp + ax * 0.2) and not solid_at(tp + ax * len_tol)
            Hh = _Hits(_crop(rows[s['head_part']]['shape'], tuple(lo), tuple(hi)))
            rh = (M3['clear_d'] / 2 + M3['washer']['d'] / 2) / 2
            seats, unders = [], []
            for dd in dirs[::2]:
                ws = [x for x in (Hh(hp - ax * 0.3 + dd * rh, ax) or []) if x > 0]
                if len(ws) >= 2:
                    seats.append(ws[0] - 0.3)
                    unders.append(ws[1] - ws[0])
            t_c = (seats and min(seats) or 0.0) + 1.0
            clr = [_first(Hh(hp + ax * t_c, dd, 0.0, 30.0)) for dd in dirs]
            clr = [x for x in clr if x is not None]
            probs = []
            if len(dias) < 6 or abs(np.mean(dias) - ins['bore_d']) > 0.1 + 1e-6 or min(dias) < ins['bore_d'] - 0.1 - 1e-6:
                probs.append('bore dia %s (need %.1f +-0.1)' % (_r(np.mean(dias)) if dias else None, ins['bore_d']))
            if not ok_lines:
                probs.append('bore not open at exactly one end on every probe line (ends %s, faces %s, open %s)'
                             % (ends, entries, opens))
            elif depth < need_d - 1e-3 or local < need_d - 1e-3:
                probs.append('bore depth %.3f from the face, %.3f locally on one probe line (need >= insert + 0.2 = '
                             '%.2f on every line)' % (depth, local, need_d))
            if min(walls) < L.FDM['MIN_WALL_LOADED'] - 1e-3:
                probs.append('wall %.3f round the insert at %s toward %s < %.1f' % (wmin[0], wmin[1], wmin[2],
                                                                                    L.FDM['MIN_WALL_LOADED']))
            if engage < M3['engage_min'] - 1e-6:
                probs.append('engage %.2f < %.1f' % (engage, M3['engage_min']))
            if not tip_void:
                probs.append('tip (or tip + 0.2, or tip + its %.2f length tolerance) in material: the screw bottoms'
                             % len_tol)
            if not unders or min(unders) < L.FDM['MIN_WALL_LOADED'] - 1e-3:
                probs.append('under the washer %s < %.1f' % (_r(min(unders)) if unders else None,
                                                              L.FDM['MIN_WALL_LOADED']))
            if seats and abs(min(seats) - M3['washer']['t']) > 0.05:
                probs.append('washer seat %.2f from the head point (washer %.1f)' % (min(seats), M3['washer']['t']))
            if len(clr) < len(dirs) or min(clr) < M3['clear_d'] / 2 - 0.025:
                probs.append('clearance hole in %s r %s < %.2f' % (s['head_part'], _r(min(clr)) if clr else None,
                                                                   M3['clear_d'] / 2))
            row.update(bore_dia=_r(np.mean(dias)) if dias else None, bore_depth=_r(depth), bore_depth_local_min=_r(local),
                       bore_depth_need=_r(need_d), open_end=sorted(set(opens)), insert_span_from_head=[_r(t0), _r(t1)],
                       wall_min=_r(min(walls)), wall_min_at=dict(point=wmin[1], toward=wmin[2]), engage=_r(engage),
                       tip_from_head=_r(t_tip), tip_in_void=tip_void, length_tol=len_tol,
                       washer_seat=_r(min(seats)) if seats else None,
                       under_washer_min=_r(min(unders)) if unders else None,
                       head_clear_r=_r(min(clr)) if clr else None, status='fail' if probs else 'pass')
            if probs:
                row['error'] = '; '.join(probs)
        except Exception as e:  # noqa: BLE001
            row.update(status='fail', error='%s: %s' % (type(e).__name__, str(e)[:200]))
        if rows.get(ins['part'], {}).get('stub') or rows.get(s['head_part'], {}).get('stub'):
            row['status'] = 'stub'
        out.append(row)
    return out


def check_joint_checks(L, R):
    """r5 (judge 3 s6.7: "the new j7_float check" is J7-required): a CRITICAL_JOINTS entry may name whole checks
    (`required_checks`) besides its feature probes. The joint row passes only if each named check produced rows, none
    failed or is a stub, and >= 1 row passed (an 'info' WARN row neither passes nor blocks). Rows go to
    critical_features (the release gate)."""
    out = []
    for j in registry(L, 'CRITICAL_JOINTS'):
        req = list(j.get('required_checks') or [])
        if not req:
            continue
        probs, seen = [], {}
        for c in req:
            st = [r.get('status') for r in (R.get(c) or [])]
            seen[c] = dict(n=len(st), passed=st.count('pass'), failed=st.count('fail'), stub=st.count('stub'),
                           info=st.count('info'))
            if not st:
                probs.append('%s: not run / no rows' % c)
            elif 'fail' in st or 'stub' in st or not st.count('pass'):
                probs.append('%s: %d fail, %d stub, %d pass' % (c, st.count('fail'), st.count('stub'), st.count('pass')))
        out.append(dict(kind='joint_check', id=j['id'], part=(j.get('parts') or [None])[0], required_checks=req,
                        checks=seen, status='fail' if probs else 'pass', **({'error': '; '.join(probs)} if probs else {})))
    return out


# ------------------------------------------------------------------------------------------- r6: print orientation
# User 2026-10-08 "settle the print order and orientation". The per-part face_down is a computed, regression-protected
# claim: print_overhang slices every production STL in its print pose, layer by layer, and classifies all new area that
# lies beyond the 45 deg allowance of the layer below. Each pixel of it must be a short overhang (<= cantilever_max from
# supported material), part of an anchored bridge (a straight run in one of 8 directions whose two ends both meet
# supported material, <= bridge_max long), within edge_tol of one of those, or inside a declared support zone
# (layout.PRINT_SUPPORT_ZONES). Anything else FAILs, and a declared zone that no region needs FAILs as stale.
def _cs_polys(cs):
    return [np.asarray(p, float) for p in cs.to_polygons() if len(p) >= 3]


def _signed_area(p):
    x, y = p[:, 0], p[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def _raster(cs, x0, y0, nx, ny, px):
    """Boolean mask [ny, nx] of a CrossSection on a px grid starting at (x0, y0); outer contours fill, holes erase
    (drawn largest first, so nested islands come back)."""
    from PIL import Image, ImageDraw
    img = Image.new('L', (nx, ny), 0)
    d = ImageDraw.Draw(img)
    for p in sorted(_cs_polys(cs), key=lambda q: -abs(_signed_area(q))):
        d.polygon([((x - x0) / px - 0.5, (y - y0) / px - 0.5) for x, y in p], fill=255 if _signed_area(p) > 0 else 0)
    return np.asarray(img) > 127


def _grow(M, step):
    """One dilation step; 4- and 8-neighbourhood alternate, so n steps approximate a Euclidean n-pixel distance."""
    P = np.pad(M, 1)
    D = P[1:-1, 1:-1] | P[:-2, 1:-1] | P[2:, 1:-1] | P[1:-1, :-2] | P[1:-1, 2:]
    if step % 2:
        D |= P[:-2, :-2] | P[:-2, 2:] | P[2:, :-2] | P[2:, 2:]
    return D


def _reach(seed, within, n):
    """Pixels of `within` reached from seed in n growth steps without leaving seed | within."""
    G, allowed = seed.copy(), seed | within
    for i in range(n):
        G = _grow(G, i) & allowed
    return G & within


def _rot(M, deg):
    from PIL import Image
    if abs(deg) < 1e-9:
        return M
    return np.asarray(Image.fromarray(M.astype(np.uint8) * 255).rotate(deg, resample=Image.NEAREST, expand=True)) > 127


def _unrot(M, deg, shape):
    if abs(deg) < 1e-9:
        return M
    B = _rot(M, -deg)
    h, w = shape
    y0, x0 = (B.shape[0] - h) // 2, (B.shape[1] - w) // 2
    return B[y0:y0 + h, x0:x0 + w]


def _enclosed(V):
    """Pixels of the void mask V not connected (4-neighbourhood) to the window border: holes inside the region."""
    G = np.zeros_like(V)
    G[0, :], G[-1, :], G[:, 0], G[:, -1] = V[0, :], V[-1, :], V[:, 0], V[:, -1]
    while True:
        N = _grow(G, 0) & V
        if np.array_equal(N, G):
            return V & ~G
        G = N


def _bridged_runs(R, A, H, max_px):
    """Row runs of R no longer than max_px -> int32 masks of run length (0 = none): runs with both neighbours in A
    (bridges), runs with one neighbour in A and the other in H (a hole inside the region: its perimeter loop prints in
    the same layer, held by the runs beside it)."""
    h, w = R.shape
    P = np.zeros((h, w + 2), bool)
    P[:, 1:-1] = R
    d = np.diff(P.astype(np.int8), axis=1)
    rs, a_ = np.nonzero(d == 1)
    _, b_ = np.nonzero(d == -1)
    Ap, Hp = np.zeros((h, w + 2), bool), np.zeros((h, w + 2), bool)
    Ap[:, 1:-1], Hp[:, 1:-1] = A, H
    B, E = np.zeros(R.shape, np.int32), np.zeros(R.shape, np.int32)
    for r, a, b in zip(rs, a_, b_):
        if b - a > max_px:
            continue
        left, right = (Ap[r, a], Hp[r, a]), (Ap[r, b + 1], Hp[r, b + 1])
        if left[0] and right[0]:
            B[r, a:b] = b - a
        elif (left[0] and right[1]) or (left[1] and right[0]):
            E[r, a:b] = b - a
    return B, E


def _rot_i(M, deg):
    from PIL import Image
    if abs(deg) < 1e-9:
        return M
    return np.asarray(Image.fromarray(M.astype(np.int32), mode='I').rotate(deg, resample=Image.NEAREST, expand=True))


def _unrot_i(M, deg, shape):
    if abs(deg) < 1e-9:
        return M
    B = _rot_i(M, -deg)
    h, w = shape
    y0, x0 = (B.shape[0] - h) // 2, (B.shape[1] - w) // 2
    return B[y0:y0 + h, x0:x0 + w]


def _classify(region, anchor, opts):
    """Raster classification of one unsupported region -> (bad mask, its pixel centres x / y, area, longest bridge)."""
    px = opts['px']
    m = 2 * px + opts['edge_tol']
    bx0, by0, bx1, by1 = region.bounds()
    x0, y0 = bx0 - m, by0 - m
    nx, ny = int(math.ceil((bx1 - bx0 + 2 * m) / px)), int(math.ceil((by1 - by0 + 2 * m) / px))
    import manifold3d as m3
    win = m3.CrossSection.square([nx * px, ny * px]).translate([x0, y0])
    R = _raster(region, x0, y0, nx, ny, px)
    A = _grow(_raster(anchor ^ win, x0, y0, nx, ny, px), 1) & ~R
    H = _enclosed(~R & ~A)
    near = _reach(A, R, int(math.ceil(opts['cantilever_max'] / px)))
    max_px, big = int(opts['bridge_max'] / px), np.iinfo(np.int32).max
    span_b, span_e = np.full(R.shape, big, np.int32), np.full(R.shape, big, np.int32)
    for k in range(opts['directions']):
        deg = 180.0 * k / opts['directions']
        Br, Er = _bridged_runs(_rot(R, deg), _rot(A, deg), _rot(H, deg), max_px)
        for src, dst in ((Br, span_b), (Er, span_e)):
            if src.any():
                back = _unrot_i(src, deg, R.shape)
                np.minimum(dst, np.where(back > 0, back, big), out=dst)
    bridged = R & ~near & (span_b < big)
    hole_edge = R & ~near & ~bridged & (span_e < big)
    acc = near | bridged | hole_edge
    acc = _reach(acc, R, int(math.ceil(opts['edge_tol'] / px))) | acc
    bad = R & ~acc
    # a teardrop apex or a sliver thinner than one extrusion width (0.4) prints as a single line: not a region
    half = max(1, int(round(0.5 * dc.FDM['NOZZLE'] / px)))
    core = bad.copy()
    for i in range(half):
        core = ~_grow(~core, 0)
    thick = _reach(core, bad, half) | core
    apex = float((bad & ~thick).sum()) * px * px
    bad = thick
    need = np.where(bridged, span_b, 0).max() if bridged.any() else 0
    need_e = np.where(hole_edge, span_e, 0).max() if hole_edge.any() else 0
    jj, ii = np.nonzero(bad)
    return dict(bad_x=x0 + (ii + 0.5) * px, bad_y=y0 + (jj + 0.5) * px, area=float(R.sum()) * px * px,
                span=float(max(need, need_e)) * px, hole_edge=float(hole_edge.sum()) * px * px, apex=apex)


def check_print_overhang(L, pid, man, zones=(), opts=None, face_down=None):
    """r6: one production part. man = manifold3d Manifold in print pose (Z0 = bed); zones = [dict(id, box (print
    frame), why)] from layout.PRINT_SUPPORT_ZONES mapped by the build. -> one row (pass / fail) with the bridges, the
    zone use and every unsupported region outside a zone."""
    import manifold3d as m3
    o = dict(getattr(L, 'PRINT_OVERHANG', {}) or {}, **(opts or {}))
    h, allow = o['layer'], o['layer'] * math.tan(math.radians(o['overhang_deg']))
    row = dict(kind='print_overhang', part=pid, face_down=face_down or L.PARTS[pid]['face_down'], rule=dict(
        layer=h, overhang_deg=o['overhang_deg'], cantilever_max=o['cantilever_max'], bridge_max=o['bridge_max'],
        edge_tol=o['edge_tol'], directions=o['directions'], px=o['px']))
    if man is None or man.is_empty():
        row.update(status='fail', error='no print-pose mesh')
        return row
    zmax = man.bounding_box()[5] if hasattr(man, 'bounding_box') else None
    if zmax is None:
        bb = man.to_mesh().vert_properties
        zmax = float(np.max(np.asarray(bb)[:, 2]))
    n = int(math.floor(zmax / h + 1e-9))
    bridges, unsupported, used, regions, short, apex = [], [], {}, 0, 0, 0.0
    prev = man.slice(0.5 * h)
    for k in range(1, n):
        z = (k + 0.5) * h
        S = man.slice(z)
        supp = prev.offset(allow, m3.JoinType.Round)
        U = S - supp
        prev = S
        if U.area() < o['min_area']:
            continue
        anchor = S ^ supp
        near = anchor.offset(o['cantilever_max'], m3.JoinType.Round)
        for comp in U.decompose():
            if comp.area() < o['min_area']:
                continue
            regions += 1
            if (comp - near).area() < o['min_area']:
                short += 1
                continue
            c = _classify(comp, anchor, o)
            xs, ys = c['bad_x'], c['bad_y']
            zb = k * h
            apex += c['apex']
            if c['span'] > 0.0:
                bridges.append(dict(z=_r(zb, 2), span_mm=_r(c['span'], 2), area_mm2=_r(c['area'], 2),
                                    hole_edge_mm2=_r(c['hole_edge'], 2), bbox=[_r(v, 1) for v in comp.bounds()]))
            if not len(xs):
                continue
            inside = np.zeros(len(xs), bool)
            for zn in zones:
                x0, x1, y0, y1, z0, z1 = zn['box']
                if z0 - h <= zb <= z1 + h:
                    sel = (xs >= x0) & (xs <= x1) & (ys >= y0) & (ys <= y1) & ~inside
                    if sel.any():
                        used[zn['id']] = used.get(zn['id'], 0.0) + float(sel.sum()) * o['px'] ** 2
                        inside |= sel
            if (~inside).any():
                out_x, out_y = xs[~inside], ys[~inside]
                unsupported.append(dict(z=_r(zb, 2), area_mm2=_r(float((~inside).sum()) * o['px'] ** 2, 2),
                                        bbox=[_r(float(out_x.min()), 1), _r(float(out_y.min()), 1),
                                              _r(float(out_x.max()), 1), _r(float(out_y.max()), 1)]))
    stale = sorted(zn['id'] for zn in zones if zn['id'] not in used)
    bridges.sort(key=lambda b: -b['span_mm'])
    probs = []
    if unsupported:
        probs.append('%d unsupported region(s) outside the declared support zones, largest %.1f mm2 at z %.2f'
                     % (len(unsupported), max(u['area_mm2'] for u in unsupported),
                        max(unsupported, key=lambda u: u['area_mm2'])['z']))
    if stale:
        probs.append('declared support zone(s) %s are never needed (stale declaration)' % ', '.join(stale))
    row.update(layers=n, regions=regions, short_overhangs=short, bridge_regions=len(bridges),
               longest_bridge_mm=max((b['span_mm'] for b in bridges), default=0.0), apex_line_mm2=_r(apex, 2),
               hole_edge_bridges=sum(1 for b in bridges if b['hole_edge_mm2'] > 0.0),
               hole_edge_mm2=_r(sum(b['hole_edge_mm2'] for b in bridges), 2), bridges=bridges[:12],
               supports_used={k: _r(v, 2) for k, v in sorted(used.items())},
               declared_zones=[dict(id=zn['id'], why=zn.get('why', '')) for zn in zones],
               unsupported=sorted(unsupported, key=lambda u: -u['area_mm2'])[:20],
               status='fail' if probs else 'pass')
    if probs:
        row['error'] = '; '.join(probs)
    return row
