# GS8 D2 r2 rectification record (`cad/gs8-d2-v1`)

Response in CAD and documents to the external audit `audit/d2-readiness-2026-10-04/REVIEW.md` (baseline: the r1 build
receipt 2026-10-04 14:15:51). Work done 2026-10-05 00:00-01:40 machine time (UTC+8) by R1-R4 and the integrator, then
a **fixer pass 02:00-03:40** on the findings of 2 verifiers (M-V-MPS-1..9 mechanical, E-V-E1..12 evidence/electrical).
Brief: `RECTIFICATION-BRIEF.md`; working notes: `NOTES.md` ("r2 ..." sections). The reviewer-facing summary is
`audit/d2-readiness-2026-10-04/RESPONSE.md`.

**What "pass" means here.** Every value below is computed on CAD solids and purchased-part **proxies**. Nothing was
printed, sliced, bought, measured, assembled or powered. Unrun tests are "not run". No gate was closed by changing a
threshold, and no physical test was replaced by a calculation.

## Build state

**History (r2).** This section records the r2 build that the 2026-10-05 audit validated; it is kept as history. The
current release state (r3: audit 2026-10-05 corrections, the same production STLs (11) byte for byte, more rows, the
G-KNOB-1 / G-COMB-1 / G-J4-1 records, G-W13, per-joint coverage) is in `DESIGN.md` s1 and s3 (generated from the
current receipt) and `HANDOFF.md` s1. The r2 receipt is kept in `out/_r2-2026-10-05/`.

Receipt `out/build-receipt.json` (r2, now `out/_r2-2026-10-05/build-receipt.json`), **built 2026-10-05 03:39:36 +0800** (Kowa default, full build), `checks.json`
SHA-256 `acbc586777a5a6759d2b407263d7fa9665c60a5969fdec25fd592a86f7c18fb4`. The values below are from that build.

| State (`status_states`) | Status |
|---|---|
| `cad_checks` | **computed: pass**: 21 of 21 checks, 526 rows, 0 failed, 0 stubs; `cad_release_candidate: true` (a CAD state only) |
| `slicer_review` | not run: 0 of the r2 printed parts (11) with a recorded verdict (no slicer on this machine) |
| `coupon_validation` | not run: 0 of 6 coupon gates (the r2 coupon set (24) exported, none printed) |
| `measured_fit` | not run: 0 of 17 gates |
| `assembly_operation` | not run: 0 of 21 gates |

Second run: Fujinon lens, 1 mm sweep steps, run 03:34 on the same sources: every check passes
(`out/checks-fujinon-sweep1mm.json`, SHA-256 `15ad0fbd...`, hash-linked in the receipt `files`). r1 outputs:
`out/_r1-2026-10-04/`, `baseline-r1-2026-10-04.zip`; the integrator's 01:32 r2 JSONs: `out/_r2-integrator-0132/`.
Read-only re-check after the build (a scratch script modelled on the reviewer's `check_artifacts.py`, which was not
run because it writes into the audit folder): 16 source, 64 output and 4 gate-doc SHA-256 values match the receipt;
the r2 STL set (11 parts + 24 coupons) is watertight, consistently wound and of positive volume.

| Count | r1 | r2 (01:32) | **r2 final (03:39)** |
|---|---|---|---|
| Checks / rows | 15 / 393 | 19 / 496 | **21 / 526** (+`release_access`, `stack_retention`) |
| Printed pieces | 12 | 11 | **11** (-2 skirts, +`pi_keeper`) |
| PT 3.0 x 12 PH1 screws | 4 | 6 | **7** (+s_k1, s_k2; +s_j, the J4 lock) |
| Snap latches with no release access | 4 Pi hooks + 1 skirt barb | 0 claimed; the hood's 4 were unmodelled (M-V-MPS-2) | **0, modelled**: hk1/hk2 pin hold-open (`release_access`), hk3/hk4 45 deg return (`removals` hood_off) |
| Critical-feature entries (structural) | none | 74 | **87**, graded by feature class |
| Hardware gates in the receipt | | 34 | **46** (44 open, 2 withdrawn): + EVF-G1..G9, G4b, G-MP-FPC |
| Mass / CoM ahead of the grip axis (Kowa, estimate) | 880 g / +4.0 | 883 g / +3.7 | **887 g / +3.7** |
| Mass / CoM (Fujinon, estimate) | 765 g / -8.7 | 768 g / -9.0 | **772 g / -8.9** |
| Print estimate (manifest model, not a slicer) | 288.5 g, about 15.5 h | 289.3 g, 15.5 h | **292.9 g, 15.7 h** |

## Per finding

### 1. Pi service is destructive: **accepted** (CAD rectified; physical gates open)

- **Changed.** R1: the 4 floor snap hooks are deleted; a removable printed `pi_keeper` on 2 PT screws (s_k1, s_k2, same
  PH1) holds the stack, which is located only by its 4 boss pockets. Fixer: s_k2 re-sited (y 28.25, r 3.6; its wall
  was 1.75 over the top 2 mm); the hood (which must come off first) is now removable without breaking anything:
  hk1/hk2 get 2 pin release holes (hold-open), hk3/hk4 a 45 deg return catch; a hood post stops the far corner of the
  stack 0.15 above the far kit screw head (the 4 fingers sit on 2 adjacent edges); the keeper bridge clears the panel
  bosses by SLIDE. ASSEMBLY s7 items 8-10 give the procedure and the full toolset (PH1, 2 release pins, tweezers, ESD).
- **Evidence.** `removals` hood_off (release zones hk1-hk4 only), keeper_out, pi_out: 0 hits; coverage rows pass.
  `release_access` pin_hk1/hk2: 0 mm3 on any other part, strain at the 0.55 push 1.51 % (2.26 % with Kt; limit 2.5 %).
  `service_driver` s_k1/s_k2 pass. `boss_geometry` s_k1 2.55 / s_k2 2.35 over 5-95 % of the depth (need 2.25).
  `stack_retention`: CoM 16.7 mm inside the retention hull; lift at the pockets <= 0.19 (limit 1.9); post gap 0.15.
  `clearance` J9 keeper bridge 0.25. Sections `section-pi-keeper-*.png`.
- **Remains (not run).** G-KEEP-1 (whole keeper, tub floor coupon, 2 stand-in boards on the real X1203 kit: 5 full
  cycles), G-PT-1 (keeper bosses), G-SNAP-2 (hook coupons + 5 whole-hood remove/refit cycles), G-PI-1, and the
  review's repeated insertion/removal on printed parts.

### 2. Thin-wall pass does not establish local thickness: **accepted** (CAD rectified; print tests open)

- **Changed.** R3: `CRITICAL_FEATURES`, exact B-rep chords, missing-coverage FAIL; the share screen is secondary. R2: skirt
  necks and groove lips gone with J5; panel end land 1.30; cap retention fixes. Fixer: the minimum now comes from a
  **feature class** (hook, lug, lip, boss, wing, pin, neck, bar 1.6; wall, land 1.2), so an entry literal cannot lower
  it; a structural entry with no class fails. This lifted the hood tooth (land 1.0: 1.62), the tub ledges (1.65), the
  cap key head tip (1.65) and the panel boss cap (1.60). Added entries: s_k2 seam (2.35), EVF rails and groove ends,
  eyepiece collar, J4 lock boss, hood stack post; stick_sleeve and knobs carry a named rationale (`PART_RATIONALE`).
- **Exceptions, named.** Class `flexure` with a gate (G-CAP-1, not run): the cap detent strip 1.50 / 1.25 at the
  dimple / 1.275 at the front-corner exit, **below the 1.6 loaded rule**. Nonstructural: panel antirot skin 0.8,
  badge and "exposure" glyph ridges, the stick-rail lip tip, the hood plunger-channel web (1.08). A 0.25 feather in
  the tub rear wall at the panel seam (the eyepiece bore's teardrop roof running out through the seam plane) surfaced
  in the fixer builds and is **fixed**: the end face is notched 1.2 deep there. `unclassified_thin_spots`: none.
- **Remains.** G-CAP-1, G-PANEL-1, G-SNAP-2, G-KEEP-1 coupons: not run. The 2 geometry items above.

### 3. Panel opening depends on an inaccessible skirt barb: **accepted** (CAD rectified; physical gate open)

- **Changed.** R2: skirts and J5 eliminated; the panel = 4 PH1 screws + pull +Y. Fixer: J4 gets its own lock screw s_j
  (step 3), so panel service no longer frees the base (r2's s_b1/s_b2 were also the only J4 lock).
- **Evidence.** `removals` panel_off (strap, cap, pack, lens, stick fitted): 0 hits (r3: geometry evidence only, not
  permission to part a lead with the pack fitted; ASSEMBLY s7 P1-P4 comes first); `service_driver` s_b1/s_b2/s_r1/s_r2
  pass; `driver` s_j at step 3 pass (handle 2.35 from the strap); `boss_geometry` s_j 2.75.
- **Remains.** G-PANEL-1 (5 open/close cycles, strap fitted): not run. User decision: the black band (16 -> 8 mm).

### 4. Peak power 27 W > X1203 25.5 W: **accepted**; closure **dependent on hardware**

- **Changed.** R4: workload states S0-S4, restrictions R-P1..R-P8, fallback 4.5. Fixer: the S3 board estimate was below
  the published CPU-only figure; it is now 11-12.5 W [est] and an HDMI +5 V row (0.26 W) is added. The 4.4 rows are an
  **estimated envelope, not a bound: 17.7-22.1 W** (69-87 % of 25.5 W), only **0.8-2.3 W under the G-W12 P1 limit
  (22.9 W)** without the CPU cap; R-P3 (CPU cap) is now recommended. The fallback (4.5) lists the keeper re-derivation.
- **Remains.** G-W12 (P1-P7, failure actions named for every criterion): not run. Order: G-W6 before the EVF freeze,
  the print set, then G-W12 (B feeds through an XT30 into the real pigtail).

### 5. Component interfaces not frozen: **accepted, dependent on hardware**

- **Changed.** R4: `MEASURED-PARTS.md` records, G-MP-* gates; EVF bench assembly before the carrier freeze; G-W6 kept.
  Fixer: records that name only a class say **"variant NOT chosen: procurement decision (user)"** (pack, HDMI lead,
  run button, 18/24 switch, FPC length); MP-FPC and the Active Cooler height line added; EVF gates written EVF-G1..G9
  and listed in the receipt; G-W6 no longer waits for G-W12 and is expected to call for the regulated feed (+1 part,
  +2 joints, a BOM contingency; r3: withdrawn, replaced by EVF-feed option C, WIRING s4.8).
- **Remains.** Buy, photograph, measure; change only the geometry a measured difference touches.

### 6. EVF board +Y restraint not explicit: **accepted** (CAD rectified; real-board check open)

- **Changed.** R2/R3: panel stop rib, 6-direction `evf_restraint`. Fixer: r2's -Y arrest shared 29 % of its contact with
  the HDMI receptacle; the bottom rail now stands 1.0 clear of the receptacle and plug (gap y 3..18) and 0.6 off the
  plug envelope in +X, and the top rail is relieved over the ZIF. The check moves the plug envelope with the board,
  finds the first contact per zone and FAILs a connector/ZIF/plug zone within the PCB's first contact + 0.2.
- **Evidence.** First contact is the PCB in all 6 directions: +-X 0.25, +Y 0.30 (panel rib), -Y 0.31, +-Z 0.25; no
  connector, ZIF or plug zone within 0.45. Renders `section-evf-board-x137.png`, `-z78.png`.
- **Remains.** G-EVF-2 with the real board, plug and cables: not run.

### 7. Assembly simplicity weaker than the exterior suggests: **accepted**

- **Changed.** R4: OPTIONS (a) and (b) quantified, presented, not applied; (c) applied as finding 3; full toolset; no hex
  in the insert repair. Fixer: tool list corrected (the soldering count includes the A0 blob; the release blade is
  replaced by 2 pins); FASTENER-POLICY E has a per-boss drill table (r2's single depth drilled through the tub floor at
  s_k and the boss cap at s_b); s_k walls corrected (1.8 / 1.6); ISO 7045 M2.5 k is up to 2.1, above G-PI-1's 2.0
  (measure on receipt); the driver audit runs at each screw's own step (3, 4, 8). BOM: 7 PT screws, the `%%` header
  fixed, the regulated-feed contingency line.
- **Remains.** The user's choice on (a) and (b).

### 8. Release status needs separate physical evidence: **accepted**

- **Changed.** R3: `cad_release_candidate`, `status_states`, `open_evidence`, `hardware_gates`. Fixer: gate ids match as
  whole tokens (G-W1 no longer matches a G-W12 file); each state lists its required items (printed parts or gate ids)
  and stays in `open_evidence` until every item has a file with a recorded verdict line; the EVF-SELECTION gates are
  in `hardware_gates` (source hashed); DESIGN no longer says "print- and assembly-ready"; HANDOFF rewritten for r2.
- **Remains.** Nothing in CAD. Slicer review stays "not run" (no slicer installed; none downloaded).

## Fixer pass (verifier findings on r2)

| Id | Sev. | Result | Change and evidence |
|---|---|---|---|
| M-V-MPS-1 | blocker | fixed in CAD | s_k2 (-64, 28.25) r 3.6: wall 2.35 at every level; `check_bosses` samples 7 levels over 5-95 %; entry tub_keeper_boss_s_k2_seam 2.35 |
| M-V-MPS-2 | blocker | fixed in CAD; G-SNAP-2 open | pin release holes + 45 deg return; `removals` hood_off, camera_out, eyepiece_out, evf_out; "parts taken off" coverage; `release_access`; tool list; G-SNAP-2 adds 5 hood cycles |
| M-V-MPS-3 | major | fixed in CAD; G-EVF-2 open | rail cut back round the plug and ZIF; per-zone first contact, plug envelope moves with the board |
| M-V-MPS-4 | major | fixed in CAD; tilt test open | hood stack-stop post; `stack_retention` (hull margin 16.7, lift <= 0.19); without the post the LP gives 0.58 max |
| M-V-MPS-5 | major | fixed in CAD | J4 lock screw s_j (step 3); ASSEMBLY s7 items 3 and 11 |
| M-V-MPS-6 | major | fixed, 3 gated exceptions | feature classes; hood tooth, ledges, cap key tip, panel boss cap thickened; cap detent strip = gated `flexure` (G-CAP-1) |
| M-V-MPS-7 | major | fixed | G-KEEP-1 = whole keeper + floor coupon (both keeper bosses, 4 Pi bosses) + 2 stand-in boards on the real kit |
| M-V-MPS-8 | minor | fixed | bridge underside 12.85 over boss tops 12.6: 0.25; clearance zone J9 |
| M-V-MPS-9 | minor | fixed (per part, not per joint) | EVF rail/collar entries; `PART_RATIONALE` for stick_sleeve, knobs, plunger, eyecup; a per-joint coverage rule is not added |
| E-V-E1 | blocker | fixed | DESIGN s2 reworded; no other readiness claim in the D2 docs |
| E-V-E2 | major | fixed (document) | WIRING 4.2/4.4/4.7, W-9, s10: 17.7-22.1 W envelope, margin to P1 stated |
| E-V-E3 | major | fixed (document) | FASTENER-POLICY E per-boss table; s_k walls 1.8 / 1.6 |
| E-V-E4 | major | fixed | whole-token match; per-item verdict counts; `open_evidence` until all items have verdicts |
| E-V-E5 | major | fixed | EVF-G1..G9, G4b in `hardware_gates`; counts 46 / 44 open |
| E-V-E6 | major | fixed (document) | gate order; B through the XT30; actions for P3/P5/P6; regulated-feed contingency in BOM and OPTIONS |
| E-V-E7 | major | fixed (document) | variants marked as user decisions; MP-FPC; cooler line |
| E-V-E8 | major | fixed | HANDOFF rewritten from this receipt |
| E-V-E9 | minor | fixed | WIRING 4.5 lists the keeper re-derivation |
| E-V-E10 | minor | fixed | receipt time and checks.json hash cited above; Fujinon on final sources, hashed |
| E-V-E11 | minor | fixed | tool 2 wording; Pi-service toolset; FASTENER-POLICY G; ISO 7045 k 2.1 (Engineers Edge table) |
| E-V-E12 | minor | fixed | R-P8 "discharge"; G-W5 adds 10 min at 8.6 A; BOM `%%` |

## What is still failing or open

- **Failing CAD checks: none.**
- **Open in CAD (named, not failing):** the cap detent strip below 1.6 (gated flexure, G-CAP-1); the hood
  plunger-channel web 1.08; (r2: no per-joint coverage rule; r3 added one: 12 required joints, `CRITICAL_JOINTS` /
  `REQUIRED_JOINT_IDS`, the cap joint J6 reported as info because it rests on G-CAP-1).
- **Not run (all physical):** slicer review; the coupons (G-PT-1, G-KEEP-1, G-PANEL-1, G-CAP-1, G-EVF-2, G-SNAP-2, J4
  record, knob bores, clearance comb); measured parts (G-MP-*, EVF-G*, G-CAM-1, G-HDMI, G-RUN-1, G-ENC-1, G-PI-1,
  G-PLG-1, G-LENS); electronics G-W1..G-W12 (r3: G-W1..G-W13, G-W13 only with EVF-feed option C; the coupon
  calibrations now have ids G-KNOB-1, G-COMB-1, G-J4-1); dry assembly, service cycles and the powered recording test.
- **User decisions:** the lens; the black band (16 -> 8 mm); OPTIONS (a) and (b); the un-chosen purchase variants (pack,
  HDMI lead, run button, 18/24 switch, FPC length); (r3) the EVF feed: option A diode or option C 4.55 V LDO
  (WIRING s4.8).

## r3 (2026-10-05, follow-up audit)

Audit: `audit/d2-readiness-2026-10-05/REVIEW.md` (+ `artifact-audit.json`, `evidence-logic-audit.json`); response to the
reviewer: `audit/d2-readiness-2026-10-05/RESPONSE.md`. The r2 text above is kept as history. Working log: `NOTES.md`
"r3 checks", "r3 docs", "r3 electronics", "r3 integrate-baseline", "r3 fix-baseline" (25 verifier findings, all
fixed), "r3 led-removal", "r3 rib-tip". Every result below is a computed check or a document change. Nothing was
printed, sliced, bought, measured, assembled or powered on this machine, and nothing was committed.

**r3 build state (baseline).** Receipt `out/build-receipt.json`, built 2026-10-05 16:53:58 +0800 (Kowa, `--sweep-step
1.0`, after the LED-removal and rib-tip decisions): 21 of 21 categories pass; 552 rows = 542 pass + 10 info + 0 fail;
critical_features 119 rows = 109 pass + 10 info (3 G-CAP-1 gated flexures, the J6 cap joint, 6 named exceptions);
unclassified thin spots none; `cad_release_candidate` true (computed checks on proxies only); checks.json SHA-256
`0e0de579...`. The audit corrections alone left every production and coupon STL (r3: 11 + 24) byte-identical to the
r2 build that the audit validated (releases 13:02:27 and 16:15:58); after the rib-tip decision 10 of 11 and 23 of 24
are identical (tub.stl and coupon-pi-keeper-tub.stl differ only at the rib_l tip) (r2 outputs kept in `out/_r2-2026-10-05/` with SHA256SUMS). Fujinon 1 mm run
`out/_fujinon-r3rib` (16:45:57): 21 of 21. Evidence states: slicer_review not run (11 items),
coupon_validation not run (9), measured_fit not run (17), assembly_operation not run (22); 50 hardware gates listed,
48 open, 2 withdrawn. Regression tests: `test_r3_regressions.py` 27 of 27; `layout.py` self-check 129 of 0 failed;
`make_tables.py --check`: stale none, count lint 0, selftest ok.

**Geometry change in the baseline: none from the audit corrections.** One user geometry decision came later (NOTE 5,
16:25, "blunt the rib_l gusset tip to a 1.2 land"); its state is in "User decisions during r3" below.

### R3-1. Battery-connected service shortcut (REVIEW s1, high): **accepted** (documents corrected; physical gates open)
- Change: `ASSEMBLY.md` s7 now opens with the isolation prerequisite P1-P4 for EVERY electronic service route,
  panel-only included: P1 shut down (EVF shutdown screen, then dark, wait 5 s), P2 cap off, P3 pull the pack (the
  junction follows), P4 unplug the XT30. "A halted Pi is not electrical isolation" is stated. Initial assembly uses
  the same rule (s1 "Power last"; s2 step 10 fits the pack last); s6 microSD and s7 items 2-11 point to P1-P4.
  The same order is in ASSEMBLY s1/s6, FASTENER-POLICY, DESIGN, SPEC and the layout/checks scope note. No switch added.
- Fitted-pack clearance kept as geometry evidence only: the `removals` / `service_driver` rows whose state keeps the
  pack fitted (panel_off, hood_off, camera_out, eyepiece_out, evf_out) carry the `scope` field
  `layout.SERVICE_GEOMETRY_ONLY_NOTE` ("geometry only: electronic service still requires shutdown and XT30
  disconnection first", ASSEMBLY s7 P1-P4). The r2 panel_off line in "Per finding / 3" above is to be read that way.
- Evidence: release `removals` 11 of 11 and `service_driver` 6 of 6 pass with the scope text; HANDOFF step 8 starts
  every service cycle with P1-P4.
- Remains: dry assembly and service cycles with the real parts (HANDOFF s5); the halted-state rail and EVF behaviour
  are bench gates (G-W4, G-W8), not CAD.

### R3-2. Evidence bound to item and revision; failures stay visible (REVIEW s2, medium): **accepted** (code changed)
- Change (`build_d2.py`, `evidence/README.md`, `evidence/_record-template.json`, SPEC s6 item 10): one structured
  JSON record per tested item with `item` (exact part / coupon / gate id), `state`, `artifacts` = {path: sha256 of the
  file actually tested}, `profile`, `verdict`, `date`, `by`, `notes`. File names are never matched. A record counts
  only if its artifact hashes equal the CURRENT files (`required_artifacts_of`: a coupon record names every coupon STL
  of its id; measured_fit names the gate doc; assembly_operation names the gate doc and every `stl/<part>.stl`).
  Completeness and acceptance are separate: per item the outcome is pass, fail, conflict, stale, rejected or not run;
  a state closes only when every item has a current pass. Fail, conflict, stale, rejected, unmatched and unassigned
  records stay in `open_evidence` / `open_evidence_detail`. Calibration records registered: **G-KNOB-1** (knob-bore
  ladders), **G-COMB-1** (clearance comb), **G-J4-1** (tongue + keyhole fit) in `CALIBRATION_ITEMS`, PRINT-GUIDE
  s6.1, SPEC s6. `summarize()` rejects unknown row statuses, an info category needs at least one real pass and no
  unresolved row, and an empty category fails.
- Evidence: `test_r3_regressions.py` 27 of 27, among them the audit's cases: `test_file_names_are_not_evidence`,
  `test_stale_r1_record_is_stale`, `test_old_revision_production_record_is_stale`,
  `test_coupon_record_cannot_cover_production_part`, `test_failed_verdict_stays_open`, `test_conflicting_records`,
  `test_rejected_fail_beside_pass_stays_open`, `test_calibration_items_registered`, `test_unknown_status_rejected`,
  `test_info_only_category_does_not_pass`, `test_empty_category_fails`, `test_unknown_state_fail_record_stays_open`,
  `test_item_typo_keeps_state_open`, `test_measured_and_assembly_records_name_doc_and_stls`. The suite with
  `--against-r2` shows the defect in the r2 code for the comparable cases. Release receipt: 0 records, 4 states not run.
- Remains: no hardware record exists yet; every state stays "not run" until records are filed.

### R3-3. Critical-feature coverage (REVIEW s3, medium): **accepted** (code changed; no threshold changed)
- Change (`checks.py`, `layout.py` R3 block): the nominated origin ray is always measured whatever the span count; an
  origin outside material FAILs ("stale origin"). Span rays that miss the solid FAIL unless the entry lists them in
  `expect_outside` with a reason. Per-joint coverage: `CRITICAL_JOINTS` (12 joints: J1, J2, J3, J4, J6, J7, J8,
  J9 keeper, J9 stack stop, J12, J13 grip, J13 strap) and the fixed registry `REQUIRED_JOINT_IDS` (12); coverage fails
  if a required id is missing, unmeasured, non-pass, or non-structural without a named gate, if a load-bearing part is
  in no joint, or if the registry is absent. The cap flexures (1.25-1.50) stay G-CAP-1 gated exceptions, and J6
  reports `info`, not `pass`. 5 new probes (panel locate ribs 1.2 as locating walls, panel encoder side hooks 1.6,
  panel b2 cap 1.6, base s_b2 / s_j head floors).
- Evidence: `hood_groove_lower_lip` (4-ray span) origin is now measured: pass. The stricter rule exposed one silent r2
  miss, `tub_evf_groove_wall_bot_px` ray at -0.5 (the deliberate 5 V lead end relief); it is declared in
  `EXPECT_OUTSIDE` with that reason (the rays at y 2.0 / 2.5 measure 1.3); no origin was stale. Tests
  `test_even_span_measures_origin_and_stale_origin_fails`, `test_unexpected_missing_ray_fails_and_expect_outside_allows_it`,
  `test_deleted_joint_entries_fail`, `test_deleted_joint_with_its_probes_fails`, `test_joint_registry_required`,
  `test_flexure_is_gated_exception_not_ordinary_pass`, `test_joint_rejects_unknown_feature_status`,
  `test_baseline_joint_ids_fixed`, `test_baseline_registry_joints_complete`. Release: critical_features 119 rows,
  109 pass + 10 info, 0 fail (16:53:58; 118 = 108 + 10 before the rib-tip probe).
- Remains: probes measure the CAD solid, not printed strength (coupons and slicer review open).

### R3-4. Handwritten counts (REVIEW s4, low): **accepted**
- Change: `make_tables.py counts()` is the authoritative count source (generated block in DESIGN.md s1.1);
  `make_tables.py --check` now also runs a handwritten-count lint over every `cad/gs8-d2-v1/*.md` and
  `electronics/gs8-d2-v1/*.md` (briefs and NOTES skipped) with a selftest of the audit's r2 phrases. Fixed: OPTIONS
  6 -> 7 PT screws and 9 -> 10 measured-part records; PRINT-GUIDE coupon heading 21 -> 24; DESIGN option reference for
  the black band (R2's finding-3 option (b), not OPTIONS (b) = shorter FPC); FASTENER-POLICY count; ASSEMBLY s7 item
  10 far-corner tilt now reads "CAD restraint added (hood stack-stop post, `stack_retention` 1 of 1 pass), physical
  tilt/knock test open (G-KEEP-1 follow-up)".
- Evidence: lint on the r2 docs flags exactly the audited lines (FASTENER-POLICY:13, OPTIONS:25, OPTIONS:31,
  PRINT-GUIDE:135); current `--check`: stale none, lint 0, selftest ok.

### R3-5. Hardware limitations kept explicit (request part 3): **dependent on hardware**
- EVF feed: the generic "5 V regulator" is withdrawn (a 5.0 V output breaks the project's 4.90 V maximum). It is now a
  requirement, **R-EVF-REG** (WIRING s4.8): setpoint 4.55 V, band 4.39-4.71 V inside the accepted 4.25-4.90 V
  (terminal margins 0.125 / 0.19 V), input 4.715-5.355 V, dropout <= 0.30 V at 0.30 A, <= 0.29 W, rise <= 44 C at
  <= 150 C/W, ripple <= 50 mV p-p, envelope 16 x 7.5 x 4.5 in `ko_5v_up` (box arithmetic, not a CAD fit). Candidate
  option C (4.55 V LDO replaces the 1N5817; +3 parts, +11 joints; BOM D2-16R/C/P at quantity 0; device class Torex
  XC6210 with [to confirm] items) is a USER DECISION; option A (diode) is expected to fail G-W6. New gate **G-W13**
  (regulator bench qualification); G-W11 row adds a regulator thermocouple (case <= 90 C). Nothing is verified.
- Power: 27 W peak against the X1203 25.5 W stays; the 17.7-22.1 W restricted workload is labelled an estimate, not a
  margin; **G-W12** stays open until measured on the real stack. The EVF still needs measured hardware and the bench
  optical sequence (MEASURED-PARTS MP-EVF, EVF-G1..G9) before the rear carrier is frozen.
- Separation: every status block (DESIGN s1, HANDOFF s1, WIRING, MEASURED-PARTS, BOM) separates computed CAD results
  from procurement, printing and physical tests, which are all "not run".

### User decisions during r3
- **No LED indicators** (NOTE 4, 15:55: "remove the LED indicators. I/O will be via the dials, on/off, record button
  and the EVF."). I/O = exposure dial, 18/24 dial, power plunger, record button and EVF. Applied to the baseline with
  no geometry change: the plunger is no longer a light pipe (black ASA), the Pi onboard LEDs are set off in config.txt
  (WIRING s8, [to confirm on the bench, G-W3]), procedures read the EVF (boot screen, shutdown screen, dark), the BOM
  drops the natural-ASA/clear-PETG line (60 purchased lines; estimates SGD 340.61 -> 305.73). Release rebuilt 16:15:58:
  21 of 21, every production and coupon STL (11 + 24) identical to r2. Not studied: the plunger as a flexing tab printed
  into the hood plate (one fewer printed part).
- **Blunt the `rib_l` gusset tip to a 1.2 land** (NOTE 5, 16:25). The 0.60 mm knife-edge at the 45 deg tip of
  `RIBS['rib_l']`, present since r2, was found by the candidate work (seeded thin-wall screen missed it on the r2 mesh).
  Done (NOTES "r3 rib-tip"): `RIBS['rib_l']` x0 -13.0 -> -12.1 in layout.py (printed_tub.py unchanged), material
  only removed (22.5 mm3); new probe `tub_rib_l_tip` (land, min 1.2) in J7_camera: 1.25 at all 5 rays; dense scan
  minimum 0.598 -> 2.384. Trial and release (16:53:58) 21 of 21; tub.stl and coupon-pi-keeper-tub.stl differ from r2
  only at the tip, the other production and coupon STLs are identical (10 of 11, 23 of 24). Open: the SPEC.md s9 rib_l row text
  waits for the next release rebuild (SPEC is hashed). Not printed or measured.
- The FR1 candidate is not changed by either decision; it inherits both on adoption (it still carries the r2 rib tip).

### FR1 fastener-reduction candidate (request part 2): exploratory, not adopted
`candidate-fr1/CANDIDATE.md`. Every joint change is under the `D2_FR` toggle; `D2_FR=none` rebuilds every r2 production STL (11 at r2)
byte-identically. PT body screws 7 -> 4 (panel A2 keys + keeper keyed seat + hood yslide) or 7 -> 5 (with hood
screw1); UPS kit 8 M2.5 screws + 4 standoffs unchanged. Candidate build `candidate-fr1/out` (15:26:25, full, 1 mm):
21 of 21, 544 rows = 534 pass + 10 info, critical_features 126 pass + 10 info. New gates G-FRP-1, G-KEEP-1r,
G-YSLIDE-1 are not run and not in the release gate docs. Summary and choices: HANDOFF s4-s5.

### r3 still open
- Failing CAD checks: none. Named in CAD: cap detent strip (G-CAP-1), hood plunger-channel web 1.08, s_k2 wall 1.6.
- All physical work: slicer review, the coupons (24 at r4) + 3 calibration records, measured parts, G-W1..G-W13, EVF bench,
  dry assembly, service cycles, powered recording test. User decisions: lens, black band, OPTIONS (a)/(b), purchase
  variants, EVF feed A or C, and the FR1 joint options.

## r4 (2026-10-05 evening, maturity pass; follow-up audit `audit/d2-readiness-2026-10-05-r3`)

Request (user): "take the next steps to improve the maturity of D2", after a comparison against the release EVF
(`cad/gs8-release-v1`) that found D2 at CAD parity but behind on print and wiring readiness. Response to the reviewer:
`audit/d2-readiness-2026-10-05-r3/RESPONSE.md`. Log: `NOTES.md` "r4 maturity pass". Baseline before r4:
`baseline-r3-2026-10-05.zip`. Computed checks, desk research and documents only; nothing printed, sliced, bought,
measured, assembled or powered; nothing committed.

**r4 build state.** Receipt 2026-10-05 21:51:07 +0800 (Kowa, 1 mm sweeps): 23 of 23 categories, 593 rows = 581 pass +
12 info + 0 fail; checks.json `c820ef01...`; 16/16 sources, 91/91 outputs, 4/4 gate docs match disk. Fujinon
`out/_fujinon-r4` 21:45:35: 23 of 23. Every production and coupon STL (r4: 11 + 24) byte-identical to r3 (no geometry change);
15 new modifier meshes. Tests 31 of 31. Gates 53 listed (50 + 3 `/whole` items), 51 open, 2 withdrawn.

### R4-1. Audit logic issue 1, whole-part evidence bound only to coupons: **accepted** (code changed)
`build_d2.WHOLE_PART_TESTS` splits G-SNAP-2, G-KEEP-1 and G-PANEL-1: the coupon item stays in coupon_validation; the
whole-part cycles become assembly_operation items `<gate>/whole`, bound to the gate doc and every production STL (a
changed hood or tub makes them stale). `apply_gate_outcomes` reports the gate as a pass only when both halves pass.
SPEC s10 and `evidence/README.md` say so. Test `test_whole_part_test_is_split_and_goes_stale`.

### R4-2. Audit logic issue 2, malformed field types crash evaluation: **accepted** (code changed)
`validate_record` checks field types first; `_key()` keeps non-string values out of dict/set lookups. An array `state`
is rejected on its item; an object `item` stays visible as an unmatched record; neither raises. Test
`test_malformed_field_types_are_rejected_not_crashing`; the auditor's `check_r3_logic.py` re-run in scratch: no exception.

### R4-3. Audit logic issue 3, a declared replacement can waive an unchecked joint: **accepted** (code changed)
`checks.check_joint_coverage` accepts a replacement only from a CRITICAL_JOINTS entry that itself validated (a pass,
or complete coverage resting on a named gate); an FR_JOINTS-only declaration waives nothing and the error names it.
Test `test_unvalidated_replacement_cannot_waive_required_joint`; the older `test_deleted_joint_with_its_probes_fails`
now merges its fork joint into CRITICAL_JOINTS (as the real fork does). The fork's own copy of checks.py is unchanged
(it merges correctly); it takes the fix on adoption.

### R4-4. Builder-facing corrections (FR1) and test definitions: **accepted** (documents changed)
HANDOFF hood removal: 2.5 mm toward the open left side (+Y), then lift. `candidate-fr1/coupons_fr_keeper.py` gate text:
tip gap 0.15 (pocket y0 -29.9, tongue y0 -29.75), keeper coupon manifest regenerated, 24 FR coupon meshes still
watertight. `fr1_counts.py`: the keyword column is labelled a subset and the full ASSEMBLY s1.1 count is stated (a
12-tool set at r4, 11 without the hood pins). WIRING G-W13 (e): a defined off rail (the real VBUS with a 100 ohm stand-in), VOUT
bias within the device ratings, logged through shutdown. Row C of the option table and the recommendation no longer
say "met by design". The FR1 receipt still records the old `coupons_fr_keeper.py` hash (a text-only change; the FR1
package is consolidated on adoption, as the audit asks).

### R4-5. Airflow outputs mislabelled: **accepted** (label only; study still paused)
`airflow/out/variants/VARIANTS-tables.md` carries a STATUS banner (partial, superseded model output; the UA 0.20 block
reuses UA 0.095 values; a printed "FAIL" is a model flag, not G-W11). Nothing was re-run.

### R4-6. Wiring maturity (comparison with the release EVF): **CAD and documents improved; bench gates open**
New `cable_routes` check (checks.py); 6 link keep-outs close 4 gaps found in the comparison plus a 1.0 mm gap and a
4 x 0.4 mm run-lead edge contact found by the new check; the gaps held no printed solid. Pigtail fuse W-10 (Littelfuse
0251015.MXL) in the `xt30_pair` proxy; R-PACK-BMS; G-W1 and G-W5 extended. Option C regulator candidates made
concrete (TLV75801P primary, XC6220B45 fixed alternative), not adopted.

### R4-7. Print maturity: **CAD and documents improved; slicer review open**
`layout.print_modifiers` + `build_d2.export_modifiers`: 15 modifier meshes in the print pose, checked
(`print_modifiers`), hash-linked and required by slicer-review records; the panel's threaded bosses get the 40 % rule
for the first time. PRINT-GUIDE s1.1, DRAFT label removed, pilot count 6 -> 7 corrected; SPEC s9 rib_l row applied.

### r4 still open
- Failing CAD checks: none. Named in CAD: cap detent strip (G-CAP-1), hood plunger-channel web 1.08, s_k2 wall 1.6.
- Not checked by CAD: cable bend radius; the fuse sleeve's hand fit in the junction slack (G-W5); regulator thermals.
- All physical work (51 open gates). User decisions: lens, black band, OPTIONS (a)/(b), purchase variants, EVF feed
  A or C, FR1 joints.

## r5 (2026-10-06): heavy-lens support (J7-R float)

Trigger: the user's request "Fix the sagging issue for the heavy lens first" (the load-path section of
`LENS-ZOOM-CANDIDATES.md`). Brief `R5-BRIEF.md`; study `research/r5-lens-support/` (2 dossiers, 3 designs, 3 judges,
probes); implementation log `research/r5-lens-support/IMPL-NOTES.md` (steps 1-3). This is not an audit response:
it corrects a wrong model that every earlier release shared.

### R5-1. The camera model was wrong: **corrected** (CAD rebuilt; MP-CAM open)
r1-r4 modelled the GS camera from the stills R1 record: 39.5 sq front lands seated on the tub wall at x -5.2, a dia 36
ring in a dia 36.5 bore, the C flange at x +10.6, and 2 printed pins (dia 1.9) in the mounting holes. The official
drawing (`research/m12-drawings/gs_side.png`, 10.05 px/mm) shows a different stack: the C-CS adapter (dia 30.75 x 5.0),
the BFAR head (dia 36 x 1.2), a round housing (dia 35.5 x 10.35) with a split lock tab on top and a tripod block
below, then the PCB (38 sq) and the plastic rear cover (39.5 sq). So the C flange sat about 10 mm too far forward,
the 39.5 "lands" were the rear cover, the pins ended about 7 mm short of the PCB and located nothing, the keeper sat
about 1.2 behind the real cover, the real camera could rock about 5 deg nose-down, and the tripod block would have
collided with the Pi / cooler envelope. r5 rebuilds `CAM` and the `gs_camera` proxy as tagged sub-solids,
parametric in the BFAR screw-out s (0..3.0, nominal 1.25); every value carries a `CAM['status']` ('drawing',
'unconfirmed', 'estimate') and MP-CAM measures it. The tripod block comes off at bench step B0.

### R5-2. The lens hung on the camera's own mount: **rectified in CAD** (J7-R float; G-LENS, G-COL-1, G-CAM-2 open)
The premise of the user's question was partly wrong: the mount is milled aluminium; the compliant link is the
housing-to-PCB joint (2 M2 screws, nylon washers, a gasket). The fix is the same either way: a printed, per-lens
`lens_collar` holds the lens on its fixed rear band (45 deg cone seat, slit pinch s_c4) and is anchored on the tub
front wall (s_c1..s_c3, M3 in heat-set inserts, + a compression foot). The camera hangs on the lens; the tub lip, a
hood roll fin and the panel keeper are catches with gaps. Pins and turret deleted. Two of three judges recommended
it; it scored highest overall.

### R5-3. Checks whose premise was the wrong camera model: **replaced by real-model equivalents** (none weakened)
1. `layout.self_check`: 'turret bore clears ring' and 'lens clears turret front' -> 25 r5 rows: lip - adapter 0.825
   (>= 0.75), counterbore - BFAR 0.75 (>= 0.7), lip gap 0.5 (>= 0.4), tab gap 0.4 at s 0 (>= 0.3), keeper 0.5 behind
   the cover at s_max, plate bore - adapter 2.875 (>= 2.0); per lens: collar front <= first moving ring - 2.0, seat =
   C + band x0, bore - band 0.3 (0.2..0.4), cone off the rear step, rear face ahead of the plate; insert bosses
   x0 >= -7.6 and wall >= 1.6; hood hole tops <= 95.3; axis >= 10 inside the anchor polygon; lugs and washer inside
   |y| <= 35. (183 layout checks, 0 failed.)
2. `checks.clearance_zones`: the 2 "camera ring in tub / hood bore" zones -> 3 real-stack zones: BFAR in the tub
   counterbore (stated 0.5 = the lip gap), adapter in the tub lip (0.825), adapter in the hood plate bore (2.875).
3. J7 `CRITICAL_FEATURES`: `tub_cam_pin_0/1` (the pins located nothing) -> the collar, anchor and catch probes (19
   required ids); `tub_front_wall_seat` moved from the plain wall 30 below the axis to the TL boss root.
4. `test_hood_panel`: the ring / CS-ring / adapter cylinders against the hood -> BFAR + body at s 0 / nominal / max,
   the adapter and both lenses.
5. `MATES` tub / gs_camera: contact -> clearance (the camera no longer seats). New clearance mates for the adapter and
   lens boxes are still measured on the solids at the same 0.05 mm3 as `check_interference`.
6. `boss_geometry` measured every `SCREWS` row by PT rules, so the 4 M3 rows failed (pilot 4.0 / 3.4): it now
   measures kind PT only (the same 7 rows and rules), and kind M3 gets `check_inserts` (insert rules).
7. `make_tables.counts()['pt']` and the PT sub-groups count kind PT only (7, unchanged); a separate M3 count (4) with
   its own lint kind. The lint self-test's planted "12 printed parts" phrases are derived as count + 1, because 12 is
   now the true count.
8. `build_d2.STATE_GATES`: G-COL-1 is a coupon gate (3 new coupons); G-CAM-2 is an assembly item (it was caught by the
   `G-CAM-` measured-fit prefix, which binds only the gate doc; an assembled test must also bind every production STL).

### R5-4. New checks (SPEC s6 5h; J7 `required_checks`)
`j7_float` (the hanging unit against everything else at s 0 / 1.25 / 3.0), `lens_support` (FAIL > 150 g without a
band; a zoom needs a fixed band >= 15 mm; WARN until the band is measured), `lens_clamp` (anchor polygon; slip moment
>= 1.5 x static; WARNs at 5 g), `inserts`. Regression cases: 7 new (38 in all).

### R5-5. Build state
Release `out/build-receipt.json` 2026-10-06 16:32:38 (Kowa, 1 mm): 27 of 27 categories, 749 rows = 732 pass + 17 info
+ 0 fail; 17 sources, 101 outputs and 4 gate docs match. Fujinon (`out/_fujinon-r5`, 1 mm): 27 of 27, 729 pass + 17
info + 0 fail. Geometry vs r4: tub, hood and panel changed, `lens_collar` new, 3 tub modifier meshes new, the rest
byte-identical; coupons + 3 (G-COL-1), `hood_ledge_ret` re-triangulated only. One step-2 geometry fix: s_c4 moved
x 4.8 -> 4.7 (the collar's bed chamfer left 1.585 of insert wall; now 1.70 / 1.685).

### r5 still open
- WARN rows (listed, not blocking): no lens band measured (Kowa 'drawing', Fujinon 'assumed', Computar 'drawing');
  the Kowa's computed slip moment 0.170 N m is below its 5 g knock moment 0.286 N m (the lens rocks elastically in the
  collar at a knock; aim only). G-COL-1 sets the real pinch; a PC or ASA-CF collar is the upgrade path.
- Physical: MP-CAM (G-CAM-1), G-LENS, G-COL-1, G-CAM-2; G-W11 decides ASA or PC for the collar.
- Plan B (housing clamp) is documented only, for a G-LENS fail.
