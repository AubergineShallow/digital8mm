# Panel thin-spot classification and correction

Scope: `r5-cloud-polish-20261007`, copied r5 source; 2026-10-07 SGT. This is computed geometry evidence only.

## Why the release was held

The fresh pinned Linux baseline produced two unclassified screen samples even though the original Windows receipt
reported none. The screen is seeded but its surface samples depend on tessellation order, so identical seed values
do not prove identical sample locations across exports. The original release summary did not block on this list.
The fork now adds a mandatory classification row to `critical_features`: any nonempty or malformed list blocks a
CAD-release claim. No screen threshold, class floor, sampling radius or physical gate was relaxed.

## Exact evidence on the captured original STEP

1. At (-67.2, 34.99, 36.66), the approximately 0.532 mm screen result is material between engraved exposure-label
   strokes. Exact BRep chords on the original STEP give 0.521940 mm in X but 2.800000 mm through the panel in Y.
   The panel backing is intact; this is a shallow decorative ridge, not a 0.532 mm enclosure wall. No new exception
   was used to clear the revised panel.
2. At (-66.52, 24.0, 69.95), the 1.049 mm screen result belongs to the encoder top-hook tooth. Moving 0.03 mm into
   its root gives an exact 1.020000 mm chord along Y, at X -66, -63 and -60 in the original STEP. All three source-
   built cradle teeth have the same 1.020000 mm root. Their beam thickness is 1.6 mm, but existing critical probes
   measured only those beams. The missing tooth-root section is load-bearing and must not be called cosmetic.

The captured original STEP established these values. The packaged `../../test_panel_refinements.py` reproduces
the source-geometry contrast and asserts the original/refined root thickness; no machine-specific scratch probe
is required to run that regression.

## Correction, invariants and regression

The encoder cradle land is now a layout parameter set to 1.0 mm rather than 0.4. This moves only each tooth's tip
and extra land 0.6 mm toward -Y. The catch plane, engagement, beam section, root/gusset and PCB location do not move.
The exact root 0.03 mm inside the beam face becomes 1.62 mm, above the unchanged 1.6 mm loaded-feature floor.

Three explicit tooth-root features are mandatory in `J12_encoder_cradle`. They are measured at multiple points
across each tooth's width. `test_panel_refinements.py` verifies all three 1.62 mm roots, plants the former 0.4 mm
land and recovers its failing 1.02 mm roots, and compares unchanged geometry ahead of the catch. The snap strain
calculation uses the new declared land. G-SNAP-2 remains unrun and must test the revised production coupon.

The existing encoder cradle coupon crop reaches Y = 22.0; the revised tooth tip is Y = 22.35, so the entire revised
feature is still included. The coupon must be regenerated from this panel, not reused from the baseline.

## Typeface reproducibility

`layout.ENGRAVE` declared DejaVu Sans, but `d2_common.engrave` actually defaulted to Arial. A cloud host may substitute
another font. The fork now uses the unchanged `fonts/DejaVuSans-Bold.ttf` file explicitly via CadQuery's `fontPath`,
with its permissive upstream license alongside it. SHA-256:
`a4c5bc453ca281d90ea079e596da7ae0dfeb5777497c29ec254e76d97ff6f890`.
The family/style/file/hash are declared in layout and included in receipt source hashes. Missing or modified font
bytes fail before engraving; arbitrary family overrides fail instead of silently falling back to another font.
This intentionally makes the actual geometry match the declared typeface, so the new lettering is visually reviewed.

## Revised panel evidence

The revised panel was rebuilt from source and checked by the packaged panel regressions and full release builds.
On that actual BRep:
- valid single geometry; no builder notes;
- every panel critical feature passes, including three newly measured tooth roots;
- thin-wall screen passes, minimum 1.199 mm (a nominal 1.2 mm end feature within the existing screen tolerance);
- unclassified thin-spot list is empty;
- no new nonstructural exception, widened classification radius or reduced structural floor.

The current full-build receipt and separate clearance/service/engraving probe remain the authority for integrated
packaging. Actual printability, fatigue, fit and retention still need the existing physical gates.
