"""Order-of-magnitude stack (buoyancy) through-flow, which the isothermal LBM does not include (af-run, ESTIMATE).

Two-zone stack model: warm body air (uniform excess dT over ambient 30 C) between the roof vent (top, inlet_roof
z ~98 mm) and the low vents in parallel (out_band, out_corner, out_wall, x1203; area-weighted mid height).  Stack
pressure dp = rho g H dT / T_body; vent losses from params.json (dp = a_lin v + K 0.5 rho v|v|, v over the box
area) in series (top) + parallel (low).  Heat carried = rho cp Q dT.  No fan, no wall loss, no internal resistance.
Writes out/buoyancy.json.  .venv-cad/Scripts/python.exe cad/gs8-d2-v1/airflow/buoyancy_estimate.py
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, "params.json")))
rho, cp, g = P["fluid"]["rho"], P["fluid"].get("cp", 1007.0), 9.81
dom = np.load(os.path.join(HERE, "out", "domain-2.0.npz"))
meta = json.loads(str(dom["meta_json"]))
o, d = np.array(meta["origin_mm"]), float(dom["dx"])
zc = {}
for v in ("inlet_roof", "out_band", "out_corner", "out_wall", "x1203"):
    c = np.argwhere(dom["mask__vent__" + v])
    zc[v] = float(o[2] + c[:, 2].mean() * d)
low = ["out_band", "out_corner", "out_wall", "x1203"]
A = {v: P["vents"][v]["area_mm2"] * 1e-6 for v in zc}
z_low = sum(zc[v] * A[v] for v in low) / sum(A[v] for v in low)
H = (zc["inlet_roof"] - z_low) / 1000.0


def dp_vent(v, q):
    u = q / A[v]
    return P["vents"][v].get("a_lin_Pa_per_mps", 0.0) * u + P["vents"][v]["K"] * 0.5 * rho * u * abs(u)


def q_of_dp(v, dp):
    lo, hi = 0.0, 1e-2
    for _ in range(80):
        m = 0.5 * (lo + hi)
        lo, hi = (m, hi) if dp_vent(v, m) < dp else (lo, m)
    return 0.5 * (lo + hi)


def total_dp(q):
    # low vents in parallel at common dp_l carrying q; top vent carries q
    lo, hi = 0.0, 10.0
    for _ in range(80):
        m = 0.5 * (lo + hi)
        s = sum(q_of_dp(v, m) for v in low)
        lo, hi = (m, hi) if s < q else (lo, m)
    return dp_vent("inlet_roof", q) + 0.5 * (lo + hi)


rows = []
for dT in (5.0, 10.0, 20.0, 40.0, 60.0):
    T = 303.15 + dT
    dps = rho * g * H * dT / T
    lo, hi = 0.0, 1e-3
    for _ in range(60):
        m = 0.5 * (lo + hi)
        lo, hi = (m, hi) if total_dp(m) < dps else (lo, m)
    q = 0.5 * (lo + hi)
    rows.append({"dT_K": dT, "stack_dp_Pa": dps, "Q_m3s": q, "heat_W": rho * cp * q * dT})
res = {"label": "ESTIMATE (order of magnitude, not simulated)", "H_m": H, "z_vents_mm": zc, "z_low_mm": z_low,
       "rows": rows, "direction": "warm air leaves through the roof vent and enters through the low front/side vents "
       "(opposite to the fan-driven direction found in the network model)"}
json.dump(res, open(os.path.join(HERE, "out", "buoyancy.json"), "w"), indent=1)
for r in rows:
    print(f"dT {r['dT_K']:4.0f} K: stack {r['stack_dp_Pa']:.3f} Pa  Q {r['Q_m3s']*1e6:6.1f} cm3/s  heat {r['heat_W']:.2f} W")
print(f"H {H*1000:.0f} mm")
