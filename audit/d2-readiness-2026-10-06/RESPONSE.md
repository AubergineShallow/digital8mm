# Response to the D2 r5 audit of 2026-10-06 (GS8 D2 r6)

Written 2026-10-08, in reply to the user's request: "Settle the print order and orientation. Fix the minor findings as
well." This is the only file added to this folder; the reviewer's files are unchanged. State and next steps:
`cad/gs8-d2-v1/HANDOFF.md` section "r6". Every result below is a computed check or a document change. Nothing was
printed, sliced, bought, measured, assembled or powered.

**Baseline after r6.** Kowa receipt `cad/gs8-d2-v1/out/build-receipt.json`, built 2026-10-08 16:05:33 +0800 (`--skip-renders --sweep-step 1.0`): 28 categories, 27 passing and `mass_com` report-only (L9 below); 852 rows = 833 pass + 19 info + 0 fail; no stubs; `cad_release_candidate` true. Fujinon (15:56:46): 28 categories, 830 pass + 19 info + 0 fail. `audit_cloud_release.py --final-release`: pass, 20/20 sources, 86/86 outputs, 4/4 gate docs. The geometry changed in the tub (insert bores 0.1 deeper), the collar (ears r 5.6, 17.3 g) and the new centring gauge; every other production STL is unchanged in shape. Balance: Kowa 895.3 g, +1.5 mm; Fujinon 781.9 g, -9.7 mm (unchanged).

**Not in this pass.** M1, the collar clamp spring and its thermal term, was not part of the request. It stays the one
open design defect. The r6 report-only row `anchor_polygon_bolted` (L7) and the G-W11 collar thermocouple (B-8) make
its consequences visible. Fix it before the collar is printed. The print order already puts the collar last.

## Major findings

| Item | Response | Change | Evidence |
|---|---|---|---|
| M1 collar clamp has no spring | not addressed (outside the request) | none; still open, see above | - |
| M2 print order (= B-1) | **fixed, and enforced by the build** | `layout.PRINT_PREREQS` lists, for every printed part, the gates whose measurements set its geometry. They come from the MEASURED-PARTS "Blocks" column, plus G-COMB-1 (and G-KNOB-1, G-COL-1 where they apply). `COUPON_PREREQS` holds the G-COL-1 coupons to G-CAM-1 and G-LENS. A slicer record (or G-COL-1 coupon record) filed or dated before its prerequisites passed is rejected. The receipt's `print_release` lists what each part still waits for. PRINT-GUIDE s7 is generated from these tables. The tub, hood and panel wait for G-CAM-1 and G-LENS together (both at B0), so the edge case of lens segments reaching the chassis is covered too | `test_r6_print_order_rejects_records_before_their_gates`, `test_r6_print_prereqs_are_live_gate_ids`; contract rows `print_order`; PRINT-GUIDE s7 |
| M3 not under version control | **fixed** (2026-10-08, user-approved) | the D2 fork is in the GitHub repository `AubergineShallow/digital8mm`, byte-exact (`* -text`), so receipt hashes hold on a fresh clone | repository history |

## Orientation (the user's request)

The face-down of every part is unchanged and is now a computed, regression-protected claim. The new category
`print_overhang`:
- slices each production STL (and the new centring gauge) in its print pose every 0.2 mm;
- takes the new area of each layer beyond the 45° allowance of the layer below, rasterised at 0.1 mm;
- requires each patch to be a short overhang (≤ 1.0 mm from supported material), an anchored bridge (≤ 30 mm), a bridge
  that ends at a screw hole (reported), a teardrop apex line, or inside a declared support zone.

A declared zone that nothing needs fails as stale.

**It confirmed the bridges the guide lists.** The measured spans match the guide: hood J2 lip 20.7 (guide 21), housing
ceiling 15.1 (15.2), base shelf 24.7 (25), head pockets 18.2 (18.5), tub scoop roof 19.7 (20), collar washer seats 7.2
(7.5).

**It found two overhangs nobody had listed:**
- the s_k2 keeper boss chin (2.9 x 7.3 mm, off the floor wall), which clears the X1203 edge by 0.25;
- the LL collar-insert boss chin (3.3 x 2.4 mm, off the front wall), which clears the Pi box by 0.3.

Each prints as a flat ledge and would droop toward the board it clears. Both are now declared paint-on supports, so the
tub has 4 supports instead of 2. Review note A3 (0.65-0.8 mm of ear wall in the first layers) is fixed with ear r 5.6.
Evidence: `checks.json` `print_overhang`; `test_r6_print_overhang_bridge_island_zone`; PRINT-GUIDE s3.

## Minor findings

| Item | Response | Change | Evidence |
|---|---|---|---|
| X2 nothing centres the collar | fixed | **Centring gauge** (`printed_collar.centring_gauge`, `stl/tools/collar_gauge.stl`, one per lens): two 45° cones, one on the tub lip's front edge and one in the collar's 0.6 bore-entry chamfer, so no fit clearance is in the chain. **Step 7 reordered:** the collar is fitted first, with the camera still out, and centred with the gauge while s_c1..s_c3 are torqued; then the camera goes in. A collar refit takes the camera out. **Check:** j7_float subtracts the declared centring stack from every lateral gap: 0.30 with the gauge (0.60 without, reported), plus 0.25 hood-to-tub for the roll fin. | `centring_gauge` rows (seat 0 mm³ / gap 0, hood 0.75, insertion and driver clear); `j7_float` `lateral_stack` rows; `test_r6_centring_gauge_seats_and_shifted_gauge_fails` |
| X3 band edge on a 45° cone | covered | G-LENS records band OD, edge form and position (cloud polish), and the print order now blocks every affected print until it passes. The flatter cone or flat shoulder is not adopted: it is a design choice for after G-LENS | MEASURED-PARTS MP-CAM; PRINT_PREREQS |
| X4 datum chain, s past 3.0 | fixed (documentation + check) | B0 requires s inside `CAM['s_range']`. The BFAR is never screwed out past 3.0. MP-CAM records the BFAR's full travel at both stops. The polish added the sensor-datum inputs. j7_float now sweeps the whole range | ASSEMBLY B0 item 5; MEASURED-PARTS MP-CAM; L2 |
| X5 / B-6 torque and no torque tool | fixed | the polish capped s_c1..s_c3 at 0.15 N m. r6 adds an adjustable torque screwdriver to the BOM (D2-77) and the toolset (tool 13), required for every M3 and PT screw | BOM D2-77; ASSEMBLY s1, s1.1; FASTENER-POLICY I |
| B-2 adapter can leave with the lens | fixed | B0 item 3: seat the adapter and paint-mark adapter and BFAR. The mark is checked at every lens change, and an adapter that came out is refitted before any lens | ASSEMBLY B0, s7, lens swap; step 7 check |
| B-3 screw bottoming / local depth | refuted in part, tightened | The bottoming scenario cannot happen: the 3.4 clearance runs through each boss end. Fixed anyway: the insert bore is 0.1 deeper (4.3; the LL face sits partly on the RV 5 corner, which is why one probe read 4.184), `check_inserts` compares the local depth with the full need, and it tests the tip at its ISO 4759-1 js15 length tolerance | `inserts` rows; `test_r6_inserts_tip_length_tolerance`; FASTENER-POLICY I |
| B-4 / B-5 bench support, s_c4 wording | already fixed by the cloud polish | - | ASSEMBLY B0, step 8 |
| B-7 lens torque through the cover | fixed | step 8 and service item 6a hold the camera by its metal lens mount (housing), never the cover. Panel-on lens swaps use fingertip torque only and never force a thread against the roll fin. G-CAM-2 repeats its corner check after 5 swaps | ASSEMBLY s1, step 8, s7; SPEC G-CAM-2 |
| B-8 "PC if > 50 C" untestable | fixed | collar in ASA; G-W11 adds a thermocouple at the collar's LR foot; above 50 C, reprint in PC and repeat G-COL-1 | WIRING G-W11; PRINT-GUIDE s1 |
| B-9 evidence README stale | fixed | 12 parts with the collar, tub 10 modifiers, G-COL-1 listed | evidence/README.md |
| B-10 stale numbers | fixed | PRINT-GUIDE s1.1 infill sentence; DESIGN s6 12 solder joints; tool count 14 | PRINT-GUIDE, DESIGN, OPTIONS |
| L1 light lens without a collar | already fixed by the cloud polish | - | `lens_support` |
| L2 three back-focus samples | fixed | `j7_float` samples `s_range` every 0.25 plus s_nom (13 positions) | `test_r6_j7_float_clash_between_old_samples_fails` (planted clash at s 2.0: missed by 0 / 1.25 / 3, caught now) |
| L3 missing solids skip rows | fixed | a missing lens is a j7_float FAIL row; a missing collar of any production lens is a lens_support FAIL row ('stub' when the collar module is a stub) | `test_r6_j7_float_missing_lens_fails`, `test_r6_lens_support_missing_collar_fails` |
| L4 lens checked for overlap only | fixed | the lens keeps ≥ 0.5 to every part but its collar, adapter and camera | `test_r6_j7_float_lens_zero_gap_contact_fails` |
| L5 duplicate probe IDs | fixed | a duplicate ID in any id registry FAILs `critical_features`; the 4 intentional overrides now go through `layout.replace_feature` (in place, with the reason recorded); new probe `tub_front_wall_lr_foot` under the LR foot, required by J7 | `test_r6_duplicate_feature_id_fails`; `critical_features` |
| L6 "measured" is a string | fixed | `'measured'` clears the band WARN only with a current passing G-LENS record (evaluated before the checks); without one it FAILs | `test_r6_band_measured_needs_a_g_lens_record` |
| L7 bolted-only margin not gated | fixed (as a WARN) | new row `anchor_polygon_bolted`: info + WARN while the bolted triangle alone leaves the axis outside (-8.8 mm). The polish's three-bolt reaction model (LR inactive) screens the loads | `test_r6_bolted_only_anchor_margin_warns`; receipt `warnings` |
| L8 stub relabel | already fixed by the cloud polish | - | - |
| L10 empty coupon map | fixed | a coupon gate with no coupon STL rejects every record and FAILs a contract row | `test_r6_coupon_gate_without_coupons_rejects_every_record` |
| L11 coupons / Fujinon not source-linked | fixed | the build FAILs a contract row if a coupon manifest was cut from other sources; `checks.json` records its sources; the receipt's `carried_checks` says whether the carried Fujinon checks match; the final-release audit requires it | contract rows `coupon_producer`; receipt `carried_checks`; `audit_cloud_release.py` |

## Notes

| Item | Response |
|---|---|
| X6 prying pivot | superseded: the cloud polish replaced the pivot estimate with a three-bolt reaction model (LR inactive); the old figure is kept only for comparison |
| X7 G-COL-1 bolting order | already in G-COL-1 (cloud polish); r6 adds the gauge and the torque screwdriver to it |
| X8 keeper comment | already corrected (2.25 at nominal) |
| X9 levelling range | unchanged: step 10 keeps the conservative ±1.4° window |
| L9 `mass_com` has no rule | fixed: report-only category, summary status `info`, not counted as a passing category (no balance rule is enforced, by decision R5-BRIEF choice 10) |
| L12 a-e | (a) the receipt hashes the test suites, the release audit and the evidence README (`support_files`); (b) record dates must be ISO 8601; (c) evidence README says MP-CAM is filed as G-CAM-1 / G-LENS; (d) README counts fixed; (e) noted, no change |
| B-11 service driver | fixed: driver audits for s_c4 in the closed body and s_j at base removal (`layout.SERVICE_DRIVER`) |
| B-12 heat-set tip | fixed: BOM D2-74 names the tip system of the chosen iron |
| B-13 dry fit on the hood | fixed: PRINT-GUIDE s5 item 6 does it on the G-COL-1 coupons |
| B-14 heat-setting behind a 2.5 wall | fixed: ASSEMBLY B1 and FASTENER-POLICY I say to back the boss |

**Tests after the final build:** `test_r3_regressions.py` 82 of 82 (65 + 17 new r6 cases, one per planted fault above); the 9 focused unittest suites 73 tests, OK (4 POSIX-only skips); `test_collar.py` both lenses PASS (151.8 s); `make_tables.py --check` stale none, lint 0.
