# r5 step 2 probe: check_inserts only (tub + lens_collar + COTS).
import json
import os
import sys
D2 = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
sys.path.insert(0, D2)
import build_d2 as B  # noqa: E402
import checks as CK  # noqa: E402
import layout as L  # noqa: E402
prow = {}
for pid in ('tub', 'lens_collar'):
    prow.update(B.build_printed(only=pid)[0])
rows = dict(B.build_cots(), **prow)
for r in CK.check_inserts(L, rows):
    print(json.dumps({k: v for k, v in r.items() if k not in ('spec', 'kind')}, default=str))
