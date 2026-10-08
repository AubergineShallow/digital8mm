"""Independent float-gap check (auditor, geometry): analytic GS camera stack vs production STLs (read-only).
STLs are in print pose; undo FACE_DOWN_ROT and translate to the manifest bbox minimum."""
import json, sys, math
import numpy as np, trimesh


def _rot(ax, deg):
    a = math.radians(deg); c, s_ = math.cos(a), math.sin(a)
    return {'x': np.array([[1, 0, 0], [0, c, -s_], [0, s_, c]]), 'y': np.array([[c, 0, s_], [0, 1, 0], [-s_, 0, c]]),
            'z': np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1]])}[ax]

D = r'C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1/'
ROT = {'-Z': (0, 0, 0), '+Z': (180, 0, 0), '+Y': (-90, 0, 0), '-Y': (90, 0, 0), '+X': (0, 90, 0), '-X': (0, -90, 0)}
FD = {'tub': '-Y', 'hood': '+Z', 'panel': '+Y', 'lens_collar': '+X'}
man = {p['id']: p for p in json.load(open(D + 'out/parts-manifest.json'))['parts']}


def load(pid):
    m = trimesh.load(D + 'out/stl/%s.stl' % pid)
    rx, ry, rz = ROT[FD[pid]]
    v = m.vertices.copy()
    for ang, ax in ((rz, 'z'), (ry, 'y'), (rx, 'x')):      # inverse order, negative angles
        if ang:
            v = v @ _rot(ax, -ang).T
    bb = man[pid]['bbox']
    v = v - v.min(0) + np.array([bb[0], bb[2], bb[4]])
    m.vertices = v
    return m


LY, LZ = 0.0, 60.0
BF = -4.4


def d_cyl(p, r, x0, x1):        # distance outside a solid x-axis cylinder (0 inside)
    rr = np.hypot(p[:, 1] - LY, p[:, 2] - LZ)
    dr = np.maximum(rr - r, 0)
    dx = np.maximum(np.maximum(x0 - p[:, 0], p[:, 0] - x1), 0)
    return np.hypot(dr, dx)


def d_box(p, lo, hi):
    lo, hi = np.array(lo), np.array(hi)
    d = np.maximum(np.maximum(lo - p, p - hi), 0)
    return np.linalg.norm(d, axis=1)


def cam(s):
    hf = BF - 1.2 - s
    hx0 = hf - 10.35
    parts = {
        'housing': lambda p: d_cyl(p, 17.75, hx0, hf),
        'tab': lambda p: d_box(p, (hf - 5.02, -5.08, LZ + 16.75), (hf, 5.08, LZ + 22.1)),
        'screwheads': lambda p: np.minimum(d_box(p, (hf - 4.5, 5.08, 77.4), (hf - 0.5, 7.08, 81.4)),
                                           d_box(p, (hf - 4.5, -7.08, 77.4), (hf - 0.5, -5.08, 81.4))),
        'pcb': lambda p: d_box(p, (hx0 - 1.4, -19, LZ - 19), (hx0, 19, LZ + 19)),
        'cover': lambda p: d_box(p, (hx0 - 1.4 - 6.49, -19.75, LZ - 19.75), (hx0 - 1.4, 19.75, LZ + 19.75)),
        'bfar_head': lambda p: d_cyl(p, 18.0, BF - 1.2, BF),
        'bfar_thread': lambda p: d_cyl(p, 14.4, hf, BF - 1.2) if s > 0 else np.full(len(p), 1e9),
        'adapter': lambda p: d_cyl(p, 15.375, BF, BF + 5.0),
    }
    return parts


def main():
    meshes = {k: load(k) for k in FD}
    pts = {}
    for k, m in meshes.items():
        sel = m.copy()
        # crop to camera region then subdivide for accuracy
        c = sel.triangles_center
        keep = (c[:, 0] > -40) & (c[:, 0] < 3) & (np.abs(c[:, 1]) < 30) & (c[:, 2] > 30) & (c[:, 2] < 90)
        sel.update_faces(keep)
        sel.remove_unreferenced_vertices()
        v, f = trimesh.remesh.subdivide_to_size(sel.vertices, sel.faces, 0.3)
        pts[k] = v
        print(k, 'pts', len(v))
    for s in (0.0, 1.25, 3.0):
        print('--- s', s)
        for nm, fn in cam(s).items():
            row = []
            for k, v in pts.items():
                d = fn(v)
                i = int(np.argmin(d))
                row.append('%s %.3f @(%.2f,%.2f,%.2f)' % (k, d[i], *v[i]))
            print('%-11s' % nm, ' | '.join(row))


if __name__ == '__main__':
    main()
