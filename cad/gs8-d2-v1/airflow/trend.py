"""Print the window history of a run log (out/run-<tag>.log): step, fan Q / dp / curve, lambda, vent flows (cm3/s).
  .venv-cad/Scripts/python.exe cad/gs8-d2-v1/airflow/trend.py 2.0 [every]"""
import json
import os
import sys

tag = sys.argv[1]
every = int(sys.argv[2]) if len(sys.argv) > 2 else 4
rows = []
for line in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", f"run-{tag}.log")):
    if line.startswith('{"step"'):
        rows.append(json.loads(line.replace("NaN", "null")))
vents = [k for k in rows[-1] if k.startswith("Q_vent__")] if rows else []
print("step   fanQ_cm3s  dp   dp_curve lam   res_u  " + " ".join(v[8:16].rjust(9) for v in vents) + "  sum_out")
for i, r in enumerate(rows):
    if i % every and i != len(rows) - 1:
        continue
    vs = [r.get(v, 0) * 1e6 for v in vents]
    print(f"{r['step']:6d} {r.get('fan_Q', 0)*1e6:8.1f} {r.get('fan_dp', 0):5.1f} {r.get('fan_dp_curve', 0):6.1f} "
          f"{r.get('fan_lambda', 0):5.2f} {r.get('res_u') or 0:6.3f}  " + " ".join(f"{v:9.2f}" for v in vs) +
          f"  {sum(v for v in vs if v > 0):7.2f}")
