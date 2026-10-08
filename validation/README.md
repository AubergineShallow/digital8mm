# Cloud verification records

These records describe computational/host checks only. All 53 physical gates remain open.

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
```

The strict cloud artifact audit intentionally expects unadvanced physical evidence. Real bench results belong in the
project's structured evidence workflow; they must not be invented to turn an unmeasured assumption green.
