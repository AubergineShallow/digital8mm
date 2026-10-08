"""ESTIMATE: grillage (Hambly) model of the 2.8 ASA side panel, out-of-plane w = +Y (outward). Not FEA-validated."""
import numpy as np
E, NU, T = 1800.0, 0.35, 2.8
G = E / (2 * (1 + NU))
X0, X1, Z0, Z1, NX, NZ = -152.1, -4.6, 8.2, 97.0, 37, 22
xs = np.linspace(X0, X1, NX + 1); zs = np.linspace(Z0, Z1, NZ + 1)
hx, hz = xs[1] - xs[0], zs[1] - zs[0]
nid = lambda i, j: i * (NZ + 1) + j
N = (NX + 1) * (NZ + 1)
P = np.array([(x, z) for x in xs for z in zs])

def kmem(p1, p2, EI, GJ):
    d = p2 - p1; L = np.hypot(*d); c, s = d / L
    kb = EI / L ** 3 * np.array([[12, 6 * L, -12, 6 * L], [6 * L, 4 * L * L, -6 * L, 2 * L * L],
                                 [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L * L, -6 * L, 4 * L * L]])
    kt = GJ / L * np.array([[1, -1], [-1, 1]])
    k = np.zeros((6, 6))                       # local per node: (w, phi_t, phi_b)
    ib = [0, 2, 3, 5]; it = [1, 4]
    k[np.ix_(ib, ib)] += kb; k[np.ix_(it, it)] += kt
    R = np.array([[1, 0, 0], [0, -s, c], [0, c, s]])   # local <- global (w, gx, gz)
    Tm = np.zeros((6, 6)); Tm[:3, :3] = R; Tm[3:, 3:] = R
    return Tm.T @ k @ Tm

def rib_props(w, d, beff=20.0):
    """extra EI, GJ of a rib w (in-plane width) x d (depth into -Y) on the plate (composite with beff of plate)."""
    A1, y1 = beff * T, T / 2; A2, y2 = w * d, T + d / 2
    yc = (A1 * y1 + A2 * y2) / (A1 + A2)
    Ic = beff * T ** 3 / 12 + A1 * (y1 - yc) ** 2 + w * d ** 3 / 12 + A2 * (y2 - yc) ** 2
    a, b = max(w, d), min(w, d)
    J = a * b ** 3 * (1 / 3 - 0.21 * b / a * (1 - b ** 4 / (12 * a ** 4)))
    return E * (Ic - beff * T ** 3 / 12), G * J

def build(ribs=()):
    K = np.zeros((3 * N, 3 * N))
    def add(a, b, EI, GJ):
        k = kmem(P[a], P[b], EI, GJ); dofs = [3 * a, 3 * a + 1, 3 * a + 2, 3 * b, 3 * b + 1, 3 * b + 2]
        K[np.ix_(dofs, dofs)] += k
    for i in range(NX + 1):
        for j in range(NZ + 1):
            if i < NX:   # x member, strip width hz (half at edges)
                b = hz * (0.5 if j in (0, NZ) else 1.0)
                add(nid(i, j), nid(i + 1, j), E * b * T ** 3 / 12, G * b * T ** 3 / 6)
            if j < NZ:
                b = hx * (0.5 if i in (0, NX) else 1.0)
                add(nid(i, j), nid(i, j + 1), E * b * T ** 3 / 12, G * b * T ** 3 / 6)
    for (pa, pb, w, d) in ribs:   # rib along the straight line pa -> pb: chain of members between nearest nodes
        n = int(np.ceil(np.hypot(pb[0] - pa[0], pb[1] - pa[1]) / min(hx, hz))) + 1
        pts = [near((pa[0] + (pb[0] - pa[0]) * t, pa[1] + (pb[1] - pa[1]) * t)) for t in np.linspace(0, 1, n)]
        pts = [p for k_, p in enumerate(pts) if k_ == 0 or p != pts[k_ - 1]]
        EI, GJ = rib_props(w, d)
        for a, b in zip(pts[:-1], pts[1:]):
            add(a, b, EI, GJ)
    return K

def near(p):
    return int(np.argmin((P[:, 0] - p[0]) ** 2 + (P[:, 1] - p[1]) ** 2))

def nodes_in(x0, x1, z0, z1):
    return [k for k in range(N) if x0 - 1e-6 <= P[k, 0] <= x1 + 1e-6 and z0 - 1e-6 <= P[k, 1] <= z1 + 1e-6]

BEAR = [k for k in range(N) if P[k, 0] <= X0 + 1e-6 or P[k, 0] >= X1 - 1e-6]

def solve(K, pins, load_pt, F=1.0):
    f = np.zeros(3 * N); f[3 * near(load_pt)] = F
    pins = set(pins); act = set(BEAR) - pins
    for it in range(60):
        fix = sorted(pins | act); fd = [3 * k for k in fix]
        free = np.setdiff1d(np.arange(3 * N), fd)
        u = np.zeros(3 * N)
        u[free] = np.linalg.solve(K[np.ix_(free, free)], f[free])
        R = K @ u - f
        rel = {k for k in act if R[3 * k] < -1e-9}
        pen = {k for k in set(BEAR) - pins - act if u[3 * k] < -1e-9}
        if not rel and not pen:
            break
        act = (act - rel) | pen
    return u[0::3]


def flex(K, pins, nodes):
    """w-flexibility among `nodes` (pins bilateral w=0), one multi-RHS solve."""
    fd = [3 * k for k in set(pins)]
    free = np.setdiff1d(np.arange(3 * N), fd)
    pos = {d: i for i, d in enumerate(free)}
    B = np.zeros((len(free), len(nodes)))
    for c, k in enumerate(nodes):
        B[pos[3 * k], c] = 1.0
    U = np.linalg.solve(K[np.ix_(free, free)], B)
    rows = [pos[3 * k] for k in nodes]
    return U[rows, :]


def contact_w(C, nb, iload, F=1.0):
    """C over [bearing nodes (nb) + load nodes]; unilateral bearing (w >= 0, r >= 0). Returns w at the load node."""
    b = np.arange(nb); act = set(range(nb))
    for _ in range(200):
        a = sorted(act)
        r = np.zeros(nb)
        if a:
            r[a] = np.linalg.solve(C[np.ix_(a, a)], -C[a, nb + iload] * F)
        w = C[:nb, :nb] @ r + C[:nb, nb + iload] * F
        neg = [i for i in a if r[i] < -1e-12]
        pen = [i for i in b if i not in act and w[i] < -1e-9]
        if not neg and not pen:
            break
        if neg:
            act.discard(min(neg, key=lambda i: r[i]))
        else:
            act.add(min(pen, key=lambda i: w[i]))
    return float(C[nb + iload, :nb] @ r + C[nb + iload, nb + iload] * F)
