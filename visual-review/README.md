# D2 cloud polish visual supplement

Six views of the final Kowa cloud-polish CAD candidate. They preserve the approved D2 architecture and show the intended paint-filled markings. The camera has not been physically built or tested.

## Gallery

- `renders/hero.png` - overall form and intended finish
- `renders/controls.png` - corrected selector shaft state and pinned-font labels
- `renders/controls-raw.png` - the same control geometry with unfilled engraving
- `renders/collar_pinch.png` - collar, washer seating and top-down pinch access
- `renders/rear.png` - viewfinder, storage access, grip and strap-side view
- `renders/service.png` - illustrative part separation; harnesses omitted

The exploded view is not an assembly sequence. Follow the main ASSEMBLY.md, including shutdown and physical battery isolation before internal service. Assembly STEP depicts cleared, post-processed holes; sacrificial printing membranes belong to the production STL/print guide.

The visible materials are illustrative. Black fill on the silver panel and white fill on the selector index/power symbol follow the existing finish intent. The exposed encoder shaft is a neutral hardware proxy, not a blue PCB surface. No decorative part was added, and no bore, fastener, or access opening is hidden.

## Findings and evidence

`REVIEW.md` explains the visual/ergonomic review and the changes it informed. `ENCODER-PUSH-REQUIREMENT.md` defines the measurement and acceptance procedure for the uncommissioned encoder push. `control_geometry_probe.json` preserves the baseline geometric measurements behind that finding and the repaired selector mismatch.

All 53 physical gates remain open. The render is not evidence of lens-band fit, optical focus, print quality, switch travel, comfort, cable routing, thermal performance or assembled stability. Kowa is the default modeled lens; the alternative Fujinon has its separate validated computational build in the main package.

`RENDER-PROVENANCE.json` binds the final images/scripts to the Kowa build receipt and source/STEP checks. It also records the independently passing Fujinon receipt. Baseline and intermediate candidate renderings are excluded.

## Reproduce the views

Prerequisites: the main project beside this folder; its pinned CadQuery 2.6.1 environment and exported final STEP files; Blender 4.3.2. From `project/visual-review`, use the pinned Python interpreter for this serialized mesh-export step:

    python ../cad/gs8-d2-v1/run_locked.py -- scripts/export_review_meshes.py --cad-root ../cad/gs8-d2-v1 --build-out ../cad/gs8-d2-v1/out --out meshes

The exporter refuses mismatched recorded Python/font sources or part STEP hashes. Do not run a second CAD command concurrently or remove its lock.

Render one view:

    blender -b -t 6 --python scripts/render_review.py -- --assets meshes --out renders --view hero --samples 128 --revision r5-cloud-polish-20261007

Repeat with `controls`, `collar_pinch`, `rear` and `service`. Add `--raw` to `controls` for the unfilled comparison. Optional exploration views are `collar` and `grip`.

The renderer uses Cycles CPU with denoising disabled and no external scene assets. It changes only lighting, display materials and explanatory exploded positions. The scripts do not rebuild a production release or close any hardware gate.

The separately delivered six-page PDF contains these same six views. `scripts/build_visual_gallery.py` reproduces it from `renders` using Pillow and ReportLab; its hash is recorded in RENDER-PROVENANCE.json.
