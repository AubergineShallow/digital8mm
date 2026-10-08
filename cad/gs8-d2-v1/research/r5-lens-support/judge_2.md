# Judge 2: heavy-lens sag fix, review of designs 1-3 (manufacturability and assembly lens), 2026-10-06

Read-only review. Nothing in the repo was edited or built. My one probe is `scratchpad/sag/j2/probe_j2.py` (CadQuery,
D2 `layout.py` + `cots.py`). Frame: +X forward, +Y left (panel), +Z up, lens axis (y 0, z 60), units mm.

## 0. Verdict

| | D1 lens collar + floating camera + BFAR lip (M3 + nuts) | D2 housing clamp (cradle replaces tripod block, clip, 3 PT) | D3 lens collar bearing (LCB) on tub wall + panel tie |
|---|---|---|---|
| bypass (30) | 88 | 75 | 85 |
| alignment (20) | 60 | 80 | 70 |
| buildability (20) | 38 | 66 | 50 |
| robustness to camera internals (15) | 45 | 50 | 65 |
| generality 300-600 g (10) | 80 | 50 | 85 |
| impl_risk in this CAD (5, higher = safer) | 30 | 60 | 45 |
| **total** | **62** | **67** | **70** |

**Recommendation: build D2's housing clamp as the J7 fix for the heavy lens now (the Kowa), with the grafts in s4,
and keep D3's set-then-lock lens collar as the documented, reserved extension for lenses over 300 g.**

Why D2 wins on my lens although D3 scores higher on the weighted table:
- D3 (and D1) solve the lens side only. Neither gives the *real* camera a defined J7: the D2 pins end at x -8.2,
  about 7.4 mm short of the real PCB (front about x -15.55), the tripod block must come off, and with it off the
  module rests on one tab and can sag about 5 deg onto the keeper. D3 explicitly leaves this to "J7's owner". D2 is
  the only design that defines a seat, a location and a preload for the real camera, so some form of D2 is needed
  in every outcome.
- The real creep path is the housing-to-PCB joint (2 M2 screws, nylon washers, sticky gasket), not a plastic mount.
  Holding the aluminium housing (D2) takes the lens moment off that joint completely, the same way the camera's own
  tripod block does. That is the sag fix for the 215 g Kowa.
- D2 uses only the existing PT 3.0 x 12 / PH1 machinery, adds two small prints, drives every screw from the front at
  step 7 with a straight driver, and leaves lens swaps unchanged (no per-lens part, no pinch, no re-levelling).
- D1/D3 hang the camera on the lens. That needs a per-lens collar on a band whose non-rotation is inferred from a
  photo (Kowa dia 42 knurl), and a short 5.4 mm band that gaps at about 0.16 N m after relaxation (5 g knock 0.25).
- Heavy zooms (305-600 g) are the real reason for a lens-side support. D3's LCB is the best form of it. Add it when a
  zoom is chosen, as a second support that is pinched last onto the already-clamped camera (cine "set in place").

## 1. What I verified in the code (claims the designs rely on)

| Claim | Where | Result |
|---|---|---|
| Pins dia 1.9, tips at x -8.2 | `printed_tub.py:195-198` (from x -5.15, 2.65 + 0.4 cone) | confirmed; real PCB front about -15.55, so the pins locate nothing (D1, D2) |
| Real tripod block (bottom z 29-30, x -5.2..-17.24) collides | `layout.py:477-487` pi5 box z <= 36.1 (x <= -5.55), cooler box z <= 36.3 (x <= -9.5), `ko_exhaust` z <= 36.2 | confirmed: about 6 mm overlap; the block must come off for every design |
| Module sag with block off | keeper z 66..76, tab pivot z about 80-81.6, real cover-to-keeper gap 1.23 | 1.23 / 14 rad = 5.0 deg (D2) confirmed |
| Real-stack Kowa hits the turret | C flange about +2.25: dia 42 knurl x 4.45..9.85 vs turret bore r 18.25 to x 8.5 (`layout.py:98-99`) | confirmed (D3 probe 1169 mm3 plausible); the turret must go in all three |
| D2 cradle clearances | Pi box top 36.1, cooler 36.3, exhaust 36.2 vs cradle bottom 36.75 | 0.65 / 0.45 / 0.55 confirmed |
| D2 cbore vs hood bore teardrop flank | flank line y - z = -33.48 for r 18.75 + flat 1.0; cbore r 3.5 at (13.5, 40.5) | 1.08 confirmed |
| D2 screw stack | head x -0.5, plate 2.0 + pad 0.15 + gap 0.05 + wall 2.5, tip x -12.5 | engage 7.3, pilot 8.3 = engage + 1 confirmed |
| Driver audit scope | `layout.screw_audit_set` = every add of the screw's own step (`layout.py:777-780`) | D2 (step 7, no turret, no lens): free. **D3 fails as written** (lens is in step 9 adds) |
| Auto screw cuts | `printed_tub._right` only for axis (0,1,0) (`printed_tub.py:328-333`); `printed_panel._cuts` treats every `into 'panel <PANEL_BOSSES key>'` as a +Z screw from the boss bottom (`printed_panel.py:216-230`) | D2's explicit cuts are right; **D3's "pilots from the existing rule" is wrong** |
| Contract rule 5 | `MODULE_CONTRACT` item 5 and `test_tub.py:42-47` (printed part vs every non-mate COTS **box**) | **D1's LL nut boss overlaps the pi5 COTS box by 29.35 mm3** (probe); 0 against the pi5 proxy shape |
| Fastener policy | `FASTENER-POLICY.md` C (no threadlocker on ASA; T_spec 0.35-0.5; no re-torque), E (M3 x 10 ISO 7045 PH1 is the only M3), G (PH1 only; no hex/L-key) | used below |
| Hood front-top chamfer | `printed_hood.py:131-133`: (x 0, z 97) to (x -3, z 100) | D1's TL/TR dia 9 holes leave 0.5 on the front face |

Also confirmed from the dossiers and the code: no check models load or preload (`mass_com` only reports); the camera
proxy is a box plus two tubes; the turret upper half needs tree supports today (`printed_hood.py:21-27`), so deleting
it helps the hood print in all three designs.

## 2. Design reviews

### 2.1 Design 1: tub-grounded lens collar, floating camera, BFAR lip, M3 + captive nuts (62)

**Strengths.**
- The fullest bypass: after the pinch, the housing/gasket joint and the BFAR thread carry only the camera's own
  34 g. Axial datum on the BFAR face makes C flange = lip + 5.000, independent of back focus.
- Careful real-stack reading (C flange about +0.7, s parameter), roll-fin idea, collar-per-lens table, G-CAM-2 load
  test that compares PCB-held against lens-held.
- Deleting the turret removes the hood's tree support.

**Refuted or wrong.**
1. "Each boss in the final state 0 mm3": the LL nut boss (OD 8.8 at y 24.5, z 36, x -7.6..-5.2, teardrop apex -Y)
   overlaps the **pi5 COTS box by 29.35 mm3** (probe). It misses only the pi5 proxy shape. `MODULE_CONTRACT` item 5
   and `test_tub` (`cots_box_overlaps`) treat the box as binding.
2. Hood foot holes TL/TR (dia 9 at z 92) leave **0.5 mm** to the front-top chamfer on the plate face (z 97), below
   MIN_FEATURE 0.8.
3. Collar bore = band + 0.1 (**0.05 radial**), below FDM LOCATE 0.15. A printed dia 42 bore is not held to that; the
   lens may not enter, and a slit ring bolted on both sides of the slit (TR and LL) cannot be spread to help.
4. Lip "x -4.3..-2.6": the tub wall outer face is x -2.7 (`XT1`); -2.6 is inside the 0.2 tub-hood gap. s_c1..3 tip
   "x -8.8" vs 2.7 - 12 = -9.3. (Minor.)
5. Assembly order: at step 7 the camera "stops on the lip", but the lip is a forward stop only. Nothing seats,
   locates or preloads the camera from step 7 to the pinch at step 9 (pins deleted, keeper 0.5-2.25 behind, fin on
   one side). The C-mount lens is then threaded blind, through the collar, into a loose camera: cross-thread risk.
6. Captive M3 thin nuts go into hex pockets **open toward -X** at step 3 and are not retained when the pull-in screw
   is withdrawn. Steps 4-7 (Pi drop, hood, EVF, camera) follow before the collar screws catch them at step 8. D1's
   own text: a lost nut means hood off.

**Buildability (my lens).**
- New fastener family (M3 x 12 + ISO 4035 thin nuts + washers, 14 pieces) outside policy A; `check_bosses`,
  `check_driver`, `screw_pierces`, BOM, tables and policy all need an M3+nut kind. Re-torque of the pinch head seat
  is against policy C.
- Collar print (+X face down, 45 deg ear gussets, feet at the top) is fine. Tub lip and counterbore are fine
  (teardrop up +Y). Roll fin hanging from the hood roof prints vertically (2.25 x 4 x 56: slender, 2 webs).
- Per-lens collar; a lens swap that changes collar is 4 screws plus re-levelling on live view.
- Largest change set of the three (new part, new hardware kind, tub, hood, panel, cots, 4 steps).

### 2.2 Design 2: housing clamp (cam_cradle in the tripod-block seat, cam_clip over the tab, 3 PT from the front) (67)

**Strengths.**
- Correct diagnosis: the compliant, creep-prone link is housing -> PCB (M2 + nylon washers + gasket). Holding the
  aluminium housing takes the lens moment off it entirely, as the camera's own tripod block does.
- Exact constraint: x, pitch, yaw on two faces in the housing front plane (tab + cradle); y, z, roll on 2 pins in the
  cradle; nose-up on a hook 0.1 behind the tab. Nose-down (the only sustained case) is a preloaded couple of 39.7:
  about 7.9 N m with 100 N per screw after creep; plastic sees compression only (<= 1.7 MPa sustained).
- Pure PT 3.0 x 12 / PH1, 3 screws, all driven from +X at step 7 with no lens, adapter or turret in the way. Two
  small prismatic prints (2.7 g, 1.1 g).
- Lens swaps unchanged (C thread only). Insertion probes (camera_in, clip_in, panel_on 0 mm3) with stated margins.
  The 3 screws also fasten the hood plate's lower half to the tub.

**Refuted or wrong.**
1. Cradle pin holes dia 2.2 at y +-16.5 in a cradle y +-18: **0.4 mm outer wall** (< MIN_WALL 1.2). Moving the pins
   inward is not possible (the pin edge would come within 0.8 of the tub bore teardrop flank). Fix: cradle y +-19.5
   (wall 1.9); room exists (rib_l y >= 24.1, hood post y <= -27.6, panel locate rib y >= 24).
2. "Low-strength threadlocker" on the block screws: they pass through printed ASA; FASTENER-POLICY C bans
   threadlocker on ASA (stress cracking).
3. "Camera key or PH1" for the block screws: the factory screws are hex socket; policy E/G exclude hex keys. PH1
   ISO 7045 replacements of the measured thread must be mandatory, not optional.
4. Hood rear pads 0.15 proud leave **0.05** drop-on clearance over a 60 mm vertical drop (SLIDE is 0.25). Use 0.10
   pads (0.10 clearance; the screw closes 0.10).
5. "The Kowa's dia 42 ring sits 1.55 ahead of the heads": heads end x +1.9, ring starts x 4.45 (C flange 2.25 + 2.2):
   2.55. Conservative, harmless.

**Buildability (my lens).**
- Cradle: face_down +X, datum face on the bed, pilots vertical in print (strong PT case). Clip: face_down +Y, pilot
  horizontal (weak case; policy B modifier, insert fallback, G-PT-1 coupon).
- Bench step: tripod block off (one hex key, once, at the bench: policy F exception), cradle on with PH1 screws while
  pressed on a flat, back focus set and locked. Then camera + cradle in as one, clip in, 3 screws.
- Insertion margins 0.25-0.3 (rib_l, `ko_run_cross`) come from drawing reads; re-run after MP-CAM.
- The cradle copies an unmeasured interface (angled shoulders, 2 screws); measurable on receipt. If the block is
  integral, every design needs a new answer (D2 Plan B collar, or an axis/Pi move).
- In-body back focus only with the panel off and the lock-screw head on +Y; otherwise bench (as D1).
- No lens support for zooms (D2 says so): 600 g rides on the BFAR thread and the housing (metal; strength fine) and
  the aim stiffness is the 2.5 wall under a 40 mm footprint: about 0.36-0.72 deg/N m, 0.6 deg under a 1.6 N m hand
  load (transient, aim only).

### 2.3 Design 3: Lens Collar Bearing on the tub outer face, tied to the panel (70)

**Strengths.**
- Best structural analysis: plate FE of the front wall (57 mm disc 0.079 deg/N m vs 0.48-0.74 for an r 20 seat), the
  free left wall edge tied to the panel, a long sleeve for the Computar's dia 48.5 fixed barrel.
- Set-then-lock: the pinch is the last operation, so it cannot force lens-sensor geometry.
- LCB print is clean: rear face = datum = bed face, no supports, hoop stress in-layer; the relief slot makes the
  sleeve a low-force C-ring. Hood without turret prints without supports (27 mm bridge).
- Lens-side dimensions derive from C_FLANGE_X and a `support` band, so a stack correction is a reprint of one part.
  Corrected Kowa segment table; `ko_lens_lock_sweep`.

**Refuted or wrong.**
1. "Pilots come from the existing `_cuts` 'panel ...' rule": `printed_panel._cuts` treats every
   `into 'panel <PANEL_BOSSES key>'` as a +Z screw from the boss bottom (top = (tip x, tip y, boss z0), depth =
   tip z - z0 + 1). For s_l2/s_l3 (axis -X) it would cut a wrong vertical 5 mm pilot and no X pilot.
2. s_l1..s_l3 at "step 9, lens not yet fitted": `screw_audit_set` takes every add of step 9, the lens included, so
   the driver audit runs against the lens proxy (bit at z 85-92 and the dia 30 handle overlap a Kowa of r 27). The
   step must be split (LCB + s_l1..3 before the lens step).
3. s_lp at 0.25 N m is outside policy C (0.35-0.5); a "snug" class needs a policy entry and a coupon.
4. "J7 gives >= 0.45 mm float; pins dia 1.6 in the dia 2.5 holes": on the real camera the pins end about 7.4 mm in
   front of the PCB and key nothing; roll and position before the pinch are undefined ("tines beside the top tab" is
   not designed). D3 relies on a J7 it does not provide.

**Buildability (my lens).**
- The hood plate gets a dia 58 "D" opening plus 3 ear notches. The lower plate (plunger well, guard, SD slot, exhaust
  slots) then hangs on a 2.8 strip on the left (y 32.2..35 at the S2/S3 notches, less the R1.4 edge round) and a
  3.35 strip on the right that runs into the out_corner slot mesh (1.4 webs). It prints, but it is a floppy flap.
- Panel tie: s_l2/s_l3 thread into panel bosses, so every panel removal (camera, hood, EVF service) needs the lens off
  and 2 LCB screws out, and each cycle spends one of the 5 PT reuses of those horizontal-in-print pilots.
- Per-lens LCB (11.6-23 g) and a pinch PT screw threaded into the LCB itself (horizontal in print, re-pinched at
  every lens swap: 5-reuse limit per LCB).
- In-body back focus at step 7 needs live view with the panel off (bench supply): acceptable.

One more D2 defect found while writing the spec: the hood cbore (dia 7 at (+-13.5, 40.5)) leaves a **1.08 web** to the
hood bore's truncated teardrop flank, below MIN_WALL 1.2 (D2 quotes 1.08 as a pass). Moving the two lower stations
to **(+-14.0, 40.5)** gives 1.44 (flank line y - z = -33.48; distance 4.94 - 3.5) and keeps every other margin (tub
hole to the tub teardrop 3.24, cradle pilot wall 2.5 below / 4.25 outside, out_corner 3.5).

## 3. Recommendation and grafts

**Final: "J7-H" = D2's housing clamp, corrected, plus grafts.** It fixes the heavy-lens sag for the Kowa now:
- lens moment path: lens -> adapter -> BFAR (locked) -> aluminium housing -> tab face (top) + cradle (bottom,
  preloaded by 2 PT) -> tub front wall. The PCB, its 2 M2 screws, nylon washers and gasket carry only the PCB +
  cover (about 10 g) and the FPC: about 0.0005 N m, against 0.09-0.12 N m today (Kowa).
- module rocking (0.8 deg today, about 5 deg with the real camera and no block) is gone: preloaded couple, about
  7.9 N m nose-down capacity after creep, 2.3 N m nose-up.
- printed parts are in compression on broad faces (<= 1.7 MPa sustained), so creep shows only as preload loss.

**Grafts.**
1. (D1) Bench step B0 records the BFAR protrusion t at Kowa infinity into `CAM['bfar_t']`; every lens-side datum is
   derived from it (`C_FLANGE_X = X_FW_IN + 1.2 + t + 5.0`). D1's contact-whitelist idea becomes check (c) in
   `check_j7_load_path`. D1's G-CAM-2 comparison (PCB-held vs housing-held) is the gate.
2. (D3) Corrected Kowa segment table and thumb-screw sweep rings (`ko_lens_lock_sweep`) instead of the clocked
   `lock_screws`; a `support` band entry per lens (data only, for the future collar); a numeric `LOAD_MODEL` used by a
   load check; `mass_com` WARN outside 0..+8.
3. (D3) Zoom path reserved, not built: for any lens > 300 g or > 0.15 N m static about the seat, a per-lens collar
   (D3's LCB: rear face on the tub outer face, split sleeve on the fixed band, pinch last) is added as a second
   support "set in place" after the housing is clamped. It can share the 3 s_cam stations: an LCB flange 2.2 thick on
   the tub outer face replaces "hood plate 2.0 + pad 0.1 + gap 0.1" in the same stack (head at x -0.5, engage 7.3).
   The hood plate then needs D3's opening. Apply D3's step split and the `_cuts` fix at that time.
4. (D2 variant beta) If G-CAM-2 nose-up fails, a second clip screw pair at (+-11.5, 80.5) (D2 s9.4).
5. Fixes to D2: cradle y +-19.5 (pin-hole wall 1.9); lower stations at y +-14.0 (hood web 1.44); hood pads 0.10
   (drop clearance 0.10); no threadlocker; block screws replaced by cross-recess A2 pan heads of the measured thread
   (PH1 if M2.5, PH0 if M2: a bench-only exception like the slotted BFAR lock screw); adapter rides on the lens.

**Rejected parts.** D1's floating camera with captive nuts and M3 hardware (assembly and policy cost, pi5 box
violation); D3's panel tie (service coupling) and its "J7 float" assumption; D2's threadlocker and 0.15 pads.

## 4. Implementation spec (J7-H)

**Order.** MP-CAM first (s5). Numbers below are drawing nominals (D2 s2); every one is a `layout` parameter that
MP-CAM overwrites. Build only through `run_locked.py`. hf = `X_FW_IN` = -5.2.

### 4.1 `layout.py`
- **`CAM`** (replaces the lands/ring/cs_ring/c_adapter/holes model):
  - `hf` = X_FW_IN (seat: housing front plane on the wall inner face; declared contact tub/gs_camera);
  - `housing` CYL x r 17.5, x hf-10.35..hf (-15.55..-5.2); `tab` B(hf-5.02, hf, -5.08, 5.08, 77.5, 81.6),
    `tab_slot` 0.8 (y -0.4..0.4); `lock_screw` axis Y at (x -7.8, z 79.4), `lock_head_side` '+y' (MP-CAM);
  - `pcb` B(-16.95, -15.55, -19.0, 19.0, 41.0, 79.0), 4 holes dia 2.5 at (+-15, 45/75) (proxy only, no pins);
  - `cover` B(-23.44, -16.95, -19.75, 19.75, 40.25, 79.75); `rear_x` = -23.44;
  - `bfar` dict(r 18.0, head 1.2, t 1.25, t_max 5.0) -> head x hf+t..hf+t+1.2;
  - `adapter` dict(r 15.375, l 5.0); `CS_FLANGE_X` = hf + 1.2 + t (-2.75); `C_FLANGE_X` = CS_FLANGE_X + 5.0 (+2.25);
  - `block_seat` (MP-CAM: 2 screw axes, thread, shoulder faces), `tripod_block` = 'removed at B0';
  - `wall_bore_d` 37.5; `pins` [(-16.5, 46.0), (16.5, 46.0)], pin_d 1.9, len 3.0, tip chamfer 0.4;
  - `stations` = {'l': (14.0, 40.5), 'r': (-14.0, 40.5), 't': (0.0, 85.6)};
  - `keeper` B(-27.27, -23.94, 4.0, SPLIT, 66.0, 76.0) (cover rear - 0.5; crash stop only);
  - `insert` dict(start_dx -7.2, lift 4.5).
- **`CRADLE`**: box B(-13.5, -5.2, -19.5, 19.5, 36.75, 50.0) minus CYL x r 17.75 (x -15.6..-5.1); front face x -5.2
  = datum; pilots dia 2.5 along -X at stations l/r from x -5.2, depth 8.3 (0.4 x 45 entry chamfer via
  `dc.pt_boss`); pin holes dia 2.2 x 3.3 at (+-16.5, 46.0), 0.3 x 45 entry chamfer; block-seat negative + 2
  clearance holes and cbores for the block screws (MP-CAM).
- **`CLIP`**: block B(-13.5, -5.2, -8.0, 8.0, 81.85, 89.1); hook B(-12.32, -10.32, -6.0, 6.0, 77.8, 81.85) (0.1
  behind the tab rear face x -10.22, 0.3 over the housing); pilot dia 2.5 along -X at station t, depth 8.3.
- **`HOOD`**: delete `turret`, `turret_b`; add `cam_holes` (3 x dia 3.4 at the stations, cbore dia 7.0 x 0.5 at
  x -0.5..0, rear pads dia 9 x 0.10 at x -2.6..-2.5). `HOOD_BOX` x1 8.5 -> 0.0.
- **PARTS**: `cam_cradle` (module `printed_cam`, ASA, black, face_down '+X', owner tub, infill small, envelope
  B(-13.6, -5.2, -19.6, 19.6, 36.7, 50.1), supports none); `cam_clip` (face_down '+Y', envelope
  B(-13.6, -5.2, -8.1, 8.1, 77.7, 89.2), otherwise the same).
- **SCREWS** (new block; repeat the `COTS['pt_screws']` recount line after it):
  - `s_cam_l`: joins [hood, tub, cam_cradle], into 'cam_cradle pilot_l', head_part hood, axis (-1, 0, 0),
    head_point (-0.5, 14.0, 40.5), tip (-12.5, 14.0, 40.5), engage 7.3, step 7, cbore dict(part 'hood', d 7.0,
    x (-0.5, 0.0)); `s_cam_r` the same at y -14.0; `s_cam_t` into 'cam_clip pilot' at (0, 85.6), joins [hood, tub,
    cam_clip]. Stack: plate 2.0 under the head + pad 0.10 + gap 0.10 + wall 2.5 = 4.7, engage 12 - 4.7 = 7.3.
  - Add the `cbore['x']` form to every consumer (`print_modifiers` already keys on parts; `printed_hood` cuts it
    explicitly; `checks.check_bosses` under-head measure).
- **MATES**: keep (tub, gs_camera, contact) for the tab face; add (tub, cam_cradle, contact), (cam_cradle, gs_camera,
  contact), (tub, cam_clip, contact), (cam_clip, gs_camera, clearance). The hood/tub pads stay 0.10 apart in CAD.
- **STEPS**: step 7 adds [gs_camera, cam_cradle, cam_clip, s_cam_t, s_cam_l, s_cam_r], tool 'PH1 (hand only)',
  action text per s4.6. Step 9: delete "clock the Kowa lock screws to the right"; adapter + lens as one unit.
- **INSERTIONS**: `camera_in` moving [gs_camera, cam_cradle], path [(-7.2, 60, 4.5), (-7.2, 0, 4.5), (-7.2, 0, 0),
  (0, 0, 0)], ignore [ko_fpc_loop, ko_fpc_cam]; `clip_in` (step 7, listed after camera_in) moving [cam_clip],
  path [(-2.9, 40, 0), (-2.9, 0, 0), (0, 0, 0)]; new `lens_on` (step 9) moving [c_cs_adapter, lens], path
  [(60, 0, 0), (0, 0, 0)].
- **REMOVALS / LATCH_FREE**: `camera_out` off [lens, c_cs_adapter, panel, cam_clip], unscrew [s_cam_t, s_cam_l,
  s_cam_r], moving [gs_camera, cam_cradle], reverse of camera_in, tool PH1; `clip_out` reverse of clip_in, unscrew
  s_cam_t; `hood_off` unscrew += s_cam_*; LATCH_FREE cam_cradle 'stays on the camera (2 bench screws)'.
- **KEEPOUTS**: `ko_fpc_cam` B(-28.67, -23.64, -8, 8, 39.4, 47.0); EXTERIOR `ko_lens_lock_sweep` = 2 rings r <= 24 at
  flange +12.5..16.3 and +31.1..34.9 (Kowa).
- **LENSES['kowa_lm6hc']** segments (r, from flange): thread 12.7 (-6.7..0), spigot 15.75 (0..2.2), knurl 21.0
  (2.2..7.6), groove 19.5 (7.6..10.6), focus 20.85 (10.6..22.4), label 19.3 (22.4..30.9), iris 19.25 (30.9..36.6),
  step 20.75 (36.6..41.7), front 27.0 (41.7..50.5), dome 23.0 (50.5..56.6); `thumb_screws` at +14.4 (focus) and
  +33.0 (iris) as sweep rings; `support` dict(r 21.0, x0 2.2, x1 7.6, status 'inferred fixed'). Fujinon: add
  `support` placeholder. COTS lens box B(C_FLANGE_X - 6.7, C_FLANGE_X + 56.6, -27, 27, 33, 87).
- **LOAD_BEARING_PARTS** += cam_cradle, cam_clip. **CRITICAL_FEATURES**: tub_cam_tab_seat (land 1.2, probe the wall
  at (-3.95, 0, 80) replacing `tub_front_wall_seat`'s off-load point), tub_cam_pin_0/1 (pin 1.6, new positions),
  cradle_face (land 1.2), cradle_pin_wall (wall 1.2), clip_hook (lug 1.6), hood_cam_underhead_l/r/t (lug 1.6,
  plate 2.0), panel_cam_keeper (lug, unchanged id). **CRITICAL_JOINTS J7_camera**: parts [tub, hood, panel,
  cam_cradle, cam_clip], `required` = all of the above. **SECTIONS**: section-j7-y14 and section-j7-y0.
- **LOAD_MODEL**: F_relaxed 100 N per PT, shock 5 g, hand 1.6 N m, wall 0.72 deg/N m (long-term), allowables 4 MPa
  XY / 2 MPa Z sustained.
- **self_check**: drop the two turret rows; add: wall_bore_d/2 - bfar r >= 0.6; |start_dx| >= 1.2 + t_max + 0.5;
  Kowa knurl start (C_FLANGE_X + 2.2) - (X_FRONT - 0.5 + PT head_h) >= 1.0; head-to-Fujinon radial (station r -
  3.0 - 19.5) >= 0.5; s_cam stack 4.7 and engage >= 7; cradle face x = tab face x = hf.

### 4.2 Parts
- **`printed_tub.py` `_front`**: bore teardrop r 18.75 (apex +Y, as today); pins at the new `CAM['pins']`; 3 explicit
  dia 3.4 cuts along X (x -5.3..-2.6) at the stations (no auto-cut exists for -X screws).
- **`printed_hood.py`**: delete `_turret`, `TURRET_R_FILLET`, PRINT supports item (1); `_bore_tool` from
  `CAM['wall_bore_d']` over x -2.8..+0.3 with the -Z truncated teardrop (flat 1.0, z 40.25) and a 0.5 x 45 front
  chamfer; 3 holes, cbores and 0.10 pads from `HOOD['cam_holes']`.
- **`printed_panel.py`**: keeper reads the new `CAM['keeper']` (no code change if it already reads the box).
- **new `printed_cam.py`** (pattern `printed_keeper.py`; imports math, cadquery, d2_common only): `PRINT` for both
  ids (cradle +X: "datum face on the bed, not post-processed, pilots vertical in print"; clip +Y: "pilot horizontal:
  policy B weak case"); `build`, `build_part`. Bed chamfers 0.6 on the bed-face edges; no fillets on the bed face.
- **`cots.py`**: `gs_camera` from the CAM sub-shapes (cover, pcb, housing + tab - slot, lock-screw head, BFAR tube
  r 18 / 12.7, FPC recess), tagged sub-solids `body` (housing, tab), `rear` (pcb, cover), `bfar`; COTS box
  B(-23.44, hf + 1.2 + t, -19.75, 19.75, 40.25, 81.6). `c_cs_adapter` tube r 15.375 / 12.7 at CS..C flange. Lens
  proxy from the corrected segments.

### 4.3 `checks.py`
- Replace the two "J7 camera ring in tub/hood bore" zones (lines 163-168) by "J7 BFAR in tub bore" and "J7 BFAR /
  adapter in hood plate bore": zone x -5.15..0.0, +-19.25 about the axis, target 0.75 (min 0.675).
- New **`check_j7_load_path`** (FAIL/PASS, in `checks.json`):
  (a) camera `rear` sub-solids >= 0.5 from every printed solid (keeper included);
  (b) `bfar` and the adapter >= 0.4 from tub and hood, with the proxy rebuilt at t = 0 and t = t_max;
  (c) camera contacts whitelist: `body` touches only the tub (tab front face, area >= 20 mm2) and the cradle (block
      seat); anything else in contact FAILs;
  (d) capacity: nose-down M = 2 x F_relaxed x (tab centroid z - station z) and nose-up M from the clip hook >= 1.5 x
      the 5 g moment of every LENSES entry about hf (FAIL), and >= 1.0 x the 1.6 N m hand case (WARN).
- `mass_com`: WARN outside 0..+8 for every lens (unchanged pass rule otherwise).
- Driver, boss, interference and modifier checks run from SCREWS as they are; confirm `check_bosses` accepts the
  `cbore['x']` form and a 'cam_cradle'/'cam_clip' receiver.

### 4.4 Build, tables, BOM
- `build_d2.py`: EXPLODE cam_cradle with the camera (-X 25), cam_clip +Z 15; SECTIONS render the two J7 cuts.
- `make_tables.py`: `estimate_volume` branches for cam_cradle (~2.6 cm3) and cam_clip (~1.0 cm3); counts +2 prints,
  PT 7 -> 10.
- `make_bom.py`: PT_USED += 3; new line "2 x cross-recess pan A2, camera block thread (MP-CAM), length = factory"
  (or INCLUDED_IN gs_camera if the factory screws are cross-recess).

### 4.5 Tests
- New `test_cam.py`: envelopes, print poses, keep-outs, COTS box overlaps (mates only), sweeps camera_in, clip_in,
  panel_on, lens_on; removals camera_out, clip_out; J7 features; `check_j7_load_path` with two synthetic FAILs
  (keeper moved to 0.2 behind the cover; s_cam_l deleted).
- `test_tub.py`: bore 37.5, new pins, 3 holes, no pi5 box overlap. `test_hood_panel.py` (lines 80-84): no turret,
  plate bore 37.5, holes/cbores/pads, lens and camera sub-shapes vs the hood at t 0 and t_max, keeper moved.
- `test_r3_regressions.py`: checker logic of `check_j7_load_path`.

### 4.6 Step text (ASSEMBLY.md and `STEPS`)
- **B0 (bench, new, before step 7):** remove the tripod block (factory hex key, once). Fit the cradle with the 2
  cross-recess screws, cradle face and housing front plane pressed on a flat glass, <= 0.15 N m, no threadlocker.
  Adapter + Kowa on, target >= 50 m (or collimator) at f/1.8: loosen the BFAR lock screw 1/4 turn, turn the BFAR to
  peak focus, tighten. Record t (BFAR face to housing front plane, +-0.05) and send it to `CAM['bfar_t']`. Unscrew
  lens + adapter as one while pinching the BFAR head.
- **Step 7:** plug the FPC. Camera + cradle in from the left 4.5 high and 7.2 behind the seat, lower 4.5, push +X
  7.2 onto the 2 pins (tab and cradle faces on the wall). Clip in from the left 2.9 behind, push +X. Drive s_cam_t,
  then s_cam_l, s_cam_r from the front through the hood plate, PH1, 0.35-0.5 N m, stop at head contact.
- **Step 9:** adapter on the lens; lens + adapter into the BFAR by hand; check infinity on live view; lock the Kowa
  thumb screws (they ride their rings).
- **Service:** camera out = lens, panel, s_cam_t + clip, s_cam_l/r, camera + cradle out (reverse path); the cradle
  stays on the camera. Lens swap = C thread only.

### 4.7 Docs
- SPEC.md s9 J7 row ("housing front plane on the wall at the tab and a printed cradle in the tripod-block seat; 2
  pins; 3 PT from the front; PCB and cover touch nothing"), turret rows out, s10 G-LENS / G-CAM-1 rewritten, G-CAM-2
  added. DESIGN.md J7, parts (+2), masses and CoM (Kowa about +1.0, Fujinon about -11). ASSEMBLY.md B0, 7, 9,
  service, tools (bench: factory hex key once; slotted driver for the BFAR lock screw; PH0 only if the block thread
  is M2). FASTENER-POLICY.md A (10 PT; s_cam_*), B (cradle pilots vertical in print, clip pilot horizontal), F rows
  (block screws, BFAR lock screw, lens + adapter unit), G (step 7 from the front). PRINT-GUIDE.md rows for both
  prints; hood supports reduced. MEASURED-PARTS.md MP-CAM rewritten + G-CAM-2. LENS-ZOOM-CANDIDATES.md "Load path":
  premise corrected (aluminium mount; gasket joint is the creep path), J7-H adopted, zoom rule (s3 graft 3).
  HANDOFF.md, NOTES.md.

## 5. Bench gates

- **MP-CAM (before CAD freeze and before the tub/hood print):** variant and PCB revision; tripod block removable (2
  screws: thread, length, head, axis angle, seat faces, photo + calipers); housing OD and length; tab width, height,
  depth and rear face; lock-screw size and head side; front-plane coplanarity of tab and block seat (+-0.02 on a
  surface plate); BFAR head OD, thickness, pitch, travel; t at Kowa infinity; adapter OD, band length, 5.00
  face-to-face; PCB and cover x from the housing front plane; cover square and centring; FPC exit. Drives `CAM`,
  `CRADLE`, `CLIP`, the insertion offsets, `ko_fpc_cam`. If the block is integral: stop; review D2 Plan B (housing
  collar) or an axis/Pi move.
- **G-CAM-2 (load path, new):** tub-front coupon (wall slice x -13.6..-2.7 with the bore, rib and the 3 stations) +
  hood-plate slice + cradle + clip + 3 PT; camera with the Kowa. (1) Dial indicator on the Kowa front barrel: hang
  645 g (3x) at the lens CoM, nose-down then nose-up: residual after unloading <= 0.02 mm. (2) Corner focus at f/1.8
  (focus peaking or slanted edge, 4 corners) with 0 and 645 g: no corner change beyond the depth of focus. (3) Hold
  215 g for 24 h at 50 C: corner focus unchanged, aim change <= 0.1 deg, keeper-to-cover feeler >= 0.3, no screw
  re-torqued. (4) Repeat (1) with the camera held only by its PCB holes as the baseline: J7-H must cut the
  deflection at the lens front by >= 5x. (5) Lock screw loose vs tight recorded.
- **G-PT-1:** add the cradle coupon (pilot vertical in print) and the clip coupon (pilot horizontal).
- **G-LENS (rewritten):** Kowa rear protrusion clears the BFAR bore and the IR glass; the dia 42 knurl does not turn
  or translate with focus or iris (needed only for a future collar); CoM by knife edge; thumb-screw envelope; 5 g
  knock on the housing seat with no image tilt.
- **G-ZOOM-1 (future):** before any lens > 300 g or > 0.15 N m static about hf: design its collar on a fixed band
  >= 15 mm long (D3 LCB), pinched last.

## 6. Residual risks
1. The design copies an unmeasured block seat; MP-CAM must come first.
2. Tub front-wall flex sets aim stiffness (0.36-0.72 deg/N m): aim only, transient under hand loads on zooms.
3. Insertion margins 0.25-0.3 are drawing-based.
4. Clip pilot is the weak PT orientation; variant beta (2 more screws) is the fallback for nose-up.
5. The cradle sits 0.45 over the cooler and closes part of the camera-underside recirculation path (airflow study
   paused).
6. No CAD was built here; every number above must pass the real suite.
