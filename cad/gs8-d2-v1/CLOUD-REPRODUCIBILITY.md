# D2 r5 cloud-polish reproducibility

This is the private cloud fork `r5-cloud-polish-20261007`, based on the stable desktop r5 snapshot captured on 2026-10-06. It is not a continuation of any later desktop rebuild and does not rename that work as r6. All conclusions below are computational; physical evidence remains open.

## Input provenance

- Source archive: `GS8-D2-r5-source-notes-20261006.zip`, SHA-256 `658c059c1227d100cf32056c39a55fc0de77b1d0e87c1cba45ae9d27837371d5`.
- Supplement: `GS8-D2-r5-CAD-review-supplement-20261006.zip`, SHA-256 `b2ba0dd5c2522a78d98460e42500d394751d070f18abf52aaf6aac951d636002`.
- All source/supplement manifest records and the original receipt's 17 sources, 101 outputs and 4 gate documents were hash-verified in cloud. The supplied files were stable across the transfer's pre/post hash sweeps, but this was not an atomic filesystem snapshot.
- The original snapshot is preserved separately from this working copy. The original user's computer was not changed.

## Runtime correction

Use Python 3.12.14 and `cad/gs8-pxl-v3/cad-requirements-lock.txt`. An isolated virtual environment is sufficient; do not change system Python.

The received lock omitted a dependency used by `checks.py`: `manifold3d`. A fresh build reproduced `ModuleNotFoundError` at `check_evf_restraint`. Read-only metadata from the original CAD interpreter confirmed `manifold3d==3.5.4`; this exact pin is now added to the lock. No geometric check was removed or downgraded.

All original 42 pins matched in cloud before the correction. With manifold3d added, all 43 pins match and `pip check` reports no broken requirements. Important versions are CadQuery 2.6.1, cadquery-ocp 7.8.1.1.post1, VTK 9.3.1 and manifold3d 3.5.4.

For Linux/macOS, use the virtual environment's `bin/python`; Windows uses `Scripts/python.exe`. Every heavy D2 CAD build, part test and render continues through `run_locked.py`.

## Headless render limitation

The pinned VTK wheel exposes `vtkXOpenGLRenderWindow`, with neither EGL nor OSMesa support. This cloud runtime has no display and prohibits local Unix socket creation. Starting installed Xorg with its dummy driver failed; supported escalation produced the same result. That restriction was not bypassed.

`--fast` still runs geometry checks and STL exports but skips STEP and VTK assembly views. The section plots use a different rendering path. `--skip-renders` retains fresh assembly/per-part STEP, STL, every geometric check and section plots, and skips only the VTK assembly-view path. The selected flag is recorded in receipt argv. Five output-routing tests cover fresh STEP, stale-view exclusion, unchanged default/fast behavior and unchanged check selection. Original r5 renders must never be passed off as views of changed geometry.

Blender 4.3.2 Cycles CPU renders headlessly here with `scene.cycles.use_denoising = False` (OpenImageDenoise is not included). Such visual artifacts are separate Blender renders, with their own input STEP hashes and view manifest. They are not exact reproductions of the original VTK images and do not establish physical fit, strength, thermal performance or image quality.

## Release discipline

- Freeze shared source before the final Fujinon/Kowa builds and hash audit.
- Follow `HANDOFF.md` section 9: regenerate coupons, generated tables/BOM and the alternate-lens checks before sealing the final Kowa receipt.
- Keep original baseline outputs separate. Only freshly generated or explicitly source-bound carried artifacts belong in the new receipt.
- Rerun regressions and table consistency after all source changes.
- Preserve the distinction between computed CAD checks, host software tests, slicer review, coupon tests, measured fit and powered assembly. No cloud check closes a physical gate.

## Independent output checks

`test_build_outputs.py` covers STEP/VTK routing. `test_print_stock_exports.py` exercises actual binary STL and STEP serialization for both Kowa and Fujinon: printable production/coupon meshes retain the three removable membranes, while per-part STEP round-trips to the cleared finished geometry. The main mechanical tests separately prove that clearing those holes restores the exact finished shape without removing washer-seat material. These are export/manufacturability checks, not print trials.

After final generation, run `audit_cloud_release.py --out cad/gs8-d2-v1/out --final-release --alternate-out cad/gs8-d2-v1/out/_fujinon-cloud-polish-20261007 --json <report.json>`. It checks every receipt source/output/gate-document hash, the required 27-category set, actual production STL manifold shells/volumes, current STEP presence, skipped-view exclusion and unchanged physical evidence states. It also rejects unclassified thin spots even if the legacy category summary is green. The cloud fork now returns a nonzero process exit for a failed computed candidate. The original builder did not. A successful exit still requires receipt and independent-artifact audit review.

The fresh unmodified baseline's Linux tessellation initially exposed two panel sample points absent from the Windows receipt's unclassified list. This is why source pins and a green aggregate alone are insufficient: exact locations need geometry-backed classification, and platform mesh/sample differences must remain visible.

## Cross-executor locking and producer provenance

The original PID-liveness lock can misidentify a live process in another tool execution's PID namespace as dead. POSIX execution now uses a kernel flock on the persistent `.cad.lock` inode. The inode is not unlinked or replaced; the child inherits its descriptor so terminating the wrapper does not release a still-running build. Lock contention times out without running the queued command. The original Windows process-lock path is retained. Five project-local regressions cover contention, stable inode/metadata, wrapper termination, and the Windows metadata path; a separate-tool-execution contention probe also passed. Do not package `.cad.lock` as source or delete it to break a live build.

The runner plus font asset and license are included in the final receipt source hashes. Common-test and coupon outputs now record producer source hashes at generation time; coupon manifests also record each written STL hash. The build carries those producer hashes unchanged. The final independent audit checks complete expected source/gate/part/pin sets, result validity and revisions, duplicate/missing JSON fields, all coupon assets and the matched Fujinon result. It never treats recomputing current source hashes as proof that an older carried artifact was generated from them.
