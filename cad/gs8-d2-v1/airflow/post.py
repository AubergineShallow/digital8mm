"""D2 airflow study, af-run post-processing.

  .venv-cad/Scripts/python.exe cad/gs8-d2-v1/airflow/post.py compute --tag 2.0      # thermal + tracers -> out/thermal-<tag>.npz, out/metrics-<tag>.json
  .venv-cad/Scripts/python.exe cad/gs8-d2-v1/airflow/post.py figs --tag 2.0         # figures -> out/figures/<tag>/
  .venv-cad/Scripts/python.exe cad/gs8-d2-v1/airflow/post.py merge                   # out/metrics.json from all metrics-*.json

Thermal: steady upwind FV on the window-mean LBM field (thermal.py, BiCGSTAB), heat loads params.heat S2 (record,
G-W11 case) and S3 (burst), ambient 30 C; walls adiabatic (conservative) and with the exterior loss U = params.walls.
Recirculation: (a) exhaust tag c = 1 at the fin-exit plane (thermal.recirculation_tracer) and (b) a unit source in the
blower interior: R = c_in / (c_in + 1/Q_fan) with c_in the flux-weighted value at the fan intake (= fraction of the
intake air that has already passed through the fan; it also counts the bypass over the open-top fins).
SoC estimate (ESTIMATE): T_fin_inlet_air + P_soc x R_sink(Q_fin), R_sink = network.sink_R (params.sink), Q_fin =
x-flux into the fin block at its inlet face, T_fin_inlet_air = flux-weighted air T on the face just upstream.
"""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
sys.path.insert(0, HERE)
import lbm  # noqa: E402
import thermal  # noqa: E402

STATES = ("S2", "S3")


def load(tag):
    z = np.load(os.path.join(OUT, f"flow-{tag}.npz"))
    dom = lbm.load_domain(os.path.join(OUT, str(z["domain"])))
    params = json.load(open(os.path.join(HERE, "params.json")))
    return z, dom, params


def fin_faces(dom):
    fb = dom["masks"]["fin_block"]
    xs = np.where(fb.any(axis=(1, 2)))[0]
    return fb, int(xs.min()), int(xs.max())


def fin_flow_profile(prob, dom):
    """x-flux (m3/s) through each x face of the fin block, from the inlet face (x0-1 | x0) to the exit face."""
    fb, x0, x1 = fin_faces(dom)
    prof = []
    for i in range(x0 - 1, x1 + 1):
        sec = fb[i + 1] if i + 1 <= x1 else fb[i]
        prof.append(float(prob.F[0][i][sec].sum()))
    return prof, x0, x1


def flux_mean_on_face(prob, field, i, sec):
    """flux-weighted mean of field on the x face i|i+1 over section sec (upwind value)."""
    f = prob.F[0][i][sec]
    up = np.where(f >= 0, field[i][sec], field[i + 1][sec])
    w = np.abs(f)
    return float((w * np.nan_to_num(up)).sum() / max(w.sum(), 1e-30))


def label_ambient_by_vent(prob, dom, lab):
    """Assign each ambient cell to the vent whose outside buffer it belongs to: multi-source growth from each vent
    zone through outside air only (labels 3 buffer, 4 ambient, 5 vent zone).  (thermal.label_ambient_by_vent seeds
    only ambient cells touching a vent zone, but the buffer is 5 cells deep, so most reservoirs stayed unlabelled.)"""
    names = sorted(k[6:] for k in dom["masks"] if k.startswith("vent__"))
    through = np.isin(lab, (3, 4, 5)) & prob.open
    L = np.full(prob.shape, -1, np.int32)
    for k, n in enumerate(names):
        L[dom["masks"]["vent__" + n] & (L < 0)] = k
    for _ in range(1000):
        grew = False
        for k in range(len(names)):
            g = thermal.dilate(L == k) & through & (L < 0)
            if g.any():
                L[g] = k
                grew = True
        if not grew:
            break
    La = np.where(prob.amb, L, -1)
    return La, names


def compute(tag, parts=("tracers", "recirc", "thermal")):
    t0 = time.time()
    lbm.set_low_priority()
    z, dom, params = load(tag)
    log = open(os.path.join(OUT, f"post-{tag}.log"), "a", buffering=1)
    print(f"=== {time.strftime('%H:%M:%S')} compute {tag}", file=log)
    hist = json.loads(str(z["history"]))
    fl = params["fluid"]
    rho, cp = fl.get("rho", 1.13), fl.get("cp", 1007.0)
    lab = np.load(os.path.join(OUT, str(z["domain"])))["label"]
    leg = json.dumps(dom["meta"].get("label_legend"))
    dom["masks"]["exterior"] = (lab == 2) & dom["solid"]     # inactive outside cells (label 2, see label_legend)
    prob = thermal.Problem(dom, z["u"], rho=z["rho"], nu_t=z["nu_t"], log=log)
    M = {"tag": tag, "status": str(z["status"]), "args": json.loads(str(z["args"])),
         "info": json.loads(str(z["info"])), "criteria": json.loads(str(z["criteria"])),
         "criteria_final": json.loads(str(z["criteria_final"])), "problem": prob.summary(),
         "history_last": hist[-1] if hist else None, "n_windows": len(hist)}
    masks = dom["masks"]
    last = hist[-1]
    Qf = float(last.get("Q_fan_intake", last.get("fan_Q")))
    M["fan"] = {"Q_m3s": Qf, "Q_CFM": Qf / 4.719e-4, "dp_delivered_Pa": last.get("fan_dp"),
                "dp_curve_Pa": last.get("fan_dp_curve"), "lambda": last.get("fan_lambda"),
                "Q_fin_exit_plane_m3s": last.get("Q_fan_outlet")}
    vq = {k[8:]: float(v) for k, v in last.items() if k.startswith("Q_vent__")}
    M["vents_Q_out_positive_m3s"] = vq
    M["Q_through_m3s"] = {"in": sum(-v for v in vq.values() if v < 0), "out": sum(v for v in vq.values() if v > 0)}
    # pressures and speeds at probes
    p, u = z["p"], z["u"]
    sp = np.sqrt((u.astype(np.float64) ** 2).sum(0))
    M["probes"] = {}
    for k, m in masks.items():
        if k.startswith("probe__") or k in ("fan_intake", "fan_outlet", "fin_block"):
            mm = m & prob.open
            if mm.any():
                M["probes"][k] = {"cells": int(mm.sum()), "speed_mean_mps": float(sp[mm].mean()),
                                  "speed_max_mps": float(sp[mm].max()), "p_mean_Pa": float(p[mm].mean())}
    body = prob.active & ~masks["fan_actuator"]
    M["body_air"] = {"cells": int(body.sum()), "speed_mean_mps": float(sp[body].mean()),
                     "p_mean_Pa": float(p[body].mean())}
    # fin flow
    prof, x0, x1 = fin_flow_profile(prob, dom)
    M["fins"] = {"x_faces_flux_m3s": prof, "Q_fin_inlet_m3s": prof[0], "Q_fin_exit_face_m3s": prof[-1],
                 "x0": x0, "x1": x1}
    fb = masks["fin_block"]
    sec_in = fb[x0]
    fields = {}
    mp, tp = os.path.join(OUT, f"metrics-{tag}.json"), os.path.join(OUT, f"thermal-{tag}.npz")
    if set(parts) != {"tracers", "recirc", "thermal"} and os.path.exists(mp):
        old = json.load(open(mp))
        old.update({k: v for k, v in M.items()})
        M = old
        if os.path.exists(tp):
            fields = {k: v for k, v in np.load(tp).items()}
    nfan = lbm.mask_normal(dom["meta"], "fan_intake")
    if "tracers" in parts:
        La, names = label_ambient_by_vent(prob, dom, lab)
        M["intake_air_by_vent"], M["tracer_solve"] = {}, {}
        for k, n in enumerate(names):
            c, info = prob.solve(amb_value=(La == k).astype(np.float64), method="bicgstab", tol=1e-6)
            fields["tracer__" + n] = c.astype(np.float32)
            st = thermal.probe_stats(prob, c, masks["fan_intake"], weight="flux", normal=nfan)
            M["intake_air_by_vent"][n] = st.get("flux_mean", st.get("mean"))
            M["tracer_solve"][n] = {"ambient_cells": int((La == k).sum()), "iters": info.get("iters"),
                                    "res": info.get("res")}
        M["intake_air_by_vent_sum"] = sum(v for v in M["intake_air_by_vent"].values() if v is not None)
        print(f"tracers done {time.time()-t0:.0f}s", file=log)
    if "recirc" in parts:
        _recirc(M, fields, prob, dom, masks, nfan, rho, cp, Qf, log, t0)
    if "thermal" in parts:
        _thermal(M, fields, prob, dom, masks, nfan, params, fl, rho, cp, vq, prof, x0, sec_in, leg, log, t0)
    np.savez_compressed(tp, **fields)
    M["network_compare"] = network_compare(params)
    M["compute_s"] = time.time() - t0
    json.dump(M, open(mp, "w"), indent=1, default=float)
    print(f"=== done {time.time()-t0:.0f}s", file=log)


def _recirc(M, fields, prob, dom, masks, nfan, rho, cp, Qf, log, t0):
    rc, rinfo = thermal.recirculation_tracer(prob, dom, tag="fan_outlet")
    fields["recirc_tag"] = rc.astype(np.float32)
    st = thermal.probe_stats(prob, rc, masks["fan_intake"], weight="flux", normal=nfan)
    th1, _ = thermal.solve_temperature(prob, dom, {"fan": 1.0}, T_amb=0.0, rho=rho, cp=cp)
    st2 = thermal.probe_stats(prob, th1, masks["fan_intake"], weight="flux", normal=nfan)
    c_in = st2.get("flux_mean", st2.get("mean"))
    rise = 1.0 / (rho * cp * max(Qf, 1e-12))
    M["recirculation"] = {"tag_fin_exit_at_intake": st.get("flux_mean", st.get("mean")),
                          "source_method_R": c_in / (c_in + rise), "source_c_in_K_per_W": c_in,
                          "source_rise_K_per_W": rise,
                          "note": "fraction of fan intake air that has already passed through the fan"}
    age, ainfo = thermal.mean_age(prob)
    fields["age_s"] = age.astype(np.float32)
    M["mean_age_s"] = {k: thermal.probe_stats(prob, age, m).get("mean") for k, m in masks.items()
                       if k.startswith("probe__") or k == "fan_intake"}
    print(f"recirc/age done {time.time()-t0:.0f}s", file=log)


def _thermal(M, fields, prob, dom, masks, nfan, params, fl, rho, cp, vq, prof, x0, sec_in, leg, log, t0):
    import network
    fp = params["fins"]
    wl = params.get("walls", {})
    U = wl.get("U") or wl.get("U_W_m2K")
    M.setdefault("thermal", {})
    nf = prob.shell_faces(dom, 2)
    M["wall_loss_model"] = {"U_W_m2K": U, "shell_face_area_m2": float(nf.sum()) * prob.dx ** 2,
                            "params_wall_area_m2": wl.get("area_m2"), "label_legend": leg,
                            "note": "exterior = label 2 cells; shell = solid within 2 cells of it; loss = U x "
                                    "(active-cell faces on the shell) x (T_air - 30 C)"}
    for S in STATES:
        heat = {k: v for k, v in params["heat"][S].items() if isinstance(v, (int, float))}
        A_sh = M["wall_loss_model"]["shell_face_area_m2"]
        UA_net, UA_hi = wl.get("UA_W_per_K", 0.204), wl["U_range"][1] * wl["area_m2"]
        M["wall_loss_model"]["cases"] = {"wall_UA0.20": f"U_eff = {UA_net:.3f} W/K / {A_sh:.4f} m2 (same UA as "
                                         "the network model)", "wall_UA0.30": f"U_eff = {UA_hi:.3f} W/K / "
                                         f"{A_sh:.4f} m2 (params U_range high 4.5 W/m2K x body area)"}
        for case, h in (("adiabatic", None), ("wall_UA0.20", UA_net / A_sh), ("wall_UA0.30", UA_hi / A_sh)):
            T, info = thermal.solve_temperature(prob, dom, heat, T_amb=fl.get("T_amb_C", 30.0), rho=rho, cp=cp,
                                                h_ext=h)
            fields[f"T__{S}__{case}"] = T.astype(np.float32)
            r = {"heat_in_W": info["heat_in_W"], "enthalpy_out_W": info["enthalpy_out_W"],
                 "shell_loss_W": info["shell_loss_W"], "balance_rel": info["balance_rel"],
                 "not_applied": info["heat_report"]["not_applied"], "iters": info.get("iters"),
                 "res": info.get("res"), "h_ext_W_m2K": h, "probes": {}}
            for k, m in masks.items():
                if k.startswith("probe__") or k.startswith("heat__") or k == "fan_intake":
                    s_ = thermal.probe_stats(prob, T, m, weight="flux" if k == "fan_intake" else "volume",
                                             normal=nfan if k == "fan_intake" else None)
                    r["probes"][k] = {a: s_.get(a) for a in ("mean", "max", "flux_mean")}
            r["exhaust_T_by_vent_C"] = {}
            for vid in vq:
                m = masks["vent__" + vid]
                s_ = thermal.probe_stats(prob, T, m, weight="flux", normal=lbm.mask_normal(dom["meta"], "vent__" + vid))
                r["exhaust_T_by_vent_C"][vid] = {"flux_mean": s_.get("flux_mean"), "max": s_.get("max"),
                                                 "direction": "out" if vq[vid] > 0 else "in"}
            T_fin_in = flux_mean_on_face(prob, T, x0 - 1, sec_in)
            Qfin = max(prof[0], 0.0)
            out = {}
            for lvl, rjc in params["sink"]["R_jc_K_per_W"].items():
                R = network.sink_R(Qfin, fp, fp["fed_channels"], fp["height_mm"], R_jc=rjc,
                                   k_al=params["sink"]["k_fin_W_mK"]) if Qfin > 1e-9 else float("inf")
                out[lvl] = {"R_sink_K_per_W": R, "T_soc_C": T_fin_in + heat["soc"] * R}
            r["soc_estimate"] = {"T_fin_inlet_air_C": T_fin_in, "Q_fin_m3s": Qfin, "P_soc_W": heat["soc"],
                                 "by_R_jc": out, "label": "ESTIMATE"}
            M["thermal"][f"{S}__{case}"] = r
            print(f"{S} {case} done {time.time()-t0:.0f}s bal {info['balance_rel']}", file=log)


def network_compare(params):
    d = json.load(open(os.path.join(OUT, "network.json")))
    res = {}
    for c in d["cases"]:
        if c.get("curve") == "nominal" and c.get("speed") == 1.0 and c.get("kscale") == 1.0:
            key = f"{c['config']}|beta{c.get('beta')}|{c.get('out_wall_node')}"
            res[key] = {"Q_fan_m3s": c["Q_fan_m3s"], "Q_fin_m3s": c["Q_fin_m3s"],
                        "Q_bypass_m3s": c.get("Q_bypass_m3s"), "recirculation_fraction": c.get("recirculation_fraction"),
                        "Q_through_m3s": c["Q_through_m3s"], "vents": c["vents_m3s_out_positive"],
                        "S2_T_soc_C": c["thermal"]["S2"]["T_soc_est_C"], "S3_T_soc_C": c["thermal"]["S3"]["T_soc_est_C"],
                        "S2_T_body_C": c["thermal"]["S2"]["T_body_C"]}
    return res


if __name__ == "__main__":
    cmd = sys.argv[1]
    tag = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else "2.0"
    if cmd == "compute":
        parts = sys.argv[sys.argv.index("--parts") + 1].split(",") if "--parts" in sys.argv else             ("tracers", "recirc", "thermal")
        compute(tag, parts)
    elif cmd == "figs":
        import post_figs
        post_figs.figs(tag)
    elif cmd == "merge":
        import post_figs
        post_figs.merge()
