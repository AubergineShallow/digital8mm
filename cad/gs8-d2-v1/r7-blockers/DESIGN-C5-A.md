# DESIGN-C5-A: exposure knob press, panel shafts, shaft cut (BX-5, BX-13, BX-14), angle A (sequence)

Status: design only, 2026-10-08 22:45-23:55 MPST. One of two independent designs for cluster C5. No repo file was
changed except this one. Probes: session scratchpad `r7/C5-A/p1.py` (sweeps, driver gaps, panel backing), `p2.py`
(thumb access, switch stack), `p3.py` (rest-pose bearing) and `p4.py` (prototype of the computed retention test), run against `layout.py` and the r6 per-part STEP files in `out/step/parts/` (16:05 build).
Everything is computed from CAD proxies. Nothing was printed, bought or measured.

## 1. Problem, re-checked against the current code

| Item | Value in the code / probe | BLOCKERS figure | Verdict |
|---|---|---|---|
| What holds the encoder against a -Y push (knob press, inward) | Only the 3 cradle hook teeth (`printed_panel._cradle`, `CRADLE` t 1.6, top w 8, sides w 5). In `panel.step`, inside the encoder footprint +-20 mm and behind the PCB back face (y < 24.1), the panel has only 3 solids: the teeth (29.3 + 18.3 + 18.3 mm3, y 22.35..24.1). Nothing else backs the board. | "only the 3 cradle hook teeth" | correct |
| Tooth reach over the PCB | `ENCODER['cradle_hooks']['tooth']` 0.40; printed tooth 0.65 = 0.40 + SLIDE 0.25. STEP: top tooth reaches z 69.4 against the PCB top edge z 69.8; side teeth reach x -75.25 / -50.75 against the PCB edges -75.65 / -50.35. Total tooth bearing area: (8 + 5 + 5) x 0.4 = 7.2 mm2 (p4: a 0.3 mm push, less the 0.1 play, overlaps 1.44 mm3 = 7.2 x 0.2). | 0.4 mm | correct |
| What holds the encoder against a +Y pull (knob pulled off) | The encoder body front face (12.5 x 13.5) bears on the panel inner face (y 32.2). The panel is fully solid over that footprint, less the dia 7.5 hole (74.7 mm2 in a 0.6 mm slab, p1). | not stated | **new: a pull is safe in the closed body; only a push is unsafe** |
| Knob fit | `knob_exp` bore D 6.0/4.5 + `FDM['KNOB_BORE_OFFSET']` 0.10 radial: nominally 0.1 clearance. The D-bore ladder coupon (G-KNOB-1) sets the real value; the print note says "Press onto the D shaft" and G-MP-ENC asks for no play beyond 0.1. So the fit is meant to be snug. Press force: unknown. | as stated | correct |
| Hook release force (my estimate, not in the repo) | Eccentric pull on a hook: tip deflection = F e L^2 / (2 E I). E 1.8 GPa, L 9.85 (`snap_strains` Lc), e about 1.0 mm, release at 0.40 mm: top hook about 40 N, each side hook about 25 N, about 90 N together. About 45 N if only 0.2 mm of tooth engages after printing. Order of magnitude only; ignores friction and tooth-face rotation. | not stated | an FDM press fit can exceed this: BX-5 stays MAJOR |
| In-use loads on the same path | Encoder push < 5 N (`PART_RATIONALE['knob_exp']`); a finger pushing while turning; the camera set down on its left side (895.3 g with the Kowa lens, `mass_com`; `knob_exp` is the most proud point of the left side). | not stated | about 1/10 to 1/20 of the estimate; angle A does not change them (s6) |
| Proud shafts (BX-13) | Encoder shaft end y 44.0 = 9.0 above the panel face (y 35.0); cut switch shaft y 42.0 = 7.0. With the knobs on: `knob_exp` top y 44.2 (9.2 proud), `knob_fps` y 42.2 (7.2). The +Y extreme at steps 8, 9 and 10 is `knob_exp` (44.2); next `encoder` 44.0, `knob_fps` 42.2, eyecup 38.76 (steps 9+), eyepiece 35.25, base_grip 35.2. | 7-9 mm | correct |
| BX-13 under angle A | With the knobs fitted at step 2, resting the body on its left side puts body weight and screw thrust on `knob_exp`, then the shaft, the encoder and the 0.4 teeth. That is the BX-5 load path again. | n/a | **angle A must ban the left-side rest pose** (s2 A2) |
| Switch stack (BX-14) | `SWITCH_1824`: body front face y 32.2 (= SPLIT), bushing 32.2..38.2, shaft to y 42.0 (9.8 above the body face), nut y 35.0..37.4 on the outer face. BOM D2-11 says "nut + washer"; MP-SW says "the stop washer set for 2 positions". The washer is not modelled, and where it sits (body side or nut side) is not known. | "7.0 above the panel face; measure the nut/washer stack" | 7.0 is right for the fitted shaft. A cut length measured on the loose switch depends on the unknown washer, so measure in place and cut off the panel (s2 A3) |

## 2. Chosen fix and why

**A1. Both knobs go on at bench step 2, with the panel off.** Snap the encoder in by pushing on the back of its
board. Keep that thumb flat on the board back. Press `knob_exp` onto its D shaft with the other palm until it stops
on a 0.2 mm paper shim on the panel face. The thumb takes the press, not the hooks. `knob_fps` goes on the same way;
its switch nut takes the push. The knobs then stay on and ride with the panel (`panel_on`, `panel_off`). No knob is
ever pressed while the panel is on the body. A knob may be pulled off with the panel on, because the panel backs
the encoder for a pull. A new knob is pressed on only at the bench, panel off.

Probe facts behind A1:
- A dia 20 thumb column on the encoder axis, from y -31 up to the PCB back face (y 24.1), meets 0.0 mm3 of panel
  (p2). The 3 teeth sit at the PCB edges, outside radius 10.
- With the knobs in the `panel_on` moving set, the knob sweep (+70 Y to home) meets 0.0 mm3 of every static part
  present at step 8: tub, hood, base_grip, pi_keeper, plunger, lens_collar (STEP), and every COTS box including
  lens, strap, eyepiece and gs_camera (p1). The only overlaps are with the encoder and switch boxes, which move with
  the knobs.
- The step-8 driver envelopes (bit dia 6.5 x 40 + handle dia 30 x 100) clear both knobs by a wide margin: bit gaps
  >= 50.61 mm, handle gaps >= 86.04 mm (s_b1, s_b2, s_r1, s_r2).

**A2. The left side is never a rest face once the knobs are on (BX-13).** All 4 panel screws are driven in one pose:
the camera upside down on its hood roof on a folded cloth, grip up. At step 8 the only +Z extreme is the hood
(z 100.0); the next part is the tub at 97.3, so the hood roof alone carries the camera. Drive s_b1 and s_b2 down.
For s_r1 and s_r2, put a flat block no taller than 25 mm (a closed paperback is fine) against the left side, along
the cloth, between x -145 and -5. It bears on the hood band and the top strip of the panel face. In this pose the
knobs start 29 mm above the bench (`knob_exp` z 71 body), so a 25 mm block leaves 4 mm. The eyepiece (x <= -149.5)
is outside the block. The block takes the screw thrust straight into the bench, not into the knobs or the base
joint. The panel's EVF cap already clamps the eyepiece when this pose is used (panel pushed on first).

**A3. The switch shaft is cut off the panel (BX-14).** Dry-fit the switch on the panel with its washer as supplied
and the nut finger-tight. Measure the shaft protrusion P above the panel face (caliper depth rod). Take the switch
off. Cut P - 7.0 mm off the shaft end, with the shaft held in soft vise jaws next to the cut, the switch hanging
free. Never clamp the bushing thread; never saw on the panel. Deburr, refit, nut finger-tight + 1/8 turn. This
gives 7.0 above the panel face whatever the washer stack is. The same rule covers the encoder shaft: if MP-ENC shows
it standing more than 9.0 above the panel face, cut it with the encoder out of the cradle.

Alternatives considered:
- Keep the knob at step 9 and "twist it on lightly": wording only; the load path through the teeth stays. Rejected.
- A backstop rib or hook under the encoder PCB: ko_hdmi_run lies there. This is a geometry change (the angle-B
  route). It can be combined with A1; it is not needed for assembly once A1 holds.
- Grub-screw knob: adds a fastener and a radial drive into a 28 mm knob. Rejected.
- A printed backing anvil instead of a thumb: the board's back-part layout is unmeasured (MP-ENC), and a thumb
  conforms to it. Kept only as a fallback if G-MP-ENC shows parts that a thumb must not press.

## 3. Exact implementation

No printed or COTS geometry changes. No KEEPOUTS, CABLES or BOM rows change. All changes are sequence data, two new
layout tables, one new check category and text.

### 3.1 layout.py

| Where | Change |
|---|---|
| `STEPS` step 2 | `bench=['panel', 'encoder', 'switch_1824', 'knob_exp', 'knob_fps']`. `tool`: add "caliper with depth rod; vise with soft jaws (2 wood offcuts); printer paper (2 strips, about 0.2 mm)". `action`: the step-2 text in s5.1. |
| `STEPS` step 8 | `adds` += `'knob_exp', 'knob_fps'` (they enter the body with the panel). `action`: replace the last sentence with the screw-pose text in s5.1. |
| `STEPS` step 9 | `adds=['eyecup', 'usb_stick', 'stick_sleeve']`. `action`: "Push the eyecup over the barrel. Fit the sleeve to the stick, push the stick in from the rear. (The knobs went on at step 2; r5: the adapter went in at step 7, the lens at step 8.)" |
| `INSERTIONS` `panel_on` | `moving=['panel', 'encoder', 'switch_1824', 'knob_exp', 'knob_fps']`; path unchanged. |
| `REMOVALS` `panel_off` | unchanged (it already moves both knobs). |
| `LATCH_FREE` | `knob_exp`: "rides with the panel. Pull straight off (+Y) only: the panel backs the encoder. Refit only at the bench with the panel off and the board backed (PRESS_FITS)". `knob_fps`: "rides with the panel; pull or press (the switch nut backs it)". |
| `PART_RATIONALE['knob_exp']` | append "Pressed on at bench step 2 with the board backed; never pressed in the body (PRESS_FITS)." |
| new `PRESS_FITS` (after `MATES`) | one row per `MATES` entry of kind `'press'`, see below. |
| new `REST_POSES` (after `STEPS`) | the step-8 pose, see below. |

```python
PRESS_FITS = [   # r7 C5-A (BX-5): how every press mate is reacted, and where it is made
    dict(part='knob_exp', onto='encoder', axis=(0, -1, 0), step=2, where='bench', retention='snap',
         backing='thumb flat on the encoder board back (panel off); 0.2 paper shim on the panel face sets the stop',
         snap_zones=['enc_tooth_top', 'enc_tooth_left', 'enc_tooth_right']),
    dict(part='knob_fps', onto='switch_1824', axis=(0, -1, 0), step=2, where='bench', retention='rigid',
         backing='switch nut on the panel face', snap_zones=[]),
    dict(part='tripod_nut', onto='base_grip', axis=TRIPOD_PRESS_AXIS, step=3, where='body', retention='rigid',
         backing='pocket floor (slip fit, flat bar seats it: BLOCKERS C-10)', snap_zones=[]),
    dict(part='stick_sleeve', onto='usb_stick', axis=STICK_SLEEVE_PRESS_AXIS, step=9, where='bench',
         retention='hand', backing='stick held in the hand before stick_in', snap_zones=[]),
]
# The tooth zones are boxes derived from ENCODER['pcb'] and ENCODER['cradle_hooks'] (same numbers as the
# CRITICAL_FEATURES cradle-tooth rows at layout.py:1656-1664): top x c+-4.0, z pcb.z1-0.40..pcb.z1+SL+1.6;
# sides z 45..50, x pcb.x0-SL-1.6..pcb.x0+0.40 and mirror; y from the hook tip (22.35) to SPLIT for all three.
SNAP_TOOTH_ZONES = {...}   # 3 boxes as above

REST_POSES = [   # r7 C5-A (BX-13): how the body sits while screws are driven after the knobs are on
    dict(id='hood_down', step=8, down='+Z', screws=['s_b1', 's_b2', 's_r1', 's_r2'], support='folded cloth',
         stop=dict(face='+Y', band_mm=25.0, x=(-145.0, -5.0), for_screws=['s_r1', 's_r2'],
                   note='flat block <= 25 mm tall against the hood band and the panel top strip')),
    dict(id='base_down_8', step=8, down='-Z', screws=['s_c4'], support='bench', stop=None),    # s_c4 snug, panel still off
    dict(id='base_down_10', step=10, down='-Z', screws=['s_c4'], support='bench', stop=None),  # level check re-snug
]
REST_FORBIDDEN = {'+Y': 'left side: knob_exp is the most proud point (y 44.2); never a rest face from step 8 on'}
```

`TRIPOD_PRESS_AXIS` and `STICK_SLEEVE_PRESS_AXIS`: take the existing directions from the tripod pocket and the stick
sleeve entries (the implementer reads them; I did not re-derive them). The snap rows and the knob rows are the ones
that matter for this cluster; the other two rows exist so the coverage rule has no exceptions.

### 3.2 checks.py: new category `handling` (29 categories after the change)

`check_handling(L, rows, parts_of=None)`. `parts_of(step)` returns {id: shape or box} in the assembly pose (default:
printed STEP solids from the build plus `COTS[...]['box']`; tests pass plain boxes, as `check_j7_float` does).

Rows of kind `press_fit`, one per `PRESS_FITS` row:
1. Coverage: every `MATES` entry of kind `'press'` has exactly one `PRESS_FITS` row (same part/onto pair).
2. Computed retention. Move the target (`onto`) by 0.3 mm along `axis`. Intersect it with every other part present
   at the end of the target's entry step, except the pressed part and anything that moves with the target.
   Subtract the volume inside the row's `snap_zones` and any overlap already present at rest (that is an
   `interference` failure, reported there). Call the rest V_rigid. Declared `rigid` needs V_rigid >= 0.5
   mm3; declared `snap` needs V_rigid < 0.05 mm3 and some overlap inside the snap zones (the hooks exist). A
   mismatch fails, so a backstop added later (for example by the angle-B design) forces the row to be updated.
   `hand` rows skip this test. Use the `cots.py` proxy solid of the target, never its bounding box (the
   `switch_1824` box spans the panel thickness at rest). Prototyped in probe p4 on the r6 panel.step and the cots.py proxies: encoder
   rest overlap 0.0, displaced overlap 1.44 mm3, all inside the 3 tooth zones, so V_rigid 0.0 (`snap`);
   switch_1824 rest overlap 0.0, V_rigid 15.92 mm3 (the nut on the panel face; `rigid`).
3. Rule for `snap`: `where == 'bench'`; the press step is a bench step (`in_body` False) and appears in that step's
   `bench` list; the pressed part first appears in a `STEPS['adds']` list at the same step as its target; and it is
   in the `moving` set of every `INSERTIONS` and `REMOVALS` path that moves the target. Any breach fails with
   "snap-retained target pressed in the body" or "pressed part not carried with its target".
4. Rule for `where == 'body'`: the target retention must be `rigid`.

Rows of kind `rest_pose`, one per `REST_POSES` row:
1. Present set = `present_at(step)`. Extreme extent along `down` over all present parts. Touching set = parts within
   0.5 mm of that extreme. Fail if the touching set holds any `PRESS_FITS` part, any `snap` target, the lens, the
   eyepiece or the eyecup. Report the margin to the next part (step 8: hood 100.0, next tub 97.3, margin 2.7).
2. Stop slab: the half-space beyond the stop face plane (y > YL - 0.01) limited to the band (`band_mm` from the rest
   plane) and the x range. Fail if any present part other than panel, hood or tub enters the slab, or if no part
   reaches the face plane within 0.05 (no bearing). Report the clearance from the band to the nearest knob (4.0) and
   to the eyepiece along x (4.5).
3. Coverage: every screw driven at or after the step where a `snap`-target press part enters the body (step 8)
   appears in a `REST_POSES['screws']` list at its step: s_b1, s_b2, s_r1, s_r2 (`hood_down`), s_c4 at steps 8 and
   10 (`base_down_8`, `base_down_10`: touching sets {base_grip} at z -110.0, next strap -108.0, margin 2.0; and
   {cap} at -116.0, next base_grip -110.0, margin 6.0; computed from the same extents as s1).

Info rows (not pass/fail): the touching set of every `REST_FORBIDDEN` face for steps 8-10 (today `knob_exp` at
y 44.2), so the guide can cite it.

### 3.3 Other code

- `build_d2.py`: register `handling` in the category list and the receipt; no other change.
- `make_tables.py`: no code change. It regenerates the step tables from `STEPS` and `INSERTIONS` (step 2 bench list,
  step 8 parts and `panel_on` motion, step 9 parts).
- New `test_r7_c5_handling.py` (planted faults, s4).
- `guide/guide_steps.py`: s5.2.

## 4. Computed checks and planted-fault regressions

New category `handling` (s3.2): `press_fit` rows (4), `rest_pose` rows (3), coverage rows (2), info rows (3).
Pass criterion: every non-info row passes. Existing checks that now also cover the change, with no code change:
`sweeps` (`panel_on` sweeps the knobs), `driver` (the step-8 audit set gains both knobs), `removals` (unchanged),
`mate_overlap` (knob mates unchanged).

`test_r7_c5_handling.py`, in the style of `test_r3_regressions.py` (fast: a copied layout namespace plus box
`parts_of`, no CAD build):

| Test | Planted fault | Expected |
|---|---|---|
| `test_knob_pressed_in_body_fails` | move `knob_exp` from the step-2 `bench` and step-8 `adds` lists back to step-9 `adds` (the r6 state) | `press_fit knob_exp` fails: "snap-retained target pressed in the body" |
| `test_knob_not_carried_fails` | drop `knob_exp` from `panel_on.moving` | `press_fit` fails: "pressed part not carried with its target"; `sweeps panel_on` also fails (the encoder shaft sweeps through a static knob) |
| `test_press_mate_without_row_fails` | delete the `knob_fps` row of `PRESS_FITS` | coverage row fails |
| `test_snap_declared_rigid_fails` | set `knob_exp` `retention='rigid'` | `press_fit` fails: V_rigid 0.0 < 0.5 |
| `test_backstop_makes_snap_stale` | add a 26 x 0.2 x 26 plate at y 19.3..19.5 on the encoder axis (0.1 behind the rearmost back part, the QT sockets at y 19.6) to `parts_of(8)` | `press_fit knob_exp` fails: "declared snap but backed (V_rigid > 0.05): update PRESS_FITS" |
| `test_rest_on_left_side_fails` | `REST_POSES` step 8 `down='+Y'` | `rest_pose` fails: touching set {knob_exp} |
| `test_bare_shaft_rest_fails` | r6 state (knobs at step 9) and `down='+Y'` at step 8 | fails: touching set {encoder} (shaft at y 44.0): BX-13 as reported |
| `test_stop_band_too_tall_fails` | `band_mm=32.0` | `rest_pose` fails: `knob_exp` enters the stop slab |
| `test_stop_over_eyepiece_fails` | `x=(-160.0, -5.0)` | fails: eyepiece (y 35.25) in the slab |
| `test_screw_without_pose_fails` | remove `s_r2` from `REST_POSES['screws']` | coverage row fails |

## 5. Document changes

### 5.1 ASSEMBLY.md (hand text; the step tables regenerate from `STEPS`)

- **s1.1 tools**, row 7: "Junior hacksaw + small flat file + caliper (depth rod) + a vise with soft jaws (2 wood
  offcuts) | measure the switch shaft in place, then cut it off the panel and deburr (2)". New row 15: "Printer
  paper, 2 strips (about 0.2 mm together) | knob stop shim (2) | - | -". Row 6 stays.
- **Step 2** text: "Paint-fill the engraving. **Switch shaft, off the panel:** fit the 18/24 switch dry (tab in its
  slot, the washer as supplied, nut finger-tight). Measure how far the shaft stands above the panel face (P, caliper
  depth rod). Take the switch off. Clamp the shaft in soft vise jaws right next to the cut and cut P - 7.0 mm off
  its end. Never clamp the bushing thread and never saw with the switch on the panel. Deburr. Refit the switch (tab
  in its slot), nut finger-tight + 1/8 turn. **Encoder:** snap it into its cradle by pushing on the back of its board
  until all 3 hooks click. **Knobs:** lay the 2 paper strips on the panel face round the encoder shaft. Keep your
  thumb flat on the back of the encoder board and press `knob_exp` onto its D shaft with the other palm until it
  stops on the paper. The thumb takes the push, not the hooks. Press `knob_fps` on the same way, its flat to the D
  flat (the switch nut takes the push). Pull the paper out. From now on the knobs ride with the panel: never press a
  knob while the panel is on the body."
- **Step 8**, replace the last sentence: "Hold the panel home and turn the camera over onto its hood roof on a folded
  cloth, grip up. Lay a flat block no taller than 25 mm (a closed paperback) on the cloth against the left side,
  between the eyepiece and the lens; it bears on the hood band and the panel strip below the knobs, and keeps the
  panel home. Drive s_b1 and s_b2 down. Drive s_r1 and s_r2 horizontally from the right, the block taking the push
  (hold the grip with your other hand). 0.35-0.5 N m, stop at head contact. Never lay the
  camera on its left side: the exposure knob would carry it."
- **Step 9** text: as in s3.1.
- **s3 checks.** Row 2 add: "Knobs on: a paper strip slides under each knob skirt with light drag (0.2 gap); the
  shaft ends sit just below the knob tops; the switch shaft stands 7.0 +-0.3 above the panel face and was cut off
  the panel." Row 8 add: "Screws driven in the hood-down pose; the camera was never on its left side." Row 9: delete
  "Knobs fully on;".
- **s5 Battery use** (handling), add: "Set the camera down on its base or its right side. Never on its left side: the
  exposure knob is the highest point there and would push the encoder off its cradle."
- **s7 service.** Item 2: replace "and the two knobs off their shafts (reverse step 9)" with "(the knobs stay on:
  they ride with the panel)". Item 3: add "Use the step-8 pose (hood roof down on a cloth, block against the left
  side for s_r1/s_r2). If the eyecup is on, the cloth takes its 0.76 mm." Item 4 stays ("the knobs ride out on their
  shafts"). New item 4a **Knob change**: "Pull the old knob straight off (+Y); the panel backs the encoder for a pull.
  To fit a knob, take the panel off first (items 3-4) and press it on at the bench as in step 2, thumb behind the
  encoder board. Never press a knob on with the panel on the body."

### 5.2 Other documents

- **MEASURED-PARTS.md**, MP-ENC gate. G-KNOB-1 add: "record the press-on force with the board backed (kitchen scale
  under the panel coupon, N) and the pull-off force". G-ENC-1 add: "cradle pull-out along -Y on the panel coupon
  (push the shaft with a scale, board unbacked) >= 25 N. Basis: 3 x the camera weight (8.8 N with the Kowa) resting
  on the knob; this also covers the declared < 5 N push. Below 25 N, adopt a backstop (angle B) before the first
  build." Add: "if the shaft would stand more than 9.0 above the panel face, cut it with the encoder out of the
  cradle". MP-SW gate G-MP-SW: replace "after the cut (y 42.0 +-0.3, deburred)" with "record P (dry-fit
  protrusion), the washer position (body side or nut side) and thickness, and the length cut; the cut is made off
  the panel; final 7.0 +-0.3 above the face, deburred. The knob nut recess clears nut + washer by >= 0.25 (CAD:
  recess roof y 38.45, nut top 37.4, bushing end 38.2, so 1.05 and 0.25). A nut-side washer thicker than 0.8 needs a
  deeper `knob_fps` recess (knob reprint only)."
- **printed_small.py** `PRINT['knob_exp']['notes']`: "Pressed on at bench step 2 with the encoder board backed
  (ASSEMBLY step 2); never pressed on in the closed body." Text only, the STL is unchanged. It is still a receipt
  source edit.
- **WIRING.md** s7: no change for this cluster. Note for the BX-2 cluster: plugging the QT pushes the encoder +Y,
  which the panel backs; unplugging pulls -Y into the teeth, so pinch the plug while a fingertip pushes the board back
  toward the panel.
- **BOM.md / bom.csv / harness-schedule.csv**: no change. Paper, cloth and a paperback are not BOM items. The caliper
  and vise are tool rows in ASSEMBLY s1.1 only.
- **guide/guide_steps.py**: step-2 page: `new` += `'knob_exp', 'knob_fps'`; parts += "2 knobs (printed)"; tools +=
  caliper, vise, paper; `do` = the step-2 text in 5 short lines (cut off the panel; refit the switch; snap the
  encoder; thumb behind the board, press `knob_exp` onto the paper; `knob_fps` the same); `check` += "knobs 0.2 off
  the panel (paper drags)", "switch shaft 7.0 above the face". Step-9 page: `new` and `offsets` drop both knobs;
  parts drop "2 knobs"; `do` drops "Push the two knobs onto their D shafts."; `check` drops "knobs fully on". Page
  8b: the knobs are drawn on the panel (they move with it). Page 8c: `do` gets the hood-down pose and the block; the
  view shows the camera inverted. Delete `ISSUES['9']` and `ISSUES['2']` (BX-5), `TIPS['2']` (BX-14) and
  `TIPS['8c']` (BX-13): the fixes are now in the steps. New `TIPS['10']`: "Set the camera down on its base or right
  side, never on its left side (knobs)."
- **guide/BLOCKERS-2026-10-08.md**: leave the review as written. HANDOFF.md records BX-5, BX-13 and BX-14 as closed
  by r7 C5, with the new `handling` rows as evidence.

## 6. Interactions and risks

| Check / area | Effect | Evidence |
|---|---|---|
| sweeps | `panel_on` moving set gains both knobs. | p1: 0.0 mm3 against every static step-8 part; `stick_in`, `pack_in`, `cap_on` already list the knobs as obstacles. |
| removals | none: `panel_off` already moves the knobs; `LATCH_FREE` text only. | `removals` 12/12 today. |
| driver, service_driver | the step-8 audit set gains both knobs. | bit gaps >= 50.61, handle gaps >= 86.04 mm (p1); 11/11 expected to stay. |
| EVF restraint | none. The hood-down pose is used only after the panel is pushed on, when its cap clamps the eyepiece spigot. Between steps 6 and 8 keep the body level or nose-down (existing wording). | `evf_restraint` 6/6. |
| j7_float, lens | geometry unchanged. The hood-down pose turns the lens and camera over; by then the 2 thumb screws are tight and s_c4 is at 0.2 N m (step 8 order). The collar holds the lens; the camera still touches nothing. | `j7_float` 49/49 is pose-independent geometry. |
| thin_wall, critical_features, print_overhang, bed_fit, stl_mesh | none (no geometry change). | - |
| keepouts, cable_routes | none. QT plugging pushes the encoder +Y into the panel (backed); see the WIRING note for unplugging. | - |
| mass_com | none. | - |
| rest pose geometry | the hood roof is one flat face, x -169.9..-2.5, y -32.3..34.9 at z 100 (p3); the CoM (x -45.5, y 0.84) lies inside it. The stop band bears on about 2966 mm2 of panel face and 308 mm2 of hood band (p3). | p3 |
| other clusters | BX-2 (QT lead, panel tilted from its bottom edge): the knobs are on the outer face and do not touch the body when the panel is tilted outward. BX-4 (camera hold at step 8): unaffected. If the angle-B designer adds a backstop behind the encoder, the `press_fit` row flips from `snap` to `rigid` by computation; keep the bench press anyway (cheapest load path). | - |

Weaknesses of this angle, stated plainly:
1. **In-use loads still go through the 0.4 mm teeth.** A user pushing on the knob while turning it, the encoder push
   (< 5 N) and the camera set down on its left side all push the encoder -Y. Angle A only removes the largest load
   (the press fit). My rough release estimate (45-90 N) is about 10x these loads, but it is an estimate. G-ENC-1 with
   the new 25 N threshold decides. If it fails, a backstop (angle B) is needed.
2. **The thumb presses the parts on the board back.** Their layout is unmeasured (MP-ENC). The press force is unknown
   until G-KNOB-1. A thumb spreads tens of newtons safely over SMD parts and the two JST-SH sockets (pressing them
   toward the board, the mating direction). If G-MP-ENC finds a part that must not be pressed, print a small backing
   pad that bears on the free strips; this is the named fallback.
3. **A knob change costs one panel opening**: 4 PT drives on the 5-drive tally (FASTENER-POLICY C). A knob pull-off
   alone does not. Knob changes should be rare.
4. **The rest pose depends on the user.** The guide and the s5 handling note must be followed. The `rest_pose` check
   proves that the stated pose is safe; it cannot stop someone from laying the camera on its left side later.
5. **s_r2 sits 52.5 mm above the bench in the hood-down pose**, above the 25 mm block. The thrust on s_r2 makes a
   tipping moment about the block edge; the other hand holds the grip. The block still takes the thrust, so the base
   joint does not.

## 7. Acceptance criteria

Computed (after the full rebuild through `run_locked.py`):

| Check | Must hold |
|---|---|
| `handling` press_fit | 4/4 pass. `knob_exp`: retention `snap`, V_rigid 0.0 mm3 with tooth overlap 1.44 mm3; pressed at bench step 2; carried by `panel_on` and `panel_off`. `knob_fps`: `rigid`, V_rigid 15.92 mm3 (>= 0.5). |
| `handling` rest_pose | `hood_down` passes: touching set {hood} at z 100.0, next part tub 97.3 (margin 2.7); stop slab free of knobs (4.0 mm to `knob_exp`) and of the eyepiece (4.5 mm in x); bearing parts panel and hood. `base_down_8` and `base_down_10` (s_c4) pass: touching {base_grip} (margin 2.0) and {cap} (margin 6.0). |
| `handling` coverage | every `'press'` mate has a row; s_b1, s_b2, s_r1, s_r2 and s_c4 (steps 8 and 10) are covered by a rest pose. |
| ASSEMBLY tables | step 8 "In the body after this step" 35 -> 37 ids; step 9 stays 40; step 2 bench list shows both knobs. |
| `sweeps` | 14/14; `panel_on` moving set includes both knobs; 0 mm3. |
| `driver`, `service_driver` | 11/11 each; knob gaps >= 50 mm (bit) and >= 86 mm (handle). |
| everything else | all 28 existing categories pass with unchanged numbers (no geometry change); categories become 29. |
| tests | `test_r7_c5_handling.py` 10/10, plus the existing test files unchanged. |

Physical gates that later confirm it: G-KNOB-1 (press-on force with the board backed; pull-off force); G-ENC-1
(cradle -Y pull-out >= 25 N on the panel coupon); G-MP-ENC (back-part layout: thumb-safe or the backing pad);
G-MP-SW (P, washer position and thickness, cut off the panel, 7.0 +-0.3); G-PANEL-1 (panel openings, unchanged).

## 8. User decisions

None required. This angle uses no new purchased part and no printed geometry change. Decided here: a knob change
needs the panel off (one tally drive per screw); the bench aids (paper strips, folded cloth, a block <= 25 mm, a
vise with soft jaws, a caliper) are household or workshop items, not BOM rows.

## 9. Effort and receipt sources

| Work | Hours |
|---|---|
| layout.py: STEPS, INSERTIONS, LATCH_FREE, PART_RATIONALE, PRESS_FITS, SNAP_TOOTH_ZONES, REST_POSES | 0.75 |
| checks.py `check_handling` + build_d2.py registration | 2.0 |
| test_r7_c5_handling.py (10 planted faults) | 1.0 |
| ASSEMBLY.md, MEASURED-PARTS.md, printed_small.py note, guide_steps.py, HANDOFF.md | 1.25 |
| full release rebuild through run_locked.py, guide rebuild, review of the receipt | 0.75 (machine time extra) |
| **Total** | **about 5.75** |

Receipt sources touched: `layout.py`, `checks.py`, `build_d2.py`, `printed_small.py` (note text only). Changing
`layout.py` forces a full release rebuild. ASSEMBLY.md and DESIGN.md step tables regenerate through
`make_tables.py`. The guide rebuilds from `guide_steps.py`. No STL changes are expected; if the build shows any STL
hash change, stop and find out why.
