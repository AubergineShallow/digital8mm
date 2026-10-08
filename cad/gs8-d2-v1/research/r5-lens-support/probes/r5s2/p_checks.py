# r5 step 2 probe (2026-10-06): the new r5 checks on tub / hood / panel / lens_collar + COTS without the full build.
#   .venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/research/r5-lens-support/probes/r5s2/p_checks.py
import json
import os
import sys
import time

D2 = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
sys.path.insert(0, D2)
import build_d2 as B  # noqa: E402
import checks as CK  # noqa: E402
import layout as L  # noqa: E402

t0 = time.time()
prow = {}
for pid in ('tub', 'hood', 'panel', 'lens_collar'):
    prow.update(B.build_printed(only=pid)[0])
rows = dict(B.build_cots(), **prow)
print('built', round(time.time() - t0, 1), flush=True)
res = {}
collars = B.lens_collars(rows)
for nm, fn in (('inserts', lambda: CK.check_inserts(L, rows)),
               ('j7_float', lambda: CK.check_j7_float(L, rows)),
               ('lens_support', lambda: CK.check_lens_support(L, rows, collars=collars)),
               ('lens_clamp', lambda: CK.check_lens_clamp(L, rows, collars=collars)),
               ('driver_m3', lambda: CK.check_driver(L, rows, screw_ids=['s_c1', 's_c2', 's_c3', 's_c4']))):
    t1 = time.time()
    res[nm] = fn()
    print('==', nm, round(time.time() - t1, 1), 's', flush=True)
    for r in res[nm]:
        keep = {k: v for k, v in r.items() if k not in ('per_obstacle', 'nearest', 'audit_set', 'support', 'src',
                                                       'masses', 'kind')}
        print('  ', json.dumps(keep, default=str)[:420])
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'p_checks.json'), 'w', encoding='utf-8',
          newline='\n') as f:
    json.dump(res, f, indent=1, default=str)
print('total', round(time.time() - t0, 1))
