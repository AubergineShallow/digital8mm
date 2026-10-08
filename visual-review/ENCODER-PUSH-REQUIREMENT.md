# D2 exposure encoder push acceptance

Acceptance guidance integrated into the cloud-polish MP-ENC/G-MP-ENC and G-W9 work. The original geometry measurements are from the immutable r5 source. Required switch travel remains unknown, and no physical control test is claimed.

## Finding

The exposure encoder is push-capable, and WIRING section 8 makes a reset function available. The current fit gate verifies only shaft fit and the knob rest gap. It does not verify axial push travel. A knob can rotate normally yet stop against the panel or bushing before the switch closes.

Source evidence:
- `layout.py`: panel outer plane `YL = 35.0`; `KNOBS["knob_exp"]["y"] = (35.2, 44.2)`.
- `layout.py`: fixed bushing tip `ENCODER["bushing"]["a"][1] = 37.2`.
- `printed_small.py::build_knob`: recess roof is bushing tip + `FDM["SLIDE"] = 37.45`.
- Therefore unloaded panel clearance is 0.20 mm and unloaded bushing-roof clearance is 0.25 mm. The first-contact limit is at most 0.20 mm, before print/finish error or a positive running-clearance allowance. These are assembly-coordinate distances, not a measured switch travel.
- `MEASURED-PARTS.md`, MP-ENC: no push travel or full-stroke clearance record exists.

## Datum definitions

Use the fitted production panel, encoder and knob. The encoder must be fully latched in its actual cradle and the knob fitted to the depth intended for normal operation.

1. Panel datum P: the local outer panel plane, nominal Y = 35.0 mm. Positive Y points out of the control face; a press moves the knob and shaft in negative Y.
2. Fixed bushing datum B: the outer end of the stationary threaded bushing. Do not confuse this with the moving shaft shoulder or tip.
3. Rest datum K0: the nearest rigid knob underside face over the panel, with no finger load and the switch released.
4. Recess datum KR: the inside roof of the knob recess directly above the stationary bushing.
5. Travel s: the negative-Y displacement of the moving shaft/knob from the released position. Measure it at the shaft or knob using a dial indicator/caliper with the panel fixed, not by hand-force displacement of the whole panel.

Record gP = K0 - P and gB = KR - B after painting/finishing. Record the encoder part/variant, actuation stroke, release stroke, rated/full permitted stroke where available, and any drawing tolerances. Record whether the knob slides on the shaft or the cradle visibly deflects during the operation; neither is acceptable as a substitute for real switch travel.

## Acceptance procedure for MP-ENC and G-W9

- Measure the actual part before freezing knob height and recess depth. Record reliable contact closure and release over at least ten normal presses; use the manufacturer's allowed travel and force limits when available. If the switch travel specification is unavailable, leave it unconfirmed until the installed test is recorded.
- Choose the required operating stroke from the actual part data and repeated test, including its stated tolerance/overtravel. Do not populate the CAD parameter with a generic encoder value.
- Parameterize `required_push_travel_mm` as unknown until that record exists. Derive both rest gaps from the model, and report the available first-contact travel as `min(gP, gB)`.
- At the required operating stroke, the knob must clear both the panel and the fixed bushing by the declared axial running allowance. Use the project's existing slide allowance (0.25 mm) unless a validated fit record explicitly establishes another allowance; never infer allowance from successful rotation alone.
- Keep sufficient measured D-flat engagement and no axial shaft preload at rest. The knob must remain removable by the documented method. Do not hide the through bore with a separate cosmetic cap.
- Turn throughout the useful range, then press and release with the production panel closed. There must be no panel rubbing, bushing stop, binding, switch held closed at rest, accidental reset while rotating, or knob migration. Verify the reset behavior on the EVF under G-W9; software-only tests do not close this hardware gate.
- If it fails, raise the knob mounting/underside clearance and deepen its bushing recess as required by the measurement, then recheck shaft engagement, envelope/hand clearance, printability and the CAD operation sweep. Reprint only the affected part if the revised design permits.

## Example check (symbolic, not an assumed hardware dimension)

`panel_remaining = gP - required_push_travel_mm`

`bushing_remaining = gB - required_push_travel_mm`

`pass = measured_travel_is_current and min(panel_remaining, bushing_remaining) >= axial_running_allowance_mm`

For the existing r5 gaps this reduces to `min(0.20 - s, 0.25 - s)`. No positive stroke can satisfy a 0.25 mm residual allowance. The current CAD does not establish push readiness; this should be an explicit uncommissioned control operation, not a fabricated pass or a reason to invent a switch dimension.

The encoder remains the exposure control and the physical 18/24 selector remains unchanged. No new menu, indicator, printed part, or external control is proposed.
