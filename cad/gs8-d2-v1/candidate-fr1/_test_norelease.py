"""Quick test of checks._no_release_row (tub only). Run through the CAD lock from the repo root:
  D2_FR=<sel> .venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py --max-wait-min 4 -- \
      cad/gs8-d2-v1/candidate-fr1/_test_norelease.py [--force]
Without --force it runs what build_d2 runs (check_release_access when RELEASE_ACCESS is non-empty, else the
no-release row). --force (fix-candidate VC-L4) ALSO calls _no_release_row whatever RELEASE_ACCESS says, so the
discrimination claim 'D2_FR=none (two-pin release) fails all five no-release conditions' is reproducible here."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_d2 as B, layout as L, checks as CK
rows = B.build_printed(only='tub')[0]
print(os.environ.get('D2_FR'), json.dumps(CK.check_release_access(L, rows) if L.RELEASE_ACCESS else [CK._no_release_row(L, rows)], default=str)[:900])
if '--force' in sys.argv[1:]:
    r = CK._no_release_row(L, rows)
    print('FORCED _no_release_row on D2_FR=%s:' % os.environ.get('D2_FR'), json.dumps(r, default=str)[:1600])
