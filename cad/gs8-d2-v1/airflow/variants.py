"""D2 airflow study, af-variants: the same basic model (lbm.py + thermal.py, unchanged) on SUGGESTED cooling fixes.
No CAD change: the solid mask of out/domain-2.0.npz is edited in memory and saved as out/variants/domain-2.0-<V>.npz.

  V1  intake shroud: a 1-cell duct wall from the blower top (around mask__fan_intake) up to the hood roof, around the
      inlet_roof footprint -> the blower can draw only through inlet_roof.
  V2  V1 + exhaust compartment: the fin block, the space over it and the ko_exhaust plenum are walled off from the body
      (side walls, a lid just above out_corner, a floor at the fin base) -> the fin exhaust can leave only through
      out_band / out_corner / out_wall (and the out_wall rows below the fin base still open to the body).
  V3  V2 + lid directly on the fin block (pin field under a shroud): air forced along +X through the fins.

  .venv-cad/Scripts/python.exe cad/gs8-d2-v1/airflow/variants.py build
  .venv-cad/Scripts/python.exe cad/gs8-d2-v1/airflow/variants.py run V1 --flow-end 14:55 --end 15:15
  .venv-cad/Scripts/python.exe cad/gs8-d2-v1/airflow/variants.py report

Functions copied (not imported) from af-run's run_airflow.py / post.py so their later edits cannot change these runs:
scaled_params, criteria, label_ambient_by_vent, fin profile / face mean, the thermal / recirculation blocks (only the
adiabatic and wall_UA0.20 cases).  lbm.py / thermal.py / network.py are imported unchanged.
"""
import copy
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
VOUT = os.path.join(OUT, "variants")
sys.path.insert(0, HERE)
import lbm  # noqa: E402
import thermal  # noqa: E402

VARIANTS = ("V1", "V2", "V3")
STATES = ("S2", "S3")
BASE_FLOW = "flow-2.0-pass1-10k.npz"     # af-run's converged pass-1 field of the existing arrangement (init only)


def ijk(dom, m):
    w = np.where(m)
    return [(int(a.min()), int(a.max())) for a in w]


def dilate2d(m):
    o = m.copy()
    o[1:] |= m[:-1]; o[:-1] |= m[1:]; o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
    return o


def build_variant(dom, lab, V):
    """Return (solid, masks, label, info) for variant V (cumulative: V2 includes V1, V3 includes V2)."""
    solid = dom["solid"].copy()
    M = dom["masks"]
    vents = np.zeros_like(solid)
    for k, m in M.items():
        if k.startswith("vent__"):
            vents |= m
    protected = vents | M["ambient"] | np.isin(lab, (3, 4)) | M["fan_actuator"] | M["fan_intake"] | M["fin_block"]
    walls = {}
    info = {}
    nz = solid.shape[2]
    # ---- V1: intake duct
    vr = M["vent__inlet_roof"]
    kv0, kv1 = ijk(dom, vr)[2]
    ki0, ki1 = ijk(dom, M["fan_intake"])[2]
    F = vr.any(2) | M["fan_intake"].any(2)
    ring = dilate2d(F) & ~F
    kk = np.arange(nz)
    zsel = (kk >= ki0) & (kk <= kv1)
    w1 = ring[:, :, None] & zsel[None, None, :] & ~solid & ~protected
    # floor of the duct at the intake level where the footprint is not housing / intake
    fl = F[:, :, None] & (kk == ki1)[None, None, :] & ~solid & ~protected
    w1 |= fl
    walls["V1_intake_duct"] = w1
    duct = F[:, :, None] & ((kk > ki1) & (kk < kv0))[None, None, :] & ~solid
    info["V1"] = {"footprint_cells_xy": int(F.sum()), "k_intake": [ki0, ki1], "k_roof_vent": [kv0, kv1],
                  "duct_air_cells": int(duct.sum()), "wall_cells": int(w1.sum()),
                  "duct_box_mm": box_mm(dom, duct)}
    if V in ("V2", "V3"):
        fi, fj, fk = ijk(dom, M["fin_block"])
        bi0 = min(ijk(dom, M["vent__out_band"])[0][0], ijk(dom, M["vent__out_corner"])[0][0])
        jr1 = ijk(dom, M["vent__out_wall"])[1][1]
        kc1 = max(ijk(dom, M["vent__out_corner"])[2][1], ijk(dom, M["vent__out_wall"])[2][1],
                  ijk(dom, M["vent__out_band"])[2][1])
        C = np.zeros_like(solid)
        C[fi[0]:bi0, jr1 + 1:fj[1] + 1, fk[0]:kc1 + 1] = True
        shell = thermal.dilate(C) & ~C
        w2 = shell & ~solid & ~protected
        walls["V2_exhaust_compartment"] = w2
        info["V2"] = {"compartment_ijk": [[fi[0], bi0 - 1], [jr1 + 1, fj[1]], [fk[0], kc1]],
                      "compartment_box_mm": box_mm(dom, C), "compartment_air_cells": int((C & ~solid).sum()),
                      "wall_cells": int(w2.sum())}
        if V == "V3":
            lid = np.zeros_like(solid)
            lid[:, :, fk[1] + 1] = M["fin_block"].any(2)
            w3 = lid & ~solid & ~protected
            walls["V3_fin_lid"] = w3
            info["V3"] = {"lid_k": fk[1] + 1, "lid_z_mm": z_of(dom, fk[1] + 1), "wall_cells": int(w3.sum())}
    allw = np.zeros_like(solid)
    for w in walls.values():
        allw |= w
    solid2 = solid | allw
    masks2 = {k: (m & ~allw) for k, m in M.items()}
    lab2 = lab.copy()
    lab2[allw] = 11
    # leak checks: air reachable from the duct / the fins without crossing a vent or the blower interior
    through = ~solid2 & ~vents & ~M["fan_actuator"] & ~M["fan_intake"]
    if True:
        r = thermal.flood(duct & ~solid2, through)
        info["V1"]["leak_cells_duct_to_body"] = int((r & ~duct).sum())
    if V in ("V2", "V3"):
        r = thermal.flood(M["fin_block"] & ~solid2, through | M["fin_block"])
        Cair = C & ~solid2
        info["V2"]["leak_cells_compartment_to_body"] = int((r & ~Cair).sum())
        touch = {k[6:]: bool((thermal.dilate(r) & m).any()) for k, m in M.items() if k.startswith("vent__")}
        info["V2"]["vents_reached_from_fins"] = touch
    info["walls_total_cells"] = int(allw.sum())
    return solid2, masks2, lab2, walls, info


def box_mm(dom, m):
    if not m.any():
        return None
    d, o = dom["dx_mm"], dom["origin"]
    return [[round(o[a] + d * (lo - 0.5), 2), round(o[a] + d * (hi + 0.5), 2)] for a, (lo, hi) in enumerate(ijk(dom, m))]


def z_of(dom, k):
    return float(dom["origin"][2] + dom["dx_mm"] * k)


def cmd_build():
    os.makedirs(VOUT, exist_ok=True)
    src = os.path.join(OUT, "domain-2.0.npz")
    z = np.load(src)
    dom = lbm.load_domain(src)
    lab = z["label"]
    allinfo = {}
    for V in VARIANTS:
        solid2, masks2, lab2, walls, info = build_variant(dom, lab, V)
        meta = copy.deepcopy(dom["meta"])
        meta["label_legend"] = dict(meta.get("label_legend", {}), **{"11": "variant wall (SUGGESTED fix, solid)"})
        meta["variant"] = {"id": V, "info": info, "note": "af-variants: solid mask edited in memory; SUGGESTION, "
                                                          "not a CAD change"}
        out = {k: z[k] for k in z.files if not k.startswith("mask__") and k not in ("solid", "label", "meta_json")}
        out.update({"solid": solid2, "label": lab2, "meta_json": json.dumps(meta)})
        out.update({"mask__" + k: m for k, m in masks2.items()})
        for wn, w in walls.items():
            out["wall__" + wn] = w
        np.savez_compressed(os.path.join(VOUT, f"domain-2.0-{V}.npz"), **out)
        allinfo[V] = info
        slice_pngs(dom, lab2, walls, V)
        print(V, json.dumps(info))
    json.dump(allinfo, open(os.path.join(VOUT, "domain-edits.json"), "w"), indent=1)


def slice_pngs(dom, lab2, walls, V):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    d, o = dom["dx_mm"], dom["origin"]
    cols = ["#d0e4f5", "#8a8a8a", "#f2f2f2", "#a6e0e0", "#5cb85c", "#f0892a", "#d62728", "#c33bc3", "#f0d43a",
            "#7e4fb8", "#111111", "#1a1a6e"]
    cm = ListedColormap(cols)
    sl = [("y", -10.0), ("z", 27.0), ("x", -58.0), ("x", -7.0), ("y", -28.0)]
    fig, axs = plt.subplots(len(sl), 1, figsize=(9, 4.2 * len(sl)))
    for ax, (a, v) in zip(axs, sl):
        ai = "xyz".index(a)
        i = int(round((v - o[ai]) / d))
        img = np.take(lab2, i, axis=ai).astype(int)
        ax_h = [b for b in range(3) if b != ai]
        ext = [o[ax_h[0]] - d / 2, o[ax_h[0]] + d * (lab2.shape[ax_h[0]] - 0.5),
               o[ax_h[1]] - d / 2, o[ax_h[1]] + d * (lab2.shape[ax_h[1]] - 0.5)]
        ax.imshow(img.T, origin="lower", extent=ext, cmap=cm, vmin=-0.5, vmax=11.5, interpolation="nearest")
        ax.set_title(f"{V} domain edit, {a} = {o[ai] + d * i:.1f} mm (navy = suggested wall)", fontsize=9)
        ax.set_xlabel("xyz"[ax_h[0]] + " (mm)"); ax.set_ylabel("xyz"[ax_h[1]] + " (mm)")
        ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(os.path.join(VOUT, f"domain-edit-{V}.png"), dpi=80)
    plt.close(fig)


# ------------------------------------------------------------------------------------------------ flow (copied)
def scaled_params(params, meta):
    """copy of run_airflow.scaled_params: vent K referenced to the box area -> grid velocity basis."""
    p = copy.deepcopy(params)
    for vid, vm in meta.get("vents", {}).items():
        r = float(vm.get("area_ratio_discrete_to_box") or 1.0)
        vp = p["vents"].get(vid)
        if vp is None:
            continue
        vp["K_box"] = vp["K"]
        vp["K"] = float(vp["K"]) * r * r
        vp["a_lin_Pa_per_mps"] = float(vp.get("a_lin_Pa_per_mps", 0.0) or 0.0) * r
    return p


def criteria(s, curve_dp_tol=0.05, q_tol=0.01, mass_tol=0.02, vent_tol=0.05, min_steps=6000):
    """copy of run_airflow.criteria (brief: fan point on the curve within 5 %, Q steady within 1 %, vent mass balance
    within 2 %; af-run's extra: each vent Q range over the window <= 5 % of the through-flow)."""
    h = s.history
    if not h:
        return {"ok": False}
    last_step = h[-1]["step"]
    span = max(0.1 * last_step, 3000)
    win = [r for r in h if r["step"] > last_step - span]
    q = np.array([r.get("Q_fan_intake", r.get("fan_Q", 0.0)) for r in win])
    qm = float(np.mean(q))
    q_var = float((q.max() - q.min()) / max(abs(qm), 1e-12))
    r = h[-1]
    fan_err = abs(r.get("fan_dp", 0) - r.get("fan_dp_curve", 0)) / max(abs(r.get("fan_dp_curve", 0)), 1e-9)
    vq = {k[8:]: v for k, v in r.items() if k.startswith("Q_vent__")}
    qin = sum(-v for v in vq.values() if v < 0)
    qout = sum(v for v in vq.values() if v > 0)
    mass = abs(qout - qin) / max(qin, 1e-12)
    vr = {}
    for k in vq:
        a = np.array([r_.get("Q_vent__" + k, 0.0) for r_ in win])
        vr[k] = float((a.max() - a.min()) / max(qin, 1e-12))
    vent_var = max(vr.values()) if vr else 0.0
    ok = (len(win) >= 6 and q_var <= q_tol and fan_err <= curve_dp_tol and mass <= mass_tol and
          vent_var <= vent_tol and last_step >= min_steps)
    return {"ok": bool(ok), "step": last_step, "window_steps": span, "Q_intake_mean": qm, "Q_rel_range": q_var,
            "fan_dp": r.get("fan_dp"), "fan_dp_curve": r.get("fan_dp_curve"), "fan_rel_err": fan_err,
            "fan_lambda": r.get("fan_lambda"), "vent_Q": vq, "Q_in": qin, "Q_out": qout, "mass_rel": mass,
            "vent_rel_range": vr, "vent_rel_range_max": vent_var}


def hhmm(t):
    lt = time.localtime()
    h, m = (int(x) for x in t.split(":"))
    return time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, h, m, 0, 0, 0, -1))


def run_flow(V, t_end, log):
    dpath = os.path.join(VOUT, f"domain-2.0-{V}.npz")
    dom = lbm.load_domain(dpath)
    params = scaled_params(json.load(open(os.path.join(HERE, "params.json"))), dom["meta"])
    s, notes = lbm.build_solver(dom, params, speed=1.0, curve_key="curve_100", fin_model=None, log=log)
    ck = os.path.join(VOUT, f"ckpt-{V}.npz")
    if os.path.exists(ck):
        s.load(ck)
        print(f"resumed {ck} step {s.step_count}", file=log)
    else:
        z = np.load(os.path.join(OUT, BASE_FLOW))
        s.init_fields(z["u"], z["p"])
        print(f"init from {BASE_FLOW} (existing arrangement, new wall cells zeroed)", file=log)
    status, crit = "maxsteps (PARTIAL)", {}
    while True:
        st = s.run(1000, mon_every=500, sample_every=5, tol=-1.0, checkpoint=ck, ckpt_every=1000,
                   deadline=t_end, verbose=True, log=log)
        crit = criteria(s)
        print("CRIT " + json.dumps({k: v for k, v in crit.items() if k != "vent_Q"}), file=log)
        if st == "diverged":
            status = "diverged"
            break
        if crit.get("ok"):
            status = "converged"
            break
        if st == "deadline" or time.time() > t_end:
            status = "deadline (PARTIAL)"
            break
        if s.step_count >= 30000:
            break
    if status != "diverged" and time.time() < t_end + 120:
        s.run(1500, mon_every=1500, sample_every=5, tol=-1.0, verbose=True, log=log)   # longer averaging window
    crit_final = criteria(s)
    f = s.fields()
    np.savez_compressed(os.path.join(VOUT, f"flow-2.0-{V}.npz"), u=f["u"], p=f["p"], nu_t=f["nu_t"], rho=f["rho"],
                        domain=f"variants/domain-2.0-{V}.npz", history=json.dumps(s.history),
                        info=json.dumps(s.info()), notes=json.dumps(notes), status=status,
                        criteria=json.dumps(crit), criteria_final=json.dumps(crit_final))
    s.save(ck)
    print(f"=== flow {V} {status} steps {s.step_count} {time.strftime('%H:%M:%S')}", file=log)
    return status


# --------------------------------------------------------------------------------------------- post (copied)
def label_ambient_by_vent(prob, dom, lab):
    """copy of post.label_ambient_by_vent (grows each vent's label through its outside buffer)."""
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
    return np.where(prob.amb, L, -1), names


def fin_profile(prob, dom):
    fb = dom["masks"]["fin_block"]
    xs = np.where(fb.any(axis=(1, 2)))[0]
    x0, x1 = int(xs.min()), int(xs.max())
    prof = []
    for i in range(x0 - 1, x1 + 1):
        sec = fb[i + 1] if i + 1 <= x1 else fb[i]
        prof.append(float(prob.F[0][i][sec].sum()))
    return prof, x0, x1, fb[x0]


def flux_mean_on_face(prob, field, i, sec):
    f = prob.F[0][i][sec]
    up = np.where(f >= 0, field[i][sec], field[i + 1][sec])
    w = np.abs(f)
    return float((w * np.nan_to_num(up)).sum() / max(w.sum(), 1e-30))


def probe_T(prob, T, masks, nfan):
    out = {}
    for k, m in masks.items():
        if k.startswith("probe__") or k.startswith("heat__") or k == "fan_intake":
            s_ = thermal.probe_stats(prob, T, m, weight="flux" if k == "fan_intake" else "volume",
                                     normal=nfan if k == "fan_intake" else None)
            out[k] = {a: s_.get(a) for a in ("mean", "max", "flux_mean")}
    return out


def run_post(V, t_end, log):
    import network
    t0 = time.time()
    z = np.load(os.path.join(VOUT, f"flow-2.0-{V}.npz"))
    dpath = os.path.join(VOUT, f"domain-2.0-{V}.npz")
    dom = lbm.load_domain(dpath)
    lab = np.load(dpath)["label"]
    params = json.load(open(os.path.join(HERE, "params.json")))
    fl = params["fluid"]
    rho, cp = fl.get("rho", 1.13), fl.get("cp", 1007.0)
    dom["masks"]["exterior"] = (lab == 2) & dom["solid"]
    prob = thermal.Problem(dom, z["u"], rho=z["rho"], nu_t=z["nu_t"], log=log)
    hist = json.loads(str(z["history"]))
    last = hist[-1]
    masks = dom["masks"]
    nfan = lbm.mask_normal(dom["meta"], "fan_intake")
    mp, tp = os.path.join(VOUT, f"metrics-{V}.json"), os.path.join(VOUT, f"thermal-{V}.npz")
    Qf = float(last.get("Q_fan_intake", last.get("fan_Q")))
    vq = {k[8:]: float(v) for k, v in last.items() if k.startswith("Q_vent__")}
    prof, x0, x1, sec_in = fin_profile(prob, dom)
    M = {"variant": V, "status": str(z["status"]), "criteria": json.loads(str(z["criteria"])),
         "criteria_final": json.loads(str(z["criteria_final"])), "info": json.loads(str(z["info"])),
         "edits": dom["meta"].get("variant"), "problem": prob.summary(), "n_windows": len(hist),
         "steps": last["step"], "history_last": last,
         "fan": {"Q_m3s": Qf, "Q_CFM": Qf / 4.719e-4, "dp_delivered_Pa": last.get("fan_dp"),
                 "dp_curve_Pa": last.get("fan_dp_curve"), "lambda": last.get("fan_lambda"),
                 "Q_fin_exit_plane_m3s": last.get("Q_fan_outlet")},
         "vents_Q_out_positive_m3s": vq,
         "Q_through_m3s": {"in": sum(-v for v in vq.values() if v < 0), "out": sum(v for v in vq.values() if v > 0)},
         "fins": {"x_faces_flux_m3s": prof, "Q_fin_inlet_m3s": prof[0], "Q_fin_exit_face_m3s": prof[-1]},
         "thermal": {}, "parts_done": [], "label": "COMPUTED by the basic model (proxy geometry, estimated fan "
                                                   "curve, estimated loads); SoC = ESTIMATE"}
    M["through_fraction"] = M["Q_through_m3s"]["in"] / max(Qf, 1e-12)
    p = z["p"]
    M["vent_p_inside_Pa"] = {}
    for vid in vq:
        vm = masks["vent__" + vid]
        mm = thermal.dilate(vm) & prob.active & ~vm & ~np.isin(lab, (3, 4))
        if mm.any():
            M["vent_p_inside_Pa"][vid] = float(p[mm].mean())
    fields = {}

    def save():
        M["compute_s"] = time.time() - t0
        json.dump(M, open(mp, "w"), indent=1, default=float)
        np.savez_compressed(tp, **fields)

    save()
    wl = params["walls"]
    A_sh = float(prob.shell_faces(dom, 2).sum()) * prob.dx ** 2
    UA = wl.get("UA_W_per_K", 0.204)
    M["wall_loss_model"] = {"shell_face_area_m2": A_sh, "UA_W_per_K": UA, "U_eff_W_m2K": UA / A_sh,
                            "note": "same as af-run 'wall_UA0.20': U_eff = UA(network) / air-cell shell face area"}
    fp = params["fins"]
    for S in STATES:
        heat = {k: v for k, v in params["heat"][S].items() if isinstance(v, (int, float))}
        for case, h in (("wall_UA0.20", UA / A_sh), ("adiabatic", None)):
            if time.time() > t_end:
                M.setdefault("skipped", []).append(f"{S}__{case} (deadline)")
                continue
            T, info = thermal.solve_temperature(prob, dom, heat, T_amb=fl.get("T_amb_C", 30.0), rho=rho, cp=cp,
                                                h_ext=h, deadline=t_end)
            fields[f"T__{S}__{case}"] = T.astype(np.float32)
            r = {"heat_in_W": info["heat_in_W"], "enthalpy_out_W": info["enthalpy_out_W"],
                 "shell_loss_W": info["shell_loss_W"], "balance_rel": info["balance_rel"],
                 "not_applied": info["heat_report"]["not_applied"], "iters": info.get("iters"),
                 "res": info.get("res"), "h_ext_W_m2K": h, "probes": probe_T(prob, T, masks, nfan)}
            r["exhaust_T_by_vent_C"] = {}
            for vid in vq:
                s_ = thermal.probe_stats(prob, T, masks["vent__" + vid], weight="flux",
                                         normal=lbm.mask_normal(dom["meta"], "vent__" + vid))
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
            M["parts_done"].append(f"{S}__{case}")
            print(f"{V} {S} {case} {time.time()-t0:.0f}s bal {info['balance_rel']} res {info.get('res')}", file=log)
            save()
    if time.time() < t_end:
        rc, _ = thermal.recirculation_tracer(prob, dom, tag="fan_outlet", deadline=t_end)
        fields["recirc_tag"] = rc.astype(np.float32)
        st = thermal.probe_stats(prob, rc, masks["fan_intake"], weight="flux", normal=nfan)
        th1, _ = thermal.solve_temperature(prob, dom, {"fan": 1.0}, T_amb=0.0, rho=rho, cp=cp, deadline=t_end)
        st2 = thermal.probe_stats(prob, th1, masks["fan_intake"], weight="flux", normal=nfan)
        c_in = st2.get("flux_mean", st2.get("mean"))
        rise = 1.0 / (rho * cp * max(Qf, 1e-12))
        M["recirculation"] = {"tag_fin_exit_at_intake": st.get("flux_mean", st.get("mean")),
                              "source_method_R": c_in / (c_in + rise), "source_c_in_K_per_W": c_in,
                              "source_rise_K_per_W": rise}
        M["parts_done"].append("recirc")
        save()
    if time.time() < t_end:
        age, _ = thermal.mean_age(prob, deadline=t_end)
        fields["age_s"] = age.astype(np.float32)
        body = prob.active & ~masks["fan_actuator"]
        M["mean_age_s"] = {k: thermal.probe_stats(prob, age, m).get("mean") for k, m in masks.items()
                           if k.startswith("probe__") or k == "fan_intake"}
        M["mean_age_s"]["interior_air"] = thermal.probe_stats(prob, age, body).get("mean")
        M["parts_done"].append("age")
        save()
    if time.time() < t_end:
        La, names = label_ambient_by_vent(prob, dom, lab)
        M["intake_air_by_vent"] = {}
        for k, n in enumerate(names):
            if time.time() > t_end:
                break
            c, _ = prob.solve(amb_value=(La == k).astype(np.float64), method="bicgstab", tol=1e-6, deadline=t_end)
            st = thermal.probe_stats(prob, c, masks["fan_intake"], weight="flux", normal=nfan)
            M["intake_air_by_vent"][n] = st.get("flux_mean", st.get("mean"))
        M["parts_done"].append("tracers")
        save()
    print(f"=== post {V} done {time.time()-t0:.0f}s {time.strftime('%H:%M:%S')}", file=log)


def cmd_run(V, flow_end, end):
    lbm.set_low_priority()
    log = open(os.path.join(VOUT, f"run-{V}.log"), "a", buffering=1)
    print(f"=== {time.strftime('%Y-%m-%d %H:%M:%S')} {V} flow_end {flow_end} end {end}", file=log)
    while lbm.free_ram_mb() < 1200:
        print(f"waiting for RAM: {lbm.free_ram_mb():.0f} MB", file=log)
        if time.time() > hhmm(flow_end):
            print(f"VARIANT_FAILED {V}: no RAM before the flow deadline", file=log)
            return
        time.sleep(20)
    try:
        if not os.path.exists(os.path.join(VOUT, f"flow-2.0-{V}.npz")):
            run_flow(V, hhmm(flow_end), log)
        run_post(V, hhmm(end), log)
        print(f"VARIANT_DONE {V}", file=log)
    except Exception as e:  # noqa: BLE001
        import traceback
        traceback.print_exc(file=log)
        print(f"VARIANT_FAILED {V} {e!r}", file=log)


# ------------------------------------------------------------------------------------------------------ report
PROBES = [("fan_intake", "fan intake air (flux mean)", "flux_mean"), ("probe__fin_exit", "fin exit air", "mean"),
          ("probe__evf_board", "EVF board air", "mean"), ("probe__x1203_ic", "X1203 air", "mean"),
          ("probe__camera", "camera air", "mean"), ("probe__usb_stick", "USB stick air", "mean"),
          ("probe__pi_board", "Pi board air", "mean")]


def base_metrics():
    for name, flow in (("metrics-2.0.json", "flow-2.0.npz"), ("metrics-2.0-pass1-10k.json", "flow-2.0-pass1-10k.npz")):
        pth = os.path.join(OUT, name)
        if os.path.exists(pth):
            m = json.load(open(pth))
            if m.get("thermal"):
                return m, name, flow
    return None, None, None


def summarize(m, params):
    if m is None:
        return None
    r = {"fan_Q_cm3s": m["fan"]["Q_m3s"] * 1e6, "fan_dp_Pa": m["fan"]["dp_delivered_Pa"],
         "fan_dp_curve_Pa": m["fan"]["dp_curve_Pa"], "fan_lambda": m["fan"].get("lambda"),
         "Q_through_in_cm3s": m["Q_through_m3s"]["in"] * 1e6, "Q_through_out_cm3s": m["Q_through_m3s"]["out"] * 1e6,
         "Q_fin_inlet_cm3s": m.get("fins", {}).get("Q_fin_inlet_m3s", 0) * 1e6,
         "Q_fin_exit_face_cm3s": m.get("fins", {}).get("Q_fin_exit_face_m3s", 0) * 1e6,
         "vents_cm3s_out_positive": {k: v * 1e6 for k, v in m["vents_Q_out_positive_m3s"].items()},
         "status": m.get("status"), "steps": m.get("steps", (m.get("history_last") or {}).get("step"))}
    r["through_fraction"] = r["Q_through_in_cm3s"] / max(r["fan_Q_cm3s"], 1e-9)
    q = m["Q_through_m3s"]
    r["mass_balance_rel"] = abs(q["out"] - q["in"]) / max(q["in"], 1e-15)
    rc = m.get("recirculation") or {}
    r["recirculation_R_source"] = rc.get("source_method_R")
    r["recirculation_tag_fin_exit"] = rc.get("tag_fin_exit_at_intake")
    ag = m.get("mean_age_s") or {}
    r["mean_age_s"] = {k: ag.get(k) for k in ("interior_air", "fan_intake", "probe__evf_board", "probe__camera",
                                              "probe__x1203_ic", "probe__usb_stick") if k in ag}
    r["intake_air_by_vent"] = m.get("intake_air_by_vent")
    r["thermal"] = {}
    for key, t in (m.get("thermal") or {}).items():
        pr = t.get("probes", {})
        e = {lab: (pr.get(k) or {}).get(w) for k, lab, w in PROBES}
        se = t.get("soc_estimate", {})
        e["T_fin_inlet_air_C"] = se.get("T_fin_inlet_air_C")
        e["T_soc_est_C"] = {lv: v.get("T_soc_C") for lv, v in se.get("by_R_jc", {}).items()}
        e["R_sink_K_per_W"] = {lv: v.get("R_sink_K_per_W") for lv, v in se.get("by_R_jc", {}).items()}
        e["energy_balance_rel"] = t.get("balance_rel")
        e["res"] = t.get("res")
        e["G_W11_pass_SoC_lt_80_nominal"] = (e["T_soc_est_C"].get("nominal") or 1e9) < 80.0
        e["G_W11_pass_SoC_lt_80_high"] = (e["T_soc_est_C"].get("high") or 1e9) < 80.0
        e["X1203_air_lt_70"] = (e.get("X1203 air") or 1e9) < 70.0
        r["thermal"][key] = e
    return r


def vent_dp(params, vid, q_m3s):
    """forced pressure drop over a vent from the params loss law at flow q (box face velocity)."""
    vp = params["vents"][vid]
    a = vp.get("area_mm2") or vp.get("face_area_mm2")
    v = abs(q_m3s) / (a * 1e-6) if a else 0.0
    rho = params["fluid"].get("rho", 1.13)
    return float((vp.get("a_lin_Pa_per_mps", 0.0) or 0.0) * v + vp["K"] * 0.5 * rho * v * v)


def cmd_report():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    params = json.load(open(os.path.join(HERE, "params.json")))
    bm, bname, bflow = base_metrics()
    rows = {"existing": summarize(bm, params)}
    rawv = {}
    for V in VARIANTS:
        pth = os.path.join(VOUT, f"metrics-{V}.json")
        rawv[V] = json.load(open(pth)) if os.path.exists(pth) else None
        rows[V] = summarize(rawv[V], params)
        if rows[V]:
            rows[V]["parts_done"] = rawv[V].get("parts_done")
            rows[V]["criteria_final"] = {k: v for k, v in rawv[V].get("criteria_final", {}).items() if k != "vent_Q"}
            rows[V]["vent_p_inside_Pa"] = rawv[V].get("vent_p_inside_Pa")
    # buoyancy hand estimate (ESTIMATE): stack between the roof inlet (z ~97) and the low outlets (z ~30)
    g, Tabs, rho = 9.81, 303.15, params["fluid"].get("rho", 1.13)
    H = (97.0 - 30.0) / 1000.0
    buoy = {"H_m": H, "basis": "dp_stack = rho g H dT / T_abs (ESTIMATE, not simulated; the LBM has no buoyancy)",
            "dp_stack_Pa_by_dT": {str(dT): rho * g * H * dT / Tabs for dT in (5, 10, 20, 40)}, "forced": {}}
    for k, r in rows.items():
        if not r:
            continue
        fd = {vid: vent_dp(params, vid, q * 1e-6) for vid, q in r["vents_cm3s_out_positive"].items()}
        buoy["forced"][k] = {"vent_dp_from_loss_law_Pa": fd, "max_vent_dp_Pa": max(fd.values()) if fd else None}
        t = r["thermal"].get("S2__wall_UA0.20") or {}
        if t.get("fan intake air (flux mean)") is not None:
            dT = (t.get("EVF board air") or 30) - 30.0
            buoy["forced"][k]["S2_wall_body_dT_K(EVF air)"] = dT
            buoy["forced"][k]["stack_dp_at_that_dT_Pa"] = rho * g * H * dT / Tabs
    res = {"label": "COMPUTED by the basic voxel LBM + steady advection-diffusion model (proxy geometry, ESTIMATED fan "
                    "curve and loads); SoC temperature = ESTIMATE (fin-inlet air + P_soc x R_sink(Q_fin)); "
                    "buoyancy = hand ESTIMATE",
           "existing_source": f"out/{bname} (af-run)" if bname else None, "rows": rows, "buoyancy": buoy,
           "edits": json.load(open(os.path.join(VOUT, "domain-edits.json"))),
           "made": time.strftime("%Y-%m-%d %H:%M:%S")}
    json.dump(res, open(os.path.join(VOUT, "metrics-variants.json"), "w"), indent=1, default=float)
    # ---- velocity slices, same colour scale
    flows = [("existing", os.path.join(OUT, bflow) if bflow else None, os.path.join(OUT, "domain-2.0.npz"))]
    flows += [(V, os.path.join(VOUT, f"flow-2.0-{V}.npz"), os.path.join(VOUT, f"domain-2.0-{V}.npz")) for V in VARIANTS]
    flows = [f for f in flows if f[1] and os.path.exists(f[1])]
    d0 = np.load(os.path.join(OUT, "domain-2.0.npz"))
    dx, o = float(d0["dx"]), d0["origin"]
    vmax = 3.0
    for a, val in (("y", -11.0), ("z", 27.0)):
        ai = "xyz".index(a)
        i = int(round((val - o[ai]) / dx))
        fig, axs = plt.subplots(len(flows), 1, figsize=(8, 3.3 * len(flows)) if a == "y" else (8, 2.6 * len(flows)))
        axs = np.atleast_1d(axs)
        for ax, (nm, fp_, dp_) in zip(axs, flows):
            u = np.load(fp_)["u"].astype(np.float64)
            sol = np.load(dp_)["solid"].astype(bool)
            sp = np.sqrt((u ** 2).sum(0))
            img = np.ma.masked_where(np.take(sol, i, axis=ai), np.take(sp, i, axis=ai))
            hb = [b for b in range(3) if b != ai]
            ext = [o[hb[0]] - dx / 2, o[hb[0]] + dx * (sol.shape[hb[0]] - 0.5), o[hb[1]] - dx / 2,
                   o[hb[1]] + dx * (sol.shape[hb[1]] - 0.5)]
            cmap = plt.get_cmap("viridis").copy()
            cmap.set_bad("#9a9a9a")
            im = ax.imshow(img.T, origin="lower", extent=ext, cmap=cmap, vmin=0, vmax=vmax, interpolation="nearest")
            ax.set_title(f"{nm}: |u| (window mean), {a} = {o[ai] + dx * i:.0f} mm; grey = solid", fontsize=9)
            ax.set_xlabel("xyz"[hb[0]] + " (mm)"); ax.set_ylabel("xyz"[hb[1]] + " (mm)")
            ax.set_aspect("equal")
            fig.colorbar(im, ax=ax, label="m/s (clipped at 3)", shrink=0.85)
        fig.tight_layout()
        fig.savefig(os.path.join(VOUT, f"velocity-{a}{val:g}.png"), dpi=85)
        plt.close(fig)
    # ---- bar chart: through-flow and SoC estimate
    names = [k for k in rows if rows[k]]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    tf = [rows[k]["Q_through_in_cm3s"] for k in names]
    fq = [rows[k]["fan_Q_cm3s"] for k in names]
    x = np.arange(len(names))
    a1.bar(x - 0.2, fq, 0.4, color="#9aa7b8", label="fan flow")
    a1.bar(x + 0.2, tf, 0.4, color="#2a6db0", label="through-flow (vents)")
    for xi, t_, f_ in zip(x, tf, fq):
        a1.text(xi + 0.2, t_ + 5, f"{t_:.0f}\n({100 * t_ / max(f_, 1e-9):.0f} %)", ha="center", fontsize=8)
    a1.set_xticks(x, names); a1.set_ylabel("cm3/s"); a1.set_title("Fan flow and through-flow (computed)", fontsize=10)
    a1.legend(fontsize=8, frameon=False)
    for sp_ in ("top", "right"):
        a1.spines[sp_].set_visible(False); a2.spines[sp_].set_visible(False)
    cases = [("S2__wall_UA0.20", "S2 wall loss", "#2a6db0"), ("S3__wall_UA0.20", "S3 wall loss", "#c4502a"),
             ("S2__adiabatic", "S2 adiabatic", "#8fb5dd"), ("S3__adiabatic", "S3 adiabatic", "#e8a088")]
    wdt = 0.2
    for ci, (ck, lab_, col) in enumerate(cases):
        vals = []
        for k in names:
            t = rows[k]["thermal"].get(ck) or {}
            vals.append((t.get("T_soc_est_C") or {}).get("nominal") or np.nan)
        vv = np.clip(np.array(vals, float), 0, 200)
        a2.bar(x + (ci - 1.5) * wdt, vv, wdt, color=col, label=lab_)
        for xi, v, v0 in zip(x, vv, vals):
            if np.isfinite(v0):
                a2.text(xi + (ci - 1.5) * wdt, v + 2, f"{v0:.0f}", ha="center", fontsize=7, rotation=90)
    a2.axhline(80, color="#333333", lw=1, ls="--")
    a2.text(len(names) - 0.5, 82, "G-W11 SoC 80 C", fontsize=8, ha="right")
    a2.set_ylim(0, 200)
    a2.set_xticks(x, names); a2.set_ylabel("deg C (bars clipped at 200)")
    a2.set_title("SoC ESTIMATE, R_jc nominal, 30 C ambient", fontsize=10)
    a2.legend(fontsize=7, frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(os.path.join(VOUT, "compare-throughflow-soc.png"), dpi=90)
    plt.close(fig)
    print(json.dumps({k: (None if not r else {"Q": r["fan_Q_cm3s"], "dp": r["fan_dp_Pa"], "thr": r["Q_through_in_cm3s"],
                                              "frac": r["through_fraction"], "R": r["recirculation_R_source"]})
                      for k, r in rows.items()}, default=float))


# ------------------------------------------------------------------------------------------- md tables (14:20)
def _f(x, fmt="{:.0f}"):
    try:
        if x is None or not np.isfinite(float(x)):
            return "n/a"
        return fmt.format(float(x))
    except (TypeError, ValueError):
        return "n/a"


def _tcase(r, S, case):
    """thermal entry of a row; the existing pass-1 metrics only have 'wall_loss' (UA 0.095 W/K): flagged."""
    t = r["thermal"].get(f"{S}__{case}")
    if t is None and case == "wall_UA0.20" and r["thermal"].get(f"{S}__wall_loss"):
        return r["thermal"][f"{S}__wall_loss"], " (UA 0.095)"
    return t, ""


def cmd_md():
    """writes out/variants/VARIANTS-tables.md from metrics-variants.json (tables only; VARIANTS.md embeds them)."""
    res = json.load(open(os.path.join(VOUT, "metrics-variants.json")))
    rows = {k: v for k, v in res["rows"].items() if v}
    L = []
    names = list(rows)
    L.append("| quantity | " + " | ".join(names) + " |")
    L.append("|---|" + "---|" * len(names))

    def row(lab, fn):
        L.append(f"| {lab} | " + " | ".join(fn(rows[k]) for k in names) + " |")
    row("run status / steps", lambda r: f"{r.get('status')} / {r.get('steps')}")
    row("fan Q (cm3/s) [CFM]", lambda r: f"{_f(r['fan_Q_cm3s'])} [{_f(r['fan_Q_cm3s'] / 471.9, '{:.2f}')}]")
    row("fan dp delivered / on curve (Pa)", lambda r: f"{_f(r['fan_dp_Pa'], '{:.1f}')} / {_f(r['fan_dp_curve_Pa'], '{:.1f}')}")
    row("through-flow in / out (cm3/s)", lambda r: f"{_f(r['Q_through_in_cm3s'], '{:.1f}')} / {_f(r['Q_through_out_cm3s'], '{:.1f}')}")
    row("through-flow / fan flow", lambda r: _f(100 * r["through_fraction"], "{:.0f} %"))
    row("mass balance (out-in)/in", lambda r: _f(100 * r["mass_balance_rel"], "{:.1f} %"))
    row("fin inlet / fin exit face flow (cm3/s)", lambda r: f"{_f(r['Q_fin_inlet_cm3s'])} / {_f(r['Q_fin_exit_face_cm3s'])}")
    row("recirculation R (fan-heat source method)", lambda r: _f(r.get("recirculation_R_source"), "{:.3f}"))
    row("fin-exit tag at fan intake", lambda r: _f(r.get("recirculation_tag_fin_exit"), "{:.3f}"))
    row("mean age interior air / fan intake (s)", lambda r: f"{_f((r.get('mean_age_s') or {}).get('interior_air'), '{:.1f}')} / {_f((r.get('mean_age_s') or {}).get('fan_intake'), '{:.1f}')}")
    vids = sorted({v for r in rows.values() for v in r["vents_cm3s_out_positive"]})
    for v in vids:
        row(f"vent {v} (cm3/s, + = out)", lambda r, v=v: _f(r["vents_cm3s_out_positive"].get(v), "{:+.1f}"))
    for v in vids:
        row(f"fan intake air from {v}", lambda r, v=v: _f((r.get("intake_air_by_vent") or {}).get(v), "{:.2f}"))
    L.append("")
    for S in STATES:
        for case in ("wall_UA0.20", "adiabatic"):
            L.append(f"**{S}, {'wall loss UA 0.20 W/K' if case != 'adiabatic' else 'adiabatic walls'}** "
                     "(air temperatures COMPUTED, deg C; SoC = ESTIMATE)")
            L.append("")
            L.append("| quantity | " + " | ".join(names) + " |")
            L.append("|---|" + "---|" * len(names))
            for _k, lab, _w in PROBES:
                row(lab, lambda r, lab=lab: (lambda t: _f(t[0].get(lab)) + t[1] if t[0] else "n/a")(_tcase(r, S, case)))
            row("fin inlet air", lambda r: (lambda t: _f(t[0].get("T_fin_inlet_air_C")) if t[0] else "n/a")(_tcase(r, S, case)))
            row("R_sink nominal (K/W)", lambda r: (lambda t: _f((t[0].get("R_sink_K_per_W") or {}).get("nominal"), "{:.1f}") if t[0] else "n/a")(_tcase(r, S, case)))
            for lv in ("low", "nominal", "high"):
                row(f"SoC ESTIMATE, R_jc {lv}", lambda r, lv=lv: (lambda t: _f((t[0].get("T_soc_est_C") or {}).get(lv)) if t[0] else "n/a")(_tcase(r, S, case)))
            row("G-W11 SoC < 80 (nominal / high R_jc)", lambda r: (lambda t: ("pass" if t[0]["G_W11_pass_SoC_lt_80_nominal"] else "FAIL") + " / " + ("pass" if t[0]["G_W11_pass_SoC_lt_80_high"] else "FAIL") if t[0] else "n/a")(_tcase(r, S, case)))
            row("X1203 air < 70", lambda r: (lambda t: ("pass" if t[0]["X1203_air_lt_70"] else "FAIL") if t[0] else "n/a")(_tcase(r, S, case)))
            row("energy balance (rel)", lambda r: (lambda t: _f(t[0].get("energy_balance_rel"), "{:.0e}") if t[0] else "n/a")(_tcase(r, S, case)))
            # ---- fin flow along the length and the SoC ESTIMATE on the length-mean fin flow (sensitivity, same sink law)
    import network
    params = json.load(open(os.path.join(HERE, "params.json")))
    fp = params["fins"]
    raw = {}
    for k in names:
        if k == "existing":
            pth = os.path.join(OUT, str(res.get("existing_source", "")).split()[0].replace("out/", ""))
        else:
            pth = os.path.join(VOUT, f"metrics-{k}.json")
        raw[k] = json.load(open(pth)) if os.path.exists(pth) else {}
    qlen = {}
    for k in names:
        prof = np.array((raw[k].get("fins") or {}).get("x_faces_flux_m3s") or [np.nan])
        qlen[k] = (float(np.clip(prof, 0, None).mean()), float(prof[len(prof) // 2]))
    L.append("**Fin flow along the fin block** (COMPUTED x-flux through the fin section) and the SoC ESTIMATE on the "
             "length-mean fin flow (same sink law as af-run, which uses the fin INLET flow; air that leaves the open "
             "top early does not wash the whole fin length, so the inlet basis is optimistic)")
    L.append("")
    L.append("| quantity | " + " | ".join(names) + " |")
    L.append("|---|" + "---|" * len(names))
    L.append("| fin flow at mid-length (cm3/s) | " + " | ".join(_f(1e6 * qlen[k][1]) for k in names) + " |")
    L.append("| length-mean fin flow, negatives as 0 (cm3/s) | " + " | ".join(_f(1e6 * qlen[k][0]) for k in names) + " |")
    socl = {}
    for S in STATES:
        for case in ("wall_UA0.20", "adiabatic"):
            cells = []
            for k in names:
                t, flag = _tcase(rows[k], S, case)
                tin = t.get("T_fin_inlet_air_C") if t else None
                vals = []
                for lv in ("nominal", "high"):
                    rjc = params["sink"]["R_jc_K_per_W"][lv]
                    R = network.sink_R(qlen[k][0], fp, fp["fed_channels"], fp["height_mm"], R_jc=rjc,
                                       k_al=params["sink"]["k_fin_W_mK"]) if qlen[k][0] > 1e-9 else float("inf")
                    vals.append(None if tin is None else tin + params["heat"][S]["soc"] * R)
                socl[f"{k}|{S}|{case}"] = vals
                cells.append(f"{_f(vals[0])} / {_f(vals[1])}{flag}")
            L.append(f"| SoC ESTIMATE length-mean basis, {S} {case} (R_jc nominal / high) | " + " | ".join(cells) + " |")
    json.dump({"fin_flow_length_mean_and_mid_m3s": qlen, "soc_length_mean_basis_C_nominal_high": socl,
               "label": "ESTIMATE (sensitivity of the SoC estimate to the fin-flow basis)"},
              open(os.path.join(VOUT, "soc-length-basis.json"), "w"), indent=1)
    L.append("")
    b = res.get("buoyancy", {})
    L.append("**Buoyancy hand ESTIMATE** (not simulated; the LBM has no buoyancy): stack dp = rho g H dT / T_abs, "
             f"H {_f(1000 * b.get('H_m', 0), '{:.0f}')} mm: " + ", ".join(
                 f"dT {k} K -> {_f(v, '{:.3f}')} Pa" for k, v in (b.get("dp_stack_Pa_by_dT") or {}).items()))
    L.append("")
    L.append("| case | largest forced vent dp from the loss law (Pa) | S2 wall-case body air rise at the EVF (K) | stack dp at that rise (Pa) |")
    L.append("|---|---|---|---|")
    for k, fd in (b.get("forced") or {}).items():
        L.append(f"| {k} | {_f(fd.get('max_vent_dp_Pa'), '{:.3f}')} | {_f(fd.get('S2_wall_body_dT_K(EVF air)'), '{:.0f}')} | "
                 f"{_f(fd.get('stack_dp_at_that_dT_Pa'), '{:.3f}')} |")
    L.append("")
    L.append(f"Source of the existing-arrangement column: {res.get('existing_source')}; tables made {res.get('made')}.")
    # ---- temperature slices (S2 wall case, y = -11 and z = 27), same colour scale
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        ex = str(res.get("existing_source", "")).split()[0].replace("out/metrics-", "thermal-").replace(".json", ".npz")
        sets = [("existing", os.path.join(OUT, ex), os.path.join(OUT, "domain-2.0.npz"))]
        sets += [(V, os.path.join(VOUT, f"thermal-{V}.npz"), os.path.join(VOUT, f"domain-2.0-{V}.npz")) for V in VARIANTS]
        sets = [s_ for s_ in sets if os.path.exists(s_[1])]
        d0 = np.load(os.path.join(OUT, "domain-2.0.npz"))
        dx, o = float(d0["dx"]), d0["origin"]
        for a, val in (("y", -11.0), ("z", 27.0)):
            ai = "xyz".index(a)
            i = int(round((val - o[ai]) / dx))
            fig, axs = plt.subplots(len(sets), 1, figsize=(8, 3.3 * len(sets)) if a == "y" else (8, 2.6 * len(sets)))
            axs = np.atleast_1d(axs)
            for ax, (nm, tp_, dp_) in zip(axs, sets):
                z = np.load(tp_)
                key = "T__S2__wall_UA0.20" if "T__S2__wall_UA0.20" in z.files else "T__S2__wall_loss"
                if key not in z.files:
                    ax.set_title(f"{nm}: no S2 wall-case field"); continue
                T = z[key].astype(np.float64)
                sol = np.load(dp_)["solid"].astype(bool)
                img = np.ma.masked_where(np.take(sol, i, axis=ai) | ~np.isfinite(np.take(T, i, axis=ai)), np.take(T, i, axis=ai))
                hb = [b_ for b_ in range(3) if b_ != ai]
                ext = [o[hb[0]] - dx / 2, o[hb[0]] + dx * (sol.shape[hb[0]] - 0.5), o[hb[1]] - dx / 2,
                       o[hb[1]] + dx * (sol.shape[hb[1]] - 0.5)]
                cmap = plt.get_cmap("inferno").copy()
                cmap.set_bad("#9a9a9a")
                im = ax.imshow(img.T, origin="lower", extent=ext, cmap=cmap, vmin=30, vmax=130, interpolation="nearest")
                ax.set_title(f"{nm}: air T, S2, wall loss ({key[7:]}), {a} = {o[ai] + dx * i:.0f} mm", fontsize=9)
                ax.set_xlabel("xyz"[hb[0]] + " (mm)"); ax.set_ylabel("xyz"[hb[1]] + " (mm)")
                ax.set_aspect("equal")
                fig.colorbar(im, ax=ax, label="deg C (clipped 30-130)", shrink=0.85)
            fig.tight_layout()
            fig.savefig(os.path.join(VOUT, f"temperature-S2wall-{a}{val:g}.png"), dpi=85)
            plt.close(fig)
    except Exception as e:  # noqa: BLE001
        print(f"temperature figure skipped: {e!r}")
    open(os.path.join(VOUT, "VARIANTS-tables.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "md":
        cmd_md()
        sys.exit(0)
    if c == "build":
        cmd_build()
    elif c == "run":
        a = sys.argv
        cmd_run(a[2], a[a.index("--flow-end") + 1], a[a.index("--end") + 1])
    elif c == "report":
        cmd_report()
