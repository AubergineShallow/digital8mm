# SPEC-C6: plunger retention, tool 13 margins, hood release comb (BX-6, BX-12, BX-17)

Status: FINAL design spec after adversarial review, r7 blocker round, 2026-10-08 (designer 22:45-23:15 MPST, review
23:15-00:35 MPST). Nothing in the repo was changed except this file. The numbers below were re-computed against the
current r6 code. Probes are in the session scratchpad `r7/C6/` (probe1.py: layout numbers; probe2.py / probe3.py:
driver envelope family against the per-part STEP files and the COTS proxies; probe4.py: release comb envelope against
the `hood_off` context and the lifting hood) and `r7/C6-review/` (rprobe_driver.py runs: handle 30 x 250 and 40 x 250).
Nothing was printed, bought or measured. The review changed BX-12 (purchase range, handle length) and BX-17 (push
window derived from a tolerance stack, measured comb) materially; see "Review notes" at the end.

## 1. Problems restated (re-checked)

### BX-6 plunger (step 5)

| item | value (layout r6) | note |
|---|---|---|
| stem in tub hole | stem 11 x 6 in hole 11.6 x 6.6: 0.30 per side | `PLUNGER['stem']`, `['tub_hole']` |
| stem engaged in the 2.5 wall at rest | x -5.0..-2.7 = **2.30 mm** | free cocking up to about atan(0.6/2.3) = 14.6 deg |
| flange rear face at rest | x -2.5, **0.20 mm proud** of the tub face (XT1 -2.7) | the 0.4 recess (x -3.1..-2.7) is entered only after 0.2 of press |
| nib to Pi button | 0.25 gap, travel 0.60, press 0.35 of 0.45 | `layout_self_check` 'plunger travel presses button' |
| hood channel | `hood_pocket` x -2.5..-1.3, y 1.9..16.1, z 0.3..24.7: open at the plate foot | skin x -1.3..0 in front of it |
| skin inner face vs plunger front face | both at x -1.3: line-to-line | a declared slide mate (`MATES` hood/plunger) |
| plunger mass | about 0.4 g (0.37 cm3 ASA) | weight about 4 mN |

Correction to BLOCKERS BX-6: the flange does not sit "in a 0.4 mm recess" at rest. It stands 0.2 mm in front of the
tub face, so the recess gives no retention at all. With the hood absent, the plunger is held only by 2.3 mm of stem
in a hole with 0.3 mm clearance. Any nose-down tilt beyond the friction angle (about 17-27 deg for ASA on ASA) slides
it forward. Drift of more than 2.3 mm drops it out. Smaller drift is still a fault: the skin foot then lands flat on
the flange top (z 24.4) and the hood jams about 24 mm before home, because the foot has no lead-in. There is no
`plunger_in` insertion in `layout.INSERTIONS`, so no sweep covers the plunger at all.

### BX-12 tool 13 margins (steps 3, 8)

`checks.json` `driver` (envelope bit dia 6.5 x 40 + handle dia 30 x 100, `layout.DRIVER`). Where checks.json reports
"nothing within 15 mm" (null), the exact distance from probe2 is given instead, marked (p):

| screw | step | bit gap (part) | handle gap (part) |
|---|---|---|---|
| s_b1, s_b2 | 8 | 0.25 (base_grip, dia 7 cbore) | 12.31 / 24.23 (base_grip) |
| s_r1, s_r2 | 8 | 0.25 (tub, dia 7 cbore) | null; 37.4 (p) |
| s_j | 3 | 0.25 (base_grip, dia 7 cbore) | **2.35 (strap)** |
| s_k1, s_k2 | 4 | 1.23 (pi_keeper) | 20.1 / 39.29 (tub) |
| s_c1..s_c3 | 7 | 0.50 (lens_collar) | null; 34.7 (p) |
| s_c4 | 8 | 0.75 (lens_collar) | **6.5 (hood)** |

All BLOCKERS numbers are confirmed. Two further faults were found:

- The audit fixes the handle at exactly 40 mm from the head. A real tool with a longer bit puts its handle somewhere
  else, and that position is not audited.
- The BX-12 interim tip ("a >= 50 mm PH1 bit whose turned shank covers at least the first 8 mm") does not match the
  audited envelope, which needs OD <= 6.5 over the full 40 mm. A 1/4 in hex body is 7.3 mm across corners. It is
  outside the envelope wherever it stands less than 40 mm from the head.

The current BOM row D2-77 says only "shank dia <= 6.5 over >= 40 mm, handle dia <= 30". It does not limit the handle
length or the bit protrusion.

### BX-17 hood release (s7 item 9)

| item | value | source |
|---|---|---|
| hole / pin | dia 1.6 / dia 1.5, 0.05 radial | `HOOD_RELEASE` |
| tooth face, ledge face | y -32.10, y -31.70: tooth overlaps the ledge by **0.40** | `RELEASE_ACCESS`, `HOOK` (SL 0.25) |
| right-wall outer face to tooth face | **2.90** | YR -35.0 |
| push 0.55: clearance to ledge | 0.15 | |
| strain at 0.55 | 1.51 % nominal, **2.26 % with Kt 1.5** (limit 2.5 %) | `release_access` |
| push at the strain limit | **0.607** | a_land 9.35 |
| beam force at the push (E 2000 MPa assumed) | about 8.0 N at 0.40, **11.0 N at 0.55** | estimate |
| hood lift force once hk1/hk2 are open | about 37 N: hk3/hk4 cam-out about 15 N each (45 deg, mu 0.3) + pin drag 2 x 11 x 0.3 | estimate, unmeasured |

BX-17 is confirmed and is worse than stated:

- Each deflected tooth pushes its pin back out with about 11 N. A 0.05 mm radial clearance gives no friction against
  that, so "the pins stay in by friction" is false.
- The s7 text "push until it stops" names no stop. Nothing in the layout limits the push. The usable window is
  narrow: from 0.40 + clearance (the tooth clears the ledge) up to 0.607 (the strain limit). A free pin can be pushed
  past 0.607.
- Lifting the hood needs about 37 N, so the body must also be held down. With free pins, one person would need three
  hands.

## 2. Chosen fixes and why

**BX-6: orientation rule plus a lead-in on the hood skin, with the missing insertion and a capture check added.**

1. Step 5 orientation. Hold the body by the grip with the nose up 30-60 deg from setting the plunger until all 4
   hooks click. Gravity then slides the plunger rearward until the nib rests on the Pi button. tan 30 = 0.58 is above
   the assumed friction bound mu 0.5. The plunger weighs about 0.4 g, so it rests on the button with about 3 mN,
   orders of magnitude below any tactile-switch force. The pack is out (power last), so a click does nothing.
   Resting on the button, the flange front face sits 0.25 behind the skin (x -1.55). The tilt also lays the hood's
   front plate on the tub face by its own weight (gravity component along body -X is sin(tilt)): the 0.2 plate gap
   (`HOOD['plate_x']` = XT1 + 0.2) closes, so the skin inner face slides down at x -1.5, still 0.05 in front of the
   resting plunger. Held off the face instead, the skin foot passes in front of the flange and traps it when the
   plate closes. The only jam case is a skin foot landing on the flange top, which item 2 removes.
2. Geometry safety net. Add a **0.8 x 45 deg lead-in chamfer** on the inner bottom edge of the hood plate skin across
   the channel width (y 1.9..16.1). With the existing 0.3 bed chamfer on the plunger front edges, a plunger left up to
   **1.1 mm** forward is cammed home by the descending plate instead of jamming. The cam stops at the rest position
   (x -1.3), so it never presses the button. Review check of the arithmetic: the skin foot's lowest inner point after
   the lead-in is x -1.3 + 0.8 = -0.5; the plunger's chamfered top-front edge starts at x (-1.3 + d) - 0.3; capture
   needs -0.5 >= -1.6 + d, so d <= 1.1. Both 45 deg faces are parallel, so the cam is a face-on-face slide (no edge
   digging) up to d = 1.1. The plunger chamfer exists only if `d2_common.bed_chamfer` succeeds on the plunger's +X face
   (it is the face_down; the flange top edge at y 9 is straight, the 0.8 '|X' fillets are only at the corners). That
   helper returns the solid unchanged on a kernel failure and only appends to `d2_common.NOTES`, so the capture
   check must read the built plunger too (`plunger_chamfer_built`, s4), not just the parameter.

Rejected:

- A light interference rib or detent. It adds drag that the Pi switch spring must beat on every return. That force is
  unknown (G-PLG-1 measures only height and travel). A plunger stuck in holds the power button down, and a long hold
  forces a power-off.
- Captive barbs behind the wall. There is only 0.25 mm to the button face and 0.8 mm to the PCB edge.
- A plunger that rides down with the hood. The stem must pass the wall along X, while the hood moves along Z.

**BX-12: buy to an audited envelope family. No counterbore or strap change.**

The probe shows that a longer bit only helps (table in s3.2). At a 60 mm protrusion, s_j's handle gap is 5.69 and
s_c4's is 26.5. At 80 mm they are 12.86 and 46.5. No screw gets worse, and nothing is hit with a dia 30 x 130 handle,
both at the build steps and with every part fitted (s_c1..s_c3 with the collar off). The review re-ran the probe with
a dia 30 x **250** handle (bit 40 / 58 / 60 / 80): no hit on any screw, same gaps (the nearest solids are all within
the first 130 mm). So the handle length is not a constraint and the audit uses 250 (a 130 mm limit would have made
G-MP-T13 reject a normal-length adjustable torque screwdriver for no geometric reason).

The review also found that the audited `bit_len` is measured from `head_point` (the face the screw head bears on),
while a buyer measures the bit from the holder nose to the tip. The tip sits in the PH1 recess, which is shallower
than the pan head (`PT['head_h']` 2.4), so bl >= the tip-measured protrusion t. s_j's margin is steep near the
nominal: 4.98 at bl 58 (review probe), 5.69 at 60, about 7.8 at 65 (from the dia 40 run: 2.81 + 5.0 radius).

So tool 13 is specified as a PH1 bit standing **65-80 mm** proud of the holder nose (tip-measured), OD <= 6.5 over
that length (the hex inside the holder), with holder nose + handle within dia 30 for 250 mm behind the bit. The audit
checks the family (40 / 60 / 80 mm head-referenced, handle 30 x 250) and requires >= 5.0 mm handle margin at the 60 mm
nominal, which sits 5 mm below the purchase minimum (covers the tip/head offset and the measuring ambiguity of a
quick-release nose). A dia 40 handle was probed too: no hit, but s_j drops to 1.02 / 2.81 / 8.19 at 60 / 65 / 80, so
the handle stays dia <= 30.

The dia 7 counterbores stay as they are. The 0.25 is the margin of the 6.5 envelope, and the real turned-shank OD is
confirmed on receipt. Growing them to dia 8 would thin the base_grip and tub around the PT heads (head dia 6.0) and
gain nothing that the bit specification does not already give. The strap needs no geometry change: at 60 mm or more,
the handle is 5.7 mm or more clear of it.

**BX-17: a printed two-pin release comb (tool 9 becomes the comb + the 2 D2-71 dowels).**

The comb is a stiff bar with two stop pads that bear on the right-wall outer face next to each release hole. Its two
blind pockets fix each dowel's protrusion P, so the push is set by geometry, not by feel. The hk2 pocket is a slot
that floats +-0.8 in X, so the printed 80 mm spacing does not have to match the tub. A palm pad lets one hand push the
comb in and down: this holds both pins and holds the body down through the pins and the stop pads. The other hand
lifts the hood.

**Review correction: the push window is set by a tolerance stack, so the comb is made to measured numbers.**

- What must clear is the tooth face itself (y -32.10, the tooth's outermost face) passing the tub ledge face
  (y -31.70). With the pin tip holding the tooth face, the clearance is c = P - W, where W is the tub's wall + ledge
  (outer face YR to ledge face, nominal 3.30). **c contains no hood term**: hood lateral play cancels. The designer's
  risk row "hood play shifts the window by 0.1" was wrong for the clearance side.
- The beam deflection is (tooth travel) - (hood translation). The pin travel is c + overlap (0.40 nominal = tooth
  0.65 - SL 0.25). Once the panel is off, the hood is free to move inboard (+Y) up to its right-wall locate, so a hood
  sitting outboard translates first. The review credits only h_min = LOCATE 0.15 - print error 0.10 = 0.05 (both
  from `HOOD_TO_TUB_LATERAL` 0.25 = LOCATE + 0.1 print error) and charges 0.10 print error on the tooth:
  deflection_max = c + 0.40 + 0.10 - 0.05 = c + 0.45.
- Unmeasured, the stack does not fit: W (printed tub, +-0.1), the pocket depth (0.2 layer quantisation +-0.1; the
  bridged pocket ceiling sags *shallower*, which means more push) and the dowel length together are about +-0.2,
  against a window of 0.157 (0.45..0.607 push). A comb printed to nominal numbers cannot guarantee the window, with
  any nominal.
- Measured, it does. G-MP-REL (replaces the designer's MP-PIN): W at hk1 and hk2 on the bare tub before step 3 (calipers
  over the wall top, outer face to ledge face), both dowel lengths, then the printed comb with the dowels seated: P
  from each stop pad to its dowel tip. c = P - W is then known to about +-0.03 (RSS of two caliper readings,
  `meas_tol` 0.02 each, the D2-72 class; G-MP-REL records the caliper's stated accuracy).
- Window for the measured c: c >= clear_min 0.05 + 0.03 = **0.08**, and c + 0.45 + 0.03 <= 0.607 (strain limit with
  Kt), so c <= **0.13**. Target c 0.10, so `HOOD_RELEASE['push']` (nominal, = overlap + c) becomes **0.50**: strain
  2.06 % with Kt; worst case deflection 0.13 + 0.45 = 0.58, 2.39 % <= 2.5 %; worst clearance 0.05.
- If the measured c is outside 0.08..0.13, re-print the comb with each pocket depth corrected by the measured error
  (the error is mostly slicer quantisation and ceiling sag, which repeat). The comb is a small print.

This replaces the designer's fixed "push 0.53 +- 0.07" (the 0.07 was not derived from anything).

Rejected:

- A press fit or tighter hole. It cannot hold 11 N axially with a hand-insertable fit, and printed 1.6 holes vary
  +-0.1.
- A self-holding clip or band round the body. Everything that could react it is either on the lifting hood (top,
  front plate) or 70+ mm away. A 12 x 14 mm printed bar cantilevered 110 mm bends about 1.2 mm under 11 N (E 2000 MPa), more than the
  whole push window.
- A strain stop on the hood behind each beam. It is a hood geometry change in a crowded zone. It is kept as a
  fallback if G-SNAP-2 fails (s8).

## 3. Exact implementation

### 3.1 BX-6 plunger

**layout.py `PLUNGER`.** Add these keys:

- `hood_leadin=0.8`: 45 deg lead-in on the inner bottom edge of the hood skin, across `hood_pocket['y']`.
- `edge_chamfer=0.3`: the plunger front-edge chamfer. Today printed_small.py writes this as the literal
  `bed_chamfer(..., 0.3)`; it must read this key instead.
- `drift_tol=1.0`: the forward drift the hood must cam home.
- `mu_max=0.5`: the assumed upper bound of dry ASA-on-ASA friction. Gate G-PLG-2 checks it.

**layout.py `STEPS` step 5.**

- New key `orient=dict(axis='nose_up', tilt_deg=(30.0, 60.0), hold='grip', until='hood_on snaps')`.
- New `action`: "Hold the body by the grip, nose up 30-60 deg (front face tilted up; about 45 is ideal). Set the
  plunger in the front-wall hole, flange outside. It slides back onto the Pi button by itself (it is far too light to
  press it; if your finger clicks the button, that is harmless, the pack is out). Keep the nose up and lower the hood along the body until the 4 hooks click. The front plate traps the
  plunger. Then level the body and push the microSD home through the front slot (both walls) with tweezers, contacts
  up, until it latches."

**layout.py `INSERTIONS`.** Add `dict(id='plunger_in', step=5, moving=['plunger'], path=[(8.0, 0, 0), (0, 0, 0)])`
before `hood_on`. Review correction on the mechanism: `check_sweeps` takes as obstacles `present_at(step)` minus
the parts moved by LATER `INSERTIONS` entries of the same step (list order, not the `adds` order). So `plunger_in` must
sit in the list before both `hood_on` and `sd_in` (today `sd_in` comes after `eyepiece_in`); then hood and microsd
are excluded and `hood_on` still sees the plunger as an obstacle. It must pass: the stem has 0.30
clearance per side, and the nib ends 0.25 from the button.

**printed_hood.py `_plate_cuts(L)`.** Add one cut: a triangular prism along Y over `P['hood_pocket']['y']`
(1.9..16.1). Its XZ section has a 45 deg face from (x pk_x1, z plate_z0 + a) to (x pk_x1 + a, z plate_z0), with
a = `P['hood_leadin']`, pk_x1 = -1.3 and plate_z0 = 0.3. Extend the triangle 0.05 past the skin inner face and the
foot so the boolean is clean. That leaves 0.5 mm of skin at the foot edge across the 14.2 mm channel width only. The
hood prints `+Z` face down, so the foot is the print top and the chamfer faces up: no overhang.

**printed_small.py `build_plunger`.** Use `P['edge_chamfer']` for the bed chamfer. The value is unchanged, so the STL
stays the same.

### 3.2 BX-12 tool 13 and the driver audit

**layout.py `DRIVER`.**

- `bit_len` 40.0 -> **60.0**: the audited nominal protrusion from `head_point` (the face the head bears on) to the
  holder nose. It is 5 mm below the purchase minimum (65, tip-measured), because bl >= tip-measured protrusion.
- New `bit_len_family=(40.0, 60.0, 80.0)`.
- `handle_len` 100.0 -> **250.0**: holder nose + handle (review: probed, no hit; no practical length limit).
- New `handle_margin_min=5.0`.
- New `buy_protrusion=(65.0, 80.0)` (tip-measured, G-MP-T13).
- New `spec`, the single source of the purchase text: "PH1 bit 65-80 mm proud of the holder nose (measured to the
  tip); OD <= 6.5 over the whole protruding length (a 1/4 in hex body must sit inside the holder); holder nose + handle
  within dia 30 for 250 mm behind the bit".
- `bit_d` 6.5, `handle_d` 30, `bit_d_range` and `handle_d_range` are unchanged.
- Family soundness (review): a member between two family members has its bit inside the longer member's bit and its
  handle inside the union of the two neighbours' handles whenever the family step (20) <= `handle_len`. So a hit-free
  family proves the whole continuous range 40..80 hit-free. The check asserts that step rule.

Probe2/3 results for the family (handle dia 30 x 130, build-step present sets; the "all fitted" set gives the same
values except s_k, which is driven with the hood off). The review's 30 x 250 run gave identical values and no hit
(s_j 4.98 at bl 58):

| screw | handle gap at 40 / 60 / 80 | bit gap (all) |
|---|---|---|
| s_j | 2.35 / **5.69** / 12.86 (strap) | 0.25 |
| s_c4 | 6.5 / **26.5** / 46.5 (hood) | 0.75 |
| s_k1 / s_k2 | 18.2 / 20.75 / 20.75 ; 18.2 / 38.2 / 43.06 (probe proxies; checks.json at 40 x 100: 20.1 / 39.29, tub) | 1.23 |
| s_b1 / s_b2 | 12.31 / 24.23 (constant) | 0.25 |
| s_r1, s_r2 | 37.4 / 57.4 / 77.4 | 0.25 |
| s_c1..s_c3 | 34.7 / 54.7 / 74.7 | 0.50 |

No hits in any member.

**checks.py `check_driver`.**

- Loop over `D['bit_len_family']`. Each member builds its bit cylinder (0..-bl) and handle cylinder
  (-bl..-bl-handle_len) and runs the same exact common against the audit set.
- Every member must have no hit.
- At `D['bit_len']` (the nominal), the handle gap must be `>= D['handle_margin_min']`, or no solid may lie within
  15 mm.
- `D['bit_len'] <= D['buy_protrusion'][0]` (the audited nominal is not longer than the shortest bit allowed to be
  bought), `max(family) >= D['buy_protrusion'][1]`, and every family step `<= D['handle_len']` (soundness rule above).
- The row keeps today's top-level fields, computed for the nominal member, and adds
  `family=[dict(bit_len, bit_gap, handle_gap, hits)]`.
- `service_driver` calls the same function, so it inherits the family.

**checks.py `check_collar_gauge`** (line about 2065, uses `D`): run its driver-vs-gauge clearance over the same family.
This is a shared edit with C4-B (s6).

**make_tables.py:482** (screw table). Print the bit as "6.5 x 40-80" from the family and add the handle "30 x 250".

**electronics/gs8-d2-v1/bom.csv row D2-77** (and BOM.md via make_bom.py). The new description is "Adjustable torque
screwdriver 0.1-0.6 N m (readable at 0.15 / 0.2 / 0.35 N m), straight, + PH1 power bit (1/4 in hex E6.3 with a
turned shank, or the driver's own system bit): " followed by `DRIVER['spec']` verbatim, then " (the DRIVER audit
family; check on receipt: MEASURED-PARTS G-MP-T13)". Price stays unpriced. Take the text from `DRIVER['spec']` if make_bom.py can import
the layout; otherwise copy it word for word, and the test in s4 compares the two.

**No change** to any counterbore (`PT['cbore_d']` 7.0) or to the strap geometry.

### 3.3 BX-17 release comb

**layout.py `HOOD_RELEASE`.**

- `push` 0.55 -> **0.50** (= overlap 0.40 + target clearance 0.10). Strain becomes 1.37 % nominal / 2.06 % with Kt;
  the clearance to the ledge is 0.10.
- New `clear_min=0.05`, `c_target=0.10`, `meas_tol=0.02` (caliper class, D2-72; G-MP-REL confirms),
  `tooth_err=0.10` and `h_min=0.05`. The last two are not typed numbers: the check derives them as
  `HOOD_TO_TUB_LATERAL - FDM['LOCATE']` and `FDM['LOCATE'] - tooth_err`; the keys only document them.
- `tool` becomes "hood release comb (printed, stl/tools/release_comb.stl, made to G-MP-REL) + 2 x dia 1.5 x 16 steel
  dowels (D2-71)".
- The overlap is computed, not typed: `ledge face y - tooth_face y` = (Y_RW_IN + ledge) - RELEASE_ACCESS tooth_face y
  = -31.70 - (-32.10) = 0.40. Today's `check_release_access` never compares the push with the overlap at all (it checks
  reach, other-part overlap and strain only), so the clearance row below is a new guard, not an extension.

**layout.py new `RELEASE_COMB`** (after `RELEASE_ACCESS`; z = `HOOD_RELEASE['z']` 87.7, YR -35.0):

| key | value | why |
|---|---|---|
| `bar` | B(-133.0, -37.0, YR - 14.0, YR - 1.0, z - 5.0, z + 5.0) | relieved 1.0 off the wall; ends 2.0 clear of the s_r1 cbore edge (x -35.0) |
| `stop_pads` | B(x - 5, x + 5, YR - 1.0, YR, z - 5.0, z + 5.0) at x -45.0 and x -125.0 | review: local datum at each pin, so wall bow between the stations (printed tub) does not change P; W is measured at the same stations |
| `pad` | B(-97.0, -73.0, YR - 44.0, YR - 14.0, z - 5.0, z + 5.0) | palm pad, 24 x 30, centred between the pins |
| `pin_len` | 16.0 nominal; **replaced per pocket by the G-MP-REL dowel lengths before printing** | |
| `W_nom` | computed: YR -> ledge face = 2.5 + 0.8 = **3.30**; replaced per station by G-MP-REL | |
| `protrusion` | computed: `W + c_target` = 3.30 + 0.10 = **3.40** (= tooth-face distance 2.90 + push 0.50) | |
| `pocket_depth` | `pin_len - protrusion` = **12.60** from the pad face (floor 14.0 - 12.60 = 1.40 >= MIN_WALL 1.2) | the dowel bottoms in it |
| `pocket_hk1` | round dia 1.6 at (x -45.0, z 87.7) | locates |
| `pocket_hk2` | slot 1.6 (Z) x **3.1** (X) at (x -125.0, z 87.7): X float **+-0.8** | absorbs the printed 80 mm spacing error |
| `spacing_tol` | **0.8** (0.5 % of 80 on each of comb and tub, an assumed ASA scale error; G-MP-REL step 3 confirms both dowels enter) | must be <= the float |
| `mouth_chamfer` | 0.5 on both pockets | the comb slides over the dowel ends |
| `edge_chamfer` | 0.5 on the outer edges | |
| `lift_clear` | 3.0 | the pins must be clear of the hood within 3 mm of lift (computed 0 at 2.0) |
| `face_down` | **'-Z'** (review: the 10 mm side of bar + pad on the bed) | the stop pads and the pockets lie in the print plane: no pad overhang, no bridged pocket ceiling (the designer's '+Y' put the pocket floor on a bridge that sags toward more push, and with pads it would float the bar). Pockets print as horizontal dia 1.6 holes (below TEARDROP_ABOVE_D 8) |
| `meas_window` | c = P - W in **0.08..0.13** per station | G-MP-REL acceptance; outside it, re-print with the depth corrected |
| `stl` | 'stl/tools/release_comb.stl', ASA, 100 % infill | |

Probe4 (designer), with the comb as the bar + pad boxes, full face on the wall, pins at protrusion 3.43; the review's
changes (1.0 relief with two pads, protrusion 3.40) only move solids away from the wall or shorten the pins, so the
result carries over; the r7 build recomputes it from the real solid:

- Against the `hood_off` context (tub, base_grip, tripod_nut, run_button, strap, x1203, x1203_kit, pi5, cooler,
  pi_keeper, usb_stick, stick_sleeve, xt30_pair, pack, cap): tub 0.000 mm3 (touch at the stop face only); every other
  part >= 46.8 mm away.
- Hood: comb gap 2.90, at the final pose and at every lift.
- Pins vs hood: 1.66 mm3 total at 0 (the two teeth, by design), 0.96 at +0.5, 0.25 at +1.0, **0 from +2.0**.

**printed_hood.py.** Add the module function `release_comb(L)`. It is not in `PARTS` and follows the pattern of
`printed_collar.centring_gauge`: bar + two stop pads + palm pad, both pockets cut from the stop-pad faces with
per-pocket depths (from `RELEASE_COMB`, i.e. from G-MP-REL when recorded), chamfers. With the load taken at the stop
pads, which sit at the pins, bar bending under the palm (about 0.09 mm at mid-span for 30 N, E 2000 MPa, 10 x 13
section, an estimate) does not change P. Contract rule 4 is kept
(math, cadquery, d2_common only).

**build_d2.py.** Export it through C4-A's `export_tools(prow)` if that has landed; otherwise add
`export_release_comb()`, a copy of `export_gauge`. Either way:

- STL in print pose at `stl/tools/release_comb.stl`;
- `check_print_overhang` and `thin_wall` rows;
- a manifest row (kind 'service tool (not a production part)', `print_after=['G-MP-REL']`);
- the assembly-frame solid passed to `check_release_access`.

**layout.py `REMOVALS` `hood_off`.** The `tool` text comes from `HOOD_RELEASE['tool']`. The `note` becomes the s7
item 9 procedure (s5).

**layout.py new `TOOL_PREREQS = {'release_comb': ('G-MP-REL',)}`** (review correction). Do NOT add the comb to
`PRINT_PREREQS`: build_d2.py (about line 1255) fails the `print_order` 'coverage' row unless `PRINT_PREREQS` and
`PRINT_SEQUENCE` list exactly the `PARTS` keys, and the comb is not a part. build_d2's print-order block gets one more
loop, `('tool', L.TOOL_PREREQS)`, next to `('part', ...)` and `('coupon gate', ...)`, so an unknown gate fails there.
The gate must be named `G-MP-...`: `STATE_GATES` classes only `^G-MP-` (and a few others) as `measured_fit`, and only
measured_fit / coupon gates are "live" print prerequisites. The designer's "MP-PIN" / "MP-T13" would have fallen into
the catch-all `assembly_operation` class and failed as "not live"; they are now G-MP-REL and G-MP-T13, and both are
added as gates in MEASURED-PARTS.md so the gate list that feeds `sitems['measured_fit']` contains them.
G-MP-REL has three parts: (a) W at hk1/hk2 on the bare tub before step 3, (b) both dowel lengths, both before the comb
is printed (the print prerequisite), and (c) P with the dowels seated in the printed comb, before the comb's first use
(a use prerequisite, recorded in the same G-MP-REL record).

**bom.csv D2-71.** The description becomes "2 x dia 1.5 x 16 steel dowels, ISO 8734 class (hood release; seated in
the printed release comb, tool 9, made to MEASURED-PARTS G-MP-REL)". The drill-shank option is dropped, because
its length is not controlled. No new BOM row: the comb is a printed tool (filament only).

## 4. New and extended computed checks

| check (category) | rows | pass criterion |
|---|---|---|
| `plunger_capture` (**new category**, `checks.check_plunger_capture(L, rows)`; build_d2 adds it to the summary; 28 -> 29 categories) | `leadin_built` | Section the built hood at y = `PLUNGER['axis'][0]` (9.0) with `section_lines`. There must be a segment from (-1.3, 0.3 + a) to (-1.3 + a, 0.3), +-0.05, at 45 +- 3 deg. This reads the solid, not the parameter. |
| | `plunger_chamfer_built` (review) | Section the built plunger at y 9.0: a 45 +- 3 deg segment of length 0.3 +- 0.05 (projected) must join the front face x -1.3 and the flange top z 24.4. Reads the solid: catches a silent `bed_chamfer` failure. |
| | `drift_capture` | measured lead-in (from `leadin_built`) + measured plunger chamfer (from `plunger_chamfer_built`) `>= drift_tol` (0.8 + 0.3 = 1.1 >= 1.0). The parameters are reported beside the measured values and must agree within 0.05. |
| | `cam_stops_at_rest` | `hood_pocket.x1 == flange.x1` (+-0.01) and nib gap > 0 (0.25): the cam never presses the button. |
| | `orientation_rule` | step 5 has `orient`; tilt_min >= degrees(atan(mu_max)) + 3 (29.6 <= 30); tilt_max <= 60; `eyepiece` not in `present_at(5)` (BX-13's loose eyepiece arrives at step 6). |
| | `retention_report` (info) | stem engagement 2.30, free cocking 14.6 deg, plunger weight on the button (mN). |
| `sweeps` (extended) | `plunger_in` | Today's sweep rule. 14 -> 15 rows. |
| `driver`, `service_driver` (extended) | each screw | No hit for any member of `bit_len_family` (handle 30 x 250). Nominal handle gap >= `handle_margin_min` (5.0) or nothing within 15 mm. `family` list reported. Plus one `driver` row `family_rules`: `bit_len <= buy_protrusion[0]`, `max(family) >= buy_protrusion[1]`, every family step <= `handle_len`. |
| `release_access` (extended, 2 -> 5 rows) | `pin_hk1`, `pin_hk2` | The pin now runs from the comb pocket floor to `YR + protrusion`, so pin_length = `pin_len`. Today's rules hold (reach, 0 overlap on other parts, Kt strain at `push`), plus: tip consistency `YR + protrusion == tooth_face_y + push` (+-0.01); overlap computed as ledge face - tooth face (0.40); c_nom = push - overlap (0.10); clearance `c_nom - sqrt(2)*meas_tol >= clear_min` (0.072 >= 0.05); deflection `c_max + overlap + tooth_err - h_min` <= push at the strain limit (0.13 + 0.45 = 0.58 <= 0.607, 2.39 %), with `c_max` = `meas_window[1]`, `tooth_err` and `h_min` derived from `HOOD_TO_TUB_LATERAL` and `FDM['LOCATE']`; `meas_window[0] >= clear_min + sqrt(2)*meas_tol`. |
| | `pin_unmeasured` (info) | The same stack with W, pocket depth and dowel length unmeasured (+-0.1 each, LAYER/2 for the pocket): reports that no nominal fits the window (about +-0.2 vs 0.157), which is why the comb is gated on G-MP-REL. Info only. |
| | `comb_envelope` | The comb solid (from `printed_hood.release_comb`) has <= VOL_TOL overlap with every `hood_off` context part. Against the hood it is checked at the final pose and along the `hood_off` path (0..5 mm in 0.5 mm steps, then 5 mm steps to the end). Pins vs hood must be <= VOL_TOL at every lift >= `lift_clear`. |
| | `comb_tolerance` | float (0.8) >= `spacing_tol` (0.8); pocket floor >= `FDM['MIN_WALL']` (1.40); stop pads present at both stations and the bar face relieved (bar y1 <= YR - 0.5); `pin_len` / W per station taken from a G-MP-REL record when one exists (else the nominal, flagged "nominal"); if P is recorded, c = P - W inside `meas_window` per station, else 'pending G-MP-REL (c)' (info, not fail). |
| `print_order` (extended) | `tool release_comb` | every gate in `TOOL_PREREQS['release_comb']` is a live measured_fit / coupon gate (G-MP-REL). The 'coverage' row stays PARTS-only. |
| `print_overhang`, `thin_wall` (tools rows) | `release_comb` | as for `collar_gauge` |
| `layout_self_check` (new rows) | `driver spec text` | `DRIVER['spec']` appears verbatim in bom.csv D2-77 and in the ASSEMBLY tool 13 row (make_tables output). |
| | `release tool text` | `HOOD_RELEASE['tool']` appears in REMOVALS `hood_off` and in ASSEMBLY s7 item 9. |

**Planted-fault regressions:** new file `test_r7_c6.py`, written like test_r3_regressions.py. Each case monkeypatches
a copy of the layout and calls the check function. The geometry cases use small cadquery boxes or the out/step parts,
so the test needs no full build.

| test | planted fault | expected |
|---|---|---|
| `test_plunger_leadin_zero` | `PLUNGER['hood_leadin']=0` (and a hood section without the 45 deg segment) | `plunger_capture` `drift_capture` and `leadin_built` FAIL |
| `test_plunger_orient_missing` | step 5 `orient` removed | `orientation_rule` FAIL |
| `test_plunger_orient_too_flat` | `tilt_deg=(15, 60)` | FAIL (15 < 29.6) |
| `test_plunger_insertion_missing` | `plunger_in` removed from INSERTIONS | FAIL on a new `sweeps` coverage row. The rule: every non-screw id in `STEPS` `adds` has an INSERTIONS entry or a reason in a new `layout.INSERTION_EXEMPT`. Today the ids without one are tub (step 3, the datum), plunger, foam_pad, knob_exp, knob_fps and eyecup. [Plan edit P6-3: the exempt list is {tub, eyecup}; foam_pad (C1) and the knobs (C5) have INSERTIONS entries; a stale exemption fails.] |
| `test_driver_long_bit_hit` | obstacle box planted on the s_c4 axis 315-325 mm above the head (only the 80 mm member's handle, 80..330, reaches it; the 60 mm member ends at 310) | `driver` s_c4 FAIL although the 40 and 60 mm members pass |
| `test_driver_margin` | strap proxy moved 3 mm toward s_j | s_j FAIL on `handle_margin_min` at the 60 mm nominal (5.69 - 3 = 2.69) |
| `test_driver_family_gap` (review) | `bit_len_family=(40.0, 300.0)` | `family_rules` FAIL (step 260 > handle_len 250) |
| `test_driver_buy_mismatch` (review) | `bit_len=70.0` with `buy_protrusion=(65, 80)` | `family_rules` FAIL (nominal longer than the shortest bit allowed) |
| `test_driver_spec_text_drift` | bom.csv D2-77 text edited to "handle dia <= 30" only | `layout_self_check` FAIL |
| `test_plunger_chamfer_missing` (review) | plunger solid built with the bed chamfer skipped (as on a silent `bed_chamfer` failure) | `plunger_chamfer_built` and `drift_capture` FAIL while `leadin_built` passes |
| `test_comb_overpush` | `HOOD_RELEASE['push']=0.58` (comb protrusion changed to match) | `release_access` FAIL (c_nom 0.18 outside the window; deflection 0.18 + 0.45 = 0.63 > 0.607) |
| `test_comb_underpush` | `push=0.47` (comb matched) | FAIL (c_nom 0.07 - 0.028 = 0.042 < 0.05) |
| `test_comb_tip_mismatch` (review) | `RELEASE_COMB['c_target']=0.15` with push left at 0.50 | FAIL on tip consistency (comb tip 0.05 deeper than the audited push) |
| `test_comb_wide_window` (review) | `meas_window=(0.08, 0.20)` | FAIL (0.20 + 0.45 = 0.65 > 0.607) |
| `test_comb_prereq_unknown` (review) | `TOOL_PREREQS['release_comb']=('MP-REL',)` (no `G-` prefix) | `print_order` 'tool release_comb' FAIL (not a live gate) |
| `test_comb_no_float` | hk2 pocket made round | `comb_tolerance` FAIL |
| `test_comb_hits_wall` | `RELEASE_COMB['stop_pads']` y1 = YR + 0.5 | `comb_envelope` FAIL (tub overlap) |
| `test_comb_no_relief` (review) | bar y1 = YR (full face on the wall, no pads) | `comb_tolerance` FAIL (relief missing) |
| `test_comb_hits_hood` | a lip added to the comb, B(-100, -70, YR, -30.0, ZT1 + 0.5, ZT1 + 4.0), reaching over the hood band edge | `comb_envelope` FAIL (hood at the final pose and along the lift; no tub overlap) |

## 5. Document changes

**ASSEMBLY.md**

- Step 5 text: the new `STEPS` action (s3.1), generated by make_tables.
- Step 5 s3 check: "Plunger trapped: from the front it moves 0.6 and springs back (Pi button), and it does not come
  out with the hood on".
- s1.1 tool 9: "Hood release comb, printed (`stl/tools/release_comb.stl`), + 2 x dia 1.5 x 16 steel dowels (D2-71):
  sets each tooth 0.08-0.13 mm past its ledge (push about 0.50 mm); made to G-MP-REL (measure the tub and the dowels
  first, then check the printed comb)".
- s1.1 tool 13: the `DRIVER['spec']` text (s3.2).
- PT-torque table cell: "tool 13 (BOM D2-77, bit 65-80 mm proud)".
- s7 item 9: replace "push one release pin ... The pins stay in by friction, so the 2 releases are made one at a time
  and stay made." with:

  > Stand the body on a non-slip mat with its open left side against a book. Push one dowel into each right-wall
  > release hole (hk1 x -45, hk2 x -125, z 87.7) with a light fingertip push until it meets the tooth; do not press
  > on. Slide the comb over both dowel ends (round pocket on hk1) and push it until both stop pads sit on the wall:
  > the comb, not your thumb, sets how far each tooth goes (0.08-0.13 past its ledge, as measured at G-MP-REL).
  > Each tooth pushes back with about 10 N. Left hand: palm on the comb pad, pushing in and down; this holds both
  > pins and the body. Right hand: lift the hood straight up 60 by its band. The teeth leave the pins within 2 mm.
  > If the hood catches, stop and lower it: do not pull harder and do not push a dowel by hand "until it stops".
  > Nothing stops a free dowel, and past 0.6 mm the hook is over its strain limit.

  Computed: push 0.50 nominal (c 0.10 past the ledge; measured window c 0.08..0.13), strain 2.06 % with Kt (worst
  case 2.39 % with the hood tooth print error), comb 0 mm3 on every other part.

**electronics/gs8-d2-v1/BOM.md / bom.csv**: rows D2-71 and D2-77 as in s3 (regenerate BOM.md with make_bom.py).
WIRING.md: no change.

**MEASURED-PARTS.md**: two new entries.

- **G-MP-REL** (replaces the designer's MP-PIN): (a) on the bare printed tub, before step 3: W at hk1 (x -45) and
  hk2 (x -125), calipers D2-72 over the wall top, outer face to the ledge face (nominal 3.30); (b) both D2-71 dowel
  lengths, each assigned to its pocket; record the caliper's stated accuracy (the CAD assumes `meas_tol` 0.02).
  Pocket depth_i = L_i - (W_i + 0.10); print the comb only after (a) and (b). (c) Before the comb's first use: seat
  both dowels in the comb and measure P_i, pad face to dowel tip; c_i = P_i - W_i must be 0.08..0.13. Outside that,
  re-print with depth_i corrected by (c_i - 0.10). Also confirm both dowels enter the tub holes with the comb on
  (spacing float).
- **G-MP-T13**: tool 13 on receipt. Measure the bit OD over its protruding length (<= 6.5), the protrusion from the
  holder nose to the tip (65-80), the largest holder/handle dia (<= 30) and the length behind the bit (<= 250). On a
  fail, change the bit or extension, not the CAD.

**SPEC.md**

- J10 row: add "hood skin foot lead-in 0.8 x 45 deg over the channel".
- G-PLG-1 text gets a new **G-PLG-2**: with the pack out, set the plunger at 45 deg nose-up, lower the hood 5 times,
  and record that the plunger is captured every time. Also record a deliberate 1.0 mm forward drift: is it cammed
  home or does it jam? And the plunger-on-ASA slide angle (confirms mu_max <= 0.5).
- G-SNAP-2/whole: "the release is made with the comb; record whether both teeth clear (the hood lifts with no
  catch) and whether any beam root whitens after 5 cycles".

**guide/guide_steps.py**

- Tools line 21: "(9, 'Hood release comb (printed) + 2 dowels dia 1.5 x 16 (service only)', 'D2-71')".
- Tool 13 line: the `DRIVER['spec']` short form "bit 65-80 mm proud, dia 6.5 max; handle dia 30 max".
- `TIPS['5a']` -> "Hold the body by the grip, nose up 30-60 deg, from the plunger until the hood clicks: the plunger
  rests on the Pi button by gravity. Level it again for the microSD." (BX-6 resolved by the r7 orientation rule and
  the hood lead-in.)
- `TIPS['3b']`: drop the BX-12 strap line (handle gap now about 7.8-12.9 mm with a 65-80 mm bit).
- `TIPS['B0']` -> "Tool 13: PH1 bit 65-80 mm proud of the holder, 6.5 mm max over that length, handle dia 30 max
  (measure on receipt, G-MP-T13)."
- The service page (caution list) adds the comb wording from s7 item 9.
- BLOCKERS-2026-10-08.md: append a closure line for BX-6, BX-12 and BX-17 pointing to this spec once the r7 build
  passes. Leave the table text itself alone.

**HANDOFF.md**: r7 entry with the new check category and numbers (s7).

## 6. Interactions and risks

| area | effect |
|---|---|
| `hood_on` sweep | The lead-in only removes hood material: still 0 hits. The plunger stays an obstacle. |
| `interference`, `mate_overlap` | The hood/plunger slide mate is unchanged (skin inner face x -1.3). The chamfer is below the plunger (z 0.3..1.1 vs plunger z >= 16.6), so no new contact. |
| `critical_features`, `thin_wall` | The lead-in leaves a 0.5 mm foot edge over 14.2 mm of the skin. No critical feature sits there (hood features: hooks, band, groove lip, foot holes at the collar feet, roll fin). Expect no change to the share-based thin_wall screen. If `unclassified_thin_spots` lists the edge, classify it in `THIN_OK` as a lead-in edge (non-structural). |
| `print_overhang` | Hood: the chamfer faces up in the `+Z` pose. Comb (review): `-Z` face down; bar, stop pads and palm pad share the z - 5 face, the pockets are horizontal dia 1.6 holes and the hk2 slot top is a 3.1 bridge (MAX_BRIDGE 30). |
| `print_order` | The comb goes in the new `TOOL_PREREQS`, not `PRINT_PREREQS` (that table must equal PARTS). New gate ids G-MP-REL, G-MP-T13 and G-PLG-2 appear in MEASURED-PARTS.md / SPEC.md, so `hardware_gates` lists three more open items (measured_fit class); receipt open-gate counts change, no fail. |
| `keepouts` | Hood change is at the foot, away from every KEEPOUTS box (ko_* all sit inside the tub). The comb is outside the body. |
| `evf_restraint`, `j7_float`, `lens_support`, `cable_routes`, `stack_retention` | No geometry they read changes. |
| `driver` / `service_driver` | Three members per screw, about 3x the OCP booleans for that check; the 250 mm handle makes the cylinders longer, not more numerous (the bounding-box prefilter rejects most parts). Probe2 ran 55 member-screw cases, STEP loading included, inside its 10 min limit; the review's 44-case 30 x 250 run took about 2 min. Measure the build-time increase in the r7 build. All members pass today. |
| `mass_com` | The comb and dowels are service tools, not in the mass. The hood loses about 0.005 g. |
| BX-13 (eyepiece loose rearward, steps 6-8) | The nose-up rule is limited to step 5, before the eyepiece exists. `orientation_rule` asserts this. |
| C4-A (camera key, `export_tools`) | Use the same `export_tools` for the comb. The comb takes tool number 9 (it replaces the pins as the tool), so there is no clash with C4-A tools 15 and 16. |
| C4-B (gauge thumb in `check_driver`) | C4-B quotes the old envelope "handle 30 x 100 from x 43.3". After this change the handle starts at x 43.3 / 63.3 / 83.3 (the family) and is 250 long. C4-B's thumb and gauge obstacles must be checked against every member. Whoever lands second rebases onto the family loop. |
| C1 (BX-1 tub rail), C2/C3 (leads) | No shared geometry. [Plan edit P6-4: C1 changes no printed part; C3 changes the tub via FLOOR_HOLES.] This spec does not touch the tub. |
| `release_access` numbers | push 0.55 -> 0.50 changes the reported strain (2.26 -> 2.06 %) and the tooth overlap volume (0.865 mm3 per pin at 0.55; smaller at 0.50, recomputed by the build). ASSEMBLY s7 text and make_tables must quote the new values. |
| Risk: hood lateral play (corrected by the review) | The clearance c = P - W has no hood term, so hood play cannot make the tooth fail to clear. It only changes the deflection; the check charges 0.10 tooth print error and credits only 0.05 of the hood's inboard translation (LOCATE 0.15 minus the 0.10 print error in `HOOD_TO_TUB_LATERAL`). That translation credit is an assumption (the hood is free in +Y once the panel is off; nothing modelled stops it); G-SNAP-2/whole (whitening after 5 cycles) confirms it. Without the credit the worst case is 0.13 + 0.50 = 0.63 (2.59 %). Fallback (user decision): a hood strain stop behind hk1/hk2. |
| Risk: unmeasured forces | Hook push-back about 10 N at 0.50 and lift 37 N are estimates (E 2000 MPa, mu 0.3). If the lift is much higher, one hand on the comb may not hold the body down. Then two people do it: one holds the comb, one lifts the hood. The comb still sets the push. |
| Risk: measuring W | W is read with caliper jaws reaching about 7-9 mm below the wall top (ledge z 88.55..90.25, wall top 97.3) on the bare tub. If the jaws cannot seat on the ledge face, the fallback is to measure the wall thickness at the station (outer to inner face, 2.5 nominal) and the ledge projection (0.8 nominal, depth rod from the inner face) separately; three caliper readings then enter c, and the measured window narrows to about 0.09..0.12 (sqrt(3) x 0.02 = 0.035 on each side). |
| Risk: friction bound | mu_max 0.5 is assumed. If G-PLG-2 shows the plunger does not slide at 30 deg, the tilt range moves to 45-60 deg (a parameter change, no geometry). |

## 7. Acceptance criteria

Computed (r7 build, `out/checks.json`):

- `plunger_capture`: 5 pass rows + 1 info. `leadin_built` finds the 45 deg segment (0.8 +- 0.05);
  `plunger_chamfer_built` finds the 0.3 segment on the built plunger; `drift_capture` 1.1 >= 1.0 from the measured
  segments. `orientation_rule` tilt 30-60 >= 29.6.
- `sweeps`: 15/15 pass, including `plunger_in` and `hood_on` with the lead-in, plus the coverage row.
- `driver` 11/11 (+ `family_rules`) and `service_driver` pass for all of `bit_len_family` (40/60/80, handle
  30 x 250). Nominal handle gaps: s_j >= 5.0 (expected 5.69, strap), s_c4 >= 5.0 (expected 26.5, hood). Bit gaps
  unchanged (0.25 at the dia 7 counterbores, 0.75 s_c4, 1.23 s_k).
- `release_access` 4 pass + 1 info: push 0.50 (c 0.10), tip consistency 0.00, clearance 0.072 >= 0.05, worst
  deflection 0.58 <= 0.607 (2.39 %), nominal strain 2.06 %; pin length 16.0; comb 0 mm3 on every context part and the
  lifting hood; pins clear of the hood at lift >= 2.0 (limit 3.0); `comb_tolerance` 'nominal' + 'pending G-MP-REL (c)'.
- `print_order`: 'tool release_comb' pass; 'coverage' unchanged (PARTS only).
- Tools manifest: `release_comb` row with print_overhang pass. thin_wall and critical_features: 0 fail.
- Every other category: same pass counts as r6, plus the added rows (29 categories, 0 fail).
- `test_r7_c6.py`: 19/19. Existing tests: all pass.

Physical gates (later):

- **G-PLG-1 + G-PLG-2**: plunger capture at 45 deg x 5, drift 1.0 cammed home, slide angle <= 30 deg, button
  travel/press.
- **G-MP-REL**: (a) W at hk1/hk2 on the bare tub and (b) dowel lengths before the comb is printed; (c) P on the
  printed comb, c = P - W in 0.08..0.13, before first use.
- **G-MP-T13**: tool 13 inside the purchase envelope (bit 65-80 proud, OD <= 6.5, handle dia <= 30 for 250).
- **G-SNAP-2/whole**: comb release lifts the hood 5 times with no catch and no whitening (also confirms the hood
  translation credit, s6).

## 8. User decisions

None required. Everything above is decided within the rules: the comb uses dowels already in the BOM (D2-71), and
tool 13 was already in the BOM (D2-77, unpriced). The longer PH1 power bit (65-80 mm proud) is part of tool 13.

Optional, only if G-SNAP-2/whole fails: approve a hood geometry change (a strain stop behind hk1/hk2) instead of
re-printing the comb.

## 9. Effort and receipt impact

| work | h |
|---|---|
| BX-6: layout keys and step text, `plunger_in`, hood lead-in cut, `check_plunger_capture` (incl. `plunger_chamfer_built`) + build_d2 summary | 1.75 |
| BX-12: `DRIVER` family (250 handle, `buy_protrusion`, `family_rules`), `check_driver` loop, `check_collar_gauge` family, make_tables, bom.csv/make_bom, MEASURED-PARTS G-MP-T13 | 1.5 |
| BX-17: `RELEASE_COMB` (pads, relief, -Z pose), `printed_hood.release_comb`, export + manifest, `TOOL_PREREQS` + print_order loop, `check_release_access` stack rows, REMOVALS text, G-MP-REL | 3.0 |
| `test_r7_c6.py` (19 cases) | 1.25 |
| Documents (ASSEMBLY via make_tables, SPEC, MEASURED-PARTS, BOM, guide_steps, HANDOFF) | 1.0 |
| Full rebuild through run_locked.py + check review | 1.0 (build time) |
| **Total** | **about 9.5 h** (BX-12 alone about 2 h; it can land first) |

Receipt sources touched:

- layout.py, printed_hood.py, printed_small.py (text only, same solid), checks.py, build_d2.py (export + print_order tool loop), make_tables.py.
- layout.py and checks.py force a full release rebuild (`build_d2.py` through `run_locked.py`; one CAD job at a
  time).
- Production STLs that change: **hood.stl only** (lead-in). plunger.stl should stay byte-identical (same chamfer value; confirm with the receipt hash, since the bed_chamfer call now reads a key).
- New tool STL: `stl/tools/release_comb.stl`.
- Outside the CAD receipt: electronics/gs8-d2-v1/bom.csv, BOM.md (make_bom.py), MEASURED-PARTS.md, SPEC.md,
  ASSEMBLY.md (generated tables), guide/guide_steps.py (the guide rebuild follows the CAD rebuild).

## Review notes (adversarial review, 2026-10-08 23:15-00:35 MPST)

Verified with my own probes (scratchpad `r7/C6-review/`), against the r6 code:

- BX-6: PLUNGER geometry (stem x -5.0..-1.3 in the hole to XT1 -2.7: 2.30 engaged; flange rear face x -2.5, 0.20 proud
  of the tub face; nib 0.25 from the button at x -5.55); the capture arithmetic d <= 0.8 + 0.3 = 1.1; hood plate gap
  0.2 (`HOOD['plate_x']`); the insertion coverage gap (exactly tub, plunger, foam_pad, knob_exp, knob_fps, eyecup lack
  an INSERTIONS entry); `eyepiece` first present at step 6; the plunger is printed `+X` face down, so the 0.3 bed
  chamfer is on the front-face perimeter, including the flange top edge.
- BX-12: re-ran the designer's driver probe with handle 30 x 250 (bit 40 / 58 / 60 / 80): 44 cases, no hit, gaps equal
  to the 130 run (s_j 2.35 / 4.98 / 5.69 / 12.86; s_c4 6.5 / 24.5 / 26.5 / 46.5). With handle 40 x 250 (bit 60 / 65 /
  80): no hit, s_j 1.02 / 2.81 / 8.19.
- BX-17: strain law from `check_release_access` (a_land 9.35, Kt 1.5): 2.06 % at 0.50, 2.26 % at 0.55, limit push
  0.607. Tooth face -32.10 and ledge face -31.70 from `Y_RW_IN` -32.5 + ledge 0.8 + SL 0.25 - tooth 0.65.
  `HOOD_TO_TUB_LATERAL` 0.25 = LOCATE 0.15 + 0.1 print error. Today's check has no push-vs-overlap row.
- Build plumbing: `build_d2` print_order 'coverage' requires PRINT_PREREQS keys == PARTS; `STATE_GATES` classes only
  `^G-MP-` (and G-PLG-, G-CAM-1, ...) as measured_fit; `hardware_gates` reads gate ids from MEASURED-PARTS.md,
  SPEC.md and WIRING.md; `check_sweeps` excludes parts moved by later same-step INSERTIONS (list order).

Changed:

1. BX-17 push window: the designer's push 0.53 +- 0.07 was not derived, and the risk row about hood play was wrong.
   The clearance is c = P - W (tub-referenced; hood play cancels). Unmeasured, the stack is about +-0.2 against a
   0.157 window, so no fixed comb works. The comb is now made to measurements (G-MP-REL: W and dowel lengths before
   printing, P on the printed comb before use, accept c 0.08..0.13). Push nominal 0.50, worst deflection 0.58
   (2.39 %), with only 0.05 hood-translation credit; that assumption and the no-credit worst case (2.59 %) are stated,
   with G-SNAP-2/whole as the gate and the hood strain stop as the user-decision fallback.
2. Comb geometry: two stop pads at the pins with the bar relieved 1.0 (local datum); hk2 float +-0.5 -> +-0.8
   (0.5 % scale error on each part, an assumption confirmed at G-MP-REL); print pose `+Y` -> `-Z` (the `+Y` pose put
   the pocket floor on a bridge that sags toward MORE push, and with pads would float the bar).
3. Gate naming and print order: MP-PIN / MP-T13 -> G-MP-REL / G-MP-T13 (non-`G-MP-` ids are not live print
   prerequisites); the comb goes in a new `TOOL_PREREQS`, not `PRINT_PREREQS` (that would fail print_order
   'coverage'); build_d2's print-order block gets a 'tool' loop.
4. BX-12: the purchase range 60-80 -> 65-80 mm tip-measured, because the audit's `bit_len` is head-referenced
   (bl >= tip protrusion) and s_j's margin falls below 5.0 just under 60 (4.98 at 58). Handle length 130 -> 250
   (probed hit-free, so MP-T13 no longer rejects normal-length torque screwdrivers). New `buy_protrusion` and a
   `family_rules` row (nominal <= purchase minimum, family max >= purchase maximum, family step <= handle_len: this
   step rule is what makes the discrete 40/60/80 family cover the continuous range).
5. BX-6: added `plunger_chamfer_built` (`bed_chamfer` fails silently, so the parameter-only `drift_capture` could
   pass with no plunger chamfer); `drift_capture` now uses the measured segments. Added the gravity effect on the
   hood plate during the nose-up descent (skin at x -1.5, 0.05 in front of the resting plunger). Corrected the sweep
   obstacle mechanism (INSERTIONS list order).
6. Tests 12 -> 19 (driver family gap, buy mismatch, plunger chamfer missing, comb tip mismatch, wide window, prereq
   without `G-`, comb without relief); the long-bit obstacle moved to 315-325 mm for the 250 handle. Over/under-push
   expectations recomputed. Effort 8.5 -> 9.5 h.
7. Removed unsupported claims: the comb "30 min print" and the bit price; the status time stamp.

Not changed, checked and kept: the orientation rule and its 30-60 deg range; the 0.8 lead-in; rejecting a friction
rib (Pi switch force unknown); no counterbore or strap change; the comb envelope result (the review's changes only
move solids away from the wall or shorten the pins; the r7 build recomputes it from the real solid).

Open: the hook push-back and lift forces are estimates; the hood's lateral freedom in +Y with the panel off is
assumed, not modelled; the caliper accuracy is assumed 0.02 until G-MP-REL records it.

## Plan edits (integration, 2026-10-09 00:00-01:00 MPST; PLAN.md wins where it and this spec differ)

Plan edits: P6-1 C6 is the last cluster in PLAN.md and is on the drop list (all three items are MINOR). Inside the
cluster the order is BX-6 (6a), BX-12 (6b), BX-17 (6c); drop from the end.
Plan edits: P6-2 `release_comb(L)` lives in SPEC-C4's new `printed_tools.py` (not printed_hood.py); one
`export_tools()` in build_d2 exports it next to `fpc_fold_card`; `TOOL_PREREQS = {'fpc_fold_card': (),
'release_comb': ('G-MP-REL',)}`. If C4-BX-8 has not landed, create printed_tools.py and export_tools() here.
Plan edits: P6-3 `INSERTION_EXEMPT` = {tub (datum), eyecup (pushed over the barrel)} only: SPEC-C1 puts foam_pad in
`evf_pair_in` and SPEC-C5 puts both knobs in `panel_on`. Add a rule: an exempt id that also has an INSERTIONS entry
fails ("stale exemption"). If C1 or C5 did not land, keep their ids exempt with the r6 reason.
Plan edits: P6-4 Stale cross-references: "C1 edits printed_tub.py" (section 6) is void (C1 changes no printed part;
C3 changes the tub through FLOOR_HOLES). "C4-A tools 15 and 16" is void: C4's final spec adds tool 15 only (fold
card, renumbered 18); 15-17 are C1 pliers, C5 paper, C1 mirror (PLAN.md X-9). The hood "roll fin" in the hood-feature list is deleted by SPEC-C4
(tab catch instead).
Plan edits: P6-4b check_driver: the family loop is the outer loop; SPEC-C4's `held` envelopes are added to the audit
set inside it. check_collar_gauge family edit is C6's; C4 does not touch it.
Plan edits: P6-5 Guide TIPS['3b'] is shared with SPEC-C3 (BX-16 text): one merged tip. D2-71 and D2-77 text edits go
into make_bom.py `LINES` (bom.csv / BOM.md are generated; make_bom imports layout, so D2-77 reads DRIVER['spec']).
Plan edits: P6-6 Build time: the 3-member family roughly triples driver/service_driver booleans; measure it in the
release build. `plunger_capture` registers with `info_neutral=True` (retention_report info row).
