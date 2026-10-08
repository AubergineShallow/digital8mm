# SPDX-License-Identifier: MIT
"""D2 airflow study: voxel air domain of the baseline arrangement (no CadQuery; numpy + trimesh + manifold3d).

Run (repo root, OUTSIDE the CAD lock, after export_meshes.py):
  .venv-cad/Scripts/python.exe cad/gs8-d2-v1/airflow/voxelize.py [--dx 2.0 1.5]
Inputs : airflow/out/meshes/*.stl + index.json (assembly position), layout.py (VENTS, COTS features, KEEPOUTS).
Outputs: airflow/out/domain-<dx>.npz (shared interface in airflow/NOTES.md), airflow/out/domain/*.png, summary JSON.

Occupancy: each part is sliced (manifold3d) at 3 sub-levels per cell and the slice contours are scan-converted with
the even-odd rule at 3 x 3 sub-points per cell (27 sub-samples per cell, tiny jitter against degenerate hits).
Shell parts (tub, hood, panel, base_grip) are solid where ANY sub-sample is inside (keeps walls >= dx/3 closed);
every other part where >= 14 of 27 sub-samples are inside (volume majority).
"""
import argparse
import ctypes
import json
import os
import sys
import time

import numpy as np

AF = os.path.dirname(os.path.abspath(__file__))
D2 = os.path.dirname(AF)
sys.path.insert(0, D2)
import layout as L  # noqa: E402

OUT = os.path.join(AF, 'out')
MESHES = os.path.join(OUT, 'meshes')
FIGS = os.path.join(OUT, 'domain')
SHELL = ('tub', 'hood', 'panel', 'base_grip')
NSUB = 3
JIT = 1.37e-4                       # mm, breaks ties between sample points and CAD planes
NB = 5                              # buffer cells beyond each vent face (+1 ambient layer)
LAT = 2                             # lateral growth of each buffer box (cells)


def low_priority():
    if os.name == 'nt':
        k = ctypes.windll.kernel32
        k.SetPriorityClass(k.GetCurrentProcess(), 0x4000)       # BELOW_NORMAL


def free_mb():
    try:
        sys.path.insert(0, D2)
        import run_locked
        return run_locked.free_ram_mb()
    except Exception:  # noqa: BLE001
        return float('inf')


# ------------------------------------------------------------------------------------------- grid
class Grid:
    """Cell faces on multiples of dx (x = 0 front face, z = 0 body bottom are cell faces)."""

    def __init__(self, dx, lo, hi):
        self.dx = dx
        self.i0 = np.floor(np.array(lo) / dx).astype(int)
        self.i1 = np.ceil(np.array(hi) / dx).astype(int)
        self.n = tuple(int(v) for v in (self.i1 - self.i0))
        self.origin = (self.i0 + 0.5) * dx                     # centre of cell (0,0,0)

    def centres(self, a):
        return self.origin[a] + self.dx * np.arange(self.n[a])

    def subs(self, a):
        """Sub-sample coordinates along axis a, NSUB per cell."""
        off = (np.arange(NSUB) - (NSUB - 1) / 2) / NSUB * self.dx
        return (self.centres(a)[:, None] + off[None, :]).ravel() + JIT * (1 + 0.37 * a)

    def box_cells(self, b, mode='centre'):
        """Bool mask of cells for box b ({'x':(..),..}). mode 'centre' = centre inside; 'touch' = cell overlaps."""
        m = np.ones(self.n, bool)
        for a, k in enumerate('xyz'):
            c = self.centres(a)
            lo, hi = b[k]
            if mode == 'centre':
                s = (c >= lo) & (c <= hi)
            else:
                s = (c + self.dx / 2 > lo) & (c - self.dx / 2 < hi)
            shp = [1, 1, 1]
            shp[a] = -1
            m &= s.reshape(shp)
        return m

    def ijk(self, p):
        return tuple(int(round((p[a] - self.origin[a]) / self.dx)) for a in range(3))


# ------------------------------------------------------------------------------------------- occupancy
def load_manifold(path):
    import manifold3d as mf
    import trimesh
    m = trimesh.load(path, force='mesh')
    m.merge_vertices()
    man = mf.Manifold(mf.Mesh(vert_properties=np.ascontiguousarray(m.vertices, np.float32),
                              tri_verts=np.ascontiguousarray(m.faces, np.uint32)))
    return m, man


def scan_parity(polys, xs, ys):
    """Even-odd inside test of the sample lattice xs (cols) x ys (rows) against closed contours -> bool[rows, cols]."""
    nr, nc = len(ys), len(xs)
    if not polys or nr == 0 or nc == 0:
        return np.zeros((nr, nc), bool)
    P0 = np.concatenate(polys)
    P1 = np.concatenate([np.roll(p, -1, axis=0) for p in polys])
    y0, y1 = P0[:, 1], P1[:, 1]
    ymin, ymax = np.minimum(y0, y1), np.maximum(y0, y1)
    hy, hx = ys[1] - ys[0] if nr > 1 else 1.0, xs[1] - xs[0] if nc > 1 else 1.0
    jlo = np.clip(np.ceil((ymin - ys[0]) / hy - 1e-9), 0, nr).astype(np.int64)
    jhi = np.clip(np.ceil((ymax - ys[0]) / hy - 1e-9), 0, nr).astype(np.int64)
    # half-open [ymin, ymax): exact for uniform rows
    cnt = jhi - jlo
    keep = cnt > 0
    if not keep.any():
        return np.zeros((nr, nc), bool)
    e = np.repeat(np.nonzero(keep)[0], cnt[keep])
    start = np.repeat(np.cumsum(cnt[keep]) - cnt[keep], cnt[keep])
    j = jlo[e] + (np.arange(len(e)) - start)
    yr = ys[j]
    t = (yr - y0[e]) / (y1[e] - y0[e])
    xc = P0[e, 0] + t * (P1[e, 0] - P0[e, 0])
    k = np.clip(np.ceil((xc - xs[0]) / hx), 0, nc).astype(np.int64)
    h = np.bincount(j * (nc + 1) + k, minlength=nr * (nc + 1)).reshape(nr, nc + 1)
    return (np.cumsum(h, axis=1)[:, :nc] & 1).astype(bool)


def part_count(G, man, bounds):
    """uint8[nx,ny,nz] = number of the 27 sub-samples of each cell inside the part (0 outside its bbox)."""
    cnt = np.zeros(G.n, np.uint8)
    lo, hi = np.array(bounds[0]), np.array(bounds[1])
    rng = []
    for a in range(3):
        c = G.centres(a)
        sel = np.nonzero((c + G.dx >= lo[a]) & (c - G.dx <= hi[a]))[0]
        if len(sel) == 0:
            return cnt
        rng.append((sel[0], sel[-1] + 1))
    xs = G.subs(0)[rng[0][0] * NSUB:rng[0][1] * NSUB]
    ys = G.subs(1)[rng[1][0] * NSUB:rng[1][1] * NSUB]
    zs = G.subs(2)
    nxw, nyw = rng[0][1] - rng[0][0], rng[1][1] - rng[1][0]
    for kz in range(rng[2][0], rng[2][1]):
        acc = np.zeros((nyw, nxw), np.uint8)
        for z in zs[kz * NSUB:(kz + 1) * NSUB]:
            if z <= lo[2] or z >= hi[2]:
                continue
            polys = [np.asarray(p, float) for p in man.slice(float(z)).to_polygons()]
            ins = scan_parity(polys, xs, ys)
            acc += ins.reshape(nyw, NSUB, nxw, NSUB).sum(axis=(1, 3)).astype(np.uint8)
        cnt[rng[0][0]:rng[0][1], rng[1][0]:rng[1][1], kz] = acc.T
    return cnt


# ------------------------------------------------------------------------------------------- morphology (no scipy)
def dilate(m, n=1, diag=False):
    """6-neighbour (or 26-neighbour with diag) dilation, n steps."""
    for _ in range(n):
        d = m.copy()
        if diag:                         # 26-neighbour = separable 3-tap OR along each axis
            for a in range(3):
                s = np.moveaxis(d, a, 0)
                t = s.copy()
                t[1:] |= s[:-1]
                t[:-1] |= s[1:]
                d = np.moveaxis(t, 0, a)
        else:
            for a in range(3):
                s = np.moveaxis(m, a, 0)
                t = np.moveaxis(d, a, 0)
                t[1:] |= s[:-1]
                t[:-1] |= s[1:]
        m = d
    return m


def flood(seed, passable, maxit=100000):
    cur = seed & passable
    for _ in range(maxit):
        nxt = dilate(cur) & passable
        if np.array_equal(nxt, cur):
            return cur
        cur = nxt
    raise RuntimeError('flood did not converge')


def components(passable):
    """Connected components (6-neighbour) by min-label propagation -> (labels int32, -1 outside; sizes dict)."""
    lab = np.where(passable, np.arange(passable.size, dtype=np.int32).reshape(passable.shape), np.int32(2**31 - 1))
    big = np.int32(2**31 - 1)
    while True:
        old = lab.copy()
        for a in range(3):
            s = np.moveaxis(lab, a, 0)
            p = np.moveaxis(passable, a, 0)
            m = np.minimum(s[1:], s[:-1])
            s[1:] = np.where(p[1:], np.minimum(s[1:], m), big)
            s[:-1] = np.where(p[:-1], np.minimum(s[:-1], m), big)
        if np.array_equal(old, lab):
            break
    lab = np.where(passable, lab, -1)
    ids, cnt = np.unique(lab[lab >= 0], return_counts=True)
    return lab, dict(zip(ids.tolist(), cnt.tolist()))


def boundary_faces(n):
    m = np.zeros(n, bool)
    m[0], m[-1], m[:, 0], m[:, -1], m[:, :, 0], m[:, :, -1] = True, True, True, True, True, True
    return m


# ------------------------------------------------------------------------------------------- vents
AX = {'x': 0, 'y': 1, 'z': 2}


def vent_geometry(vid, v):
    """(axis, sign, wall interval along the normal, lateral box) for a layout.VENTS entry."""
    face = v['face']
    sgn, ax = (1 if face[0] == '+' else -1), face[1]
    b = dict(v['box'])
    wall = list(b[ax])
    if v.get('tub_window') is not None:          # front vents: hood plate slots + tub window in series
        tw = v['tub_window'][ax]
        wall = [min(wall[0], tw[0]), max(wall[1], tw[1])]
    return AX[ax], sgn, tuple(wall), b


def vent_zone(G, b, a, wall):
    """Cells whose interval along axis a overlaps the wall and whose centre lies inside the lateral box."""
    bb = dict(b)
    bb['xyz'[a]] = wall
    m = G.box_cells(bb, mode='centre')
    c = G.centres(a)
    s = (c + G.dx / 2 > wall[0] + 1e-6) & (c - G.dx / 2 < wall[1] - 1e-6)
    lat = np.ones(G.n, bool)
    for k, ax in enumerate('xyz'):
        if k == a:
            continue
        ck = G.centres(k)
        shp = [1, 1, 1]
        shp[k] = -1
        lat &= ((ck >= bb[ax][0]) & (ck <= bb[ax][1])).reshape(shp)
    shp = [1, 1, 1]
    shp[a] = -1
    del m
    return lat & s.reshape(shp)


def buffer_box(G, b, a, sgn, wall):
    """Outside buffer: NB cells + 1 ambient layer beyond the outer wall face, lateral box grown by LAT cells."""
    bb = {}
    for k, ax in enumerate('xyz'):
        if k == a:
            f = wall[1] if sgn > 0 else wall[0]
            bb[ax] = (f, f + sgn * (NB + 1) * G.dx) if sgn > 0 else (f - (NB + 1) * G.dx, f)
        else:
            bb[ax] = (b[ax][0] - LAT * G.dx, b[ax][1] + LAT * G.dx)
    m = G.box_cells(bb, mode='centre')
    # ambient = far layer + lateral rim of the buffer box
    amb = np.zeros(G.n, bool)
    idx = np.nonzero(m)
    lo = [idx[k].min() for k in range(3)]
    hi = [idx[k].max() for k in range(3)]
    for k in range(3):
        sl = [slice(lo[j], hi[j] + 1) for j in range(3)]
        if k == a:
            sl[k] = slice(hi[k], hi[k] + 1) if sgn > 0 else slice(lo[k], lo[k] + 1)
            amb[tuple(sl)] = True
        else:
            for e in (lo[k], hi[k]):
                s2 = list(sl)
                s2[k] = slice(e, e + 1)
                amb[tuple(s2)] = True
    return m, amb & m


# ------------------------------------------------------------------------------------------- domain
LABELS = {0: 'interior air', 1: 'solid (part)', 2: 'exterior inactive (solid)', 3: 'outside buffer air',
          4: 'ambient reservoir', 5: 'vent porous zone', 6: 'fan actuator (blower interior)', 7: 'fan intake opening',
          8: 'fin block (porous, X)', 9: 'dropped pocket (solid)', 10: 'plug (closed hole, solid)'}
INTAKE_R = 9.0          # mm, blower intake radius = the proxy's hub circle (cots.cooler, r 9.0): ESTIMATE


def load_parts(index):
    parts = []
    for pid, r in index['parts'].items():
        if r.get('stl') is None:
            continue
        mesh, man = load_manifold(os.path.join(OUT, r['stl']))
        parts.append(dict(id=pid, kind=r['kind'], mesh_watertight=bool(mesh.is_watertight),
                          manifold_status=str(man.status()), man=man, bounds=r['bounds'], stub=r.get('stub')))
    return parts


def occupancy(G, parts, log):
    solid = np.zeros(G.n, bool)
    best = np.zeros(G.n, np.uint8)
    part = np.full(G.n, -1, np.int16)
    rows = []
    for i, p in enumerate(parts):
        t0 = time.time()
        if p['man'].is_empty():
            rows.append(dict(id=p['id'], error='empty manifold (%s)' % p['manifold_status']))
            log('  %-14s EMPTY manifold %s' % (p['id'], p['manifold_status']))
            continue
        c = part_count(G, p['man'], p['bounds'])
        s = (c > 0) if p['id'] in SHELL else (c >= 14)
        vol_vox = float(c.sum()) / 27 * G.dx ** 3
        vol_true = float(p['man'].volume())
        upd = s & (c > best)
        part[upd] = i
        best[upd] = c[upd]
        part[s & (part < 0)] = i
        solid |= s
        glo = G.origin - G.dx / 2
        ghi = G.origin + G.dx * (np.array(G.n) - 0.5)
        inside = bool(np.all(np.array(p['bounds'][0]) >= glo) and np.all(np.array(p['bounds'][1]) <= ghi))
        rows.append(dict(id=p['id'], rule='any' if p['id'] in SHELL else 'majority', cells=int(s.sum()),
                         vol_subsample_mm3=round(vol_vox, 1), vol_mesh_mm3=round(vol_true, 1), inside_grid=inside,
                         vol_err=round(vol_vox / max(vol_true, 1e-9) - 1, 4) if inside else None,
                         seconds=round(time.time() - t0, 2)))
        log('  %-14s cells %7d sub-sample vol err %s  %.1fs' % (p['id'], s.sum(), rows[-1]['vol_err']
                                                                 if inside else 'n/a (partly outside grid)',
                                                                 time.time() - t0))
    return solid, part, rows


def cell_box(G, b, mode='centre'):
    return G.box_cells(b, mode)


def fan_model(G, label):
    """Carve the blower proxy into housing walls + intake + actuator; fin block; outlet plane. Returns masks."""
    c = L.COTS['cooler']
    fb, bx = c['features']['blower'], c['box']
    fin_z = (23.4, 30.5)                          # cots.cooler fin height (plate top .. fin top)
    blow = G.box_cells(dict(x=fb['x'], y=fb['y'], z=(23.4, fb['z'][1])), 'centre')
    idx = np.nonzero(blow)
    lo = [idx[k].min() for k in range(3)]
    hi = [idx[k].max() for k in range(3)]
    inner = np.zeros(G.n, bool)
    inner[lo[0] + 1:hi[0] + 1, lo[1] + 1:hi[1], lo[2]:hi[2]] = True       # walls: -X, +-Y, top; +X layer kept
    zc = G.centres(2)
    in_fin_z = ((zc >= fin_z[0]) & (zc <= fin_z[1])).reshape(1, 1, -1)
    outlet_layer = np.zeros(G.n, bool)
    outlet_layer[hi[0]] = True
    inner &= ~(outlet_layer & ~in_fin_z)                                   # +X face above the fins = wall
    top = np.zeros(G.n, bool)
    top[lo[0] + 1:hi[0], lo[1] + 1:hi[1], hi[2]] = True
    xc, yc = (fb['x'][0] + fb['x'][1]) / 2, (fb['y'][0] + fb['y'][1]) / 2
    X, Y = np.meshgrid(G.centres(0), G.centres(1), indexing='ij')
    circ = ((X - xc) ** 2 + (Y - yc) ** 2 <= INTAKE_R ** 2)[:, :, None]
    intake = top & circ
    fins = G.box_cells(dict(x=(fb['x'][1], bx['x'][1]), y=bx['y'], z=fin_z), 'centre') & ~blow
    # fin exit plane: first cell layer past the fin block (+X), over the fin y/z extent
    fidx = np.nonzero(fins)
    fx = fidx[0].max() + 1
    outlet = np.zeros(G.n, bool)
    outlet[fx] = fins[fx - 1]
    return dict(blower_box=blow, actuator=inner, intake=intake, fins=fins, outlet=outlet,
                info=dict(blower_cells=[lo, hi], intake_r_mm=INTAKE_R, intake_centre=[xc, yc],
                          fin_z=fin_z, fin_x=[fb['x'][1], bx['x'][1]], fin_y=list(bx['y']), outlet_i=int(fx),
                          fin_section_discrete_mm2=float(fins.any(axis=0).sum() * G.dx ** 2),
                          fin_section_proxy_mm2=round((bx['y'][1] - bx['y'][0]) * (fin_z[1] - fin_z[0]), 1),
                          fin_length_cells=int(np.unique(fidx[0]).size), fin_length_mm=round(bx['x'][1] - fb['x'][1], 2),
                          blower_outlet_open_discrete_mm2=float((inner & outlet_layer).sum() * G.dx ** 2),
                          blower_outlet_proxy_mm2=round((fb['y'][1] - fb['y'][0]) * (fin_z[1] - fin_z[0]), 1),
                          intake_area_discrete_mm2=float(intake.sum() * G.dx ** 2),
                          intake_area_circle_mm2=round(np.pi * INTAKE_R ** 2, 1)))


def shift(m, a, s):
    """Mask moved by s cells along axis a (no wrap)."""
    o = np.zeros_like(m)
    src = [slice(None)] * 3
    dst = [slice(None)] * 3
    if s > 0:
        src[a], dst[a] = slice(0, -s), slice(s, None)
    else:
        src[a], dst[a] = slice(-s, None), slice(0, s)
    o[tuple(dst)] = m[tuple(src)]
    return o


def geodesic(seed, passable, maxit=5000):
    """BFS distance in cells (6-neighbour) from seed through passable; -1 unreachable."""
    d = np.full(seed.shape, -1, np.int32)
    cur = seed & passable
    d[cur] = 0
    seen = cur.copy()
    for k in range(1, maxit):
        front = dilate(cur) & passable & ~seen
        if not front.any():
            break
        d[front] = k
        seen |= front
        cur = front
    return d


def build(dx, parts, log):
    G = Grid(dx, (-156.0, L.YR - (NB + 3) * dx, -2 * dx), (L.X_FRONT + (NB + 3) * dx, L.YL + 2.0, L.H + (NB + 3) * dx))
    log('grid dx %.2f n %s origin %s (%d cells)' % (dx, G.n, np.round(G.origin, 3).tolist(), np.prod(G.n)))
    solid, part, occ_rows = occupancy(G, parts, log)
    pid = [p['id'] for p in parts]
    shell_solid = np.isin(part, [pid.index(s) for s in SHELL if s in pid])
    # plugs: floor lead holes into the grip/battery bay (bay excluded from the domain) + microSD tweezer slot
    plugs = {}
    for h, b in L.FLOOR_HOLES.items():
        plugs['floor_' + h] = G.box_cells(b, 'touch') & ~solid
    sd = L.KEEPOUTS['ko_sd']
    plugs['sd_slot'] = G.box_cells(dict(x=(L.X_FW_IN - 0.6, L.X_FRONT), y=sd['y'], z=sd['z']), 'touch') & ~solid
    plug_all = np.zeros(G.n, bool)
    for m in plugs.values():
        plug_all |= m
    vents = {}
    zones = np.zeros(G.n, bool)
    for vid, v in L.VENTS.items():
        a, sgn, wall, b = vent_geometry(vid, v)
        z = vent_zone(G, b, a, wall)
        buf, amb = buffer_box(G, b, a, sgn, wall)
        vents[vid] = dict(a=a, sgn=sgn, wall=wall, box=b, zone=z, buf=buf, amb=amb)
        zones |= z
    closed = solid | plug_all | zones
    ext = flood(boundary_faces(G.n) & ~closed, ~closed)
    fan = fan_model(G, None)
    fi = fan['info']
    seed = np.zeros(G.n, bool)
    seed[G.ijk((fi['intake_centre'][0], fi['intake_centre'][1], L.COTS['cooler']['box']['z'][1] + 2.5 * dx))] = True
    leak = bool((seed & ext).any())
    interior0 = ~closed & ~ext
    lab, sizes = components(interior0)
    if leak:
        raise RuntimeError('the body interior connects to the outside without passing a vent (leak): see NOTES')
    main = int(lab[seed][0])
    pockets = []
    for k, n in sorted(sizes.items(), key=lambda t: -t[1]):
        if k == main:
            continue
        m = lab == k
        ii = np.nonzero(m)
        cen = [round(float(G.origin[q] + dx * ii[q].mean()), 1) for q in range(3)]
        near = np.unique(part[dilate(m) & solid])
        pockets.append(dict(cells=int(n), vol_mm3=round(n * dx ** 3, 1), centroid=cen,
                            bounded_by=[pid[j] for j in near if j >= 0]))
    return G, dict(solid=solid, part=part, pid=pid, occ=occ_rows, shell_solid=shell_solid, plugs=plugs,
                   plug_all=plug_all, vents=vents, zones=zones, ext=ext, fan=fan, seed=seed, lab=lab, main=main,
                   pockets=pockets, sizes=sizes)


HEAT = {   # component -> (source, how): air cells next to the proxy receive its heat (SoC heat -> fin block)
    'x1203': ('box', 'X1203 charger/boost field proxy box (cots.x1203 "parts": x0+12..x0+40, y0+12..y1-12, z 7.6..11)'),
    'evf_board': ('part', 'evf_board'),
    'camera': ('part', 'gs_camera'),
    'usb_stick': ('part', 'usb_stick'),
    'pi_board': ('box', 'Pi 5 PCB slab + underside parts (PI x/y, z 16.0..21.4); the jack blocks get no heat'),
}


def finish(G, D, log):
    dx, n = G.dx, G.n
    solid, part, pid, fan = D['solid'], D['part'], D['pid'], D['fan']
    label = np.ones(n, np.int8)                       # 1 = solid part
    interior = D['lab'] == D['main']
    label[interior] = 0
    label[D['ext']] = 2
    pocket = (D['lab'] >= 0) & ~interior
    label[pocket] = 9
    label[D['plug_all']] = 10
    masks, vmeta = {}, {}
    amb_all = np.zeros(n, bool)
    for vid, v in D['vents'].items():
        a, sgn = v['a'], v['sgn']
        cots_block = v['zone'] & solid & ~D['shell_solid']
        z = v['zone'] & ~cots_block
        bufair = v['buf'] & D['ext'] & ~solid & ~z
        label[bufair] = 3
        amb = v['amb'] & bufair
        amb_all |= amb
        label[z] = 5
        masks['vent__' + vid] = z
        thick = np.unique(np.nonzero(z)[a]).size
        face = z.any(axis=a).sum()
        vb = v['box']
        lat = [k for k in 'xyz' if k != 'xyz'[a]]
        vmeta[vid] = dict(normal=[float(sgn) if k == a else 0.0 for k in range(3)], axis='xyz'[a],
                          wall_interval_mm=list(v['wall']), thickness_cells=int(thick), zone_cells=int(z.sum()),
                          face_cells=int(face), face_area_discrete_mm2=round(float(face) * dx * dx, 1),
                          face_area_box_mm2=round((vb[lat[0]][1] - vb[lat[0]][0]) * (vb[lat[1]][1] - vb[lat[1]][0]), 1),
                          area_ratio_discrete_to_box=round(float(face) * dx * dx / max(
                              (vb[lat[0]][1] - vb[lat[0]][0]) * (vb[lat[1]][1] - vb[lat[1]][0]), 1e-9), 3),
                          cells_blocked_by_cots=int(cots_block.sum()),
                          blocked_by=sorted({pid[j] for j in np.unique(part[cots_block]) if j >= 0}),
                          slot_w=L.VENTS[vid]['slot_w'], pitch=L.VENTS[vid]['pitch'],
                          open_area_ratio_slots=round(L.VENTS[vid]['slot_w'] / L.VENTS[vid]['pitch'], 3))
    label[amb_all] = 4
    # fan: housing walls solid, intake open, actuator, fin block porous
    other = solid & (part != pid.index('cooler'))          # never carve another part's cells
    for k in ('actuator', 'intake', 'fins', 'outlet'):
        fan[k] = fan[k] & ~other
    housing = fan['blower_box'] & ~fan['actuator'] & ~fan['intake']
    label[housing] = 1
    label[fan['actuator']] = 6
    label[fan['intake']] = 7
    label[fan['fins']] = 8
    fluid = np.isin(label, [0, 3, 4, 5, 6, 7, 8])
    solid_out = ~fluid
    masks['ambient'] = label == 4
    masks['fan_actuator'] = label == 6
    masks['fan_intake'] = label == 7
    masks['fin_block'] = label == 8
    masks['fan_outlet'] = fan['outlet'] & fluid
    air = label == 0
    # heat masks: interior air cells within 1 cell (26-neighbour) of the proxy; 2 cells if fewer than 8
    hmeta = {}
    for comp, (src, how) in HEAT.items():
        if comp == 'pi_board':
            cells = G.box_cells(dict(x=L.PI['x'], y=L.PI['y'], z=(16.0, 21.4)), 'touch')
        elif src == 'box':
            x0, x1 = L.PI['x']
            y0, y1 = L.PI['y']
            cells = G.box_cells(dict(x=(x0 + 12.0, x0 + 40.0), y=(y0 + 12.0, y1 - 12.0), z=(7.6, 11.0)), 'touch')
        else:
            cells = part == pid.index(how)
        hm = dilate(cells, 1, diag=True) & air
        rad = 1
        if hm.sum() < 8:
            hm, rad = dilate(cells, 2, diag=True) & air, 2
        masks['heat__' + comp] = hm
        hmeta[comp] = dict(source=how, proxy_cells=int(cells.sum()), air_cells=int(hm.sum()), radius_cells=rad)
    masks['heat__soc'] = masks['fin_block'].copy()
    hmeta['soc'] = dict(source='SoC heat into the fin block air (cooler fins)', air_cells=int(masks['heat__soc'].sum()))
    # probes
    up1 = shift(masks['fan_intake'], 2, 1) & air
    up2 = shift(masks['fan_intake'], 2, 2) & air
    masks['probe__fan_intake_air'] = up1 | up2
    masks['probe__evf_board'] = masks['heat__evf_board']
    masks['probe__x1203_ic'] = masks['heat__x1203']
    masks['probe__pi_board'] = masks['heat__pi_board']
    masks['probe__camera'] = masks['heat__camera']
    masks['probe__usb_stick'] = masks['heat__usb_stick']
    masks['probe__exhaust_plenum'] = G.box_cells(L.KEEPOUTS['ko_exhaust'], 'centre') & air
    masks['probe__fin_exit'] = masks['fan_outlet']
    masks['probe__roof_inlet_inner'] = shift(masks['vent__inlet_roof'], 2, -1) & air
    for vid, v in D['vents'].items():
        masks['probe__outside_' + vid] = shift(masks['vent__' + vid], v['a'], v['sgn']) & (label == 3) | \
            (shift(masks['vent__' + vid], v['a'], v['sgn']) & (label == 4))
    for k, m in D['plugs'].items():
        masks['leak__' + k] = m
    return label, fluid, solid_out, masks, vmeta, hmeta


def connectivity(G, label, fluid, masks, vmeta):
    """Every vent must reach the fan intake (outside the blower) and the fin exit through air."""
    lab, sizes = components(fluid)
    comp = sorted(sizes.values(), reverse=True)
    no_fan = fluid & ~masks['fan_actuator'] & ~masks['fin_block']
    d_in = geodesic(masks['fan_intake'], fluid & ~masks['fan_actuator'] & ~masks['fin_block'] | masks['fan_intake'])
    d_out = geodesic(masks['fan_outlet'], no_fan | masks['fan_outlet'])
    res = dict(fluid_components=len(comp), component_cells=comp[:5])
    for vid in vmeta:
        z = masks['vent__' + vid]
        a = d_in[z]
        b = d_out[z]
        vmeta[vid]['path_cells_from_fan_intake'] = int(a[a >= 0].min()) if (a >= 0).any() else None
        vmeta[vid]['path_cells_from_fin_exit'] = int(b[b >= 0].min()) if (b >= 0).any() else None
    res['all_vents_reach_intake'] = all(v['path_cells_from_fan_intake'] is not None for v in vmeta.values())
    res['all_vents_reach_fin_exit'] = all(v['path_cells_from_fin_exit'] is not None for v in vmeta.values())
    amb = masks['ambient']
    res['ambient_reachable_from_intake'] = bool((d_in[amb] >= 0).any())
    return res


# ------------------------------------------------------------------------------------------- output
COL = ['#cfe6f7', '#8a8d91', '#f4f4f2', '#a6e3e0', '#5fb760', '#f08a24', '#d62728', '#c03fbf', '#f2d43d', '#7d4fb0',
       '#111111']
SLICES = [('z', 27.0, 'cooler fins + blower'), ('z', 33.0, 'blower top, out_corner'), ('z', 13.0, 'X1203 sandwich'),
          ('x', -7.0, 'exhaust plenum'), ('x', -140.0, 'EVF board'), ('y', -10.0, 'roof inlet - blower - fins - front'),
          ('y', -33.6, 'right wall vents'), ('x', -58.0, 'roof inlet over the blower')]


def render(G, label, masks, tag, log):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap, BoundaryNorm
    from matplotlib.patches import Patch
    os.makedirs(FIGS, exist_ok=True)
    cmap = ListedColormap(COL)
    norm = BoundaryNorm(np.arange(-0.5, 11.5), cmap.N)
    heat = np.zeros(G.n, bool)
    for k, m in masks.items():
        if k.startswith('heat__') and k != 'heat__soc':
            heat |= m
    files = []
    for ax, val, what in SLICES:
        a = 'xyz'.index(ax)
        i = int(round((val - G.origin[a]) / G.dx))
        sl = np.take(label, i, axis=a)
        hs = np.take(heat, i, axis=a)
        oth = [k for k in range(3) if k != a]
        lo = [G.origin[k] - G.dx / 2 for k in oth]
        hi = [G.origin[k] + G.dx * (G.n[k] - 0.5) for k in oth]
        w = 5.0 * (hi[0] - lo[0]) / max(hi[1] - lo[1], 1) + 2.5
        fig, axp = plt.subplots(figsize=(min(max(w, 6.0), 14.0), 5.2), dpi=110)
        axp.imshow(sl.T, origin='lower', extent=(lo[0], hi[0], lo[1], hi[1]), cmap=cmap, norm=norm,
                   interpolation='nearest')
        yy, xx = np.nonzero(hs.T)
        axp.scatter(lo[0] + (xx + 0.5) * G.dx, lo[1] + (yy + 0.5) * G.dx, s=2, c='#7a0019', marker='s', lw=0)
        axp.set_xlabel('xyz'[oth[0]] + ' (mm)')
        axp.set_ylabel('xyz'[oth[1]] + ' (mm)')
        axp.set_title('D2 air domain dx %.1f: %s = %.1f (%s); dark red dots = heat-source air' % (G.dx, ax, val, what),
                      fontsize=9)
        axp.set_aspect('equal')
        present = sorted(set(np.unique(sl).tolist()))
        axp.legend(handles=[Patch(color=COL[k], label=LABELS[k]) for k in present], fontsize=6, loc='upper left',
                   bbox_to_anchor=(1.01, 1.0))
        fig.tight_layout()
        fn = os.path.join(FIGS, 'slice-%s-%s%s.png' % (tag, ax, ('%g' % val).replace('-', 'm')))
        fig.savefig(fn)
        plt.close(fig)
        files.append(os.path.relpath(fn, OUT).replace('\\', '/'))
    log('rendered %d slices' % len(files))
    return files


def save(G, D, label, fluid, solid_out, masks, vmeta, hmeta, conn, figs, index, tag):
    counts = {LABELS[k]: int((label == k).sum()) for k in LABELS}
    finfo = {k: (np.asarray(v).tolist() if isinstance(v, (list, tuple)) else v) for k, v in D['fan']['info'].items()}
    meta = dict(
        dx_mm=G.dx, shape=list(G.n), origin_mm=G.origin.tolist(), frame='layout.py assembly mm, X fwd, Y left, Z up',
        source=dict(revision=index['revision'], lens=index['lens'], variant=index.get('variant'),
                    mesh_sources=index.get('sources'), mesh_tol_mm=index.get('tol_mm')),
        occupancy=dict(rule='27 sub-samples per cell; shell parts %s solid if any sub-sample inside, others if >= 14'
                       % list(SHELL), parts=D['occ']),
        label_legend={str(k): v for k, v in LABELS.items()}, label_counts=counts,
        fan=dict(force_unit=[1.0, 0.0, 0.0], note='body force +X in mask__fan_actuator (blower interior, from the '
                 'intake to the fin entry); walls -X, +-Y, top are solid cells (1 cell), bottom = cooler plate; the +X '
                 'layer is open only over the fin height', intake_radius_mm=INTAKE_R,
                 intake_basis='proxy hub circle r 9.0 in cots.cooler (ESTIMATE, no published intake size used)',
                 **finfo),
        fins=dict(porous_axis='x', plate_normal='y', note='cots.cooler fins: 1.0 thick plates at 2.5 pitch normal to '
                  'Y, open on top in the proxy (no shroud modelled): low resistance along X (and Z between plates), '
                  'high along Y; metal volume fraction in the proxy fin block = 0.4'),
        vents=vmeta, heat=hmeta, connectivity=conn,
        pockets=dict(policy='every interior air region not connected to the main body air (the region holding the fan '
                     'intake) is dropped (label 9, solid): with no path to the fan or a vent it carries no forced '
                     'flow', list=D['pockets'][:40], n=len(D['pockets']),
                     total_mm3=round(sum(p['vol_mm3'] for p in D['pockets']), 1)),
        plugs=dict(note='closed (solid, label 10): floor_pigtail and floor_run_lead = lead holes into the grip / '
                   'battery bay (bay excluded, holes treated as closed by the leads + grommet); sd_slot = microSD '
                   'tweezer slot through both front walls (ko_sd) treated closed (card in place; a real leak path of '
                   'about 12 x 2.3 mm minus the card). mask__leak__* lets the solver open them as a sensitivity',
                   cells={k: int(m.sum()) for k, m in D['plugs'].items()}),
        masks={k: int(m.sum()) for k, m in masks.items()}, figures=figs,
        interior_air_mm3=round(float((label == 0).sum()) * G.dx ** 3, 1),
        fluid_cells=int(fluid.sum()))
    arr = dict(dx=np.float32(G.dx), origin=G.origin.astype(np.float64), solid=solid_out, label=label,
               part=D['part'], part_legend=np.array(D['pid']), meta_json=np.array(json.dumps(meta)))
    for k, m in masks.items():
        arr['mask__' + k] = m
    fn = os.path.join(OUT, 'domain-%s.npz' % tag)
    np.savez_compressed(fn, **arr)
    with open(os.path.join(FIGS, 'summary-%s.json' % tag), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(meta, f, indent=1)
    return fn, meta


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--dx', type=float, nargs='+', default=[2.0, 1.5])
    args = ap.parse_args(argv)
    low_priority()
    fm = free_mb()
    if fm < 1200:
        print('free RAM %.0f MB < 1200: retry later' % fm)
        return 75
    with open(os.path.join(MESHES, 'index.json'), encoding='utf-8') as f:
        index = json.load(f)
    lines = []

    def log(s):
        print(s, flush=True)
        lines.append(s)
    t0 = time.time()
    parts = load_parts(index)
    log('loaded %d parts (%.1fs); not watertight: %s; manifold errors: %s' % (
        len(parts), time.time() - t0, [p['id'] for p in parts if not p['mesh_watertight']],
        [(p['id'], p['manifold_status']) for p in parts if 'NoError' not in p['manifold_status']]))
    os.makedirs(FIGS, exist_ok=True)
    for dx in args.dx:
        tag = '%.1f' % dx
        G, D = build(dx, parts, log)
        label, fluid, solid_out, masks, vmeta, hmeta = finish(G, D, log)
        conn = connectivity(G, label, fluid, masks, vmeta)
        log('dx %s: interior air %d cells, pockets %d (%.0f mm3), conn %s' % (
            tag, (label == 0).sum(), len(D['pockets']), sum(p['vol_mm3'] for p in D['pockets']), conn))
        figs = render(G, label, masks, tag, log)
        fn, meta = save(G, D, label, fluid, solid_out, masks, vmeta, hmeta, conn, figs, index, tag)
        log('wrote %s (%.1fs)' % (fn, time.time() - t0))
        with open(os.path.join(FIGS, 'voxelize.log'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(lines) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
