"""Validation tests for thermal.py on synthetic domains (af-solver).  Run: python test_thermal.py [name ...]
Writes out/tests/test_thermal.json.  Plain asserts; pytest-compatible."""
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import thermal  # noqa: E402

RESULTS = {}


def test_1d_advection_diffusion():
    """Uniform flow U along x between Dirichlet ends (T 0 at x0, 1 at xN): exact discrete upwind solution and the
    continuous analytic profile (exp(Pe x/L) - 1)/(exp(Pe) - 1)."""
    n, dx, D = 61, 1e-3, 2e-5
    pc = 0.1                                   # cell Peclet U dx / D
    U = pc * D / dx
    solid = np.zeros((n, 3, 3), bool)
    amb = np.zeros_like(solid)
    amb[0] = amb[-1] = True
    dom = {"dx_mm": dx * 1e3, "solid": solid, "masks": {"ambient": amb}, "meta": {}}
    u = np.zeros((3,) + solid.shape)
    u[0] = U
    prob = thermal.Problem(dom, u, alpha=D)
    val = np.zeros(solid.shape)
    val[-1] = 1.0
    T, info = prob.solve(amb_value=val, cfl=0.9, tol=1e-10, max_iter=400000, check_every=500)
    t = T[:, 1, 1]
    i = np.arange(n)
    r = 1 + pc
    exact_d = (r ** i - 1) / (r ** (n - 1) - 1)
    Pe = U * (n - 1) * dx / D
    exact_c = (np.exp(Pe * i / (n - 1)) - 1) / (math.exp(Pe) - 1)
    e_d = float(np.abs(t - exact_d).max())
    e_c = float(np.abs(t - exact_c).max())
    RESULTS["advection_diffusion_1d"] = {"Pe": Pe, "cell_Pe": pc, "max_err_vs_discrete": e_d,
                                         "max_err_vs_analytic": e_c, "iters": info["iters"], "res": info["res"]}
    assert e_d < 1e-4, e_d
    assert e_c < 0.03, e_c


def _box(seed=0):
    """Walled duct 40 x 12 x 12 (fluid 10 x 10), ambient x<2 and x>37, internal block, noisy non-solenoidal u."""
    rng = np.random.default_rng(seed)
    shp = (40, 12, 12)
    solid = np.ones(shp, bool)
    solid[:, 1:-1, 1:-1] = False
    solid[18:22, 3:7, 3:7] = True               # obstacle
    x = np.arange(shp[0])[:, None, None] * np.ones(shp, bool)
    amb = ((x < 2) | (x > 37)) & ~solid
    heat = (x >= 12) & (x < 16) & ~solid
    heat2 = (x >= 25) & (x < 27) & ~solid
    vin = (x >= 2) & (x < 4) & ~solid
    vout = (x >= 36) & (x < 38) & ~solid
    y = np.arange(shp[1])[None, :, None]
    z = np.arange(shp[2])[None, None, :]
    prof = np.clip((y - 0.5) * (10.5 - y) * (z - 0.5) * (10.5 - z) / 25.0 ** 2, 0, None)
    u = np.zeros((3,) + shp)
    u[0] = 0.5 * prof * (1 + 0.2 * rng.standard_normal(shp))
    u[1] = 0.05 * rng.standard_normal(shp)
    u[2] = 0.05 * rng.standard_normal(shp)
    u *= ~solid
    nut = 1e-4 * rng.random(shp)
    dom = {"dx_mm": 2.0, "solid": solid, "meta": {},
           "masks": {"ambient": amb, "heat__a": heat, "heat__b": heat2, "vent__in": vin, "vent__out": vout,
                     "fan_outlet": (x == 30) & ~solid, "fan_intake": (x == 8) & ~solid}}
    return dom, u, nut


def test_projection_and_energy_balance():
    """Noisy velocity -> projected divergence-free fluxes; heat in = enthalpy out (adiabatic) and
    = enthalpy out + shell loss (h_ext 10 W/m2K); a uniform field is an exact steady solution (stays put)."""
    dom, u, nut = _box()
    prob = thermal.Problem(dom, u, nu_t=nut)
    s = prob.summary()
    T, info = thermal.solve_temperature(prob, dom, {"a": 1.5, "b": 0.5}, T_amb=30.0, cfl=0.9, tol=1e-9,
                                        max_iter=200000)
    T2, info2 = thermal.solve_temperature(prob, dom, {"a": 1.5, "b": 0.5}, T_amb=30.0, h_ext=10.0, cfl=0.9,
                                          tol=1e-9, max_iter=200000)
    U, iu = prob.solve(amb_value=1.0, cfl=0.9, tol=1e-12, max_iter=200, check_every=100, x0=np.ones(dom["solid"].shape))
    T3, info3 = thermal.solve_temperature(prob, dom, {"a": 1.5, "b": 0.5}, T_amb=30.0, tol=1e-10,
                                          max_iter=5000, method="bicgstab")
    q_out, q_in = prob.boundary_flux()
    dT_mix = 2.0 / (1.13 * 1007.0 * q_out)
    th_out = thermal.probe_stats(prob, T - 30.0, (np.arange(40)[:, None, None] == 35) * np.ones(dom["solid"].shape,
                                                                                              bool), "flux")
    RESULTS["energy_balance"] = {
        "projection": s["projection"], "Q_out": q_out, "Q_in": q_in,
        "adiabatic": {k: info[k] for k in ("heat_in_W", "enthalpy_out_W", "balance_rel", "iters", "res")},
        "exterior_h10": {k: info2[k] for k in ("heat_in_W", "enthalpy_out_W", "shell_loss_W", "balance_rel",
                                               "iters", "res")},
        "uniform_T_max_dev": float(np.nanmax(np.abs(U[prob.open] - 1.0))),
        "mixing_cup_dT_K": dT_mix, "outlet_flux_mean_dT_K": th_out.get("flux_mean"),
        "T_max_C": float(np.nanmax(T)),
        "bicgstab": {"iters": info3["iters"], "res": info3["res"], "balance_rel": info3["balance_rel"],
                     "max_dT_vs_pseudo_K": float(np.nanmax(np.abs(T3 - T)))}}
    assert abs(info3["balance_rel"]) < 1e-6 and float(np.nanmax(np.abs(T3 - T))) < 1e-4
    assert s["projection"]["div_after_rel"] < 1e-6, s["projection"]
    assert abs(q_out - q_in) / q_out < 1e-6
    assert abs(info["balance_rel"]) < 1e-3, info["balance_rel"]
    assert abs(info2["balance_rel"]) < 1e-3, info2["balance_rel"]
    assert info2["shell_loss_W"] > 0
    assert RESULTS["energy_balance"]["uniform_T_max_dev"] < 1e-6


def test_tracers_and_age():
    """Per-vent tracers sum to 1; flux-weighted outlet age = V/Q (nominal time constant); no recirculation tag
    upstream in a through-flow duct."""
    dom, u, nut = _box(1)
    u[1:] = 0.0
    prob = thermal.Problem(dom, u, nu_t=None, alpha=2e-6)
    kw = dict(cfl=0.9, tol=1e-9, max_iter=200000)
    tr, lab, names, infos = thermal.vent_tracers(prob, dom, **kw)
    ssum = sum(np.nan_to_num(tr[n]) for n in names)
    dev = float(np.abs(ssum[prob.active] - 1).max())
    age, ia = thermal.mean_age(prob, **kw)
    q_out, _ = prob.boundary_flux()
    V = float(prob.active.sum()) * prob.V
    # flux-weighted age on the faces into the outlet ambient
    x = np.arange(40)[:, None, None] * np.ones(dom["solid"].shape, bool)
    f = prob.F[0][37]
    a_face = age[37]
    age_out = float((f * np.nan_to_num(a_face)).sum() / f.sum())
    rc, ir = thermal.recirculation_tracer(prob, dom, **kw)
    rc_in = thermal.probe_stats(prob, rc, dom["masks"]["fan_intake"])
    RESULTS["tracers_age"] = {"vents": names, "tracer_sum_max_dev": dev,
                              "tracer_in_at_intake": thermal.probe_stats(prob, tr["in"], dom["masks"]["fan_intake"]),
                              "age_out_s": age_out, "V_over_Q_s": V / q_out, "age_rel_err": age_out * q_out / V - 1,
                              "recirc_at_intake": rc_in, "age_iters": ia["iters"]}
    assert dev < 1e-4, dev
    assert abs(age_out * q_out / V - 1) < 0.03, (age_out, V / q_out)
    assert rc_in["max"] < 0.01, rc_in


ALL = ["test_1d_advection_diffusion", "test_projection_and_energy_balance", "test_tracers_and_age"]

if __name__ == "__main__":
    names = sys.argv[1:] or ALL
    ok = True
    for nm in names:
        t = time.time()
        try:
            globals()[nm]()
            print(f"PASS {nm} ({time.time() - t:.0f} s)", flush=True)
        except AssertionError as e:
            ok = False
            print(f"FAIL {nm}: {e}", flush=True)
        RESULTS.setdefault("_timing_s", {})[nm] = time.time() - t
    os.makedirs(os.path.join(HERE, "out", "tests"), exist_ok=True)
    path = os.path.join(HERE, "out", "tests", "test_thermal.json")
    old = json.load(open(path)) if os.path.exists(path) else {}
    old.update(RESULTS)
    json.dump(old, open(path, "w"), indent=1, default=float)
    sys.exit(0 if ok else 1)
