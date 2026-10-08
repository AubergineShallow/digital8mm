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
    them from check 1; this is the stricter companion check)."""
    out = []
    for a, b, kind in L.MATES:
        k = kind.split()[0]
        if k not in ('contact', 'slide', 'clearance'):
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
    rr = L.CAM['wall_bore_d'] / 2 + 0.5
    for part in ('tub', 'hood'):
        Z.append(('J7 camera ring in %s bore' % part, 'gs_camera', part,
                  (L.X_FW_IN + 0.05, L.HOOD['turret_b']['a'][1], ly - rr, ly + rr, lz - rr, lz + rr),
                  L.CAM['wall_bore_d'] / 2 - L.CAM['ring']['r']))
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
        bit_back = dc.cyl_along(D['bit_d'] / 2, -D['bit_len'], -L.PT['head_h'] - 0.1, hp, ax)   # behind the head
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
    for n, ins in enumerate(L.INSERTIONS):
        if only is not None and only not in ins['moving'] and only not in L.present_at(ins['step']):
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
        hits, worst, stub, err = [], {}, False, []
        pts = _path_points(ins['path'], step_mm)
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
                        osh = rows[o]['shape'] if o in rows else dc.box_solid(L.KEEPOUTS[o])
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
        hard_err = [e for e in err if 'fallback' not in e]
        st = 'pass' if not hits and not hard_err else ('stub' if hits and all(h['stub'] for h in hits) and not hard_err
                                                      else 'fail')
        out.append(dict(insertion=ins['id'], step=ins['step'], moving=ins['moving'], obstacles=obst,
                        keepouts=sorted(set(active_ko)), snaps=ins.get('snaps', []), positions=len(pts), hits=hits,
                        errors=err, status=st, method='manifold3d mesh boolean, tessellation 0.05 mm, tol %.1f mm3'
                        % SWEEP_TOL))
    return out


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
    pilot)/2 = 2.25) and material under the head on the counterbore shoulder (>= MIN_WALL_LOADED 1.6)."""
    PT, out = L.PT, []
    for s in L.SCREWS:
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
def registry(L, name):
    """A layout registry list; CRITICAL_FEATURES / REMOVALS / SECTIONS entries are de-duplicated by id (last wins,
    first position kept)."""
    items = list(getattr(L, name, []) or [])
    if name in ('CRITICAL_FEATURES', 'REMOVALS', 'SECTIONS'):
        d = {}
        for it in items:
            d[it['id']] = it
        return list(d.values())
    return items


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


def check_critical_features(L, rows):
    """Finding 2. Every CRITICAL_FEATURES entry measured on the built solid; structural < min_mm FAILs; an origin
    outside the material FAILs (stale entry); every LOAD_BEARING_PARTS member needs >= 1 structural entry (missing
    coverage FAILs). Non-structural entries and NONSTRUCTURAL_EXCEPTIONS are reported, never a pass basis."""
    out = []
    feats = registry(L, 'CRITICAL_FEATURES')
    for f in feats:
        pid = f['part']
        row = dict(kind='feature', id=f['id'], part=pid, min_mm=f.get('min_mm'), structural=bool(f.get('structural', True)),
                   origin=list(f['origin']), direction=list(f['direction']), note=f.get('note', ''))
        cls, need, cls_err = feature_class(L, f)                 # FIXER r2 (M-V-MPS-6): class floor, not the literal
        row.update(cls=cls, entry_min_mm=f.get('min_mm'), min_mm=need)
        gate = (getattr(L, 'FEATURE_GATES', {}) or {}).get(f['id'])
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
        offs, ax = [0.0], None
        if f.get('span'):
            n, step, ax = f['span']
            ax = np.array(ax, float)
            ax /= np.linalg.norm(ax)
            offs = [(k - (n - 1) / 2.0) * step for k in range(int(n))]
        vals, skipped, centre_err, best = [], 0, None, None
        for s in offs:
            p = o + (ax * s if ax is not None else 0.0)
            t, w0, w1, why = chord(r['shape'], tuple(float(x) for x in p), tuple(float(x) for x in d))
            if t is None:
                if abs(s) < 1e-12:
                    centre_err = why
                skipped += 1
                continue
            vals.append(round(t, 3))
            if best is None or t < best[0]:
                best = (t, p + d * w0, p + d * w1)
        row.update(rays=len(offs), rays_outside=skipped, values=vals,
                   measured_mm=None if not vals else round(min(vals), 3),
                   entry=None if best is None else [_r(x, 2) for x in best[1]],
                   exit=None if best is None else [_r(x, 2) for x in best[2]],
                   method='OCP IntCurvesFace_ShapeIntersector chord through origin (B-rep, exact)')
        if r.get('stub'):
            row.update(status='stub', note='measured on the stub envelope (meaningless); ' + row['note'])
        elif centre_err is not None:
            row.update(status='fail', error='stale entry: ' + centre_err)
        elif not row['structural']:
            row['status'] = 'info'
        elif cls_err:
            row.update(status='fail', error=cls_err)
        else:
            row['status'] = 'pass' if row['measured_mm'] >= need - 1e-3 else 'fail'
            if row['status'] == 'pass' and cls in getattr(L, 'FEATURE_CLASS_GATED', ()) and \
                    row['measured_mm'] < L.FDM['MIN_WALL_LOADED'] - 1e-3:
                row['exception'] = 'below the 1.6 loaded rule; kept as a %s only against %s' % (cls, gate)
        out.append(row)
    for pid in registry(L, 'LOAD_BEARING_PARTS'):
        if pid not in L.PARTS:
            out.append(dict(kind='coverage', part=pid, status='info', note='not in PARTS (part removed): no entry needed'))
            continue
        n = sum(1 for f in feats if f['part'] == pid and f.get('structural', True))
        out.append(dict(kind='coverage', part=pid, structural_entries=n, status='pass' if n else 'fail',
                        error=None if n else 'missing coverage: load-bearing part has no structural entry'))
    for e in registry(L, 'NONSTRUCTURAL_EXCEPTIONS'):
        out.append(dict(e, kind='exception', status='info'))
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
        stub = any(rows.get(i, {}).get('stub') for i in list(rem['moving']) + ctx)
        st = 'fail' if (hits or err or missing) else 'pass'
        if st == 'fail' and stub and not err and not missing:
            st = 'stub'
        out.append(dict(removal=rem['id'], moving=rem['moving'], off=rem.get('off', []), context=ctx,
                        release=[z if isinstance(z, str) else 'box' for z in rem.get('release', [])],
                        tool=rem.get('tool', ''), note=rem.get('note', ''), positions=len(pts), hits=hits,
                        errors=err + (['moving part(s) not built: ' + ', '.join(missing)] if missing else []),
                        status=st, method='manifold3d mesh boolean, tessellation 0.05 mm, tol %.1f mm3; service state'
                        % SWEEP_TOL))
        if rem.get('unscrew'):
            ids_ctx = [i for i in ctx if not i.startswith('s_')]
            drv += check_driver(L, rows, screw_ids=set(rem['unscrew']), audit_set_of=lambda _s, c=ids_ctx: c,
                                context='service: ' + rem['id'])
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
