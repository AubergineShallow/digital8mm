# r7 design C4-A: the camera key (BX-4, with BX-8 and BX-15)

Status: design spec, 2026-10-08 23:00 MPST. Designer C4, angle A (tool-based). Nothing in the repo is changed by this
file. Probes: session scratchpad `r7/C4A/` (`key1.py`, `key2.py`, `key3.py`, `hoodmap.py` and the JSON/log files).
They run on the r6 geometry (`layout.py` imported, assembly-pose STEPs in `out/step/parts/`, COTS boxes, the
`cots.gs_camera_parts` camera at s = 0, 1.25 and 3.0). Nothing was printed, bought or measured.

## 1. Problem, re-checked against the current code

The lens must be threaded into the C-CS adapter (step 8, s7 6a, the panel-on lens swap). The thread reaction must go
through metal, never through the compliant housing-to-PCB joint (audit B-7; lens rule in ASSEMBLY.md s1).

| BLOCKERS number | re-check (r6 code) | verdict |
|---|---|---|
| housing dia 35.5 x 10.35, x -17.2..-6.85 | `CAM['housing']`, `cam_hf_x()` = -6.85 at s 1.25 | correct |
| front wall x -5.2 | `X_FW_IN` -5.2. The BFAR head (x -5.6..-4.4) sits in the counterbore; only 1.25 mm of BFAR thread (dia 28.8) is exposed | correct; no grip on the BFAR |
| PCB / cover 1.25 / 2.0 proud | half-widths 19.0 / 19.75 vs housing r 17.75 | correct |
| ~6 mm below to the cooler | housing bottom z 42.25, cooler top z 36.3: 5.95 | correct. Also: `rib_l` (z <= 41) and the LL insert boss (z 32..40) block any tool path under the housing from the left at y 24..32 |
| ~19.5 mm to the hood roof | 97.3 - 77.75 = 19.55 to the housing top. **Missing in BLOCKERS:** the split lock tab rises to z 82.1, with lock-screw head envelopes (dia 4 x 2, both sides, z 77.4..81.4). Above it the hood hook hk3 (x -7.85..-5.6, y 18..26) reaches down to z 86.8, the TL/TR collar insert bosses (x -7.6..-5.2) to z 86.5, and the hood rail block that takes the panel tongue (`HOOD_RAIL`, x <= -11.5, y 23.9..32) to z 90.0 (`hoodmap.py`) | the free height over the tab is 4.4 mm at the front, 7.9 mm behind x -11.5 |

Two more findings:

- **The only positive metal feature is the lock tab.** It is part of the aluminium housing (x hf-5.02..hf, y +-5.08),
  and the lock-screw heads sit on its +-Y faces. The housing band itself is a plain cylinder: holding it by friction
  needs about 34 N of clamp (T 0.3 N m, mu 0.5, r 17.75), and fingers there also touch the PCB/cover edge.
- **The panel-on lens swap breaks the lens rule as written.** ASSEMBLY.md s7 "Lens swap" lets the camera turn
  "until its cover meets the roll fin, which then holds it". That reacts the thread through the cover and the
  housing-to-PCB joint. The text admits this ("never forced"), but the user rule says never.

## 2. Chosen fix and why

**A printed camera key (tool 15) on the lock tab.** It is a U-fork. Its two jaws straddle the tab and the
lock-screw heads in Y with 0.3 mm per side, and a rear pad sits 0.3 mm behind the tab's rear face. An arm runs +Y out
of the open left side to a handle. The key is lowered over the tab from the open left side: in raised by 5.5 mm, then
down. When the lens turns, the camera rotates at most 0.85 deg (computed) before a jaw meets a screw head. From there the
reaction path is lens -> adapter -> BFAR (locked) -> housing -> tab/head -> key -> hand. The PCB and the cover are
never in the path: the key keeps 2.03 mm from the PCB at every s, and the cover keeps 0.51 mm from the roll fin.
Pushing the handle +X presses the tab, and with it the camera, onto the lip catch while the thread starts. The body
must stay upright (vise on the grip, or held from above). On its right side the cover would rest on the roll fin
(3.1), and the fin would take the first roll.

**The panel-on lens swap is withdrawn.** Every lens off or on is done with the panel off (s7 items 1-4), using the
key. With the panel on, no tool can reach the camera: the panel closes the left side, the collar and lens fill the
front, and the hood roof is solid. Cost: one PT drive on each of the 4 panel bosses per lens change (5-drive tally).
In practice this costs little. A change to a different lens already needs the panel off, because that lens has its
own collar (s7 6a-6c). Only removing and refitting the same lens loses the panel-on option.

Alternatives considered:
- *Finger wording only* (BLOCKERS interim): no positive grip, and the PCB edge is loaded; not physically assured.
- *Friction C-clamp on the 10.35 band from the left*: the lower jaw cannot pass `rib_l` / the LL boss at y 24..32
  under z 41. It needs about 34 N of clamp on a 10 mm band next to the PCB.
- *Roof port in the hood plus a vertical key* (would also serve the panel-on swap): a hood geometry change. The port
  must pass the 22.8 mm jaw span. It meets the hood rib at y 8.4..10 (z >= 94.3), at x <= -10, and needs a plug. Not designed;
  offered as a user decision (section 8).
- *A grip on the BFAR or the adapter*: they sit inside the counterbore, the lip and the hood plate. They cannot be
  reached from inside the body.

**BX-8 (FPC S-fold): partial bench pre-fold.** Fold the Pi end of the slack (5 layers) on the bench with a printed
fold card, and tape it. Fold only the camera-end tail (about 3-4 layers) in place, on top of that flat pack.
**BX-15 (thumb on the gauge): a thumb dimple** on the gauge face in the lower-right quadrant. No collar screw is
there, so one thumb position serves s_c1, s_c2 and s_c3, and the computed check proves it.

## 3. Implementation

### 3.1 The camera key (tool 15): geometry

It is a flat printed plate, 6.82 mm thick in X. It prints on its -X face with no supports. All x values are relative to
the housing front `hf = cam_hf_x(s)`, so the key fits the camera at every s. The y and z values are absolute (lens axis
y 0, z 60).

| feature | x | y | z | purpose |
|---|---|---|---|---|
| plate (whole key) | hf-8.32 .. hf-1.5 | -11.38 .. 100 | 77.2 .. 84.0 (handle 72 .. 88) | one flat print |
| tab notch, open to -Z and +X | hf-5.32 .. front | -7.38 .. +7.38 | below 82.6 (roof 82.6..84.0, 1.4 thick) | tab plus head envelopes inside, 0.3 per side, 0.5 over the tab top |
| jaws (the notch cheeks) | hf-5.32 .. hf-1.5 | +-7.38 .. +-11.38 (4.0 thick) | 77.2 .. 84.0 | bear on the screw-head end faces (y +-7.08), contact z 77.4..81.4 |
| rear pad (behind the notch) | hf-8.32 .. hf-5.32 | -11.38 .. +11.38 | 78.25 .. 84.0 | 0.3 behind the tab rear face (hf-5.02); +X push. 0.5 over the housing top, 2.03 in front of the PCB |
| arm | as plate | 11.38 .. 40 | 77.2 .. 84.0 | out of the left opening (y 32.2) |
| handle (T-bar) | as plate | 40 .. 52 | 58 .. 96 | outside the body outline (y 35) by 5 mm; finger hooks on both Y faces |

Mass about 8 g (ASA, 100 %, 4 perimeters). The probe used a straight handle (y 40..100, z 72..88). The T-bar lies
wholly at y >= 40, where nothing is present with the panel off, so the probe result holds.

**Body orientation and hands (computed reason).** The body stays upright (gravity -Z). **Never lay it on its right
side**: the camera would then sag -Y onto the hood roll fin (0.8 gap; the counterbore allows 0.75 at the front). The
cover would rest flat on the fin, and the fin would take the first roll with zero backlash, before the key's 0.3 mm
clearance closes. Upright, the camera sags only -Z in the counterbore, and the cover keeps its Y gap to the fin.
- Preferred: hold the grip lightly in a soft-jawed bench vise. One hand holds the key T-bar and the other turns the lens.
- Without a vise: hold the body with the left hand from above, palm on the hood. The fingers come over the left edge
  and hook round the T-bar just outside the opening. The right hand turns the lens. The roll reaction goes key ->
  fingers -> palm -> body, and never through the camera cover or PCB.
The hand pushes or pulls the T-bar along Y (that is how the roll reaction arrives) and presses it +X for the lip catch.

**Insertion path** (relative to seated; `CAM_KEY['path']`): (dx0, +60, +5.5) -> (dx0, 0, +5.5) -> (dx0, 0, 0) ->
(0, 0, 0), with `dx0 = min(0, -8.15 - (hf - 1.5))`. That is -1.05 at s 0 and 0 at s >= 1.25. In transit the key's
front stays at x <= -8.15 (hk3 x0 -7.85 minus 0.3). Its top stays at z <= 89.5 (the panel-groove block at 90.0 minus
0.5), and its bottom at 82.7, over the tab top 82.1 and the head tops 81.4. Then it goes down over the tab and slides
+X until the pad touches the tab.

**Computed (`key3.py`, 2 mm steps, jaws 4.0):**

| s | dx0 | path hits (tub, hood, lens_collar, lens rear, camera, BFAR, 13 COTS boxes present at step 7) | seated gap: camera / tub / hood / collar / lens rear |
|---|---|---|---|
| 0.0 | -1.05 | none | 0.30 / 1.90 / 2.80 / 5.16 / 6.10 |
| 1.25 | 0 | none | 0.30 / 2.61 / 2.84 / 6.26 / 6.42 |
| 3.0 | 0 | none | 0.30 / 3.54 / 3.59 / 7.88 / 7.23 |

The probe solid had no notch roof. The roof lies inside the jaws' (x, z) envelope and inside their Y sweep, so it adds
no hit. The implementation check re-runs this on the real solid.

**Roll stop before the fin.** Computed by `roll.py`: the camera solid is rotated about the lens axis in 0.05 deg
steps against the key solid and the `HOOD['roll_fin']` box, at s_nom. The key is met at +-0.85 deg, and there the
cover is still 0.51 mm from the fin. The cover comes within 0.3 mm of the fin only at +-1.50 deg. The key-to-board
(PCB + cover) gap stays 2.03 throughout. Analytic cross-check: the jaw meets the outer head corner at 0.81 deg, and the
cover meets the fin at 2.37 deg. So the key always stops the camera first, and only metal (head or tab) is touched. The
PCB and the cover keep 2.03 mm from the key at every s. If a head is missing on one side (real head side
unconfirmed, `CAM['status']['tab']`), the jaw on that side would bear on the tab face after 6.05 deg. The cover would
reach the fin first. That is why the jaw gap is set from MP-CAM (3.2) before the key is printed.

**Torque capacity** (design torque `T_design` 0.5 N m, against about 0.1-0.3 N m of fingertip torque on a dia 42 knurl,
5-15 N at r 21):

| quantity | value | limit |
|---|---|---|
| hand force along Y, F = T / r_c, r_c 19.4 (head centre z 79.4) | 25.8 N (15.5 N at 0.3 N m) | <= 40 N (`F_hand_max`; a pencil-grip push) |
| jaw bearing on a dia 4 head, about 9.7 mm2 | 2.6 MPa | <= 5 MPa (ASA, printed) |
| jaw bending, 4.0 x 6.8 section, 2.8 lever | 4.0 MPa | <= 8 MPa (in-plane layers) |
| arm buckling, 6.82 x 6.8, cantilever L 40 | Pcr 550 N | >= 10 F |
| side load on the lock tab / head | 25.8 N along the screw axis, into the tab | metal; no load on the PCB joint |

### 3.2 Layout entries (`layout.py`)

- New dict after `COLLAR` (r7 C4):
  `CAM_KEY = dict(clear=0.3, jaw_t=4.0, x_rel=(-8.32, -1.5), notch_x0_rel=-5.32, z=(77.2, 84.0), pad_z0=78.25,
  roof_over_tab=0.5, arm_y1=40.0, handle=dict(y=(40.0, 52.0), z=(58.0, 96.0)), raise_dz=5.5, path_y=60.0,
  T_design=0.5, F_hand_max=40.0, bearing_max=5.0, body_gravity='-Z', stl='stl/tools/camera_key.stl', face_down='-X',
  status='jaw gap from the drawing envelope until MP-CAM (G-KEY-1)')`. The code derives
  `transit_front_max` (-8.15) and `transit_top_max` (89.5) from the hk3 and groove boxes minus 0.3 / 0.5. They are
  never typed as numbers. Sources: hk3 from `HOOD_HOOKS` (front wall, y 22, x_face `X_FW_IN`, w 8, t 1.6, built
  x -7.85..-5.6, y 18..26, z 86.8..97.3), and the rail block from `HOOD_RAIL['box']` (x -134.5..-11.5, y 23.9..32,
  z0 90.0). The TL/TR insert bosses (`TUB_INSERT_BOSSES`, x -7.6..-5.2, z 86.5..94.5) give the same front limit.
- `CAM['tab']` gains `over_heads=dict(plus=None, minus=None)`: the measured outermost metal face on each side (head end
  face, or the tab face if there is no head), from the tab mid-plane. With None, the code uses the drawing envelope
  w/2 + head_h = 7.08. The jaw inner faces are `over_heads + CAM_KEY['clear']`, per side.
- `INSERTIONS` `lens_in` gains `hold=dict(tool='camera_key', state='panel off')`. A new
  `REMOVALS += [dict(id='lens_off', moving=['lens'], reverse_of='lens_in', off=['s_c4'], hold=dict(tool='camera_key'))]`
  makes s7 6a a computed record. Today no REMOVALS record moves the lens. The `removals` sweep then covers the lens
  coming out with the panel off.
- `STEPS` step 7 `tool` += ', FPC fold card (tool 16)'. Step 8 `tool` = 'camera key (tool 15); PH1 torque screwdriver
  (tool 13)'. Action texts: section 5.
- `SERVICE_DRIVER` `lens_swap_closed_body`: keep the id (s_c4 is still loosened in the closed body for the step 10
  level check). Note -> 'step 10 level check: s_c4 loosened one turn from above with every part fitted (since r7 every
  lens change is made with the panel off)'.
- `COLLAR['gauge']` gains `thumb=dict(c=(-10.6, 49.4), d=16.0, depth=0.6, envelope_d=20.0, envelope_len=60.0)`
  (BX-15). The point is (y, z), on the face annulus r 10..20, at r 15, 45 deg into the lower-right quadrant.
- `CABLES` `fpc` gains `fold=dict(box='ko_fpc_loop', pitch=2.0, bend_r=1.0, t=0.15, panel=13.5, pre_layers=5,
  start_from_pi=30.0, work_allow=15.0, mate_pose=('camera_in', 0), margin=5.0)` (BX-8). `KEEPOUTS` is unchanged.
  The pack lies in the lower 10 mm of `ko_fpc_loop` (z 36.6..46.6), and the in-place layers above it.

### 3.3 Code

- `printed_tools.py` (new, receipt source): `camera_key(layout, s=None)` builds the plate above from `CAM_KEY` and
  `CAM['tab']`, at the s given (the default is s_nom). `fpc_fold_card(layout)` is a 2.0 x 13.5 x 45 plate (2.0 = 2 x
  bend_r). Both are assembly tools, not production parts, like `centring_gauge`.
- `printed_collar.centring_gauge`: cut the thumb dimple (dia 16, 0.6 deep, 0.3 chamfer) into the front face at
  `thumb['c']`, plus an engraved arrow. The gauge prints face-down -X, so the dimple is on the top face: no overhang.
- `cots.gs_camera_parts`: also return `metal` (housing + tab + heads) and `board` (PCB + cover) as separate solids.
  `body` stays their fuse, so nothing that uses it changes.
- `build_d2.py`: `export_tools(prow)` next to `export_gauge`. It writes `stl/tools/camera_key.stl` and
  `stl/tools/fpc_fold_card.stl`, runs `check_print_overhang` and `thin_wall` on both, and adds both to the manifest
  `tools` list. It calls `CK.check_camera_key`, `CK.check_lens_hold` and `CK.check_fpc_fold`. G-KEY-1 joins the gate
  map the way G-COL-1 does for the gauge.
- `make_bom.py` / `bom.csv`: two rows in "F. Tools and accessories": "Camera key, printed ASA (tool 15)" and "FPC fold
  card, printed ASA (tool 16)". Each costs 0 plus filament, with its `stl/tools/...` path. D2-48 already carries
  Kapton tape. No harness row changes: the FPC stays 200 mm.

### 3.4 BX-8: FPC fold numbers (estimates, `cable_routes` method)

| quantity | value | source |
|---|---|---|
| FPC length / route estimate / allowance / slack | 200 / 60.9 / 20 / 119.1 | `checks.json` `cable_routes` fpc |
| length to store in the loop (200 - 60.9) | about 139 mm | |
| loop box | 12.8 (x) x 17.5 (y) x 19.4 (z) | `ko_fpc_loop` |
| layer (panel 13.5 + bend pi x 1.0) at pitch 2.0 | 16.6 mm per layer, 9 layers max (18.0 <= 19.4) | 139 / 16.6 = 8.4 layers |
| Pi end to loop entry | about 29 mm, so the pack starts at about 30 mm (paint-pen mark) | box-centre polyline + half the up-box |
| bench pre-fold | 5 layers = 83 mm, pack 10 mm high, sits at z 36.6..46.6 | |
| reach at the step 7 plugging pose (`camera_in` waypoint 0) | loop +Y face to the camera socket 40.7 mm, plus 15 mm to work the latch, plus about 9 mm out of the pack = 64.5 mm needed; tail after the pack 200 - 30 - 83 = 87 mm | margin about 22 mm (rule >= 5) |
| folded in place after the camera is in | about 56 mm = 3-4 layers, on top of the taped pack, at y 2..19.5, 13-30 mm in from the opening | was 9 layers / 119 mm |
| pre_layers = 6 | tail 70 mm against 64.5 needed: margin 5.5 mm, too thin for an estimate | so 5 is the maximum |

The fold card (2.0 thick, 13.5 wide) sets the bend radius (1.0 = half the card) and the panel length.

Bench procedure (new text for step 4, before CAM1 is plugged): "Mark the FPC 30 mm from its Pi (22-pin) end. From the
mark, fold 5 layers zig-zag over the fold card, contacts outward on the first panel as the route needs. Slide the card
out, and hold the pack with one Kapton strip round its middle. Plug CAM1 and lay the pack flat in the loop space
behind the camera seat. The panels run across the body (Y), and the fold edges face the opening and the right wall."

## 4. New computed checks (no category added; the rows join existing categories)

| function (checks.py) | category / item | rows and pass criterion |
|---|---|---|
| `check_camera_key(L, rows, key_of, cam_parts_of)` | `lens_support` / `camera_key` | **seated** (s in `j7_s_values`): key and camera overlap <= VOL_TOL; key-to-metal gap = `clear` +-0.02; key-to-board (PCB + cover) gap >= 1.5 (2.03 computed). **roll_stop**: rotate the camera metal about the lens axis in 0.05 deg steps (manifold rotate) until it first meets the key (theta_k, each direction). Rotate the cover until its gap to `HOOD['roll_fin']` is 0.3 (theta_f). Pass if theta_k + 0.1 <= theta_f in both directions, and at theta_k the key-to-board gap is > 0 (only metal touched). Expected 0.85 deg against 1.50 deg (roll.py). Both angles are taken with the camera at its gravity rest for `body_gravity`: shifted by the counterbore clearance (0.75) in that direction, with the rear free to rest on whatever it meets. Upright (-Z) leaves the fin gap at 0.8. Right side down (-Y) closes it, and the row fails. **insertion**: sweep `CAM_KEY` path in 2 mm steps against tub, hood, lens_collar, every COTS solid present at step 7, the lens (for `lens_off`) and the camera (every waypoint but the last) <= SWEEP_TOL, at each s. **capacity**: F = T_design / r_c <= F_hand_max; bearing <= bearing_max; arm Pcr >= 10 F (analytic, inputs in the row). **print**: `check_print_overhang` (face_down -X) and `thin_wall` >= MIN_WALL (roof 1.4) on the exported STL pose. |
| `check_lens_hold(L, R)` | `lens_support` / `lens_hold` | Every INSERTIONS or REMOVALS record whose moving set holds `lens` carries `hold`. Its tool has a check whose rows all pass in R, its `state` ('panel off') matches the record's present set (the panel is not present), and the record's step text names the tool. This closes the defect class: a thread on the camera turned with a "hold" that nothing computes. |
| `check_collar_gauge` (extended) | `lens_support` / `centring_gauge` part `thumb` | Thumb envelope: a cylinder (dia `envelope_d` 20, length 60 along +X from the gauge front face at `thumb['c']`) against the driver bit and handle of each of s_c1..s_c3 <= VOL_TOL, min gap >= 10 mm. Expected gaps: bits 27.6-33.2 mm, handles 15.9-16.1 mm. |
| `check_fpc_fold(L)` | `cable_routes` / cable `fpc` item `fold` | (a) layers = ceil((length - est) / (panel + pi x bend_r)) <= floor(box z / pitch); (b) panel + 2 (bend_r + t) <= box y; (c) mate-pose reach: tail = length - start_from_pi - pre_layers x layer >= dist(box +Y face, end part at `mate_pose`) + work_allow + 9 + margin; (d) card thickness == 2 x bend_r. The end part's pose at `mate_pose` comes from the INSERTIONS waypoint, so any lead mated outside its final pose can declare `mate_pose` and be checked the same way (QT, BX-2, and XT30, BX-3, are other clusters; same field). |

Planted-fault regressions (new `test_r7_c4.py`, style of `test_r3_regressions.py`; each changes a copy of the layout
dict in memory and expects the named row to fail):

1. `CAM_KEY['clear']` 0.3 -> 1.5: roll_stop fails (theta_k about 4.1 deg > 1.40).
2. `CAM['tab']['over_heads']` minus -> 5.08 (no head on one side) with the key built from the drawing envelope:
   roll_stop fails (6.05 deg).
3. `CAM_KEY['z']` top 84.0 -> 90.0: insertion fails on the hood (HOOD_RAIL block, z 90) and hk3.
4. `CAM_KEY['x_rel']` shifted -3.0 (the pad on the PCB): seated board gap fails.
5. Delete `hold` from `lens_in`: `lens_hold` fails. Put the panel in the `lens_off` present set: `lens_hold` fails
   (state 'panel off').
6. Gauge `thumb['c']` -> (20.0, 80.0) (on the s_c1 line): thumb row fails.
7. `fold['pre_layers']` 5 -> 7: reach fails. `fold['pitch']` 2.0 -> 2.5: layer count fails (9 x 2.5 > 19.4).
8. `CAM_KEY['body_gravity']` '-Z' -> '-Y' (body on its right side): roll_stop fails (the cover rests on the fin).
9. Text lint: ASSEMBLY.md and `guide_steps.py` contain neither "roll fin, which then holds it" nor "finger and thumb
   through the open left side hold the camera".

## 5. Document changes (exact wording)

**layout STEPS step 8 action** (it generates the ASSEMBLY.md step block between `BEGIN:steps` and `END:steps`):
"Lens, panel still off: fit s_c4 loosely. Keep the body upright, with the grip in a soft-jawed vise or the body held
from above (never on its right side). Put the camera key (tool 15) in through the open left side, above the camera's
lock tab. Lower it over the tab, then move it forward until its pad touches the back of the tab. Its T-bar stays
outside the body. Its jaws sit either side of the tab and its two screw
heads, clear of the PCB and the cover. Pass the lens through the collar. Hold the key handle with one hand: press it
forward (toward the lens) and let it take the turn. Screw the lens into the adapter with the other hand, fingertip
torque only, until it stops. The key, not the cover, holds the camera against the turn. Lift the key out the way it
went in. Set iris and focus, and tighten the 2 thumb screws. Push the lens gently rearward until the knurl seats on
the collar cone. The camera now hangs on the lens (it touches neither the tub lip, the counterbore nor the fin).
Snug s_c4 straight down from above, 0.2 N m. Panel: ... (unchanged)."

**Step 7 action**, after "Fold the FPC slack into its loop": replace that sentence with "As the camera goes in, lay
the FPC tail (about 3-4 layers) zig-zag on top of the taped pack in the loop space, using the fold card as a paddle.
It must not touch the blower inlet." In the gauge sentence, replace "hold it home with a thumb" with "hold it home with
your thumb in the dimple on its face (lower right, the side with no collar screw)".

**Step 4 action**: add the bench pre-fold sentence from 3.4 before "plug CAM1".

**ASSEMBLY.md s1 lens rule row** (line 23), replace from "At step 8 (panel off) ..." to "... fingertips only, so the
roll fin never becomes a wrench." with: "Every lens off or on is done with the panel off and the camera key (tool 15)
on the lock tab. The key takes the turn through the metal housing, and the cover and the PCB stay out of the path
(computed: `lens_support` camera_key, `lens_hold`). There is no lens swap with the panel on."

**ASSEMBLY.md s1.1 tools table**: add "| 15 | Camera key, printed (`stl/tools/camera_key.stl`) (r7) | holds the camera
by its lock tab while the lens is screwed in or out (8; s7 6a) | D2-8x | - |" and "| 16 | FPC fold card, printed
(`stl/tools/fpc_fold_card.stl`) (r7) | pre-fold the camera FPC (4) and lay its tail (7) | D2-8y | - |".

**ASSEMBLY.md s3 checks**: row 7 add "FPC pack taped, tail layers flat, nothing on the blower inlet". Row 8 add
"key out of the body before the lens is pushed back onto the cone".

**ASSEMBLY.md s7 item 6a**, replace with: "a. Lens: loosen s_c4 one turn (straight PH1 from above). Body upright (vise
or held from above, step 8). Fit the camera key over the lock tab. Hold the key handle and unscrew the lens by hand. Lift
the lens out forward (+X 40), then lift the key out. The camera now rests in its cage. Check the adapter mark (B0 item
3). (CAD record `lens_off`.)" In "To close", replace "the lens through the collar with the camera held by its metal
mount" with "the lens through the collar with the camera key on the lock tab".

**ASSEMBLY.md "Lens swap" paragraph** (after s7 item 11), replace the whole paragraph with: "**Lens swap (r7).** A
lens is always changed with the panel off: pack out (item 1), panel off (items 3-5), then item 6a. The camera key
holds the camera, and the cover never meets the roll fin under thread torque. Fit the new lens as step 8. A lens with a
different band needs its own collar: items 6b-6c, then step 7 with that collar's centring gauge, then step 8. Back
focus: as before (check infinity on live view; if it is off, reset s with the camera out, B0). Each panel opening
uses one drive on each of the 4 panel bosses (tally, FASTENER-POLICY C)." Keep the G-CAM-2 line ("repeats its corner
check after 5 swaps").

**ASSEMBLY.md B0**: add "the camera is outside the body here: hold it round the housing, not by the cover".

**WIRING.md**: s7 row 4 ("FPC -> Pi CAM/DISP 1") note -> "pre-fold 5 layers 30 mm from the Pi end on the fold card,
Kapton strip; camera end loose". Row 7 note -> "lay the tail (3-4 layers) on the pack; `cable_routes` fpc fold row".
The harness-schedule `fpc` routing note gets the same two sentences.

**BOM.md / bom.csv**: the two tool rows (3.3). Regenerate with make_bom.py.

**MEASURED-PARTS.md, MP-CAM** gains: "tab over heads, +Y and -Y: the outermost metal face on each side of the lock tab
from the tab mid-plane (head end face, or the tab face if there is no head), and the head diameter. These set
`CAM['tab']['over_heads']`. The camera key is printed after this record." New physical gate **G-KEY-1** (after
MP-CAM, first print of the key): "With the camera in its cage (panel off), fit the key. Rock the camera by hand both
ways. The free roll at the tab top is <= 0.35 mm (feeler) each way. Then the cover does not touch the roll fin, and
the key does not touch the PCB or the cover. Thread the Kowa in and out 3 times with the key: the adapter mark does not
move."

**guide_steps.py**: delete ISSUES `'8a'` (BX-4). Add TIPS `'8a'`: "Camera key on the lock tab, handle in one hand,
pressed toward the lens. Turn the lens with fingertips only, until it stops. Lift the key out before you push the lens
back onto the cone." `'7a'` -> "BX-15 (fixed): thumb in the dimple on the gauge face, lower right. That spot is clear
of all three screwdriver lines." `'7b'` -> "BX-8 (fixed): the pack was folded on the bench at step 4. Lay only the
tail, 3-4 layers, on top of it as the camera goes in." The guide figure for 8a needs the key drawn (diagrams.py /
lineart.py: add `camera_key.stl` to the step-8 present set, as the gauge is drawn at step 7).

**BLOCKERS-2026-10-08.md**: leave it as the record. HANDOFF.md top gets a line for r7 C4.

## 6. Interactions and risks

| area | effect |
|---|---|
| production parts | **none changed.** Tub, hood, panel, collar, base and keeper keep their geometry. So thin walls, critical features, print_overhang, bosses, inserts, EVF restraint, keepouts, sweeps, removals, release access, mass and bed fit are untouched. The gauge gains a 0.6 mm dimple (tool only; its own overhang and thin-wall rows re-run). |
| j7_float | untouched: the key is out of the body before the lens goes back onto the cone. Planted fault 5 plus the step text make the order explicit. |
| driver audit | the key is not present when any screw is driven (fitted and removed inside step 8, before s_c4). The audit sets do not change. |
| cable_routes | gains the fpc `fold` row; the existing fpc row is unchanged. |
| COTS camera model | `gs_camera_parts` gains tagged sub-solids only; `body` is unchanged, so j7_float and interference see the same solid. |
| **real lock-tab geometry** (main risk) | the tab, head side and head height are drawing or unconfirmed. If a head is absent, the jaw on that side must be thickened by about 2 mm (set from MP-CAM). If the real tab is wider than the 14.16 envelope, the jaws move out: there is room to about y +-19 before the hood roll fin and webs at y <= -20.55. **The tightest numbers are vertical.** In transit the key clears the tab top by 0.6 and the HOOD_RAIL block by 0.5 (1.35 below in practice, because the camera sags 0.75 -Z in the counterbore when upright). A tab more than about 0.5 mm taller than drawn needs a thinner notch roof (1.4 -> 0.8 gains 0.6). MP-CAM measures the tab top radius. |
| lock-screw load | the key pushes the head 26 N along its own axis (at the 0.5 N m design torque). Assumption: the head does not slip in the split tab; it is clamped. If MP-CAM shows a set screw or a recessed head, the jaw bears on the tab faces instead (same gap rule). |
| reaction through the lens thread start | the key holds roll only. The camera still floats 0.75 mm in the counterbore; the lens rear cell centres the adapter as the thread starts (as today). |
| panel boss tally | lens changes are now panel-off: one drive per panel boss per change (5-drive tally, then the M3 insert fallback, FASTENER-POLICY D-E). Section 8. |
| vise use | a soft-jawed vise on the grip walls (2.5 mm ASA) must be light. The alternative is one-hand-from-above (section 3.1). Neither is computed. |
| BX-8 fold | the pack and tail rely on the `cable_routes` estimate (box-centre polyline). The real FPC route and its stiffness are MP-FPC. The 22 mm reach margin covers about +-15 mm of estimate error. |
| other clusters | C1 (BX-1, EVF rail and HDMI) and the QT/XT30 clusters (BX-2, BX-3) may add `mate_pose` reach rows; `check_fpc_fold`'s reach part should be the shared function. Nobody else touches `CAM`, the collar, the gauge or step 8's lens text. If another cluster rewrites step 8's panel text (BX-2 QT), merge at the text level only. |

## 7. Acceptance criteria

Computed (after implementation, full release build):
- `lens_support` camera_key rows pass at s 0, s_nom and 3.0. Insertion hits <= SWEEP_TOL against every obstacle
  (probe: none). Seated key-to-metal gap 0.30, key-to-board >= 1.5 (probe 2.03). Roll stop 0.85 deg <= 1.40
  (that is 1.50 - 0.1). Hand force 25.8 N <= 40 at 0.5 N m. Bearing <= 5 MPa.
- `lens_support` lens_hold passes for `lens_in` and `lens_off`.
- `lens_support` centring_gauge thumb: driver gap >= 10 mm (expected about 15.9).
- `cable_routes` fpc fold: 5 + 4 layers <= 9, panel 13.5 + 2.3 <= 17.5, reach margin >= 5 mm (expected about 22).
- All 28 existing categories still pass; the receipt lists the two new tool STLs; test_r7_c4.py passes (9 planted
  faults fail as expected).

Physical gates:
- MP-CAM (extended): tab over heads, both sides, and head diameter.
- G-KEY-1 (new): free roll <= 0.35 mm at the tab top with the key on; no cover-to-fin or key-to-PCB contact; 3 Kowa
  in/out cycles with the adapter mark unmoved.
- MP-FPC and the first build: the pack fits under the tail, nothing touches the blower inlet, the camera FPC is plugged
  at the start pose without strain.

## 8. User decisions

1. **Withdraw the panel-on lens swap** (recommended, and assumed in this spec). Every lens off or on then needs the
   panel off: one drive on each of the 4 panel bosses, and the 5-drive tally gives 4 lens changes before the M3 insert
   fallback. A change to a different lens already needs the panel off. The alternative is a plugged port in the hood
   roof above the lock tab, so the key works with the panel on. That means a visible hole on the top of the hood, a
   hood geometry change and its plug. It is not designed here: about 6 h more, and it must clear the hood rib at
   y 8.4..10.
2. None else: no part to buy. A bench vise is optional (the one-hand-from-above hold works without it).

## 9. Effort and receipt sources

| work | hours |
|---|---|
| `printed_tools.py` (camera_key, fpc_fold_card), gauge dimple | 1.5 |
| `layout.py` entries (CAM_KEY, over_heads, hold, lens_off, gauge thumb, fpc fold, STEPS text) | 1.0 |
| `checks.py`: check_camera_key (rotation stop with manifold), check_lens_hold, check_fpc_fold, gauge thumb row | 2.5 |
| `build_d2.py` export_tools and receipt, `cots.py` sub-solids | 1.0 |
| test_r7_c4.py (9 planted faults) | 1.0 |
| docs: ASSEMBLY (generated step block via make_tables), WIRING, harness-schedule, BOM (make_bom), MEASURED-PARTS, guide_steps plus the step-8 figure | 1.5 |
| full release rebuild through run_locked and review | 1.0 |
| **total** | **about 9.5 h** |

Receipt sources touched: `layout.py`, `checks.py`, `cots.py`, `build_d2.py`, `printed_collar.py`, the new
`printed_tools.py`, `make_tables.py` (only if the tools table is generated), `electronics/gs8-d2-v1/make_bom.py` and
`bom.csv`. `layout.py`, `checks.py`, `cots.py` and `printed_collar.py` force a full release rebuild (all STLs, STEPs
and checks). Production STLs should come out byte-identical except `stl/tools/collar_gauge.stl` (dimple). Verify that
in the receipt diff.
