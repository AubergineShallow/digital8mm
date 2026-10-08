"""Steps-to-converge estimate on the synthetic body-like domain of bench_solver.py (af-solver).
python bench_converge.py [ncells] [minutes]  ->  out/tests/bench_converge.json (+ .log), checkpoint in out/tests/."""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lbm  # noqa: E402
import thermal  # noqa: E402
import bench_solver as B  # noqa: E402

if __name__ == "__main__":
    lbm.set_low_priority()
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 150000
    minutes = float(sys.argv[2]) if len(sys.argv) > 2 else 20.0
    od = os.path.join(HERE, "out", "tests")
    os.makedirs(od, exist_ok=True)
    log = open(os.path.join(od, f"bench_converge_{n}.log"), "w")
    print("RAM free MB", lbm.free_ram_mb(), file=log, flush=True)
    dom = B.make_domain(n)
    s, notes = lbm.build_solver(dom, B.PARAMS, log=log)
    t0 = time.time()
    st = s.run(10 ** 6, mon_every=500, tol=2e-3, tol_q=3e-3, tol_fan=0.02, n_ok=3, deadline=t0 + 60 * minutes,
               verbose=True, log=log, checkpoint=os.path.join(od, f"bench_converge_{n}.ckpt.npz"), ckpt_every=5000)
    wall = time.time() - t0
    f = s.fields()
    res = {"cells": int(dom["solid"].size), "status": st, "steps": s.step_count, "wall_s": wall,
           "s_per_step": wall / max(s.step_count, 1), "phys_time_s": s.step_count * s.dt, "info": s.info(),
           "last": s.history[-1], "notes": notes}
    prob = thermal.Problem(dom, f["u"], rho=f["rho"], nu_t=f["nu_t"])
    res["thermal_problem"] = prob.summary()
    for m in ("bicgstab", "pseudo"):
        t = time.time()
        T, info = thermal.solve_temperature(prob, dom, {"soc": 4.0, "board": 1.0}, T_amb=30.0, tol=1e-6,
                                            max_iter=(3000 if m == "bicgstab" else 60000), method=m,
                                            deadline=time.time() + 600)
        res["thermal_" + m] = {k: info[k] for k in ("iters", "res", "converged", "heat_in_W", "enthalpy_out_W",
                                                    "balance_rel")}
        res["thermal_" + m]["wall_s"] = time.time() - t
        res["thermal_" + m]["T_max_C"] = float(np.nanmax(T))
    json.dump(res, open(os.path.join(od, f"bench_converge_{n}.json"), "w"), indent=1, default=str)
    print("DONE", st, file=log, flush=True)
