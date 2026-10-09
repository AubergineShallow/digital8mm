# GS8 D2 handoff, r7 (2026-10-09): blocker review 2026-10-08 rectified in CAD (BX-1 BLOCKER and the four MAJORs)

Read this section first; the r6 entry below it and everything after are history. The user asked: "Rectify these
blockers. Cease work by 0730H tmr." The review is `guide/BLOCKERS-2026-10-08.md` (BX-1..BX-17); its r7 status lines
are at its end. The fix specs are `r7-blockers/SPEC-C1.md`..`SPEC-C6.md` (each has a fix-up correction note at the
top), the integration plan is `r7-blockers/PLAN.md` and the work log with every real number is
`r7-blockers/IMPL-LOG.md`. Revision label: `GS8 D2 r7-20261009 (r6-20261008 + blocker review 2026-10-08 fixes)`.
Working copy: the `digital8mm` repository; nothing committed or pushed. As before, nothing was printed, sliced, bought,
measured, assembled or powered.

**Release state:** Kowa receipt `out/build-receipt.json`, built **2026-10-09 05:56:23 +0800** (`--skip-renders --sweep-step 1.0`, 338.9 s): **35 categories = 34 pass + `mass_com` report-only (info); 990 rows = 960 pass + 30 info + 0 fail**, no stubs, `cad_release_candidate` true; checks.json `2d6f68b2...`. Fujinon `out/_fujinon-cloud-polish-20261007/` (05:50:40, 348.8 s): 35 categories, 987 rows = 957 pass + 30 info + 0 fail, candidate true; its checks are carried as `out/checks-fujinon-sweep1mm.json` and match the release sources (`carried_checks`). `audit_cloud_release.py --final-release`: pass, sources 20/20, outputs 86/86, gate docs 4/4, 35 categories, 58 gates (56 open, 2 withdrawn) (`validation/rebuilt-cad-integrity.json`). `make_tables --check`: stale none, lint 0. New categories (7): `mate_paths`, `mate_reach`, `cable_stow`, `header_housings`, `lead_access`, `handling`, `roll_catch`. STLs changed against r6: tub (C3 floor hole), hood (C4 tab catch) and the coupon cut from the tub (`coupon-pi-keeper-tub`); every other STL is byte-identical, including base_grip, panel, knobs, plunger and the collar gauge. Balance: Kowa 896.2 g, +1.55 mm; Fujinon 782.8 g, -9.65 mm. Printed set 298.1 g / 16.0 h (estimates). Every part's `print_release` is still blocked: no bench record exists yet.

**Release run (05:01-05:56 MPST):** the part-done BX-15 hunks (never landed; one failing test case) were rolled back first, per PLAN s5 S7. Attempt 1 failed only `make_tables --check`: the count lint read the Pi model number in the generated step-1 phrase "dry-fit the Pi ... on the standoffs" as a standoff count; STEPS[1] now drops the model number (text only). Attempt 2 failed only the audit's registrations: the three new gates G-EVF-3, G-QT-1 and G-HDR-1 (and their assembly-evidence items, 26 -> 29) were not registered, and its lineage test looked for `r5-cloud-polish-20261007` in the label. `audit_cloud_release.py` now registers them and accepts the `r6-20261008` parent tag; no rule was removed. Attempt 3 (Fujinon, Kowa, tables, check, audit) passed.

**Tests (after the release build, 05:56-06:09, all through `run_locked.py`; `validation/README.md`):**
`test_r3_regressions.py` 82/82; the focused unittest list 73 OK (4 POSIX-only skips); `test_collar.py` both lenses
PASS (118.8 s); r7 suites 94/94: `test_r7_c1` 14, `test_r7_c2_mate_reach` 13, `test_r7_c4` 11 (cases 1-10 and 13),
`test_r7_c5_handling` 19, `test_r7_lead_access` 21, `test_r7_fixup` 9, `test_r7_integration` 7 (the category-count
case now runs against the r7 checks.json); `test_hood_panel.py` hood + panel PASS.

**What r7 changed (each item: what was wrong, the fix, the computed proof, the physical gate):**
- **BX-1 BLOCKER, C-16, BX-7, BX-9 (C1, EVF slot).** The r6 order mated the EVF HDMI outside and then slid the pair
  in, so the plug crossed the tub (60-66 mm3). Now the pair slides in unplugged (foam pad stuck to the OLED back, BX-7),
  the 5 V PH junction is mated 60 mm out and tucked with tweezers (BX-9), and the HDMI is plugged in place: push from
  the stick-guide top or straight up from the open well (no lever; tool 10 is only an upright push stick). Service
  (C-16) unplugs the HDMI in place first with smooth-jaw pliers (tool 15) coming up from the well. New shared
  machinery: PLUGS (20) with carried-box sweeps/removals, ACCESS corridors (9), new category `mate_paths`
  (plug_in, access, coverage incl. the MATE_POSES rule); `evf_restraint` support_span rows. Gate G-EVF-3.
- **BX-5, BX-13, BX-14 (C5, knobs and handling).** Knobs are pressed on at bench step 2 with a thumb behind the board on
  a 0.2 mm paper shim and ride in with the panel; the 18/24 shaft is cut off the panel (P - 6.9, final 6.7-7.1).
  Panel screws are driven with the camera on its hood roof at the bench edge (overhang -Y 20 mm); rests are only the
  hood roof at the bench edge (step 8 and service) or the right side (right_down_8/10); base-down is hand-held and
  the camera never stands on its grip end (tips at about 6 deg). New category `handling` (press_cover, press_fit, snap_basis, rest_pose with a
  driver-plane rule and a static-stability rule >= 10 deg, rest_cover). Gates G-KNOB-1, G-ENC-1, G-MP-ENC, G-MP-SW.
- **BX-2, BX-10 (C2, encoder lead and header housings).** The QT lead is 250 mm (240-270; Adafruit 4397 spliced to
  Pololu 5521, splice window 91-115 mm in the straight cross run) and is plugged with the panel 60 mm off: a helper
  holds the body, the panel is propped on a block about 110 mm tall, the PH junction is mated first with both hands,
  then the QT by a fingernail push; the spare folds into `ko_lead_stow` at +30 mm. Single 1-pin header housings
  (1x2 only on 33/34, 37/39), seated with open tweezer tips. New categories `mate_reach` (hand and tail envelopes per
  MATE_POSES row), `cable_stow`, `header_housings` (gaps cooler 0.68, kit 0.75, tub 1.13, hood 2.27; completeness
  rows); `cable_routes` plug-point rule. Gates MP-QT (filed as the QT lead line of MP-ENC), G-QT-1, G-HDR-1.
- **BX-3, BX-11, BX-16 (C3, battery pigtail and run lead).** The pigtail is cut to L_cut = 200 mm + the G-W2
  pads-to-W length (stop if pads-to-W > 25 mm: G-W5 drop 0.15 V), formed into a U at the W mark, taped under the
  X1203 and strain-relieved with neutral-cure RTV (no standoff tie); the XT30 comes 28.4 mm out of the mouth (>= 15).
  The junction is re-posed flat on the pack top under the run button, female end to the rear, fuse beside it (exits
  8.0/8.0 mm vs 7.2 needed). Step 10: camera on its right side, pack in the palm. The run lead is threaded up the base
  passage and the rear of the floor hole (now x -41.5..-28, window 3.5 >= 3.2) before the button and the tub. New
  category `lead_access` (mouth, range, store with exits, lanes, separation, run window, wrap clearance,
  pigtail_drop); tub floor hole changed (base_grip byte-identical). Gates G-W2 (d_board, stop branch), G-MP-PACK
  (rigid exit <= 0.8 mm, fold), MP-RUN.
- **BX-4 (C4 core, lens torque).** The hood roll fin is replaced by a two-tine tab catch, so the camera's metal lock
  tab takes the lens-thread torque and nobody holds the camera. Step 8 turns the camera back off the tine before s_c4
  (lint), and the step-10 level check is done every time. New category `roll_catch` (first contact 3.258 deg centred,
  1.758..4.773; PCB/cover >= 10.258, margin >= 5.485; window 0.679/0.129; axial 1.40; tine 6.8 MPa est; lens_hold +
  text lints over STEPS, ASSEMBLY and the guide sources). Gates G-CAM-1 (lock-screw head side), G-CAM-2.
- **Verification and fix-up.** Five read-only verifiers (one per cluster) planted the r6 faults back and found 10 major
  physical-procedure defects, all closed by the fix-up slot (see SPEC-Cn correction notes and IMPL-LOG 03:34-04:47).
- **Documents:** ASSEMBLY (tools 15-17, checks rows, handling, service items), MEASURED-PARTS, SPEC gate list, WIRING
  (W-QT, pigtail, notes), make_tables/make_bom data, guide_steps (pages, GATES, TIPS; ISSUES now empty), BLOCKERS
  status lines. Generated blocks were regenerated by the release (make_tables, make_bom).

**Not fixed this round (open, spec ready):**
- C6: BX-6 (plunger capture, SPEC-C6 6a), BX-12 (driver family, 6b), BX-17 (hood release comb, 6c). Interim guide tips
  stay (pages 3b, 5a, B0).
- BX-15 (SPEC-C4 5b, collar-gauge thumb dimple + held-hand driver envelopes): a part-done version was in the tree,
  never landed (its test case failed); the release rolled it back, so the collar gauge is the r6 part. Interim tip on
  page 7a.
- BX-8 (SPEC-C4 5c, FPC fold card): not started. Interim tip on page 7b.
- Computed minors left open by the fix-up: roll_catch lens-out lateral offset should come from the counterbore play;
  no rule ties a recorded G-CAM-1 pass to `HOOD['tab_catch']` head_side; `cable_stow` reports 'info' (not fail) for a
  spare with no sized home on cables without a stow; no C-16 `unplug=[]` regression plant.
- G-MP-PACK: the rigid solder-cup/heat-shrink length beyond each XT30 housing must be measured (allowance 0.8 mm);
  if longer, re-pose and rerun lead_access.
- G-W2/G-W5: if the X1203 pads are more than 25 mm of string from W, do not cut the pigtail (decision needed).
- Hand-written SPEC.md s5 "Assembly order" table still shows pre-r7 wording (HDMI mated outside, knobs at step 9,
  level check only if off); layout.STEPS and the generated ASSEMBLY step blocks are correct.
- M1 (collar clamp spring/thermal term) from r6, every physical gate, G-W12 power, the airflow study, plan B.
- Guide: re-rendered after the tests (`guide/build_guide.py --remesh`, 06:12, 43 pages, 103.6 s; footer GS8 D2
  r7-20261009) into the local `guide/out/` only; the published guide artifact was not republished and still shows r6
  (r6 outputs kept in the release scratch folder). Stale text left in the guide's picture code (presentation only,
  not changed after the freeze): `guide/diagrams.py` lines 82-84 (page 1b picture still says "tie to a standoff",
  which contradicts the page's own caution and the BX-3 fix) and lines 212-225 (page 6 EVF-mate note "All three
  outside the body"); `guide/build_guide.py` line 832 service label "EVF out (BX-1)"; page 1b item 3 still marks W
  by edge measurement, while STEPS[1] now finds the edge by dry-fitting the Pi. Fix these strings and re-render.

**User decisions (PLAN s10; defaults applied, nothing bought):**
1. U-1 (C1): smooth-jaw long-nose pliers are tool 15 (hand tool, no BOM row). Default: included.
2. U-2 (C2): QT lead = Adafruit 4397 spliced to Pololu #5521 (about USD 2 extra; BOM D2-24/D2-24B). Option: an
   unverified one-piece JST-SH to 4 x Dupont lead, 240-270 mm, after the MP-QT buy-check.
3. U-3 (C4): keep the 200 mm 22-to-15 FPC (BX-8 open; G-MP-FPC confirms). Option: a 100-150 mm FPC.
4. U-4 (C6): only if G-SNAP-2/whole fails, approve a hood strain stop behind hk1/hk2. Nothing to decide now.
5. U-5 (C1): bench-mating the EVF HDMI (tub cut, panel heel, right-wall-down rule) is not recommended; reconsider only
   if G-EVF-3 fails on the first print.
6. U-6: C6 (BX-6, BX-12, BX-17), BX-8 and BX-15 stay open with interim wording and ready specs; or allow more time.

**What the user must do first (bench, in this order):** as r6 (coupons; PRINT-GUIDE s7 order 2 measurements starting
with B0/MP-CAM, now including the G-CAM-1 lock-screw head side and the MP-QT/MP-HDMI/MP-PACK/MP-X1203 additions; update
`layout.py`; rerun the release sequence), then fix M1 before the collar prints. Before cutting the pigtail: G-W2 pads-to-W.

# GS8 D2 handoff, r6 (2026-10-08): print order and orientation settled, audit 2026-10-06 minor findings fixed

Superseded by the r7 entry above; kept as history. The sections below it are older history (cloud polish, then r5 and earlier). The user asked:
"Settle the print order and orientation. Fix the minor findings as well." The point-by-point answer to the audit is
`audit/d2-readiness-2026-10-06/RESPONSE.md`. Revision label: `GS8 D2 r6-20261008 (r5-cloud-polish-20261007 + ...)`.
Working copy: the `digital8mm` repository. As before, nothing was printed, sliced, bought, measured, assembled or
powered.

**Release state:** Kowa receipt `out/build-receipt.json`, built **2026-10-08 16:05:33 +0800** (`--skip-renders --sweep-step 1.0`, 522.6 s): **28 categories = 27 pass + `mass_com` report-only (info); 852 rows = 833 pass + 19 info + 0 fail**, no stubs, `cad_release_candidate` true; checks.json `c215f4c7...`. Fujinon `out/_fujinon-cloud-polish-20261007/` (15:56:46): 28 categories, 849 rows = 830 pass + 19 info + 0 fail, candidate true; its checks are carried as `out/checks-fujinon-sweep1mm.json` and match the release sources (`carried_checks`). `audit_cloud_release.py --final-release`: pass, sources 20/20, outputs 86/86, gate docs 4/4, 28 categories, 55 gates (53 open, 2 withdrawn) (`validation/rebuilt-cad-integrity.json`). `make_tables --check`: stale none, lint 0. Balance unchanged: Kowa 895.3 g, +1.5 mm; Fujinon 781.9 g, -9.7 mm. Printed set 297.5 g / 16.0 h (estimates); collar 17.3 g (ears r 5.6); centring gauge 22.0 g. Every part's `print_release` is blocked: no bench record exists yet.

**What r6 changed:**
- **Print order (audit M2): one table, enforced.**
  - `layout.PRINT_PREREQS` names, for every printed part, the gates whose measurements set its geometry. They are
    the MEASURED-PARTS "Blocks" column, plus G-COMB-1, and G-KNOB-1 or G-COL-1 where they apply.
  - `COUPON_PREREQS` holds the G-COL-1 coupons to G-CAM-1 and G-LENS. `PRINT_SEQUENCE` is the order within a stage.
  - A slicer record, or a G-COL-1 coupon record, filed or dated before its gates passed is rejected.
  - The receipt's `print_release` shows what each part still waits for. PRINT-GUIDE s7 is generated from these
    tables.
- **Orientation: settled and computed.** Every face-down is unchanged. The new category `print_overhang` checks every
  production STL and the centring gauge layer by layer (rules in SPEC s6 item 4p).
  - It confirmed every bridge the guide lists.
  - It found two unlisted overhangs, the s_k2 keeper-boss chin and the LL collar-insert-boss chin. Each now has a
    declared paint-on support: the tub has 4 supports, not 2.
  - The collar ears are r 5.6 (review A3).
- **Centring (X2):**
  - A printed centring gauge per lens (`stl/tools/collar_gauge.stl`).
  - Step 7 now fits and centres the collar before the camera goes in.
  - j7_float subtracts the declared centring stack from every lateral gap.
- **Checks:**
  - j7_float sweeps the back-focus range every 0.25 mm (L2). A missing lens or collar FAILs (L3). The lens keeps
    0.5 mm from every other part (L4). A duplicate probe ID FAILs, and there is a new LR-foot wall probe (L5).
  - "measured" needs a G-LENS record (L6). The bolted-only anchor margin gets a WARN (L7). An empty coupon map is
    rejected (L10). The coupons and the carried Fujinon checks are source-linked (L11). Record dates must be ISO,
    and the support files are hashed (L12).
  - mass_com is report-only (L9). Insert depth and screw-length tolerance (B-3). Service driver audits for s_c4 and
    s_j (B-11).
- **Documents:**
  - Adapter mark at B0 and at every lens change (B-2). Hold the metal lens mount, not the cover (B-7).
  - Collar in ASA, with a G-W11 thermocouple at the collar foot (B-8). Stale counts fixed (B-9, B-10).
  - Torque screwdriver in the BOM (D2-77) and as tool 13 (B-6). Heat-set tip system named (B-12).
  - Coupon dry fit (B-13). Back the boss while heat-setting (B-14). Keep s inside its range (X4).

**Still open:**
- **M1:** the collar clamp has no spring and no thermal term. It was not part of this request, and it is the one open
  design defect. Fix it before the collar is printed; the print order already puts the collar last.
- Every physical gate (53 open, 2 withdrawn).
- G-W12 power.
- The paused airflow study.
- Plan B, if G-LENS shows the band moves.

**What the user must do first (bench, in this order):**
1. Print the calibration coupons; they need no measurement.
2. In parallel, do the bench measurements of PRINT-GUIDE s7, order 2, starting with B0: MP-CAM with the lens,
   including the adapter mark and the BFAR travel.
3. Update `layout.py` with any difference, and rerun the release sequence (`CLOUD-START-HERE.md`).
4. Then print the G-COL-1 coupons and the gauge, and run G-COL-1. Fix M1 first.
5. Finally print the parts as PRINT-GUIDE s7 releases them.

# Cloud-polish fork: r5-cloud-polish-20261007

## Adopted as the desktop baseline (2026-10-07, main desktop session)

The user asked for the four `GS8-D2-cloud-polish-0N-of-04.zip` archives to be verified and, if satisfactory, used as
the new baseline. The verification passed and the package is installed here. The cloud text below ("independent copy",
"not a replacement") describes how it was made; from now on it *is* the desktop baseline.

**How it was verified:**
- **Provenance:** the package equals the desktop r5 state at 22:04 SGT on 2026-10-06 plus `SOURCE-CHANGES.patch`
  (81 files).
  - The other 1,147 files are byte-identical to the desktop.
  - The patch applies cleanly to the desktop files and reproduces the package exactly.
  - The only later desktop work, `audit/d2-readiness-2026-10-06/`, is untouched by the package and kept.
- **Code review:** the check changes are stricter, not weaker:
  - every lens needs a support band;
  - a three-bolt anchor model with LR inactive;
  - stub attribution only when every offender is a stub;
  - unclassified thin spots now block the release;
  - the knob/encoder proxies are now in mate_overlap.
- **Rerun on this machine** (same pinned environment, Windows):
  - tests: `test_r3_regressions` 65/65; 73 focused tests (4 POSIX-only skips); `test_common` ALL OK; `test_collar`
    PASS;
  - builds: coupons; Kowa and Fujinon builds both candidate true;
  - `make_tables --check` clean.
  - Against the cloud outputs, all 87 mesh files compared (production, coupon and modifier, both lenses) have the same face counts, volumes within 2.5e-9 relative and bounds within
    1e-14 mm. The check outcomes are identical (Kowa 748 pass + 18 info, Fujinon 745 + 18, 27/27). Only the
    serialized bytes differ (Linux against Windows).
  - Software (`software/gs8-camera-evf`): 256/256 after a one-line Windows test fix. `test_d2_app` compared against
    the 8.3 short temp path; it now uses `Path(tmp).resolve()`.

**What is on disk now:**
- `out/` holds the Windows-built outputs from this machine (STLs byte-identical across the two local Kowa builds).
- Final Kowa receipt: **2026-10-07 13:34:26 +0800**, 27/27, 748 pass + 18 info + 0 fail, candidate true.
- `audit_cloud_release.py` passes: sources 20/20, outputs 85/85, gate docs 4/4 (`research/cloud-polish/desktop-adoption-audit.json`).
- Fujinon: `out/_fujinon-cloud-polish-20261007/` (local build).
- Pre-adoption state:
  - r5 outputs in `out/_r5-2026-10-06/`;
  - sources and docs in `baseline-r5-2026-10-06.zip`;
  - the copy log in `research/cloud-polish/ADOPTION-COPY-LOG.txt`.
- The cloud-built outputs remain inside the 4 zips.

**Still open:**
- Every physical gate.
- The 2026-10-06 audit (`audit/d2-readiness-2026-10-06/REVIEW.md`) has no response yet:
  - M1: the collar clamp has no spring or thermal term;
  - M2: print order before MP-CAM. Partly covered by the polish's G-LENS rebuild rule.
  - M3: the D2 fork is not in git.
- Commands: use `--skip-renders` as in `CLOUD-START-HERE.md`, or omit it here to get the VTK views (VTK works on this
  machine).

This is an independent copy of the captured r5 snapshot, not the original project's next release and not a claim to
supersede later desktop work. Snapshot checkpoint: `789f40731f0c3cebf691f3920e8d244057219048`. The original files are
untouched. Read `CLOUD-POLISH-NOTES.md` first for changes, verification and remaining physical gates, then the r5
handoff below for inherited design history. Current generated results belong to this fork only; the historical
732-pass/17-info result below describes the captured r5 source.

## Final cloud-polish verification (2026-10-07 SGT)

- Kowa, built 00:06:26 +0800: **27 categories, 748 pass + 18 info + 0 fail**; candidate true, no stubs or
  unclassified thin spots. Receipt: `out/build-receipt.json`.
- Fujinon, built 00:02:15 +0800: **27 categories, 745 pass + 18 info + 0 fail**; candidate true, no stubs or
  unclassified thin spots. Receipt: `out/_fujinon-cloud-polish-20261007/build-receipt.json`.
- Independent source/output/gate-document rehash: Kowa 20 / 85 / 4; Fujinon 20 / 54 / 4, all matching. Serialized
  STL/STEP and print-stock/finished-geometry checks pass. Tests: 65 legacy regressions + 73 focused cases; the final
  both-lens collar integration test passes (127.6 s). Generated table/BOM checks are clean.
- All **53 physical gates remain open** (two historical gates withdrawn). Slicer, coupon, measured-fit and
  assembly/operation states remain **not run**. This is a computed CAD candidate, not a print or camera readiness claim.
- Start with MP-CAM/G-LENS, then production coupons including the revised encoder teeth and collar print stock;
  encoder push travel, power/thermal and assembled sag acceptance remain unverified. The data-only Computar cannot
  export a collar until its rear-entry design is resolved from measurements.

# GS8 D2 handoff (r5, 2026-10-06: heavy-lens support, the J7-R float; r4 maturity pass below; FR1 still exploratory)

Read this first; section 0 is new and supersedes the build numbers of sections 0b and 1. Then `R5-BRIEF.md`,
`RECTIFICATION.md` sections "r5", "r4" and "r3", `DESIGN.md` s1 and s6f, and for the reviewer
`audit/d2-readiness-2026-10-05-r3/RESPONSE.md` (and the earlier `audit/d2-readiness-2026-10-05/RESPONSE.md`). The FR1
candidate is in `candidate-fr1/CANDIDATE.md`. Earlier handoffs are superseded (r1: `baseline-r1-2026-10-04.zip`; r2:
`baseline-r2-2026-10-05.zip`; r3: `baseline-r3-2026-10-05.zip`; r4: `baseline-r4-2026-10-06.zip`, outputs in
`out/_r4-2026-10-06/`).

**What is true on this machine:** every result here is a computed CAD check on built solids and purchased-part
proxies, desk research from datasheets and drawings, or a document change. Nothing has been printed, sliced, bought,
measured, assembled or powered, and no git commit was made for r3, r4 or r5.

## 0. r5 (2026-10-06): heavy-lens support ("Fix the sagging issue for the heavy lens first")

Receipt `out/build-receipt.json`, built **2026-10-06 16:32:38 +0800** (Kowa, `--sweep-step 1.0`, 579.6 s): **27 of 27
categories, 749 rows = 732 pass + 17 info + 0 fail**, 0 stubs, `cad_release_candidate` true; checks.json SHA-256
`c9d748c8...`; 17 of 17 sources, 101 of 101 outputs and 4 of 4 gate docs match the files on disk. Fujinon
`out/_fujinon-r5` (16:16:05, `--fast`, 1 mm): 27 of 27, 746 rows = 729 pass + 17 info + 0 fail (copied to
`out/checks-fujinon-sweep1mm.json`, `83b55def...`). Tests `test_r3_regressions.py` 38 of 38; `make_tables.py --check`
stale none, lint 0; BOM 67 purchased lines, 0 uncovered. Evidence: slicer 12, coupons 10, measured 17, assembly 26
items, all "not run"; 55 gates listed, 53 open, 2 withdrawn.

**What r5 changed (decision and study: `R5-BRIEF.md`, `research/r5-lens-support/`; log `IMPL-NOTES.md`):**
- **Premise corrected.** The GS lens mount is milled aluminium; the compliant link is the housing-to-PCB joint (2 small
  M2 screws, nylon washers, a gasket). D2's r4 camera model did not match the official drawing: the C flange sat 10 mm
  too far forward, there are no front lands, and the 2 pins located nothing.
- **J7-R float.** A printed, per-lens `lens_collar` clamps the lens on its fixed rear band (Kowa knurl dia 42) with a
  45 deg cone that sets its axial position, and is anchored on the tub front wall: 3 M3 x 10 screws (s_c1..s_c3) in
  brass heat-set inserts + a compression foot; the pinch s_c4 (M3 x 16, from above) is the last operation on the lens.
  The camera hangs on the lens and touches no printed part at any back-focus setting; the tub lip, a hood roll fin and
  the panel keeper are catches with gaps (`j7_float`: body 0.40 axial / 0.80 lateral, BFAR 0.50 / 0.75, adapter
  0.825). Pins and turret deleted; tripod block off at bench step B0.
- **Checks:** `j7_float`, `lens_support`, `lens_clamp`, `inserts` (J7 required); the r4 checks built on the wrong
  camera model were replaced by real-model equivalents (RECTIFICATION r5); `boss_geometry` and the PT counts are
  PT-only. 4 WARN rows, listed not blocking: no lens band is measured yet (3), and the Kowa's computed slip moment
  0.170 N m is below its 5 g knock moment 0.286 N m (static ratio 2.97 >= 1.5; aim only, it recovers).
- **STLs vs r4:** changed `tub` (96.6 g), `hood` (51.7 g, no turret), `panel` (keeper moved); new `lens_collar` (Kowa
  17.0 g, about 0.95 h; Fujinon 18.6 g) and 3 tub modifier meshes; the rest byte-identical. Coupons: + 3 for G-COL-1;
  `hood_ledge_ret` re-triangulated only (same volume). Printed total about 297 g / 16.0 h (estimates).
- **Balance:** Kowa 895 g, CoM +1.5 ahead of the grip axis (r4 +3.7); Fujinon 782 g, -9.8 (r4 -8.9). Rules unchanged.
- **Gates:** G-CAM-1 rewritten as MP-CAM (with its lens line, G-LENS extended); new G-COL-1 (collar coupons) and
  G-CAM-2 (sag acceptance on the assembled camera: corner-vs-centre focus change <= 4 um under 3x lens mass, a 15 N
  side push, 50 g on the cover, 1 h at 50 C). Plan B (housing clamp) documented only.

**What the user must do first (bench, in this order):** (1) MP-CAM: measure the camera against `CAM`, take the tripod
block off and confirm nothing is left below r 18, set the back focus with the Kowa at infinity and record s;
(2) G-LENS: confirm the Kowa knurl does not move when focus and iris turn (dial <= 0.02) and measure it (OD, position,
chamfer, thumb screws, CoM); the same for the Fujinon (its band is assumed); (3) only then print the G-COL-1 coupons
and run them (they replace the clamp estimates); (4) after assembly, G-CAM-2. Any measured difference: update `CAM` /
`LENSES`, rebuild, re-run (s9).

**r5 verification (2026-10-06 16:50-17:02, time-boxed, read-only; `research/r5-lens-support/verify/review_*.md`):**
- Three independent reviewers (geometry and physics; assembly and manufacturing; code, check integrity and docs) found
  **no blocker or major issue**.
- **Confirmed by them:**
  - The camera model matches the GS drawing.
  - The Kowa ring order is corrected.
  - The build order and driver audits hold.
  - There is finger room to hold the camera through the open left side.
  - No r4 check was weakened, and the 4 new checks FAIL on planted faults.
  - The regression tests pass 38/38, `make_tables --check` is clean, and the receipt re-hashes.
- **Not yet fixed (next session, then re-run the s9 release sequence):**
  - G1: add a sensor-plane datum and derive s_nom from it.
  - G2: MP-CAM measures C flange to cover rear directly, because the drawing's 5.8 adapter element may close the
    keeper gap at s_max.
  - G3: G-LENS must update `LENSES` support x0/x1 and rebuild before the tub and panel are printed; the float gaps sit
    at their rules.
  - G4: anchor torque 0.25 N m is high for short heat-set inserts. Use 0.10-0.15 N m, or add a pull-out step to
    G-COL-1.
  - G5: the bolted anchors alone do not enclose the lens axis; the pass relies on the compression foot LR. Add a
    prying factor.
  - A1: the s_c4 washer seat has zero clearance.
  - A2: add a sacrificial bridge layer over the ear counterbores.
  - A4: at bench B0, set back focus with the tripod block still on and the camera clamped, then take it off.
  - F1: under J7-R, any lens without a collar should FAIL, whatever its mass.
  - F2: `j7_float` should downgrade to stub only when every offending obstacle is a stub.
  - F3: port the planted-fault probes into `test_r3_regressions.py`.
  - Notes G6-G9, A3, A5-A8, F4-F6 are in the review files. F4 (the DESIGN pin row) and F5 (an r5 note in
    LENS-M12-ANAMORPHIC) were done at 17:05, outside the hashed docs.

**Still open, unchanged in kind:** every physical gate, G-W12 power, airflow (paused), the named CAD exceptions.

## 0b. r4 (2026-10-05 evening): what changed (history; its build numbers are superseded by s0)

r4 receipt (now `out/_r4-2026-10-06/build-receipt.json`), built **2026-10-05 21:51:07 +0800** (Kowa, `--sweep-step 1.0`): **23 of 23 categories,
593 rows = 581 pass + 12 info + 0 fail**, 0 stubs, `cad_release_candidate` true; checks.json SHA-256 `c820ef01...`;
16 of 16 sources, 91 of 91 outputs and 4 of 4 gate docs match the files on disk. Fujinon `out/_fujinon-r4` (21:45:35,
`--fast`, 1 mm): 23 of 23. **Geometry: unchanged** (every production and coupon STL, r4: 11 + 24, byte-identical to the
r3 release; the Fujinon STLs also identical). Tests `test_r3_regressions.py` 31 of 31; `make_tables.py --check` stale
none, lint 0; BOM 62 purchased lines, 0 uncovered. Evidence: slicer 11, coupons 9, measured 17, assembly 25 items, all
"not run"; 53 gates listed, 51 open, 2 withdrawn.

**What r4 added:**
- **Wiring:** a computed `cable_routes` check (continuity of every route's keep-out chain with a passage of at least
  1.0 x 1.0, both ends reaching their parts, estimated length + allowance within the cable; bend radius is still a bench
  item). It found 6 weak joints (gaps of 0.1, 0.2, 2.0, 10.0, 1.0 and 0.2 mm, and a run-lead edge contact 4 x 0.4 mm);
  6 link keep-outs close them (KEEPOUTS 27 -> 33; keep-out pairs 81 -> 97, all clear; sweeps still pass). Tightest
  cable: the QT lead, 17.4 mm over route + allowance.
- **Pigtail fuse (WIRING W-10):** Littelfuse 0251015.MXL, 15 A very fast, in the + conductor near the XT30 female,
  drawn in the `xt30_pair` proxy under the plug pair (so the pack-insertion sweep sees it). Pack protection requirement
  R-PACK-BMS (WIRING s4.7); G-W1 adds 10 plug-ins, G-W5 the sleeve temperature and the drop with the fuse (estimate
  0.135 V against 0.15 V: only 15 mV in hand). +1 part, +2 joints (12 joints).
- **Print:** 15 slicer modifier meshes `out/stl/modifiers/<part>__mod_<id>.stl` (tub 7, panel 4, base_grip 4; the
  FASTENER-POLICY 40 % rule round every pilot; the panel bosses had none before), checked by `print_modifiers`, hash-
  linked, and required in slicer-review records. PRINT-GUIDE s1.1; DRAFT label removed; SPEC s9 rib_l row applied.
- **Option C made concrete, not adopted:** WIRING s4.8 now names TI TLV75801P (adjustable, 4.553 V with 11.5 k / 1.58 k
  0.1 %, band 4.459-4.638 V from datasheet limits) as the primary candidate and Torex XC6220B45BPR-G as the fixed
  alternative (no stock); XC6210 rejected. No candidate blocks reverse current: G-W7 (c) with the regulator decides.
  BOM D2-16R/D/C/P at quantity 0. Research with sources: `electronics/gs8-d2-v1/RESEARCH-r4-fuse-ldo.md`.
- **Audit 2026-10-05-r3 answered:** malformed record types are rejected, not a crash; an FR_JOINTS-only replacement
  waives nothing; G-SNAP-2 / G-KEEP-1 / G-PANEL-1 are split into coupon items and `/whole` assembly items bound to every
  production STL; G-W13 (e) uses a defined off rail; "met by design" withdrawn; the hood removal direction (+Y), the
  keeper coupon gap (0.15) and the tool count (12 -> 11) corrected in FR1; the airflow tables carry a partial-output
  banner (study still paused, nothing re-run).

**Decisions for the user (now with concrete parts):** the lens; the black band; OPTIONS (b) (OPTIONS (a) was declined
by the user on 2026-10-05: the 18/24 stays a physical switch);
purchase variants; EVF feed A (diode, G-W6 expected to fail) or C (TLV75801P carrier); the FR1 joints. **The fuse was
decided in r4** (a second protection layer, +1 part); remove it only if the pack itself carries a second protection
element (R-PACK-BMS item 6 in the research file).

**Still open, unchanged in kind:** every physical gate (51 open), G-W12 power (27 W planning peak vs 25.5 W), airflow
(paused, inconclusive), the named CAD exceptions (cap detent strip, hood web 1.08, s_k2 wall 1.6).

## 1. State at r3 (baseline release; build numbers superseded by s0)

Receipt `out/build-receipt.json`, built **2026-10-05 16:53:58 +0800** (Kowa lens, `--sweep-step 1.0`, after the
LED-removal and rib-tip decisions), `checks.json` SHA-256 `0e0de579d234021f65068ec741fc59e548ecf8144f868e3d5c7e6498d479b6f1`.

| `status_states` | Status |
|---|---|
| `cad_checks` | computed: pass, 21 of 21 categories, 552 rows (542 pass, 10 info: 3 G-CAP-1 flexures, the J6 cap joint, 6 named exceptions; 0 fail), 0 stubs, unclassified thin spots none |
| `slicer_review` | **not run** (0 of the r3 printed parts (11); no slicer on this machine) |
| `coupon_validation` | **not run** (0 of 9 items: 6 coupon gates + G-KNOB-1, G-COMB-1, G-J4-1; the r3 coupon set (24) exported) |
| `measured_fit` | **not run** (0 of 17 gates) |
| `assembly_operation` | **not run** (0 of 22 gates, incl. G-W13) |

`cad_release_candidate: true` means only that the computed CAD checks on proxies pass and no printed part is a stub.
Second run: Fujinon lens, 1 mm sweeps (`out/_fujinon-r3rib`, 16:45:57): 21 of 21 (`out/checks-fujinon-sweep1mm.json`).

**What changed in r3:**
- **Geometry (from the audit corrections): none.** The audit corrections left every production and coupon STL (r3: 11 + 24)
  byte-identical to the r2 build of 03:39:36 that the audit validated (release of 13:02 and 16:15).
- **User decision: blunt the `rib_l` gusset tip to a 1.2 land** (the only geometry change in r3; release built 16:53:58 after the user's rib-tip decision: the tub gusset `rib_l` tip is blunted from a 0.60 mm knife edge (x -13) to a 1.2 land (x -12.1); new structural probe `tub_rib_l_tip` (land class, min 1.2) in J7_camera measures 1.25 at all 5 rays; dense scan minimum 0.598 -> 2.384 mm. Trial `out/_trial-r3-rib` and release both 21 of 21.)
  Now every production STL but the tub (10 of the r3 set of 11) and every coupon STL but one (23 of 24) are
  byte-identical to r2; `tub.stl` (0d4bbca8) and
  `coupon-pi-keeper-tub.stl` (e0325d05, its tub cut contains the tip) differ only at the rib_l tip. Not yet applied:
  the SPEC.md s9 rib_l row text (NOTES "r3 rib-tip"; SPEC is hashed, so it waits for the next release rebuild).
- **Checks and evidence:** structured evidence records bound to the hashes of the tested files; pass / fail / conflict
  / stale / rejected / not run kept visible; calibration records G-KNOB-1, G-COMB-1, G-J4-1; strict category summaries;
  origin-always probes with declared exclusions; 12 required load-path joints. 27 regression tests pass.
- **Documents:** service isolation P1-P4 before any internal electronic service (ASSEMBLY s7); counts from one source
  (DESIGN s1.1, linted by `make_tables.py --check`); EVF feed requirement R-EVF-REG and gate G-W13 (WIRING s4.8).
- **User decision: no LED indicators.** I/O is the exposure dial, the 18/24 dial, the power plunger, the record button
  and the EVF. The plunger is printed in black ASA (no light pipe); the Pi onboard LEDs are set off in config.txt
  ([to confirm on the bench], G-W3); procedures read the EVF. No geometry change.

**Has a test plan, not a result:** every coupon, calibration record, measured part, slicer review, bench power gate,
EVF bench gate, assembly and service cycle in s7. **Measured: nothing.**

**Estimates, not measurements:** printed mass about 293 g and print time about 15.7 h (volume model, not a slicer);
camera about 887 g (Kowa) or 772 g (Fujinon); CoM 3.7 mm ahead of the grip axis (Kowa) or 8.9 mm behind it (Fujinon).

## 2. What D2 is now (r2 geometry; r5 additions in s0)

12 printed parts since r5 (tub, panel, hood, base_grip, cap, pi_keeper, plunger, 2 knobs, eyecup, stick_sleeve, and
r5's lens_collar); 4 M3 lens-collar screws in heat-set inserts (r5); 7 PT 3.0 x 12
PH1 screws: 4 enclosure, 2 Pi keeper, 1 base lock (s_j); UPS kit 8 M2.5 screws + 4 standoffs (separate); 20 COTS
proxies; 10 harnesses; 10 solder joints (+2 if the pack lacks an XT30; under EVF-feed option C the diode is replaced:
+3 parts, +11 joints). Counts: DESIGN.md s1.1. The panel opens with 4 screws; the Pi stack sits under a screwed keeper
plus a hood post over the far corner; the hood comes off with 2 release pins and a lift; the EVF board has a +Y stop;
the battery cap is tool-free.

## 3. FR1 fastener-reduction candidate (exploratory, NOT adopted)

`candidate-fr1/` is a separate fork; the baseline release and its exports are unchanged. Every joint change is under
the `D2_FR` toggle (`all` = panel + keeper + hood=yslide; `none`; single joints; comma lists), and `D2_FR=none`
rebuilds every r2 production STL (11 at r2) byte-identically. Rough joint geometry, 33 explanatory views (20 FR views + 13 "before"
views: `candidate-fr1/out/renders/fr1-index.md`), coupons and the full argument are in `candidate-fr1/CANDIDATE.md`.
It still carries the r2 rib_l tip and the r2 LED wording; it inherits both user decisions on adoption.

**Before / after** (computed from the layout by `fr1_counts.py`; CANDIDATE s7):

| | r2 baseline (`none`) | FR1 recommended (`all`) | 5-screw alternative (`panel,keeper,hood=screw1`) |
|---|---|---|---|
| PT body screws | 7 (s_b1, s_b2, s_r1, s_r2, s_k1, s_k2, s_j) | 4 (s_r1, s_r2, s_k2, s_j) | 5 (s_r1, s_r2, s_k2, s_j, s_h1) |
| UPS kit M2.5 screws / standoffs (separate) | 8 / 4 | 8 / 4 | 8 / 4 |
| printed parts | 11 | 11 | 11 |
| purchased lines (COTS rows) | 21 | 21 | 21 |
| loose release pins (service tool) | 2 | 0 | 0 |
| tools, full ASSEMBLY s1.1 toolset (r4: was a 9 -> 8 keyword subset) | 12 (incl. release pins) | 11 (pins gone) | 11 |
| assembly steps | 10 | 10 | 10 |
| hood flexures | 4 | 0 | 4 |

**Service sequence.** Every internal electronic service starts with ASSEMBLY s7 P1-P4: shut down (EVF shutdown screen,
then dark, wait 5 s), cap off, pull the pack, unplug the XT30. A halted Pi is not isolation; the fitted-pack sweeps are
geometry evidence only. Action counts including those 4 steps (r2 -> FR1 `all`): panel off 9 -> 7 (s_r1, s_r2 from the
right only; no base screws, so the tripod plate stays on); hood off 25 -> 22 (push the hood 2.5 mm toward the open
left side, +Y, then lift; r4: was misstated as "toward the right wall", which is the locking direction; no pins,
no tool); Pi stack out 30 -> 27 (s_k2 out, the keeper backs out of its seat). With hood=screw1:
7 / 24 / 28 (s_h1 out, then lift). Reassembly is the reverse, pack last.

## 4. Validation results (computed only)

| build | D2_FR | mode | built | categories | rows (pass / info / fail) | critical features (pass / info / fail) | STLs vs r2 |
|---|---|---|---|---|---|---|---|
| baseline `out/` | (release) | full, 1 mm | 16:53:58 | 21/21 | 542 / 10 / 0 | 109 / 10 / 0 | 10/11 identical; tub changed (rib_l tip) |
| baseline `out/_fujinon-r3rib` | (Fujinon) | --fast, 1 mm | 16:45:57 | 21/21 | | | tub changed (rib_l tip) |
| `candidate-fr1/out/` | all | full, 1 mm | 15:26:25 | 21/21 | 534 / 10 / 0 | 126 / 10 / 0 | base_grip, hood, panel, pi_keeper, tub changed |
| `candidate-fr1/out/_none` | none | --fast, 2 mm | 15:37:51 | 21/21 | | 108 / 10 / 0 | 11/11 identical |
| `candidate-fr1/out/_int-pks1` | panel,keeper,hood=screw1 | --fast, 2 mm | 15:44:56 | 21/21 | | 126 / 10 / 0 | 5 changed |
| `candidate-fr1/out/_int-panel-r3m` | panel | --fast, 2 mm | 15:50:30 | 21/21 | | 118 / 10 / 0 | 3 changed |
| `candidate-fr1/out/_int-keeper-r3m` | keeper | --fast, 2 mm | 15:57:44 | 21/21 | | 114 / 10 / 0 | 2 changed |
| `candidate-fr1/out/_int-hood-yslide-r3m` | hood=yslide | --fast, 2 mm | 16:21:14 | 21/21 | | 110 / 10 / 0 | 2 changed |
| `candidate-fr1/out/_int-hood-screw1-r3m` | hood=screw1 | --fast, 2 mm | 16:28:05 | 21/21 | | 110 / 10 / 0 | 2 changed |

All candidate rows use the current fork checks (the corrected r3 checks plus one fork-only computed row,
`no_release_required`, which replaces the empty release_access category when the hood has no pins; a forced run on
`none` fails all 5 of its conditions). In every build the only non-pass joint is J6_cap_grip (`info`, G-CAP-1), as in
the baseline. The two hood=screw1 builds list one unresolved info row: the r2 rib_l tip (tub t 0.98 at
(-12.95, 31.85, 20.75)), present in every state including r2, and the subject of the user's rib-tip decision. Full
table: `candidate-fr1/out/fr1-validation.md`. Coupons: the FR-state coupon set (24 in the fork), all watertight by trimesh.

## 5. Open items

**Named in CAD (no check fails on them):** the cap detent strip 1.25-1.5 (gated flexure, G-CAP-1); the hood
plunger-channel web 1.08 (1.2 nominal); s_k2 is a marginal M3-insert site (wall 1.6, exactly the minimum). r5: the
`lens_support` WARNs (no lens band measured) and the `lens_clamp` Kowa 5 g WARN (until G-COL-1).

**Hardware gates: 55 listed in the receipt (r5), 53 open, 2 withdrawn (G-SNAP-1, G-SKIRT-1).**
- Coupons: G-PT-1, G-KEEP-1, G-SNAP-2, G-PANEL-1, G-CAP-1, G-EVF-2, (r5) G-COL-1, and the calibration records G-KNOB-1, G-COMB-1,
  G-J4-1 (PRINT-GUIDE s6.1).
- Measured parts: G-MP-PACK, G-MP-X1203, G-MP-EVF, G-MP-FPC, G-MP-ENC, G-MP-SW, G-MP-STICK, G-CAM-1, G-HDMI, G-RUN-1,
  G-ENC-1, G-PI-1, G-PLG-1, G-LENS, EVF-G1, EVF-G7, EVF-G8 (r5: G-CAM-1 and G-LENS are MP-CAM with its lens line).
- Electrical and operation: G-W1..G-W13 (G-W13 only with EVF-feed option C), (r5) G-CAM-2, G-EVF-1, EVF-G2..G6, EVF-G4b, EVF-G9,
  G-FPC-1 (option b only).
- FR1 only (not in the release gate docs until adopted): G-FRP-1 (panel keys), G-KEEP-1r (keeper seat), G-YSLIDE-1
  (hood slide), plus G-J4-1 with the FR panel fitted.

## 6. Decisions for the user

**Release options:** (1) lens Kowa LM6HC (default) or Fujinon HF6XA-5M (r5: each has its own collar; both builds pass); (2) black band 8 mm base or R2's finding-3
option (b) (NOTES "r2 R2 options"; +2 printed parts); (3) OPTIONS (a) 18/24 in the encoder push menu: DECLINED by the user 2026-10-05 (keep the switch); (4) OPTIONS (b)
shorter FPC (length at G-FPC-1); (5) purchase variants (MEASURED-PARTS); (6) EVF feed: option A diode (G-W6 expected to
fail the 4.90 V bound) or option C 4.55 V LDO as the primary feed (WIRING s4.8, recommended candidate; G-W13 first).

**FR1 joint options (choose per joint; each is a computed pass and physically unverified; adopt only after its gate):**
1. **Hood: `yslide` (recommended), `screw1`, or keep `pins`.** yslide removes the 2 loose pins, the 4 flexing hooks and
   the 2 wall holes with no screw and no tool; cost: a 2.5 mm transverse push, a printed key fit G-YSLIDE-1 must
   confirm, and a widened plunger channel that opens the inner 1.2 mm of the microSD slot over 1.1 mm (card guidance
   unverified). screw1 trades the pins for one visible PH1 screw (s_h1) and keeps 4 spring hooks. Keep pins only if
   G-YSLIDE-1 fails.
2. **Panel: A2 keys + 2 screws (recommended if G-FRP-1 passes), or keep 4 screws.** One drive direction, no base
   screws, the tripod plate stays on. Costs: an ESTIMATED softer seam between the keys (0.001 -> 0.057 mm/N), a bottom
   edge that is keyed rather than screwed (G-FRP-1), and **less in-use grip retention**: s_b1/s_b2 also held the base in
   X, so with A2 the lock screw s_j alone holds the base in the unlock direction (G-J4-1 with the FR panel fitted).
3. **Pi keeper: keyed seat + s_k2 (recommended), or keep s_k1 + s_k2.** 2 -> 1 screw and a shorter finger lever, no new
   tool; adds one printed 0.15 fit (G-KEEP-1r) and keeps the hood stack-stop post.
4. **Base/grip lock: retained** (T tongues + s_j). Not removed, so panel retention is never the only base lock; a
   screw-free J4 latch is a later study.
5. **Battery cap: unchanged** (dovetail keys + detent, tool-free, G-CAP-1).

Result: PT body screws 7 -> 4 with all recommended options (`D2_FR=all`), or 7 -> 5 with screw1. UPS kit unchanged.
On adoption: port the chosen toggles into the baseline sources, add `no_release_required` (or an equivalent) to the
baseline `checks.py` if the hood loses its pins, write the FR gates into the release gate docs, take the rib-tip and
LED changes, and rebuild the release.

## 7. Remaining physical gates, in order

Evidence for every step: one structured record per item as `evidence/README.md` describes (copy
`evidence/_record-template.json`): `item` = the part id or gate id, `state`, `artifacts` = {path: sha256 of the file
actually sliced, printed or tested}, `profile`, `verdict` pass|fail, `date`, `by`; photos and notes are attachments
named in `notes` (file names are never matched). A coupon record names every coupon STL of its id; an
`assembly_operation` record names the gate's doc and every production STL.

**Step 1. Decide and order.** Decide s6 release options 1, 3, 4, 5 and 6 (they change what is ordered) and, if wanted,
the FR1 joints (they change what is printed). Order from `electronics/gs8-d2-v1/BOM.md`. Nothing has been bought.

**Step 2. EVF bench first (MP-EVF), before any carrier freeze:** EVF-G1 identity; EVF-G7 panel release (stop if
bonded); EVF-G8 flex; EVF-G4 power range; G-W7, then EVF-G2; the jig with the real plug and leads, then G-MP-EVF and
G-EVF-1. EVF feed: option C = G-W13 on the regulator carrier, then G-W6 on the regulated lead; option A = G-W6 on the
G-W4 bench feed (a fail is likely and leads to option C).

**Step 3. Measured parts** (MEASURED-PARTS): MP-PACK (and G-W1), MP-X1203 including the cooler line (G-W2, G-PI-1),
MP-CAM with its lens line (r5: bench step B0, G-CAM-1, G-LENS; before any lens collar is printed), MP-HDMI, MP-FPC; then MP-RUN, MP-ENC, MP-SW, MP-STICK.

**Step 4. Power on the bench:** G-W3, G-W4, G-W5 (10 min at 8.6 A on an electronic load), G-W6 (step 2), then
**G-W12** on the real stack and loads (WIRING s9: the 27 W vs 25.5 W question; the 17.7-22.1 W figure is an
estimate). G-W12 stays open until measured.

**Step 5. Update geometry only where a measurement differs** (MEASURED-PARTS "If it fails"); rebuild, then re-run
`make_coupons.py`, `coupons_r1.py`, `make_tables.py`, `make_bom.py`.

**Step 6. Slice** every production STL with the PRINT-GUIDE settings (`slicer_review`: item = part id, artifact
`stl/<part>.stl`; note slicer, version, time, filament and warnings).

**Step 7. Coupons and calibration records** (`out/stl/coupons/`, PRINT-GUIDE s6): `clearance_comb` (G-COMB-1) and the
2 knob-bore ladders (G-KNOB-1) first; then G-PT-1; G-KEEP-1 on the real X1203 kit; G-SNAP-2; G-PANEL-1; G-CAP-1;
G-EVF-2; `tongue` + `keyhole_slot` (G-J4-1); (r5) the collar coupons (G-COL-1) after G-LENS. For adopted FR1 joints, the FR coupons in
`candidate-fr1/out/stl/coupons-fr/`: G-FRP-1, G-KEEP-1r, G-YSLIDE-1 (CANDIDATE s9).

**Step 8. Print the full set and dry-assemble** per ASSEMBLY s2 (bench B0, B1, then steps 1-9), no pack. r5: then
G-CAM-2 (sag acceptance) on the assembled camera.

**Step 9. Service cycles**, each starting with ASSEMBLY s7 P1-P4 and closing with the pack last: hood 5 times
(G-SNAP-2, or G-YSLIDE-1); keeper 5 times on the real stack, then the far-corner tilt test (G-KEEP-1 follow-up);
panel 5 times with the strap fitted.

**Step 10. Electrical, closed body:** G-W8, G-W9, G-W10, G-W11, G-W12 again in the closed body, then the powered
recording test.

The receipt reads the evidence records but never judges them. A state stays open until every item it needs has a
current recorded pass; failed, conflicting, rejected and stale records stay listed in `open_evidence`.

## 8. Cooling (airflow study)

A separate basic airflow study of the fan with the existing arrangement (user request 11:20) lives in
[`airflow/`](airflow/) (brief `airflow/AIRFLOW-BRIEF.md`, state `airflow/NOTES.md`). The user paused it at 14:20 and
later asked to continue it; when this handoff was written (17:00) the report `airflow/AIRFLOW.md` did not
exist yet, so the report is **pending**. Results so far are partial: network estimates and a first 3D pass in
`airflow/out/`, unverified. Whatever it reports, it is a **basic simulation, not a measurement**: the Pi fan curve is
not published, so fan, vent and thermal numbers are estimates. **G-W11 (thermal) and G-W12 (power workload) stay
open** until measured on the real stack in the closed body.

## 9. Commands (repo root; CadQuery only through `run_locked.py`, in the foreground)

1. `.venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/build_d2.py --sweep-step 1.0`: full
   release build. Fujinon: `--lens fujinon_hf6xa --fast --sweep-step 1.0 --out cad/gs8-d2-v1/out/_fujinon-<tag>`;
   copy its `checks.json` to `out/checks-fujinon-sweep1mm.json` **before** the main build, so the receipt hashes it.
2. `... run_locked.py -- cad/gs8-d2-v1/make_coupons.py --out cad/gs8-d2-v1/out` and
   `... run_locked.py -- cad/gs8-d2-v1/coupons_r1.py --out cad/gs8-d2-v1/out`, both before the main build.
3. `python cad/gs8-d2-v1/make_tables.py` (then `--check`) and `python electronics/gs8-d2-v1/make_bom.py`.
4. Tests (no CAD lock): `.venv-cad/Scripts/python.exe -B cad/gs8-d2-v1/test_r3_regressions.py`.
5. FR1: `D2_FR=<sel> .venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py --max-wait-min 4 --
   cad/gs8-d2-v1/candidate-fr1/build_d2.py --fast --out cad/gs8-d2-v1/candidate-fr1/out/_<tag>`.
