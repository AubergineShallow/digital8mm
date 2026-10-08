# Response to the 2026-10-05 follow-up audit (GS8 D2 r3)

Written 2026-10-05 by the r3 final-docs role. The reviewer's files in this folder are unchanged; this is the only file
added here. Full record: `cad/gs8-d2-v1/RECTIFICATION.md` section "r3 (2026-10-05, follow-up audit)"; state and next
steps: `cad/gs8-d2-v1/HANDOFF.md`. Every result below is a computed check or a document change. Nothing was printed,
sliced, bought, measured, assembled or powered, and nothing was committed.

**Baseline preserved.** The r3 release (`cad/gs8-d2-v1/out/build-receipt.json`, built 2026-10-05 16:53:58 +0800,
`--sweep-step 1.0`) passes 21 of 21 categories, 552 rows = 542 pass + 10 info + 0 fail. The audit corrections alone
left all 11 production STLs and 24 coupon STLs byte-identical to the r2 build you rebuilt (releases 13:02 and 16:15) (r2 outputs kept in `cad/gs8-d2-v1/out/_r2-2026-10-05/`).
The audit corrections changed checks, evidence handling and documents only. The one r3 geometry change is a later user
decision: the `rib_l` gusset tip was blunted to a 1.2 land, so `tub.stl` and `coupon-pi-keeper-tub.stl` now differ from
r2 only at that tip (10 of 11 production and 23 of 24 coupon STLs identical; new probe `tub_rib_l_tip` 1.25 mm).

| finding | response | change | evidence |
|---|---|---|---|
| 1. Battery-connected service shortcut (high) | accepted | ASSEMBLY s7 opens with P1-P4 (shut down; cap off; pull the pack; unplug the XT30) for every electronic service route, panel-only included; "a halted Pi is not electrical isolation"; initial assembly fits the pack last. Fitted-pack `removals` / `service_driver` rows carry a `scope` field: geometry only. No switch added. | release removals 11/11, service_driver 6/6 with the scope text; HANDOFF step 8 starts each service cycle with P1-P4 |
| 2. Evidence binding and visible failures (medium) | accepted | structured records (`item`, `state`, `artifacts` {path: sha256 of what was tested}, `profile`, `verdict`, `date`, `by`); no file-name matching; outcomes pass / fail / conflict / stale / rejected / not run tracked apart from completeness; failed, stale, conflicting, rejected and unmatched records stay in `open_evidence`; G-KNOB-1, G-COMB-1, G-J4-1 registered; unknown row statuses rejected; an info category needs a real pass; an empty category fails | `test_r3_regressions.py` 27/27, incl. `test_file_names_are_not_evidence`, `test_stale_r1_record_is_stale`, `test_coupon_record_cannot_cover_production_part`, `test_failed_verdict_stays_open`, `test_unknown_status_rejected`, `test_info_only_category_does_not_pass`, `test_calibration_items_registered` |
| 3. Critical-feature coverage (medium) | accepted | origin always measured (stale origin fails); missing span rays fail unless declared in `expect_outside` with a reason; 12 required load-path joints (`CRITICAL_JOINTS`, `REQUIRED_JOINT_IDS`); the cap flexures stay G-CAP-1 exceptions and J6 reports info | `hood_groove_lower_lip` origin now measured (pass); one silent r2 miss (`tub_evf_groove_wall_bot_px`, deliberate 5 V lead relief) now declared; tests `test_even_span_measures_origin_and_stale_origin_fails`, `test_unexpected_missing_ray_fails_and_expect_outside_allows_it`, `test_deleted_joint_with_its_probes_fails`, `test_flexure_is_gated_exception_not_ordinary_pass`; release critical_features 109 pass + 10 info |
| 4. Handwritten counts (low) | accepted | `make_tables.py counts()` is the count source (DESIGN s1.1); `--check` lints handwritten counts in every release and electronics doc; OPTIONS 7 PT / 10 MP records, PRINT-GUIDE 24 coupons, DESIGN option reference, ASSEMBLY far-corner tilt = CAD restraint added, physical test open | the lint flags exactly your four r2 lines; current `--check` lint 0 |
| EVF and regulator (gates section) | accepted, dependent on hardware | generic "5 V regulator" withdrawn; requirement R-EVF-REG (WIRING s4.8): 4.55 V setpoint, 4.39-4.71 V band inside 4.25-4.90 V, dropout, heat and envelope stated; option C (LDO replaces the diode) is a user decision; new bench gate G-W13 | not verified: no part bought or measured |
| Power (gates section) | accepted, dependent on hardware | 27 W vs 25.5 W kept; 17.7-22.1 W labelled an estimate; G-W12 open | none until measured |
| Fit and print process | accepted, dependent on hardware | every status block keeps slicer, coupons, measured parts and assembly as "not run" | receipt: 4 evidence states not run, 48 of 50 gates open (2 withdrawn) |

**User decisions made during r3 (recorded, not audit items):** no LED indicators (I/O = exposure dial, 18/24 dial,
power plunger, record button, EVF; no geometry change, STLs unchanged); blunt the `rib_l` gusset tip to a 1.2 land
(a 0.60 mm tip present since r2, which the seeded thin-wall screen had missed; see the sentence above).

**Fastener-reduction candidate FR1 (your joint study): exploratory, not adopted.** `cad/gs8-d2-v1/candidate-fr1/`
(`CANDIDATE.md`) is a separate fork with every joint change under a toggle; `D2_FR=none` reproduces all 11 r2 STLs.
PT body screws 7 -> 4 (panel 2 keys + 2 screws, keeper keyed seat + 1 screw, hood drop + 2.5 mm transverse slide into
rigid keys, no pins) or 7 -> 5 with a one-screw hood; base lock s_j and the tool-free cap are kept; UPS kit screws and
standoffs reported separately and unchanged. Candidate build: 21 of 21 categories, critical features 126 pass + 10 info
+ 0 fail. Its new gates (G-FRP-1, G-KEEP-1r, G-YSLIDE-1) are not run. The user chooses which joints, if any, to adopt.
