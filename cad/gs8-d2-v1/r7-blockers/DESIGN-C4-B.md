# DESIGN-C4-B: hold the camera through metal while the lens is threaded (BX-4, BX-8, BX-15)

Status: design spec, angle B (geometry / sequence), 2026-10-08 22:45-23:55 MPST. One of two independent designs for
cluster C4. Nothing in the repo was changed except this file. Probes: session scratchpad `r7/C4B/` (`zone.py`,
`roll.py`, `roll2b.py`, `roll3.py`; outputs `roll_1p2.txt`, `roll2c.txt`, `roll3.txt`). Geometry: `layout.py` imported, r6 part STEPs in
`out/step/parts/` (assembly pose), camera rebuilt from `cots.gs_camera_parts` code with metal and PCB/cover split.

**Short version.** Delete the hood roll fin (it catches the camera COVER). Add a **tab catch**: two printed tines
hanging from the hood band, one each side of the camera's split lock tab (aluminium, part of the housing), 1.2 mm
off the lock-screw head envelopes. Any thread torque now rolls the camera 3.2 deg and lands a metal tab/head face on
a tine. The PCB and cover touch no printed part up to 14 deg and no COTS box before 13.0 deg (cooler). No hand holds the camera at step 8, at s7 item 6a or at the
panel-on lens swap. One hand carries and turns the lens. Axial only: at step 8 one fingertip pushes the cover centre forward onto the lip catch; at the panel-on swap the body is tipped nose-down.
BX-15: a thumb stem on the centring gauge. BX-8: bench pre-crease of the FPC accordion plus a fold-budget check.

## 1. Problem restated (re-checked in the current code)

| quantity | BLOCKERS value | re-check (source) | verdict |
|---|---|---|---|
| housing band | dia 35.5 x 10.35, x -17.2..-6.85 | `CAM['housing']`, `cam_hf_x()` = -6.85 at s_nom 1.25 (s 0: -15.95..-5.6; s 3: -18.95..-8.6) | correct |
| front wall inner face | x -5.2 | `X_FW_IN` | correct |
| PCB / cover proud of the band | 1.25 / 2.0 | `CAM['pcb']['sq']` 38, `CAM['cover']['sq']` 39.5 vs 35.5 | correct |
| room below the band | about 6 mm | housing bottom z 42.25 vs cooler top 36.3: 5.95 | correct |
| room above | about 19.5 mm | housing top z 77.75 vs hood band underside `ZT1` 97.3: 19.55 | correct |

New evidence found in this re-check (not in BLOCKERS):

- **The roll fin itself breaks B-7.** With no hand on the camera, thread torque rolls it until the cover's -Y
  corner meets the hood roll fin (`HOOD['roll_fin']`, 0.8 off the cover). Computed: contact at **2.34 deg** in both
  directions (s 0 and s 1.25). With the hood at its lateral extreme toward the fin (centring stack 0.30 +
  `HOOD_TO_TUB_LATERAL` 0.25 = 0.55), contact at **0.70 deg**. The reaction then passes cover -> PCB -> the compliant
  housing-to-PCB joint (2 M2, nylon washers, gasket): exactly what B-7 forbids. (`roll_1p2.txt`.)
- **The panel-on lens swap depends on that fin by design.** ASSEMBLY s7 "Lens swap" and `LATCH_FREE['lens']` say
  "the camera turns with it until its cover meets the hood roll fin". With the panel on no hand can reach the camera,
  so every panel-on lens swap reacts the torque through the cover. BX-4 is therefore wider than step 8.
- **The +-1.4 deg level window is text only.** No check computes it (`grep` of checks.py: no roll / window code).
- **Bench reorder is impossible.** The lens cannot pass the lip bore (dia 32.4) or the hood plate bore (36.5) from
  inside (lens envelope `COTS['lens']` y +-27). The cover (39.5 sq) cannot pass them from outside. The camera can
  enter only from inside, the lens only from outside. So "thread lens and camera together on the bench" is out.
- **The only non-round metal on the hanging unit is the split lock tab.** `CAM['tab']`: w 10.16 (y +-5.08), top r
  22.1 (z 82.1), depth 5.02 behind the housing front; lock-screw head envelope dia 4 x 2 at z 79.4 on both sides
  (y +-5.08..+-7.08), head side unconfirmed (MP-CAM). BFAR and adapter are plain rings; the tripod block is removed.

## 2. Chosen fix and why

**Hood tab catch, roll fin deleted.** Two printed tines hang from the hood band, one each side of the lock tab, and
the roll fin and its two webs go. The tab and the lock-screw heads are aluminium/steel and belong to the housing,
which carries the BFAR thread. Torque path when a lens is turned: lens -> C-CS adapter -> BFAR -> housing -> tab ->
tine -> hood -> tub -> collar -> lens. The compliant housing-to-PCB joint is outside this loop. The tines are
catches with gaps (like the lip and the keeper), so the J7-R float holds in the final pose.

Computed with the current geometry (tines as specified in s3, gap 1.2, z0 78.0; `roll_1p2.txt`, `roll2c.txt`; the z0 78.5 re-run in `roll3.txt` gives the same angles and window):

| case | metal (tab/head) meets a tine at | PCB/cover first contact |
|---|---|---|
| centred, s 0 / 1.25 / 3, either direction | 3.22 deg | no printed part to 14 deg (hood without fin, tub; panel checked at offsets 0 and -0.55); COTS cooler box at 13.01 deg, Pi 5 box 13.8 deg (probe roll3) |
| hood/camera offset 0.55 lateral (centring 0.30 + hood 0.25) | 1.72 / 4.73 deg | no printed part to 14 deg; cooler box about 11.8 deg with a 0.30 camera-to-stack offset in z (estimate, 0.26 mm/deg) |
| real part with the lock-screw head on ONE side only (envelope tines) | 3.22 deg head side, 8.44 deg bare side (6.96..9.94 with the 0.55 offset) | as above: the bare-side catch (<= 9.94 deg) still comes >= 1.9 deg before the cooler box |
| level window +-1.4 deg, centred | gap left 0.679 | - |
| level window +-1.4 deg, worst 0.55 offset | gap left 0.129 (>= J7_RUNNING 0.1) | - |

So the tab catch is the first contact in every case, before G-CAM-1 fixes the head side. After G-CAM-1 the bare-side
tine moves in (s3, `head_side`) and both directions catch at about 3.2 deg.

Torque and strength estimate (no measurement exists, so a deliberately high design torque):

| item | value |
|---|---|
| design torque | 0.5 N m (strong fingertip snug on a dia 40-54 lens; normal seating "until it stops" is about 0.05-0.2 N m, estimate) |
| contact force | F = 0.5 / 0.0174 = 28.7 N (smallest contact radius: tab face at the head base, r 17.4) |
| tine section | web 4.6 (x) x 3.0 (y) + rear flange 2.0 (x) x 12.0 (y): I = 476 mm4, Z = 62 mm3 |
| bending at the band root | arm 19.3 (z 78 -> 97.3): M = 554 N mm, sigma = 8.9 MPa across the layers (hood prints band-down, `face_down` +Z) |
| margin | ASA interlayer about 15-25 MPa (literature range, not measured): SF 1.7-2.8 at 0.5 N m, about 6-9 at 0.15 N m |
| tip deflection | 28.7 x 19.3^3 / (3 x 2000 x 476) = 0.07 mm (E 2 GPa assumed) |

Alternatives considered:

- Thread lens and camera together on the bench, then insert: impossible (s1, bore sizes).
- Move the roll catch to the BFAR or the adapter: both are plain rings; nothing to catch without a new tool.
- Keep the fin as a far backstop (gap >= 4): possible, but it adds nothing once the tab catch exists and keeps a
  cover contact in the model. Deleted instead; the cover meets no printed part to 14 deg and the cooler box at 13.0 deg.
- Hand-held "camera steady" fork (angle A): needs a tool and a hand, still bears only on the 10.35 band, and cannot
  work with the panel on. The tab catch works panel on or off with no tool.

## 3. Exact implementation

### 3.1 Tab catch (BX-4)

`layout.py`, `HOOD` dict: delete `roll_fin` and `roll_webs`. Add:

```python
tab_catch=dict(gap=1.2,              # r7 C4-B: lateral gap, tine face to the lock-screw head envelope (both sides)
               head_side='both',     # 'both' until G-CAM-1; then '+Y' or '-Y' (the bare side moves in, s below)
               bare_y=None,          # G-CAM-1: |y| of the bare side's outermost metal (tab face 5.08 or screw tip)
               t=3.0, x=(-14.5, -7.9), z0=78.5,      # web: 3.0 thick in y, x span, bottom z (top = ZT1 + 0.5)
               flange=dict(dx=2.0, dy=12.0),         # rear flange x -14.5..-12.5, outward 12.0 from the tine face
               lead_in=1.0, root_r=2.0),             # 1.0 x 45 chamfer on the rear inner vertical edge; band fillet
```

New function in layout.py beside `cam_hf_x`: `tab_catch_boxes(L=None) -> list[B]` returning the 4 boxes (web and
flange, +Y and -Y). Inner face |y| per side: `y_in = CAM['tab']['w']/2 + CAM['tab']['head_h'] + gap` = 8.28 on a
head side or for 'both'; on the bare side after G-CAM-1, `y_in = bare_y + gap`. Web: x -14.5..-7.9,
|y| y_in..y_in+3.0, z 78.5..97.8. Flange: x -14.5..-12.5, |y| y_in..y_in+12.0, z 78.5..97.8. The +Y web merges into
the existing roof rib (`printed_hood.RIB`, y 8.4..10.0, ends x -10.0).

Why these numbers (all from probes against the r6 geometry):

| limit | value | margin |
|---|---|---|
| tine front x -7.9 vs TL/TR insert-boss rear face x -7.6 (hood drops 60 mm along -Z at step 5) | `hood_on` sweep min 0.30 | equals the 0.3 rule used for the lip land; keep |
| tine rear x -14.5 vs BFAR head at the camera_in entry offset (x -16.7..-15.5) | 1.0 | |
| tine rear x -14.5 vs PCB front face at s 0 (x -15.95), final pose | 1.45 axial (J7 body axial 0.4) | 0.95 when the camera sits on its lip catch (lens out) |
| tine bottom z 78.5 vs adapter top during the 2 mm-high traverse (z 77.375) | camera_in sweep min 0.625 at z0 78.0; 1.00 at z0 78.5 (probe) | |
| tine x span vs tab/heads over s 0..3 and the axial play (lip 0.5 ahead, keeper 0.5..3.5 behind) | head overlap >= 1.7 mm in x in every state | tab never leaves the slot except by camera_out |
| tine flange vs panel material (y >= 26.15 in the tine band) | 5.9 | panel_on unaffected |
| keepouts and COTS boxes inside the tine envelope | none (only the gs_camera bounding box, already overlapped by the tub lip) | |

`printed_hood.py`: replace `_roll_fin(L)` by `_tab_catch(L)` (boxes from `L.tab_catch_boxes()`, rear inner vertical
edge chamfer `lead_in`, root fillet `root_r` to the band where the kernel allows; otherwise a 2 x 45 root chamfer).
Line 300: `adds += ... + _tab_catch(L)`. Docstring line 31: "the camera tab catch (2 tines) hangs from the band".
Print: band down (`face_down` +Z), the tines grow straight up: no overhang, no support.

`cots.py`, `gs_camera_parts(L, s=None, head_side='both')`: also return `'metal'` (housing + tab + heads) and
`'pcb_cover'` (PCB + cover). `'body'` stays their union, so `j7_float` and every existing caller are unchanged.
`head_side` '+Y' / '-Y' builds one head only (used by the new check while `HOOD['tab_catch']['head_side']` is
'both').

`layout.py`, other entries:

- `CAM['tab']`: add `tip_h=None` (screw tip protrusion on the non-head side) and `CAM['status']['tab']` = "drawing;
  lock-screw head side and tip protrusion unconfirmed: G-CAM-1 sets HOOD['tab_catch'] head_side / bare_y".
- New `ROLL_CATCH = dict(design_torque_Nm=0.5, window_deg=1.4, window_gap=0.3, scan_deg=14.0, step_deg=0.25,
  tol=0.01, margin_deg=1.0, tine_sigma_max_MPa=10.0, tine_defl_max=0.1)`.
- `CRITICAL_FEATURES`: replace `hood_cam_roll_fin` by `hood_tab_catch_p` and `hood_tab_catch_n`: part 'hood',
  origin (-11.2, +-9.78, 88.0), direction (0, 1, 0), min_mm 2.4, structural, note "r7 C4-B: camera tab catch (1.2
  off the lock-screw heads; contact only while a lens is turned)". The class rule at line 1778 becomes
  `(r'^hood_tab_catch_[pn]$', 'wing')`.
- J7 notes (lines 216, 1276, 1281) and the G-CAM-1 text (line 1837): "hood roll fin" -> "hood tab catch"; G-CAM-1
  adds "lock-screw head side, head height and tip protrusion; tab width and top radius".
- `HOOD_TO_TUB_LATERAL` comment (line 1910): the tab catch, not the roll fin, now carries it.
- `LATCH_FREE['lens']`: "r7: loosen s_c4 one turn (straight PH1 from above), unscrew the lens by hand: the camera
  turns with it about 3 deg until its metal lock tab meets the hood tab catch, which holds it".
- `STEPS` 7, 8, 10 text: see s5 (same wording as ASSEMBLY.md).
- `INSERTIONS camera_in`: unchanged path. Its obstacles already include 'hood', so the tines are swept.

No new purchased part, no BOM or harness row for the tab catch (it is hood material, +1.5 g, ASA).

### 3.2 Centring gauge thumb stem (BX-15)

`layout.py` `COLLAR['gauge']`: add `thumb=dict(roof_deg=45.0, stem_r=6.0, flare_x=44.0, disc_r=10.0,
disc_x=(48.0, 52.0), envelope=dict(r=10.0, length=25.0))`. `printed_collar.centring_gauge()`: the profile gets a
45 deg conical roof closing the bore at the grip front (r 10 -> 6), a stem r 6 to x 44, a 45 deg flare to r 10 at
x 48 and a disc r 10 to x 52 (prints rear-down: every step widens or narrows at 45 deg, no support). The thumb
pushes the disc along the axis; the stem is also the pull-out handle.

Clearance (driver envelope bit 6.5 x 40, handle 30 x 100 from x 43.3): s_c1/s_c2 axes are 32.42 from the lens axis,
handle edge 17.42, so the disc and a 20 mm thumb (r 10) keep 7.4. s_c3 (y 28, z 36): 36.88, handle edge 21.88,
clearance 11.9. The gauge face is no longer touched by the thumb.

### 3.3 FPC accordion (BX-8)

The camera traverse at x offset -11.1 sweeps through `ko_fpc_loop` (cover rear x -36.2 at s_nom, -37.94 at s 3,
vs loop x -42.5..-29.7; that is why `camera_in` ignores the loop). So the fold cannot be laid before the camera; it
has to collapse as the camera arrives. Decision: **bench pre-crease, collapse in place**, no geometry change now.

- At B0 (bench), crease the FPC as an accordion at fixed stations on a printed paper template generated by
  `make_tables.py` (new table "FPC crease stations": station i at `L1 + i * p` from the Pi end, `L1` = route
  length up to the loop entry, `p` = loop layer length + pi * r_min, r_min 1.0), mountain/valley alternating, then
  open it flat again. Kapton strip and the template go in the step 7 kit.
- Step 7: plug the camera outside the body (as now). Hold the creased slack loosely open across the left opening
  while the camera slides in -Y; the pre-set creases should fold up as the camera comes home (expected behaviour of
  a pre-creased accordion whose stacking axis is the slide axis y; nobody has tried it: confirm at the first
  assembly and record it under G-CAM-2). After the +X push, press the
  pack into `ko_fpc_loop` with the 120 mm tweezers and lay the Kapton strip across it. It must not touch the blower
  inlet.
- `CABLES` fpc: add `fold=dict(kind='accordion', loop='ko_fpc_loop', r_min=1.0, t=None, w=None, mated_at=
  ('camera_in', 0))`; `t` and `w` are the FPC thickness and width, MP gate G-FPC-1 (measure on receipt). Until
  then the check uses 0.15 and 16.0 as stated upper estimates and says so.

FPC fold budget with today's numbers (estimate, same box-centre method as `cable_routes`): width along z (19.4 >=
16), layers along x: straight 12.8 - 2 x (1.0 + 0.15) = 10.5, layer length with the bend 10.5 + pi x 1.0 = 13.6,
layers = ceil(119.1 / 13.6) = 9, stack along y = 8 x 2.15 + 0.15 = 17.35 against 17.5: **0.15 mm margin**. The fold
fits only just; BX-8 is real. Mating-pose reach (camera at the `camera_in` start, socket about (-36.2, 60, 45.8),
loop entry about (-42.5, 18.3, 38.0)): about 43 mm direct vs about 26 mm in the final pose, so only about 20-35 mm of
the 119 mm slack is needed. A shorter cable (s8, user decision) would cut the fold to about 6 layers (stack 10.9).

## 4. New computed checks and planted-fault regressions

### 4.1 `roll_catch` (new category, J7 family; 29th category)

`checks.check_roll_catch(L, rows, s_values=None, parts_of=None)`; registered in `build_d2.py` beside `j7_float`.
Rows (all must pass):

| row | method | pass criterion |
|---|---|---|
| `first_contact` per (s in `j7_s_values`, offset in {0, +-(centring_worst + HOOD_TO_TUB_LATERAL)} along y and along z, head variant in {'both'} plus {'+Y', '-Y'} while `head_side` == 'both', direction +-) | rotate `metal` and `pcb_cover` about the lens axis in `step_deg` steps to `scan_deg`, bisection to `tol`, against every final-state solid except `J7_FLOAT_EXCLUDE` (printed parts, COTS solids, screws), cropped as in `check_j7_float` | the first contact is metal with the hood tab catch; `pcb_cover` first contact (if any) >= metal angle + `margin_deg`; a missing tab catch or no metal contact within `scan_deg` is a FAIL |
| `window` per (s, offset, direction) | distance metal <-> hood at +-`window_deg` | >= `window_gap` 0.3 at offset 0; >= `J7_RUNNING` 0.1 at the worst offset |
| `tine_strength` (estimate row) | F = design torque / smallest contact radius (from the first-contact pose); cantilever from z0 to the band with the computed section of `tab_catch_boxes()` | sigma <= `tine_sigma_max_MPa` 10, deflection <= 0.1 mm |
| `axial_engagement` per s and axial state (lip contact, final, keeper contact) | x overlap of the head envelope with the tine span | >= 1.0 mm in every state |

Expected values today (probe): first contact 3.22 deg (1.72..9.94 over the variants), PCB/cover: no printed part to 14 deg, cooler box 13.0 deg (about 11.8 with a 0.30 offset),
window 0.679 / 0.129, sigma 8.9 MPa, deflection 0.07, axial overlap >= 1.7.

### 4.2 Driver audit with assembly tools and the thumb (BX-15 class)

`STEPS` entries get an optional `tools_present` list. Step 7: `['collar_gauge', 'thumb_gauge']`, where
`thumb_gauge` is a cylinder r 10 x 25 on the lens axis from the disc front (x 52). `checks.check_driver` adds
these solids to the audit set of the screws driven while the tool is in place (s_c1..s_c3). Pass: no hit, and the
row reports the nearest gap to the tool (today about 7.4 to the s_c1/s_c2 handles). This closes the gap noted in
C-1: tools held during a drive were never in the audit.

### 4.3 `cable_routes` extension: fold budget and mating-pose reach (BX-8 class)

For each cable with `fold`: layers, stack and margin as in s3.3; FAIL if the stack exceeds the loop width or the
FPC width exceeds the loop height; `info` row while `t`/`w` are estimates. For each cable with `mated_at`
(insertion id, waypoint): direct distance from the last fixed keep-out on its route to the moving connector at that
waypoint, plus the route up to that keep-out, plus the allowance, <= length. This is the generic "lead mated in a
pose other than the final one" check; C2/C3 (BX-2 QT lead, BX-3 XT30) need the same function, so it should be
written once and shared (coordinate with those designers).

### 4.4 Planted-fault regressions (`test_r7_c4.py`, style of `test_r3_regressions.py`, run via `run_locked.py`)

Each case builds a modified `layout` namespace (deep copy of `HOOD` / `CAM` / `COLLAR`) and asserts the failure
channel, plus one positive control on the unmodified layout.

| case | planted fault | expected |
|---|---|---|
| `test_roll_fin_back_fails` | re-add the r6 roll fin (gap 0.8) | `roll_catch` first_contact FAIL: pcb_cover meets hood at 2.34 deg before metal |
| `test_no_tab_catch_fails` | `tab_catch` removed | first_contact FAIL "no metal catch within 14 deg" |
| `test_tight_gap_fails_window` | gap 0.5 | window FAIL (about 0.5 - 0.52 < 0.3) |
| `test_float_kept` | gap 0.4 | `j7_float` body lateral FAIL (0.4 < 0.5) |
| `test_tine_into_entry_path` | tine x0 -16.0 | `sweeps` camera_in FAIL (BFAR head at the entry offset) |
| `test_tine_low` | z0 76.5 | `sweeps` camera_in FAIL (adapter during the 2 mm-high traverse) |
| `test_bare_side_fin` | head_side 'both', fin at gap 2.0 re-added | first_contact FAIL on the bare-side variant (cover meets the fin at about 6.1 deg, before 8.44) |
| `test_gauge_thumb_on_rim` | `thumb_gauge` envelope moved to r 25 toward s_c3 | `driver` s_c3 FAIL |
| `test_fpc_stack_over` | `fold.r_min` 1.2 | `cable_routes` fpc fold FAIL (stack 20.6 > 17.5) |
| `test_mating_reach_short` | fpc length 90 | `cable_routes` fpc mated_at FAIL |
| positive control | none | all rows pass, first contact 3.22 deg |

## 5. Document changes (exact wording)

**ASSEMBLY.md** (and the same text in `layout.STEPS`, from which `make_tables.py` regenerates the tables):

- Lens rule row (s1, line 23), replace from "At step 8 (panel off) ..." to "... never becomes a wrench." with:
  "r7 (BX-4): nobody holds the camera. Thread torque turns it about 3 deg until its metal lock tab meets the hood tab
  catch (two tines, one each side of the tab), so the reaction goes housing -> tab -> hood and never through the
  cover or the PCB. Panel off (step 8): one fingertip on the centre of the cover keeps the camera forward on its lip
  catch (push only; never pinch or turn the cover). Panel on (lens swap): tip the body nose-down so the camera comes
  forward onto its lip catch. Turn the lens with fingertips only."
- Step 7, gauge sentence: "... hold it home with your thumb on the end disc of its stem (never on the gauge face)
  and tighten s_c1, s_c2, s_c3 ...; pull the gauge out by its stem." Camera sentence: "... then push it +X 11.1 until
  the adapter has passed the tub lip and the lock tab has gone in between the two tab-catch tines under the hood (if
  the tab stops on a tine end, roll the camera level and push again) ...". FPC sentence: "The FPC was creased at B0:
  hold the slack loosely open while the camera slides in; after the +X push press the folded pack into its loop with
  the tweezers and lay the Kapton strip across it, clear of the blower inlet."
- Step 8, first sentences: "Lens, panel still off: fit s_c4 loosely. One fingertip on the centre of the camera
  cover, through the open left side, presses the camera forward (+X) onto its lip catch (axial push only). Pass the
  lens through the collar and screw it into the adapter with fingertips: the camera turns with it until its lock tab
  meets the hood tab catch (about 3 deg), which holds it through metal. Never grip the cover or the PCB to stop it.
  Turn until the lens stops; no extra snug. Set iris and focus ..." and "... the camera now hangs on the lens (it
  touches neither the tub lip, the counterbore nor the tab-catch tines) ...".
- s3 check 8: "... look down between the two tab-catch tines: a gap each side of the lock tab; the camera touches
  neither the tub lip nor the counterbore."
- Step 10: "(window +-1.4 deg: the lock-screw heads keep >= 0.3 off the tab-catch tines)".
- s7 "Lens swap" paragraph: replace "the hood roll fin beside the cover ... after 5 swaps." with "the hood tab catch
  either side of its lock tab. Loosen s_c4 one turn (straight PH1 from above). Tip the body nose-down. Carry the lens
  with one hand and unscrew it with fingertips only: the camera turns with it about 3 deg until its lock tab meets
  the tab catch, which holds it through the metal housing. A stuck thread: stop; never more than fingertip torque.
  G-CAM-2 checks the tab and the tines after 5 swaps." Item 6a: "lens off as in the lens swap (the tab catch holds
  the camera; no hand on the camera)."
- B0: add "paint mark across BFAR and housing as well as across adapter and BFAR; check both marks at every lens
  change" (the tab catch reacts torque through the BFAR thread, as any hold on the housing would). And: "crease the
  FPC on the crease template (accordion, r >= 1, stations from the template); open it flat again."

**WIRING.md** s7 and `harness-schedule.csv` (fpc routing note): "accordion pre-creased at B0 on the crease
template; collapses as the camera slides in at step 7; pressed into ko_fpc_loop and held by one Kapton strip".

**BOM.md / bom.csv**: no new row (tines are hood material; the template is printed on paper; Kapton is already in
the kit). If the user picks the shorter FPC (s8), change the fpc name and length in `CABLES`, `bom.csv` and the
harness schedule, then re-run `make_bom.py`.

**MEASURED-PARTS.md**: G-CAM-1 adds "lock-screw head side, head dia and height, tip protrusion on the other side,
tab width and top radius; set `HOOD['tab_catch']` head_side / bare_y and rebuild; roll_catch and j7_float must
pass again". G-CAM-2 adds "lens off: roll the camera by hand both ways; the tab meets a tine at about 3 deg and the
cover touches nothing. Lens on and seated: a 0.5 mm feeler passes between each tine and the tab/heads. After 5
swaps: no whitening at the tine roots". New G-FPC-1: "FPC width and thickness on receipt (fold budget)".

**guide/guide_steps.py**: delete `ISSUES['8a']` (BX-4) and the TIPS entries for '7a' (BX-15) and '7b' (BX-8) once
the CAD lands; the step texts above replace them. Page 8a caption: "one fingertip on the cover centre, push forward;
turn the lens; the camera stops on the tab catch". Page 7a: "thumb on the stem disc". Re-render the hood and gauge
views. Append a status line to BLOCKERS-2026-10-08.md: BX-4, BX-8, BX-15 fixed in CAD (r7); keep the table.

## 6. Interactions and risks

| area | effect |
|---|---|
| j7_float | tines are new hood obstacles: body lateral 1.2 (rule 0.5), axial 1.45 to the PCB at s 0 (rule 0.4); centring remaining 1.2 - 0.30 - 0.25 = 0.65 (rule 0.1). The fin row goes. |
| sweeps | camera_in min 1.00 (probe, z0 78.5; 0.625 at z0 78.0); hood_on 0.30 to the TL/TR insert bosses; camera_out mirrors camera_in; panel_on 5.9 away. |
| driver, service_driver | no screw axis passes the tines; s_c1/s_c2 tips end at x >= -7.0 (M3 x 10 + 0.29), 0.9 ahead of the tine front x -7.9. |
| critical_features, thin walls | 2 rows replace 1; tines 3.0 thick (rule 2.4). |
| print_overhang | hood band-down: tines and flanges vertical, chamfers on vertical edges: no new overhang. Gauge stem: 45 deg roof and flare. |
| keepouts, cable_routes | no keep-out inside the tines; the FPC runs behind the camera (x <= -24). |
| evf_restraint, inserts, lens_support | unaffected (far from the tines). |
| mass_com | fin and webs out (about 665 mm3), tines in (about 1420 mm3): hood +0.7 g. |
| BFAR thread | the reaction passes the BFAR fine thread pinched by the lock screw, as any hold on the housing would. Mitigation: BFAR/housing paint mark; never loosen the lock screw in the body. |
| unknown lock-screw head | a larger real head shrinks the 1.2 gap; G-CAM-1 measures it before the hood is printed. Until then the bare side catches late (up to 9.9 deg) but still before any PCB/cover contact. |
| other clusters | printed_hood.py and layout.HOOD are also touched by the BX-6 (plunger) and BX-17 (hood release) fixes: merge by hand. The mating-pose reach function (s4.3) is wanted by C2 (BX-2) and C3 (BX-3): write it once. |
| weaknesses of this angle | relies on the tab being where the drawing puts it; tine strength across layers is an estimate (SF 1.7 at 0.5 N m); the fingertip axial push at step 8 still touches the cover (axial only, friction torque about 0.02 N m, estimate); the FPC fold keeps a 0.15 margin unless a shorter cable is bought. |

## 7. Acceptance criteria

Computed, after the full release rebuild (29 categories, 0 fail):

- roll_catch: first contact metal <-> tab catch in every row, 3.2 +- 0.1 deg centred (1.7..10 deg over the offset
  and head variants); PCB/cover first contact >= metal angle + 1.0 deg in every row (expect >= 1.9); window >= 0.3 centred (expect
  0.68) and >= 0.1 at the worst offset (expect 0.13); sigma <= 10 MPa (expect 8.9); axial overlap >= 1.0.
- j7_float: all rows pass; tine lateral >= 0.5 (1.2), axial >= 0.4 (1.45); centring remaining >= 0.1 (0.65).
- sweeps: camera_in, camera_out, hood_on, panel_on pass; camera_in min distance to the tines >= 0.9 (probe 1.00).
- driver: 11/11 plus the gauge and thumb in the step-7 set, no hit, nearest >= 5 (expect 7.4).
- cable_routes: fpc fold margin >= 0 (0.15 today) and mating-pose reach slack >= 0.
- Every regression in s4.4 fails as stated against its planted fault and passes on the real layout.

Physical gates: G-CAM-1 (head side and size, before the hood is printed), G-CAM-2 on the first assembly (roll check,
feeler, 5-swap root check), G-FPC-1 on receipt.

## 8. User decisions

1. FPC length (optional purchase). Keep the 200 mm Standard-Mini (fold stack 17.35 in 17.5: works, 0.15 margin)
   or buy a 150 mm 22-to-15 cable if one can be sourced (about 6 layers, stack about 10.9, mating reach still met).
   Availability and price are not checked here. Default if no answer: keep 200 mm.

Everything else is decided above.

## 9. Effort and receipt sources

| work | hours |
|---|---|
| layout.py (HOOD tab_catch, tab_catch_boxes, CAM tab status, ROLL_CATCH, CRITICAL_FEATURES, STEPS, LATCH_FREE, COLLAR gauge thumb, CABLES fold) | 1.0 |
| printed_hood.py (_tab_catch), cots.py (metal / pcb_cover split, head_side) | 0.8 |
| printed_collar.py (gauge stem) | 0.5 |
| checks.py (check_roll_catch, driver tools_present, fold and mating-reach rows), build_d2.py registration | 2.5 |
| make_tables.py (crease-station table, regenerated steps) | 0.5 |
| test_r7_c4.py (10 planted faults + control) | 1.5 |
| docs (ASSEMBLY, WIRING, harness CSV, MEASURED-PARTS, guide_steps, BLOCKERS status) | 1.5 |
| full release rebuild via run_locked.py, verify, receipt | 1.5 |
| total | about 9.8 |

Receipt sources touched: layout.py, printed_hood.py, printed_collar.py, cots.py, checks.py, build_d2.py,
make_tables.py. A full release rebuild is required (hood STL/STEP, gauge tool STL, all tables and checks).
