"""Designer 3: quick ACM plate FE of the D2 tub front wall (YZ plane) with a rigid disc at the lens axis.
Units mm, N, MPa. w = X displacement. Pitch moment = about Y (nose-down), yaw = about Z.
Read-only study; no repo files touched."""
import numpy as np, itertools, sys, json

def acm_k(a, b, D):
    """12x12 ACM element stiffness, element a (y) x b (z); dofs per node (w, w_y, w_z)."""
    def P(x, y):
        return np.array([1, x, y, x*x, x*y, y*y, x**3, x*x*y, x*y*y, y**3, x**3*y, x*y**3])
    def Px(x, y):
        return np.array([0, 1, 0, 2*x, y, 0, 3*x*x, 2*x*y, y*y, 0, 3*x*x*y, y**3])
    def Py(x, y):
        return np.array([0, 0, 1, 0, x, 2*y, 0, x*x, 2*x*y, 3*y*y, x**3, 3*x*y*y])
    def Pxx(x, y):
        return np.array([0, 0, 0, 2, 0, 0, 6*x, 2*y, 0, 0, 6*x*y, 0])
    def Pyy(x, y):
        return np.array([0, 0, 0, 0, 0, 2, 0, 0, 2*x, 6*y, 0, 6*x*y])
    def Pxy(x, y):
        return np.array([0, 0, 0, 0, 1, 0, 0, 2*x, 2*y, 0, 3*x*x, 3*y*y])
    nodes = [(0, 0), (a, 0), (a, b), (0, b)]
    C = np.array([row for (x, y) in nodes for row in (P(x, y), Px(x, y), Py(x, y))])
    Ci = np.linalg.inv(C)
    g, wg = np.polynomial.legendre.leggauss(4)
    K = np.zeros((12, 12))
    for (gi, wi), (gj, wj) in itertools.product(zip(g, wg), zip(g, wg)):
        x, y = a*(gi+1)/2, b*(gj+1)/2
        B = np.vstack([Pxx(x, y), Pyy(x, y), 2*Pxy(x, y)]) @ Ci
        K += B.T @ D @ B * wi * wj * a * b / 4
    return K

def run(t=2.5, E=2000.0, nu=0.35, rd=20.0, h=1.9, left='ss', top='ss', holes=True, load='pitch',
        y0=-35.0, y1=32.2, z0=0.0, z1=97.3, extra_rigid=None, thick_zones=None):
    ny, nz = int(round((y1-y0)/h)), int(round((z1-z0)/h))
    ys, zs = np.linspace(y0, y1, ny+1), np.linspace(z0, z1, nz+1)
    a, b = ys[1]-ys[0], zs[1]-zs[0]
    def Dm(tt):
        d = E*tt**3/(12*(1-nu*nu))
        return d*np.array([[1, nu, 0], [nu, 1, 0], [0, 0, (1-nu)/2]])
    kcache = {}
    nn = (ny+1)*(nz+1); N = 3*nn
    K = np.zeros((N, N))
    hole_boxes = [(-26.5, 17.5, 25.9, 29.7), (-31, -21, 32, 38), (3.2, 14.8, 17.2, 23.8), (-11.5, 0.5, 15.9, 18.6)]
    for i in range(ny):
        for j in range(nz):
            yc, zc = (ys[i]+ys[i+1])/2, (zs[j]+zs[j+1])/2
            r = np.hypot(yc, zc-60.0)
            tt = t
            if holes and any(b0 <= yc <= b1 and c0 <= zc <= c1 for b0, b1, c0, c1 in hole_boxes):
                tt = 0.05
            if thick_zones:
                for (b0, b1, c0, c1, tz) in thick_zones:
                    if b0 <= yc <= b1 and c0 <= zc <= c1:
                        tt = max(tt, tz)
            if r <= rd or (extra_rigid and extra_rigid(yc, zc)):
                tt = 40.0
            if tt not in kcache:
                kcache[tt] = acm_k(a, b, Dm(tt))
            ke = kcache[tt]
            ns = [i*(nz+1)+j, (i+1)*(nz+1)+j, (i+1)*(nz+1)+j+1, i*(nz+1)+j+1]
            dofs = np.array([[3*n, 3*n+1, 3*n+2] for n in ns]).ravel()
            K[np.ix_(dofs, dofs)] += ke
    fixed = set()
    for i in range(ny+1):
        for j in range(nz+1):
            n = i*(nz+1)+j
            if i == 0 or j == 0:                     # right wall fold, floor fold: clamped
                fixed |= {3*n, 3*n+1, 3*n+2}
            if i == ny and left == 'ss':
                fixed |= {3*n}
            if j == nz and top == 'ss':
                fixed |= {3*n}
    free = np.array(sorted(set(range(N)) - fixed))
    F = np.zeros(N)
    disc = [(i, j) for i in range(ny+1) for j in range(nz+1) if np.hypot(ys[i], zs[j]-60.0) <= rd-0.5]
    arm = np.array([(zs[j]-60.0) if load == 'pitch' else ys[i] for i, j in disc])
    f = arm/np.sum(arm*arm)*1000.0                    # 1000 N mm total moment
    for (i, j), fi in zip(disc, f):
        F[3*((i)*(nz+1)+j)] += fi
    u = np.zeros(N)
    u[free] = np.linalg.solve(K[np.ix_(free, free)], F[free])
    w = np.array([u[3*(i*(nz+1)+j)] for i, j in disc])
    rot = np.sum(w*arm)/np.sum(arm*arm)               # rad per 1000 N mm
    return rot

if __name__ == '__main__':
    out = {}
    for name, kw in [
        ('tub 2.5 rd20 pitch ss/ss', dict(rd=20)),
        ('tub 2.5 rd20 pitch free-left free-top', dict(rd=20, left='free', top='free')),
        ('tub 2.5 rd20 yaw ss/ss', dict(rd=20, load='yaw')),
        ('tub 2.5 rd28 pitch ss/ss', dict(rd=28)),
        ('tub 2.5 rd28 yaw ss/ss', dict(rd=28, load='yaw')),
        ('tub+hood 5.0 rd28 pitch ss/ss', dict(rd=28, t=5.0)),
        ('tub+hood 3.15 rd28 pitch ss/ss', dict(rd=28, t=3.15)),
        ('tub+hood 3.15 rd28 pitch free/free', dict(rd=28, t=3.15, left='free', top='free')),
    ]:
        r = run(**kw)
        out[name] = r
        print('%-40s %.3e rad per N m = %.3f deg per N m' % (name, r, np.degrees(r)), flush=True)
    json.dump(out, open(sys.argv[1] if len(sys.argv) > 1 else 'd3_plate.json', 'w'), indent=1)
