"""D2 airflow study, af-run: 3D LBM flow run on the voxel domain of the existing (baseline r2) arrangement.

Usage (repo root, outside the CAD lock):
  .venv-cad/Scripts/python.exe cad/gs8-d2-v1/airflow/run_airflow.py --dx 2.0 --case base [--speed 0.5]
      [--curve curve_100] [--fin-model plates|axis|diag] [--init out/flow-2.0.npz] [--max-min 50]

Fan point: lbm's local fan law + slow lambda trim is the outer iteration of the fan force onto the curve; every
500-step window is logged (fan_Q, fan_dp delivered, fan_dp_curve, lambda).  Convergence (af-run criteria, brief):
  * fan intake Q steady within 1 % over the last 10 % of steps (at least the last 3000 steps),
  * fan point on the curve within 5 %,
  * mass balance over the vents: |sum of signed vent Q| <= 2 % of the inflow.
Vent K: params K is referenced to the nominal box face area; the grid face area differs (meta area ratio r =
A_grid/A_box), so the porous zone gets K r^2 and a_lin r (same dp at the same volume flow).
Writes out/flow-<dx>[-case].npz (u, p, nu_t, rho, history, info, notes, status, criteria) and a checkpoint.
"""
import argparse
import copy
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lbm  # noqa: E402


def scaled_params(params, meta, log):
    p = copy.deepcopy(params)
    for vid, vm in meta.get("vents", {}).items():
        r = float(vm.get("area_ratio_discrete_to_box") or 1.0)
        vp = p["vents"].get(vid)
        if vp is None:
            continue
        vp["K_box"] = vp["K"]
        vp["K"] = float(vp["K"]) * r * r
        vp["a_lin_Pa_per_mps"] = float(vp.get("a_lin_Pa_per_mps", 0.0) or 0.0) * r
        print(f"vent {vid}: area ratio {r:.3f} -> K {vp['K_box']:.3f} -> {vp['K']:.3f} (grid velocity basis)", file=log)
    return p


def criteria(s, curve_dp_tol=0.05, q_tol=0.01, mass_tol=0.02, vent_tol=0.05, min_steps=8000):
    h = s.history
    if not h:
        return {"ok": False}
    last_step = h[-1]["step"]
    span = max(0.1 * last_step, 3000)
    win = [r for r in h if r["step"] > last_step - span]
    q = np.array([r.get("Q_fan_intake", r.get("fan_Q", 0.0)) for r in win])
    qm = float(np.mean(q)) if len(q) else 0.0
    q_var = float((q.max() - q.min()) / max(abs(qm), 1e-12)) if len(q) else 1.0
    r = h[-1]
    fan_err = abs(r.get("fan_dp", 0) - r.get("fan_dp_curve", 0)) / max(abs(r.get("fan_dp_curve", 0)), 1e-9)
    vq = {k[8:]: v for k, v in r.items() if k.startswith("Q_vent__")}
    qin = sum(-v for v in vq.values() if v < 0)
    qout = sum(v for v in vq.values() if v > 0)
    mass = abs(qout - qin) / max(qin, 1e-12)
    # vent flows (the through-flow) settle on the body circulation time, much slower than the fan point:
    # each vent's Q range over the window <= vent_tol x the through-flow
    vr = {}
    for k in vq:
        a = np.array([r_.get("Q_vent__" + k, 0.0) for r_ in win])
        vr[k] = float((a.max() - a.min()) / max(qin, 1e-12)) if len(a) else 1.0
    vent_var = max(vr.values()) if vr else 0.0
    ok = (len(win) >= 6 and q_var <= q_tol and fan_err <= curve_dp_tol and mass <= mass_tol and
          vent_var <= vent_tol and last_step >= min_steps)
    return {"ok": bool(ok), "step": last_step, "window_steps": span, "Q_intake_mean": qm, "Q_rel_range": q_var,
            "fan_dp": r.get("fan_dp"), "fan_dp_curve": r.get("fan_dp_curve"), "fan_rel_err": fan_err,
            "fan_lambda": r.get("fan_lambda"), "vent_Q": vq, "Q_in": qin, "Q_out": qout, "mass_rel": mass,
            "vent_rel_range": vr, "vent_rel_range_max": vent_var}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dx", default="2.0")
    ap.add_argument("--case", default="")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--curve", default="curve_100")
    ap.add_argument("--fin-model", default=None)
    ap.add_argument("--init", default=None)
    ap.add_argument("--max-min", type=float, default=50.0)
    ap.add_argument("--chunk", type=int, default=2000)
    ap.add_argument("--max-steps", type=int, default=40000)
    ap.add_argument("--final-window", type=int, default=2000)
    ap.add_argument("--min-steps", type=int, default=20000)
    a = ap.parse_args()
    lbm.set_low_priority()
    tag = a.dx + (("-" + a.case) if a.case else "")
    out = os.path.join(HERE, "out")
    logf = open(os.path.join(out, f"run-{tag}.log"), "a", buffering=1)
    print(f"=== {time.strftime('%Y-%m-%d %H:%M:%S')} run {tag} {vars(a)}", file=logf)
    while lbm.free_ram_mb() < 1200:
        print(f"waiting for RAM: {lbm.free_ram_mb():.0f} MB free", file=logf)
        time.sleep(30)
    t_end = time.time() + 60 * a.max_min
    dom = lbm.load_domain(os.path.join(out, f"domain-{a.dx}.npz"))
    params = scaled_params(json.load(open(os.path.join(HERE, "params.json"))), dom["meta"], logf)
    s, notes = lbm.build_solver(dom, params, speed=a.speed, curve_key=a.curve, fin_model=a.fin_model, log=logf)
    ck = os.path.join(out, f"ckpt-{tag}.npz")
    if os.path.exists(ck):
        s.load(ck)
        print(f"resumed from {ck} at step {s.step_count}", file=logf)
    elif a.init:
        z = np.load(os.path.join(HERE, a.init) if not os.path.isabs(a.init) else a.init)
        src = z["u"], z["p"]
        dsrc = str(z["domain"]) if "domain" in z.files else None
        if dsrc and dsrc != f"domain-{a.dx}.npz":
            d0 = lbm.load_domain(os.path.join(out, dsrc))
            rf = lbm.resample_fields({"u": src[0], "p": src[1], "nu_t": z["nu_t"], "rho": z["rho"]}, d0, dom)
            src = rf["u"], rf["p"]
        p0 = src[1] * (a.speed ** 2 if a.speed != 1.0 else 1.0)
        s.init_fields(src[0] * a.speed, p0)
        print(f"init from {a.init} (speed scale {a.speed})", file=logf)
    status, crit = "maxsteps", {}
    while True:
        st = s.run(a.chunk, mon_every=500, sample_every=5, tol=-1.0, checkpoint=ck, ckpt_every=a.chunk,
                   deadline=t_end, verbose=True, log=logf)
        crit = criteria(s, min_steps=a.min_steps)
        print("CRIT " + json.dumps({k: v for k, v in crit.items() if k != "vent_Q"}), file=logf)
        if st == "diverged":
            status = "diverged"
            break
        if crit.get("ok"):
            status = "converged"
            break
        if st == "deadline" or time.time() > t_end:
            status = "deadline (PARTIAL)"
            break
        if s.step_count >= a.max_steps:
            status = "maxsteps (PARTIAL)"
            break
    if status != "diverged" and time.time() < t_end + 300:
        s.run(a.final_window, mon_every=a.final_window, sample_every=5, tol=-1.0, verbose=True, log=logf)
        crit_final = criteria(s, min_steps=a.min_steps)
    else:
        crit_final = crit
    f = s.fields()
    np.savez_compressed(os.path.join(out, f"flow-{tag}.npz"), u=f["u"], p=f["p"], nu_t=f["nu_t"], rho=f["rho"],
                        domain=f"domain-{a.dx}.npz", history=json.dumps(s.history), info=json.dumps(s.info()),
                        notes=json.dumps(notes), status=status, criteria=json.dumps(crit),
                        criteria_final=json.dumps(crit_final), args=json.dumps(vars(a)),
                        params_used=json.dumps({k: params[k] for k in ("vents", "fan")}))
    s.save(ck)
    print(f"=== DONE {time.strftime('%H:%M:%S')} status {status} steps {s.step_count}", file=logf)
    print(f"DONE {tag} {status} {s.step_count}")


if __name__ == "__main__":
    main()
