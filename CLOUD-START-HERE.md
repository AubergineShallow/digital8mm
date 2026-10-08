# GS8 D2 · cloud-polish copy

**Fork: `r5-cloud-polish-20261007`.** This independent copy starts from the stable desktop r5 capture of
6 October 2026, 14:04–14:05 UTC, with verified CAD exports captured by 14:11:53 UTC. Later desktop work is a separate
history. Extract into a new folder; do not overwrite or blindly merge into the active desktop project.

## Current result

- **Kowa:** 27 passing CAD categories; 748 pass + 18 information rows, no failures, stubs or unclassified thin spots.
- **Fujinon:** 27 passing categories; 745 pass + 18 information rows, no failures, stubs or unclassified thin spots.
- Independent audits verify every required source/output/gate-document hash, actual STL meshes, fresh STEP,
  producer-bound coupons/common tests, both-lens linkage and complete runtime/manifest coverage.
- **Tests:** 65 CAD regressions + 73 focused tests; the full collar check passes for both lenses. The D2/EVF package
  passes 256 host tests; the post planner passes 66, the existing recorder 110, and native numerical models 69.
- **Physical qualification: unchanged.** All 53 physical gates remain open. Nothing was printed, sliced, measured,
  assembled, powered, purchased or deployed by this pass. These results do not establish fabrication or operation readiness.

## Read and inspect

1. [Mechanical changes and remaining decisions](cad/gs8-d2-v1/CLOUD-POLISH-NOTES.md)
2. [Runtime, rendering and evidence details](cad/gs8-d2-v1/CLOUD-REPRODUCIBILITY.md)
3. [D2 software integration](software/gs8-camera-evf/D2-INTEGRATION.md) and
   [host EVF presentation](software/gs8-camera-evf/D2-PRESENTATION.md)
4. [Verification records](validation/README.md)
5. [Final visual review](visual-review/README.md): six source-linked views, including unfilled markings

Current Kowa outputs are in `cad/gs8-d2-v1/out/`; Fujinon outputs are in
`cad/gs8-d2-v1/out/_fujinon-cloud-polish-20261007/`. Each has an assembly STEP, per-part STEP, production STL,
section plots, manifests and receipt. The primary output also has the 27 coupon STLs.

**Print/assembly distinction:** collar production/coupon STL contains three removable 0.2 mm bridge membranes.
STEP and assembly checks describe the cleared finished geometry. Follow the print-manifest postprocessing notes;
do not alter washer-seat, cone or foot datums. Computar remains data-only, with no approved printable collar.

Assembly-view renders are included in the STEP-hash-linked `visual-review/` supplement. The pinned VTK display path is unavailable
in cloud; `--skip-renders` keeps STEP, STL, all geometry checks and section plots. It skips only VTK assembly views.

## Reproduce the CAD

Work from this extracted `project/` directory. Preserve the supplied `out/` elsewhere before a clean rebuild.

```text
python tools/bootstrap_cad.py
```

This creates the pinned Python 3.12.14 environment and its 43 dependencies, including the previously missing
`manifold3d==3.5.4`. In every command below, use `.venv-cad/bin/python` on Linux/macOS or
`.venv-cad/Scripts/python.exe` on Windows in place of `python`. Do not use an unrelated system interpreter.

```text
python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/test_common.py
python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/make_coupons.py
python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/coupons_r1.py
python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/build_d2.py --skip-renders --sweep-step 1.0
python cad/gs8-d2-v1/make_tables.py
python electronics/gs8-d2-v1/make_bom.py
python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/build_d2.py --lens fujinon_hf6xa --skip-renders --sweep-step 1.0 --out cad/gs8-d2-v1/out/_fujinon-cloud-polish-20261007
python -c "import shutil; shutil.copyfile('cad/gs8-d2-v1/out/_fujinon-cloud-polish-20261007/checks.json','cad/gs8-d2-v1/out/checks-fujinon-sweep1mm.json')"
python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/build_d2.py --skip-renders --sweep-step 1.0
python cad/gs8-d2-v1/make_tables.py --docs design
python cad/gs8-d2-v1/make_tables.py --check
python cad/gs8-d2-v1/audit_cloud_release.py --out cad/gs8-d2-v1/out --final-release --alternate-out cad/gs8-d2-v1/out/_fujinon-cloud-polish-20261007 --json validation/rebuilt-cad-integrity.json
```

A failed computed candidate now returns a nonzero exit. Still inspect the final independent audit. Keep heavy CAD
commands serialized through the runner; never delete its persistent lock to bypass an active build.

The main fault suite is `test_r3_regressions.py` (custom runner). Additional suites cover datums, panel roots/font,
collar rear land and print stock, output routing, release gates, audit omissions and process locking. Their exact
commands and results are summarized in [validation/README.md](validation/README.md).

## Try the software safely on a host

From `software/gs8-camera-evf/`, using Python 3.10+ (the pinned environment also works):

```text
python -m unittest discover -s tests -v
python -m gs8_camera_evf d2-demo --output demo-two-takes
python -m gs8_camera_evf inspect --output demo-two-takes
python examples/render_d2_presentation.py --output evf-previews
```

Use a new demo directory. Takes are synthetic, with no camera footage or performance proof. The optional preview
script needs Pillow. `d2-run` is the integrator entrypoint described in D2-INTEGRATION; real adapters, commissioning,
live preview compositing, retained shutdown display and power-off behavior remain integration and hardware-qualification work. The post tool is
still a planner, not a completed DNG-to-film-to-video renderer.

## First real-world steps

Measure MP-CAM/G-LENS before production printing; then qualify collar/fastener coupons and assembled sag/focus.
Verify selector and exposure-push travel, real cable/FPC routing, thermal behavior and all power gates. In particular,
the 27 W planning peak still exceeds the X1203's 25.5 W rating. Do not transplant the historical 3S wiring/software
instructions into this D2 1S2P design. Keep the physical 18/24 switch and no-LED decisions.

The old desktop-output snapshot, environments, credentials, caches and runtime locks are excluded from this package.
Relevant research/decision documents and source provenance are retained. `PACKAGE-MANIFEST.json` records included
file hashes and exclusions; the final package follows an earlier recoverable source checkpoint.

[Source provenance](SOURCE-PROVENANCE.json) identifies the captured baseline and local checkpoint.
[SOURCE-CHANGES.patch](SOURCE-CHANGES.patch) is the reviewable code/document delta; generated CAD outputs and render pixels are excluded from that diff.
