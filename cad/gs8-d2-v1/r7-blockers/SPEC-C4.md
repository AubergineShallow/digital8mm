# SPEC-C4 (final): reacting lens-thread torque through metal (BX-4 MAJOR, BX-8, BX-15)

**r7 fix-up correction (VERIFY-C4, 2026-10-09).** The procedure left the camera resting on a tine when s_c4 was
snugged. Step 8 (and the Lens swap / s7 6a texts) now turn lens and camera together the other way to the other tine
(about 6.5 deg of free roll), then back about half way, before s_c4 (`LENS_TURN_BACK`, checked by
`checks.lens_turn_back_lint` inside the roll_catch lens_hold_lint row); the step 10 level check is unconditional.
lens_hold_lint also scans the guide sources' string literals and joined ASSEMBLY paragraphs. roll_catch is in the
release audit's EXPECTED_CATEGORIES. The tine check by feel replaces the feeler/look-down checks (the roof hides the tines).

Status: final spec, judge + synthesis, 2026-10-08 23:10-00:40 MPST. This spec merges the two designs:
`DESIGN-C4-A.md` (A: a hand-held printed camera key) and `DESIGN-C4-B.md` (B: a hood tab catch). **Winner: B's
tab catch for BX-4, with four corrections from my probes.** From A it takes the `lens_hold` class check, the
`lens_off` record, the BX-15 thumb dimple and the printed FPC fold card. Nothing in the repo was changed except
this file. Judge probes are in the session scratchpad `r7/C4J/`: `j1.py` / `j1.log` (loop room, A's pack, r6
fin, gravity sag), `j2.py` / `j2.log` (tine front vs the tub bosses, head overlap) and `j3.py` / `j3.log` (the
final tines, x1 -8.2 / z0 78.5: catch angles and window with y, z and sag offsets; PCB/cover vs COTS boxes and the
panel). They use the r6 STEPs in
`out/step/parts/` and `layout.py` imported, with B's `roll.py` camera split into metal and PCB/cover. Nothing was
printed, bought or measured.

## 1. Problem, re-checked in the current code

### 1.1 BLOCKERS BX-4 numbers: all correct

| BLOCKERS value | re-check (layout r6) | verdict |
|---|---|---|
| housing dia 35.5 x 10.35, x -17.2..-6.85 | `CAM['housing']` d 35.5, depth 10.35; `cam_hf_x()` -5.6 / -6.85 / -8.6 at s 0 / 1.25 / 3 | correct |
| front wall x -5.2 | `X_FW_IN` | correct |
| PCB / cover 1.25 / 2.0 proud | `CAM['pcb']` 38 sq (t 1.4), `CAM['cover']` 39.5 sq (t 6.49) | correct |
| about 6 mm free below | housing bottom z 42.25 vs `COTS['cooler']` box top z 36.3: 5.95 | correct |
| about 19.5 mm to the hood roof | 97.3 - 77.75 = 19.55, but see 1.2 | correct, misleading |

### 1.2 What BLOCKERS missed (confirmed by both designers and by my probes)

1. **The only positive metal feature is the split lock tab.** `CAM['tab']`: w 10.16 (y +-5.08), top z 82.1,
   depth 5.02 behind the housing front. Lock-screw head envelopes dia 4 x 2 sit on both sides, at y +-5.08..+-7.08,
   z 79.4. Which side has the head is unconfirmed (MP-CAM). BFAR and adapter are plain rings inside the
   counterbore, the lip and the hood plate.
2. **Little free height above the tab** (A, `hoodmap.py`): hood hook hk3 reaches down to z 86.8, the TL/TR collar
   insert bosses on the tub to z 86.5 (y +-11, z 90.5, rear face x -7.6), and `HOOD_RAIL` to z 90.0.
3. **The r6 roll fin itself breaks B-7.** With no hand on the camera, thread torque turns the camera until the
   cover meets `HOOD['roll_fin']`. My `j1 (c)`:
   - 2.34 deg centred;
   - **0.70 / 0.72 deg** with the hood 0.55 toward the fin (centring 0.30 + `HOOD_TO_TUB_LATERAL` 0.25);
   - 2.34 / 2.42 deg with the camera sagged 0.75 down in the counterbore.

   That reaction passes cover -> PCB -> the compliant housing-to-PCB joint. ASSEMBLY s7 "Lens swap" and
   `LATCH_FREE['lens']` ("until its cover meets the hood roll fin") rely on it, so every panel-on lens swap breaks
   the lens rule by design. No check computes the +-1.4 deg level window today.
4. **No bench workaround:** the lens cannot pass the lip bore (dia 32.4) from inside, and the cover cannot pass
   from outside (B).

### 1.3 Four corrections to the designs

| item | design claim | judge probe | consequence |
|---|---|---|---|
| A, roll stop | the key stops the camera at 0.85 deg, before the cover comes within 0.3 of the fin (1.50 deg) | at hood offset -0.55 the cover meets the r6 fin at **0.70 deg**, before the key stop (`j1 (c)`) | A fails at the worst hood offset unless the fin also goes, and then A changes the hood anyway |
| A, BX-8 pack | pre-fold 5 layers at step 4 and lay the pack in `ko_fpc_loop` z 36.6..46.6 | the `camera_in` traverse (offset -11.1, +2 high) sweeps the loop box above z 42.25. Camera to pack distance is **0.00** at s 0 / 1.25 / 3 (`j1 (b)`) | a pack laid before the camera is dragged by it. Rejected |
| B, PCB/cover roll limit | first COTS contact is the cooler box at 13.0 deg (B allowed about 11.8 with an offset) | with the gravity sag that applies at lens-out (dz -0.75), the cover meets the cooler box at **10.22 deg**. With one head only, the bare side catches at 8.44 centred and **9.94 at dy +0.55** (`j1 (d)`) | the one-head pre-gate margin is 0.28 deg, not >= 1.9. Section 4 adds sag to the check with an explicit pre-gate margin |
| B, tine front x -7.9 | `hood_on` 0.30 to the TL/TR bosses | 0.30 also in the **final pose**: the tub's TL/TR insert bosses (y +-11, z 86.5..94.5) stand right in front of the tines (`j2`) | the tine front moves back to **x -8.2**: 0.60 gap (0.30 at -7.9 and 0.80 at -8.4, linear in x). Minimum head overlap 1.40 (rule 1.0) |

B's other numbers hold. `j3` re-ran them on the final tines (front x -8.2) at s 0 and 3, with offsets dy +-0.55,
dz +-0.55, the sag dz -0.75, and the sag combined with dy +-0.55:
- tine catch 3.22 deg centred, 1.72..4.73 deg in every offset case; z offsets and sag do not change the angle;
- window 0.679 centred, 0.129 at the worst y offset (1.118 on the other side with sag);
- PCB/cover with sag: cooler box 10.22 deg, Pi 5 box 10.94 deg, the same at dy 0 / +-0.55;
- `camera_in` minimum 1.00 at z0 78.5 (B, `roll3.txt`; the rear face and bottom are unchanged);
- no printed part touches the PCB/cover before 14 deg (B, `roll2c.txt`; panel at dy +0.55 in `j3`).

### 1.4 BX-8 and BX-15 numbers

- BX-8: `cable_routes` fpc slack 119.1. `ko_fpc_loop` is x -42.5..-29.7, y 2..19.5, z 36.6..56 (12.8 x 17.5 x 19.4).
  Correct. The loop box cannot grow in +Y: extending it to y 24 meets the Pi 5 box at 0.5 mm and touches
  `ko_fpc_run`, `ko_fpc_link`, `ko_hdmi_pi` and `ko_hdmi_run` (`j1 (a)`).
- BX-15: s_c1 (y 11, z 90.5), s_c2 (-11, 90.5), s_c3 (28, 36), all driven along -X. The gauge is 44.3 dia. Correct.
  The existing `check_collar_gauge` checks the driver against the gauge, but nothing checks the thumb.

## 2. Chosen fix and why

**BX-4: the hood tab catch. Delete the roll fin and its 2 webs.** Two printed tines hang from the hood band, one
on each side of the camera's lock tab, 1.2 mm off the lock-screw head envelopes. When a lens is turned, the camera
turns about 3.2 deg until a metal head or tab face lands on a tine. The loop is lens -> C-CS adapter -> BFAR ->
housing -> tab -> tine -> hood -> tub -> collar -> lens. The compliant housing-to-PCB joint is outside it. In the
final state the tines are catches with gaps (lateral 1.2), so the J7-R float holds.

- Nobody holds the camera at step 8, at s7 6a or at the panel-on lens swap. The panel-on swap is fixed, not
  withdrawn.
- At step 8 (panel off), one fingertip pushes the cover centre forward, axially only, to keep the camera on its lip
  catch while the thread starts. Estimated friction torque through the cover: mu 0.5 x 5 N x 4 mm patch radius =
  0.01 N m, 2 % of the 0.5 N m design torque. The tab catch takes the rest.
- With the panel on, the body is tipped nose-down, as today. Then nothing touches the cover.

**BX-15: A's thumb dimple** on the gauge face, at (y -10.6, z 49.4): the lower quadrant on the camera's right
(-Y). Its gap is 15.9 mm to the nearest driver handle, against 7.4 mm for B's stem, and it needs no profile change.
**Class fix: B's held envelopes** in `check_driver`, so a hand or tool held during a drive is audited.

**BX-8: crease on the bench, fold in place after the camera is home.** The accordion stacks along Y (fold edges
face +-X; FPC width along Z, B's orientation), so it is pushed in from the open side like a bellows. A printed fold
card (2.0 mm = 2 x r_min, one layer wide) sets the bend radius and the stations. The card is also the paddle at
step 7. No pack is laid before the camera (1.3), and `KEEPOUTS` is unchanged (1.4). A fold-budget row is added.
The mating-pose reach is C2's `MATE_POSES` row `fpc_cam` (slack 118.2 in SPEC-C2); C4 adds no second reach
function.

Alternatives considered:
- A (camera key) solves only part of the problem. At the worst hood offset the r6 fin is met first. The panel-on
  swap must be withdrawn (one PT drive per panel boss per lens change). The transit margins are 0.5 / 0.6 mm, and
  the body needs a vise or a third hand.
- Wording only (the BLOCKERS interim): a hold that nothing computes. A friction clamp on the 10.35 band: about 34 N
  of clamp next to the PCB, and it cannot pass `rib_l` / the LL boss. Bench threading: impossible (1.2).
- Keeping the fin as a far backstop: it adds a cover contact to the model and nothing else. Deleted.

## 3. Exact implementation

### 3.1 `layout.py`

**`HOOD`** (line about 102): delete `roll_fin` and `roll_webs`. Add:

```python
tab_catch=dict(gap=1.2,                 # r7 C4: tine face to the lock-screw head envelope, each side
               head_side='both',        # 'both' until G-CAM-1; then '+Y' or '-Y' and bare_y is required
               bare_y=None,             # G-CAM-1: |y| of the bare side's outermost metal (tab face or screw tip)
               t=3.0,                   # web thickness in y (CRITICAL_FEATURES min 2.4)
               x=(-14.5, -8.2),         # judge: front -8.2 (0.60 to the TL/TR tub insert bosses; B had -7.9 = 0.30)
               z0=78.5, top=ZT1 + 0.5,  # bottom z; merges into the band
               flange=dict(dx=2.0, dy=12.0),   # rear flange x -14.5..-12.5, outward 12.0 from the tine face
               lead_in=1.0,             # 1.0 x 45 chamfer, rear inner vertical edge (tab entry at step 7)
               root_chamfer=2.0),       # 2 x 45 at the band where the fillet fails
```

**New function** beside `cam_hf_x`: `tab_catch_boxes(L=None) -> list[B]`. It returns 4 boxes: a web and a flange
for +Y and for -Y.
- Inner face per side: `y_in = CAM['tab']['w']/2 + CAM['tab']['head_h'] + gap` = 8.28. On the bare side, once
  `head_side` is set: `y_in = bare_y + gap`.
- Web: x -14.5..-8.2, |y| y_in..y_in+t, z z0..top.
- Flange: x -14.5..-12.5, |y| y_in..y_in+12.0, z z0..top.
- Raise `ValueError` if `head_side` != 'both' and `bare_y` is None.
- The +Y web merges into `printed_hood.RIB` (y 8.4..10.0).

**`CAM['tab']`**: add `tip_h=None`. `CAM['status']['tab']` = "drawing; lock-screw head side, head dia/height and
tip protrusion unconfirmed: G-CAM-1 sets HOOD['tab_catch'] head_side / bare_y".

**New `ROLL_CATCH`**:

```python
ROLL_CATCH = dict(design_torque_Nm=0.5, window_deg=1.4, window_gap=0.3, scan_deg=14.0, step_deg=0.25, tol=0.01,
                  margin_deg=1.0,              # declared geometry: PCB/cover first contact >= metal + 1.0 deg
                  margin_unconfirmed_deg=0.2,  # one-head variants while head_side == 'both' (pre-G-CAM-1 only)
                  tine_sigma_max_MPa=10.0, tine_defl_max=0.1, E_MPa=2000.0)
```

The lateral offset (centring worst 0.30 + `HOOD_TO_TUB_LATERAL` 0.25 = 0.55) and the lens-out sag (the counterbore
radial clearance, (`CAM` `cb_d` 37.5 - BFAR head dia) / 2 = 0.75) are derived in the check. Neither is typed as a number.

**`CRITICAL_FEATURES`** (line 1772): replace `hood_cam_roll_fin` with `hood_tab_catch_p` and `hood_tab_catch_n`:
part 'hood', origin (-11.35, +-9.78, 88.0), direction (0, 1, 0), min_mm 2.4, structural, note "r7 C4: camera tab
catch, 1.2 off the lock-screw heads; contact only while a lens is turned". Class rule (line 1778):
`(r'^hood_tab_catch_[pn]$', 'wing')`. In the joint whole-check list (line 1281), replace 'hood_cam_roll_fin' with
both new ids.

**Text constants:**
- J7 comments (lines 216, 1276), `HOOD_TO_TUB_LATERAL` comment (1910), checks.py comment (1659): "hood roll fin"
  -> "hood tab catch".
- `PRINT_PREREQ_WHY['G-CAM-1']`: "... hood tab catch (lock-screw head side, head dia/height, tip protrusion, tab
  width/top) ...". The hood already waits for `_CAMERA` (G-CAM-1) and G-MP-FPC in `PRINT_PREREQS`; no change.
- `LATCH_FREE['lens']` (line 1591): "r7: loosen s_c4 one turn (straight PH1 from above), tip the body nose-down,
  unscrew the lens with fingertips: the camera turns about 3 deg until its metal lock tab meets the hood tab catch,
  which holds it (nobody holds the camera)".

**`INSERTIONS` `lens_in`**: add `hold='hood_tab_catch'`. **`REMOVALS`**: add
`dict(id='lens_off', moving=['lens'], reverse_of='lens_in', off=['s_c4'], hold='hood_tab_catch')`. Panel present:
this is the panel-on lens swap and s7 6a. The `removals` sweep then covers it.

**`STEPS`**:
- Step 7 `tool` += "; FPC fold card (tool 15)".
- Step 7 gains `held=[dict(id='collar_gauge'), dict(id='thumb_gauge', kind='cyl', at='COLLAR.gauge.thumb')]`.
- Action texts: section 5.
- Step 8 `tool` unchanged. Step 10 text: section 5.

**`COLLAR['gauge']`**: add `thumb=dict(c=(-10.6, 49.4), d=16.0, depth=0.6, envelope_d=20.0, envelope_len=60.0)`.

**`CABLES` `fpc`**: add `fold=dict(kind='accordion', box='ko_fpc_loop', stack_axis='y', layer_axis='x',
width_axis='z', r_min=1.0, t=0.15, w=16.0, estimate=True, gate='G-MP-FPC', start_from_pi=None)`. `t` and `w` are
stated upper estimates until G-MP-FPC. `start_from_pi` is computed: the route to the loop entry, from the existing
polyline. No length change; no harness row change.

### 3.2 Geometry and code

| file | function | change |
|---|---|---|
| `printed_hood.py` | `_roll_fin(L)` -> `_tab_catch(L)` | Build the boxes from `L.tab_catch_boxes()`, with the `lead_in` chamfer on the rear inner vertical edge and the root fillet (or `root_chamfer`). Line 300: `adds += _hooks(L) + _edge_flange(L) + _tab_catch(L)`. Docstring lines 4 and 31: "the camera tab catch (2 tines) hangs from the band". The hood prints band-down (`face_down` +Z): the tines and flanges grow straight up, with no overhang and no support. |
| `printed_collar.py` | `centring_gauge()` | Cut a dia 16 x 0.6 thumb dimple with a 0.3 chamfer into the front face at `thumb['c']`, plus an engraved arrow. The face is the top in the print pose: no overhang. |
| `printed_tools.py` (new) | `fpc_fold_card(L)` | A plate 2.0 thick (= 2 x `r_min`) x 10.5 wide x 24 long, plus a 30 mm handle. The width is the layer straight length: `ko_fpc_loop` x 12.8 - 2 (r_min + t). The 24 mm length is `w` 16 + 8. Engraved "r1 / FPC". It prints flat. It is an assembly tool, like `centring_gauge`. C6's `release_comb` may share the same export helper. |
| `cots.py` | `gs_camera_parts(L, s=None, head_side='both')` | Also return `'metal'` (housing + tab + heads) and `'pcb_cover'` (PCB + cover). `'body'` stays their union, so `j7_float` and every existing caller see the same solid. `head_side` '+Y' / '-Y' builds one head only. |
| `checks.py` | `check_roll_catch`, `check_driver` `held`, cable_routes fold rows | See section 4. |
| `build_d2.py` | registration, export | Register `R['roll_catch'] = CK.check_roll_catch(L, man_rows)` next to `j7_float`. Export `stl/tools/fpc_fold_card.stl` next to `export_gauge`, with `print_overhang` and `thin_wall` rows. Add it to the manifest `tools` list. |
| `make_tables.py` | tables | New "FPC crease stations" table in ASSEMBLY.md s2 (B0). Station i at `start_from_pi + i x (10.5 + pi x r_min)` from the Pi end, mountain and valley alternating, 9 stations today. Regenerate the step tables. |
| `test_hood_panel.py` | r5 block (lines 95-96, 136) | `roll_fin_to_cover` / `roll_fin_ok` -> `tab_catch_to_metal` (>= gap - 0.01 at every s) and `tab_catch_to_pcb_axial` (>= 0.9). |

**Tine numbers** (probes against the r6 geometry; `x1` -8.2 only changes what `j2` lists):

| limit | value |
|---|---|
| tine front x -8.2 vs TL/TR tub insert-boss rear face x -7.6 (final pose and the whole `hood_on` -Z drop) | 0.60 (-7.9: 0.30; -8.4: 0.80; `j2`) |
| head x-overlap with the tine (s 0..3; axial lip +0.5, final, keeper -3.5) | min 1.40 (s 0 on the lip catch); 1.9..4.0 elsewhere |
| tine rear x -14.5 vs the BFAR head at the `camera_in` entry offset | 1.0 |
| tine rear vs PCB front, s 0 | 1.45 final, 0.95 on the lip catch (J7 axial rule 0.4) |
| tine bottom z 78.5 vs the adapter during the 2 mm-high traverse | `camera_in` min 1.00 |
| flange vs panel material | 5.9 |
| s_c1 / s_c2 tips (x -7.0 with the 0.29 sink) vs tine front | 1.2 |
| strength, F = 0.5 N m / r 17.4 = 28.7 N; T-section web 4.3 x 3.0 + flange 2.0 x 12.0; I 468 mm4, Z 61.8 mm3; arm 19.3 | sigma 9.0 MPa (limit 10; ASA interlayer 15-25 literature, SF 1.7-2.8), deflection 0.07 mm |
| mass | fin + webs out (about 665 mm3), tines in (about 1380 mm3): hood +0.7 g |

### 3.3 BOM and harness

- `electronics/gs8-d2-v1/bom.csv` + `make_bom.py` -> BOM.md: one row in "F. Tools and accessories": "FPC fold card,
  printed ASA (tool 15), `stl/tools/fpc_fold_card.stl`, 0 cost plus filament". Kapton is already D2-48.
- No new part for the tab catch (hood material). No harness row change: the FPC stays 200 mm.
- `harness-schedule.csv` fpc routing note: section 5.

## 4. New computed checks

### 4.1 `roll_catch` (new category; J7 family)

Signature: `checks.check_roll_catch(L, rows, s_values=None, parts_of=None)`.

- Camera solids: `metal` and `pcb_cover` from `cots.gs_camera_parts`.
- Rotation axis: the camera axis, displaced by the case offset.
- Obstacles: every solid present in the final state, plus every solid present at each record that has a `hold`:
  printed parts, COTS solids/boxes and screws, cropped as in `check_j7_float`. The lens is excluded (it turns with
  the camera).
- Cases, for each s in `checks.j7_s_values(L)` (0 .. 3, the same set as `j7_float`):
  - offsets (dy, dz) in {(0, 0), (+-0.55, 0), (0, +-0.55)};
  - **lens-out cases** (records with `hold`) add the sag: (0, -0.75) and (+-0.55, -0.75);
  - direction + and -.

| row | pass criterion | expected (probes) |
|---|---|---|
| `first_contact` (declared geometry, `head_side` as set) | The first contact within `scan_deg` is `metal` with the hood tab catch (0.25 deg steps, bisection to 0.01). Any `pcb_cover` first contact comes >= metal + `margin_deg` 1.0. FAIL if there is no metal contact within 14 deg, the first contact is anything else, or the tab catch is missing. | 3.22 centred; 1.72..4.73 with the offsets; PCB/cover: cooler box 10.22 with sag, 13.01 without; no printed part to 14 |
| `first_contact_unconfirmed` (only while `head_side == 'both'`) | Variants '+Y' and '-Y' (one head). Metal is still first, and PCB/cover >= metal + `margin_unconfirmed_deg` 0.2. The row carries `gate='G-CAM-1'` and the note "hood is print-blocked until G-CAM-1 (PRINT_PREREQS)". It is skipped once `head_side` is set, because the declared row then covers the real part. | bare side 8.44 centred, 9.94 worst, vs cooler 10.22 with sag: margin 0.28 |
| `window` (final state: camera on the lens, no sag) | Metal-to-hood distance at +-`window_deg`: >= `window_gap` 0.3 at offset 0, and >= `J7_RUNNING` 0.1 at the worst offset. | 0.679 / 0.129 |
| `tine_strength` (estimate row) | F = `design_torque_Nm` / the smallest contact radius in the first-contact poses. Cantilever from the contact z to the band, using the computed section of `tab_catch_boxes()`. sigma <= 10 MPa, deflection <= 0.1. | 9.0 MPa, 0.07 mm |
| `axial_engagement` | Head envelope (or tab, on the bare side) x-overlap with the tine x span, for every s and axial state (lip +0.5, final, keeper -3.5): >= 1.0. | min 1.40 |
| `lens_hold` (class check, from A) | Every `INSERTIONS` / `REMOVALS` record whose moving set holds 'lens' has `hold`. The hold feature exists in its part (`tab_catch_boxes()` non-empty, hood present in that record's set), and its `first_contact` rows pass. Text lint: `STEPS`, `LATCH_FREE` and ASSEMBLY.md contain none of the phrases in the new `LENS_HOLD_FORBIDDEN = ('cover meets', 'roll fin, which then holds', 'roll fin beside', 'hold the camera by its metal lens mount', 'hold the cover')` (case-insensitive). | pass for `lens_in`, `lens_off` |

This closes the class: a thread turned on the camera, held by something nothing computes, or reacted through the
board.

### 4.2 `check_driver`: held envelopes (BX-15 class)

`STEPS[i]['held']` lists the solids held in place while that step's screws are driven: assembly tools by id
(`collar_gauge` = the built gauge solid in its seated pose), and hand envelopes (`kind='cyl'`, a dia
`envelope_d` x `envelope_len` cylinder along +X from the gauge face at `thumb['c']`).
- `check_driver` adds them to the audit set of every screw whose `step` is i. `service_driver` inherits the same
  path.
- With C6's bit-length family, every family member is checked.
- Pass: no hit, and the row reports `held_gap` (the smallest gap from bit or handle to a held solid).
- New rule: `held_gap >= 10` for hand envelopes, `<= VOL_TOL` overlap for tools.
- Expected (A's numbers, re-computed by hand): thumb to the s_c2 handle 16.1, s_c3 15.9, s_c1 21.4; bits >= 27.6.

`check_collar_gauge` keeps its driver row unchanged.

### 4.3 `cable_routes`: fpc fold budget (BX-8 class)

This is one more item in `check_cable_routes`, for each cable with `fold`. The function is
`_fold_rows(L, cable)`.
- straight = box[layer_axis] - 2 (r_min + t) (12.8 -> 10.5);
- layer = straight + pi x r_min (13.64);
- n = ceil(slack / layer), where slack is the existing row's value (119.1 -> 9);
- stack = (n - 1)(2 r_min + t) + t (17.35);
- pass if stack <= box[stack_axis] (17.5) **and** w <= box[width_axis] (16 <= 19.4).
- The row carries `estimate=True` and `gate='G-MP-FPC'` while `fold['estimate']`, and reports the margin
  (0.15 today).
- The card row checks `fpc_fold_card` thickness == 2 r_min and width == straight (built solid vs `fold`).

The mating-pose reach is **not** duplicated. SPEC-C2's `check_mate_reach` row `fpc_cam` (`MATE_POSES`, camera at
the `camera_in` start) covers it. If C2 has not landed when C4 is implemented, C4 adds that one `MATE_POSES` row
exactly as C2 writes it.

### 4.4 Planted-fault regressions: `test_r7_c4.py`

The style follows `test_r3_regressions.py`, run through `run_locked.py`. Each case deep-copies `HOOD` / `CAM` /
`COLLAR` / `CABLES` / `STEPS` into a modified layout namespace and asserts the named failure. A positive control
runs on the real layout.

| # | planted fault | expected failure |
|---|---|---|
| 1 | r6 `roll_fin` box re-added to the hood | `roll_catch.first_contact`: pcb_cover meets the hood at 0.70 deg (dy -0.55) before metal |
| 2 | `tab_catch` removed | `first_contact`: "no metal catch within 14 deg" (PCB/cover first at the cooler box, 10.22) |
| 3 | `gap` 0.5 | `window` at the worst offset (< 0.1) |
| 4 | `gap` 0.4 | `j7_float` body lateral (< 0.5) |
| 5 | tine `x` (-16.0, -8.2) | `sweeps camera_in` (BFAR head at the entry offset) |
| 6 | `z0` 76.5 | `sweeps camera_in` (adapter in the 2 mm-high traverse) |
| 7 | tine `x` (-14.5, -7.5) | `interference` / `hood_on` with the TL/TR tub insert bosses |
| 8 | `COTS['cooler']['box']` z1 36.3 -> 37.3 | `first_contact_unconfirmed`: the cover meets the cooler box at about 6.4 deg (B's 0.26 mm/deg rate), before 9.94 + 0.2. This proves that COTS boxes and the lens-out sag are in the obstacle set. The declared row still passes (4.73 + 1.0 < 6.4) |
| 9 | `head_side` '+Y' with `bare_y` None | `tab_catch_boxes` ValueError -> build row FAIL |
| 10 | `hold` deleted from `lens_in`; `LATCH_FREE['lens']` reset to the r5 text | `lens_hold` FAIL (missing hold; lint "cover meets") |
| 11 | `COLLAR['gauge']['thumb']['c']` -> (11.0, 75.0) | `driver` s_c1 `held_gap` < 10 |
| 12 | `fold['t']` 0.25; then `fold['r_min']` 1.2 | `cable_routes` fpc fold (stack 18.25 / 20.55 > 17.5) |
| 13 | positive control | all rows pass; first contact 3.22 +-0.05 deg centred |

## 5. Document changes (exact wording)

The step blocks in ASSEMBLY.md come from `layout.STEPS` through `make_tables.py`. Edit STEPS, then regenerate.
Other clusters edit the same steps' texts: C2 (step 8 panel/QT sentences) and C6. Merge at the sentence level; C4
owns only the sentences quoted here.

**STEPS step 7 action:**
- Gauge sentence -> "... hold it home with your thumb in the dimple on its face (lower, on the camera's right
  side: no collar screw there) and tighten s_c1, s_c2, s_c3 from the front ...".
- Camera sentence, after "+X 11.1 until the adapter has passed the tub lip" add: "and the lock tab has gone in
  between the two tab-catch tines under the hood (if the tab stops on a tine end, roll the camera level and push
  again)".
- Replace "Fold the FPC slack into its loop." with: "The FPC was creased at B0. Keep its slack loose and out of
  the opening while the camera slides in. Then fold it back along its creases and push the folded pack -Y into the
  loop space behind the camera with the fold card (tool 15) as a paddle. Lay one Kapton strip across it. It must
  not touch the blower inlet."

**STEPS step 8 action**, first sentence -> "Lens, panel still off: fit s_c4 loosely. One fingertip on the centre of
the camera cover, through the open left side, presses the camera forward (+X) onto its lip catch: push only,
never pinch or turn the cover. Pass the lens through the collar. Screw it into the adapter with fingertips until it
stops, with no extra snug. The camera turns with it about 3 deg until its metal lock tab meets the hood tab catch,
which holds it through metal. Set iris and focus, ...". In the hang sentence, "nor the fin" -> "nor the tab-catch
tines". Panel sentences: unchanged by C4.

**STEPS step 10 action:** "(window +-1.4 deg: the cover keeps >= 0.3 off the hood roll fin)" -> "(window +-1.4
deg: the lock-screw heads keep >= 0.3 off the tab-catch tines; computed `roll_catch` window)".

**ASSEMBLY.md s1 lens rule row** (line 23): replace from "At step 8 (panel off) finger and thumb ..." to "... so the
roll fin never becomes a wrench." with: "r7 (BX-4): nobody holds the camera. Thread torque turns it about 3 deg
until its metal lock tab meets the hood tab catch (two tines, one each side of the tab). The reaction goes housing
-> tab -> hood, never through the cover or the PCB (computed: `roll_catch`). Panel off (step 8): one fingertip on
the cover centre keeps the camera forward on its lip catch, push only. Panel on (lens swap): tip the body nose-down
so the camera comes forward onto its lip catch. Turn the lens with fingertips only."

**ASSEMBLY.md s1.1 tools table:** add "| 15 | FPC fold card, printed (`stl/tools/fpc_fold_card.stl`) (r7) | crease
the camera FPC (B0); paddle for the folded pack (7) | D2-8x | - |". If another cluster has taken 15, renumber at the
merge.

**ASSEMBLY.md s2 B0:** add two items:
- "Paint a second mark across BFAR and housing (the first is across adapter and BFAR). Check both marks at every
  lens change: the tab catch reacts the thread through the BFAR thread, like any hold on the housing would."
- "Crease the FPC on the fold card at the stations in the FPC crease-station table (accordion, mountain and valley
  alternating, from the Pi end). Open it flat again."

**ASSEMBLY.md s3 checks:**
- Row 7 add: "FPC pack folded on its creases and taped; nothing on the blower inlet."
- Row 8: "nor the roll fin" -> "nor the tab-catch tines; look down between the tines: a gap on each side of the
  lock tab".

**ASSEMBLY.md s7 item 6a** -> "a. Lens: loosen s_c4 one turn (straight PH1 from above). Unscrew the lens with
fingertips: the tab catch holds the camera, and no hand touches it. Lift the lens out forward (+X 40). Check both
paint marks (B0). (CAD record `lens_off`.)" In "To close", replace "the lens through the collar with the camera held
by its metal mount" with "the lens as step 8 (fingertip push on the cover centre, tab catch holds)".

**ASSEMBLY.md "Lens swap" paragraph** (after s7 item 11): replace "the hood roll fin beside the cover ... and hold
the metal mount." with: "the hood tab catch either side of its lock tab. Loosen s_c4 one turn (straight PH1 from
above). Tip the body nose-down. Carry the lens with one hand and unscrew it with fingertips only: the camera turns
with it about 3 deg until its lock tab meets the tab catch, which holds it through the metal housing. A stuck
thread: stop, never more than fingertip torque." Keep the rest (G-CAM-2 after 5 swaps, adapter mark, nose-down for
the new lens, collar per band, back focus). Change "Then check the adapter mark" to "Then check both paint marks".

**MEASURED-PARTS.md:**
- MP-CAM / G-CAM-1 add: "lock-screw head side, head dia and height, tip protrusion on the other side, tab width
  and top radius. Set `HOOD['tab_catch']` head_side / bare_y (and `CAM['tab']`), rebuild; `roll_catch` and
  `j7_float` must pass again before the hood is printed."
- G-CAM-2 add: "lens off, panel off: roll the camera by hand both ways. The tab meets a tine at about 3 deg and the
  cover touches nothing. Lens on and seated: a 0.5 mm feeler passes between each tine and the tab/heads. After 5
  swaps: no whitening at the tine roots, both paint marks unmoved."
- MP-FPC / G-MP-FPC: replace the S-fold wording with "the accordion (fold card, stations from the crease table)
  folded by hand into a printed `ko_fpc_loop` box stays inside it (stack <= 17.5 along Y). Record width and
  thickness: they replace `CABLES['fpc']['fold']` t / w (estimate = False)".

**electronics/gs8-d2-v1/WIRING.md s7:**
- Row 4 note -> "camera end loose; FPC creased at B0 on the fold card".
- Row 7 note -> "after the camera is home: fold the slack back on its creases, push the pack -Y into `ko_fpc_loop`
  with the fold card, Kapton strip; `cable_routes` fpc fold row".

**harness-schedule.csv** fpc routing note: the same two sentences.

**BOM.md:** regenerated by `make_bom.py` (the tool row, 3.3).

**guide/guide_steps.py:**
- Delete `ISSUES['8a']` (BX-4).
- `TIPS['7a']` -> "BX-15 (fixed): thumb in the dimple on the gauge face, lower, on the camera's right. That spot is
  clear of all three screwdriver lines (computed)."
- `TIPS['7b']` -> "BX-8 (fixed): the FPC was creased at B0. After the camera is home, fold it back on its creases
  and push the pack in with the fold card."
- New `TIPS['8a']` -> "Fingertip pushes the cover centre forward; turn the lens with fingertips until it stops. The
  camera stops on the tab catch. Never grip the cover."
- Line 312: "nor the roll fin" -> "nor the tab-catch tines".
- Re-render the hood and gauge views.

**guide/build_guide.py** line 838: replace the roll-fin sentence with "the hood tab catch holds the camera through
its metal lock tab; no hand on the camera".

**Roll-fin text sweep:** SPEC.md (6), DESIGN.md (4), PRINT-GUIDE.md (3), R5-BRIEF.md (2), NOTES.md, HANDOFF.md,
RECTIFICATION.md and LENS-ZOOM-CANDIDATES.md (1 each). Current-state statements -> "hood tab catch (r7)". Keep
historical r5/r6 records and mark them "superseded r7". The `lens_hold` lint covers ASSEMBLY.md, STEPS and
LATCH_FREE.

**BLOCKERS-2026-10-08.md:** append one status line only: "r7: BX-4, BX-8, BX-15 fixed in CAD (SPEC-C4)". The table
stays as the record. **HANDOFF.md** top: one r7 C4 line.

## 6. Interactions and risks

| area | effect |
|---|---|
| `j7_float` | Tines are new hood obstacles. Body lateral 1.2 (rule 0.5); axial to the PCB 1.45 at s 0 (rule 0.4); centring remaining 1.2 - 0.30 - 0.25 = 0.65 (rule 0.1). The roll-fin row goes. The float is unchanged in kind: catches with gaps. |
| `sweeps` / `removals` | `camera_in` min 1.00 to the tines; `camera_out` mirrors it. `hood_on` 0.60 to the TL/TR tub bosses (was 0.30 in B). `panel_on` 5.9. New `lens_off` record (lens +X 40, panel present). |
| `driver` / `service_driver` | No screw axis passes the tines; the s_c1/s_c2 tips stay 1.2 ahead. New `held` envelopes at step 7. C6's bit-length family: `held` must loop over every member. Whoever lands second rebases (C6 already notes this). |
| `critical_features`, `thin_wall` | 2 rows replace 1; web 3.0 (min 2.4). The joint whole-check list is updated. |
| `print_overhang` | Hood band-down: the tines are vertical, so no new overhang. Gauge dimple on the top face. Fold card flat. |
| `keepouts`, `cable_routes` | No keep-out inside the tines; `KEEPOUTS` unchanged. New fpc fold row (margin 0.15, estimate, gate G-MP-FPC). |
| `evf_restraint`, `inserts`, `lens_support`, `lens_clamp` | Unaffected (far from the tines; lens collar unchanged). |
| `mass_com` | Hood +0.7 g. |
| BFAR thread | The reaction passes the BFAR fine thread, pinched by the lock screw, as any hold on the housing would. Mitigation: the second paint mark (B0); never loosen the lock screw in the body. |
| fingertip push at step 8 | Axial only; estimated friction torque 0.01 N m through the cover (2 % of design torque). Not computed in CAD; stated in the step text. |
| **unknown lock-screw head** (main risk) | Real head side, size and tip are unconfirmed. Before G-CAM-1 the bare side catches at up to 9.94 deg, only 0.28 deg before the cover meets the COTS cooler box with sag (10.22). That is why the `first_contact_unconfirmed` margin is 0.2, and why the hood must not print before G-CAM-1 (already in `PRINT_PREREQS`). After G-CAM-1 the bare-side tine moves in (`bare_y`), and both directions catch at about 1.7-4.7 deg. A real head > 0.7 larger than the envelope fails `j7_float` lateral: then set the gap from the measurement. |
| tine strength | Bending crosses the layers (hood prints band-down). sigma 9.0 MPa at a deliberately high 0.5 N m; SF 1.7-2.8 on a literature range, not measured. G-CAM-2 checks the roots after 5 swaps. |
| window margin | 0.129 at the worst 0.55 offset (rule 0.1). A real centring stack worse than 0.30 shows up in G-COL-1 and fails the computed row; it does not fail silently. |
| FPC fold | Stack 17.35 in 17.5 (estimate t 0.15, r_min 1.0). The fold is a G-MP-FPC item, and the tub and hood already wait for G-MP-FPC. Folding the pre-creased pack into place by hand is untried; G-MP-FPC does exactly that on the bench. |
| other clusters | C6 edits `printed_hood.py` (`_plate_cuts`, `release_comb`) and `check_collar_gauge` / the driver family: merge by hand, no shared geometry. C2 owns `MATE_POSES` / `check_mate_reach` (row `fpc_cam` covers the FPC reach), and C2 edits step 8 panel text: sentence-level merge. C1 and C3: no overlap. C5: no overlap. |

## 7. Acceptance criteria

Computed, after the full release rebuild (all existing categories pass, plus `roll_catch`):
- `roll_catch.first_contact`: metal meets the tab catch first in every row; 3.22 +-0.05 deg centred, 1.7..4.8 deg
  over the offsets and sag; PCB/cover >= metal + 1.0 deg (expected >= 5.4: 4.73 vs the cooler box 10.22).
- `roll_catch.first_contact_unconfirmed`: metal first; margin >= 0.2 deg (expected 0.28).
- `roll_catch.window`: >= 0.3 centred (0.679), >= 0.1 at the worst offset (0.129).
- `roll_catch.tine_strength`: sigma <= 10 MPa (9.0), deflection <= 0.1 (0.07). `axial_engagement` >= 1.0 (1.40).
- `roll_catch.lens_hold`: pass for `lens_in` and `lens_off`; text lint clean.
- `j7_float`: all rows pass; tine lateral 1.2, axial >= 0.95, centring remaining 0.65.
- `sweeps`: `camera_in` >= 0.9 to the tines (1.00); `hood_on` >= 0.5 to the TL/TR tub bosses (0.60); `removals`
  `lens_off` pass.
- `driver`: 11/11 (and C6's family) with `held` at step 7: no hit, thumb `held_gap` >= 10 (15.9).
- `cable_routes` fpc fold: stack <= 17.5 (17.35), width 16 <= 19.4; card row pass. C2 `mate_reach` fpc_cam
  slack >= 0.
- `critical_features` hood_tab_catch_p/n >= 2.4; `print_overhang` and `thin_wall` for the hood, the gauge and the
  fold card pass.
- `test_r7_c4.py`: all 12 planted faults fail as stated, and the positive control passes.
- Production STLs change only for `hood.stl` (tines in, fin out); tool STLs: `collar_gauge.stl` (dimple), new
  `fpc_fold_card.stl`. Verify in the receipt diff.

Physical gates:
- **G-CAM-1** (before the hood prints): head side, head size, tip, tab width and top; set `head_side` / `bare_y`;
  rebuild.
- **G-CAM-2** (first assembly): roll-by-hand check, 0.5 mm feeler at the tines, root and paint-mark check after
  5 swaps.
- **G-MP-FPC**: accordion in a printed loop box; real t / w replace the estimates.
- **G-COL-1**: the centring stack that the window margin relies on.

## 8. User decisions

1. **FPC length (optional purchase).** Keep the 200 mm Standard-Mini: the fold fits on the estimate, margin 0.15,
   and G-MP-FPC confirms it. Or buy a 100-150 mm 22-to-15 cable, if one can be sourced (WIRING.md already notes this
   option): about 6 layers, stack about 10.9. Availability and price were not checked. **Default if no answer: keep
   200 mm**, and revisit only if G-MP-FPC fails.

Everything else is decided here. The panel-on lens swap is kept, not withdrawn.

## 9. Effort and receipt sources

| work | hours |
|---|---|
| `layout.py` (HOOD tab_catch, `tab_catch_boxes`, CAM tab status, ROLL_CATCH, CRITICAL_FEATURES + joint list, LATCH_FREE, INSERTIONS hold, REMOVALS lens_off, STEPS 7/8/10 text + `held`, COLLAR gauge thumb, CABLES fold, G-CAM-1 text) | 1.0 |
| `printed_hood.py` (`_tab_catch`), `cots.py` (metal / pcb_cover, head_side), `printed_collar.py` (dimple), `printed_tools.py` (fold card) | 1.2 |
| `checks.py`: `check_roll_catch` (with lens_hold and lint), `check_driver` `held`, `_fold_rows` | 2.5 |
| `build_d2.py` registration and export; `make_tables.py` crease table; `test_hood_panel.py` r5 block | 0.7 |
| `test_r7_c4.py` (12 faults + control) | 1.3 |
| docs: ASSEMBLY (STEPS + hand-written rows), MEASURED-PARTS, WIRING, harness CSV, BOM via make_bom, guide_steps / build_guide + re-render, roll-fin text sweep, BLOCKERS status line, HANDOFF | 1.5 |
| full release rebuild through `run_locked.py`, receipt diff, review | 1.3 |
| **total** | **about 9.5 h** |

Receipt sources touched: `layout.py`, `printed_hood.py`, `printed_collar.py`, `printed_tools.py` (new), `cots.py`,
`checks.py`, `build_d2.py`, `make_tables.py`, plus `electronics/gs8-d2-v1/make_bom.py` and `bom.csv`. `layout.py`,
`checks.py`, `cots.py`, `printed_hood.py` and `printed_collar.py` force a full release rebuild (all STLs, STEPs,
checks, tables). Run it once, after the merges with C2 and C6.

## Judging

Scores are 1-5 (5 best).

| criterion | A: camera key | B: tab catch | reasons |
|---|---|---|---|
| 1. removes the physical problem (re-probed) | 2.5 | 4.5 | A: at the worst hood offset (-0.55) the r6 fin meets the cover at 0.70 deg, before A's key stop at 0.85 (`j1 (c)`). A also withdraws the panel-on swap instead of fixing it. B: metal is first in every case, including panel-on swaps and with the body on its side. Small minus: the fingertip axial push at step 8. |
| 2. robustness to unmeasured dimensions | 2.5 | 3.5 | A: transit margins 0.5 / 0.6 mm, a jaw gap from MP-CAM, but a cheap reprint. B: gap 1.2 and window 0.129 at the worst offset. B missed the gravity sag: the one-head pre-gate margin is 0.28 deg, not 1.9 (`j1 (d)`). The hood is already blocked by G-CAM-1, so a real head is designed in before printing. |
| 3. user rules (driver, printed/COTS, J7-R, power last) | 4 | 5 | Both pass. A needs a vise or a third hand. B adds no tool and keeps the float as catches with gaps. |
| 4. blast radius | 4.5 | 3 | A changes no production part. B changes the hood, CRITICAL_FEATURES, the joint list and test_hood_panel, and shares `printed_hood.py` with C6. |
| 5. assembly and service simplicity | 2 | 4.5 | A: blind key insertion under the hood with sub-mm margins, a body hold, and the panel off for every lens change. B: nothing to hold; a fingertip push with the panel off, nose-down with the panel on. |
| 6. quality of the new computed check | 3.5 | 4 | A: `lens_hold` is the right class check, but `roll_stop` missed the hood offset. B: `roll_catch` over s, offsets and head variants, plus the window, and it catches the existing fin defect. B missed the sag; tools_present is generic. |
| BX-8 | 2 | 3 | A's pre-laid pack is hit by the camera traverse (`j1 (b)`, distance 0). B's orientation is right (width along Z, push from the open side), but self-collapse is untried. Final: B's orientation, a hand fold after the camera is home, A's fold card. |
| BX-15 | 4 | 3 | A's dimple: 15.9 mm to the handles and no profile change. B's stem: on-axis, but 7.4 mm and a longer tool. Final: A's dimple plus B's generic `held` mechanism. |
| **total (criteria 1-6)** | **19** | **24.5** | **B wins.** It is corrected by the judge: tine front -8.2, sag and z offsets in the check, the pre-gate margin, lens-out cases. It takes A's `lens_hold`, `lens_off`, the dimple and the fold card. |

## Plan edits (integration, 2026-10-09 00:00-01:00 MPST; PLAN.md wins where it and this spec differ)

Plan edits: P4-1 No BOM row for the fold card (3.3): printed tools are not BOM rows (tool 14, the collar gauge, has
none; SPEC-C6's comb has none). Tool table row reads "| 18 | FPC fold card, printed (`stl/tools/fpc_fold_card.stl`)
(r7) | crease the camera FPC (B0); paddle for the folded pack (7) | printed (PRINT-GUIDE s3) | - |" (tool **18**, not 15)
(PLAN.md X-9: 15 pliers C1, 16 paper strips C5, 17 optional mirror C1, 18 fold card; C6 comb keeps tool 9). Every "tool 15" in this spec reads "tool 18".
Plan edits: P4-2 `printed_tools.py` holds BOTH `fpc_fold_card(L)` and SPEC-C6's `release_comb(L)` (moved there from
printed_hood.py). build_d2 gets one `export_tools()` writing stl/tools/*.stl with print_overhang/thin_wall rows and
manifest rows; `TOOL_PREREQS = {'fpc_fold_card': (), 'release_comb': ('G-MP-REL',)}` (C6) is read by the
print_order 'tool' loop. Add printed_tools.py to the receipt source list.
Plan edits: P4-3 check_driver `held` is built inside SPEC-C6's bit-length family loop when C6-BX-12 has landed
(every member; the thumb-to-handle gap is radial, so 15.9 is expected for every member that overlaps the thumb
cylinder axially); if C6-BX-12 is dropped, `held` runs on the single r6 member (40 x 100). Rule unchanged (>= 10).
Plan edits: P4-4 Section 6 "C5: no overlap" is void: SPEC-C5 edits the last sentence of the step-8 action and
adds the knobs to `panel_on`; SPEC-C2 edits the panel sentences. The merged step-8 text is PLAN.md s4; C4 owns the
lens sentences and "nor the tab-catch tines". Step 10 merges with SPEC-C3's XT30 sentence.
Plan edits: P4-5 Build time: roll_catch must stay under about 3 min per build (bbox prefilter per solid, manifold
booleans, coarse 0.5 deg scan then bisection to 0.01). Measure it in the first trial build; if longer, reduce the
scan to the first-contact bracket, never the case set.
Plan edits: P4-6 Delivery order inside the cluster (PLAN.md S5): core BX-4 first (tab catch, cots sub-solids,
roll_catch, lens_off, texts), then BX-15 (dimple + held), then BX-8 (fold rows + card). Each sub-step leaves the
build green; BX-15 and BX-8 are on the drop list. `roll_catch` registers with `info_neutral=True` if it carries
estimate rows as 'info'.
