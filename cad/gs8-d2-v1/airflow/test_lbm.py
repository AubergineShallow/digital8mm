"""Validation tests for lbm.py on synthetic domains (af-solver).  Run: python test_lbm.py [name ...]
Writes out/tests/test_lbm.json with the measured numbers.  Plain asserts; pytest-compatible."""
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lbm  # noqa: E402

RESULTS = {}


def _duct(nx, n, wall=1):
    solid = np.ones((nx, n + 2 * wall, n + 2 * wall), bool)
    solid[:, wall:-wall, wall:-wall] = False
    return solid


def lattice_solver(solid, tau=0.8, periodic=(False, False, False), cs=0.0):
    """Lattice units: dx = dt = 1, rho = 1, nu = (tau - 0.5)/3."""
    return lbm.LBM(solid, dx_m=1.0, nu_phys=(tau - 0.5) / 3, rho_phys=1.0, u_ref=0.1, u_lat_max=0.1,
                   tau_min=0.5, cs_smag=cs, periodic=periodic, threads=1)


def test_square_duct_poiseuille():
    """Periodic square duct (16 x 16 fluid cells) driven by a body force vs the analytic series flow rate."""
    n, g, tau = 16, 2.5e-4, 0.8
    solid = _duct(8, n)
    s = lattice_solver(solid, tau, periodic=(True, False, False))
    s.set_fan(~solid, [1, 0, 0], mag_phys=g, ctrl_every=10 ** 9, ctrl_start=10 ** 9)
    s.add_probe("x", np.ones_like(solid), [1, 0, 0])
    st = s.run(8000, mon_every=200, tol=1e-6, n_ok=2)
    nu = (tau - 0.5) / 3
    h = n / 2
    ser = sum(math.tanh(i * math.pi / 2) / i ** 5 for i in range(1, 400, 2))
    qa = 4 * h ** 4 * g / (3 * nu) * (1 - 192 / math.pi ** 5 * ser)
    q = s.probe_q("x")
    err = q / qa - 1
    RESULTS["square_duct_poiseuille"] = {"Q_lbm": q, "Q_analytic": qa, "rel_err": err, "steps": s.step_count,
                                         "status": st, "tau": tau}
    assert abs(err) < 0.03, err


def _porous_box(kind, K=4.0, t=2, g=4e-4, lin=0.0):
    """Fully periodic 1-D box (no walls): actuator x 0..3, porous slab x 20..20+t."""
    solid = np.zeros((40, 4, 4), bool)
    s = lattice_solver(solid, 0.8, periodic=(True, True, True))
    act = np.zeros_like(solid)
    act[0:4] = True
    zone = np.zeros_like(solid)
    zone[20:20 + t] = True
    if kind == "iso":
        s.add_porous_iso(zone, K, t, lin=lin)
    elif kind == "axis":
        s.add_porous_axis(zone, [1, 0, 0], K / t, beta_t=4.0)
    else:
        s.add_porous_diag(zone, (K / t, 3.0, 3.0))
    s.set_fan(act, [1, 0, 0], mag_phys=g, ctrl_every=10 ** 9, ctrl_start=10 ** 9)
    s.run(6000, mon_every=200, tol=1e-7, n_ok=2)
    p = (s.rho.reshape(solid.shape) - 1.0) / 3.0
    dp = float(p[10].mean() - p[30].mean())
    u = float(s.u3()[0][30].mean())
    rho = float(s.rho.reshape(solid.shape)[20:20 + t].mean())
    pred = K * 0.5 * rho * u * u + lin * rho * u
    return dp, pred, u, 4 * g


def test_porous_pressure_drop():
    """Forchheimer zone: measured dp vs K 0.5 rho u^2 (iso, axis and diag kinds; iso plus a linear Darcy term),
    and the momentum balance."""
    out = {}
    for kind, lin in (("iso", 0.0), ("axis", 0.0), ("diag", 0.0), ("iso_lin", 0.05)):
        dp, pred, u, drive = _porous_box(kind.replace("_lin", ""), lin=lin)
        out[kind] = {"dp": dp, "K_half_rho_u2": pred, "u": u, "rel_err": dp / pred - 1, "drive": drive}
        assert abs(dp / pred - 1) < 0.03, (kind, dp, pred)
        assert abs(dp / drive - 1) < 0.03, (kind, dp, drive)
    RESULTS["porous_pressure_drop"] = out


def _fan_duct(tau_min=0.53, cs=0.16, curve=((0.0, 120.0), (0.0005, 80.0), (0.001, 0.0)), K=3.0, u_ref=3.0):
    solid = _duct(64, 12)
    s = lbm.LBM(solid, dx_m=0.002, nu_phys=1.6e-5, rho_phys=1.13, u_ref=u_ref, tau_min=tau_min, cs_smag=cs,
                threads=2, dp_max=max(c[1] for c in curve))
    x = np.arange(64)[:, None, None] * np.ones(solid.shape, bool)
    s.set_ambient((x < 3) | (x > 60))
    s.add_porous_iso((x >= 40) & (x < 42), K, 2, name="vent")
    pl = lambda i: (x == i)  # noqa: E731
    s.add_probe("intake", pl(6), [1, 0, 0])
    s.add_probe("x20", pl(20), [1, 0, 0])
    s.add_probe("x50", pl(50), [1, 0, 0])
    s.add_probe("x59", pl(59), [1, 0, 0])
    s.set_fan((x >= 8) & (x < 14), [1, 0, 0], curve=[list(c) for c in curve], q_probe="intake",
              ctrl_start=200)
    return s, solid


def test_mass_balance_and_fan_curve():
    """Open duct (ambient reservoirs at both ends), fan actuator on a curve, porous vent: Q in = Q out within 1 %,
    operating point on the curve within 2 %, porous dp vs K."""
    s, solid = _fan_duct()
    st = s.run(30000, mon_every=500, tol=1e-3, tol_q=1e-3, tol_fan=0.02, n_ok=3)
    m = s.mean
    q = {k: s.probe_q(k, m["u"], m["rho"]) for k in ("intake", "x20", "x50", "x59")}
    qs = np.array(list(q.values()))
    imb = float((qs.max() - qs.min()) / qs.mean())
    qf, dpf = s.fan_state(m["u"], m["rho"])
    dpc = lbm.fan_curve_dp(qf, [[0.0, 120.0], [0.0005, 80.0], [0.001, 0.0]])
    f = s.fields()
    p = f["p"]
    dpv = float(p[36, 1:-1, 1:-1].mean() - p[46, 1:-1, 1:-1].mean())
    ubar = float(f["u"][0][41, 1:-1, 1:-1].mean())
    RESULTS["mass_balance_fan_curve"] = {"status": st, "steps": s.step_count, "Q_m3s": q, "imbalance": imb,
                                         "fan_Q": qf, "fan_dp": dpf, "curve_dp": dpc, "info": s.info(),
                                         "dp_36_46_Pa_vent_plus_duct_friction": dpv, "K_half_rho_u2_Pa": 3.0 * 0.5 * 1.13 * ubar ** 2,
                                         "last": s.history[-1]}
    assert st == "converged", st
    assert imb < 0.01, imb
    assert abs(dpf / dpc - 1) < 0.02, (dpf, dpc)


def _jet_box(tau_min, cs=0.16, steps=6000, u_ref=5.0):
    """Realistic-Re jet: blower duct (8x8 cells) -> plenum 32x30x30 -> offset 6x6 outlet; dx 2 mm, real air nu."""
    shp = (64, 32, 32)
    solid = np.zeros(shp, bool)
    x = np.arange(shp[0])[:, None, None] * np.ones(shp, bool)
    solid[:, 0, :] = solid[:, -1, :] = solid[:, :, 0] = solid[:, :, -1] = True
    duct = np.zeros(shp, bool)
    duct[:, 12:20, 12:20] = True
    solid |= (x >= 3) & (x < 16) & ~duct                     # duct wall block
    solid[56:61] = True                                      # outlet plate
    solid[56:61, 20:26, 6:12] = False                        # offset outlet hole
    s = lbm.LBM(solid, dx_m=0.002, nu_phys=1.6e-5, rho_phys=1.13, u_ref=u_ref, tau_min=tau_min, cs_smag=cs,
                dp_max=150.0)
    s.set_ambient(((x < 3) | (x > 60)) & ~solid)
    s.add_probe("in", (x == 10) & duct, [1, 0, 0])
    s.add_probe("out", (x == 58) & ~solid, [1, 0, 0])
    s.set_fan((x >= 5) & (x < 12) & duct, [1, 0, 0], curve=[[0, 150.0], [0.0005, 100.0], [0.001, 0.0]],
              q_probe="in", ctrl_start=200)
    st = s.run(steps, mon_every=500, tol=0.0)
    return s, st


def test_smagorinsky_stability_real_reynolds():
    """Jet into a plenum at real-air viscosity (Re factor 1, tau0 ~ 0.5005) with Smagorinsky C_s 0.16: must stay
    stable (finite, max lattice speed < 0.25) for 6000 steps (0.1 s, > 1 flow-through)."""
    s, st = _jet_box(tau_min=0.5)
    last = s.history[-1]
    qin, qout = s.history[-1]["Q_in"], s.history[-1]["Q_out"]
    re = abs(qin) / (0.016 ** 2) * 0.016 / 1.6e-5
    RESULTS["smagorinsky_real_Re"] = {"status": st, "info": s.info(), "last": last, "Q_in": qin, "Q_out": qout,
                                      "Re_duct": re}
    assert st != "diverged" and np.isfinite(last["umax_lat"]) and last["umax_lat"] < 0.25, last
    assert re > 1000, re


ALL = ["test_square_duct_poiseuille", "test_porous_pressure_drop", "test_mass_balance_and_fan_curve",
       "test_smagorinsky_stability_real_reynolds"]

if __name__ == "__main__":
    lbm.set_low_priority()
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
    path = os.path.join(HERE, "out", "tests", "test_lbm.json")
    old = json.load(open(path)) if os.path.exists(path) else {}
    old.update(RESULTS)
    json.dump(old, open(path, "w"), indent=1, default=float)
    sys.exit(0 if ok else 1)
