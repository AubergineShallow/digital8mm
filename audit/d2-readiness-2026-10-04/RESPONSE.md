# Response to the D2 print-readiness and simplification audit

To: the reviewer of `REVIEW.md` (4 October 2026). From: the D2 rectification team (Claude), 5 October 2026, 03:30
machine time (UTC+8). Full record: `cad/gs8-d2-v1/RECTIFICATION.md`; next steps: `cad/gs8-d2-v1/HANDOFF.md`.

**Evidence base.** One rebuilt and re-checked CAD state: receipt `cad/gs8-d2-v1/out/build-receipt.json`, built
2026-10-05 03:39:36 +0800, `checks.json` SHA-256 `acbc5867...8fb4`: 21 of 21 computed checks pass (526 rows), 0
stubs; a Fujinon/1 mm-sweep run on the same sources also passes (hash-linked). These are computed checks on CAD solids
and purchased-part proxies. **Nothing was printed, sliced, bought, measured, assembled or powered.** The four physical
evidence states in the receipt are all "not run". A read-only re-check modelled on your `check_artifacts.py` (not
run itself, as it writes into this folder) found all 16 source, 64 output and 4 gate-doc hashes matching and all 35
STLs (11 parts, 24 coupons) watertight. We do not claim the camera is complete. Your baseline is preserved
(`out/_r1-2026-10-04/`, `baseline-r1-2026-10-04.zip`). No gate was closed by changing a threshold or by a calculation.

## Per finding

### 1. Pi service is deliberately destructive: **accepted**

- **What changed.** The 4 floor snap hooks are deleted. The stack is located only by its 4 boss pockets and is held
  down by a removable printed keeper on 2 PT 3.0 x 12 PH1 screws (same driver). We compared release windows, relocated
  latches and a removable keeper by parts, access and repeat effort (`NOTES.md` "r2 R1 options"). Our own verifiers
  found that the hood, which must come off first, was still held by 4 hooks with no modelled release. Two of them now
  release with 2 straight pins pushed through holes in the right wall, which stay in and hold the hooks open. The
  other two have a 45 deg return catch and cam out on a straight lift. A post on the hood now stops the far corner of
  the stack. Procedure and tools: `ASSEMBLY.md` s7 items 8-10 (PH1, 2 pins, tweezers, ESD strap).
- **Computed evidence.** `removals` hood_off / keeper_out / pi_out: 0 mm3, with no undeclared release. `release_access`:
  the pin reaches the hook tooth with 0 mm3 on any other part, at a beam strain of 2.26 % with Kt (limit 2.5 %).
  `boss_geometry` keeper bosses: wall 2.55 and 2.35 over 5-95 % of the depth (need 2.25). `stack_retention`: the stack
  CoM is 16.7 mm inside the retention hull, and the largest lift at a boss pocket is 0.19 (limit 1.9).
- **Remains: physical, not run.** Insertion and removal with the stated tools on printed parts, repeated (G-KEEP-1: whole
  keeper, a floor coupon, 2 stand-in boards on the real X1203 kit, 5 cycles; G-SNAP-2 with 5 whole-hood cycles;
  G-PT-1), and then on the real stack without damage to the PCB or cables.

### 2. The thin-wall pass does not establish minimum local thickness: **accepted**

- **What changed.** There is now a registry of 87 named critical sections, measured by exact B-rep chords at the
  narrowest point. The minimum comes from the feature class: 1.6 for hooks, lugs, lips and bosses, 1.2 for walls and
  lands. A load-bearing part without an entry fails, and so does an entry without a class. The share screen is now
  secondary. The skirt necks (0.68-0.71) and groove lips (0.77) are gone. Measured on the current build: panel end
  land 1.30, cap key head 1.65, hood hook tooth 1.62, tub catch ledges 1.65, panel boss cap 1.60. Base/grip and cap
  now have 17 and 6 entries (r1 gave them no loaded samples).
- **Named exceptions.** The cap detent strip is still 1.25-1.5. It is below our 1.6 rule and is kept only against
  gate G-CAP-1. The nonstructural details are listed one by one: the 0.8 switch-slot skin, 2 sets of glyph ridges, a
  chamfer tip and a 1.08 vent web. A 0.25 feather found in the tub rear wall at the panel seam was fixed, not excused.
- **Remains: not run.** Printed retention pieces: G-CAP-1, G-PANEL-1, G-SNAP-2, G-KEEP-1 (24 coupon STLs, none printed).

### 3. Opening the panel depends on an inaccessible skirt barb: **accepted**

- **What changed.** Of the 3 options, we chose to eliminate the skirts (and their joint). Opening the panel is now 4
  PH1 screws and a pull, with no blade, no flexure and the optics left fitted. A new lock screw on the base slide
  means panel service no longer frees the base.
- **Computed evidence.** `removals` panel_off passes with the strap, cap, pack, lens and stick fitted, and the 4 screws
  pass the straight-driver audit in that state.
- **Remains: not run.** A repeated, non-destructive opening on printed parts with the strap fitted (G-PANEL-1). There
  is also a user decision: the black band under the panel is now 8 mm instead of 16.

### 4. Peak power 27 W exceeds the 25.5 W supply: **accepted; closure dependent on hardware**

- **What changed.** We keep the 27 W planning peak and state that the X1203 does not serve it. `WIRING.md` s4 now has
  workload states (idle, live view, record, write burst, startup) and operating restrictions R-P1..R-P8. Our verifier
  found the first burst estimate too low. The revised **estimated envelope** is 17.7-22.1 W, only 0.8-2.3 W under the
  bench limit without a CPU cap. We therefore recommend the CPU cap. A fallback with more headroom is named (2S1P
  pack + buck), with its geometry impact listed.
- **Remains: not run.** Your acceptance test, as gate G-W12: the full workload across 4.20/3.70/3.30 V, startup and write
  bursts, rail on a scope, reset and throttling bits, and temperatures at the connector and boost. Pass criteria
  P1-P7 are written, and so is the action on each failure.

### 5. Selected component interfaces are not yet frozen: **accepted; dependent on hardware**

- **What changed.** `MEASURED-PARTS.md` has one record per interface part, with the variant, photos, measurements, the
  CAD names each value drives, its gate and its pass criterion. Variants not yet chosen are marked as the user's
  procurement decisions; the pack SKU is one of them. The EVF is a bench assembly that comes before its carrier is
  frozen. The diode upper-bound gate is kept and is expected to require a regulated feed, which is carried as a BOM
  contingency. The EVF-selection gates (including panel release) are in the receipt's open-gate list (46 listed, 44
  open).
- **Remains: not run.** Every measurement and demonstrated assembly in those records.

### 6. EVF board restraint needs an explicit check: **accepted**

- **What changed.** A stop rib on the panel arrests +Y. A 6-direction check moves the board, with its HDMI plug
  envelope, until first contact and classifies the contact by board zone. The rails were cut back so that the stop is
  the PCB edge, not the HDMI receptacle (in r2 it carried 29 % of the -Y contact), the plug or the ZIF.
- **Computed evidence.** The PCB is the first contact in all 6 directions: +-X 0.25, +Y 0.30, -Y 0.31, +-Z 0.25.
  Section renders `section-evf-board-x137.png` and `-z78.png`.
- **Remains: not run.** The check with the real board and cable set (G-EVF-2).

### 7. Assembly simplicity is weaker than the exterior suggests: **accepted**

- **What changed.** `OPTIONS.md` quantifies parts, joints, tools and steps for 3 options: 18/24 in the encoder menu
  (-1 printed, -3 purchased lines, -2 joints, -2 tools), a shorter FPC (the 9-layer fold becomes one loop) and skirt
  elimination. The first two are presented, not applied. Skirt elimination is applied (finding 3). "One PH1" now
  refers to the screws only; the full toolset is in ASSEMBLY s1.1 (12 tools). The insert repair has no hex and has
  per-boss drill depths. Current counts: 11 printed, 7 PT screws, 10 harnesses, 10 solder joints (+2 per contingency).
- **Remains.** The user's choice on the two presented options.

### 8. Release status needs separate physical evidence: **accepted**

- **What changed.** The receipt's flag is now `cad_release_candidate`, with an explicit note that it is not a hardware or
  finished-camera claim. It has separate states: `cad_checks`, `slicer_review`, `coupon_validation`, `measured_fit` and
  `assembly_operation`. Each evidence state lists the items it needs and stays open until every item has a file with
  a recorded pass/fail verdict. Mass and print time are labelled estimates (about 293 g and 15.7 h, not a slicer
  result). Sources, outputs, coupons and the second run are hash-linked.
- **Remains.** The four evidence states; no slicer is installed here, so `slicer_review` stays "not run".

## Your proposed next work, now

1. **Preserve the baseline; fix Pi retention and skirt release first.** Done in CAD, with options compared. The
   physical repeat-service tests are open.
2. **Close the coverage gap; fix skirt, groove and panel geometry.** Done in CAD. Local measurements are in `checks.json`.
   The cap detent strip remains a named, gated exception.
3. **Reconcile power; record component assumptions.** Done in the documents. G-W12 and the measured-parts gates are open.
4. **Slice and print the coupons; record settings, fit, torque and release.** Not started: no slicer, no printer
   here. The coupon set covers every revised interface (24 STLs).
5. **Optional simplification.** Options (a) and (b) are presented with counts and trade-offs. (c) is applied. Pistol
   form, integrated EVF, no audio hardware and battery/storage access are unchanged.
6. **Rebuild after real parts and coupons; dry assembly and a powered recording test.** Not started; it depends on 3
   and 4. HANDOFF gives the order: measure the parts and run the EVF bench assembly (with G-W6), then print the
   coupons, the print set and G-W12.
