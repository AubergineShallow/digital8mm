"""r3 rib-tip evidence (no CAD, trimesh/manifold3d on built STLs), adapted from candidate-fr1/_thin_spot_rib_l.py:
dense local ray-thickness scan (the checks.thin_wall cone method, 20000 samples within 3 mm) round the rib_l gusset tip,
plus the tub volume change and the bounding boxes of the boolean differences old - new and new - old.
STLs are in print pose (tub face_down -Y), mapped to assembly coordinates: x = px - 154, y = pz - 35, z = 97.3 - py.
Usage (repo root): python cad/gs8-d2-v1/_thin_spot_rib_l.py <old tub.stl> <new tub.stl> [x y z]"""
import sys, os, numpy as np, trimesh, hashlib, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import _ray_hits

OLD, NEW = sys.argv[1], sys.argv[2]
R = 3.0


def load(p):
    m = trimesh.load(p)
    V0 = np.asarray(m.vertices)
    return trimesh.Trimesh(np.c_[V0[:, 0] - 154.0, V0[:, 2] - 35.0, 97.3 - V0[:, 1]], np.asarray(m.faces), process=False)


def scan(m, P):
    V, F = np.asarray(m.vertices), np.asarray(m.faces)
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    lo = np.minimum(np.minimum(a, b), c); hi = np.maximum(np.maximum(a, b), c)
    keep = np.linalg.norm(np.clip(P, lo, hi) - P, axis=1) < R
    ar = np.linalg.norm(np.cross(b - a, c - a), axis=1) / 2; N0 = m.face_normals
    rng = np.random.default_rng(1); idx = np.where(keep & (ar > 1e-9))[0]
    pick = rng.choice(idx, size=20000, p=ar[idx] / ar[idx].sum())
    r1, r2 = rng.random(20000), rng.random(20000); fl = r1 + r2 > 1; r1[fl], r2[fl] = 1 - r1[fl], 1 - r2[fl]
    pts = a[pick] + r1[:, None] * (b[pick] - a[pick]) + r2[:, None] * (c[pick] - a[pick]); N = N0[pick]
    s = np.linalg.norm(pts - P, axis=1) < R; pts, N = pts[s], N[s]
    O = pts - N * 1e-3
    th = _ray_hits(V, F, O, -N); th = np.where(np.isfinite(th), th, 6.0)
    ref = np.where(np.abs(N[:, 0:1]) < 0.9, np.array([[1., 0, 0]]), np.array([[0, 1., 0]]))
    U = np.cross(N, ref); U /= np.linalg.norm(U, axis=1)[:, None]; W = np.cross(N, U)
    ct, st = math.cos(math.radians(30)), math.sin(math.radians(30))
    for k in range(6):
        ph = math.radians(60 * k); Dk = -N * ct + (U * math.cos(ph) + W * math.sin(ph)) * st
        dk = _ray_hits(V, F, O, Dk); th = np.maximum(th, np.where(np.isfinite(dk), dk, 6.0) * ct)
    i = np.argmin(th); bad = th < 1.15
    return 'n=%d min=%.3f at %s nrm %s; share<1.15=%.3f; bbox<1.15 %s' % (
        len(th), th[i], np.round(pts[i], 2), np.round(N[i], 2), bad.mean(),
        (np.round(pts[bad].min(0), 2).tolist(), np.round(pts[bad].max(0), 2).tolist()) if bad.any() else '-')


mo, mn = load(OLD), load(NEW)
for tag, p, m in (('old', OLD, mo), ('new', NEW, mn)):
    print(tag, hashlib.sha256(open(p, 'rb').read()).hexdigest()[:12], 'watertight', m.is_watertight,
          'volume %.3f mm3' % m.volume)
    pts = [np.array([float(x) for x in sys.argv[3:6]])] if len(sys.argv) > 5 else \
        [np.array([-12.95, 31.85, z]) for z in (5.0, 12.0, 20.75, 30.0, 38.0)] + \
        [np.array([-12.15, 31.6, z]) for z in (5.0, 12.0, 20.75, 30.0, 38.0)]
    for P in pts:
        try:
            print('  scan @', P.tolist(), scan(m, P))
        except ValueError as e:
            print('  scan @', P.tolist(), 'no faces within %.1f mm (%s)' % (R, e))
print('volume delta new - old: %.3f mm3' % (mn.volume - mo.volume))
import manifold3d as M3


def man(m):
    return M3.Manifold(M3.Mesh(np.asarray(m.vertices, np.float32), np.asarray(m.faces, np.uint32)))


A, Bm = man(mo), man(mn)
for tag, d in (('old - new', A - Bm), ('new - old', Bm - A)):
    mesh = d.to_mesh(); v = np.asarray(mesh.vert_properties)[:, :3]
    print(tag, 'volume %.3f mm3' % d.volume(), 'bbox', (np.round(v.min(0), 3).tolist(), np.round(v.max(0), 3).tolist())
          if len(v) else 'empty')
