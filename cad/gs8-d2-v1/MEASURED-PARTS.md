# GS8 D2: measured-parts record (`cad/gs8-d2-v1`)

Written 2026-10-05 (r2, R4) in response to audit finding 5 (`audit/d2-readiness-2026-10-04/REVIEW.md`). **Status of
every record: not measured.** Nothing has been bought. Every value in the "CAD value" column is a proxy from
`layout.py`, a listing or an estimate. No gate here is closed in CAD, and none can be.

How to use it:
- One record per purchased part whose real dimensions or behaviour decide printed geometry or the assembly.
- On receipt, fill in the "Measured" column (calipers 0.01 mm, three readings, report the largest for envelopes and
  the smallest for holes/bores), take the photographs, and file both under `measured/<record id>/` next to this file.
- If a measured value falls outside the pass criterion, change only the listed `layout.py` names, rebuild, and re-run
  the listed checks. Do not touch parts that the measurement does not affect.
- **Order:** MP-PACK, MP-X1203, MP-CAM, MP-HDMI and **MP-EVF (bench assembly)** come before the full print set.
  MP-EVF in particular must pass **before the EVF carrier is frozen** (tub collar and board slot, panel cap, hood
  eyepiece housing). The coupons of PRINT-GUIDE s6 can be printed in parallel.

Gate ids: `G-W*` are in `electronics/gs8-d2-v1/WIRING.md` s9, `G-*` in `SPEC.md` s10 and DESIGN s9. The EVF gates of
`electronics/gs8-evf-v1/EVF-SELECTION.md` s3 (its `G1`-`G9`, `G4b`) are written **`EVF-G1` ... `EVF-G9`** here and in
the build receipt (r2 fixer, verifier E-V-E5: the receipt's `hardware_gates` now lists them, source EVF-SELECTION.md
hashed). `G-MP-*` ids are new here (r2).

**Status (r3, 2026-10-05).** Done on this machine: the CAD proxies in `layout.py`, the computed CAD checks, this
record and its pass criteria. **Not done:** procurement (no part ordered or received), printing or slicing, any
measurement or photograph, any bench assembly or power-up. Every "Measured" field is empty and every gate here is
open.

**r5 (2026-10-06, heavy-lens support).** MP-CAM is rewritten for the real GS camera stack and gains the lens line
(G-LENS). It must pass **before the tub, hood, panel or lens collar is frozen or printed**: the collar's bore and cone come straight from the lens
band, and the tub lip, counterbore, hood roll fin and panel keeper from `CAM`. The camera and lens are measured
together at bench step B0 (ASSEMBLY s2: tripod block off, back focus s set with the Kowa at infinity). The new
collar coupon gate G-COL-1 and the assembled sag acceptance G-CAM-2 are in SPEC s10.

**Exact variants (r2 fixer, verifier E-V-E7).** Where a record names only a class, the field now says
**"variant NOT chosen: procurement decision (user)"**: MP-PACK, MP-HDMI, MP-RUN, MP-SW and MP-FPC (length). These are
open user decisions (HANDOFF s5). The class text stays as the specification the order must meet.

## Summary

**Record count (r3): 10.** One record = one `## MP-<ID>:` section below, and every summary row starts with that
record's id: MP-PACK, MP-X1203, MP-CAM, MP-HDMI, MP-RUN, MP-EVF, MP-ENC, MP-SW, MP-STICK, MP-FPC. The Active Cooler
line is a second row of **MP-X1203** (measured in that record), not an eleventh record; likewise (r5) the lens line
is a second part of **MP-CAM** (the camera hangs on the lens, and both are measured together at bench step B0). Count rule for tools: the
number of distinct `^## MP-[A-Z0-9]+:` headings.

| Record | Part (BOM line) | Gate(s) | Drives (layout.py) | Blocks |
|---|---|---|---|---|
| MP-PACK | 1S2P 18650 pack (D2-13) | G-W1, G-MP-PACK | `COTS['pack']`, `CABLES` `pack_lead`, `COTS['xt30_pair']`, `KEEPOUTS['ko_xt30']`, `GRIP`, `CAP` | grip print |
| MP-X1203 | Geekworm X1203 + kit (D2-03) | G-W2, G-PI-1, G-MP-X1203 | `COTS['x1203']`, `X1203_KIT`, `PI`, `PI_BOSS`, the stack retention (r2: R1's `pi_keeper` and s_k1/s_k2, which replace `PI_HOOKS`), pigtail keep-outs | tub print |
| MP-CAM | GS camera (D2-05); r5 lens line: the lens (D2-06) | G-CAM-1, G-LENS (r5: + G-COL-1 coupons, G-CAM-2 assembled) | `CAM` (+ `CAM['status']`), `cots.gs_camera_parts`, `COTS['gs_camera']`; lens line `LENSES[...]['support']`, `collar_spec` | tub, hood, panel and lens-collar print |
| MP-HDMI | micro-HDMI 90 deg lead (D2-21) | G-HDMI, G-W7 | `CABLES` `hdmi`, `ko_hdmi_*`, `EVF['board_slot']` | tub, panel print |
| MP-RUN | run button (D2-12) | G-RUN-1 | `RUN_BTN`, `COTS['run_button']`, `CABLES` `run_lead` | grip print |
| MP-EVF | Hicenda kit + 0PE039-16X (D2-07, D2-08) | EVF-G1, EVF-G4, EVF-G7, EVF-G8, G-W6 (EVF-G4b), G-W13 (option C), G-EVF-1, G-MP-EVF | `EVF`, `EYECUP`, `COTS['hmx039']`, `COTS['evf_board']`, `COTS['eyepiece']`, `CABLES` `oled_flex`, `usb_5v` | **EVF carrier freeze** |
| MP-ENC | Adafruit 5880 (D2-10) | G-ENC-1, G-MP-ENC | `ENCODER`, `KNOBS['knob_exp']`, `COTS['encoder']` | panel print |
| MP-SW | 18/24 rotary switch (D2-11) | G-HDMI (switch part), G-MP-SW | `SWITCH_1824`, `KNOBS['knob_fps']`, `COTS['switch_1824']`, `ko_fps_up` | panel print |
| MP-STICK | SanDisk SDCZ880 (D2-09) | G-W10, G-MP-STICK | `STICK`, `STICK_SLEEVE`, `STICK_GUIDE`, `SCOOP`, `COTS['usb_stick']` | tub, sleeve print |
| MP-FPC (r2 fixer) | Pi 5 22-to-15 camera FPC, 200 mm (D2-20) | G-MP-FPC | `CABLES['fpc']` (length 200), `KEEPOUTS` `ko_fpc_up`, `ko_fpc_run`, `ko_fpc_loop` (x -42.5..-29.7, y 2..19.5, z 36.6..56: the 9-layer S-fold), `ko_fpc_cam` | step 7; tub, hood print |
| MP-X1203 (cooler line, r2 fixer; same record) | Raspberry Pi Active Cooler SC1148 (D2-02) | G-MP-X1203 (cooler line) | `COTS['cooler']` (top z 36.3), `PI['cooler_top']`; hood and FPC clearances above it | tub, hood print |

## MP-PACK: 1S2P 18650 pack

| Field | Content |
|---|---|
| Exact variant | **Variant NOT chosen: procurement decision (user).** The order must meet: 1S2P, 2 x 18650 high-drain cells (Molicel P28A or Samsung 35E class, >= 10 A continuous each), BMS >= 10 A continuous, UVP 2.5-3.0 V, 18 AWG silicone lead 60 mm, XT30U male, pull ribbon. Record on receipt: builder/vendor, cell make and model as printed on the cells, BMS part number |
| Photos | all 6 faces with a scale; the BMS (both sides if visible); the lead exit; the XT30 face showing polarity marks; the cell wrap print |
| Measure | outer L x W x H including wrap, BMS and tape (CAD box 38.0 x 20.0 x 72.0); lead exit position (end and corner); lead length to the XT30 body (CAD 60); XT30 body L x W x H; mass (CAD 105 g); open-circuit voltage; polarity |
| Drives | `COTS['pack']` box (-64.5..-26.5, -10..10, -108.8..-36.8); `CABLES` `pack_lead` length; `COTS['xt30_pair']` box; `KEEPOUTS['ko_xt30']`; the grip bay (`GRIP`) and `CAP`/`CAP_JOINT` |
| Gate and pass | **G-W1**: + on the marked contact; 3.5-3.9 V; BMS label >= 10 A. **G-MP-PACK** (new): measured envelope <= 38.0 x 20.0 x 72.0 in every axis; lead exits at the top end (toward z -36.8) and the XT30 pair lies inside `ko_xt30` when the pack is home; the cap slides shut with the pack in a printed grip (or a grip-bay coupon) without pressing the pack |
| If it fails | a larger pack changes `COTS['pack']` and `GRIP`/`CAP`: grip and cap reprint. Never shave the pack wrap |

## MP-X1203: Geekworm X1203 UPS board and its kit

| Field | Content |
|---|---|
| Exact variant | Geekworm X1203 (record the board revision silk-screen and the date code); its M2.5 kit (4 F-F standoffs, 8 M2.5 x 5 screws) |
| Photos | both PCB faces square-on with a scale; the battery pads close-up; the pogo pins side-on (free length); the USB-C; the edge components on all 4 edges; the kit parts |
| Measure | **Active Cooler (r2 fixer):** height of the fitted cooler top above the Pi PCB top and its footprint (CAD box x -72.8..-9.5, y -25.55..16.95, top z 36.3 = 16.2 above the PCB top z 20.1: `COTS['cooler']`, `PI['cooler_top']`; it sets the z clearance to the FPC fold and the hood); PCB outline and thickness (CAD 85 x 56, 1.6: `PI['x1203_z']` 6.0..7.6); mounting holes against the Pi pattern (58 x 49); standoff length (CAD **10.9**: `X1203_KIT['standoff']`, `X1203_KIT['standoff_z']`); pogo pin free and compressed height; battery pad positions (x, y from the Pi hole nearest the USB-C) and pad size; tallest part on each face (underside vs the floor bosses `PI_BOSS` top z 6.0); the parts within 2 mm of each edge; USB-C position (unused); kit screw head dia x height (CAD 4.5 x 1.75; SPEC limit 5.0 x 2.0) |
| Drives | `COTS['x1203']` (box, `features.pcb`, `features.pads`), `X1203_KIT`, `PI['x1203_z']`, `PI['pcb_z']` (and so every z above the Pi: cooler, FPC/HDMI keep-outs), `PI_BOSS`, the stack retention (r2: R1's `pi_keeper` fingers at the 4 former hook stations, 0.1 above the X1203 top), `KEEPOUTS` `ko_pig_wrap`/`ko_pig_under`/`ko_pig_in` |
| Gate and pass | **G-W2**: pads, reserved GPIO lines and the gauge address recorded. **G-PI-1**: no X1203 edge part inside the reach of the 4 keeper fingers (the former hook stations: USB edge y -20 / 12, port edge x -80 / -45); standoff 10.9 +-0.2; kit screw head <= 5.0 x 2.0 (ISO 7045 allows k 2.1: measure, FASTENER-POLICY F). **G-MP-X1203** (new): cooler top <= z 36.3 (16.2 above the Pi PCB top) with the FPC and HDMI keep-outs above it clear; PCB 1.6 +-0.1 (the keeper fingers sit 0.1 above the X1203 top face at z 7.6; a thicker board takes that clearance); every underside part clears the floor (z 2.5) by >= 0.3, misses the 4 boss pockets and, in plan, the lead keep-outs under the board (`ko_run_floor`, `ko_pig_under`, `ko_pig_in`, z 2.7..5.8); the pads reachable from the port edge so the pigtail stays in `ko_pig_wrap` |
| If it fails | standoff != 10.9 +-0.2: re-derive `PI['pcb_z']` and re-run every keep-out and sweep above the Pi before printing the tub. Pads elsewhere: re-route the pigtail keep-outs |

## MP-CAM: Raspberry Pi Global Shutter Camera stack and the lens line (r5 rewrite)

r5 (`R5-BRIEF.md`, J7-R float): the r4 record measured the mounting holes for 2 printed pins and a dia 36.5 ring
bore. Both belonged to a camera model that does not match the official GS drawing; the pins are deleted. The camera
now hangs on the lens and touches no printed part, so this record checks the real stack against `CAM` (every value
is from the drawing at 10.05 px/mm, an estimate or unconfirmed: `CAM['status']`) and, in its **lens line** (judge 3's
"MP-LENS"), the lens's fixed band that the collar clamps. The lens line is a second part of this record, like the
cooler line of MP-X1203, not an eleventh record.

| Field | Content |
|---|---|
| Exact variant | Raspberry Pi Global Shutter Camera (SC0926 class); record the PCB revision silk-screen. Lens line: Kowa LM6HC (default) and/or Fujinon HF6XA-5M, serial and marking as on the barrel |
| Photos | camera side view square-on with a scale (as `research/m12-drawings/gs_side.png`); the tripod block and its 2 screws before and after B0; the lock tab and its screw from both sides; front (adapter, BFAR) and rear (cover, 15-pin connector). Lens line: side view with a scale, both thumb screws, the knurl marked |
| Measure (camera; `CAM['status']` value in brackets) | direct C-flange-to-cover-rear distance at s = 0 and at the set s (record both in CAM.optics; component dimensions alone cannot reveal a hidden flange offset); adapter OD (CAD 30.75) and face to face (5.00 +-0.05) [drawing]; BFAR head OD and thickness (CAD 36.0 x 1.2) and the exposed BFAR face annulus outside the adapter (>= 0.8 radial for the lip catch) [drawing]; BFAR thread OD (CAD about 28.8) [drawing]; housing OD and depth (CAD 35.5 x 10.35) [drawing]; throat dia and depth (CAD 25.5 x 3.0) [unconfirmed]; lock tab width, top radius, depth and slot (CAD 10.16, r 22.1, 5.02, 0.8) and which side the lock-screw head is on and its size (CAD envelope dia 4.0 x 2.0 on both sides) [drawing; head side unconfirmed]; PCB (CAD 38 sq x 1.4) and cover (CAD 39.5 sq x 6.49) size and centring on the axis (+-0.2) [drawing]; 4 hole positions (30 square, dia 2.5) [drawing]; FPC socket position on the cover [estimate]; the tripod block (CAD 13.97 wide, 12.04 deep, 2 screws): it comes off and leaves nothing below r 18 [drawing; removability unconfirmed]; **s** = BFAR screw-out at Kowa infinity (bench step B0; CAD nominal 1.25) [unconfirmed geometric sample (B0)]; independently sourced sensor height above PCB and filter focus shift, if available (leave None if not, never back-fit assumed values); the total travel (CAD 0..3.0) [unconfirmed] |
| Measure (lens line, G-LENS) | mark the knurl, then turn focus and iris end to end: the knurl must not rotate; a dial indicator on its rear face reads <= 0.02 axial. Knurl OD (+-0.02; Kowa CAD 42.0), its rear-face position from the C flange (+-0.05; CAD +2.2, front +7.6) and its edge chamfer (CAD 0.3); the thumb-screw envelope (CAD focus at +14.4, iris at +33.0, r <= 24, width 3.8); the CoM (knife edge; Kowa CAD x 28.9 in the assembly frame, 28.3 ahead of the C flange); the rear protrusion (CAD C - 6.7) clears the camera filter at the recorded s. Fujinon: band dia 39 at +2.0..+7.8, all `'assumed'`. Any zoom: a fixed band of at least 15 mm |
| Drives | `CAM` (every key; `CAM['status']`), `cots.gs_camera_parts`, `COTS['gs_camera']`, `COTS['c_cs_adapter']`, `CAM['keeper']`, `HOOD['roll_fin']`, the tub lip and counterbore (`CAM['lip_d']`, `CAM['cb_d']`), `KEEPOUTS['ko_fpc_cam']`. Lens line: `LENSES[...]['support']` (and its `status`), `LENSES[...]['segments']`, `thumb_screws`, `layout.collar_spec`, `COLLAR`, `KEEPOUTS['ko_lens_thumb_*']` |
| Gate and pass | **G-CAM-1** (before the CAD is frozen): every camera value inside the `CAM` value, or `CAM` updated and rebuilt (then `j7_float` must pass again: body >= 0.5 lateral / 0.4 axial, BFAR >= 0.6 / 0.4, adapter >= 0.6). **G-LENS** (before tub/hood/panel/collar printing): the knurl does not move (<= 0.02) and the band values are inside `LENSES` (or updated and rebuilt); write the measured x0/x1, OD, edge chamfer, ring/thumbnail envelopes and CoM into LENSES, set its band status to 'measured', and rebuild. Rerun j7_float at both travel endpoints and the set s, lens_support, inserts, lens_clamp and the insertion/service sweeps on both selected lens variants. Regenerate affected tub, hood, panel and collar outputs before print; a changed band position is not a collar-only change. Then **G-COL-1** (coupons) and, on the assembled camera, **G-CAM-2** (SPEC s10) |
| If it fails | camera values or direct stack off: update CAM and its datum chain, then rebuild (do not fudge an unknown sensor height to close the chain) (the tub lip / counterbore, hood fin and panel keeper follow `CAM`); the tripod block will not come off cleanly: stop (it collides with the Pi envelope as D2 places the camera). Lens band moves (G-LENS fail): no collar for that lens; a collar on the locked focus ring (refocus by unpinching) or Plan B (SPEC s10: housing clamp) |

## MP-HDMI: micro-HDMI 90 deg lead

| Field | Content |
|---|---|
| Exact variant | **Variant NOT chosen: procurement decision (user).** The order must meet: micro-HDMI D to micro-HDMI D, 200 mm (+10/-0), thin shielded coax OD <= 3.0; Pi end 90 deg plug with the cable leaving upward; board end right-angle with the cable leaving -Y (EVF-SELECTION A3). Record the vendor listing and the plug moulding marks |
| Photos | each plug from 3 sides with a scale; the cable minimum bend held by hand |
| Measure | Pi-end plug height above the board when mated (CAD <= **8.5**, Q2); Pi-end plug body width and depth; cable OD; total length; board-end plug body L x W x H and its mated position on the Rev I board (the slot gap y 4..17) |
| Drives | `CABLES` `hdmi` length; `KEEPOUTS` `ko_hdmi_pi` (x -36.6..-27, y 24..32, z 17..41), `ko_hdmi_run` (z 39.6..44), `ko_hdmi_coil`, `ko_hdmi_evf`; `EVF['board_slot']['bottom_rail_gaps']` |
| Gate and pass | **G-HDMI**: Pi-end plug <= 8.5 off the board and inside `ko_hdmi_pi`; OD <= 3.0 along `ko_hdmi_run`; the board-end plug passes the slot gap y 4..17. **G-W7** (HDMI pin 19) before it meets the Pi |
| If it fails | taller plug: raise or widen `ko_hdmi_pi` and re-run the hood/panel sweeps; thicker cable: `ko_hdmi_run` |

## MP-RUN: run button and its cap

| Field | Content |
|---|---|
| Exact variant | **Variant NOT chosen: procurement decision (user).** Candidate named in the BOM: The Pi Hut Squid Button (the colour and listing are the user's order). The order must meet: pre-wired momentary push button, non-latching, red cap, female-socket leads, cap removable from its stem. Record the listing and the switch body markings |
| Photos | the button with the cap on and off; the stem; the lead and its sockets |
| Measure | cap OD (hole 13.6: `RUN_BTN['wall_hole_d']`) and height; body L x W x H (CAD 8.5 x 12.0 x 13.0: `RUN_BTN['body']`); stem section; travel; lead length (CAD 250) |
| Drives | `RUN_BTN` (body, cap, wall_hole_d, pad), `COTS['run_button']`, `CABLES` `run_lead` and its keep-outs |
| Gate and pass | **G-RUN-1**: the cap comes off its stem by hand and presses back on through the dia 13.6 hole, 5 cycles, with no damage to stem or cap and the switch still clicking; cap OD <= 13.2 (0.2 radial clearance); body inside the `RUN_BTN['body']` box |
| If it fails | a bonded cap: a different button class, or the cradle must take the button from the outside (grip revision). CAD cannot show that a cap detaches |

## MP-EVF: EVF-A bench assembly (panel release, board revision, optics, rail)

This is the most consequential record: the panel comes out of a kit prism, the board revision is unknown until
receipt, and the eyepiece is a separate part. **Build it on the bench, outside the camera, before the EVF carrier is
frozen.** The bench jig is a print of the tub rear segment (collar, OLED cell, board slot) plus the panel cap, or the
EVF coupons of PRINT-GUIDE s6 if they carry those features.

**Bench order** (each step only after the previous one passed; record results under `measured/MP-EVF/`):
1. EVF-G1 identity: photograph the kit as received (board both faces, flex marking, prism holder).
2. EVF-G7 panel release, then EVF-G8 flex measurement. Bonded panel: stop here (EVF-B or a bare-panel source).
3. EVF-G4 power range: board alone on a bench supply at 4.25 / 4.55 / 4.90 V.
4. G-W7 HDMI pin 19 isolation, then EVF-G2 timing on the Pi with the section 8 settings (stable 1024 x 768 at 60 Hz).
5. Bench jig: panel in the printed OLED cell with the foam pad, board in the printed slot against its stop with the
   real micro-HDMI plug and 5 V lead, eyepiece in the printed collar under the cap clamp.
6. G-MP-EVF focus, centring and restraint on the jig; G-EVF-1 pull-out and diopter.
7. G-W6 (EVF-G4b) rail on the real lead, on the X1203 bench feed of G-W4 (source max 5.355 V by default; r2 fixer:
   no longer "after G-W12", which needs the closed body and so the full print set). Expect the diode feed to fail
   the upper bound (WIRING s9). r3: the fail action **replaces** the diode by the 4.55 V LDO feed of WIRING s4.8
   (requirement R-EVF-REG, option C: r4 +5 parts, about +15 joints with the TLV75801P candidate, +3 / +11 with the fixed XC6220B45; recommended as the primary feed, user decision);
   then G-W13 (regulator on the bench), G-W6 on the regulated lead and a G-W7 re-run, all before the freeze.
8. Only then freeze `EVF` and print the tub, panel and hood for the full set. G-W12 comes after the print set.

| Field | Content |
|---|---|
| Exact variant | Hicenda Tindie kit "0.39 inch OLED 1024x768", option "Display+HDMI Board+Prism" (EVF-SELECTION A1): HMX039-V1 panel, flex FM04112-MF1-A (50.4) or FM04136 (60.4), HDMI driver board **Rev I** (ITE IT6801FN, about 28.5 x 27, traced EXT+/GND pads) or **Rev II** (26 x 26, 6-pin header). Display Components 0PE039-16X eyepiece (M29x0.75 spigot). Record the board revision, receiver IC and flex marking |
| Photos | EVF-G1: both board faces, the receiver IC, the flex marking, the connectors; the prism holder before and after release (clip or adhesive); the bare panel front and back with a scale; the eyepiece barrel and spigot |
| Measure | panel outline (CAD 15.6 x 13.6 x 1.93: `EVF['oled']`); flex length and stiffener (EVF-G8: 50.4 +-1, 8 +-0.5); board outline, thickness over the parts and the PCB plane (CAD 28.5 x 27 x 8: `EVF['board']`, `EVF['board_pcb_x']`); micro-HDMI receptacle position on the lower edge (CAD y 4..17); EXT+/GND pad or header position; eyepiece barrel OD (CAD 38.5), spigot length (4.5), eye-lip position (F - 20.3); **focus**: on the jig, the panel-to-flange distance at which the pixel grid is sharp with the diopter at mid travel (CAD `EVF['display_x']` = F + 6.0); **centring**: the image centre against the eyepiece axis |
| Drives | `EVF` (oled, oled_cell, board, board_pcb_x, board_slot, display_x, cap, collar, bore_d, barrel, spigot, diopter_clear), `EYECUP`, `COTS['hmx039']`, `COTS['evf_board']`, `COTS['eyepiece']`, `CABLES` `oled_flex` and `usb_5v`, the EVF board restraint (finding 6, R2/R3) |
| Gate and pass | **EVF-G7 panel release**: the panel (or panel + metal holder) comes out of the prism without cutting or prying on the glass; bonded = stop, use a bare-panel source or EVF-B. **EVF-G1 identity**: board revision recorded; Rev II changes the 5 V lead end to a 6-pin header lead (`usb_5v`). **EVF-G8 flex**: 50.4 +-1 (FM04112); FM04136 needs a longer-flex carrier. **EVF-G4**: board alone at 4.25 / 4.55 / 4.90 V, <= 0.30 A and <= 1.5 W at full white. **G-W6 (EVF-G4b, diode upper bound)**: as WIRING s9; the upper bound is **not** accepted from a typical diode drop. **G-W13** (r3, option C only): the regulator alone on the bench against R-EVF-REG (WIRING s9). **G-EVF-1**: spigot pull-out >= 20 N with the cap clamp; the diopter turns freely. **G-MP-EVF** (new): on the jig at the CAD `display_x`, the full 1024 x 768 image is sharp within the diopter travel with travel left at both ends, the image centre lies within 0.5 of the eyepiece axis, the board sits in its slot against its stop with the real micro-HDMI plug and 5 V lead fitted, and nothing presses on the OLED flex or the connectors |
| If it fails | focus or centring off: `EVF['display_x']` / `EVF['oled_cell']` (tub and panel cap reprint). Rev II or a different board: `EVF['board']`, `board_slot`, `ko_hdmi_evf`, `ko_5v_end`. Rail fails G-W6 (or option C is chosen up front): the 4.55 V LDO feed of WIRING s4.8 **replaces** the 1N5817 in the `usb_5v` lead (R-EVF-REG: band 4.39-4.71 V, dropout <= 0.30 V at 0.30 A, <= 0.29 W; carrier <= 16 x 7.5 x 4.5 in `ko_5v_up` z 40..56, no geometry change; +3 parts, about +11 joints); gates G-W13, G-W6 regulated run, G-W7 re-run. The r2 "5 V regulator" wording is withdrawn: a 5.0 V output breaks the 4.90 V maximum |

## MP-ENC: Adafruit 5880 encoder board

| Field | Content |
|---|---|
| Exact variant | Adafruit 5880 I2C STEMMA QT rotary encoder, encoder pre-soldered; A0 bridged (0x37). Record the encoder part on the board (shaft type and length) |
| Photos | both faces with a scale; the encoder side-on (bushing, shaft, flat); the 2 QT connectors |
| Measure | Push operation: actual encoder part, actuation/release stroke and permitted operating stroke with tolerance/overtravel (ENCODER.push.required_travel_mm stays None until recorded), resting knob-to-panel gap gP and recess-roof-to-fixed-bushing gap gB after finishing, D-flat engagement and any cradle deflection. Then PCB outline and thickness (CAD 25.6 x 25.3 x 1.6: `ENCODER['pcb']`); encoder body (CAD 12.5 x 13.5); bushing dia and length (CAD 7.0 x 5.0) and thread; shaft dia, flat and length (CAD D 6.0/4.5 to y 44.0); back-part height and position (QT connectors; CAD `ENCODER['back_parts']` 5.3 deep) against the side hooks at z 45..50 |
| Drives | `ENCODER` (pcb, body, bushing, shaft, shaft_flat, back_parts, panel_hole_d 7.5, cradle_hooks), `KNOBS['knob_exp']` (bore 'D 6.0/4.5'), `COTS['encoder']` |
| Gate and pass | **G-ENC-1**: the QT connectors and other back parts clear the 2 side cradle hooks (z 45..50) by >= 0.3. **G-MP-ENC** (new): the board drops into the panel cradle coupon and the hooks click (G-SNAP-2 cycle count); the bushing passes the 7.5 hole; the knob bore fits the shaft flat without play beyond 0.1 and the knob turns without rubbing. **Push remains uncommissioned:** current CAD gP = 0.20, gB = 0.25 mm; these do not establish switch actuation. At measured required stroke s, require min(gP - s, gB - s) >= 0.25 mm running allowance unless a validated fit record establishes another value. Ten normal presses must close/release reliably, without panel/bushing contact, shaft sliding, cradle flex as substitute travel, accidental reset while rotating or switch preload at rest. Verify the assembled behavior on the EVF under G-W9. Keep measured D-flat engagement and removability |
| If it fails | Update ENCODER/KNOBS from the actual part. If push bottoms out, raise the knob underside and deepen the bushing recess only as measurements require; recheck shaft engagement, envelope, hand clearance, printability and operation before a knob/panel reprint. Never choose a generic encoder stroke to make the check pass |

## MP-SW: 18/24 rotary switch and its shaft

| Field | Content |
|---|---|
| Exact variant | **Variant NOT chosen: procurement decision (user)**. The physical 18/24 switch is retained by the user's decision; OPTIONS (a) was declined. Candidate class: Lorlin CK1049. The order must meet: mini rotary switch with an adjustable stop, 6.35 mm shaft, nut + washer, anti-rotation tab, indexing angle stated on the listing. Record the maker's part number and the indexing angle |
| Photos | the switch side-on and from the shaft end (tab position); the stop washer set for 2 positions; the lugs |
| Measure | body dia and depth (CAD dia 25 x 13: `SWITCH_1824['body']` y 19.2..32.2); bushing thread and length (CAD dia 9.5 x 6.0); shaft dia and as-supplied length (CAD 6.35, cut to y 42.0); tab radius and size (CAD r 7.9, 1.2 x 2.5 x 1.5); nut AF and thickness (CAD 12.7 x 2.4); **indexing angle** between the 2 positions: the engraving (`ENGRAVE` `fps_ticks` at -45 / +45 deg, 90 deg apart) assumes 90 deg, while 30 deg is common for this class [est, recalled, not re-read] |
| Drives | `SWITCH_1824` (body, bushing, shaft, nut, panel_hole_d 10.0, anti_rot), `KNOBS['knob_fps']` (bore 'D 6.35/4.8', nut_recess, index_deg), `ENGRAVE` (`fps_ticks`, `fps_18`, `fps_24`), `COTS['switch_1824']`, `KEEPOUTS['ko_fps_up']` |
| Gate and pass | **G-HDMI** (its switch part: bushing and tab). **G-MP-SW** (new): the tab enters the panel slot and the nut seats on the panel face; after the cut (y 42.0 +-0.3, deburred) the knob seats with its face 0.2 off the panel; both positions line up with the engraved 18 and 24 within +-5 deg; GPIO13 reads low at 24 and high at 18 (G-W9) |
| If it fails | indexing angle != 90 deg: `ENGRAVE` fps marks and `knob_fps` index (panel and knob reprint). OPTIONS.md (a) removes this record |

## MP-STICK: SanDisk Extreme PRO USB 3.2 stick

| Field | Content |
|---|---|
| Exact variant | SanDisk Extreme PRO USB 3.2 solid state flash drive SDCZ880-256G (slider type). Record the exact SKU and the firmware string (`lsusb -v`) |
| Photos | the stick with the slider in and out, from 3 sides with a scale |
| Measure | body length, width and thickness (CAD 59 + 12 plug = 71, 21.3, 11.4: `STICK['body']`, `STICK['plug']`); the plug offset from the body centre; slider travel; mass (CAD 22 g) |
| Drives | `STICK` (axis, body, plug), `STICK_SLEEVE`, `STICK_GUIDE` (stick_section, sleeve_section), `SCOOP`, `COTS['usb_stick']` |
| Gate and pass | **G-MP-STICK** (new): width <= 21.3 and thickness <= 11.4 (the guide runs at + SL); the stick with the sleeve slides through the guide into the lower USB 3 port and out again by finger from the scoop, 10 cycles; enumerates at 5000M. **G-W10**: >= 100 MB/s sustained past cache on a part-filled stick, warm, EVF on, no USB resets |
| If it fails | `STICK` / `STICK_GUIDE` (tub and sleeve reprint) |

## MP-FPC: Pi 5 camera FPC, 22-to-15 pin (r2 fixer, verifier E-V-E7)

| Field | Content |
|---|---|
| Exact variant | **Length: variant NOT chosen beyond the stocked 200 mm (procurement decision, user).** Ordered as BOM D2-20: the official Raspberry Pi 22-to-15 ("Standard-Mini") camera cable, 200 mm. OPTIONS (b) presents a verified 100-150 mm cable instead (gate G-FPC-1 there) |
| Photos | both ends (contact side marked), the stiffeners, the cable laid flat with a scale |
| Measure | total length (CAD 200: `CABLES['fpc']['length']`); thickness over the conductors and over the stiffeners; stiffener lengths at both ends; width at each end (22-pin and 15-pin); **contact side** at each end relative to the Pi CAM/DISP 1 connector and the camera's 15-pin connector (sets the fold direction) |
| Drives | `CABLES['fpc']`; `KEEPOUTS` `ko_fpc_up`, `ko_fpc_run`, `ko_fpc_loop` (the 9-layer S-fold box x -42.5..-29.7, y 2..19.5, z 36.6..56.0), `ko_fpc_cam` |
| Gate and pass | **G-MP-FPC** (new): length 200 +-5; the S-fold (OPTIONS s(b)) laid by hand on the bench in a printed `ko_fpc_loop` box (or the closed tub) stays inside that box with no crease sharper than the cable's stated bend radius; both contact sides as the step-7 text assumes; camera image at the end of G-W3 with the cable folded |
| If it fails | longer or thicker: re-derive `ko_fpc_loop` and re-run the hood/camera/panel sweeps; or adopt OPTIONS (b) (user decision) |
