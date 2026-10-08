# D2 r5 cloud-polish copy

Label: `r5-cloud-polish-20261007`. Based on snapshot checkpoint
`789f40731f0c3cebf691f3920e8d244057219048` of the transferred r5 project. This is a reviewable independent fork, not
an upstream r6 and not a replacement for any later work on the original computer. The source transfer's r5 receipt
was independently read: 27 categories, 732 pass + 17 info + 0 fail. Those are captured baseline results.

## Result and preserved design

The J7-R floating-camera architecture, silver/black body, grip, fixed-band lens collar, physical exposure and 18/24
dials, record button, power plunger, EVF and no-LED decision are preserved. No extra control, printed production part,
washer type or exterior trim was added. No hardware was bought, printed, assembled, operated or measured.

### Narrow changes implemented

1. **The collar washer now seats fully.** The pinch axis moves 0.3 mm in Y to -31.0; the upper lug extends rearward
   to x 0.7 and its bearing edge stays square. Relief y -27.0 leaves the original 7.0 mm ISO 7089 washer a complete
   flat footprint, including 0.2 mm screw float plus 0.2 mm edge allowance. The lower insert wall, cone, feet, part
   envelope, existing screws and straight PH1 access remain checked. Files: `layout.py`, `printed_collar.py`.
2. **The anchor roofs have deliberate print stock.** Production and collar coupon STLs include three one-layer
   membranes, x 2.6..2.8, only across the central 3.4 mm holes in the first washer-seat roof layer. Clearing the
   holes restores the exact finished solid; the washer plane is not shifted. STEP and assembly checks always use
   the finished geometry. Print-manifest entries identify stock volume and required postprocessing. Files:
   `printed_collar.py`, `build_d2.py`, `make_coupons.py`, PRINT-GUIDE and ASSEMBLY.
3. **Lens support checks fail closed.** Every lens must have a support band at any mass, because the collar is the
   only built J7-R anchor. A nearby stub no longer disguises a real float fault. Planted-fault regressions now cover
   insert geometry, collar location/clearance, moving bands, float directions/collisions and clamp overload.
   Files: `checks.py`, `layout.py`, `test_r3_regressions.py`.
4. **Anchor loads no longer assume LR can pull.** The model solves three-bolt reactions, excludes compression-only
   LR, combines full axial shock with arbitrary-direction bending, and exposes a provisional prying factor 2.0.
   It preserves the former nominal value for comparison. This is a conservative screening assumption, not an
   experimentally established safety factor. The 100 N relaxed allowance remains unmeasured. Anchor torque is
   provisionally capped at 0.15 N m; G-COL-1 now records actual insert dimensions, production bolting order,
   pull-out/creep proof and washer contact. The uniform-pressure slip estimate is explicitly an upper bound.
5. **Unknown optical datums stay unknown.** Sensor height, filter focus shift and direct C-flange-to-cover stack
   measurements are explicit optional inputs. No die height was guessed. The old 1.25 mm nominal remains a clearly
   marked geometry sampling pose until supplied measurements resolve it; inconsistent or invalid supplied values
   cannot become a pass. MP-CAM now measures the full stack directly at s = 0 and at the bench-set s. G-LENS requires
   measured band data, rebuild and renewed checks before affected tub/hood/panel/collar printing.
6. **Bench support/order is explicit.** Back focus is set with the camera and lens supported and the tripod block
   still attached; its block is removed afterward. The bench live-view route and power-off FPC handling are stated.
   The open-side assembly instruction explains forward support for thread start; s_c4 is fitted loosely before the
   final pinch. G-CAM-2 uses the real FPC fold so its spring load is represented.
7. **Control operation is no longer inferred from appearance.** Exposure push travel stays unknown. The present
   model affords 0.20 mm to the panel and 0.25 mm to the fixed bushing, which does not establish reliable actuation.
   MP-ENC/G-W9 now require measured stroke, end-of-stroke running clearance, repeatable press/release and retained
   shaft engagement before the push action is commissioned. The 18/24 switch proxy's moving D shaft now matches
   the knob's displayed 45-degree state; fixed housing/tab and unmeasured real detent assumptions are unchanged.
   A planted old-pose fault reproduces about 8.99 mm3 overlap and now fails the nominal control-mate check.

8. **A newly exposed encoder-tooth weakness is corrected.** Rebuilding the captured baseline uncovered a real
   1.02 mm encoder snap-tooth root that the old 1.6 mm beam probes missed. All three lands now give 1.62 mm roots,
   with unchanged retention planes, beam sections and engagement. New mandatory tooth-root probes and a planted
   old-land regression cover them. The second sample was a shallow label ridge over 2.8 mm of intact panel backing.
   No new decorative exception was added. The rebuilt panel has no unclassified spots. The release summary now
   blocks any future unclassified spot rather than leaving it informational. Full evidence:
   `research/cloud-polish/PANEL-THIN-SPOT-REVIEW.md`.
9. **Lettering is reproducible.** The previously declared DejaVu font was not actually passed to the engraver;
   Arial/system substitution affected geometry. A licensed, hash-pinned DejaVu Sans Bold font is now included and
   passed explicitly. Missing or modified bytes fail before generation. The new actual glyphs are visually reviewed
   and retain the existing stroke-width/engraving-depth checks.

10. **The collar's rear cone edge has a real minimum land.** The stricter final Fujinon build caught an unused
    thin annulus at the rear entry: exact original entry chords were about 0.43 mm (Fujinon) and 0.53 mm (Kowa).
    A 1.6 mm cylindrical rear-bore land now truncates that free feather without moving the 45-degree fixed-band
    seat, bore, lens contact or outer envelope. Exact chords at the new edge are 1.63 mm. New mandatory checks
    measure the actual bore edge, so a planted old profile cannot pass by reporting corrected parameters. The
    unbuilt Computar candidate does not have room for this entry at its unmeasured band position: it is explicitly
    marked as needing a separate rear-entry design, cannot export a collar, and fails if promoted to a production
    lens without correction. No band was silently moved and no thickness rule was reduced.

## Verification and reproducibility

Only computed checks may say pass. Read the current `out/build-receipt.json`, `out/checks.json` and generated DESIGN
blocks for final Kowa/Fujinon result counts; do not reuse the baseline count as a fork result.

Final current-source builds and independent audits are complete (2026-10-07 SGT):

| Variant | Build time +0800 | Categories | Pass | Info | Fail | Stubs / unclassified | Hash audit: sources / outputs / gate docs |
|---|---|---:|---:|---:|---:|---|---|
| Kowa | 00:06:26 | 27 | 748 | 18 | 0 | none / none | 20 / 85 / 4, all match |
| Fujinon | 00:02:15 | 27 | 745 | 18 | 0 | none / none | 20 / 54 / 4, all match |

Both receipts state `cad_release_candidate: true`. The final suites pass **65 legacy regressions + 73 focused
cases**, plus the full both-lens collar integration test (127.6 s). Serialized production/coupon STLs, finished
STEP, producer provenance and the independent release audit pass. All 53 physical gates remain open; the four
physical evidence states remain not run. Computar's unsupported rear-entry status is an explicit warning, not a
production-lens approval.

Focused tests implemented/run during the refinement:
- `test_r3_regressions.py`: expanded from 38 to 65 cases for the r5 fault families and three-anchor load model.
- `test_mechanical_refinements.py`: 12 cases for complete washer support, allowed float, exact removable stock,
  print/finished separation, unknown/inconsistent datums and aligned/planted-misaligned control proxies.
- `test_collar.py`: both lens solids, envelope/bed/print orientation, cone/band interface, feet/holes, keepouts,
  camera/adapter clearances, PH1 driver access, insertion/removal sweeps and J7 critical sections.
- `test_collar_rear_land.py`: minimum entry, planted old profiles, preserved seats/envelopes and blocked unsupported-candidate exports.
- `test_panel_refinements.py`: exact tooth-root, invariant geometry and portable-font regressions.
- Release-gate tests make unknown thin spots block the computed CAD-release status.
- Independent export tests verify the serialized production/coupon STL against printable stock, and the per-part
  STEP against the finished collar, for both lens variants.
- Input-validation tests cover negative, non-finite, boolean and string values. Missing measurements stay unknown.

All CAD commands use `run_locked.py`. The isolated pinned runtime and headless export route are documented in
`CLOUD-REPRODUCIBILITY.md`. Final rendering may use Blender rather than the original X-dependent VTK path; render
appearance is never dimensional, slicer, optical, thermal or ergonomic proof.

## What still needs physical evidence or a user decision

The captured project had 53 open physical gates and no measured/printed/assembled evidence. This fork closes none
of them. Its highest-value next steps remain:

1. **MP-CAM and G-LENS first:** actual camera stack, tripod-block removability, optical/back-focus pose, lens fixed
   band, real rear-cell/filter clearance, thread length, moving-ring/thumb envelopes and mass/CoM. A different band
   position can consume float clearance; update source and rebuild before production printing.
2. **G-COL-1, print/coupon and fastener gates:** real short insert type/OD/length, fit profile, flat roofs/washer
   contact, correct bolt-before-pinch order, warm creep, pull-out/torque retention and slip. Kowa 5 g slip remains a
   warning. The data-only Computar nears the estimated anchor allowance and is not an approved heavy-zoom build.
3. **G-MP-ENC/G-W9 and MP-SW:** actual push stroke and full installed operation; actual purchased selector index
   angle, shaft/D-flat fit and both engraved states. The physical 18/24 switch remains selected; its part is not.
4. **Power gates, especially G-W12:** the 27 W planning peak still exceeds the X1203's 25.5 W rating. Operating
   restrictions and the lower estimated load are not proof. EVF diode/LDO feed selection, back-feed, boot/transients,
   pigtail voltage drop/fuse heating, pack/BMS and thermal tests remain open. No power component was silently chosen.
5. **Thermal/airflow:** the paused study predates r5, contains an approximate cooler/fin model and lacks a measured
   fan curve. It is explicitly labelled historical; no new vent or duct was justified by those results. Rebase its
   geometry and validate assumptions before using it for a thermal claim; G-W11/G-W12 remain bench tests.
6. **Assembly and ergonomics:** cable bend radii and strain relief, real FPC fold loading, full service isolation,
   the weighted grip/record/EVF mock-up, glasses/nose/hand access, warm surfaces, and repeat opening cycles.

Known thin-feature exceptions and FR1 remain gated/exploratory. The optional fourth collar anchor, housing-clamp
Plan B, new lens adapters, shortened FPC and power alternatives are not adopted by this polish pass. These depend
on measurement or a user choice; inventing dimensions would hide the actual remaining work.
