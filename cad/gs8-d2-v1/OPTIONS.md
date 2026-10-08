# GS8 D2: optional simplifications (`cad/gs8-d2-v1`)

Written 2026-10-05 (r2, R4) for audit finding 7 (`audit/d2-readiness-2026-10-04/REVIEW.md`). **Options (a) and (b)
are presented, not applied.** **User decision 2026-10-05 (evening): option (a) is DECLINED; the 18/24 selection stays a
physical switch** (`switch_1824` + `knob_fps`, D2-11). Option (b) stays open. They change the accepted D2 control arrangement or the camera cable, so the user decides.
Option (c) is R2's decision under finding 3; this file only records its counts. Nothing here is built or measured.

**Controls (r3, user decision 2026-10-05).** I/O = exposure dial (encoder, with its push switch), 18/24 dial, power plunger (on/off), run (record) button and the EVF; **no LED indicators** (user decision 2026-10-05: the plunger is black ASA, no light pipe; the Pi 5 onboard LEDs are switched off in config.txt; power-on and shutdown are shown on the EVF, WIRING s8). Option (a) below would fold the 18/24 dial into the encoder's EVF menu; it is still not applied (the decision names "the dials").

Baseline = the r1 build (2026-10-04 14:15:51, `baseline-r1-2026-10-04.zip`). r2 changes by R1 (Pi keeper) and R2
(panel opening / skirts) are listed separately in the totals, so each option's own effect stays visible.

## Totals

r3 (audit 2026-10-05 correction 1D): the current counts are generated from source in DESIGN.md s1 (`counts` block,
`make_tables.py`), and `make_tables.py --check` lints the handwritten counts below against it. The "r2 now" column
is the current release (r2 + the r2 fixer's J4 lock `s_j` and MP-FPC record).

| Count (whole camera build) | r1 baseline | **r2 now** (R1 keeper, R2 no skirts) | r2 + (a) 18/24 in the encoder menu | r2 + (b) 150 mm FPC | r2 + (a) + (b) |
|---|---|---|---|---|---|
| Printed pieces | 12 (7 enclosure + 5 accessories) | **11** (-2 skirts, +`pi_keeper`) | **10** (-`knob_fps`) | 11 | 10 |
| PT 3.0 x 12 PH1 screws | 4 | **7** (+s_k1, s_k2; +s_j, r2 fixer) | 7 | 7 | 7 |
| Other loose hardware in the camera | 3 (switch nut, switch washer, tripod nut) + X1203 kit (4 standoffs, 8 M2.5) | 3 + kit | **1** + kit (-nut, -washer) | 3 + kit | 1 + kit |
| Purchased lines removed | | | **-3** (switch D2-11, lead D2-25, PH pair D2-27; 5 pieces) | 0 (1 cable for 1 cable) | -3 |
| Harnesses (`layout.CABLES`) | 10 | 10 | **9** (-`fps_lead`) | 10 | 9 |
| Solder joints | 10 (+2 if the pack lacks an XT30) | 10 (+2) (+11 under EVF-feed option C, WIRING s4.8) | **8** (+2) (+11) | 10 (+2) (+11) | 8 (+2) (+11) |
| Contingency parts (r2 fixer) | | r3: +3 parts, +11 solder joints under EVF-feed option C (r4: +5 parts, +15 joints with the TLV75801P candidate; +3 / +11 with the fixed XC6220B45) (a 4.55 V LDO on a carrier replaces the 1N5817; recommended primary feed, user decision, quantity 0 in the BOM; WIRING s4.8, gate G-W13). The r2 "+1 regulated 5 V module if G-W6 fails" is withdrawn (a 5.0 V output breaks the 4.90 V maximum) | as r2 | as r2 | as r2 |
| Assembly tools (ASSEMBLY s1.1) | 12 | 12 (the keeper uses the same PH1; r2 fixer: the 3 mm release blade is replaced by 2 hood release pins) | **10** (-1/2 in socket or spanner, -junior hacksaw + file) | 12 | 10 |
| Steps | 10 | 10 | 10 (steps 1, 2, 4, 8, 9 each lose an operation) | 10 | 10 |
| Operations | | -2 skirt slides; +1 keeper (2 screws); the destructive Pi removal becomes 2 screws out | **-7** (see a.2) | **1 replaced**: the 9-layer S-fold becomes one relaxed loop | -7, 1 replaced |
| Keep-outs | 27 | 27 | 26 (-`ko_fps_up`) | 27 (`ko_fpc_loop` shrinks) | 26 |
| Measured-part records / new gates | | 10 records (MEASURED-PARTS, incl. MP-FPC, r2 fixer) | 9 (-MP-SW, -G-MP-SW) | 10 + G-FPC-1 | 9 + G-FPC-1 |
| Parts cost change (USD planning figures of `make_bom.py`) | | | about -9.5 (switch 6.0, lead 1.5, PH pair 1.0, knob filament) | about 0 | about -9.5 |

r2 changes by other owners (not options; for the full count): R2 eliminated the 2 skirts (option (c), applied:
-2 printed, -2 build operations, -2 service operations); R1's Pi keeper adds 1 printed piece (`pi_keeper`) and 2 PT
screws (s_k1, s_k2, step 4, same PH1; no new tool), see `NOTES.md` "r2 R1 options"; the r2 fixer adds the J4 lock
screw s_j (step 3, same PH1) and the MP-FPC record; r5 adds the lens collar (1 printed piece) and its 4 M3 screws in
heat-set inserts (same PH1; the iron's heat-set tip). **r5 totals before any option (generated: DESIGN.md s1 `counts`):
12 printed pieces, 7 PT screws + 4 M3 collar screws, 10 harnesses, 12 solder joints (r4: 10 + the 2 pigtail fuse-splice joints; +2 if the pack lacks an XT30; +15 joints, +5 parts with the TLV75801P or +11 joints, +3 parts with the XC6220B45
under EVF-feed option C, WIRING s4.8), 14 tools (r6: + the torque screwdriver and the collar centring gauge).** The current counts are generated in `electronics/gs8-d2-v1/BOM.md`
("Build counts").

## (a) 18/24 selection moved into the push-encoder EVF menu (DECLINED by the user 2026-10-05: keep the switch)

Kept for the record only; nothing below is to be applied.

### a.1 What changes

- The dedicated 2-position rotary (`switch_1824`) and its knob (`knob_fps`) are deleted. The panel keeps one dial
  (exposure). Frame rate is set in an EVF menu reached by the encoder's push switch (seesaw pin 24, today "free for an
  exposure reset", WIRING s8).
- **Record and exposure stay directly accessible**: the run button and the encoder rotation do not change.
- The frame rate is **shown permanently in the EVF overlay** ("18" / "24"), and it is **locked during a take**.

### a.2 Removed

| Kind | Removed | Count |
|---|---|---|
| Purchased | 18/24 rotary switch with nut and washer (D2-11); 2-way Dupont-to-PH lead 200 mm (D2-25); 50 mm PH pigtail pair (D2-27); the thin-wall heat-shrink on the lugs (from D2-46) | 3 lines, 5 pieces (switch, nut, washer, lead, PH pair) |
| Printed | `knob_fps` | 1 |
| Harness | `fps_lead` (GPIO13 + GND, pins 33/34) and its PH inline junction; header pins 33/34 become free | 1 harness, 1 junction |
| Joints | the 2 switch-lug joints | 2 |
| Tools | 12.7 mm (1/2 in) socket or spanner (D2-61); junior hacksaw + small flat file (D2-69) | 2 tool items |
| Operations | step 1 solder the PH pigtail to the lugs; step 2 fit the switch with its tab in the slot; step 2 nut finger-tight + 1/8 turn; step 2 cut the shaft 7.0 above the panel and deburr; step 4 plug the 18/24 lead on 33/34; step 8 mate the 18/24 PH junction; step 9 push `knob_fps` on | 7 |
| Records, gates | MP-SW / G-MP-SW; the switch part of G-HDMI; the GPIO13 line of G-W9; the 90 deg vs 30 deg indexing question | 1 record, 1 gate |
| CAD | `SWITCH_1824`, `KNOBS['knob_fps']`, `COTS['switch_1824']`, `CABLES` `fps_lead`, `KEEPOUTS['ko_fps_up']`, `ENGRAVE` `fps_ticks`/`fps_18`/`fps_24`, `MATES` (`knob_fps`), STEPS 1/2/4/8/9 text; in `printed_panel.py` the dia 10.0 switch hole, the anti-rotation slot and the nut seat | panel reprint |

### a.3 EVF and firmware implications

- **Menu**: push = open/close a one-line menu; rotate = 18 / 24; push again = confirm. A long press (>= 1 s) may be
  required so a brush of the thumb cannot change it. While recording, the menu refuses the change and shows "locked".
- **State**: the hardware switch held the state even with the camera off; the menu needs a stored value. Store it in a
  small file on the microSD (written atomically on change), restore it at boot, default 24 if the file is missing.
- **Software**: `ControlState.fps` comes from the stored menu value instead of a GPIO read (the D2 adapter of
  `software/gs8-camera-evf` is not written yet; the release-v1 `controls.py` reads FPS from expander bits). The EVF
  overlay draws the frame rate at all times. New tests: menu lock during a take, persistence across a power cycle.
- **Loss**: the frame rate is no longer visible or settable with the camera off, and D2 loses its second dial, part
  of the concept's exterior identity (hero render: "dial panel with the two knobs"). That is why this is the user's
  decision.

## (b) A shorter camera FPC (100-150 mm)

### b.1 Why

The stocked 200 mm 22-to-15 "Standard-Mini" cable needs a **9-layer S-fold** over the cooler fin end (`ko_fpc_loop`,
x -42.5..-29.7, y 2..19.5, z 36.6..56). That fold is the fiddliest operation of step 7 and a wear point.

### b.2 Length needed [est]

From CAM/DISP 1 (x -60..-50, port edge, z about 20) up to z 36.5 (about 17), across to the camera rear (about 28 in
x and 28 in y, with 2 flat 45 deg folds to turn the flat cable), down to the 15-pin connector (about 6), plus 2 x 5
of connector entry: about 100-110 mm. Step 7 brings the camera in from the left, 11 mm behind its seat, with the FPC
already plugged into it, so the cable needs about 20-30 mm of insertion slack: **about 120-140 mm in total.**
**150 mm is the candidate** (one relaxed loop of about 10-30 mm). 100 mm is probably too short for step 7.

### b.3 Candidates

| Candidate | Length | Status |
|---|---|---|
| Raspberry Pi official 22-to-15 "Standard-Mini" | 200 mm shortest (200 / 300 / 500 class) [recalled, not re-read] | current D2-20 |
| Third-party 22-to-15 Pi 5 camera FFC (Arducam, Waveshare and marketplace listings) | 100 / 150 mm class [recalled, not re-read] | candidate; pinout and contact side vary by vendor: gate G-FPC-1 |
| Adapter board + 2 cables | any | rejected: +1 part, +2 connectors |

### b.4 Gate G-FPC-1 (new, before the route changes)

- **Pinout**: continuity of all 15 conductors against the official cable (beep table, 22-pin position to 15-pin
  position), no conductor shorted to its neighbour.
- **Orientation**: the contact side at each end matches the official cable at the Pi 5 CAM/DISP 1 and the GS camera
  connectors (photograph both ends next to the official cable).
- **Function**: `rpicam-hello --list-cameras` lists the imx296 on CAM/DISP 1; 10 min of preview at the sensor's
  maximum rate with no CSI/CFE errors in `dmesg`.
- **Route**: on a printed tub (or the route mock-up), the cable reaches both connectors through step 7's insertion
  path; bends no tighter than r 1; no crease at either latch. Length 150 +5/-0.

### b.5 Effect

Parts 0, joints 0, tools 0. `CABLES` `fpc` length 200 -> 150; `ko_fpc_loop` shrinks to the loop's real size (re-run
the camera, hood and panel sweeps); the step 7 text drops the S-fold. If G-FPC-1 fails, keep the 200 mm cable.

## (c) Skirt elimination (R2, finding 3)

R2 decided this under finding 3 (panel opening without the inaccessible skirt barb): **the skirts are eliminated** in
r2 (`layout.SKIRTS_ELIMINATED = True`; `skirt_l`/`skirt_r` removed from PARTS, STEPS, MATES and INSERTIONS). Unlike (a)
and (b), it is **applied**, because it is the fix for a finding. R2's reasoning, the comparison of its options and
the new base-edge details are in `NOTES.md` ("r2 R2") and `RECTIFICATION.md`; the counts below are read from
`layout.py` at 00:13.

| Kind | Removed | Count |
|---|---|---|
| Printed | `skirt_l`, `skirt_r` (1.6 x 116.5 x 16 strips) | 2 |
| Joints | J5 dovetails (2) and their barbs `skb_l`, `skb_r` | 4 features |
| Operations | step 3 slide `skirt_r` on until the barb clicks; step 8 slide `skirt_l` on; service: pull `skirt_l` -X 125 against a barb with no tool access before the panel can open; teardown: pull `skirt_r` | 2 build + 2 service |
| Tools | none (the hood release tool stays: since the r2 fixer, 2 dia 1.5 pins instead of a blade) | 0 |
| Gates | G-SKIRT-1; the barb pull-off record of G-SNAP-2 | 1 gate + 1 record |
| Thin features | the skirt key necks (0.68-0.71) go with the skirts; the base groove lips (0.77) go with the grooves (r2 build: base_grip sampled minimum 1.44, every registered base_grip section >= its min_mm) | |
| What replaces them | the 2 panel boss tabs fill the lip notches flush (layout J3 comment) | |

With (c) applied, the r2 printed count is **10** before R1's keeper (12 - 2) and **11** with it. Options (a) and (b) apply on top: (a) -1 printed (`knob_fps`), (b) 0.
