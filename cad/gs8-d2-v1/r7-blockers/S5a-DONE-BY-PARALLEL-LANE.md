# S5a (C4 core, BX-4 MAJOR) landed by the parallel lane, 2026-10-09 02:28 MPST

The workflow's own S5a agent should **verify only, not re-implement**. Nothing was committed. Snapshot of the touched
files before S5a: `SCR/r7/snap/S5a/cad/gs8-d2-v1/` (layout.py, checks.py and build_d2.py there also hold the S1 lane's
in-progress edits of 02:01, so a rollback must revert only the S5a hunks listed below, never copy those files back;
cots.py, printed_hood.py, test_hood_panel.py and ASSEMBLY.md snapshots are S5a-only; test_r7_c4.py is new).

## What landed (PLAN s5 5a list, SPEC-C4 3.1 / 3.2 / 4.1 / 4.4 / 5)

| file | hunks (all tagged `r7 C4`) |
|---|---|
| layout.py | HOOD: `roll_fin` + `roll_webs` deleted, `tab_catch` dict added (spec values). New `tab_catch_boxes(L=None)` after `CAM['keeper']` (4 B-dicts with `side`, `kind`, `y_in`; ValueError for a bad `head_side` or `head_side` set without `bare_y`). CAM `tab` += `tip_h=None`; `CAM['status']['tab']` text. J7 comment (camera block) and `HOOD_TO_TUB_LATERAL` comment. STEPS 7 camera sentence (tab between the tines; 5a fragment only), STEPS 8 lens sentences + "nor the tab-catch tines" ([C4] fragment; the panel sentences are untouched r6 text for C2/C5 to merge), STEPS 10 window wording. INSERTIONS `lens_in` += `hold='hood_tab_catch'`. REMOVALS: `camera_out` note (no "hold the camera"), new `lens_off` (after camera_out). LATCH_FREE['lens'] r7 text. CRITICAL_JOINTS J7_camera note + required list (`hood_tab_catch_p`, `hood_tab_catch_n`). CRITICAL_FEATURES: `hood_cam_roll_fin` -> `hood_tab_catch_p/n` (origin (-11.35, +-9.78, 88.0), dir +Y, min 2.4, wing). FEATURE_CLASS_RULES `^hood_tab_catch_[pn]$` wing. PRINT_PREREQ_WHY['G-CAM-1']. New `ROLL_CATCH` and `LENS_HOLD_FORBIDDEN` after `HOOD_TO_TUB_LATERAL`. |
| printed_hood.py | `_roll_fin` -> `_tab_catch` (web + flange per side from `L.tab_catch_boxes(L)`, 1 x 45 lead-in on the rear inner vertical edge, 2 x 45 root gussets on both web faces at the band); build_part line `+ _tab_catch(L)`; docstring + PRINT supports text. |
| cots.py | `gs_camera_parts(L, s=None, head_side='both')`: also returns `metal`, `pcb_cover`, `head_side`; `body` built exactly as before. |
| checks.py | New block before `class _Hits`: `RC_VOL`, `RC_MESH`, `RC_TAB_PAD`, `_rc_matrix`, `_rc_bbo`, `_RCScan`, `_rc_assembly_text`, `lens_hold_lint`, `check_roll_catch`. J7 comment "hood roll fin" -> "hood tab catch". |
| build_d2.py | 3 lines: `INFO_NEUTRAL_R7.add('roll_catch')`; `R['roll_catch'] = CK.check_roll_catch(L, rows)` after j7_float; `order.insert(order.index('j7_float') + 1, 'roll_catch')`. |
| test_hood_panel.py | `roll_fin_to_cover` / `roll_fin_ok` -> `tab_catch_to_metal`, `tab_catch_to_pcb_axial`, `tab_catch_ok` (and the exit gate). |
| test_r7_c4.py (new) | SPEC-C4 4.4 cases 1-10 and 13 (11 = 5b, 12 = 5c not included). `--out` keeps out/ clean during development. |
| ASSEMBLY.md (hand-written only) | s1 lens rule row (SPEC-C4 s5 text), B0 item 3 + second paint mark, s3 row 8 (tab-catch tines + look between them), s7 item 6a (SPEC text) and "To close", "Lens swap" paragraph (SPEC text) + "check both paint marks". Needed so the `lens_hold_lint` row passes. The generated step blocks are NOT edited (make_tables in the release regenerates them from STEPS). |

## Quick checks (r7_quick, `--rebuild hood`, sweep step 1.0) and probes

| check | result | PLAN / spec |
|---|---|---|
| roll_catch, 13 s x 8 cases x 2 dirs, variants declared/+Y/-Y | 58 pass + 1 info, 0 fail | - |
| first_contact centred | 3.25-3.258 deg | 3.22 +-0.05 |
| first_contact range (offsets + sag) | 1.758 .. 4.773 | 1.72 .. 4.73 |
| PCB/cover first contact | box:cooler 10.258 (sag), margin >= 5.485 | 10.22, >= 5.4 |
| first_contact_unconfirmed | bare side up to 9.977, margin 0.281 (rule 0.2), gate G-CAM-1 | 9.94, 0.28 |
| window | 0.679 centred / 0.129 worst at every s | 0.679 / 0.129 |
| axial_engagement | min 1.40 (s 0, lip state) | 1.40 |
| tine_strength (estimate) | 6.8 MPa, 0.045 mm (F 24.2 N, lever 20.7, arm 17.39, I 467.6, Z 61.7) | 9.0 MPa, 0.07 |
| lens_hold | lens_in, lens_off pass; lint 0 hits | pass |
| roll_catch run time | 28.7-30.2 s (33.7k mesh booleans, 31 obstacle pieces) | budget about 3 min |
| j7_float | 50/50 pass; body lateral 1.2 to the hood; centring remaining 0.65 | 1.2, 0.65 |
| sweeps camera_in, hood_on, lens_in, panel_on, collar_on | pass | - |
| removals lens_off, camera_out, collar_off, hood_off | pass | - |
| probe clr.py (exact OCP distances) | camera_in min 1.000 (s 0 / 1.25 / 3); hood_on tines vs tub 0.600; final metal 1.200, PCB/cover 1.45 (s 0); panel 5.76 | 1.00, 0.60, 1.2, 1.45, 5.9 |
| `build_d2.py --part hood --out out/_trial-r7` | pass: contract, thin_wall, print_overhang, stl_mesh, bed, keepouts 35, interference_with_cots 21, sweeps 11, critical_features 18 pass (tab_catch_p/n 3.0 >= 2.4); hood 52.4 g | - |
| gs_camera COTS solid | identical to the pre-S5a cots.py (volume, area, bbox, mesh hash; `body` at s 0/1.25/3 identical) | identical |

Tests: `test_r7_c4.py` ALL OK (11 cases, 68 s; case 1 PCB/cover on the r6 fin at 0.734 deg, case 2 cooler box
10.258, case 8 cooler box 6.805 with declared still passing, case 13 centred 3.258/3.25/3.25). `test_hood_panel.py hood`
PASS (tab_catch_to_metal 1.2 at s 0/1.25/3; to PCB/cover 1.45/2.7/4.45). `test_common.py` ALL OK (out/test_common.json
restored from SCR/r7/r6-out-backup afterwards; out/test_hood_panel_hood.json moved to SCR/r7/S5a).

## Real numbers that differ from the spec

- First-contact angles are about +0.035 deg above the judge's j3: the check counts contact when the mesh-boolean
  overlap grows by > 1e-5 mm3 and reports the upper end of a bisection bracket <= 0.008 deg; j3 used OCP distance
  < 0.01 mm. All within the 0.05 tolerance.
- `ROLL_CATCH['step_deg']` = 0.5 (PLAN P4-5 coarse scan), not the spec's 0.25; `axial_min=1.0` added to ROLL_CATCH.
- tine_strength 6.8 MPa instead of 9.0: the check uses the computed contact (y-normal force on the head-envelope top
  edge, lever |dz| 20.7 mm, the smaller of lever and radius) and the arm from the lowest contact z (79.91) to the
  band underside ZT1, as SPEC 4.1 defines; B's 9.0 assumed r 17.4 (head base) and the full tine length 19.3. G-CAM-1
  (real head size) reruns it.
- Lint scope: ASSEMBLY.md hand-written text (outside `<!-- BEGIN/END -->`); STEPS is linted directly and the
  generated block is regenerated from it.
- Planted-fault hoods in test_r7_c4 use plain tab_catch_boxes() of the faulted layout (no chamfers); fault runs
  use s 0 only, the control s 0 / s_nom / s_max.

## Docs still to do (docs agent; SPEC-C4 s5, BX-4 parts only)

MEASURED-PARTS (MP-CAM / G-CAM-1 text, G-CAM-2 text), guide/guide_steps.py (delete ISSUES['8a'], new TIPS['8a'],
line 312 "nor the tab-catch tines"), guide/build_guide.py line 838, roll-fin text sweep (SPEC, DESIGN, PRINT-GUIDE,
R5-BRIEF, NOTES, HANDOFF, RECTIFICATION, LENS-ZOOM-CANDIDATES: current-state -> "hood tab catch (r7)"), BLOCKERS
status line, HANDOFF r7 C4 line, guide hood render. The ASSEMBLY.md hand-written BX-4 passages are DONE (above).
BX-15 (5b) and BX-8 (5c) texts depend on those sub-steps (see IMPL-LOG).
