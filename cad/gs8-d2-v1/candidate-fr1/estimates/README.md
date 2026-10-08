# Panel stiffness estimates (ESTIMATE only, not FEA-validated, nothing measured)

Copied 2026-10-05 15:16 by fix-candidate (finding VC-M3) from the fr-panel-2 session scratchpad `fp2/` so that
JOINT-panel.md s. 11.2 and CANDIDATE.md s. 2/6 can be reproduced from the fork. Files are byte copies of the scratchpad
originals (10:33-11:23).

- `grill.py`: grillage (Hambly) model of the 2.8 ASA panel (method in JOINT-panel.md s. 11.1).
- `opts.py`, `opts2.py`: option table (opts2 = unilateral wall-bearing contact, the model the table uses).
  Option '1e 1c+front rib' is **A2** (the chosen FR panel geometry).
- `opts2-output.txt`: output of `opts2.py` re-run here 15:17 (pure numpy, no CAD); it reproduces every number of the
  JOINT-panel.md s. 11.2 table and the bottom-edge profiles.
- `sens.py`: sensitivity runs; `depth.py` + `depth.pkl` + `ribchk.py` + `show.py`: the inner-face free-depth map used to
  place the frame ribs (depth.py reads the r2 STEP parts from `cad/gs8-d2-v1/out/step/parts/`, run from the repo root).

Run: `cd cad/gs8-d2-v1/candidate-fr1/estimates && ../../../../.venv-cad/Scripts/python.exe opts2.py`
