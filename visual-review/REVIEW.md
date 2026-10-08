# D2 visual and ergonomic review

Final review, 2026-10-07 SGT. Reviewed the original r5 render pixels, source design/control contracts, corrected panel pixels, and the final cloud-polish assembly/part STEP. The final Kowa receipt is 806c7b381e1133a5e69c2d1547d915ac305bec2e1cb5e5cf168f74d81eae4832. All dimensions below are CAD/source values, not physical measurements.

Both lens variants have passing computed CAD/integrity reports. All 53 physical gates remain open. The gallery is an intended-finish visualization of the separate cloud-polish fork, not a fabricated or commissioned camera.

## Recommendation

Preserve D2's approved architecture and silhouette. The silver body with black roof/front, integral black grip and two unequal dials already reads as one coherent camera. The best next improvements are verified control operation, a more legible realization of the already-specified finish, and clearer service/bench instructions. A new shell, decorative trim, knob caps, added finger grooves or hidden-screw cover would add risk without evidence of a benefit.

The body, grip position, physical 18/24 switch, absence of LED indicators and absence of audio are retained. The floating-camera/per-lens collar architecture is the current design authority. FR1 remains an unadopted exploration.

## Findings and safe changes

### V1. Exposure-encoder push clearance is not established (new functional finding)

The rest gap between knob and panel is only 0.20 mm; the bushing-to-recess-roof gap is 0.25 mm. WIRING describes a push-capable exposure control, but MP-ENC tests shaft fit and rotation without measuring push travel. A successful fit/rotation check therefore cannot establish that the button can be pressed.

Integrated in the working correction: the datum-defined, travel-aware requirement in `ENCODER-PUSH-REQUIREMENT.md` is reflected in MP-ENC/G-MP-ENC and G-W9; keep the travel parameter unknown until the actual part is measured. Report the current first-contact allowance rather than inventing a switch dimension. Any needed gap/recess change must follow the actual travel measurement; retain D-flat engagement, removal access and a positive end-of-stroke gap. The D2 integration guide now explicitly marks push-reset as uncommissioned until MP-ENC/G-W9 verifies the installed knob/panel travel.

Source: `layout.py` ENCODER/KNOBS; `printed_small.py::build_knob`; `MEASURED-PARTS.md` MP-ENC; electronics WIRING s8/s9.

### V1b. Encoder latch teeth now have the intended load-bearing section

The deeper panel inspection found a 1.02 mm tooth root in the original STEP. The corrected panel increases the tooth land from 0.4 to 1.0 mm, giving a checked 1.62 mm root while retaining the catch location and flexible beam. This strengthens the intended retention geometry without changing the exterior control layout or adding a part. Coupon and installed-control tests remain required; a stronger latch is not permission to use cradle flex as switch travel.

Source: final panel STEP, `printed_panel.py`, and the panel refinement critical-feature results.

### V2. Existing finish intent is absent from the baseline renderer (presentation issue, not missing architecture)

In the baseline hero, the engraved labels read almost the same tone as the silver panel, the small selector index merges into its black face, and the black collar/front/lens boundaries are difficult to distinguish. The encoder center also appears blue because the entire encoder proxy receives its PCB color. This does not prove that the physical shaft is blue or that a new knob cover is needed.

Action implemented in review visualization: keep exact geometry; use broad controlled illumination to reveal edges; distinguish satin ASA, matte TPU and hardware; show black fill only on the existing panel engraving floors, white fill on the existing selector index and power symbol. These finishes are already called for by ASSEMBLY step 2 and the part print notes. Use a neutral hardware material for the visible shaft rather than the PCB's blue. Preserve the through bores, recesses and knob count.

Do not mistake the finish visualization for a tested paint, surface roughness specification or procurement choice. No physical finishing was done. A raw/unfilled control view should accompany the finish view when a comparison is useful.

The panel refinement also pins DejaVu Sans Bold by font file and SHA-256, replacing the platform-dependent Arial fallback. A render of the rebuilt candidate STEP was inspected: the badge, exposure label, +/- and 18/24 digits are legible, aligned and unclipped. This is a rendered-layout observation, not a claim that a 0.4 mm nozzle or a particular paint has reproduced them.

Source: baseline `out/renders/hero.png`; final panel STEP and `renders/controls.png`; `build_d2.py::COTS_COLOUR`; `printed_panel.py` print notes; `printed_small.py` print notes; ASSEMBLY step 2.

### V3. 18/24 index alignment remains a real procurement gate (known, still open)

The current graphics place the two states 90 degrees apart. MP-SW already records that the unchosen switch's actual indexing angle must be confirmed, and requires both positions to align within +/-5 degrees. A beautifully paint-filled label can still be wrong for a procured switch.

Action: retain the physical switch and its two labels; measure the actual indexing angle before freezing the panel. Update the existing ENGRAVE and knob index parameters if required. Do not turn the selector into an EVF menu or imply that the drawn 90-degree indexing is hardware verified. The obsolete MP-SW procurement text suggesting that OPTIONS (a) could remove the switch has been corrected in the working copy, because that option was explicitly declined.

Source: MP-SW; OPTIONS opening decision; layout ENGRAVE fps items.

### V3b. The displayed selector shaft and knob do not share the same D-flat orientation (new proxy/check finding)

The close-up shows the shaft protruding into the flat-side sector of the knob bore. Source inspection confirms `cots.switch_1824` makes its shaft flat point upward (0 degrees), while `KNOBS["knob_fps"]["index_deg"] = 45` rotates both its bore flat and index. The pair is a declared mate and therefore excluded from general interference testing.

Pinned CadQuery 2.6.1 on the saved knob STEP reports 8.99165 mm³ overlap with the source shaft proxy. Rotating only the moving shaft by -45 degrees about +Y, matching the displayed knob state, gives exactly 0 mm³ overlap. This is a proxy-state inconsistency, separate from the unmeasured physical switch indexing angle in V3.

Implemented in the working correction: the proxy shaft's displayed orientation follows the knob's displayed state, and a targeted nominal control-mate check cannot be hidden by the general mate exception. The regression covers aligned 0, +/-45 and 90 degree states and rejects the planted original mismatch. Leave the fixed switch body, nut and anti-rotation tab fixed. No production exterior change or guessed switch travel is required. Evidence: `control_geometry_probe.json`; the original diagnostic used pinned CadQuery 2.6.1. The current core regression covers the repaired mate.

The same pinned B-rep probe confirms V1: zero overlap at 0.20 mm exposure-knob motion, 3.796 mm³ panel overlap at 0.21 mm, and bushing overlap beginning beyond 0.25 mm (0.140 mm³ at 0.26 mm).

### V4. Collar detail refinement should serve seating and assembly

The visible three-anchor collar is appropriate to the adopted load path. It replaces the old turret rather than adding a cosmetic layer. The existing reviewer-confirmed pinch washer seat and bridge defects are the right detail improvements: provide full washer support/clearance and a deliberate print bridge strategy. They have more value than hiding the screws or making the collar visually smaller.

The final mechanical integration includes these seat/print-stock corrections and their checks. Preserve the front driver axes and last-operation top pinch access. Do not add a trim plate or cover that obscures the lens fixed-band boundary, the slit, or the screws required for service.

Source: R5-BRIEF; review_assembly A1/A2/A3; current hero and exploded pixels; printed_collar.py.

### V5. Preserve the clean exterior, but expose service dependencies in the deliverable

There are no dangling exterior cable runs in the assembled geometry. The rear storage sleeve sits at the rear-body datum; the battery connection lives in the grip. Concealment has already been achieved by the architecture, and adding covers would increase parts and obstruct the existing access paths.

The service dependency is more important: internal service starts with shutdown and physical pack isolation; panel removal disconnects its two leads; collar anchors are driven before the lens; the floating camera must be supported for thread start. An exploded picture alone can incorrectly suggest simultaneous or arbitrary removal.

Action: label the new exploded picture as illustrative separation, disclose that harnesses are omitted, and link it to the real assembly/isolation procedure. Incorporate review A4/A5/A6 in the assembly wording where supported: bench support before removing the tripod block, explicit forward support of the floating camera during thread start, and no unsupported lens threading. The final assembly instructions incorporate the supported sequence corrections.

Source: ASSEMBLY s7/P1-P4 and steps 7-8; review_assembly A4-A6; baseline exploded/step-07/step-08/step-10 pixels.

## Ergonomic dimension audit

| Item | Source/CAD result | Interpretation and remaining check |
|---|---|---|
| Main body | 154 x 70 x 100 mm | Approved block proportions; changing them would disturb most packaging and interface contracts. |
| Width at exposure dial | 79.2 mm overall, versus 70 mm body | The dial protrudes 9.2 mm on the left. Retain unless actual hand use shows a problem. |
| Grip column | 48 mm fore-aft x 30 mm across x 102 mm high; corner radius 9 mm | Rounded rectangular, not circular. Calculated perimeter is about 140.5 mm (same perimeter as a 44.7 mm circle), but this is not a fit standard or a claim of comfort. |
| Grip junction | Existing 3 mm blend to base | Already softens the web-of-hand contact. Do not remove material near the load path or deepen grooves without structural checks. |
| Record control | 13 mm cap; center 13 mm below grip top; projects 2.5 mm beyond nominal grip front | A clear tactile/visual primary control. Verify reach and accidental activation with the user's normal grip, strap tension and shooting posture. No position change is justified by a render alone. |
| Dial separation | Centers 60 mm apart; 28/20 mm diameters; nearest circular edges 36 mm apart | Strong diameter/position distinction. Keep common knurl language; verify finger operation while supporting the camera and without blocking the finder. |
| EVF placement | Eye axis 16 mm left of body center and 78 mm above body bottom; cup lip 33.6 mm behind rear body | Gives a defined eye approach corridor, not proven nose/eyeglass clearance. Existing SPEC mock-up item remains open. |
| EVF adjustment | Housing side window x -170.2..-154.2, z 66..90; diopter radial clearance 1.25 mm | Preserve window and TPU sleeve position. Check full diopter range with the actual eyepiece, glasses if used, and normal finger access. |
| Static fore-aft balance | Kowa 895 g, center of mass 1.5 mm forward of grip axis; Fujinon 781 g, 9.8 mm behind | Both calculated centers remain over the 48 mm grip footprint. This supports preserving grip position. It does not prove stable filming, structural stiffness or comfort. |
| First-order gravitational pitch moment | About 0.013 N m Kowa; 0.075 N m rearward Fujinon, from listed masses and offsets | Computed comparison only. Actual lens, battery, cable and hardware masses must update the model. |
| Cable routing | Ten harnesses and declared internal corridors; bend-radius/real connector gates remain open | Keep service slack and connector strain relief. No finish render can validate a cable bend or pack-insertion pinch. |

## Focused physical checks to keep open

Use existing mock-up/measurement gates rather than inventing a validated ergonomic result:

1. Assemble an unpowered weighted mock-up for each lens mass case. With the strap fitted, verify secure normal holding, index-finger record reach, release without a grip change, and no accidental record actuation while lifting or setting down.
2. Use the EVF from the preferred eye, with glasses if normally worn. Check nose/cheek contact, cup comfort, complete field visibility, diopter reach and head/wrist posture. Record the actual arrangement; do not infer handedness or eyewear from a drawing.
3. Turn both dials and press the exposure control with the production panel fitted. Verify actual angular indexing, no finger pinch, no panel rub, no unintended reset and no loss of control due to the strap.
4. Verify rear storage removal by finger, cap opening/pull-ribbon access and the real connector/cable passage. Do not judge these from a transparent ghost render.
5. Check warm external surfaces and exhaust where the left supporting hand naturally sits. Thermal work remains paused/open; no airflow performance is inferred from vents or render appearance.

## Ownership and delivered assets

The visualization scripts and review assets do not alter production CAD. Their separate material and lighting choices are for inspection and presentation. Final source and model changes are documented in the main fork handoff and cloud-polish notes.

The delivered renders use the final receipt-linked Kowa geometry, with all recorded Python/font sources and each part STEP checked before mesh export. Baseline and candidate diagnostic images are excluded from the delivered gallery. The new render path is Blender Cycles CPU with denoising disabled, separate from the original VTK renderer. See RENDER-PROVENANCE.json for hashes.
