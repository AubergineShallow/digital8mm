"""Steady temperature / passive-tracer solver on the LBM velocity field (af-solver role).

Finite volumes on the voxel grid (cell = dx^3), first-order upwind advection, central diffusion with
D = alpha + nu_t / Pr_t on faces between open cells, adiabatic walls (closed faces at solids and the box boundary),
Dirichlet values at ambient reservoir cells, volumetric heat sources from mask__heat__<component> cells.

Face volume fluxes are built from the (window-mean) LBM velocity and then PROJECTED to be discretely divergence-free
(CG Poisson solve, phi = 0 at ambient cells), so the conservative upwind scheme conserves energy exactly and a uniform
temperature is an exact solution.  Fluid cells not connected to the ambient reservoir are excluded (reported).

Steady state by local pseudo-time stepping (explicit, per-cell dt = CFL * V / a_P, i.e. damped Jacobi), CFL <= 1
(default 0.4).  Optional exterior loss through the shell: U (W/m2K) on faces between open cells and shell solids.
See NOTES.md "## af-solver API".
"""
from __future__ import annotations

import json
import time

import numpy as np

def _lo(a):
    return tuple(slice(None, -1) if i == a else slice(None) for i in range(3))


def _hi(a):
    return tuple(slice(1, None) if i == a else slice(None) for i in range(3))


def dilate(m, through=None):
    """6-neighbour dilation of bool array m (optionally restricted to `through`)."""
    o = m.copy()
    for a in range(3):
        o[_lo(a)] |= m[_hi(a)]
        o[_hi(a)] |= m[_lo(a)]
    return o if through is None else (o & through) | m


def flood(seed, through, max_iter=100000):
    """Cells of `through` connected (6-neighbour) to `seed`."""
    r = seed & through
    for _ in range(max_iter):
        n = dilate(r, through)
        if n.sum() == r.sum():
            return n
        r = n
    return r


class Problem:
    """Prepared transport problem: open cells, projected face fluxes F[a] (m3/s, + along axis a), conductances
    G[a] (m3/s, = D dx for open faces), ambient (Dirichlet) cells."""

    def __init__(self, dom, u, *, rho=None, nu_t=None, alpha=2.3e-5, Pr_t=0.85, project=True, cg_tol=1e-10,
                 cg_maxiter=5000, log=None):
        t0 = time.time()
        self.dx = dom["dx_mm"] / 1000.0
        self.V = self.dx ** 3
        self.shape = dom["solid"].shape
        fluid = ~dom["solid"]
        amb = dom["masks"].get("ambient", np.zeros(self.shape, bool)) & fluid
        conn = flood(amb, fluid)
        self.amb = amb
        self.active = conn & ~amb                    # unknown cells
        self.open = conn                             # active + ambient
        self.disconnected = fluid & ~conn
        self.notes = []
        if self.disconnected.any():
            self.notes.append(f"{int(self.disconnected.sum())} fluid cells not connected to ambient: excluded")
        u = np.asarray(u, np.float64)
        if rho is not None:
            u = u * np.asarray(rho, np.float64)[None]   # mass flux / rho_ref
        A = self.dx ** 2
        self.F, self.G, self.fopen = [], [], []
        nut = np.zeros(self.shape) if nu_t is None else np.asarray(nu_t, np.float64)
        for a in range(3):
            lo, hi = _lo(a), _hi(a)
            fo = (self.open[lo] & self.open[hi]) & (self.active[lo] | self.active[hi])
            self.fopen.append(fo)
            self.F.append(np.where(fo, 0.5 * (u[a][lo] + u[a][hi]) * A, 0.0))
            D = alpha + 0.5 * (nut[lo] + nut[hi]) / Pr_t
            self.G.append(np.where(fo, D * self.dx, 0.0))
        self.div0 = self.divergence()
        self.proj = None
        if project:
            self.proj = self._project(cg_tol, cg_maxiter)
        self.setup_s = time.time() - t0
        if log:
            print(json.dumps(self.summary()), file=log)

    # ---- flux helpers
    def divergence(self):
        d = np.zeros(self.shape)
        for a in range(3):
            d[_lo(a)] += self.F[a]
            d[_hi(a)] -= self.F[a]
        return np.where(self.active, d, 0.0)

    def _lap(self, phi):
        """-L(phi) on active cells (phi zero elsewhere): sum over open faces (phi_c - phi_nb)."""
        o = np.zeros(self.shape)
        for a in range(3):
            lo, hi = _lo(a), _hi(a)
            d = np.where(self.fopen[a], phi[hi] - phi[lo], 0.0)
            o[lo] -= d
            o[hi] += d
        return np.where(self.active, o, 0.0)

    def _project(self, tol, maxiter):
        b = self.divergence()        # want -L(phi) = -div  -> F' = F - grad(phi)  makes div' = div - L(phi) = 0
        rhs = -b
        diag = np.zeros(self.shape)
        for a in range(3):
            diag[_lo(a)] += self.fopen[a]
            diag[_hi(a)] += self.fopen[a]
        diag = np.where(self.active & (diag > 0), diag, 1.0)
        x = np.zeros(self.shape)
        r = rhs.copy()
        z = r / diag
        p = z.copy()
        rz = float((r * z).sum())
        bn = float(np.sqrt((rhs * rhs).sum()))
        it, rn = 0, bn
        qscale = sum(float(np.abs(f).sum()) for f in self.F) or 1.0
        for it in range(1, maxiter + 1):
            if rn <= 1e-14 * qscale:
                break
            Ap = self._lap(p)
            pap = float((p * Ap).sum())
            if pap <= 0:
                break
            alpha = rz / pap
            x += alpha * p
            r -= alpha * Ap
            rn = float(np.sqrt((r * r).sum()))
            if rn < tol * bn:
                break
            z = r / diag
            rz2 = float((r * z).sum())
            p = z + (rz2 / rz) * p
            rz = rz2
        # L(x) = -(-L x) ; we solved -L x = -div  => L x = div
        for a in range(3):
            lo, hi = _lo(a), _hi(a)
            self.F[a] = self.F[a] - np.where(self.fopen[a], x[hi] - x[lo], 0.0)
        div1 = self.divergence()
        qref = sum(float(np.abs(f).sum()) for f in self.F) / 3.0 or 1.0
        return {"cg_iters": it, "cg_rel_res": rn / bn if bn else 0.0, "div_before_rel": float(np.abs(b).sum()) / qref,
                "div_after_rel": float(np.abs(div1).sum()) / qref}

    def boundary_flux(self):
        """Net volume flow (m3/s) from active cells into ambient cells (out > 0) and the inflow part."""
        out = inn = 0.0
        for a in range(3):
            lo, hi = _lo(a), _hi(a)
            f = self.F[a]
            m1 = self.active[lo] & self.amb[hi]       # face from active (lo) to ambient (hi): out = +f
            m2 = self.amb[lo] & self.active[hi]       # from ambient (lo) to active (hi): out = -f
            fo = np.concatenate([f[m1], -f[m2]])
            out += float(fo[fo > 0].sum())
            inn += float(-fo[fo < 0].sum())
        return out, inn

    def summary(self):
        o, i = self.boundary_flux()
        return {"active_cells": int(self.active.sum()), "ambient_cells": int(self.amb.sum()),
                "disconnected_fluid_cells": int(self.disconnected.sum()), "projection": self.proj,
                "Q_out_m3s": o, "Q_in_m3s": i, "setup_s": self.setup_s, "notes": self.notes}

    # ---- exterior loss geometry
    def shell_faces(self, dom, depth=2):
        """Per-cell count of faces between active cells and 'shell' solids: solid cells within `depth` cells of
        the outside (mask__exterior if the domain has one, else the box boundary layer and the ambient cells)."""
        solid = dom["solid"]
        ext = dom["masks"].get("exterior")
        if ext is None:
            ext = np.zeros(self.shape, bool)
            for a in range(3):
                ext[tuple(0 if i == a else slice(None) for i in range(3))] = True
                ext[tuple(-1 if i == a else slice(None) for i in range(3))] = True
            ext = (ext & solid) | self.amb
        sh = ext.copy()
        for _ in range(depth):
            sh = dilate(sh, solid)
        sh &= solid
        n = np.zeros(self.shape)
        for a in range(3):
            lo, hi = _lo(a), _hi(a)
            n[lo] += self.active[lo] & sh[hi]
            n[hi] += self.active[hi] & sh[lo]
        return n

    # ---- scalar solve
    def solve(self, *, source=None, amb_value=0.0, fixed=None, loss=None, cfl=0.4, tol=1e-6, max_iter=200000,
              check_every=200, deadline=None, x0=None, method="pseudo"):
        """Steady conservative upwind advection-diffusion:  sum_faces(F phi_up + G (phi_c - phi_nb)) = S + loss.
        source: per-cell S [phi * m3/s] (heat: W / (rho cp)); amb_value: scalar or array (Dirichlet on ambient);
        fixed: (mask, value) extra Dirichlet cells; loss: (coef [m3/s per cell], phi_ref) linear sink coef*(phi_ref -
        phi).  method 'pseudo' (local pseudo-time, damped Jacobi, CFL = cfl) or 'bicgstab' (Jacobi-preconditioned
        BiCGSTAB on the same discrete equations; same answer, far fewer sweeps).  Residual = sum|R| / sum|S| (or a
        diagonal-based scale when S = 0).  Returns (phi, info) with residual history; phi is NaN outside open cells."""
        t0 = time.time()
        phi = np.zeros(self.shape) if x0 is None else np.array(x0, np.float64)
        amb_v = np.broadcast_to(np.asarray(amb_value, np.float64), self.shape)
        phi[self.amb] = amb_v[self.amb]
        unk = self.active.copy()
        if fixed is not None:
            fm, fv = fixed
            fm = fm & self.active
            phi[fm] = np.broadcast_to(np.asarray(fv, np.float64), self.shape)[fm]
            unk &= ~fm
        S = np.zeros(self.shape) if source is None else np.asarray(source, np.float64)
        diag = np.zeros(self.shape)
        for a in range(3):
            f, g = self.F[a], self.G[a]
            diag[_lo(a)] += np.maximum(f, 0.0) + g
            diag[_hi(a)] += np.maximum(-f, 0.0) + g
        lc, lref = (None, 0.0) if loss is None else (np.asarray(loss[0], np.float64), loss[1])
        if lc is not None:
            diag += lc
        diag = np.where(unk & (diag > 0), diag, 1.0)
        sref = float(np.abs(S[unk]).sum()) or float(diag[unk].sum()) * 1e-3 or 1.0
        hist = []
        if method == "bicgstab":
            return self._bicgstab(phi, S, unk, diag, lc, lref, sref, tol, max_iter, deadline, t0)
        it = 0
        for it in range(1, max_iter + 1):
            R = self._residual(phi, S, lc, lref)
            phi[unk] += cfl * R[unk] / diag[unk]
            if it % check_every == 0 or it == max_iter:
                rr = float(np.abs(R[unk]).sum()) / sref
                hist.append((it, rr))
                if not np.isfinite(rr):
                    break
                if rr < tol:
                    break
                if deadline and time.time() > deadline:
                    break
        out = np.where(self.open, phi, np.nan)
        info = {"iters": it, "res": hist[-1][1] if hist else None, "history": hist, "converged":
                bool(hist and hist[-1][1] < tol), "wall_s": time.time() - t0}
        return out, info

    def _bicgstab(self, phi, S, unk, diag, lc, lref, sref, tol, maxit, deadline, t0):
        def A(x):
            return np.where(unk, -self._residual(x, 0.0, lc, 0.0), 0.0)

        r = np.where(unk, self._residual(phi, S, lc, lref), 0.0)
        rhat = r.copy()
        rho = alpha = om = 1.0
        v = np.zeros(self.shape)
        p = np.zeros(self.shape)
        hist = []
        it = 0
        for it in range(1, maxit + 1):
            rho1 = float((rhat * r).sum())
            if rho1 == 0.0:
                break
            p = r + (rho1 / rho) * (alpha / om) * (p - om * v) if it > 1 else r.copy()
            y = np.where(unk, p / diag, 0.0)
            v = A(y)
            alpha = rho1 / float((rhat * v).sum())
            s_ = r - alpha * v
            phi += alpha * y
            rs = float(np.abs(s_).sum()) / sref
            if rs < tol:
                hist.append((it, rs))
                break
            z = np.where(unk, s_ / diag, 0.0)
            t = A(z)
            tt = float((t * t).sum())
            om = float((t * s_).sum()) / tt if tt > 0 else 0.0
            phi += om * z
            r = s_ - om * t
            rho = rho1
            rr = float(np.abs(r).sum()) / sref
            if it % 10 == 0:
                hist.append((it, rr))
            if not np.isfinite(rr) or rr < tol or om == 0.0:
                hist.append((it, rr))
                break
            if deadline and time.time() > deadline:
                break
        # true residual check
        R = self._residual(phi, S, lc, lref)
        rt = float(np.abs(R[unk]).sum()) / sref
        out = np.where(self.open, phi, np.nan)
        return out, {"iters": it, "res": rt, "history": hist, "converged": rt < 10 * tol, "method": "bicgstab",
                     "wall_s": time.time() - t0}

    def _residual(self, phi, S, lc=None, lref=0.0):
        """R = S + loss - net outflow (advective upwind + diffusive) for every cell."""
        N = np.zeros(self.shape)
        for a in range(3):
            lo, hi = _lo(a), _hi(a)
            f = self.F[a]
            q = np.where(f > 0, f * phi[lo], f * phi[hi]) + self.G[a] * (phi[lo] - phi[hi])
            N[lo] += q
            N[hi] -= q
        R = S - N
        if lc is not None:
            R += lc * (lref - phi)
        return R

    def ambient_exchange(self, phi):
        """Net transport (phi * m3/s) from active cells into ambient cells (advective + diffusive)."""
        tot = 0.0
        for a in range(3):
            lo, hi = _lo(a), _hi(a)
            f = self.F[a]
            q = np.where(f > 0, f * phi[lo], f * phi[hi]) + self.G[a] * (phi[lo] - phi[hi])
            q = np.nan_to_num(q)
            tot += float(q[self.active[lo] & self.amb[hi]].sum()) - float(q[self.amb[lo] & self.active[hi]].sum())
        return tot


# ----------------------------------------------------------------------------------------------- applications
def heat_source(prob, dom, heat_W, rho=1.13, cp=1007.0):
    """Per-cell source (K m3/s) from {component: W} spread uniformly over the ACTIVE cells of
    mask__heat__<component>.  Returns (S, report) - report lists the W applied and anything not applied."""
    S = np.zeros(prob.shape)
    rep = {"applied_W": {}, "not_applied": {}}
    for comp, w in heat_W.items():
        if not isinstance(w, (int, float)) or w == 0 or comp == "total" or "worst" in comp:
            continue
        m = dom["masks"].get("heat__" + comp)
        if m is None and comp.endswith("_rest"):                 # params 'pi_board_rest' -> mask__heat__pi_board
            m = dom["masks"].get("heat__" + comp[:-5])
        if m is None and comp == "fan":                          # fan motor heat -> the blower interior air
            m = dom["masks"].get("heat__fan_actuator", dom["masks"].get("fan_actuator"))
        if m is None:
            rep["not_applied"][comp] = f"{w} W: no mask__heat__{comp}"
            continue
        m = m & prob.active
        n = int(m.sum())
        if n == 0:
            rep["not_applied"][comp] = f"{w} W: mask has no active air cells"
            continue
        S[m] += float(w) / n / (rho * cp)
        rep["applied_W"][comp] = float(w)
    rep["total_applied_W"] = sum(rep["applied_W"].values())
    return S, rep


def solve_temperature(prob, dom, heat_W, *, T_amb=30.0, rho=1.13, cp=1007.0, h_ext=None, shell_depth=2,
                      cfl=0.4, tol=1e-6, max_iter=200000, deadline=None, method="bicgstab"):
    """Steady air temperature (deg C).  h_ext: overall U (W/m2K) through the shell for the exterior-loss case
    (None = adiabatic walls, the conservative case).  info has the energy balance:
    heat_in_W, enthalpy_out_W (to the ambient cells), shell_loss_W, balance_rel."""
    S, rep = heat_source(prob, dom, heat_W, rho, cp)
    loss = None
    if h_ext:
        nf = prob.shell_faces(dom, shell_depth)
        loss = (nf * h_ext * prob.dx ** 2 / (rho * cp), 0.0)
    # solve for theta = T - T_amb (ambient 0) -> uniform-T exactness, better float accuracy
    th, info = prob.solve(source=S, amb_value=0.0, loss=loss, cfl=cfl, tol=tol, max_iter=max_iter,
                          deadline=deadline, method=method)
    q_in = float(S[prob.active].sum()) * rho * cp
    out = prob.ambient_exchange(np.nan_to_num(th)) * rho * cp
    shell = float((loss[0] * np.nan_to_num(th)).sum()) * rho * cp if loss else 0.0
    info.update({"heat_in_W": q_in, "enthalpy_out_W": out, "shell_loss_W": shell,
                 "balance_rel": (out + shell - q_in) / q_in if q_in else None, "heat_report": rep,
                 "T_amb_C": T_amb, "h_ext": h_ext})
    return th + T_amb, info


def label_ambient_by_vent(prob, dom):
    """Assign each ambient cell to the nearest vent zone (multi-source dilation through ambient cells).
    Returns (labels int array: -1 none, k = index into names), names."""
    names = sorted(k[6:] for k in dom["masks"] if k.startswith("vent__"))
    lab = np.full(prob.shape, -1, np.int32)
    seeds = [dom["masks"]["vent__" + n] for n in names]
    front = [dilate(s) & prob.amb for s in seeds]
    for k, f in enumerate(front):
        lab[f & (lab < 0)] = k
    for _ in range(10000):
        un = prob.amb & (lab < 0)
        if not un.any():
            break
        grew = False
        for k in range(len(names)):
            g = dilate(lab == k) & un & (lab < 0)
            if g.any():
                lab[g] = k
                grew = True
        if not grew:
            break
    return lab, names


def vent_tracers(prob, dom, **kw):
    """Per-vent inflow tracers: c_v = 1 on the ambient cells nearest vent v, 0 on the others.  c_v at a point =
    fraction of the air there that entered through vent v.  Returns {vent: field}, labels, names, infos."""
    kw.setdefault("method", "bicgstab")
    lab, names = label_ambient_by_vent(prob, dom)
    out, infos = {}, {}
    for k, n in enumerate(names):
        c, info = prob.solve(amb_value=(lab == k).astype(np.float64), **kw)
        out[n] = c
        infos[n] = info
    return out, lab, names, infos


def mean_age(prob, **kw):
    """Mean age of air (s): u.grad(tau) - div(D grad tau) = 1, tau = 0 at ambient."""
    kw.setdefault("method", "bicgstab")
    S = np.where(prob.active, prob.V, 0.0)
    return prob.solve(source=S, amb_value=0.0, **kw)


def recirculation_tracer(prob, dom, tag="fan_outlet", **kw):
    """Exhaust tag: c = 1 fixed on mask__<tag> (fin exit plane), 0 at ambient, no source.  c at the fan intake =
    fraction of intake air that last came from the fan exhaust (internal recirculation) rather than fresh."""
    kw.setdefault("method", "bicgstab")
    m = dom["masks"][tag]
    return prob.solve(amb_value=0.0, fixed=(m, 1.0), **kw)


def probe_stats(prob, field, mask, weight="volume", normal=None):
    """Mean / max / min of `field` over the open cells of mask; weight 'flux' = |flux|-weighted mean through the
    slab (face-flux magnitude summed over the cell's faces along the dominant axis of `normal` or of the flow)."""
    m = mask & prob.open
    if not m.any():
        return {"cells": 0}
    v = field[m]
    d = {"cells": int(m.sum()), "mean": float(np.nanmean(v)), "max": float(np.nanmax(v)), "min": float(np.nanmin(v))}
    if weight == "flux":
        w = np.zeros(prob.shape)
        axes = range(3) if normal is None else [int(np.argmax(np.abs(normal)))]
        for a in axes:
            fa = np.abs(prob.F[a])
            w[_lo(a)] += 0.5 * fa
            w[_hi(a)] += 0.5 * fa
        ww = w[m]
        if ww.sum() > 0:
            d["flux_mean"] = float((ww * np.nan_to_num(v)).sum() / ww.sum())
    return d
