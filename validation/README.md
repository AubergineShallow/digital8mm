# Cloud verification records

These records describe computational/host checks only. Every physical gate remains open (r7: 58 listed = 56 open +
2 withdrawn).

**r7 (2026-10-09, blocker review 2026-10-08 fixes).** `rebuilt-cad-integrity.json` is now the final-release audit of
the r7 build (Kowa 05:56:23 +0800 with the Fujinon alternate of 05:50:40): pass; sources 20/20, outputs 86/86, gate
docs 4/4; 35 categories (34 pass + `mass_com` report-only); 58 physical gates (56 open, 2 withdrawn; new G-EVF-3,
G-QT-1, G-HDR-1). Kowa 990 rows = 960 pass + 30 info + 0 fail; Fujinon 987 rows = 957 pass + 30 info + 0 fail. Tests
after that build (05:56-06:09 MPST, all through `run_locked.py`):
- `test_r3_regressions.py`: 82 of 82 cases pass;
- the focused unittest list: 73 tests OK, with 4 POSIX-only skips;
- `test_collar.py` both lenses: PASS in 118.8 s;
- r7 planted-fault suites (94 cases): `test_r7_c1.py` 14/14, `test_r7_c2_mate_reach.py` 13/13, `test_r7_c4.py`
  11/11 (cases 1-10 and 13), `test_r7_c5_handling.py` 19/19, `test_r7_lead_access.py` 21/21, `test_r7_fixup.py` 9/9,
  `test_r7_integration.py` 7/7 (its category-count case now runs against the r7 `checks.json`);
- `test_hood_panel.py` (hood and panel): PASS.

**r6 (2026-10-08).** `rebuilt-cad-integrity.json` is the final-release audit of the r6 build (Kowa 16:05:33 +0800 with
the Fujinon alternate): pass; sources 20/20, outputs 86/86, gate docs 4/4; 28 categories (27 pass + `mass_com`
report-only). Tests after that build:
- 82 custom regression cases (65 + 17 r6 planted-fault cases);
- 73 focused unittest cases, OK with 4 POSIX-only skips;
- `test_collar.py` both lenses, PASS in 151.8 s.

The records below describe the cloud-polish run that r6 builds on.

- `cad-kowa-integrity.json`: final Kowa source/output/gate-doc, mesh, STEP and producer-evidence audit.
- `cad-fujinon-integrity.json`: final Fujinon audit.
- `software-verification.json`: package source/test hashes, 256 EVF tests, post/recorder/model checks and wheel/source-package hashes. Its `sources_sha256` paths are relative to `software/gs8-camera-evf/`; `navigation_docs_sha256` paths are relative to the project root.
- `lock-contention.json`: separate-process contention, child lifetime and metadata results. Windows concurrency was not tested on Windows.

CAD verification on the final corrected geometry: 65 custom regression cases; 73 focused unittest cases; 18 common
helpers; and the full both-lens collar geometry/assembly check (127.6 s). All passed. Both final variants have 27
passing categories, zero failures/stubs/unclassified spots. Kowa has 748 pass/18 info rows, Fujinon 745 pass/18 info.

From `cad/gs8-d2-v1/`, using the pinned interpreter, run:

```text
python run_locked.py -- test_r3_regressions.py
python run_locked.py -- -m unittest -v test_mechanical_refinements test_datum_inputs test_panel_refinements test_collar_rear_land test_build_outputs test_print_stock_exports test_release_gates test_audit_cloud_release test_run_locked
python run_locked.py -- test_collar.py
python run_locked.py -- test_r7_c1.py
python run_locked.py -- test_r7_c2_mate_reach.py
python run_locked.py -- test_r7_c4.py --out <scratch>/test_r7_c4.json
python run_locked.py -- test_r7_c5_handling.py
python run_locked.py -- test_r7_lead_access.py
python run_locked.py -- test_r7_fixup.py
python run_locked.py -- test_r7_integration.py
python run_locked.py -- test_hood_panel.py
```

The r7 suites read the release STEPs in `out/step/parts` and `out/checks.json`, so run them after the release build.
`test_r7_c4.py --out` and moving `out/test_hood_panel_*.json` away keep `out/` to release outputs only.

The strict cloud artifact audit intentionally expects unadvanced physical evidence. Real bench results belong in the
project's structured evidence workflow; they must not be invented to turn an unmeasured assumption green.
