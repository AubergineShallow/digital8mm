"""Benchmark lbm.py / thermal.py on a synthetic body-like domain (af-solver).  python bench_solver.py [ncells ...]
Domain: walled box with internal obstacles, ambient buffer, two porous vents, fan actuator + fin block.
Writes out/tests/bench.json (seconds per LBM step for 1 and 4 threads, thermal seconds per iteration, CG time)."""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lbm  # noqa: E402
import thermal  # noqa: E402


def make_domain(ncells):
    """Box proportional 2.0 : 1.2 : 1.0 with ~ncells cells, dx 2 mm."""
    k = (ncells / 2.4) ** (1 / 3)
    shp = (int(round(2 * k)), int(round(1.2 * k)), int(round(k)))
    nx, ny, nz = shp
    solid = np.zeros(shp, bool)
    solid[:, 0] = solid[:, -1] = solid[:, :, 0] = solid[:, :, -1] = True
    solid[3] = True                              # left wall (x=3), ambient x<3
    solid[nx - 4] = True                         # right wall, ambient x>nx-4
    x = np.arange(nx)[:, None, None] * np.ones(shp, bool)
    y = np.arange(ny)[None, :, None] * np.ones(shp, bool)
    z = np.arange(nz)[None, None, :] * np.ones(shp, bool)
    vin = (x == 3) & (y > ny // 4) & (y < ny // 2) & (z > nz // 4) & (z < 3 * nz // 4)
    vout = (x == nx - 4) & (y > ny // 2) & (y < 3 * ny // 4) & (z > nz // 4) & (z < 3 * nz // 4)
    solid &= ~(vin | vout)
    solid |= (x > nx // 2 + 3) & (x < nx // 2 + 7) & (y < ny // 2) & (z > 2)      # board (downstream of fan)
    solid |= (x > nx // 2 + 10) & (x < nx // 2 + 16) & (y > ny // 3) & (z < nz // 2)  # component
    amb = ((x < 3) | (x > nx - 4)) & ~solid
    act = (x >= nx // 5) & (x < nx // 5 + 5) & (y > ny // 4) & (y < ny // 2) & (z > nz // 4) & (z < 3 * nz // 4)
    fins = (x >= nx // 5 + 5) & (x < nx // 5 + 12) & (y > ny // 4) & (y < ny // 2) & (z > nz // 4) & (z < 3 * nz // 4)
    box = (x >= nx // 5 - 1) & (x < nx // 5 + 13) & (y >= ny // 4) & (y <= ny // 2) & (z >= nz // 4) &         (z <= 3 * nz // 4)
    solid |= box                                 # blower housing shell around actuator + fins
    solid &= ~(act | fins)
    solid &= ~((x == nx // 5 - 1) & (y > ny // 4) & (y < ny // 2) & (z > nz // 4) & (z < 3 * nz // 4))  # intake
    solid &= ~((x == nx // 5 + 12) & (y > ny // 4) & (y < ny // 2) & (z > nz // 4) & (z < 3 * nz // 4))  # exit
    masks = {"ambient": amb, "vent__IN": vin, "vent__OUT": vout, "fan_actuator": act, "fin_block": fins,
             "fan_intake": (x == nx // 5) & act, "fan_outlet": (x == nx // 5 + 11) & fins,
             "heat__soc": fins, "heat__board": (x == nx // 2 + 7) & (y < ny // 2) & (z > 2) & ~solid}
    meta = {"masks": {"vent__IN": {"normal": [-1, 0, 0], "thickness_cells": 1},
                      "vent__OUT": {"normal": [1, 0, 0], "thickness_cells": 1},
                      "fan_intake": {"normal": [1, 0, 0]}, "fan_outlet": {"normal": [1, 0, 0]}},
            "fan_force_unit": [1, 0, 0], "fin_porous_axis": [1, 0, 0]}
    return {"dx_mm": 2.0, "origin": np.zeros(3), "solid": solid, "masks": masks, "meta": meta}


PARAMS = {"fluid": {"rho": 1.13, "nu": 1.6e-5, "cp": 1007.0, "k_air": 0.027, "T_amb_C": 30.0},
          "fan": {"curve_100": [[0.0, 100.0], [0.00026, 75.0], [0.000514, 0.0]]},
          "vents": {"IN": {"K": 8.0}, "OUT": {"K": 8.0}},
          "fins": {"K_total": 3.0}}


def bench(ncells, steps=60):
    dom = make_domain(ncells)
    out = {"shape": dom["solid"].shape, "cells": int(dom["solid"].size), "fluid": int((~dom["solid"]).sum())}
    for th in (1, 4):  # threads=1 is the default (numpy GIL contention makes 4 slower)
        s, notes = lbm.build_solver(dom, PARAMS, threads=th)
        if th == 4:
            s.chunk = 8192
        s.step(5)
        t = time.time()
        s.run(steps, mon_every=500, sample_every=5)
        out[f"lbm_s_per_step_threads{th}"] = (time.time() - t) / steps
        out["lbm_info"] = s.info()
        out["setup_notes"] = notes
        del s
    rng = np.random.default_rng(0)
    u = (0.5 * rng.standard_normal((3,) + dom["solid"].shape)) * ~dom["solid"]
    t = time.time()
    prob = thermal.Problem(dom, u)
    out["thermal_setup_s"] = time.time() - t
    out["projection"] = prob.proj
    t = time.time()
    T, info = prob.solve(source=np.where(prob.active, 1e-6, 0.0), max_iter=200, check_every=100, tol=0)
    out["thermal_s_per_iter"] = (time.time() - t) / 200
    out["ram_free_mb_after"] = lbm.free_ram_mb()
    return out


if __name__ == "__main__":
    lbm.set_low_priority()
    sizes = [int(a) for a in sys.argv[1:]] or [150000, 400000]
    res = {}
    for n in sizes:
        print("RAM free MB", lbm.free_ram_mb(), flush=True)
        r = bench(n)
        res[str(n)] = r
        print(json.dumps({k: v for k, v in r.items() if k not in ("setup_notes", "lbm_info")}, default=str), flush=True)
    os.makedirs(os.path.join(HERE, "out", "tests"), exist_ok=True)
    path = os.path.join(HERE, "out", "tests", "bench.json")
    old = json.load(open(path)) if os.path.exists(path) else {}
    old.update(res)
    json.dump(old, open(path, "w"), indent=1, default=str)
