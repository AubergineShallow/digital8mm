import sys, os, numpy as np, trimesh, pickle
sys.path.insert(0, r'cad/gs8-d2-v1/candidate-fr1')
os.environ['D2_FR'] = sys.argv[1] if len(sys.argv) > 1 else 'panel'
import layout as L
import cadquery as cq
S = os.path.dirname(os.path.abspath(__file__))
meshes = {}
for p in ('tub', 'hood', 'pi_keeper', 'stick_sleeve', 'base_grip'):
    sh = cq.importers.importStep(r'cad/gs8-d2-v1/out/step/parts/%s.step' % p).val()
    v, f = sh.tessellate(0.05, 0.3)
    meshes[p] = trimesh.Trimesh(np.array([[a.x, a.y, a.z] for a in v]), np.array(f))
xs = np.arange(-151.0, -5.0, 1.0); zs = np.arange(2.75, 96.5, 0.5)
X, Z = np.meshgrid(xs, zs, indexing='ij')
O = np.stack([X.ravel(), np.full(X.size, 32.19), Z.ravel()], 1)
D = np.tile([0, -1.0, 0], (len(O), 1))
ymax = np.full(len(O), -40.0); src = np.array(['-'] * len(O), dtype=object)
dx, dz = 1.0, 0.5
YM = np.full(X.shape, -40.0); SR = np.array(['-'] * X.size, dtype=object).reshape(X.shape)
for p, m in meshes.items():
    T = m.vertices[m.faces]
    for t in T:
        a, b, c = t
        x0, x1 = t[:, 0].min(), t[:, 0].max(); z0, z1 = t[:, 2].min(), t[:, 2].max()
        i0 = int(np.ceil((x0 - xs[0]) / dx)); i1 = int(np.floor((x1 - xs[0]) / dx))
        j0 = int(np.ceil((z0 - zs[0]) / dz)); j1 = int(np.floor((z1 - zs[0]) / dz))
        i0, j0 = max(i0, 0), max(j0, 0); i1, j1 = min(i1, len(xs) - 1), min(j1, len(zs) - 1)
        if i1 < i0 or j1 < j0: continue
        det = (b[0] - a[0]) * (c[2] - a[2]) - (c[0] - a[0]) * (b[2] - a[2])
        if abs(det) < 1e-12: continue
        gx, gz = np.meshgrid(xs[i0:i1 + 1], zs[j0:j1 + 1], indexing='ij')
        u = ((gx - a[0]) * (c[2] - a[2]) - (c[0] - a[0]) * (gz - a[2])) / det
        v = ((b[0] - a[0]) * (gz - a[2]) - (gx - a[0]) * (b[2] - a[2])) / det
        ok = (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)
        y = a[1] + u * (b[1] - a[1]) + v * (c[1] - a[1])
        ok &= y <= 32.19
        sub = YM[i0:i1 + 1, j0:j1 + 1]
        upd = ok & (y > sub)
        sub[upd] = y[upd]
        SR[i0:i1 + 1, j0:j1 + 1][upd] = p
ymax = YM.ravel(); src = SR.ravel()
boxes = [('KO:' + k, b) for k, b in L.KEEPOUTS.items()]
for k, c in L.COTS.items():
    if isinstance(c, dict) and c.get('box'): boxes.append(('C:' + k, c['box']))
boxes.append(('STICK', L.STICK['body']))
for k, b in boxes:
    (x0, x1), (y0, y1), (z0, z1) = b['x'], b['y'], b['z']
    if y0 >= 32.2: continue
    m = (O[:, 0] >= x0) & (O[:, 0] <= x1) & (O[:, 2] >= z0) & (O[:, 2] <= z1) & (min(y1, 32.2) > ymax)
    ymax[m] = min(y1, 32.2); src[m] = k
pickle.dump(dict(xs=xs, zs=zs, ymax=ymax.reshape(X.shape), src=src.reshape(X.shape)), open(os.path.join(S, 'depth.pkl'), 'wb'))
print('done')
