# Judge 1: heavy-lens sag fix for D2 J7 (structural mechanics and load path), 2026-10-06

Read-only review. No repo file was edited, built or re-run. My only probe: `scratchpad/sag/j1/pi_drop.py` (Pi stack
swept along `INSERTIONS['pi_in']` against the tub features each design adds). Frame: +X forward, +Y left (panel), +Z
up, lens axis (y 0, z 60).

## 1. Scores

| Design | Bypass /30 | Alignment /20 | Buildability /20 | Robustness /15 | Generality /10 | Impl risk /5 | Total |
|---|---|---|---|---|---|---|---|
| D1 lens collar + floating camera (J7-R) | 27 | 15 | 11 | 11 | 8 | 2 | **74** |
| D2 housing cradle + tab clip | 19 | 15 | 13 | 7 | 6 | 3 | **63** |
| D3 lens collar bearing (LCB) | 24 | 12 | 6 | 9 | 8 | 1 | **60** |

**Recommendation:** D1's architecture (the lens is carried on its own fixed barrel by a tub-grounded collar; the
camera hangs on the lens and touches nothing), with the fixes and grafts in s5. D2 becomes the documented Plan B if
MP-LENS shows the Kowa's dia 42 knurl is not fixed. The J7 real-camera re-model (s6 phase 1) is common to every
design and must come first.

## 2. Facts I verified myself

1. **The D2 camera stack is wrong** (`layout.py:202-217` against `research/m12-drawings/gs_side.png`, read at
   10.05 px/mm). From the front the drawing shows: a dia 30.75 straight-knurl element 5.8 long (the C-CS adapter),
   then a dia 36 scalloped element 1.2 thick (the back-focus ring head, BFAR), housing 10.35, PCB 1.4, cover 6.49.
   D2 models a dia 36 x 5.8 ring, then a dia 30.75 x 5 "CS ring", then a 5 mm adapter, so its C flange (+10.6) is
   about 9-10 mm too far forward. Every lens moment arm in the brief is therefore about 8-10 mm too long.
2. **The housing is round, r about 17.7** (side view, top edge 17.7 above the axis), so it passes through the dia
   36.5 bore. Only the top split tab (top about r 22.2, 10.16 wide) and the tripod block reach the wall. There is no
   39.5 square "land" at the front; 39.5 is the plastic rear cover.
3. **The tripod block must come off for every design.** Its bottom is about 30.3 below the axis (z about 29.7) and it
   runs 12.04 back from the housing front plane. Seated at x -5.2 it occupies x -17.2..-5.2, z 29.7..42, which
   overlaps the Active Cooler box (x <= -9.5, top z 36.3), `ko_exhaust` and the Pi 5 envelope. The proxy
   (`cots.py:147-159`) omits it, so today's `camera_in` pass is not evidence.
4. **The 2 pins locate nothing on the real part.** Tips at x -8.2; the real PCB front is about x -15.5 when the
   housing front plane sits at x -5.2.
5. **With the real camera, today's J7 can rock about 5 deg nose-down** (tab pivot about z 80, keeper 1.23 behind the
   real cover, 14 below the pivot). That, not mount creep, is the first-order "sag".
6. **The mount is aluminium** (dossier_external s1; I accept the sources). The creep-prone link inside the camera is
   the housing-to-PCB joint: 2 M2 socket screws with nylon washers on a sticky gasket. The brief's and
   LENS-ZOOM-CANDIDATES' "plastic mount" premise is wrong, and the user should be told.
7. **Pi drop limit** (`INSERTIONS['pi_in']`, my probe): the stack descends at x offset -2.8 from z +80, so its front
   face sweeps x <= -8.35 over y -32.3..25.8 at every height. No tub feature on the front-wall inner face may reach
   behind x -8.35 in that y band. Probe results: D1 bosses (x -7.6..-5.2) 0 mm3; D2 pins (tips -8.2) 0 mm3; **D3
   boss_l1 + corbel 106 mm3** (worst at offset (-2.8, 2.1, 68)).
8. **The hood is an L profile** (`printed_hood._shell`: band + front plate extruded over the width). The plate has a
   free lower edge and no side walls.
9. **Fastener policy** (`FASTENER-POLICY.md` s B): joint gap closed by a screw <= 0.1; counterbore dia 7.0 because
   the bit envelope is dia 6.5; PT bosses 5 reuses. `SCREWS[...]['cbore']` supports only y or z ranges
   (`layout.py:424-433, 977, 1250`), so any X-axis screw needs an x range added.
10. **Arithmetic I re-derived:** Kowa weight 2.11 N; the split-clamp tilt capacity before an edge gaps is
    M = pi F L / 6 (linear axial pressure, cos-theta circumferential, p0 = F/(r L)); D1's 0.71 / 0.17 N m and
    D2's 7.9 N m nose-down capacity check out; D2's pin/screw ligaments (1.94, 1.86, 1.08) check out.

## 3. Refuted or corrected claims

| # | Source | Claim | Finding |
|---|---|---|---|
| R1 | brief, LENS-ZOOM-CANDIDATES | The GS lens mount is plastic and creeps | Aluminium housing and BFAR; the creep link is the M2 + nylon-washer + gasket joint to the PCB |
| R2 | brief | The bore catches the dia 36 ring after 0.25 | The dia 36 element is a 1.2-thick BFAR head that moves 0.75-0.8 per turn; the long element is the dia 30.75 adapter, about 2.9 radial clear. The mechanism does not exist |
| R3 | D3 s2.3 | boss_l1 sits in free zone F1, 0 mm3 | It blocks the Pi drop (106 mm3, my probe). D3 never swept `pi_in`. No tub boss deeper than x -8.35 is possible for y -32.3..25.8 |
| R4 | D3 s2.4 | Panel bosses 0.15 behind the wall, clamped by s_l2/s_l3 | The screws close 0.15 > the 0.1 policy limit |
| R5 | D3 s2.4 | Panel bosses print vertical with no issue | The bodies do, but their X-axis pilots are horizontal in the panel print: the weak case (OD, 40 % modifier, insert fallback) |
| R6 | D3 s5 | Optional lock-screw access hole in the panel at (x -7.8, z 80) | A dia 6.5 bit along -Y at z 80 spans z 76.75..83.25 and hits D3's own boss_l2 (z 70..78) |
| R7 | D3 s2.2 | The hood plate's lower section is held by 2.9/3.35 strips and the LCB lip | The plate is a free-edged L-profile; the 58 mm opening leaves the plunger guard, SD slot and exhaust slots on two 3 mm strips. Not acceptable for a part the user presses |
| R8 | D1 s2.2 | Washer seat dia 7.4 at x -5.2..-5.7 behind a hex AF 5.55 pocket opening at x -7.6 | An M3 washer (OD 7.0) cannot pass the hex: the 3 tub-pocket washers cannot be fitted |
| R9 | D1 s2.5 | Pinch head channel dia 6.0 | Below the dia 7.0 counterbore rule; the dia 6.5 bit envelope fails `check_driver` |
| R10 | D1 s2.5 | Pinch nut pocket in the Kowa tube; "the tube wall is the lug (>= 2.1)" | The Kowa tube is 5.8 long (x 2.7..8.5): round a dia 3.4 hole that leaves 1.2 in x, and an AF 5.55 pocket leaves about 0.1. It needs a local pinch boss |
| R11 | D1 s2.5 | Collar bore = band + 0.1 (0.05 radial) | Below FDM hole tolerance (layout LOCATE 0.15/side); the knurl turns inside it while the lens threads in. Use band + 0.3 (D3) |
| R12 | D1 s5 | Step 9: level on live view | Nothing is powered until step 10 (pack). Re-order |
| R13 | D1 s2.5 | Slit sits on a free 136 deg arc between TR and LL | TR is at 109 deg and LL at 316 deg (atan2(dz, dy)); the free arc that holds the slit (180 deg) is about 207 deg. The design still works (the long arc closes easily) |
| R14 | D1 s3.2 | The lip preload (10-15 N thermal) is concentric | Only if the lip face is square to the lens axis. A one-sided contact makes it up to about 0.25 N m on the adapter-BFAR thread. Make the lip a stop with a gap (s5) |
| R15 | D2 s2 | Cradle pin holes dia 2.2 at y +-16.5 in a cradle y +-18 | 0.4 wall to the side face (< MIN_WALL 1.2). Widen to +-19 |
| R16 | D2 s3 | Aluminium chain >= 2000 N m/rad | Unverified estimate. It ignores the BFAR fine thread (dia 28.8, about 1.7 wall, flank clearance taken up only by the split-tab pinch), which in D2 carries the full lens moment |
| R17 | D2 s2 | Clip hook 0.3 over the housing | Assumes dia 35; the drawing reads about dia 35.4, giving 0.1 |

## 4. Per-design review (load path, stress, creep, tilt)

### 4.1 D1: tub-grounded lens collar, floating camera (74)

- **Load path.** Lens fixed band -> printed collar -> 3 M3 bolts + 1 compression foot -> tub front wall. The camera
  hangs on the lens through adapter and BFAR. Every camera joint (lens C thread, adapter threads, BFAR thread,
  housing, M2/gasket joint, PCB) carries only the module's own weight: about 31 g at about 6.5 mm, 0.002 N m static
  and 0.01 N m at 5 g, plus FPC drag up to 0.006 N m. That is 10-40x below today's figure, and independent of the
  lens. Focus- and zoom-ring torque also goes to the collar, not through the unlocked adapter threads. This is the
  load path Raspberry Pi's engineer recommends for heavy lenses.
- **Stress and creep.** Sustained stresses are tiny (wall bending 0.2 MPa for the Kowa static). The two real creep
  items are the bolt/pinch preloads (head bearing up to 16 MPa initially) and the clamp's thermal behaviour, which D1
  did not analyse:
  - ASA (about 90e-6/K) on an aluminium band (23e-6/K) loses hoop strain (alpha_ASA - alpha_Al) x dT = 0.0017 at
    +25 K, which is about 3.4 MPa of the 4.8 MPa initial hoop stress;
  - the Kowa clamp keeps about 0.2 N m of tilt capacity warm, which covers the 0.049 N m static moment at the band
    but not a 5 g knock. The lens then rocks elastically inside the collar (aim only, recovers).
  - Gate it (G-COL-1 at 50 C), and keep a lower-CTE collar material (PC, ASA-CF) as the upgrade path.
- **Tilt.** Focus tilt from the support: < 0.02 deg static, about 0.06 deg at 5 g (residual module weight only).
  Aim: about 0.07-0.19 deg/N m through the 2.5 wall (estimate; D3's FE gives 0.08 for a full-face disc).
- **Strengths.** It is the only design that re-datums J7 on the real camera end to end (lip, counterbore, keeper,
  roll fin, FPC). Its tub bosses respect the Pi drop. Steel nuts give unlimited reuse for collar swaps. The hood
  plate stays continuous. The turret goes, and the collar takes its look and envelope. Kowa balance about +1.6.
- **Flaws.** R8-R14, a fastener-policy exception (M3 + nuts), one collar per lens, a short Kowa band (5.4) whose
  "fixed" status is inferred, roll set optically, and the largest change set.

### 4.2 D2: cradle in place of the tripod block, clip on the tab (63)

- **Load path.** Lens -> C thread -> adapter (2 threads, unlocked) -> BFAR thread (locked by the split tab) ->
  aluminium housing -> tab face and cradle face on the wall, 3 PT screws preloaded. The PCB joint carries 0 % of the
  lens moment. This is a real fix for sag: metal does not creep, and the preloaded 40 mm couple stops the rocking
  (7.9 N m nose-down at 100 N per screw after relaxation).
- **What it does not remove.** The full lens moment and every hand load still pass the BFAR fine thread and both
  adapter threads. The stiffness of that chain is a guess (R16). Focus-ring torque still works on the unlocked
  adapter threads. For a 600 g zoom at 5 g that is about 1.8 N m through camera threads, which is the regime where
  Raspberry Pi advises supporting the lens instead.
- **Robustness.** It depends on two unknowns no other design needs: that the tripod block's 2 screws thread into the
  housing (not the PCB), and the block's mating faces (the cradle copies them). It also depends on the tab's rear
  face (clip) and on 0.25-0.3 insertion margins read off a drawing. Plan B (a friction collar on the housing) is
  weaker and creep-prone.
- **Strengths.** No per-lens part, so lens swaps are unchanged. PT screws only. The PCB is fully bypassed. Roll is
  set by pins (+-0.5 deg). Lowest new-part mass. Thorough insertion probes.
- **Flaws.** R15-R17. The hood plate becomes part of a camera clamp stack. Nose-up capacity (about 2.3 N m) only
  just covers M_d. The cradle sits 0.45 over the cooler.

### 4.3 D3: lens collar bearing on the wall, panel-anchored (60)

- **Load path.** It has the same bypass idea as D1 and the best wall interface: a 57 mm full-face land, with a
  plate FE of 0.079 deg/N m that I find plausible in order of magnitude. It also has a good per-lens sleeve:
  band + 0.3, a travel allowance and a relief slot.
- **But:**
  - its anchor boss blocks the Pi drop (R3: fatal as specified);
  - two of the three anchors are panel bosses, so the lens support is undone whenever the panel comes off
    (R4, R5);
  - the hood plate loses its middle (R7);
  - the numbers are in the wrong stack;
  - J7's real float and roll are left to "the J7 owner", and the module stays seated on the wall. That seat becomes
    a parallel path whenever the short Kowa sleeve gaps.
- **Worth keeping.** The `lens_support` and `load_path` checks, `LENSES[...]['support']`, the thumb-screw sweep
  keep-out, the band + 0.3 bore, the thermal-clearance remark and the clear statement of the zoom requirement (a fixed
  section >= 15 mm).

## 5. Recommendation and grafts

**Final design: "J7-R float + lens collar"** = D1's architecture with these changes:

1. **Lip as a stop, not a contact** (fixes R14). The lens's axial position is set by its own knurl rear corner
   seating on the collar's internal 45 deg cone. That leaves the BFAR face G_LIP = 0.3 behind the lip, so the camera
   body and BFAR touch nothing in the final state. The lip is only the step-7 insertion stop and a shock stop.
2. **Square nuts in slots open to +Z, no inner washers** (fixes R8). DIN 562 M3 nuts sit in slots inside the
   2.4-deep tub blocks plus the wall, within the Pi-drop limit. TL/TR are trapped by the hood band after step 5;
   LL is held by crush ribs, then partly covered by the panel locate rib.
3. **Pinch boss** (fixes R9, R10): local boss x 0.3..10.0 on the -Y side, a dia 7.0 head channel, M3 x 16 and a
   square nut in a side slot.
4. **Collar bore = band + 0.3** (D3 graft; fixes R11).
5. **Level after power** (fixes R12): the pinch is snugged at step 9 with the cover touching the roll fin; it is
   levelled on live view after step 10.
6. **Thermal clamp analysis plus G-COL-1 at 50 C** (D3 remark, quantified in s4.1); PC or ASA-CF collar as the
   upgrade path.
7. **D3 grafts:**
   - `LENSES[...]['support']`;
   - the corrected Kowa segments;
   - the `ko_lens_thumb` sweep keep-out;
   - `check_lens_support` (FAIL for any lens without a support);
   - the `LOAD_MODEL` load-path report;
   - a `mass_com` assertion;
   - the zoom rule: a fixed section >= 15 mm long;
   - "pinch is the last operation".
8. **D2 grafts:**
   - the real-camera proxy as sub-solids with `s` and t ranges;
   - the BFAR/adapter clearance zones checked at s_min and s_max;
   - a synthetic-FAIL regression test for the float check;
   - the bench back-focus procedure;
   - the G-LENS dial-indicator protocol;
   - the whole cradle + clip as **Plan B**, used only if G-LENS shows the Kowa knurl moves, with R15 and R17 fixed.

**Decision tree:**
- MP-CAM shows the tripod block will not come off: no current J7 works (cooler collision). Escalate: re-layout
  the axis or the Pi stack.
- MP-LENS shows the knurl is fixed: build this design.
- The knurl moves: build D2 (Plan B).
- Phase 1 below is the same in every branch.

## 6. Implementation spec (assembly frame, mm; all values are layout parameters)

### 6.0 Order
- **Phase 0 (bench, before any print):** MP-CAM extended (G-CAM-1), MP-LENS (G-LENS).
- **Phase 1 (CAD, common to every branch):** the J7-R real-camera model and the lens moved back.
- **Phase 2 (CAD):** collar, nut blocks, hood holes, roll fin, keeper, screws, checks.
- **Phase 3 (bench):** G-COL-1, G-CAM-2, then the G-LENS load test.
- Build only through `run_locked.py`.

### 6.1 layout.py
**`CAM_R`** replaces `CAM` (keep `CAM` as an alias dict, so that `MATES`/`COTS` lookups fail loudly if missed):
- `s_nom` 1.25, `s_min` 0.0, `s_max` 3.0: BFAR screw-out from fully in (MP-CAM).
- `LIP_X` -4.3 (tub lip rear face, insertion stop); `G_LIP` 0.3 (BFAR face to lip in the final state).
- `ADAPTER_L` 5.0.
- `C_FLANGE_X` = `LIP_X` - `G_LIP` + `ADAPTER_L` = **+0.4**; `CS_FLANGE_X` = `BFAR_X` = -4.6.
- `bfar` CYL r 18.0, x -5.8..-4.6. `adapter` CYL r 15.375 / r_in 12.7, x -4.6..+0.4.
- `HF_X(s)` = -5.8 - s (housing front plane). `housing` CYL r 17.7, x HF_X-10.35..HF_X.
- `tab`: B(HF_X-5.02, HF_X, -5.08, 5.08, 77.0, 82.2), slot 0.8 at y 0. `lock_screw` axis Y at (HF_X-2.5, z 79.4),
  head side from MP-CAM.
- `pcb`: B(HF_X-11.75, HF_X-10.35, -19, 19, 41, 79). `cover`: B(HF_X-18.24, HF_X-11.75, -19.75, 19.75, 40.25, 79.75).
- `tripod_block` = None (removed at bench step B0).
- `bore_cb` teardrop r 18.75, x -5.3..-4.3, up +Y. `lip` teardrop r 16.2, x -4.4..-2.6, up +Y.
- Delete `pins`, `pin_d`, `pin_len`, `pin_tip_chamfer` and `wall_bore_d`.
- `keeper` B(-30.87, -27.54, 4.0, SPLIT, 66.0, 76.0): 0.5 behind the cover rear at s_max (-27.04).
- `insert` unchanged: path -Y 2 high, down 2, +X 11.1. The adapter rides along.

**`LENSES`:**
- Kowa segments (r, from the flange): (12.7, -6.7, 0, 'C thread'), (15.75, 0, 2.2, 'rear spigot'), (21.0, 2.2,
  7.6, 'fixed knurl'), (19.5, 7.6, 10.6, 'groove'), (20.85, 10.6, 22.6, 'focus ring'), (19.3, 22.6, 30.9, 'label
  barrel'), (19.25, 30.9, 36.6, 'iris ring'), (20.75, 36.6, 41.7, 'step'), (27.0, 41.7, 50.5, 'front barrel'),
  (23.0, 50.5, 56.6, 'front').
- Replace `lock_screws` with `thumb_screws` [(14.4, 'focus'), (33.0, 'iris')], sweep r <= 24.0 over +-2.0.
- Add `support` = dict(r=21.0, x0=2.2, x1=7.6, kind='knurl', status='drawing') and `collar` = dict(bore_d=42.3).
- Fujinon: `support` (19.5, 2.0, 7.8, status 'assumed').
- Optional `computar_h6z0812`: 305 g, CoM 40 (guess), support (24.25, 1.0, 25.5), collar bore 48.8.

**`COLLAR`** (Kowa values; lens-side x from `C_FLANGE_X`):
- `flange_x` (0.3, 2.7).
- `feet` dia 8.0, x -2.7..+0.3, at TL (11, 92), TR (-11, 92), LL (24.5, 36) (bolted) and LR (-19, 44) (compression).
- `tube` r 30, x 2.7..(C+band_x1+0.4) = 8.4. `bore` r 21.15. Cone 45 deg from r 18.7 at x 0.3 to r 21.15 at
  x 2.75: the knurl corner seats at x 2.6, which is C + 2.2.
- `slit` 2.0 (z 59..61) on the -Y side, bore to outside, through tube and flange.
- `pinch_boss` B(0.3, 10.0, -31.5, -22.0, 48.0, 72.0), blended. `ear_top` y -16..16 to z 96.4. `ear_ll` R 4.4.
  45 deg gussets with driver channels dia 7.5 along X at TL/TR/LL.

**`HOOD`:**
- Delete `turret` and `turret_b`.
- `collar_holes` dia 9.0 at TL/TR/LL/LR.
- `cam_roll_fin` B(-23.5, -19.5, -22.8, -20.55, 41.0, ZT1), webs B(-23.5, -19.5, -27.6, -22.8, 44.5, 48.5) and
  (..., 75.0, 79.0).

**`TUB_NUT_BLOCKS`** {TL, TR, LL}:
- block B(-7.6, -5.2, yc-4.4, yc+4.4, zc-4.4, zc+4.4), 45 deg underside on the -Y face;
- through hole dia 3.4, x -2.6..-7.7;
- square-nut slot x -4.4..-6.3, y yc+-2.85, from zc-2.85 out through the +Z face, 2 crush ribs 0.15 on the y faces.

**`SCREWS`** (new block; repeat the `COTS['pt_screws']` recount line). Add `kind` ('PT' | 'M3') and an `x`
option to `cbore`.
- s_c1/s_c2/s_c3: kind M3, ISO 7045 M3 x 12 PH1 A2 + ISO 7089 washer under the head. joins (lens_collar, tub);
  into 'tub nut_c1..3'; head_part lens_collar; axis (-1, 0, 0); head_point (3.2, yc, zc); tip (-8.8, yc, zc);
  step 8; torque 0.2 N m.
- s_c4 (pinch): kind M3, M3 x 16. joins (lens_collar,); into 'lens_collar nut_c4'; axis (0, 0, -1); head_point
  (5.2, -26.5, 66.0); tip (5.2, -26.5, 50.0); cbore lens_collar d 7.0, z 66.0..74.5; step 9; torque 0.15-0.2 N m.
- Nut slot for c4: x 2.35..8.05, z 51.0..52.9, open to the boss -Y face.

**`COTS`:**
- gs_camera: box from the cover rear at s_max to `BFAR_X`.
- c_cs_adapter: box x -4.6..0.4, step 7.
- lens: box from C-6.7.
- nut_c1..c4: DIN 562 M3, 0.5 g, steps 3/3/3/9.
- m3_hw: 4 screws + 3 washers, about 4 g.

**`PARTS['lens_collar']`:** module `printed_collar`, ASA black, face_down '+X', owner 'hood_panel', infill 'small',
supports none, envelope B(-2.7, 10.0, -31.5, 30.0, 30.0, 96.4) (Kowa).

**`MATES`:**
- tub/gs_camera: contact -> **clearance**.
- tub/c_cs_adapter: clearance.
- lens_collar/tub: contact.
- lens_collar/hood: clearance.
- lens_collar/lens: clearance ("pinched in service").
- tub/nut_c*: press.

**`STEPS`:**
- 3 adds nut_c1..c3.
- 7 adds c_cs_adapter.
- 8 adds lens_collar and s_c1..s_c3.
- 9 adds nut_c4 and s_c4.

**`INSERTIONS`:**
- camera_in moving += c_cs_adapter.
- collar_on (step 8): [(25, 0, 0), 0].
- lens_in (step 9): [(30, 0, 0), 0].

**`REMOVALS` / `LATCH_FREE`:**
- collar_off: reverse of collar_on; unscrew s_c1..s_c3; off lens and s_c4.
- hood_off off += lens_collar, s_c1..s_c3.
- camera_out off = panel set + lens (the adapter stays on the camera and passes back through the lip).
- LATCH_FREE lens: "loosen s_c4 one turn, unscrew". nut_c*: "trapped; not removed in service".

**`KEEPOUTS`:**
- `ko_lens_thumb`: annuli r 19.25..24.0 at C + 12.4..16.4 and C + 31.0..35.0.
- Re-derive `ko_fpc_cam` from the cover rear at s_max.

**`LOAD_BEARING_PARTS`** += lens_collar.

**`CRITICAL_JOINTS['J7']`:** parts (tub, hood, panel, lens_collar). Required probes:
- tub_lip_land (land, 1.6);
- tub_nut_front_skin_TL/TR/LL (boss, 1.7);
- collar_tube_wall (wall, 8.85);
- collar_flange (land, 2.4);
- collar_foot_LR (lug, 8.0);
- collar_pinch_jaw (lug, 5.0);
- hood_cam_roll_fin (wing, 2.25);
- panel_cam_keeper (lug, 3.33);
- tub_rib_l_tip.

**`SECTIONS`:** j7r-y0 and j7r-z92.

**`self_check`:** delete the 2 turret items. Add:
- G_LIP >= 0.05 at worst tolerance;
- counterbore - BFAR >= 0.675; lip - adapter >= 0.74;
- tab gap 0.6 + s >= 0.6;
- keeper - cover >= 0.5 at s_max;
- collar tube front <= first rotating segment - 2.0;
- nut blocks x >= -8.35 + 0.75;
- M3 head-to-tip = nominal length.

### 6.2 Printed parts
- **`printed_tub.py`**
  - Replace the lens-bore teardrop with the counterbore and lip teardrops (`dc.teardrop`, up +Y).
  - Delete the pins.
  - Add the 3 nut blocks with their slots and crush ribs. LL merges into rib_l; check the `tub_rib_l_tip` probe.
  - The `_right`/`_floor` auto-cuts do not trigger (axis -X).
- **`printed_hood.py`**
  - Delete `_turret`, `TURRET_*`, its fillets and the "turret upper half" tree-support note; supports become the
    housing strip only.
  - Cut the bore tool x -2.8..+0.3.
  - Add the 4 holes (dia 9.0, teardrop toward -Z) and the roll fin with its webs, hanging from the band.
- **`printed_panel.py`:** keeper and gusset from `CAM_R['keeper']`.
- **`printed_collar.py`** (new; pattern `printed_keeper.py`; imports math, cadquery, d2_common only)
  - `PRINT = {'lens_collar': dict(face_down='+X', supports=[], notes=...)}`; `build(L)` uses `L.LENS`.
  - Geometry: flange, feet, cone, tube, slit, pinch boss and nut slot, ear gussets and dia 7.5 channels, the c4 head
    channel dia 7.0, and 0.6 bed chamfers on the +X face.
  - Must build for every LENSES entry that has a `support`.

### 6.3 cots.py
- `gs_camera` from the `CAM_R` sub-solids at `s_nom`. Tag them 'body' (housing, tab, pcb, cover) or 'lensside'
  (bfar), so the checks can split them.
- `c_cs_adapter` as above.
- `lens_proxy` from the corrected segments, with the thumb screws at one clock and the sweep kept as a keep-out.
- Add `nut_m3_square`, M3 pan screw and washer builders, and their BUILDERS entries.

### 6.4 checks.py
1. **`check_j7_float`.** At s_min, s_nom and s_max: camera 'body' sub-solids >= 0.2 from every printed part (tab to
   wall 0.6 + s, keeper 0.5, fin 0.6, nut blocks >= 2). 'lensside' to tub: radial >= 0.5, axial >= 0.05. Any
   contact FAILs.
2. **`check_lens_support`.**
   - Every LENSES entry has a `support`.
   - The band lies inside the tube with >= 0.2 each end.
   - Bore minus band = 0.2..0.4 diametral.
   - Tube front <= first rotating segment - 2.0.
   - The collar overlaps `ko_lens_thumb` by 0 mm3.
   - FAIL if a lens has no `support`; WARN if status != 'measured'.
3. **`check_clamp_capacity`.** F0 = T/(0.2 d) = 250 N at 0.15 N m; F = 0.25 F0 (relaxation x asymmetry);
   M = pi F L/6, which is 0.177 N m for the Kowa. Assert M >= 1.5 x the static moment about the band centre; WARN
   if M < the 5 g moment. Report it per lens.
4. **`check_mount_polygon`.** TL, TR, LL and LR enclose the axis in yz; the distance from the axis to every edge is
   >= 10.
5. **`load_path` report** from `LOAD_MODEL` (k_wall 500 N m/rad, range 300-800; creep x 2.2). FAIL if the static
   aim after creep is > 0.15 deg.
6. **`mass_com`:** FAIL outside 0..+8 for the default lens, WARN for the others.
7. **Clearance zones.** Replace the two "ring in bore" zones with: "BFAR in tub counterbore" >= 0.675, "adapter in
   lip" >= 0.74, "adapter in plate bore" >= 2.5.
8. **M3 screws.** `check_driver`, `screw_pierces` and `interference` handle kind M3 (the s_ prefix already
   exempts them). `check_bosses` skips kind M3. A new `check_nut_slots` asserts the slot size, front skin >= 1.6,
   rear skin >= 1.2, bolt coaxial with the slot +-0.05, and the tip >= 1.0 past the nut.
9. **Existing sweeps** re-check `pi_in` against the new tub blocks and `hood_on` against the blocks and fin
   automatically. Add collar_on, lens_in, collar_off and the new camera_in.

### 6.5 Tests
- `test_tub`: lip and counterbore present, pins gone, slots, `pi_in` 0 mm3.
- `test_hood_panel`: no turret, 4 holes, fin, keeper position; lens/camera cylinders against the hood at the new
  stack.
- New `test_collar`: contract, bed face, both lenses build, bore-band, slit, pinch walls, nut slots, sweeps and
  removals.
- `test_r3_regressions`: a synthetic FAIL for each of: `check_j7_float` (keeper 0.2 from the cover),
  `check_lens_support` (a lens without support) and `check_nut_slots` (rear skin 0.8).

### 6.6 build_d2.py, make_tables.py, make_bom.py
- **build_d2:** EXPLODE lens_collar +X 40; STEP_VIEWS; the J7-R sections; `mass_com` runs for each lens with its
  collar.
- **make_tables:** an `estimate_volume('lens_collar')` branch (about 15 cm3); counts are +1 print, PT unchanged,
  +4 M3. Update the text lints.
- **make_bom:** LINES for M3 x 12 (3), M3 x 16 (1), ISO 7089 M3 (3), DIN 562 M3 (4); the collar as a printed row.

### 6.7 Docs
- **SPEC s9/s10:** the J7 contract becomes "the collar carries the lens; the camera hangs on it and touches no
  printed part; no chassis feature loads the PCB". Turret rows deleted.
- **DESIGN:** J7, parts, mass/CoM (Kowa about +1.5).
- **ASSEMBLY:** s6.8.
- **FASTENER-POLICY:** a new section, "M3 machine screws and square nuts (lens collar)". Rationale:
  - the Pi drop limits tub bosses to 2.4 deep;
  - collar swaps need unlimited reuse;
  - same PH1 and the M3 class of section E.
  Torques 0.2 / 0.15-0.2 N m.
- **PRINT-GUIDE:** collar print; hood without turret supports.
- **MEASURED-PARTS:** MP-CAM rewritten; MP-LENS; G-CAM-2; G-COL-1.
- **LENS-ZOOM-CANDIDATES "Load path":** correct the premise (aluminium mount; creep link = PCB joint) and record
  the adopted fix plus the zoom rule (a fixed section >= 15 mm).
- **HANDOFF, NOTES.**
- **Flag for candidate-fr1:** a Y-sliding hood must clear the collar feet (collar off first) and carry the roll
  fin.

### 6.8 Assembly text (steps)
- **B0 (bench, before 7):**
  1. Remove the tripod block (2 screws; bag them).
  2. Fit the C-CS adapter hand-tight.
  3. Fit the Kowa at infinity, f/1.8, aimed at a target >= 50 m away.
  4. Loosen the lock screw 1/4 turn, turn the BFAR to peak focus, tighten the lock screw, and check the 0.3 m mark.
  5. Record s = (BFAR protrusion ahead of the housing face) - 1.2.
  6. Remove the Kowa; leave the adapter on.
- **3:** press nut_c1..c3 into their slots until they bottom (test-thread an M3 from the front, then remove it).
- **7:** camera with its adapter, on the existing path, until the BFAR face stops on the lip.
- **8:** panel, then the collar (feet through the 4 hood holes), then s_c1..s_c3 from the front at 0.2 N m.
- **9:**
  1. Lens through the open collar into the adapter (the fin holds camera roll).
  2. Push the lens back until its knurl seats on the collar cone.
  3. Turn lens and camera together until the cover's -Y face just touches the fin.
  4. Snug s_c4 to 0.15 N m.
- **10:** pack and cap.
- **10b:** power on and check level on live view. If it is off, loosen s_c4 half a turn, turn, and re-snug to
  0.2 N m.
- **Lens swap:** loosen s_c4 one turn, unscrew the lens. Swap the collar only if the band differs (3 bolts).

### 6.9 Bench gates
- **G-CAM-1 (rewritten).** Measure:
  - BFAR head OD and thickness, and its exposed front annulus;
  - adapter OD, face-to-face (5.00) and band;
  - housing OD; tab width, height and rear face; lock-screw size and head side;
  - that the tripod block comes off with 2 screws and leaves nothing below r 18 in front of the PCB;
  - cover centring +-0.2;
  - s at Kowa infinity and the full s range; FPC exit.

  Pass: everything inside the `CAM_R` tolerances. Otherwise update `CAM_R` and re-run the suite before printing
  the tub, hood or collar.
- **G-LENS (extended).**
  - Kowa: the dia 42 knurl neither turns nor moves axially over full focus and iris travel (mark it and watch).
  - Knurl OD +-0.02; rear-face position from the flange +-0.1.
  - CoM by knife edge; thumb-screw head height.
  - If the knurl moves, use Plan B (D2 cradle + clip).
- **G-COL-1 (new).** Kowa collar on a tub-front coupon (2.5 wall, one nut block) and a plate coupon, pinch at
  0.15 N m. Pass:
  - roll slip >= 1.0 N m; axial pull >= 50 N;
  - 1.1 kg (5x Kowa) at the lens CoM: lens-front deflection <= 0.05 mm, returning to <= 0.01;
  - after 24 h at 50 C under the static load: change <= 0.02 and roll slip >= 0.5 N m;
  - 20 pinch cycles without a crack.
  - If it fails warm: PC or ASA-CF collar, or a spring under the pinch head.
- **G-CAM-2 (new).** Lens clamped in the collar coupon, camera hanging; 0/50/100 g hung on the cover. Pass: the
  edge-focus change is < 1/4 of the depth of focus (about 0.05 deg); repeat after 1 h at 50 C.
- **G-W11** unchanged; it sets the creep derating.

### 6.10 Plan B (only if G-LENS fails): D2 with fixes
- Cradle widened to y +-19 (pin-hole walls >= 1.2).
- Hook gap checked against the measured housing OD (>= 0.3).
- Same J7-R phase-1 model; turret deleted; 3 PT screws through hood and tub.
- `check_j7_float` replaced by D2's `j7_load_path` (PCB/cover >= 0.5 from every printed part; capacity >= 1.5 x the
  5 g moment).
