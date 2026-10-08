"""D2 airflow study, af-run figures (matplotlib, Agg) and metrics merge.  Called through post.py figs / merge."""
import glob
import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, ListedColormap  # noqa: E402

import lbm  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
BLUE = LinearSegmentedColormap.from_list("blue", ["#f4f8fd", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
VENT_ORDER = ["inlet_roof", "x1203", "sd_slot", "out_band", "out_corner", "out_wall"]
VCOL = {v: CAT[i] for i, v in enumerate(VENT_ORDER)}
AX = "xyz"


def _load(tag):
    z = np.load(os.path.join(OUT, f"flow-{tag}.npz"))
    dom = lbm.load_domain(os.path.join(OUT, str(z["domain"])))
    th = os.path.join(OUT, f"thermal-{tag}.npz")
    t = np.load(th) if os.path.exists(th) else None
    return z, dom, t


def _centroid(m):
    idx = np.argwhere(m)
    return idx.mean(0).round().astype(int)


def planes(dom):
    mk = dom["masks"]
    fb = _centroid(mk["fin_block"])
    ev = _centroid(mk["probe__evf_board"]) if "probe__evf_board" in mk else fb
    pl = _centroid(mk["probe__exhaust_plenum"]) if "probe__exhaust_plenum" in mk else fb
    return [("z", fb[2], "z through the fins"), ("x", fb[0], "x through the cooler fins"),
            ("x", ev[0], "x through the EVF board"), ("y", pl[1], "y through the exhaust plenum")]


def _cut(arr, ax, k):
    a = AX.index(ax)
    return np.take(arr, k, axis=a)


def _extent(dom, ax):
    o, d, sh = dom["meta"]["origin_mm"] if "origin_mm" in dom["meta"] else dom["origin"], dom["dx_mm"], dom["solid"].shape
    o = np.asarray(o, float)
    ax_in = [i for i in range(3) if AX[i] != ax]
    ext = []
    for i in ax_in:
        ext += [o[i] - d / 2, o[i] + (sh[i] - 0.5) * d]
    return ext, [AX[i] for i in ax_in]


def _coord(dom, ax, k):
    o = np.asarray(dom["meta"].get("origin_mm", dom["origin"]), float)
    return o[AX.index(ax)] + k * dom["dx_mm"]


def _panel(axh, dom, field, ax, k, title, cmap, vmin, vmax, u=None, cbl=""):
    sol = _cut(dom["solid"], ax, k)
    lab = _cut(dom["label"], ax, k) if "label" in dom else None
    f = np.ma.masked_where(sol | ~np.isfinite(_cut(field, ax, k)), _cut(field, ax, k))
    ext, names = _extent(dom, ax)
    bg = np.where(sol, 1.0, np.nan)
    if lab is not None:
        ext_ = (lab == 2)
        bg = np.where(ext_, 0.0, bg)
    axh.imshow(bg.T, origin="lower", extent=ext, cmap=ListedColormap(["#ffffff", "#9a9a94"]), vmin=0, vmax=1,
               interpolation="nearest")
    norm = matplotlib.colors.LogNorm(vmin=vmin, vmax=vmax) if cbl.startswith("air speed") else         matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
    im = axh.imshow(f.T, origin="lower", extent=ext, cmap=cmap, norm=norm, interpolation="nearest")
    for v in VENT_ORDER:
        m = dom["masks"].get("vent__" + v)
        if m is not None:
            mc = _cut(m, ax, k)
            if mc.any():
                axh.contour(mc.T.astype(float), levels=[0.5], extent=ext, colors=[VCOL[v]], linewidths=1.6)
    fi = _cut(dom["masks"]["fin_block"], ax, k)
    if fi.any():
        axh.contour(fi.T.astype(float), levels=[0.5], extent=ext, colors=["#1a1a19"], linewidths=0.8,
                    linestyles="dashed")
    if u is not None:
        ia = [i for i in range(3) if AX[i] != ax]
        ua, ub = _cut(u[ia[0]], ax, k), _cut(u[ia[1]], ax, k)
        d = dom["dx_mm"]
        o = np.asarray(dom["meta"].get("origin_mm", dom["origin"]), float)
        A, B = np.meshgrid(o[ia[0]] + d * np.arange(ua.shape[0]), o[ia[1]] + d * np.arange(ua.shape[1]),
                           indexing="ij")
        s = 2
        sp = np.hypot(ua, ub)
        keep = (~_cut(dom["solid"], ax, k)) & (sp > 0.02)
        sl = (slice(None, None, s), slice(None, None, s))
        axh.quiver(A[sl][keep[sl]], B[sl][keep[sl]], (ua / np.maximum(sp, 1e-9))[sl][keep[sl]],
                   (ub / np.maximum(sp, 1e-9))[sl][keep[sl]], color="#1a1a19", scale=45, width=0.0025,
                   headwidth=3.5, alpha=0.75)
    axh.set_title(f"{title} ({ax} = {_coord(dom, ax, k):.0f} mm)", fontsize=9)
    axh.set_xlabel(f"{names[0]} mm", fontsize=8)
    axh.set_ylabel(f"{names[1]} mm", fontsize=8)
    axh.tick_params(labelsize=7)
    cb = plt.colorbar(im, ax=axh, shrink=0.8)
    cb.set_label(cbl, fontsize=8)
    cb.ax.tick_params(labelsize=7)


def _legend(fig):
    from matplotlib.lines import Line2D
    hs = [Line2D([0], [0], color=VCOL[v], lw=2, label=v) for v in VENT_ORDER if v != "sd_slot"]
    hs.append(Line2D([0], [0], color="#1a1a19", lw=1, ls="--", label="fin block"))
    hs.append(matplotlib.patches.Patch(color="#9a9a94", label="solid"))
    fig.legend(handles=hs, loc="lower center", ncol=len(hs), fontsize=8, frameon=False)


def fig_slices(tag, dom, field, name, cmap, vmin, vmax, u, cbl, sup, fd):
    pls = planes(dom)
    fig, axs = plt.subplots(2, 2, figsize=(15, 11.5))
    for axh, (ax, k, t) in zip(axs.ravel(), pls):
        _panel(axh, dom, field, ax, k, t, cmap, vmin, vmax, u=u, cbl=cbl)
    fig.suptitle(sup, fontsize=11)
    _legend(fig)
    fig.tight_layout(rect=(0, 0.04, 1, 0.96), h_pad=3.0)
    p = os.path.join(fd, name)
    fig.savefig(p, dpi=110)
    plt.close(fig)
    return p


def _trilin(u, p):
    """trilinear interpolation of u (3,nx,ny,nz) at fractional indices p (n,3)."""
    sh = np.array(u.shape[1:])
    p = np.clip(p, 0, sh - 1.001)
    i0 = np.floor(p).astype(int)
    f = p - i0
    out = np.zeros((p.shape[0], 3))
    for ox in (0, 1):
        for oy in (0, 1):
            for oz in (0, 1):
                w = (f[:, 0] if ox else 1 - f[:, 0]) * (f[:, 1] if oy else 1 - f[:, 1]) * \
                    (f[:, 2] if oz else 1 - f[:, 2])
                ii = np.minimum(i0 + np.array([ox, oy, oz]), sh - 1)
                out += w[:, None] * u[:, ii[:, 0], ii[:, 1], ii[:, 2]].T
    return out


def streamlines(dom, u, inflow_vents, nseed=40, nstep=3000, seed=1):
    """RK2 traces from random cells of each inflow vent zone (index space; u in m/s -> cells/s)."""
    rng = np.random.default_rng(seed)
    uc = u.astype(np.float64) / (dom["dx_mm"] / 1000.0)
    solid, amb = dom["solid"], dom["masks"]["ambient"]
    sh = np.array(solid.shape)
    lines = {}
    for v in inflow_vents:
        cells = np.argwhere(dom["masks"]["vent__" + v])
        pick = cells[rng.choice(len(cells), min(nseed, len(cells)), replace=False)].astype(float)
        P = pick + rng.uniform(-0.3, 0.3, pick.shape)
        tr = [P.copy()]
        alive = np.ones(len(P), bool)
        for _ in range(nstep):
            v1 = _trilin(uc, P)
            sp = np.linalg.norm(v1, axis=1)
            dt = 0.4 / np.maximum(sp, 1e-6)
            v2 = _trilin(uc, P + 0.5 * dt[:, None] * v1)
            Pn = P + dt[:, None] * v2
            ii = np.clip(np.round(Pn).astype(int), 0, sh - 1)
            stop = solid[ii[:, 0], ii[:, 1], ii[:, 2]] | amb[ii[:, 0], ii[:, 1], ii[:, 2]] | (sp < 1e-3)
            alive &= ~stop
            P = np.where(alive[:, None], Pn, P)
            tr.append(P.copy())
            if not alive.any():
                break
        lines[v] = np.stack(tr, 1)
    return lines


def fig_streamlines(tag, dom, u, vq, fd):
    inflow = [v for v in VENT_ORDER if vq.get(v, 0) < -2e-7 and "vent__" + v in dom["masks"]]
    lines = streamlines(dom, u, inflow)
    dom["masks"]["vent__fin_block"] = dom["masks"]["fin_block"]
    ex = streamlines(dom, u, ["fin_block"], nseed=30, nstep=1500, seed=2)["fin_block"]
    del dom["masks"]["vent__fin_block"]
    o = np.asarray(dom["meta"].get("origin_mm", dom["origin"]), float)
    d = dom["dx_mm"]
    fig, axs = plt.subplots(1, 2, figsize=(15, 6.5))
    body = (~dom["solid"]) & ~dom["masks"]["ambient"]
    for axh, (a, b) in zip(axs, ((0, 1), (0, 2))):
        proj = body.any(axis=3 - a - b)
        ext = [o[a] - d / 2, o[a] + (proj.shape[0] - .5) * d, o[b] - d / 2, o[b] + (proj.shape[1] - .5) * d]
        axh.imshow(np.where(proj, 1.0, np.nan).T, origin="lower", extent=ext,
                   cmap=ListedColormap(["#ecebe6"]), interpolation="nearest")
        for k in ("fan_intake", "fin_block"):
            pm = dom["masks"][k].any(axis=3 - a - b)
            axh.contour(pm.T.astype(float), levels=[0.5], extent=ext, colors=["#1a1a19"], linewidths=1.0,
                        linestyles="solid" if k == "fan_intake" else "dashed")
        for v, L in lines.items():
            for s in L:
                pts = o + s * d
                axh.plot(pts[:, a], pts[:, b], color=VCOL[v], lw=0.7, alpha=0.8)
            axh.plot([], [], color=VCOL[v], lw=2, label=f"from {v} ({-vq[v]*1e6:.1f} cm3/s in)")
        for s_ in ex:
            pts = o + s_ * d
            axh.plot(pts[:, a], pts[:, b], color="#5c5b56", lw=0.6, alpha=0.6, ls=(0, (3, 2)))
        axh.plot([], [], color="#5c5b56", lw=1.5, ls=(0, (3, 2)), label="from the fin block (exhaust), 30 seeds")
        axh.set_xlabel(f"{AX[a]} mm")
        axh.set_ylabel(f"{AX[b]} mm")
        axh.set_title(("top view (x-y)" if b == 1 else "side view (x-z)") +
                      ": traces from the inflow vents; solid = fan intake, dashed = fin block", fontsize=9)
        axh.set_aspect("equal")
    axs[0].legend(fontsize=8, loc="upper left", frameon=False)
    fig.suptitle(f"[{tag}] streamlines of the window-mean flow from each inflow vent (40 seeds each, RK2)",
                 fontsize=11)
    fig.tight_layout()
    p = os.path.join(fd, "streamlines.png")
    fig.savefig(p, dpi=110)
    plt.close(fig)
    return p


def fig_vent_bars(fd, metrics):
    rows = [(f"3D {tag}", M["vents_Q_out_positive_m3s"]) for tag, M in metrics.items()]
    nc = next(iter(metrics.values())).get("network_compare", {})
    for key in ("proxy|beta0.0|P", "covered|beta0.0|P"):
        if key in nc:
            rows.append(("network " + key.split("|")[0], nc[key]["vents"]))
    vents = [v for v in VENT_ORDER if any(v in r[1] for r in rows)]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    h = 0.8 / len(rows)
    cols = ["#2a78d6", "#86b6ef", "#1c5cab", "#eb6834", "#f2a98a", "#1baf7a"]
    for i, (name, vq) in enumerate(rows):
        y = np.arange(len(vents)) + (i - (len(rows) - 1) / 2) * h
        vals = [vq.get(v, np.nan) * 1e6 for v in vents]
        ax.barh(y, vals, height=h * 0.9, color=cols[i % len(cols)], label=name)
    ax.axvline(0, color="#1a1a19", lw=0.8)
    ax.set_yticks(np.arange(len(vents)))
    ax.set_yticklabels(vents)
    ax.invert_yaxis()
    ax.set_xlabel("vent volume flow, cm3/s (negative = inflow, positive = outflow)")
    ax.grid(axis="x", color="#e5e4de", lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(fontsize=8, frameon=False, loc="lower right")
    ax.set_title("Per-vent flow: 3D runs vs the network model (nominal fan curve, 100 % speed)", fontsize=10)
    fig.tight_layout()
    p = os.path.join(fd, "vent_flows.png")
    fig.savefig(p, dpi=110)
    plt.close(fig)
    return p


def _smooth(a, fluid, n=1):
    """display only: masked 3x3x3 box mean over fluid cells (removes the +-0.3 Pa lattice checkerboard)."""
    v = np.where(fluid, np.nan_to_num(a), 0.0)
    w = fluid.astype(float)
    sv, sw = v.copy(), w.copy()
    for ax in range(3):
        sv = sv + np.roll(sv, 1, ax) + np.roll(sv, -1, ax)
        sw = sw + np.roll(sw, 1, ax) + np.roll(sw, -1, ax)
    return np.where(fluid, sv / np.maximum(sw, 1e-9), np.nan)


def figs(tag):
    z, dom, t = _load(tag)
    dom["label"] = np.load(os.path.join(OUT, str(z["domain"])))["label"]
    fd = os.path.join(OUT, "figures", tag)
    os.makedirs(fd, exist_ok=True)
    u = z["u"].astype(np.float64)
    sp = np.sqrt((u ** 2).sum(0))
    st = str(z["status"])
    made = []
    vmax = float(np.nanpercentile(sp[~dom["solid"]], 99.5))
    made.append(fig_slices(tag, dom, sp, "speed_slices.png", BLUE, 0.01, vmax, u, "air speed m/s (log scale)",
                           f"[{tag}, {st}] window-mean air speed (log colour scale) with in-plane direction "
                           "arrows (unit length, shown where > 0.02 m/s)", fd))
    pp = _smooth(z["p"].astype(float), ~dom["solid"])
    pl = float(np.nanpercentile(np.abs(pp[~dom["solid"] & ~dom["masks"]["fan_actuator"]]), 98))
    made.append(fig_slices(tag, dom, pp, "pressure_slices.png", "RdBu_r", -pl, pl, None, "gauge pressure Pa",
                           f"[{tag}, {st}] window-mean gauge pressure, 3x3x3 fluid-cell box filter against the residual "
                           "lattice checkerboard (ambient 0; colour clipped at the 98th "
                           "percentile outside the blower, which runs to the fan pressure)", fd))
    if t is not None:
        for key in [k for k in t.files if k.startswith("T__")]:
            T = t[key].astype(float)
            Tm = float(np.nanpercentile(T[np.isfinite(T)], 99.5))
            made.append(fig_slices(tag, dom, T, f"temp_{key[3:]}.png", "Oranges", 30, Tm, None, "air T, deg C",
                                   f"[{tag}, {st}] air temperature {key[3:].replace('__', ', ')} (ambient 30 C, "
                                   "steady)", fd))
        if "recirc_tag" in t.files:
            made.append(fig_slices(tag, dom, t["recirc_tag"].astype(float), "recirc_tag.png", BLUE, 0, 1, None,
                                   "exhaust fraction", f"[{tag}] exhaust tag: fraction of local air that came "
                                   "from the fin-exit plane", fd))
        if "age_s" in t.files:
            a = t["age_s"].astype(float)
            made.append(fig_slices(tag, dom, a, "age.png", BLUE, 0, float(np.nanpercentile(a[np.isfinite(a)], 99)),
                                   None, "mean age of air, s", f"[{tag}] mean age of air since entering a vent", fd))
    mp = os.path.join(OUT, f"metrics-{tag}.json")
    vq = json.load(open(mp))["vents_Q_out_positive_m3s"] if os.path.exists(mp) else \
        {k[8:]: v for k, v in json.loads(str(z["history"]))[-1].items() if k.startswith("Q_vent__")}
    made.append(fig_streamlines(tag, dom, u, vq, fd))
    made.append(fig_history(tag, z, fd))
    print("\n".join(made))


def merge():
    metrics = {}
    for p in sorted(glob.glob(os.path.join(OUT, "metrics-*.json"))):
        metrics[os.path.basename(p)[8:-5]] = json.load(open(p))
    fd = os.path.join(OUT, "figures")
    os.makedirs(fd, exist_ok=True)
    final = {k: v for k, v in metrics.items() if "pass1" not in k}     # pass-1 = interim, kept in metrics.json only
    print(fig_vent_bars(fd, final))
    print(fig_fin_profile(fd, final))
    print(summary_md(metrics))
    notes = {
        "general": "see AIRFLOW.md for the reading; all values are ESTIMATES on proxy geometry (cots.py Active Cooler "
                   "proxy, plate fins open on top), estimated fan curve (params.fan), isothermal forced-flow LBM",
        "absolute_temperatures": "The forced-flow model carries no buoyancy and only a lumped wall loss (UA 0.20 / "
                   "0.30 W/K, or none = adiabatic). With ~2 % through-flow almost all heat must leave through the "
                   "walls, so every absolute air/SoC temperature here is set by the assumed wall loss (and by the "
                   "natural draught of out/buoyancy.json, ~35-55 cm3/s, which the model does not carry). Adiabatic "
                   "cases have no realistic steady state; read them only as 'the fan does not remove the heat'.",
        "interim": "tags containing 'pass1' are the interim 10k-step field (superseded by '2.0')",
        "partial": "runs whose status contains PARTIAL stopped at their time limit before the convergence criteria"}
    json.dump({"runs": metrics, "notes": notes},
              open(os.path.join(OUT, "metrics.json"), "w"), indent=1, default=float)


def summary_md(metrics):
    """Compact markdown summary of all runs -> out/metrics-summary.md (numbers only; reading in AIRFLOW.md)."""
    L = ["# D2 airflow 3D runs: metrics summary (af-run; ESTIMATES on proxy geometry, isothermal LBM, no buoyancy)",
         "", "| run | status | steps | fan Q cm3/s (CFM) | fan dp Pa (curve) | lambda | through-flow cm3/s (% of fan) |"
         " fin inlet Q cm3/s | fin-exit plane Q | recirc. R (source) | exhaust tag at intake |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for tag, M in metrics.items():
        f, th, rc = M["fan"], M["Q_through_m3s"], M.get("recirculation", {})
        st = M.get("history_last", {}).get("step")
        L.append(f"| {tag} | {M['status']} | {st} | {f['Q_m3s']*1e6:.0f} ({f['Q_CFM']:.2f}) | {f['dp_delivered_Pa']:.1f} "
                 f"({f['dp_curve_Pa']:.1f}) | {f['lambda']:.2f} | {th['out']*1e6:.1f} ({100*th['out']/f['Q_m3s']:.0f} %) | "
                 f"{M['fins']['Q_fin_inlet_m3s']*1e6:.0f} | {(f['Q_fin_exit_plane_m3s'] or 0)*1e6:.1f} | "
                 f"{rc.get('source_method_R', float('nan')):.3f} | {rc.get('tag_fin_exit_at_intake', float('nan')):.3f} |")
    L += ["", "| run | vent flows cm3/s (+ out) | intake air by entry vent |", "|---|---|---|"]
    for tag, M in metrics.items():
        vq = ", ".join(f"{k} {v*1e6:+.1f}" for k, v in M["vents_Q_out_positive_m3s"].items())
        ia = ", ".join(f"{k} {v:.2f}" for k, v in M.get("intake_air_by_vent", {}).items() if v is not None)
        L.append(f"| {tag} | {vq} | {ia} |")
    L += ["", "| run | case | heat in W | out via vents W | wall loss W | balance | fan intake air C | fin inlet air C |"
          " Q_fin cm3/s | R_sink nom K/W | SoC est. C (R_jc 0.6/1.0/2.4) | x1203 air max C | EVF board air mean C |"
          " USB stick air mean C | exhaust out_band C |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for tag, M in metrics.items():
        for case, r in M.get("thermal", {}).items():
            pr, se = r["probes"], r["soc_estimate"]
            g = lambda k, a="mean": (pr.get(k) or {}).get(a)  # noqa: E731
            fi = g("fan_intake", "flux_mean")
            soc = "/".join(f"{se['by_R_jc'][k]['T_soc_C']:.0f}" for k in ("low", "nominal", "high"))
            ex = (r["exhaust_T_by_vent_C"].get("out_band") or {}).get("flux_mean")
            fmt = lambda x: "-" if x is None else f"{x:.1f}"  # noqa: E731
            L.append(f"| {tag} | {case} | {r['heat_in_W']:.1f} | {r['enthalpy_out_W']:.2f} | {r['shell_loss_W']:.2f} | "
                     f"{r['balance_rel']:.1e} | {fmt(fi)} | {fmt(se['T_fin_inlet_air_C'])} | {se['Q_fin_m3s']*1e6:.0f} | "
                     f"{se['by_R_jc']['nominal']['R_sink_K_per_W']:.2f} | {soc} | {fmt(g('heat__x1203', 'max'))} | "
                     f"{fmt(g('probe__evf_board'))} | {fmt(g('probe__usb_stick'))} | {fmt(ex)} |")
    open(os.path.join(OUT, "metrics-summary.md"), "w").write("\n".join(L) + "\n")
    return "\n".join(L)


def fig_fin_profile(fd, metrics):
    """x-flux through the fin block along its length, each run (shows air leaving through the open top)."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    cols = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
    for i, (tag, M) in enumerate(metrics.items()):
        pr = np.array(M["fins"]["x_faces_flux_m3s"]) * 1e6
        dx = float(M["info"].get("dx_m", 0.002)) * 1000
        x = np.arange(len(pr)) * dx
        ax.plot(x, pr, color=cols[i % len(cols)], lw=2, marker="o", ms=4, label=f"{tag} (fan {M['fan']['Q_m3s']*1e6:.0f})")
    ax.axhline(0, color="#1a1a19", lw=0.8)
    ax.set_xlabel("distance from the fin-block inlet face along +X, mm")
    ax.set_ylabel("volume flow along +X through the fin block, cm3/s")
    ax.grid(color="#e5e4de", lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(fontsize=8, frameon=False)
    ax.set_title("Fin-block through-flow along its length (legend: fan flow, cm3/s)", fontsize=10)
    fig.tight_layout()
    p = os.path.join(fd, "fin_flow_profile.png")
    fig.savefig(p, dpi=110)
    plt.close(fig)
    return p


def fig_history(tag, z, fd):
    """convergence history of one LBM run: fan Q and dp vs the curve, vent flows, mass imbalance (window means)."""
    h = json.loads(str(z["history"]))
    st = np.array([r["step"] for r in h])
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.3))
    axs[0].plot(st, [r.get("Q_fan_intake", 0) * 1e6 for r in h], color="#2a78d6", lw=2, label="fan Q (intake), cm3/s")
    a2 = axs[0].twinx()
    a2.plot(st, [r.get("fan_dp", 0) for r in h], color="#eb6834", lw=1.5, label="fan dp delivered, Pa")
    a2.plot(st, [r.get("fan_dp_curve", 0) for r in h], color="#eb6834", lw=1, ls="--", label="fan curve dp at Q, Pa")
    axs[0].set_ylabel("fan Q, cm3/s", color="#2a78d6")
    a2.set_ylabel("fan dp, Pa", color="#eb6834")
    axs[0].set_title("fan operating point (dashed = curve at the same Q)", fontsize=9)
    cols = {"inlet_roof": "#2a78d6", "out_band": "#eda100", "out_corner": "#e87ba4", "out_wall": "#008300",
            "x1203": "#eb6834"}
    for k in [k[8:] for k in h[-1] if k.startswith("Q_vent__")]:
        axs[1].plot(st, [r.get("Q_vent__" + k, 0) * 1e6 for r in h], lw=1.8, color=cols.get(k, "#777"), label=k)
    axs[1].axhline(0, color="#1a1a19", lw=0.7)
    axs[1].set_ylabel("vent flow, cm3/s (+ = out)")
    axs[1].legend(fontsize=7, frameon=False, ncol=2)
    axs[1].set_title("per-vent flow (500-step window means)", fontsize=9)
    qin = np.array([sum(-v for k, v in r.items() if k.startswith("Q_vent__") and v < 0) for r in h])
    qout = np.array([sum(v for k, v in r.items() if k.startswith("Q_vent__") and v > 0) for r in h])
    axs[2].plot(st, qin * 1e6, color="#2a78d6", lw=1.8, label="in")
    axs[2].plot(st, qout * 1e6, color="#eb6834", lw=1.8, label="out")
    a3 = axs[2].twinx()
    a3.plot(st, 100 * np.abs(qout - qin) / np.maximum(qin, 1e-12), color="#777", lw=1, ls=":", label="|out-in|/in %")
    a3.set_ylim(0, 20)
    a3.set_ylabel("mass imbalance %, dotted", color="#777")
    axs[2].set_ylabel("through-flow, cm3/s")
    axs[2].legend(fontsize=7, frameon=False, loc="lower right")
    axs[2].set_title("through-flow in / out (vent probes)", fontsize=9)
    for a in axs:
        a.set_xlabel("LBM step")
        a.grid(color="#e5e4de", lw=0.6)
    fig.suptitle(f"[{tag}, {z['status']}] convergence history", fontsize=10)
    fig.tight_layout()
    p = os.path.join(fd, "history.png")
    fig.savefig(p, dpi=100)
    plt.close(fig)
    return p
