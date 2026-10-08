"""D3Q19 lattice Boltzmann solver for the D2 airflow study (af-solver role).

numpy float32 only (no scipy / numba).  Pull streaming with slice copies, halfway bounce-back on the solid mask,
BGK + Smagorinsky (Hou et al. 1996: tau from the non-equilibrium stress), Guo forcing.  Body forces:
  * fan actuator: uniform force density along a unit vector in mask__fan_actuator; its magnitude is rescaled every
    `ctrl_every` steps so the delivered (Q, dp_fan) sits on the fan curve (dp_fan = int(F.u dV) / Q).
  * Forchheimer porous zones (vents, isotropic): dp = K * 0.5 rho u^2 across the zone thickness, u = superficial
    velocity of the zone cells.  Implicit (exact) treatment of the quadratic drag, stable for any K.
  * fin block (anisotropic): Forchheimer along the fin axis (K per mm), strong implicit linear drag across it.
Ambient reservoir cells are reset to equilibrium at rho = 1 with their own (streamed) velocity each step
(pressure outlet / inlet with zero-gradient velocity).  Cells outside the box count as solid.
Physical units: dx [m], dt chosen so the max lattice speed u_ref*dt/dx <= u_lat_max (default 0.1).
See NOTES.md "## af-solver API".
"""
from __future__ import annotations

import json
import math
import os
import sys
import time

import numpy as np

F32 = np.float32

# D3Q19 velocities: rest, 6 faces, 12 edges
C = np.array([[0, 0, 0],
              [1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1],
              [1, 1, 0], [-1, -1, 0], [1, -1, 0], [-1, 1, 0],
              [1, 0, 1], [-1, 0, -1], [1, 0, -1], [-1, 0, 1],
              [0, 1, 1], [0, -1, -1], [0, 1, -1], [0, -1, 1]], dtype=np.int64)
W = np.array([1 / 3] + [1 / 18] * 6 + [1 / 36] * 12, dtype=np.float64)
OPP = np.array([int(np.where((C == -C[i]).all(1))[0][0]) for i in range(19)])
Cf = C.astype(F32)
# second-moment operator for the stress: xx, yy, zz, xy, xz, yz
CC = np.stack([C[:, 0] * C[:, 0], C[:, 1] * C[:, 1], C[:, 2] * C[:, 2],
               C[:, 0] * C[:, 1], C[:, 0] * C[:, 2], C[:, 1] * C[:, 2]]).astype(F32)
Wf = W.astype(F32)[:, None]
_CT = np.ascontiguousarray(Cf.T)


def set_low_priority():
    """BELOW_NORMAL priority on Windows (nice +10 elsewhere) so the r3 CAD builds win."""
    try:
        if sys.platform == "win32":
            import ctypes
            k = ctypes.windll.kernel32
            k.SetPriorityClass(k.GetCurrentProcess(), 0x4000)
        else:
            os.nice(10)
    except Exception:  # pragma: no cover
        pass


def free_ram_mb():
    """Available physical memory in MB (Windows GlobalMemoryStatusEx); None if unknown."""
    try:
        import ctypes

        class MS(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        m = MS()
        m.dwLength = ctypes.sizeof(MS)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        return m.ullAvailPhys / 2 ** 20
    except Exception:
        return None


# ----------------------------------------------------------------------------------------------- domain I/O
def load_domain(path):
    """Load out/domain-<dx>.npz -> dict(dx_mm, origin, solid, masks{name: bool}, meta{})."""
    z = np.load(path, allow_pickle=False)
    d = {"path": str(path), "dx_mm": float(z["dx"]), "origin": np.asarray(z["origin"], float),
         "solid": z["solid"].astype(bool), "masks": {}, "meta": {}}
    for k in z.files:
        if k.startswith("mask__"):
            d["masks"][k[6:]] = z[k].astype(bool)
    if "meta_json" in z.files:
        d["meta"] = json.loads(str(z["meta_json"]))
    return d


def mask_info(meta, name):
    """Per-mask metadata dict from meta (accepts meta['masks'][name] or meta[name]); {} if absent."""
    for key in ("masks", "mask_notes", "mask_meta"):
        m = meta.get(key)
        if isinstance(m, dict) and isinstance(m.get(name), dict):
            return m[name]
    v = meta.get(name)
    if isinstance(v, dict):
        return v
    if name.startswith("vent__") and isinstance(meta.get("vents"), dict):      # af-domain: meta.vents[<id>]
        v = meta["vents"].get(name[6:])
        if isinstance(v, dict):
            return v
    return {}


def mask_normal(meta, name):
    """Unit normal stored for a mask (keys 'normal', 'outward_normal', 'n'); None if absent."""
    info = mask_info(meta, name)
    for key in ("normal", "outward_normal", "n", "dir", "direction"):
        if key in info:
            n = np.asarray(info[key], float)
            return n / np.linalg.norm(n)
    for key in ("vent_normals", "normals"):
        m = meta.get(key)
        if isinstance(m, dict):
            nm = name[6:] if name.startswith("vent__") else name
            for cand in (name, nm):
                if cand in m:
                    n = np.asarray(m[cand], float)
                    return n / np.linalg.norm(n)
    return None


def slab_thickness(mask, normal):
    """Thickness (cells) of a slab-like mask along the dominant axis of `normal` = cells / projected cells."""
    ax = int(np.argmax(np.abs(normal)))
    n = int(mask.sum())
    if n == 0:
        return 1.0
    proj = int(mask.any(axis=ax).sum())
    return max(1.0, n / max(proj, 1))


def flux_through(u, mask, normal, thickness=None, rho=None):
    """Flow (u units * cell^2) through a slab mask: sum(u.n) / thickness, positive along `normal`.  With `rho`
    (lattice density, same shape as mask) it is the mass flux / rho_ref, i.e. volume flow at the reference density
    (the quantity a steady low-Mach LBM conserves exactly)."""
    if not mask.any():
        return 0.0
    n = np.asarray(normal, float)
    t = slab_thickness(mask, n) if thickness is None else thickness
    r = rho[mask] if rho is not None else None
    s = sum(float(n[a]) * float((u[a][mask] * r if r is not None else u[a][mask]).sum(dtype=np.float64))
            for a in range(3) if n[a] != 0.0)
    return s / t


# ----------------------------------------------------------------------------------------------- streaming plan
def _axis_pieces(c, n, periodic):
    """(dst, src) slice pairs along one axis for the pull shift dst[x] = src[x - c]."""
    if c == 0:
        return [(slice(None), slice(None))]
    if c > 0:
        p = [(slice(1, None), slice(0, n - 1))]
        if periodic:
            p.append((slice(0, 1), slice(n - 1, n)))
    else:
        p = [(slice(0, n - 1), slice(1, None))]
        if periodic:
            p.append((slice(n - 1, n), slice(0, 1)))
    return p


def _shift_plan(shape, periodic):
    plan = []
    for i in range(19):
        pieces = [((), ())]
        for a in range(3):
            new = []
            for (d0, s0) in pieces:
                for (d, s) in _axis_pieces(int(C[i, a]), shape[a], periodic[a]):
                    new.append((d0 + (d,), s0 + (s,)))
            pieces = new
        plan.append(pieces)
    return plan


def _bounce_back_index(solid, periodic):
    """Per direction i: flat indices of fluid cells whose pull source x - c_i is solid or outside the box."""
    pad = solid
    for a in range(3):
        w = [(0, 0)] * 3
        w[a] = (1, 1)
        pad = np.pad(pad, w, mode="wrap") if periodic[a] else np.pad(pad, w, constant_values=True)
    nx, ny, nz = solid.shape
    fluid = ~solid
    out = []
    for i in range(19):
        cx, cy, cz = C[i]
        src = pad[1 - cx:1 - cx + nx, 1 - cy:1 - cy + ny, 1 - cz:1 - cz + nz]
        out.append(np.flatnonzero((fluid & src).ravel()).astype(np.int64))
    return out


def feq_block(rho, u):
    """Equilibrium (19, n) for rho (n,), u (3, n)."""
    cu = Cf @ u
    usq = (u * u).sum(0)
    return Wf * rho * (1.0 + 3.0 * cu + 4.5 * cu * cu - 1.5 * usq)


def fan_curve_dp_vec(q, curve, speed=1.0):
    """Vectorised fan_curve_dp (q array, m3/s); reverse flow (q < 0) gets the shut-off pressure."""
    cq = np.asarray([p[0] for p in curve], float) * speed
    cp = np.asarray([p[1] for p in curve], float) * speed ** 2
    y = np.interp(q, cq, cp)
    slope = (cp[-1] - cp[-2]) / (cq[-1] - cq[-2])
    return y + np.where(q > cq[-1], slope * (q - cq[-1]), 0.0)


def fan_curve_dp(q, curve, speed=1.0):
    """Fan-law scaled curve: dp_s(Q) = s^2 dp_100(Q/s); linear interpolation, linear extrapolation past the end."""
    cq = np.asarray([p[0] for p in curve], float)
    cp = np.asarray([p[1] for p in curve], float)
    x = q / max(speed, 1e-9)
    if x <= cq[-1]:
        y = float(np.interp(x, cq, cp))
    else:
        slope = (cp[-1] - cp[-2]) / (cq[-1] - cq[-2])
        y = cp[-1] + slope * (x - cq[-1])
    return speed ** 2 * y


# ----------------------------------------------------------------------------------------------- solver
class LBM:
    """D3Q19 BGK-Smagorinsky solver on a voxel domain (lattice units inside, physical units at the API)."""

    def __init__(self, solid, *, dx_m, nu_phys=1.6e-5, rho_phys=1.13, u_ref=5.0, u_lat_max=0.1, dp_max=None,
                 drho_max=0.03,
                 tau_min=0.5, cs_smag=0.16, periodic=(False, False, False), chunk=2048, threads=1):
        self.shape = tuple(int(s) for s in solid.shape)
        self.N = int(np.prod(self.shape))
        self.solid = solid.astype(bool)
        self.fluid_flat = (~self.solid).ravel()
        self.fluid_f32 = self.fluid_flat.astype(F32)
        self.dx = float(dx_m)
        self.rho_phys = float(rho_phys)
        self.dt = u_lat_max * self.dx / float(u_ref)
        if dp_max:   # artificial compressibility: 3 dp / p_scale <= drho_max
            self.dt = min(self.dt, self.dx * math.sqrt(self.rho_phys * drho_max / (3.0 * float(dp_max))))
        self.dp_max = dp_max
        self.u_ref = float(u_ref)
        self.nu_phys = float(nu_phys)
        self.nu_lat_true = self.nu_phys * self.dt / self.dx ** 2
        tau_true = 0.5 + 3.0 * self.nu_lat_true
        self.tau0 = max(tau_true, float(tau_min))
        self.nu_lat = (self.tau0 - 0.5) / 3.0
        self.re_factor = self.nu_lat_true / self.nu_lat  # Re_sim = re_factor * Re_real (1.0 = real air)
        self.cs = float(cs_smag)
        self.periodic = tuple(bool(p) for p in periodic)
        self.chunk = int(chunk)
        self.threads = int(threads)
        self.plan = _shift_plan(self.shape, self.periodic)
        self.bb = _bounce_back_index(self.solid, self.periodic)
        f0 = (Wf * np.ones((1, self.N), F32)).astype(F32)
        self.f = f0.reshape((19,) + self.shape).copy()
        self.f2 = self.f.copy()
        self.rho = np.ones(self.N, F32)
        self.u = np.zeros((3, self.N), F32)
        self.nut = np.zeros(self.N, F32)           # lattice eddy viscosity
        self.F = np.zeros((3, self.N), F32)        # total force density used in the last step
        self.fan_idx = None
        self.fan_mag = 0.0
        self.fan_local = False
        self.por = []                              # list of porous zone dicts
        self.amb_idx = None
        self.step_count = 0
        self.history = []
        self.probes = {}                           # name -> (mask, normal, thickness)
        self.fan_ctrl = None

    # ---- unit helpers
    @property
    def u_scale(self):
        return self.dx / self.dt                   # m/s per lattice speed

    @property
    def p_scale(self):
        return self.rho_phys * self.u_scale ** 2   # Pa per lattice pressure

    def q_phys(self, q_lat):
        return q_lat * self.dx ** 3 / self.dt      # m3/s

    def info(self):
        return {"dx_m": self.dx, "dt_s": self.dt, "tau0": self.tau0, "nu_lat": self.nu_lat,
                "nu_lat_true": self.nu_lat_true, "re_factor": self.re_factor, "cs_smag": self.cs,
                "u_scale_mps": self.u_scale, "p_scale_Pa": self.p_scale, "shape": self.shape,
                "fluid_cells": int(self.fluid_flat.sum()), "u_lat_at_u_ref": self.u_ref * self.dt / self.dx,
                "drho_at_dp_max": (3.0 * self.dp_max / self.p_scale) if self.dp_max else None}

    # ---- setup
    def set_ambient(self, mask):
        self.amb_idx = np.flatnonzero(mask.ravel() & self.fluid_flat)

    def lin_lat(self, a_Pa_per_mps):
        """Linear loss a [Pa per m/s] -> lattice coefficient (dp_lat per lattice velocity, rho_lat = 1)."""
        return float(a_Pa_per_mps) / (self.rho_phys * self.u_scale)

    def add_porous_iso(self, mask, K, thickness_cells, name="", lin=0.0):
        """Darcy-Forchheimer zone: dp = lin*u + K 0.5 rho u^2 over `thickness_cells` (lin in lattice units, see
        lin_lat) -> F/rho = -(lin/t) u - (K/2t)|u|u.  Implicit exact solve, stable for any K."""
        idx = np.flatnonzero(mask.ravel() & self.fluid_flat)
        t = float(thickness_cells)
        self.por.append({"name": name, "idx": idx, "kind": "iso", "c": F32(float(K) / (2.0 * t)),
                         "b": F32(float(lin) / t)})

    def add_porous_axis(self, mask, axis, K_per_cell, beta_t=4.0, name="fins", lin_per_cell=0.0):
        """Anisotropic zone: Darcy-Forchheimer along `axis` (dp per cell = lin_per_cell u + K_per_cell 0.5 rho u^2),
        implicit linear drag beta_t (lattice 1/step) across it (blocks the transverse directions)."""
        idx = np.flatnonzero(mask.ravel() & self.fluid_flat)
        a = np.asarray(axis, float)
        a = (a / np.linalg.norm(a)).astype(F32)
        self.por.append({"name": name, "idx": idx, "kind": "axis", "axis": a,
                         "c": F32(0.5 * float(K_per_cell)), "beta": F32(beta_t), "b": F32(lin_per_cell)})

    def add_porous_diag(self, mask, K_per_cell=(0.0, 0.0, 0.0), beta=(0.0, 0.0, 0.0), name="fins"):
        """Anisotropic zone with a diagonal (grid-axis) resistance tensor: F_a/rho = -(K_a/2)|u| u_a - beta_a u_a.
        K_a = loss coefficient per lattice length along axis a (dp_a = K_a 0.5 rho |u| u_a per cell), beta_a =
        linear drag (lattice 1/step).  Implicit fixed-point solve on |u| (exact for a single active axis)."""
        idx = np.flatnonzero(mask.ravel() & self.fluid_flat)
        self.por.append({"name": name, "idx": idx, "kind": "diag",
                         "c": (0.5 * np.asarray(K_per_cell, float)).astype(F32)[:, None],
                         "beta": np.asarray(beta, float).astype(F32)[:, None]})

    def add_probe(self, name, mask, normal=None):
        """Flow-rate probe through a slab mask (normal None = dominant axis of the mean velocity)."""
        self.probes[name] = (mask & ~self.solid, None if normal is None else np.asarray(normal, float))

    def set_fan(self, mask, direction, *, curve=None, speed=1.0, q_probe=None, dp_target=None, mag_phys=None,
                ctrl_every=50, relax=0.05, ctrl_start=200, ctrl_tau=100, lam_range=(0.3, 4.0)):
        """Fan actuator: force density along `direction` ((3,) or (3, n_cells)) in `mask`.
        curve: [[Q m3/s, dp Pa], ...] at 100 %; `speed` fraction (fan laws).  q_probe: probe name used for Q.
        mag_phys: initial force density N/m3 (default dp(Q=0.5 Qmax)/L_actuator)."""
        m = mask.ravel() & self.fluid_flat
        self.fan_idx = np.flatnonzero(m)
        d = np.asarray(direction, float)
        if d.ndim == 1:
            d = np.repeat((d / np.linalg.norm(d))[:, None], self.fan_idx.size, 1)
        else:
            d = d / np.maximum(np.linalg.norm(d, axis=0, keepdims=True), 1e-12)
        self.fan_e = d.astype(F32)
        if mag_phys is None:
            ed = np.abs(self.fan_e.mean(1))
            ax = int(np.argmax(ed))
            L = slab_thickness(mask & ~self.solid, np.eye(3)[ax]) * self.dx
            dp0 = fan_curve_dp(0.5 * curve[-1][0] * speed, curve, speed) if curve else (dp_target or 10.0)
            mag_phys = dp0 / L
        self.fan_mag = float(mag_phys) * self.dt ** 2 / (self.rho_phys * self.dx)   # lattice force density
        self.fan_ctrl = {"curve": curve, "speed": float(speed), "q_probe": q_probe, "every": int(ctrl_every),
                         "relax": float(relax), "start": int(ctrl_start), "dp_target": dp_target,
                         "tau": float(ctrl_tau), "mag0": self.fan_mag, "lam_range": tuple(lam_range)}
        self._fema = None
        # local fan law (curve given): every actuator cell gets F = lambda * dp_curve(A_act * e.u) / L_act along e,
        # i.e. the curve applied without lag (its negative slope damps the loop); lambda is trimmed slowly so the
        # integral (Q, int F.u dV / Q) sits on the curve despite a non-uniform actuator flow.
        ed = np.abs(self.fan_e.mean(1))
        Lc = slab_thickness(mask & ~self.solid, np.eye(3)[int(np.argmax(ed))])
        self.fan_local = curve is not None
        self.fan_L_m = Lc * self.dx
        self.fan_A_m2 = self.fan_idx.size / Lc * self.dx ** 2
        self.fan_lambda = 1.0
        self._fan_cells_F = (F32(self.fan_mag) * self.fan_e) if not self.fan_local else np.zeros_like(self.fan_e)

    # ---- core step
    def _fan_force(self):
        Ff = np.zeros((3, self.N), F32)
        if self.fan_idx is not None and self.fan_idx.size and not self.fan_local:
            Ff[:, self.fan_idx] = F32(self.fan_mag) * self.fan_e
        return Ff

    def _apply_local_fan(self, Ff):
        """Local fan law on the force-free velocity; updates u (half-force) and Ff at the actuator cells."""
        idx = self.fan_idx
        c = self.fan_ctrl
        u0 = self.u[:, idx]
        r = self.rho[idx]
        ue = (self.fan_e * u0).sum(0).astype(np.float64)
        dp = self.fan_lambda * fan_curve_dp_vec(ue * self.u_scale * self.fan_A_m2, c["curve"], c["speed"])
        fm = (dp / self.fan_L_m * self.dt ** 2 / (self.rho_phys * self.dx)).astype(F32)
        Fc = self.fan_e * fm
        Ff[:, idx] += Fc
        self.u[:, idx] = u0 + Fc / (2.0 * r)
        self._fan_cells_F = Fc

    def _pool(self):
        if self.threads <= 1:
            return None
        if getattr(self, "_ex", None) is None:
            from concurrent.futures import ThreadPoolExecutor
            self._ex = ThreadPoolExecutor(self.threads)
        return self._ex

    def _map(self, fn):
        sl = [slice(a, min(a + self.chunk, self.N)) for a in range(0, self.N, self.chunk)]
        ex = self._pool()
        if ex is None:
            for s in sl:
                fn(s)
        else:
            list(ex.map(fn, sl))

    def _moments(self, s, f, Ff):
        fc = f[:, s]
        r = fc.sum(0)
        m = _CT @ fc
        m += 0.5 * Ff[:, s]
        m /= r
        m *= self.fluid_f32[s]
        self.rho[s] = r
        self.u[:, s] = m

    def _relax(self, s, f, F):
        fc = f[:, s]
        r = self.rho[s]
        uu = self.u[:, s]
        t0 = F32(self.tau0)
        cu = Cf @ uu
        usq = (uu * uu).sum(0)
        t = cu * F32(4.5)
        t += F32(3.0)
        t *= cu
        t += (F32(1.0) - F32(1.5) * usq)
        t *= r
        t *= Wf                                   # t = feq
        t[0] = r - t[1:].sum(0)                   # exact mass conservation in float32 (rest population)
        np.subtract(fc, t, out=t)                 # t = fneq
        P = CC @ t
        pp = P[0] * P[0] + P[1] * P[1] + P[2] * P[2] + F32(2.0) * (P[3] * P[3] + P[4] * P[4] + P[5] * P[5])
        if self.cs > 0:
            tau = F32(0.5) * (t0 + np.sqrt(t0 * t0 + F32(18.0 * math.sqrt(2.0) * self.cs ** 2) * np.sqrt(pp) / r))
            self.nut[s] = (tau - t0) * F32(1.0 / 3.0) * self.fluid_f32[s]
            t *= F32(1.0) / tau
        else:
            tau = t0
            t *= F32(1.0) / t0
        fc -= t
        FF = F[:, s]
        if FF.any():
            cF = Cf @ FF
            uF = (uu * FF).sum(0)
            cF *= F32(3.0) + F32(9.0) * cu
            cF -= F32(3.0) * uF
            cF *= Wf
            cF *= (F32(1.0) - F32(0.5) / tau)
            fc += cF

    def _collide(self):
        f = self.f.reshape(19, self.N)
        Ff = self._fan_force()
        self._map(lambda s: self._moments(s, f, Ff))
        if self.fan_local and self.fan_idx is not None and self.fan_idx.size:
            self._apply_local_fan(Ff)
        F = Ff
        for z in self.por:
            idx = z["idx"]
            if idx.size == 0:
                continue
            u0 = self.u[:, idx]
            r = self.rho[idx]
            if z["kind"] == "iso":
                s0 = np.sqrt((u0 * u0).sum(0))
                h = 1.0 + 0.5 * z["b"]
                uz = u0 * (2.0 / (h + np.sqrt(h * h + 2.0 * z["c"] * s0)))
            elif z["kind"] == "diag":
                s = np.sqrt((u0 * u0).sum(0))       # |u| fixed point, geometric-mean damping (factor <= 0.5)
                for _ in range(8):
                    uz = u0 / (1.0 + 0.5 * z["c"] * s + 0.5 * z["beta"])
                    s = np.sqrt(s * np.sqrt((uz * uz).sum(0)))
                uz = u0 / (1.0 + 0.5 * z["c"] * s + 0.5 * z["beta"])
            else:
                a = z["axis"][:, None]
                us = (u0 * a).sum(0)
                ut = u0 - a * us
                h = 1.0 + 0.5 * z["b"]
                us2 = us * (2.0 / (h + np.sqrt(h * h + 2.0 * z["c"] * np.abs(us))))
                uz = a * us2 + ut / (1.0 + 0.5 * z["beta"])
            uz = uz.astype(F32)
            F[:, idx] += 2.0 * r * (uz - u0)
            self.u[:, idx] = uz
        self.F = F
        self._map(lambda s: self._relax(s, f, F))

    def _stream(self):
        src, dst = self.f, self.f2
        for i in range(19):
            si, di = src[i], dst[i]
            for d, s in self.plan[i]:
                di[d] = si[s]
        fp = src.reshape(19, self.N)
        fn = dst.reshape(19, self.N)
        for i in range(19):
            idx = self.bb[i]
            if idx.size:
                fn[i, idx] = fp[OPP[i], idx]
        if self.amb_idx is not None and self.amb_idx.size:
            fa = fn[:, self.amb_idx]
            ra = fa.sum(0)
            ua = (np.ascontiguousarray(Cf.T) @ fa) / ra
            fn[:, self.amb_idx] = feq_block(np.ones_like(ra), ua)
        self.f, self.f2 = self.f2, self.f

    def step(self, n=1):
        for _ in range(n):
            self._collide()
            self._stream()
            self.step_count += 1

    # ---- diagnostics
    def u3(self):
        return self.u.reshape((3,) + self.shape)

    def probe_q(self, name, u=None, rho=None):
        """Flow through probe `name` in m3/s at the reference density (mass flux / rho_ref), sign along its normal
        (normal None -> dominant axis of the mean velocity).  u, rho: lattice flat fields (default: current)."""
        mask, n = self.probes[name]
        u = (self.u if u is None else u).reshape((3,) + self.shape)
        rho = (self.rho if rho is None else rho).reshape(self.shape)
        if n is None:
            mean = np.array([float(u[a][mask].sum(dtype=np.float64)) for a in range(3)])
            ax = int(np.argmax(np.abs(mean)))
            n = np.eye(3)[ax] * (1.0 if mean[ax] >= 0 else -1.0)
        return self.q_phys(flux_through(u, mask, n, rho=rho))

    def _fan_L(self):
        if getattr(self, "_fanL", None) is None:
            e = np.abs(self.fan_e.mean(1))
            m = np.zeros(self.N, bool)
            m[self.fan_idx] = True
            self._fanL = slab_thickness(m.reshape(self.shape), np.eye(3)[int(np.argmax(e))])
        return self._fanL

    def _fan_raw(self, u=None, rho=None):
        """(sum e.u over actuator cells, SIGNED Q m3/s, mean rho in actuator) for the given lattice fields
        (signed so that window averages are not inflated by start-up sloshing; abs() is taken after averaging)."""
        u = self.u if u is None else u
        rho = self.rho if rho is None else rho
        eu = float((self.fan_e * u[:, self.fan_idx]).sum(dtype=np.float64))
        pw = float((self._fan_cells_F * u[:, self.fan_idx]).sum(dtype=np.float64))   # int F.u dV (lattice)
        c = self.fan_ctrl
        if c and c["q_probe"]:
            q = self.probe_q(c["q_probe"], u, rho)
        else:
            q = self.q_phys(eu / self._fan_L())
        return pw, q, float(rho[self.fan_idx].mean())

    def fan_state(self, u=None, rho=None):
        """(Q m3/s, delivered dp Pa = int F.u dV / Q_local) of the actuator for the given (default current) fields."""
        if self.fan_idx is None or self.fan_idx.size == 0:
            return 0.0, 0.0
        eu, q, r = self._fan_raw(u, rho)
        q = abs(q)
        q_lat = q * self.dt / self.dx ** 3 / r
        dp = (eu / q_lat) * self.p_scale if q_lat > 1e-12 else 0.0     # eu = int F.u dV here
        return q, dp

    def _control_fan(self, pw, q, r):
        """Slow trim of the local fan law on moving averages (time constant fan_ctrl['tau'] steps): lambda moves
        toward lambda * dp_curve(Q) / dp_delivered with gain fan_ctrl['relax'] every fan_ctrl['every'] steps,
        dp_delivered = int F.u dV / Q_local.  Clamped to fan_ctrl['lam_range'] (default 0.3-4): a lambda at a
        bound means the actuator cannot deliver the curve (report it).  Uniform-force mode (no curve): no control."""
        c = self.fan_ctrl
        if not self.fan_local:
            return None
        q = abs(q)
        tgt = fan_curve_dp(q, c["curve"], c["speed"])
        q_lat = q * self.dt / self.dx ** 3 / r
        dpmax = max(p[1] for p in c["curve"]) * c["speed"] ** 2
        if q_lat > 1e-12:
            dp = pw / q_lat * self.p_scale
            if dp > 0.05 * dpmax and tgt > 0.05 * dpmax:
                lam = self.fan_lambda
                lo, hi = c["lam_range"]
                self.fan_lambda = min(hi, max(lo, lam + c["relax"] * 2.0 * (lam * tgt / dp - lam)))
        return tgt

    def monitor(self, um, rm, num, um_prev):
        """Record for window-mean lattice fields um (3,N), rm (N), num (N)."""
        fl = self.fluid_flat
        un = float(np.sqrt((um[:, fl].astype(np.float64) ** 2).sum()))
        res = float(np.sqrt(((um[:, fl] - um_prev[:, fl]).astype(np.float64) ** 2).sum())) / max(un, 1e-30) \
            if um_prev is not None else float("nan")
        umax = float(np.sqrt((self.u * self.u).sum(0)).max())
        rec = {"step": self.step_count, "res_u": res, "umax_lat": umax, "umax_mps": umax * self.u_scale,
               "umean_max_mps": float(np.sqrt((um * um).sum(0)).max()) * self.u_scale,
               "nut_max_lat": float(num.max()), "rho_min": float(rm[fl].min()), "rho_max": float(rm[fl].max())}
        for name in self.probes:
            rec["Q_" + name] = self.probe_q(name, um, rm)
        if self.fan_idx is not None:
            q, dp = self.fan_state(um, rm)
            fmean = float(np.sqrt((self._fan_cells_F ** 2).sum(0)).mean())
            rec.update({"fan_Q": q, "fan_dp": dp, "fan_lambda": self.fan_lambda,
                        "fan_force_mean_Npm3": fmean * self.rho_phys * self.dx / self.dt ** 2})
            if self.fan_ctrl and self.fan_ctrl["curve"]:
                rec["fan_dp_curve"] = fan_curve_dp(q, self.fan_ctrl["curve"], self.fan_ctrl["speed"])
        if not np.isfinite(umax) or umax > 0.4:
            rec["diverged"] = True
        return rec

    def _new_acc(self):
        return [np.zeros((3, self.N), np.float32), np.zeros(self.N, np.float32), np.zeros(self.N, np.float32), 0]

    def run(self, nsteps, *, mon_every=500, sample_every=5, tol=2e-3, tol_q=3e-3, tol_fan=0.02, n_ok=3,
            checkpoint=None, ckpt_every=5000, deadline=None, verbose=False, log=None):
        """Advance up to nsteps.  Fields are sampled every `sample_every` steps and averaged over monitor windows
        of `mon_every` steps (filters residual acoustics / unsteadiness); the fan law is applied every
        fan_ctrl['every'] steps on moving averages (see _control_fan).  Converged when, for n_ok consecutive windows, the window-mean velocity
        changes by < tol (relative L2), every probe Q by < tol_q and the fan dp is within tol_fan of the curve.
        Returns 'converged' | 'maxsteps' | 'deadline' | 'diverged'.  Last window mean: self.mean (lattice)."""
        status, ok, last, um_prev = "maxsteps", 0, None, getattr(self, "_um_prev", None)
        acc = self._new_acc()
        c = self.fan_ctrl
        has_fan = c is not None and self.fan_idx is not None and self.fan_idx.size > 0
        t0 = time.time()
        for _ in range(int(nsteps)):
            self.step()
            sc = self.step_count
            if sc % sample_every == 0:
                acc[0] += self.u
                acc[1] += self.rho
                acc[2] += self.nut
                acc[3] += 1
                if has_fan:
                    x = self._fan_raw()
                    if self._fema is None:
                        self._fema = list(x)
                    else:
                        a = min(1.0, sample_every / c["tau"])
                        self._fema = [m + a * (v - m) for m, v in zip(self._fema, x)]
            if has_fan and sc >= c["start"] and sc % c["every"] == 0 and self._fema is not None:
                self._control_fan(*self._fema)
            if sc % mon_every == 0 and acc[3]:
                k = acc[3]
                um, rm, num = acc[0] / k, acc[1] / k, acc[2] / k
                self.mean = {"u": um, "rho": rm, "nut": num, "samples": k, "step": sc}
                rec = self.monitor(um, rm, num, um_prev)
                rec["wall_s"] = time.time() - t0
                um_prev = self._um_prev = um
                acc = self._new_acc()
                self.history.append(rec)
                if verbose:
                    print(json.dumps({a: (round(v, 7) if isinstance(v, float) else v) for a, v in rec.items()}),
                          flush=True, file=log or sys.stdout)
                if rec.get("diverged"):
                    status = "diverged"
                    break
                good = rec["res_u"] < tol
                if last is not None:
                    for a, v in rec.items():
                        if a.startswith("Q_") or a == "fan_Q":
                            good &= abs(v - last.get(a, v)) <= tol_q * max(abs(v), 1e-12)
                if "fan_dp_curve" in rec:   # relative to the curve value, floored at 10 % of shut-off pressure
                    ref = max(abs(rec["fan_dp_curve"]), 0.1 * max(p[1] for p in c["curve"]) * c["speed"] ** 2)
                    good &= abs(rec["fan_dp"] - rec["fan_dp_curve"]) <= tol_fan * ref
                last = rec
                ok = ok + 1 if good else 0
                if ok >= n_ok:
                    status = "converged"
                    break
            if checkpoint and sc % ckpt_every == 0:
                self.save(checkpoint)
            if deadline and time.time() > deadline:
                status = "deadline"
                break
        if checkpoint:
            self.save(checkpoint)
        return status

    # ---- output / checkpoint
    def fields(self, mean=True):
        """Physical fields from the last window mean (mean=True, if any) or the instantaneous state:
        u float32[3,nx,ny,nz] m/s, p Pa (gauge, (rho_lat-1)/3 * p_scale), nu_t m2/s, rho (lattice)."""
        fl = self.fluid_f32
        m = getattr(self, "mean", None) if mean else None
        u, rho, nut = (m["u"], m["rho"], m["nut"]) if m else (self.u, self.rho, self.nut)
        return {"u": (u * F32(self.u_scale) * fl).reshape((3,) + self.shape),
                "p": ((rho - 1.0) * F32(self.p_scale / 3.0) * fl).reshape(self.shape),
                "nu_t": (nut * F32(self.dx ** 2 / self.dt)).reshape(self.shape),
                "rho": rho.reshape(self.shape).copy()}

    def init_fields(self, u_phys, p_phys=None):
        """Start from given physical fields (e.g. a coarser-grid or other-case solution resampled to this grid):
        f = feq(rho, u) with rho = 1 + 3 p / p_scale; lattice speeds clipped to 0.2."""
        u = (np.asarray(u_phys, np.float32).reshape(3, -1) / F32(self.u_scale)) * self.fluid_f32
        sp = np.sqrt((u * u).sum(0))
        u *= np.minimum(1.0, 0.2 / np.maximum(sp, 1e-12)).astype(F32)
        rho = np.ones(self.N, F32) if p_phys is None else             (1.0 + 3.0 * np.asarray(p_phys, np.float32).ravel() / F32(self.p_scale)).astype(F32)
        f = self.f.reshape(19, self.N)
        for a0 in range(0, self.N, self.chunk):
            s_ = slice(a0, min(a0 + self.chunk, self.N))
            f[:, s_] = feq_block(rho[s_], u[:, s_])
        self.f2[...] = self.f
        self._collide_dry()

    def save(self, path):
        tmp = str(path) + ".tmp.npz"
        np.savez(tmp, f=self.f, fan_mag=self.fan_mag, fan_lambda=getattr(self, "fan_lambda", 1.0), step=self.step_count,
                 history=json.dumps(self.history), info=json.dumps(self.info()))
        os.replace(tmp, path)

    def load(self, path):
        z = np.load(path)
        if z["f"].shape != self.f.shape:
            raise ValueError("checkpoint shape mismatch")
        self.f[...] = z["f"]
        self.f2[...] = z["f"]
        self.fan_mag = float(z["fan_mag"])
        if "fan_lambda" in z.files:
            self.fan_lambda = float(z["fan_lambda"])
        self.step_count = int(z["step"])
        self.history = json.loads(str(z["history"]))
        self._collide_dry()

    def _collide_dry(self):
        """Recompute rho/u from f without advancing (after a restart)."""
        f = self.f.reshape(19, self.N)
        self.rho[:] = f.sum(0)
        self.u[:] = (np.ascontiguousarray(Cf.T) @ f) / self.rho * self.fluid_f32


# ----------------------------------------------------------------------------------------------- domain builder
def _meta_vec(meta, *keys):
    for k in keys:
        v = meta.get(k)
        if v is not None:
            return v
    return None


def _axis_vec(a):
    """'x' | '+x' | '-z' | [x, y, z] -> unit vector."""
    if isinstance(a, str):
        sg = -1.0 if a.strip().startswith("-") else 1.0
        v = np.zeros(3)
        v["xyz".index(a.strip().lstrip("+-").lower())] = sg
        return v
    v = np.asarray(a, float)
    return v / np.linalg.norm(v)


def build_solver(dom, params, *, speed=1.0, curve_key="curve_100", vent_K_scale=1.0, fin_K_scale=1.0,
                 fin_model=None, u_ref=None, tau_min=0.5, cs_smag=0.16, threads=1, beta_t=4.0, log=None):
    """Wire a loaded domain (load_domain) + params.json dict into an LBM.  Returns (solver, setup_notes).
    fin_model: None (auto: 'plates' if meta.fins.plate_normal, else 'axis') | 'axis' (Darcy-Forchheimer along the
    fin axis, both other axes blocked) | 'plates' (same law along both in-plane axes, blocked across the plates) |
    'diag' (params.fins.K_per_mm_xyz).  Vents without a K in params are left open (noted)."""
    notes = []
    meta = dom["meta"]
    masks = dom["masks"]
    dx = dom["dx_mm"] / 1000.0
    fl = params.get("fluid", {})
    fan = params.get("fan", {})
    curve = fan.get(curve_key) or fan.get("curve_100")
    if u_ref is None:
        qmax = curve[-1][0] * speed if curve else 5e-4
        out = masks.get("fan_outlet")
        a_out = 0.0
        if out is not None and out.any():
            n = mask_normal(meta, "fan_outlet")
            n = np.array([1.0, 0, 0]) if n is None else n
            a_out = out.sum() / slab_thickness(out, n) * dx * dx
        a_out = a_out if a_out > 0 else 1e-4
        u_ref = max(1.0, 2.0 * qmax / a_out)
        notes.append(f"u_ref {u_ref:.2f} m/s = 2 x Qmax/A_outlet (A_outlet {a_out*1e6:.0f} mm2)")
    s = LBM(dom["solid"], dx_m=dx, nu_phys=fl.get("nu", 1.6e-5), rho_phys=fl.get("rho", 1.13), u_ref=u_ref,
            tau_min=tau_min, cs_smag=cs_smag, threads=threads,
            dp_max=(max(p[1] for p in curve) * speed ** 2 if curve else None))
    if "ambient" in masks:
        s.set_ambient(masks["ambient"])
    else:
        notes.append("WARNING no mask__ambient: closed domain")
    vents = params.get("vents", {})
    for name, m in masks.items():
        if not name.startswith("vent__"):
            continue
        vid = name[6:]
        vp = vents.get(vid) or next((v for k, v in vents.items() if k.lower() == vid.lower()), None)
        n = mask_normal(meta, name)
        info = mask_info(meta, name)
        t = info.get("thickness_cells") or info.get("zone_thickness_cells")
        if t is None:
            t = slab_thickness(m, n) if n is not None else min(slab_thickness(m, np.eye(3)[a]) for a in range(3))
        if vp is None or vp.get("K") is None:
            notes.append(f"vent {vid}: no K in params -> open (no porous loss)")
        else:
            a_lin = float(vp.get("a_lin_Pa_per_mps", 0.0) or 0.0) * vent_K_scale
            s.add_porous_iso(m, float(vp["K"]) * vent_K_scale, float(t), name=vid, lin=s.lin_lat(a_lin))
            notes.append(f"vent {vid}: K {float(vp['K']) * vent_K_scale:.3g} + a_lin {a_lin:.3g} Pa/(m/s) over "
                         f"{float(t):.2f} cells, {int(m.sum())} cells")
        s.add_probe("vent__" + vid, m, n)
    fins = params.get("fins", {})
    fb = masks.get("fin_block")
    if fb is not None and fb.any() and fins:
        mf = meta.get("fins") if isinstance(meta.get("fins"), dict) else {}
        ax = _meta_vec(meta, "fin_porous_axis", "fin_axis") or mf.get("porous_axis") or \
            mask_info(meta, "fin_block").get("axis") or [1, 0, 0]
        ax = _axis_vec(ax)
        pn = mf.get("plate_normal")
        kind = fin_model or ("diag" if "K_per_mm_xyz" in fins else ("plates" if pn else "axis"))
        if kind == "diag":
            k = np.asarray(fins["K_per_mm_xyz"], float) * dom["dx_mm"] * fin_K_scale
            s.add_porous_diag(fb, k, beta=(0, 0, 0), name="fins")
            notes.append(f"fins diag K_per_cell {k.round(4).tolist()}")
        elif kind == "plates":
            # parallel plates normal to `pn`: the per-length channel law of params.fins along the two in-plane axes
            # (along the fins and between the plates, e.g. up out of an open-top fin block), blocked across them
            kp = fins.get("K_per_mm")
            if isinstance(kp, dict):
                c = 2.0 * float(kp["b_Pa_per_mps2_per_mm"]) / s.rho_phys * dom["dx_mm"] * fin_K_scale
                lin = s.lin_lat(float(kp["a_Pa_per_mps_per_mm"]) * dom["dx_mm"]) * fin_K_scale
            else:
                c = (float(kp) if kp is not None else float(fins["K_total"]) / float(
                    fins.get("length_mm") or fins.get("length_x_mm"))) * dom["dx_mm"] * fin_K_scale
                lin = 0.0
            na = int(np.argmax(np.abs(_axis_vec(pn))))
            K3 = [c, c, c]
            B3 = [lin, lin, lin]
            B3[na] = lin + beta_t
            s.add_porous_diag(fb, K3, beta=B3, name="fins")
            notes.append(f"fins plates (normal {'xyz'[na]}): K_per_cell {c:.4g}, lin_per_cell {lin:.4g} in-plane; "
                         f"+beta_t {beta_t} across")
        else:
            kp = fins.get("K_per_mm")
            lin_cell = 0.0
            if isinstance(kp, dict):      # dp/dx = a u + b u|u| per mm (af-data form)
                kpm = 2.0 * float(kp["b_Pa_per_mps2_per_mm"]) / s.rho_phys
                lin_cell = s.lin_lat(float(kp["a_Pa_per_mps_per_mm"]) * dom["dx_mm"]) * fin_K_scale
            elif kp is not None:
                kpm = float(kp)
            else:
                L = fins.get("length_mm") or fins.get("length_x_mm") or slab_thickness(fb, ax) * dom["dx_mm"]
                kpm = float(fins["K_total"]) / float(L)
            s.add_porous_axis(fb, ax, kpm * dom["dx_mm"] * fin_K_scale, beta_t=beta_t, name="fins",
                              lin_per_cell=lin_cell)
            notes.append(f"fins axis {ax.tolist()} K_per_cell {kpm * dom['dx_mm'] * fin_K_scale:.4g}, "
                         f"lin_per_cell {lin_cell:.4g}, beta_t {beta_t}")
    act = masks.get("fan_actuator")
    if act is not None and act.any():
        mfan = meta.get("fan") if isinstance(meta.get("fan"), dict) else {}
        fu = _meta_vec(meta, "fan_force_unit", "fan_force_units", "fan_dir") or mfan.get("force_unit") or \
            mask_info(meta, "fan_actuator").get("force_unit") or [1.0, 0.0, 0.0]
        if isinstance(fu, dict):          # {submask suffix: vector} with masks fan_actuator__<suffix>
            d = np.zeros((3,) + act.shape, F32)
            for k, v in fu.items():
                sm = masks.get("fan_actuator__" + k, act if k in ("all", "default") else None)
                if sm is not None:
                    vv = np.asarray(v, float) / np.linalg.norm(v)
                    for a in range(3):
                        d[a][sm] = vv[a]
            d = d.reshape(3, -1)[:, (act & ~dom["solid"]).ravel()]
        else:
            d = np.asarray(fu, float)
        if "fan_intake" in masks:
            s.add_probe("fan_intake", masks["fan_intake"], mask_normal(meta, "fan_intake"))
        if "fan_outlet" in masks:
            s.add_probe("fan_outlet", masks["fan_outlet"], mask_normal(meta, "fan_outlet"))
        s.set_fan(act, d, curve=curve, speed=speed, q_probe="fan_intake" if "fan_intake" in masks else None)
        notes.append(f"fan: {int(act.sum())} cells, speed {speed}, curve '{curve_key}'")
    else:
        notes.append("WARNING no mask__fan_actuator")
    notes.append(json.dumps({k: (round(v, 6) if isinstance(v, float) else v) for k, v in s.info().items()}))
    if log:
        for n_ in notes:
            print(n_, file=log)
    return s, notes


def resample_fields(fields, dom_from, dom_to):
    """Nearest-cell resampling of physical fields (u [3,...], p [...]) from one domain grid to another (same
    assembly frame: origin = centre of cell (0,0,0) in mm, dx in mm).  Use with LBM.init_fields to start the 1.5 mm
    run from the 2.0 mm solution.  Cells that land in a source solid get u = 0, p = 0."""
    o1, d1, sh1 = np.asarray(dom_from["origin"], float), dom_from["dx_mm"], dom_from["solid"].shape
    o2, d2, sh2 = np.asarray(dom_to["origin"], float), dom_to["dx_mm"], dom_to["solid"].shape
    idx = []
    for a in range(3):
        c = o2[a] + d2 * np.arange(sh2[a])
        idx.append(np.clip(np.rint((c - o1[a]) / d1).astype(int), 0, sh1[a] - 1))
    I, J, K = np.ix_(*idx)
    ok = ~dom_from["solid"][I, J, K]
    u = np.stack([fields["u"][a][I, J, K] * ok for a in range(3)]).astype(np.float32)
    p = (fields["p"][I, J, K] * ok).astype(np.float32) if "p" in fields else None
    return {"u": u, "p": p}
