# SPEC-C5: exposure knob press, panel shafts, switch shaft cut (BX-5 MAJOR, BX-13, BX-14)

**r7 fix-up correction (VERIFY-C5, 2026-10-09).** Two rest-pose rules were missing and are now computed in
`handling` rest_pose for every row whose support is not 'hand': (1) driver plane: the straight driver (bit, handle +
10 mm of fingers [est]) must stay on the body side of the rest plane unless the row declares `overhang` (the body face
within edge_mm of the bench edge); s_r1 in the hood-down pose crosses the plane by 10.5 mm, so hood_down and
hood_down_s7 now declare overhang -Y, 20 mm (step 8: right face within about 20 mm of the bench edge). (2) static
stability: the centre of mass (every lens) inside the hull of the lowest 1 mm with a tip angle >= 10 deg [design
choice]; standing on the grip end tips at about 6 deg, so base_down_8/10 are support='hand' and the text never leaves the
camera standing on its grip end. New unattended rests: right_down_8 and right_down_10 (the hood roof is no rest at
step 10: the eyecup stands 0.76 proud). The REST_POSES listing below is superseded by layout.py.

Status: FINAL spec (judge + synthesis), r7 blocker round, 2026-10-08 23:15-00:40 MPST. Built from DESIGN-C5-A
(sequence) and DESIGN-C5-B (back-stop plate). Base: A. Added: a computed tripwire that makes B's plate mandatory
when its trigger conditions occur, B's eyepiece wording, and corrections from my own probes. B's plate is kept as a
ready contingency design, not built now. No repo file was changed except this one. Judge probes:
session scratchpad `r7/C5J/j1.py`, `j2.py` (layout import + r6 part STEPs in `out/step/parts/`, 16:05 build). Nothing has
been printed, bought or measured.

## 1. Problem, re-checked in the current code

| Item | Current code / probe | BLOCKERS figure | Verdict |
|---|---|---|---|
| What backs the encoder against a -Y push | j1: `panel.step` inside a box 1 mm round the PCB footprint, behind the back face (y 10..24.1), holds exactly 3 solids: the hook ends (17.4 + 10.9 + 10.9 mm3 in that box; A's larger box gave 29.3 + 18.3 + 18.3). Top tooth z 69.4..70.8 against the PCB top edge z 69.8; side teeth reach x -75.25 / -50.75 against the PCB edges -75.65 / -50.35. No other part, keep-out or COTS box sits behind the board (B, `space.py`). | "only the 3 cradle hook teeth (0.4 mm)" | correct |
| Tooth form | `printed_panel.CRADLE` tooth 0.65 (= reach 0.40 + SLIDE 0.25), lead 45 deg, `d2_common.snap_hook` called with the default `ret_deg=0.0`: a square return face. The panel prints face down (+Y), so the return face is a 0.65 mm overhang facing the bed. It will droop by an unknown amount. | - | the real return angle is unknown |
| Hook release force (estimate, not in the repo) | Two models bracket it. B (ramp, return face sagged to 45-60 deg, E 1.6-2.2 GPa, mu 0.3, load split top 0.426 / sides 0.287): 22-31 N at 45 deg, 51-69 N at 60 deg. A (square face, eccentric tension, e about 1.0): about 90 N. I re-derived both (top hook lateral stiffness 3EI/L^3 = 15.4 N/mm at E 1.8 GPa, so 6.2 N to open 0.4; ramp at 45 deg gives 25-27 N at the knob; eccentric model 88-95 N). Range: **about 22-95 N**. | not stated | a snug FDM press fit (30-50 N) sits inside the band: **BX-5 is a real MAJOR** |
| What backs the encoder against a +Y pull | The encoder body front face (12.5 x 13.5) bears on the panel inner face; the panel is solid there apart from the dia 7.5 hole (A, p1: 74.7 mm2). | not stated | a pull-off is safe with the panel on; only a push is unsafe |
| In-use push path (new) | j1: the `knob_exp` underside is a flat land of 389 mm2 (j2: 0.25 slab from y 35.2), 0.20 (gP) above solid panel: 389 mm2 of panel under that footprint (100 %), inside a fully solid annulus of 512 mm2 at r 5.75..14 (the engraving starts at r 15.8). The bench squeeze (s2) ends with the board pressed onto the panel inner face, so gP 0.20 is set at the board's +Y limit. A push moves the board through its 0.1 play onto the teeth, then compresses the encoder push switch; the knob lands on the panel after 0.1 mm of shaft travel (gP 0.20 minus the 0.1 play). From then on the panel takes the push. So in use the hooks carry at most the switch spring force at 0.1 mm of stroke (< 5 N, `PART_RATIONALE['knob_exp']`), **if** the real shaft has more than 0.1 mm of push travel (MP-ENC). | not stated | in-use loads are capped today; see the tripwire for the case where the push is commissioned |
| Push status | `ENCODER['push']`: `required_travel_mm=None`, "push operation not commissioned". MEASURED-PARTS G-MP-ENC requires gP - s >= 0.25 once the push is used. Then the knob no longer lands before the switch bottoms, and every firm push goes into the hooks. | - | **commissioning the push needs a positive back-stop**: encoded as a check (s4) |
| Thumb access at the bench | j1: a dia 20 column on the encoder axis from y -40 up to the PCB back (y 24.1) holds 0.0 mm3 of panel. | "backing the encoder PCB with a thumb" | feasible |
| Bench block alternative | j1: the panel reaches y -30.4 (its posts). A block under the board with the panel face up must be >= 49.2 mm tall (24.1 - 5.3 back parts + 30.4) or the posts land first. B's "25 x 25 block under the plate" did not state this. | - | use the thumb pinch, not a bench block |
| Proud shafts (BX-13) | j1, step 8 (r6): +Y extremes `encoder` 44.0, `switch_1824` 42.0, then eyepiece 35.25, base_grip 35.2. Steps 9-10: `knob_exp` 44.2, `encoder` 44.0, `knob_fps` 42.2. | 7-9 mm proud | correct |
| Hood-down rest face | j1, step 8: +Z extremes hood 100.0, tub 97.3, eyepiece 97.25, panel 97.0 (A, p3: one flat roof face x -169.9..-2.5, y -32.3..34.9; CoM x -45.5, y 0.84 inside it). **Steps 9-10: the eyecup is the +Z extreme at 100.76.** | - | **new**: in service the eyecup must come off before the camera is laid on its hood roof (A's s7 text rested it on the eyecup) |
| Knob z band | j1: `knob_exp` z 43.0..71.0, `knob_fps` z 47.0..67.0. Hood roof z 100: a 25 mm block band ends at z 75, 4.0 clear of `knob_exp`. | - | A's block figure correct |
| Switch stack (BX-14) | `SWITCH_1824`: body face y 32.2 (= SPLIT), bushing to 38.2, shaft to 42.0 (7.0 above the face y 35.0; 9.8 above the body face), nut y 35.0..37.4. The washer of "nut + washer" (BOM D2-11) is not modelled; its side is unknown. | "7.0 above the panel face; measure the stack" | correct. Both knob bores run through to the top (`printed_small.build_knob`), knob tops at 42.2 / 44.2: a shaft cut long shows above the knob, so the cut tolerance is one-sided (s3.5) |
| Press mates | `MATES` has 5 rows of kind `press`: tripod_nut/base_grip, stick_sleeve/usb_stick, knob_exp/encoder, knob_fps/switch_1824, **pi5/usb_stick**. | - | A's `PRESS_FITS` table had 4 rows; the coverage rule needs all 5 |

No BLOCKERS number is wrong. Two facts are new: a +Y pull is safe, and the eyecup is the hood-down extreme from
step 9.

## 2. Chosen fix and why

**Sequence fix now (angle A), with a computed tripwire that forces the back-stop plate (angle B) if a measured or
commissioned fact takes away its basis.**

1. **BX-5.** Both knobs are pressed on at bench step 2, panel off. One thumb lies flat on the encoder board back;
   the other palm presses the knob until it stops on a 0.2 mm paper shim on the panel face. The squeeze goes palm ->
   knob -> shaft -> board -> thumb, and at the end knob -> paper -> panel -> encoder body -> board -> thumb. The hooks
   carry nothing. The knobs then ride with the panel through `panel_on` and `panel_off`. No knob is ever pressed
   while the panel is on the body (computed rule). A knob may be pulled off with the panel on.
2. **In use.** The knob land caps the hook load at the switch spring force (s1). The new check proves the cap
   exists in CAD, and fails if the push gets commissioned (`required_travel_mm` set) or if G-ENC-1 records a
   pull-out below 25 N while the encoder is still snap-retained. Either failure means: build DESIGN-C5-B's
   `enc_stop` plate.
3. **BX-13.** Once the knobs are on, the left side is never a rest face. All 4 panel screws are driven with the
   camera upside down on its hood roof on a folded cloth, and a flat block no taller than 25 mm against the left
   side takes the s_r1/s_r2 thrust and holds the panel home. Between steps 6 and 8 the body stays level or nose-down
   (eyepiece, from B). In service the eyecup comes off first.
4. **BX-14.** The switch shaft is never cut on the panel. Dry-fit, measure the protrusion P in place, take the
   switch off, cut P - 6.9 off the shaft in soft vise jaws, refit. This holds for any washer stack.

Why not B now: B removes the in-use path too, but today that path is already capped by the knob land and the push is
not used. B costs a new printed part, 2 posts and a play change on the panel (a geometry change of the largest
print), 2 more PT screws (11 -> 13) and a paper fit step whose pads depend on unmeasured corner zones. The user rule
prefers a sequence fix when it removes the problem; for the defect as found (the press), A removes it fully. The
tripwire keeps B one decision away, with its design already written (DESIGN-C5-B s3).
Also rejected: "twist the knob on lightly" (wording only); a grub-screw knob (a radial fastener in a 28 mm knob);
locking the hooks (B s2: only 0.25-0.40 engaged after FDM, and C2's `ko_qt_tail` sits 0.5 mm off the left hook);
a printed bench anvil as the default (kept as the fallback if MP-ENC shows thumb-unsafe back parts).

## 3. Exact implementation

No printed or COTS geometry changes. No KEEPOUTS, CABLES, harness or BOM rows change. Changes: sequence data, three
new layout tables, one new check category, text.

### 3.1 layout.py

| Where | Change |
|---|---|
| `STEPS` step 2 | `bench=['panel', 'encoder', 'switch_1824', 'knob_exp', 'knob_fps']`. `tool` += "; caliper with depth rod; vise with soft jaws (2 wood offcuts); printer paper, 2 strips (about 0.2 mm together)". `action`: the step-2 text of s5.1. |
| `STEPS` step 6 | `action` += "From now until the panel is on (step 8) keep the body level or nose-down: only the panel's EVF cap stops the eyepiece moving rearward." |
| `STEPS` step 8 | `adds` += `'knob_exp', 'knob_fps'` (they enter with the panel). `action`: replace the last sentence ("Drive s_b1, s_b2 up from below and s_r1, s_r2 from the right: ...") with the screw-pose text of s5.1. C4 edits the lens-hold part of the same string: merge, do not overwrite. |
| `STEPS` step 9 | `adds=['eyecup', 'usb_stick', 'stick_sleeve']`. `action`: "Push the eyecup over the barrel. Fit the sleeve to the stick, push the stick in from the rear. (The knobs went on at step 2; r5: the adapter went in at step 7, the lens at step 8.)" |
| `INSERTIONS` `panel_on` | `moving=['panel', 'encoder', 'switch_1824', 'knob_exp', 'knob_fps']`; path unchanged. (`REMOVALS` `panel_off` already moves both knobs.) |
| `LATCH_FREE` | `knob_exp`: "rides with the panel. Pull straight off (+Y) only (the panel backs the encoder for a pull). Press on only at the bench, panel off, board backed (PRESS_FITS)". `knob_fps`: "rides with the panel; pull or press (the switch nut backs it)". |
| `PART_RATIONALE['knob_exp']` | append "Pressed on at bench step 2 with the board backed by a thumb; never pressed in the body (PRESS_FITS, check handling)." |
| new `PRESS_FITS`, `SNAP_TOOTH_ZONES` (after `MATES`) | below |
| new `REST_POSES`, `REST_FORBIDDEN` (after `STEPS`) | below |

```python
PRESS_FITS = [   # r7 C5 (BX-5): how every 'press' mate is reacted, and where it is made. Checked by `handling`.
    dict(part='knob_exp', onto='encoder', axis=(0, -1, 0), step=2, where='bench', retention='snap',
         backing='thumb flat on the encoder board back (panel off); 0.2 paper shim on the panel face is the stop',
         backing_axis_d=20.0,                       # thumb column dia, along -axis from the target back face
         snap_zones=['enc_tooth_top', 'enc_tooth_left', 'enc_tooth_right'],
         release_min_N=25.0, release_N=None,        # G-ENC-1: measured -Y pull-out of the cradle; None = not measured
         contingency='DESIGN-C5-B enc_stop (r7-blockers/DESIGN-C5-B.md s3)'),
    dict(part='knob_fps', onto='switch_1824', axis=(0, -1, 0), step=2, where='bench', retention='rigid',
         backing='switch nut on the panel face', snap_zones=[]),
    dict(part='tripod_nut', onto='base_grip', axis=None, step=3, where='body', retention='rigid',
         backing='pocket floor (slip fit, the flat bar seats it: BLOCKERS C-10)', snap_zones=[]),
    dict(part='stick_sleeve', onto='usb_stick', axis=None, step=9, where='bench', retention='hand',
         backing='stick held in the hand before stick_in', snap_zones=[]),
    dict(part='usb_stick', onto='pi5', axis=(1, 0, 0), step=9, where='body', retention='held',
         holders=['x1203_kit'], backing='Pi 5 on the X1203 kit standoffs (MATES pi5/x1203_kit contact)', snap_zones=[]),
]
```

- `axis=None` on the tripod row: the implementer copies the press direction from the tripod pocket entry (the pocket
  opening normal). If the computed V_rigid is < 0.5 mm3 with the proxies, declare it `held` with
  `holders=['base_grip']`. Do not loosen the thresholds.
- `SNAP_TOOTH_ZONES`: 3 boxes from `ENCODER` only (no import of printed_panel). With `h = ENCODER['cradle_hooks']`,
  `p = ENCODER['pcb']`, `SL = FDM['SLIDE']`, `y = (p.y0 - h.play - h.land - 0.05, SPLIT)`:
  `enc_tooth_top` x `c.x +- h.top.w/2`, z `(p.z1 - h.tooth - 0.05, p.z1 + SL + 2.0)`;
  `enc_tooth_left` x `(p.x0 - SL - 2.0, p.x0 + h.tooth + 0.05)`, z `h.sides.z`;
  `enc_tooth_right` mirror on `p.x1`. Today these contain the 3 hook ends found in j1 (top x -67..-59, z 69.4..70.8;
  sides x -76.65..-75.25 and -50.75..-49.35, z 45..50, all y 22.35..24.1).

```python
REST_POSES = [   # r7 C5 (BX-13): how the body sits while screws are driven once a snap-target press part is on
    dict(id='hood_down', step=8, down='+Z', screws=['s_b1', 's_b2', 's_r1', 's_r2'], support='folded cloth',
         stop=dict(face='+Y', band_mm=25.0, x=(-145.0, -5.0), for_screws=['s_r1', 's_r2'],
                   note='flat block <= 25 mm tall against the hood band and the panel strip above the knobs')),
    dict(id='base_down_8', step=8, down='-Z', screws=['s_c4'], support='bench', stop=None),
    dict(id='base_down_10', step=10, down='-Z', screws=['s_c4'], support='bench', stop=None),   # level-check re-snug
    dict(id='hood_down_s7', removal='panel_off', remove_first=['eyecup'], down='+Z',
         screws=['s_b1', 's_b2', 's_r1', 's_r2'], support='folded cloth',
         stop=dict(face='+Y', band_mm=25.0, x=(-145.0, -5.0), for_screws=['s_r1', 's_r2'], note='as hood_down')),
]
REST_FORBIDDEN = {'+Y': 'left side: knob_exp is the most proud point (y 44.2) from step 8 on; never a rest face'}
```

For a `removal` row the present set is the final state used by `checks.service_context` for that removal before
it moves (final ids minus the removal's `off` list), minus `remove_first`; the panel and its screws are still in.

### 3.2 checks.py: new category `handling`

`check_handling(L, rows, parts_of=None)`. `parts_of(state)` returns {id: shape or box} in the assembly pose
(default: printed solids from `rows` plus the `cots.py` proxy solid of each COTS part, never its bbox, because the
`switch_1824` bbox spans the panel at rest; tests pass plain boxes, as `check_j7_float` does). Row kinds:

1. `press_cover` (1 row): every `MATES` row of kind `press` has exactly one `PRESS_FITS` row (same pair), and every
   `PRESS_FITS` row names a real `press` mate.
2. `press_fit` (1 row per `PRESS_FITS` row except `hand`):
   - Arrest set = final ids minus the pressed part, the target and every `PRESS_FITS` part that rides on the target.
   - The rest overlap of the target with the arrest set is reported (`interference` owns any real clash).
   - Move the target 0.3 mm along `axis`; subtract the rest overlap. V_zone = overlap inside `snap_zones`;
     V_rigid = the rest.
   - `rigid` needs V_rigid >= 0.5 mm3. `snap` needs V_rigid < 0.05 and V_zone > 0.05 (the hooks exist and nothing
     else backs the target). `held` needs every holder present at the press step with a `contact` MATES row to the
     target. A mismatch FAILS, so a later back-stop (enc_stop) forces the row to `rigid`.
   - Rule for `snap`: `where == 'bench'`; the step is a bench step (`in_body` False) whose `bench` list holds part
     and target; the pressed part first appears in a `STEPS` `adds` list at the same step as its target; it is in
     `moving` of every `INSERTIONS` and `REMOVALS` entry that moves the target. Messages: "snap-retained target
     pressed in the body", "pressed part not carried with its target".
   - Backing access for `snap`: a cylinder of dia `backing_axis_d` on the target axis, from the target's back face
     60 mm along -axis, holds 0 mm3 of the bench parts of that step other than the target (today 0.0, j1).
   - Rule for `where == 'body'`: retention must be `rigid` or `held`.
   - Re-run today (A's p4 against the panel): encoder rest 0.0, displaced 1.44 mm3, all inside the tooth zones, so
     V_rigid 0.0: `snap`. switch_1824 rest 0.0, V_rigid 15.92 mm3 (the nut on the panel face): `rigid`.
3. `snap_basis` (1 row per `snap` row). FAIL if `ENCODER['push']['required_travel_mm']` is not None ("push
   commissioned: firm pushes load the cradle hooks; build the contingency back-stop and re-declare the row rigid"),
   or if `release_N` is not None and `release_N < release_min_N` ("G-ENC-1 below 25 N: build the contingency").
   Otherwise pass with the computed land: A_land = the pressed knob's material in a 0.25 slab above its lowest face
   (today 389 mm2), gP = knob y0 - YL (0.20), A_panel = panel material in a 0.2 slab under the land footprint
   (389 mm2, 100 % of the land). Pass also needs A_land >= 100 mm2, A_panel >= 0.9 A_land and gP <= 0.30, so a knob or panel change
   that removes the land cannot pass silently.
4. `rest_pose` (1 row per `REST_POSES` row). Present set as in s3.1. Find the extreme along `down`; touching set =
   parts within 0.5 mm of it. FAIL if it holds a `PRESS_FITS` part, a `snap` target, the lens, the eyepiece or the
   eyecup. Report the margin to the next part. Stop slab (when `stop`): the slab beyond the face plane
   (y > YL - 0.01), `band_mm` deep from the rest plane, over `x`. FAIL if any present part other than panel, hood or
   tub enters it, or if no part reaches the face plane within 0.05 (no bearing). Report the clearances to the
   nearest knob and to the eyepiece.
5. `rest_cover` (1 row): every screw driven at or after the step at which a `snap` row's pressed part enters the
   body (step 8), and every screw unscrewed by a `REMOVALS` entry that moves a `snap` target, is listed in a
   matching `REST_POSES` row: s_b1, s_b2, s_r1, s_r2 (hood_down, hood_down_s7) and s_c4 (base_down_8,
   base_down_10).
6. `info` rows: the touching set of each `REST_FORBIDDEN` face at steps 8-10 (today {knob_exp} at y 44.2).

`build_d2.py`: register `handling` after `sweeps` in the category order and the receipt (28 -> 29, plus what other
clusters add). It is not an INFO category: it must pass.

### 3.3 Other code

- `printed_small.py` `PRINT['knob_exp']['notes']`: "Pressed on at bench step 2 with the encoder board backed by a
  thumb (ASSEMBLY step 2); never pressed on in the closed body." Text only; the STL is unchanged.
- `make_tables.py`: no code change; it regenerates the step tables from `STEPS` and `INSERTIONS`.
- New `test_r7_c5_handling.py` (s4). `guide/guide_steps.py`: s5.3.

### 3.4 Contingency (not built now)

If `snap_basis` fails (push commissioned, or G-ENC-1 below 25 N), implement DESIGN-C5-B s3 as written (`enc_stop`
plate, posts post_eA/post_eB, s_e1/s_e2, hook play 0.30, `encoder_restraint`) and set the `knob_exp` row to
`retention='rigid'`. Keep the bench press either way. First re-check B's clearances against C2's `ko_qt_*` boxes as
finally implemented, and give the panel-face-up press a block >= 49.2 mm tall or keep the thumb pinch (s1).

### 3.5 Switch shaft cut (BX-14)

The cut length is measured in place, so no code or tool is needed. Target protrusion 6.9 above the panel face,
accepted 6.7..7.1. Reason: the `knob_fps` bore runs through to the knob top at 7.2, so a long shaft shows above the
knob. The bore holds the shaft from y 38.45 (recess roof) to the shaft end: 3.45 mm at 6.9, 3.25 at 6.7. The same
off-cradle rule covers the encoder shaft: if MP-ENC shows it more than 9.2 above the panel face (it would show above
`knob_exp`), cut it with the encoder out of the cradle.

## 4. Computed checks and planted-fault regressions

Pass criterion of `handling`: every non-info row passes. Existing checks that now also cover the change with no code
change: `sweeps` (`panel_on` sweeps both knobs), `driver` (the step-8 audit sets gain both knobs), `removals`
(unchanged, `panel_off` already moves them), `mate_overlap` (knob mates unchanged). If C6's "every `adds` id has an
INSERTIONS entry or a reason" rule lands, the knobs satisfy it through `panel_on` (today, at step 9, they have none).

New `test_r7_c5_handling.py`, in the style of `test_r3_regressions.py` (copied layout namespace, box `parts_of`, no
CAD build; one fast test per fault):

| Test | Planted fault | Expected |
|---|---|---|
| `test_knob_pressed_in_body_fails` | move `knob_exp` back to step-9 `adds` and out of the step-2 `bench` (r6 state) | `press_fit knob_exp` FAIL "snap-retained target pressed in the body" |
| `test_knob_not_carried_fails` | drop `knob_exp` from `panel_on.moving` | `press_fit` FAIL "not carried"; `sweeps panel_on` also fails |
| `test_press_mate_without_row_fails` | delete the `knob_fps` row | `press_cover` FAIL |
| `test_usb_press_uncovered_fails` | delete the `usb_stick`/`pi5` row | `press_cover` FAIL (the row A's table missed) |
| `test_snap_declared_rigid_fails` | `knob_exp` `retention='rigid'` | `press_fit` FAIL (V_rigid 0.0 < 0.5) |
| `test_backstop_makes_snap_stale` | add a 26 x 0.2 x 26 box at y 19.3..19.5 on the encoder axis to `parts_of` | `press_fit` FAIL "declared snap but backed: update PRESS_FITS" |
| `test_thumb_column_blocked_fails` | add a 30 x 3 x 30 panel rib box at y 10..13 on the encoder axis (bench part) | `press_fit` backing-access FAIL |
| `test_push_commissioned_fails` | `ENCODER['push']['required_travel_mm'] = 0.5` | `snap_basis` FAIL "push commissioned" |
| `test_low_release_fails` | `knob_exp` row `release_N = 18.0` | `snap_basis` FAIL "G-ENC-1 below 25 N" |
| `test_knob_land_removed_fails` | `parts_of` knob_exp as a ring with no land (underside 50 mm2) or `KNOBS['knob_exp']['y']` starting at YL + 0.5 | `snap_basis` FAIL (A_land or gP) |
| `test_rest_on_left_side_fails` | `hood_down` `down='+Y'` | `rest_pose` FAIL, touching {knob_exp} |
| `test_bare_shaft_rest_fails` | r6 state (knobs at step 9) and `down='+Y'` at step 8 | FAIL, touching {encoder} (shaft y 44.0): BX-13 as reported |
| `test_service_rest_on_eyecup_fails` | `hood_down_s7` `remove_first=[]` | `rest_pose` FAIL, touching {eyecup} at z 100.76 |
| `test_stop_band_too_tall_fails` | `band_mm=32.0` | FAIL, `knob_exp` in the stop slab |
| `test_stop_over_eyepiece_fails` | `x=(-160.0, -5.0)` | FAIL, eyepiece in the slab |
| `test_screw_without_pose_fails` | remove `s_r2` from `hood_down.screws` | `rest_cover` FAIL |

## 5. Document changes

### 5.1 ASSEMBLY.md (hand text; the step tables regenerate from `STEPS` through make_tables.py)

- **s1.1 tools.** Row 7 becomes: "Junior hacksaw + small flat file + caliper with depth rod + a vise with soft jaws
  (2 wood offcuts) | measure the switch shaft in place, then cut it off the panel and deburr (2) | D2-69 | **(a)**".
  New row (next free number at merge; C4 may take 15): "Printer paper, 2 strips (about 0.2 mm together) | knob stop
  shim (2) | - | -". A folded cloth and a closed paperback (block <= 25 mm) are named in the step-8 text, not as rows.
- **Step 2** (replaces the whole text): "Paint-fill the engraving. **Switch shaft, off the panel:** fit the 18/24
  switch dry (tab in its slot, the washer as supplied, nut finger-tight). Measure how far the shaft stands above the
  panel face (P, caliper depth rod). Take the switch off. Clamp the shaft in soft vise jaws right next to the cut,
  the switch hanging free, and cut P - 6.9 mm off the shaft end. Never clamp the bushing thread; never saw with the
  switch on the panel. Deburr. Refit the switch (tab in its slot), nut finger-tight + 1/8 turn. **Encoder:** snap it
  into its cradle by pushing on the back of its board until all 3 hooks click. **Knobs:** lay the 2 paper strips on
  the panel face round the encoder shaft. Hold the panel in one hand with that thumb flat on the back of the encoder
  board. Press `knob_exp` onto its D shaft with the other palm until it stops on the paper. Your thumb takes the
  push, not the hooks. Press `knob_fps` on the same way, its D flat to the shaft flat (the switch nut takes the
  push). Pull the paper out. From now on the knobs ride with the panel: never press a knob while the panel is on the
  body."
- **Step 6**, add at the end: "From now until the panel is on (step 8), keep the body level or nose-down: only the
  panel's EVF cap stops the eyepiece moving rearward."
- **Step 8**, replace the last sentence: "Hold the panel home and turn the camera over onto its hood roof on a folded
  cloth, grip up. Lay a flat block no taller than 25 mm (a closed paperback) on the cloth against the left side,
  between the eyepiece and the lens: it bears on the hood band and the panel strip above the knobs and keeps the panel
  home. Drive s_b1 and s_b2 first (now downward). Then drive s_r1 and s_r2 level from the right, the block taking the
  push; hold the grip with your other hand. 0.35-0.5 N m, stop at head contact. Turn the camera base-down. Never
  lay the camera on its left side: the exposure knob would carry it."
- **Step 9**: as `STEPS` step 9 in s3.1 (no knobs).
- **s3 checks.** Row 2, add: "Switch shaft cut off the panel: 6.7-7.1 above the panel face. Knobs on: a paper strip
  slides under each knob skirt with light drag (0.2 gap); the shaft ends sit at or below the knob tops." Row 6,
  add: "Body kept level or nose-down from here to step 8." Row 8, add: "Panel screws driven in the hood-down pose,
  block against the left side; the camera was never on its left side." Row 9: delete "Knobs fully on;".
- **s5 Battery use**, new bullet **Handling**: "Set the camera down on its base or its right side, never on its
  left side: the exposure knob is the highest point there, and resting on it presses the encoder push switch."
- **s7 service.** Item 2: replace "and the two knobs off their shafts (reverse step 9)" with "(the knobs stay on:
  they ride with the panel)". Item 3, add at the start: "Pull the eyecup off first (the panel still clamps the
  eyepiece): it is the highest point when the camera lies on its hood roof. Use the step-8 pose (hood roof down on
  a folded cloth, block against the left side for s_r1/s_r2), then turn the camera base-down before item 4." Item 4
  stays ("the knobs ride out on their shafts"). New item **4a. Knob change**: "Pull the old knob straight off (+Y):
  the panel backs the encoder for a pull. To fit a knob, take the panel off first (items 3-5) and press it on at the
  bench as in step 2, thumb behind the encoder board. Never press a knob on with the panel on the body." Item 5
  ("To close: reverse step 8"): add "in the step-8 pose".

### 5.2 MEASURED-PARTS.md

- **G-KNOB-1** add: "Record the press-on force with the board backed (panel coupon on a kitchen scale, N) and the
  pull-off force. The chosen rung seats by thumb and does not pull off by hand. Seat it on a 0.2 mm shim (2 strips of
  printer paper). The press-on force goes through the encoder shaft and its push switch, so it must stay below the
  shaft push strength in the encoder datasheet (MP-ENC records it; 30 N if no figure is found). A rung that needs
  more is too tight: take the next looser rung."
- **G-ENC-1** add: "Cradle pull-out along -Y on the panel coupon: push the shaft with the scale, board unbacked, until
  a hook lets go; record N in `PRESS_FITS['knob_exp']['release_N']`. Pass >= 25 N (5 x the 5 N push-switch bound;
  2.8 x the camera weight with the Kowa). Below 25 N the `handling` check fails and DESIGN-C5-B's `enc_stop` is built
  before the first assembly."
- **G-MP-ENC** add: "Record the push stroke s. The in-use load cap (the knob lands on the panel after gP 0.2 minus the
  0.1 play = 0.1 mm of shaft travel) needs s > 0.1; a shaft with less axial travel puts every push on the hooks, so
  then G-ENC-1 is repeated with the knob pushed by hand and must still pass 25 N. Commissioning the push
  (`ENCODER['push']['required_travel_mm']` set) fails `handling` until the back-stop is built. Record whether the board
  back is thumb-safe (no part a 30-50 N thumb must not press). If not, print a backing anvil that bears on the free
  board strips (fallback; not designed yet). If the shaft would stand more than 9.2 above the panel face, cut it with
  the encoder out of the cradle."
- **G-MP-SW**: replace "after the cut (y 42.0 +-0.3, deburred)" with "record P (dry-fit protrusion), the washer
  position (body side or nut side) and its thickness, and the length cut; the cut is made off the panel; final
  6.7-7.1 above the face, deburred. The knob nut recess clears nut + washer by >= 0.25 (CAD: recess roof y 38.45,
  nut top 37.4, bushing end 38.2: 1.05 and 0.25). A nut-side washer thicker than 0.8 needs a deeper `knob_fps` recess
  (knob reprint only)."

### 5.3 guide/guide_steps.py

- Page `2`: `new` += `'knob_exp', 'knob_fps'`; `parts` += "2 knobs (printed)"; `tools` += caliper, vise with soft
  jaws, 2 paper strips; `do` = 5 lines (measure P with the switch dry-fitted; cut P - 6.9 off the panel in soft
  jaws; refit the switch; snap the encoder; thumb behind the board, press each knob onto the paper); `check` += "knobs
  0.2 off the panel (paper drags)", "switch shaft 6.7-7.1 above the face".
- Page `8b`: the knobs are drawn on the panel (they move with it): add them to that page's moving parts.
- Page `8c`: `do` = the hood-down pose and the block (view: camera inverted, block drawn on the left side).
- Page `9`: `new` and `offsets` drop both knobs; `parts` drops "2 knobs"; `do` drops "Push the two knobs onto their D
  shafts."; title becomes "Eyecup, USB stick".
- Delete `ISSUES['9']`, `ISSUES['2']` (BX-5), `TIPS['2']` (BX-14) and `TIPS['8c']` (BX-13); move the eyepiece
  sentence of `TIPS['8c']` into the last step-6 page `do` list. New `TIPS['10']`: "Set the camera down on its base or
  its right side, never on its left side (the exposure knob)."

### 5.4 Other documents

- **printed_small.py** note: s3.3.
- **WIRING.md** s7: no change for this cluster. Note handed to the C2 implementer: "While plugging or unplugging the
  QT JST-SH at the encoder, back the encoder board with a fingertip, so the plug force does not go into the cradle
  hooks."
- **BOM.md / bom.csv / harness-schedule.csv**: no change.
- **HANDOFF.md**: BX-5, BX-13, BX-14 closed by r7 C5 (the `handling` rows are the evidence; the B contingency and its
  two triggers named). `guide/BLOCKERS-2026-10-08.md` stays as written.

## 6. Interactions and risks

| Check / area | Effect | Evidence |
|---|---|---|
| sweeps | `panel_on` moving set gains both knobs. | A p1: 0.0 mm3 against every static step-8 part (tub, hood, base_grip, pi_keeper, plunger, lens_collar, all COTS boxes incl. lens, strap, eyepiece, gs_camera). B `sweep.py` agrees. `stick_in`, `pack_in`, `cap_on` already list the knobs as obstacles. |
| removals, service_driver | none: `panel_off` already moves the knobs. | `removals` 12/12, `service_driver` 11/11 today. |
| driver | the step-8 audit sets gain both knobs. | A p1: bit gaps >= 50.61 mm, handle gaps >= 86.04 mm (s_b1, s_b2, s_r1, s_r2); B `drv8.py`: 0 mm3 incl. s_c4. 11/11 expected. |
| evf_restraint | none. The hood-down pose is used only once the panel is pushed home (its cap clamps the spigot). Steps 6-8 wording added (level or nose-down). | `evf_restraint` 6/6. |
| j7_float, lens_support | no geometry change. In the hood-down pose the lens thumb screws are tight and s_c4 is snug (step-8 order); the collar carries the lens, the camera still touches nothing. | `j7_float` is pose-independent geometry. |
| thin_wall, critical_features, print_overhang, bed_fit, stl_mesh, keepouts, cable_routes, mass_com, snap | none (no geometry change). | no STL hash may change; if one does, stop and find out why. |
| interference / mate_overlap | none. | knob mates unchanged. |
| C1 (BX-1, carried plugs) | independent. C1's carried-plug sweep of `panel_on` (p_qt_enc) is unaffected by two more rigid movers. | SPEC-C1 s4.1 |
| C2 (BX-2, QT lead, mating pose `qt_enc` 60 mm out) | knobs sit on the outer face, away from the hand envelope (C2 s6 says the same). Fingertip-backing note handed over (s5.4). No geometry here, so C2's `ko_qt_tail` (0.5 off the left hook) is untouched. | SPEC-C2 |
| C4 (BX-4, camera hold at step 8) | both edit the step-8 `action` string: C4 the lens part, C5 the last sentence. Merge by hand. | - |
| C6 (BX-6/12/17) | C6's "every `adds` id has an INSERTIONS entry or a reason" rule: the knobs now satisfy it through `panel_on`. C6's right-wall bar ends 2.0 clear of the s_r1 counterbore; the block is on the left side. | SPEC-C6 |
| tool numbering | the new paper-shim row takes the next free tool number at merge. | - |

Risks, stated plainly:
1. **The hooks remain the only -Y restraint.** Assembly no longer loads them. In use the knob land caps the load at
   the switch spring force, but only while the push is uncommissioned and the shaft has > 0.1 mm push travel. The
   release force is an estimate (22-95 N). Mitigation: G-ENC-1 >= 25 N and the `snap_basis` row; both failures send
   the build to the ready B contingency. Residual: a knock off the knob axis, or a drop, is not covered by any check.
2. **The thumb presses the board back.** Its parts are unmeasured (MP-ENC); the press force is unknown until
   G-KNOB-1. A thumb spreads tens of newtons over SMD parts and pushes the JST-SH sockets in their mating direction.
   Fallback: a printed backing anvil (G-MP-ENC), not yet designed. The press also passes through the encoder shaft
   and push switch (true for B as well); G-KNOB-1 caps it at the datasheet shaft push strength (30 N if unknown).
3. **A knob change costs a panel opening** (4 PT drives on the 5-drive tally, FASTENER-POLICY C). A pull-off alone
   does not. Knob changes should be rare.
4. **Rest poses depend on the user.** The check proves the written pose is safe; it cannot stop someone laying the
   camera on its left side. With the knob land this presses the push switch and loads the knurl, not the hooks.
5. **s_r2 is 52.5 mm above the bench in the hood-down pose**, above the 25 mm block. s_b1/s_b2 are driven first and
   hold the panel bottom; the other hand holds the grip against tipping.
6. **Tripod and USB rows** may need `held` instead of `rigid` if the proxies do not show a backing volume (s3.1). The
   implementer decides from the computed V_rigid; thresholds stay.
7. A full release rebuild is required (layout.py is a receipt source). No STL hash should change.

## 7. Acceptance criteria

Computed, after the full rebuild through `run_locked.py`:

| Check | Must hold |
|---|---|
| `handling` press_cover | 5 `press` mates, 5 rows, pass. |
| `handling` press_fit | `knob_exp`: `snap`, V_rigid 0.0 mm3, V_zone 1.44 mm3; bench step 2; carried by `panel_on` and `panel_off`; backing column 0.0 mm3. `knob_fps`: `rigid`, V_rigid 15.92 mm3. `tripod_nut`, `usb_stick`: pass as declared. |
| `handling` snap_basis | pass: push uncommissioned; `release_N` None; A_land 389 mm2 (>= 100), A_panel 389 mm2 (100 %, >= 0.9 A_land), gP 0.20 (<= 0.30). |
| `handling` rest_pose | `hood_down`: touching {hood} at z 100.0, next tub 97.3 (margin 2.7); stop slab clear of the knobs (4.0 to `knob_exp`) and the eyepiece (4.5 in x); bearing on panel and hood. `base_down_8` {base_grip}, margin 2.0; `base_down_10` {cap}, margin 6.0. `hood_down_s7`: touching {hood} (eyecup removed first). |
| `handling` rest_cover | s_b1, s_b2, s_r1, s_r2, s_c4 covered. |
| ASSEMBLY tables | step 8 "In the body after this step" 35 -> 37 ids; step 9 stays 40; step 2 bench list shows both knobs; `panel_on` motion lists 5 parts. |
| `sweeps` | 14/14, `panel_on` 0 mm3 with the knobs. |
| `driver`, `service_driver` | 11/11 each; knob gaps >= 50 mm (bit), >= 86 mm (handle). |
| everything else | all 28 existing categories pass with unchanged numbers; no STL hash changes. |
| tests | `test_r7_c5_handling.py` 16/16; existing tests unchanged (any that count step-8 ids are updated 35 -> 37, nothing else). |

Physical gates that later confirm it: G-KNOB-1 (press-on force with the board backed, pull-off force, 0.2 shim
seat); G-ENC-1 (cradle -Y pull-out >= 25 N, value written to `release_N`); G-MP-ENC (push stroke s > 0.1;
thumb-safe board back); G-MP-SW (P, washer side and thickness, off-panel cut, 6.7-7.1); G-PANEL-1 (panel openings,
unchanged).

## 8. User decisions

None. Decided here: no new part or screw now; knobs on at step 2; a knob change needs the panel off; the hood-down
pose with a household block; the B plate only if a gate or the push commissioning trips the check. A later decision
to commission the encoder push will, by design, require the B plate (about +9.7 g, +2 PT screws); that is noted
for whoever makes that call, not asked now.

## 9. Effort and receipt sources

| Work | Hours |
|---|---|
| layout.py: STEPS 2/6/8/9, INSERTIONS, LATCH_FREE, PART_RATIONALE, PRESS_FITS, SNAP_TOOTH_ZONES, REST_POSES | 0.75 |
| checks.py `check_handling` (6 row kinds) + build_d2.py registration | 2.25 |
| test_r7_c5_handling.py (16 planted faults) | 1.25 |
| ASSEMBLY.md, MEASURED-PARTS.md, printed_small.py note, guide_steps.py, HANDOFF.md | 1.25 |
| full release rebuild through run_locked.py, guide rebuild, receipt review | 0.75 (plus machine time) |
| **Total** | **about 6.25** |

Receipt sources touched: `layout.py`, `checks.py`, `build_d2.py`, `printed_small.py` (note text only). layout.py
forces a full release rebuild. ASSEMBLY.md and DESIGN.md step tables regenerate through make_tables.py; the guide
rebuilds from guide_steps.py.

## Judging

Scores 1-5 (5 best), with my probe re-checks.

| Criterion | A (sequence) | B (plate) | Reason |
|---|---|---|---|
| 1. Removes the physical problem | 4 | 5 | Both remove the press load on the hooks (re-checked: only the 3 hook ends back the board; thumb column 0.0; B's plate path is positive). B also removes the in-use path, which today is already capped by the knob land (389 mm2 at gP 0.20, found in this review). |
| 2. Robust to unmeasured dimensions | 5 | 3 | A's thumb and paper shim conform to any board. B's pads need free PCB corners and the measured stack, plus a sand/tape fit to <= 0.10; its panel-face-up press block would have to be >= 49.2 mm tall (the panel posts reach y -30.4), which B did not state. |
| 3. User rules | 5 | 4 | Both keep straight-driver access, J7-R float and power last. A is the sequence fix the rules prefer; B adds 2 screws where the project has been reducing them. |
| 4. Blast radius | 5 | 2 | A: no geometry, no STL change, no BOM change. B: new part, panel posts, hook play change (panel reprint), 11 -> 13 screws, BOM, coupons, bench-step driver audit, tests that count screws. |
| 5. Assembly and service simplicity | 4 | 3 | A: one squeeze at step 2, one pose at step 8; a knob change needs the panel off. B: plate, 2 screws and a paper fit at step 2 (about 10 min), but a knob could be re-pressed in the body. |
| 6. Quality of the new check | 4 | 3 | A's computed retention class (snap vs rigid by displaced overlap) plus the bench and carry rules catch the BX-5 class generically, and the rest-pose rows catch BX-13. A's table missed the `pi5`/`usb_stick` press mate and its s7 pose rested on the eyecup: both fixed here. B's `encoder_restraint` is plate-specific; its `insertion_closure` duplicates C1. |
| **Total** | **27** | **20** | |

Synthesis: A wins. Added from B and from this review: the `snap_basis` tripwire (push commissioned, or G-ENC-1 below
25 N, forces B's plate), B's step 6-8 eyepiece wording, B's G-KNOB-1 sentences, the eyecup-off service rule, the
5th press row, the one-sided shaft tolerance (6.7-7.1, the knob bores are through) and the corrected in-use
load-cap reasoning.

## Plan edits (integration, 2026-10-09 00:00-01:00 MPST; PLAN.md wins where it and this spec differ)

Plan edits: P5-1 Step 8 action: SPEC-C2 (panel 60 mm off, QT pinch, PH junction, spare fold at 30 mm, "keep the
body upright until the panel is fully home") and SPEC-C4 (lens sentences) edit the same string. The merged text
is PLAN.md s4; C5 owns the last sentences (hood-down pose, block, s_b1/s_b2 then s_r1/s_r2, never the left side).
The hood-down pose is safe for the C2 fold: once the panel is home the fold is closed in by the panel face, as in
use (SPEC-C2 P2-3).
Plan edits: P5-2 Tool numbers (PLAN.md X-9): the paper-shim row is tool 16 (15 = C1 pliers, 17 = optional
mirror, 18 = C4 fold card). Tool row 7 gains the caliper and soft-jaw vise as written.
Plan edits: P5-3 SPEC-C6's insertion coverage row: once C5 lands, knob_exp and knob_fps have an INSERTIONS entry
(`panel_on`), so they must NOT be in `INSERTION_EXEMPT` (C6 P6-3). The fingertip-backing note goes into the merged
step-8 QT sentence.
Plan edits: P5-4 `handling` registers with `info_neutral=True` (info rows). Do not run make_tables in the code step;
the release sequence regenerates ASSEMBLY/DESIGN tables. If the tripod_nut / usb_stick rows need 'held', decide
from the computed V_rigid (no threshold change).
Plan edits: P5-5 Spec gap: PRESS_FITS `stick_sleeve` uses retention 'hand', which 3.2 does not define. Define it
narrowly. 'hand' is a press of two loose parts held in the hands at the bench: `where='bench'`, neither part is in
the body at that moment, neither is a snap target, and no volume test applies. Any other use of 'hand' fails the
row. This adds a class without loosening the rigid/snap/held thresholds.
