# Design 2: heavy-lens sag fix for D2 J7 (from the "ring clamp" brief), 2026-10-06

Frame: D2 assembly, mm (+X forward, +Y left/panel, +Z up, lens axis y 0 / z 60). Read-only: no repo file was
edited. Tags:
- **[drawing]**: read directly from `research/m12-drawings/gs_side.png`, `hq_draw.png` and `gs_p5.png`.
- **[est]**: my engineering estimate.
- **[probe]**: CadQuery check (`scratchpad/sag/probe_d2.py`, `probe_d2_lib.py`, `probe_d2.json`) against the
  release STEP parts, the COTS proxies and the keep-outs.

## 0. Facts that change the brief

1. **The real camera is not the J7 model** [drawing]. Front to rear:

   | Element | Size |
   |---|---|
   | C-CS adapter | Ø30.75 straight knurl, 5.8 long |
   | Back-focus ring (BFAR) head | Ø36 scalloped, **1.2 thick** |
   | Housing (aluminium per the RPi briefs) | Ø≈35 x 10.35 |
   | Top split tab | 10.16 wide, 5.02 deep, top r ≈ 21.6; transverse lock screw at z ≈ 79.4 |
   | Tripod block | 13.97 wide, 7.62 / 12.04 deep, bottom ≈ 30.3 below the axis |
   | PCB | 38 sq x 1.4 |
   | Plastic cover | 39.5 sq x 6.49 |

   - The rear photo shows the 2 housing-to-PCB socket screws through the cover, and 2 screws on the tripod-block
     shoulders.
   - `layout.CAM`'s stack (39.5 lands / Ø36 x 5.8 ring / Ø30.75 x 5 CS ring / 5 mm adapter) is therefore wrong.
2. **Today's J7 with the real camera** [arithmetic + probe]. The housing front plane (the tab and block faces, the
   only faces outside the Ø36.5 bore) lands on the wall at x -5.2. Then:
   - **(a) It cannot be installed.** The tripod block (x -5.2..-17.24, z 29.7..42.5) is ≈6.6 mm into the Active
     Cooler (top z 36.3) and `ko_exhaust` (36.2). **It must come off.** It is labelled "Optional tripod mount" and
     looks screwed on [unconfirmed].
   - **(b) The pins locate nothing.** They end at x -8.2, 7.35 short of the PCB (front x -15.55).
   - **(c) With the block off, the camera sags.** Nothing holds the housing bottom, so the Kowa pivots the module
     nose-down on the tab until the cover meets the keeper (1.23 gap, 14 below the pivot): **≈5° of sag**.
   - **(d) The real lens hits the turret.** The C flange sits at ≈ x **+2.25** (+1.25..+3.85), not +10.6, so the
     lens sits 8.35 further back. The Kowa's Ø42 rear ring (flange +2.2..7.6) and the Fujinon's Ø39 body then hit
     the turret (x 0..8.5, bore Ø36.5).
3. **The weak link is the housing-to-PCB joint, not the mount.** The mount is aluminium. The creep-prone link is
   housing -> PCB (2 M2 screws, nylon washers, sticky gasket).
   - Holding the **housing** takes that joint out of the lens path.
   - Holding the **PCB or cover** (today's pins and keeper) puts it back in.

## 1. Concept, and why not the ring clamp

1. Remove the tripod block and bolt a printed **cam_cradle** (≈2.7 g) into its place, using the block's own 2
   screws.
2. Seat the housing front plane on the tub wall inner face (x -5.2) at the **top tab** and the **cradle face**.
   Pull the cradle onto the wall with 2 PT screws from the front.
3. Capture the tab from behind with a printed **cam_clip** (≈1.1 g) on 1 PT screw.
4. The lens moment then runs lens -> adapter -> locked BFAR -> aluminium housing -> tab/cradle -> tub wall. The PCB,
   its 2 M2 screws, the nylon washers and the gasket carry only their own ~10 g and the FPC (0 % of the lens moment).
5. The BFAR and adapter run free in Ø37.5 bores and are never clamped. Back focus is set on the bench and held by
   the camera's own lock screw. The pins move to the cradle, so nothing touches the PCB or cover (the keeper becomes
   a crash stop).

**Ring clamp rejected** [est; split-collar moment capacity M = πTL/6]:
- **BFAR head:** 1.2 mm long, so the collar is a hinge: 0.19 N m at T 300 N, against 0.38 N m needed for the Kowa
  at 5 g. The head also travels 0.75-0.8 mm per turn (t = 0 to about 5), so a fixed collar may miss it.
- **Adapter knurl:** 5.8 long on an unlocked thread: 0.91 N m, dropping to 0.46 N m after relaxation. That needs
  17 MPa of sustained hoop stress in warm ASA, against a 4-5 MPa allowable.
- **Both** also need the module to float.
- **The preloaded 40 mm housing couple** gives ≈8 N m with the plastic only in compression.

## 2. Geometry

**Real camera model** (replaces `CAM` / `cots.gs_camera`); hf = X_FW_IN = -5.2:

| Feature | Geometry |
|---|---|
| Cover | x -23.44..-16.95 |
| PCB | 38 sq, x -16.95..-15.55 |
| Housing | Ø35, x -15.55..-5.2 |
| Tab | x -10.22..-5.2, y ±5.08, z 77.5..81.6, 0.8 slot |
| Lock screw | axis Y at x -7.8, z 79.4; head side TBD (+Y on a first-angle reading) |
| BFAR head | Ø36, x -5.2+t..-4.0+t (t ≈ 1.25) |
| Adapter | Ø30.75 x 5.0 from the BFAR face |
| Tripod block | removed |

Datums: **`C_FLANGE_X` = hf + 7.45 = +2.25** (`c_flange_from_hf` 7.45 ± 1.0, MP-CAM); `CS_FLANGE_X` = -2.75.

| Part | Change | Dims / position | Print / FDM |
|---|---|---|---|
| tub | bore | Ø36.5 -> **Ø37.5** (0.75 radial to the BFAR; ≥ 0.45 at ±0.3 location) | `dc.teardrop`, apex +Y |
| tub | pins | delete (-15, 75), (15, 45); add 2 (same Ø1.9 x 3.0 spec) at **(y ±16.5, z 46)**, tips x -8.2. 1.9 from the bore, 1.86 from the +Y teardrop | horizontal, as today |
| tub | holes | 3 x Ø3.4 along X at **(±13.5, 40.5)**, **(0, 85.6)**, as explicit cuts (`_right` auto-cuts only axis (0,1,0)) | < 8, no teardrop |
| hood | turret | **delete**, with its tree supports. The real lens position forces this for any design | removes the 8.5 overhang |
| hood | plate bore | **Ø37.5**; -Z truncated teardrop kept (flat z 40.25) | as today |
| hood | screw seats | 3 x Ø3.4, front cbore **Ø7.0 x 0.5** (x -0.5..0). The bottom cbores clear the teardrop flank by 1.08 | horizontal, < 8 |
| hood | rear pads | 3 x **Ø9 x 0.15** round the holes (x -2.65..-2.5). 0.05 drop-on clearance to the tub (gap 0.2); the screw closes 0.05 (policy ≤ 0.1) | vertical face |
| panel | keeper | unchanged (now 1.23 behind the real cover). Optional: x1 = cover rear - 0.5 | - |

**`cam_cradle`** (ASA, `small` infill, black):
- **Envelope** B(-13.5, -5.2, -18, 18, 36.75, 50.0), minus the housing cylinder r 17.75 (0.25 clearance, no radial
  contact).
- **Housing interface:** a copy of the removed block's front 7.62 mm mating faces and its 2 screw holes (G-CAM-2),
  trimmed to z ≥ 36.75.
- **2 PT pilots:** Ø2.5 along X at (±13.5, 40.5), x -5.2..-13.5 (engage 7.3 + 1.0), walls ≥ 2.5.
- **2 pin holes:** Ø2.2 x 3.3 at (±16.5, 46).
- **Clearances:** 0.45 over the cooler, 0.55 over `ko_exhaust`, 2.05 in front of the PCB.
- **Print:** face_down **+X**, with the datum face on the bed. Prismatic, no overhang. The pilots run print-up (the
  strong case); the small block-screw holes are horizontal. 0.6 bed chamfers.

**`cam_clip`** (ASA, `small`, black):
- **Block** B(-13.5, -5.2, -8, 8, 81.85, 89.1): 0.25 over the tab, 0.95 over the lock-screw head.
- **Hook** B(-12.32, -10.32, -6, 6, 77.8, 81.85): 2.0 thick, **0.1 behind the tab's rear face**, 0.3 over the
  housing.
- **PT pilot:** Ø2.5 along X at (0, 85.6), 8.3 deep, walls 2.5 / 2.25.
- **Print:** face_down **+Y**, so the profile is in the bed plane: no overhang, and the hook bends in-layer. The pilot
  is horizontal (the s_b/s_k weak case: 40 % modifier and insert fallback).

**Fasteners** (PT 3.0x12 PH1, 0.35-0.5 N m; stack: hood plate 2.0 under the head + pad 0.15 + tub wall 2.5 + part):

| id | head_point | axis | tip | into / head_part / joins | engage | cbore |
|---|---|---|---|---|---|---|
| s_cam_l | (-0.5, 13.5, 40.5) | (-1,0,0) | (-12.5, 13.5, 40.5) | cam_cradle / hood / hood, tub, cam_cradle | 7.3 | hood Ø7, x -0.5..0 |
| s_cam_r | (-0.5, -13.5, 40.5) | (-1,0,0) | (-12.5, -13.5, 40.5) | as s_cam_l | 7.3 | same |
| s_cam_t | (-0.5, 0, 85.6) | (-1,0,0) | (-12.5, 0, 85.6) | cam_clip / hood / hood, tub, cam_clip | 7.3 | same |

- **Driver:** step 7, from +X with the lens and adapter off. [probe] The bit (Ø6.5 x 40) and handle (Ø30 x 100)
  overlap only the Ø7 x 0.5 cbore itself (16.6 mm³ = its volume) once the turret is gone.
- **Camera block screws (x2):** reused, or same-thread A2 PH1 pan heads per the X1203 precedent. Bench only,
  ≤ 0.15 N m [provisional], low-strength threadlocker. Needs a new FASTENER-POLICY F row, because they clamp a
  printed part.

**Paths** [probe: 0 mm³ against tub, hood, Pi stack, cooler, keeper, plunger, microSD, EVF COTS and all keep-outs
except the camera's own FPC; the only hit is the old pin at (15, 45), which is deleted]:
- **`camera_in`** (gs_camera + cam_cradle): [(-7.2, 60, 4.5), (-7.2, 0, 4.5), (-7.2, 0, 0), 0].
  - Margins: rib_l land 0.3; `ko_run_cross` during the drop 0.3; cooler 0.45.
  - The BFAR stays clear for t ≤ 5.7. The adapter stays off, as today.
- **`clip_in`**: [(-2.9, 40, 0), (-2.9, 0, 0), 0].
  - Margins: hk3 beam 0.25; the hood's panel-tongue groove (z ≥ 90, y 24..32) 0.9; PCB edge 0.33; housing 0.3.
- **`panel_on`**: 0 mm³ against the camera, cradle and clip.

## 3. Load path with numbers

The moment is taken about the wall plane x -5.2, with the C flange at +2.25. The Computar CoM (40 from the flange)
is a guess.

| Lens | Arm | 1 g | 5 g | Couple at 1 g / 5 g (lever 39.7) |
|---|---|---|---|---|
| Kowa 215 g | 35.8 | 0.075 N m | 0.377 | 1.9 / 9.5 N |
| Fujinon 100 g | 32.8 | 0.032 | 0.161 | 0.8 / 4.0 |
| Computar 305 g | 47.5 | 0.142 | 0.710 | 3.6 / 17.9 |
| Optivaron 600 g | 62.7 | 0.369 | 1.844 | 9.3 / 46.4 |
| Hand, 10-20 N at 60-80 mm | - | 0.6-1.6 | - | 15-40 |

Design values: **M_d = 2.0 N m** in any direction. PT preload starts at 300-450 N; I use **100 N per screw after
creep** [est, G-PT-1].

**Path:**
- **Nose-down:** the tab front face is in compression on the wall and the cradle screws are in tension.
- **Nose-up:** the tab's rear face bears on the clip hook (to s_cam_t), and the cradle face is in compression.
- **Yaw:** the cradle screws at y ±13.5.
- **Roll:** the pins, plus friction.
- **Then:** the tub wall, with the hood plate stacked in the 3 joints.

**Capacity:**
- **Nose-down** (the only sustained case): pivot at the tab (z ≈ 80.2), screws at z 40.5: 2 x 100 x 0.0397 =
  **7.9 N m**. That is 105x the Kowa static, 21x the Optivaron static and 4x M_d.
- **Nose-up:** cradle 0.75 + clip 37 N x 42.7 = 1.59, so **≈2.3 N m ≥ M_d** (≈4x at initial preload). The Kowa at
  5 g needs 0.38.
- **Yaw:** ≈2.7 N m.
- **Roll:** a 0.5 N m screw-on torque gives 4.1 MPa of pin shear, plus ≈2 N m of friction.

**What reaches the sensor joint:**
- **From the lens: 0.** There is no parallel path: the keeper is 1.23 clear, the pins sit on the cradle, and the FPC
  is soft.
- **Residual:** PCB + cover inertia 0.0005 N m (1 g) / 0.0025 N m (5 g); FPC ≤ 0.006 N m, transient.
- **Comparison:** holding the PCB would put 0.097 N m from the Kowa alone on that joint, so this is **16-190x
  lower**. The aluminium housing carries the moment, as it does on its own tripod mount.

**Stresses.** Allowables: sustained 4-5 MPa XY, 2-3 MPa Z, bearing 5 MPa. Short-term 44 MPa XY and 32 MPa Z, used
with a shock safety factor of at least 2.

| Section | Kowa static | Optivaron static | M_d / shock |
|---|---|---|---|
| Tab pad on the tub wall (≈26 mm²) | 0.07 MPa | 0.36 | 1.9 |
| Tub wall bending at the pads (plate point-load model) | 0.35 | 1.7 (Z, inside 2-3) | 9.2 |
| Cradle/clip face under preload (≈170 mm² cone) | 2-3, relaxing | same | same |
| Under the PT heads (hood plate) | 16-24 initial, as every D2 PT | - | - |
| Cradle bearing at the block screws | 0.15 | 0.8 | 4.3 |
| Clip hook 2.0 x 12 (in-layer) | ≈0 | ≈0 | 13 (SF 3.4) |

Sustained stresses are all ≤ 1.7 MPa, so creep shows up only as preload loss.

**Tilt:**
- **Lens vs sensor (focus; budget ±0.3°):**
  - The PCB joint sees ≤ 0.006 N m, so ≤ 0.02° even at 20 N m/rad [est].
  - The aluminium chain is ≥ 2000 N m/rad [est]: 0.011° for the Kowa at 5 g, 0.05° for the Optivaron at 5 g or
    under hand load.
  - **No plastic is in this path and there is no creep term: the focus sag is gone.**
- **Aim (sensor and lens move together):** the tub front wall gives 0.36°/N m short-term and 0.72°/N m long-term
  (hood plate not credited).
  - Kowa static: 0.027° (≤ 0.054° after creep, ≈1.7 px).
  - Kowa at 5 g: 0.14°.
  - Optivaron static: 0.13°, rising to 0.27°.
  - **1.6 N m hand load: ≈0.6° transient.**

## 4. Alignment

**The camera alone sets lens-to-sensor alignment:** RPi's housing/PCB assembly, the locked BFAR, the adapter and
the lens flange. The new parts touch only the housing tab and the housing's own tripod interface:
- never the BFAR or adapter (0.75 radial nominal, ≥ 0.45 worst case);
- never the PCB or cover (keeper 1.23, cradle and clip ≥ 2.05).

**Each degree of freedom is located once, with no forced displacement:**
- x, pitch and yaw: the wall face at the tab and the cradle face;
- y, z and roll: the 2 pins;
- the clip: no constraint (0.1 axial, ±2 lateral).

**Bench coplanarity:** the cradle face and the housing plane are pressed together on a flat while the block screws
are tightened. A residual δ ≤ 0.1 tilts the rigid module by ≤ 0.14° as the screws seat.

**Framing stack:** pitch ±0.29°, yaw ±0.21°, roll ±0.5° worst / ±0.25° typical, shift ±0.3. These are framing
only, and of the same order as the sensor's own roll in its housing. The focus-tilt stack stays inside the camera.

## 5. Assembly, back focus, service

| Step | Action | Adds | Tool |
|---|---|---|---|
| 7a bench | Tripod block off. Cradle on with its 2 screws, the cradle face and housing plane pressed on a flat (Ø40 relief), tighten. Set back focus and lock it. Adapter and lens off | cam_cradle, block screws | camera key or PH1; RPi kit driver |
| 7b | Plug the FPC. Camera + cradle in from the left, 4.5 high and 7.2 back; lower; push +X 7.2 onto the 2 pins | gs_camera | none |
| 7c | Clip in from the left, 2.9 back, above the tab; push +X 2.9 | cam_clip | none |
| 7d | s_cam_t, then s_cam_l and s_cam_r from the front, through the hood plate | 3 PT | PH1 ≤ Ø6.5 shank |
| 9 | As today (adapter, lens) **+ ∞-focus check** | - | - |

**Back focus (bench, live view):**
1. Kowa at ∞ and f/1.8, aimed at a target ≥ 50 m away (or a collimator).
2. Loosen the lock screw 1/4 turn and turn the BFAR head to peak focus. Tighten the lock screw.
3. Check that the 0.3 m mark is right.
4. Unscrew the lens, then the adapter, while pinching the BFAR head.

**In-body touch-up** (panel off): only if the lock-screw head is on +Y. Its access at x -7.8, z 79.4 clears the
clip and hk3. Loosen it, turn the lens and adapter as one to drive the BFAR, then retighten; otherwise use the
bench. A ring clamp would first need unclamping.

**Lens swap:** at the C thread, then check ∞ focus.

**Camera removal:**
1. Lens and adapter off, then panel off.
2. The 3 PT screws out from the front.
3. Clip out (reverse `clip_in`), then camera + cradle out (reverse `camera_in`).
4. The cradle stays on the camera.

`hood_off` already requires the camera out.

## 6. Interactions

- **Fujinon:** its Ø39 body (r 19.5) clears the heads (r ≥ 20.4, x ≤ +1.9). Both LENSES must build; the proxies
  move with `C_FLANGE_X`.
  - **Correct the Kowa segments** (dossier s7.1): Ø42 knurl +2.2..7.6, focus Ø41.7 +10.6..22.4, iris Ø38.5
    +30.9..36.6, Ø54 only +41.7..50.5, locks at +14.4 / +33.0.
  - The Kowa's Ø42 ring sits 1.55 ahead of the heads; the Computar's Ø48.5 barrel sits 0.35 ahead.
- **Lens lock screws** (y -28.8): unconstrained now that the turret is gone.
- **Turret / hood:**
  - The look changes: the lens now meets a flat plate with 3 black PH1 heads.
  - The turret's tree supports go.
  - J1 drop-on keeps 0.05 at the pads.
  - FR1 (Y-slide hood) should pass the same pads; this is unverified.
- **Hand clearance:** the lens rear is 2.25 ahead of the plate; the rings sit at x 13..39. The grip is unchanged.
- **FPC:** `ko_fpc_cam` moves +1.03, to B(-28.67, -23.64, -8, 8, 39.4, 47.0), and the route gets about 1 mm
  shorter.
- **rib_l:** clear in the final pose; insertion margin 0.3.
- **Keeper:** a crash stop only; `j7_load_path` asserts ≥ 0.5.
- **Vents, plunger, SD:** the screws sit at z ≥ 40.5, clear of out_band, out_corner, the plunger guard and the SD
  slot. The cradle lowers the camera underside from 40.25 to 36.75, which changes the recirculation path over the
  cooler. Airflow study paused; flagged.
- **Thermal:** the housing is now bolted to the wall, a small extra conduction path for the camera's 0.4 W.
- **Balance** (Kowa release +3.73):

  | Change | CoM shift |
  |---|---|
  | Lens back 8.35 | -2.02 |
  | Turret (-13.1 g) | -0.71 |
  | Tripod block (-5 g est) | -0.19 |
  | New parts (+5.7 g) | +0.23 |
  | Adapter | -0.06 |

  - **Kowa ≈ +1.0** (target 0..+8), total ≈ 873 g.
  - Fujinon ≈ -11.0 (was -8.89).
  - Computar ≈ +12 (est).

## 7. Unknowns (new gate G-CAM-2; extend G-CAM-1 and G-LENS)

| Unknown | Tolerated by | If it fails |
|---|---|---|
| Tripod block removable; its 2 screws (thread, length, angle) and the mating faces | cradle interface is parametric | integral: J7 is infeasible anyway (cooler); Plan B (s9) |
| Housing OD; tab size and rear face; front-plane coplanarity | 0.25 radial, 0.1 hook gap, local pads | re-derive CAM and the hook |
| Lock-screw head side and size | the clip clears z ≤ 80.9 | -Y: bench-only back focus |
| BFAR thickness, pitch, travel; t at Kowa ∞ | Ø37.5 bores; insertion valid for t ≤ 5.7 | larger insert offset or bench pre-set |
| C flange from the housing front (7.45 ± 1); adapter 5.0 vs 5.8 | clearances hold for C ≥ +1.25 | re-derive `C_FLANGE_X` |
| Cover rear (18.24 from the front plane) | keeper ≥ 0.5 rule | move the keeper and `ko_fpc_cam` |
| PT preload retention when warm (G-PT-1) | 100 N design value | variant β (2-screw clip) |
| Interior temperature (G-W11) | sustained ≤ 1.7 MPa | PC cradle and clip |

**G-LENS (real camera, Kowa, then any zoom):**
1. Dial indicator at the lens front: 3x the lens mass nose-down, then nose-up. Pass: residual < 0.02.
2. A 10-20 N side load at the ring: record the aim shift.
3. Edge focus before and after 1 h at 45 °C. Pass: no change.
4. Repeat with the lock screw loose.

**G-CAM-1:** pins into the cradle; no rock with the 3 screws driven; plus a cradle and camera coupon fit.

## 8. Implementation plan

1. **`layout.py`**
   - `CAM` as sub-boxes: cover, pcb, housing, tab, lock_screw, bfar (t, t_max), adapter, block interface, block
     screws. `C_FLANGE_X` / `CS_FLANGE_X` from `c_flange_from_hf`.
   - `wall_bore_d` 37.5; pins at (±16.5, 46); keeper rule; `ko_fpc_cam` moved.
   - PARTS `cam_cradle` and `cam_clip` (module `printed_cam`, infill `small`, faces +X / +Y, envelopes as s2).
   - A SCREWS block for s_cam_l/r/t, repeating the `COTS['pt_screws']` line. COTS `cam_block_screws`, INCLUDED_IN
     gs_camera.
   - MATES: tab contact, cradle contact, cradle-camera screwed, clip contact, clip-camera clearance, hood-tub pads.
   - STEPS 7 text and adds. INSERTIONS `camera_in` (+ cradle) and `clip_in`. REMOVALS `camera_out` (unscrew s_cam_*,
     off cam_clip) and `clip_out`. LATCH_FREE: cam_cradle.
   - LOAD_BEARING_PARTS, plus CRITICAL_FEATURES:
     - cradle_face (land 1.2) and cradle_bar (1.6);
     - clip_hook (lug 1.6);
     - tub_tab_pad (1.6) and hood_underhead (1.6).
   - J7 parts: tub, hood, cam_cradle, cam_clip, with the probes required. SECTIONS: J7 cuts at y 0 and y 13.5.
   - `self_check`: insert offset ≥ 1.5 + t_max; screw stack = 12; C flange ahead of the plate.
2. **`cots.py`:** `gs_camera` from the sub-boxes, without the block. `c_cs_adapter` Ø30.75 x 5. Kowa segments
   corrected.
3. **`printed_tub.py`:** bore, pins, 3 holes. **`printed_hood.py`:** delete `TURRET_*` (and its PRINT supports);
   bore; holes, cbores, pads.
4. **New `printed_cam.py`** (pattern `printed_keeper.py`).
5. **`checks.py`**
   - New `j7_load_path`:
     - (a) every printed solid ≥ 0.5 from the camera pcb+cover sub-solid;
     - (b) BFAR and adapter ≥ 0.4 from tub and hood at t_min and t_max;
     - (c) the camera touches the tub only at the tab;
     - (d) capacity from the J7 SCREWS and the tab centroid ≥ 1.5x the 5 g moment for every LENSES entry and the
       1.6 N m hand case.
   - New `balance` WARN outside 0..+8.
   - Replace the ring/cs_ring clearance zones with a BFAR zone (min 0.4).
6. **`build_d2.py`** (EXPLODE, STEP_VIEWS), **`make_tables.py`** (`estimate_volume`; counts +3 PT, +2 prints),
   **`make_bom.py`** (INCLUDED_IN).
7. **Tests:** new `test_cam.py`:
   - envelopes, beds and print pose;
   - `camera_in`, `clip_in`, `panel_on` and `hood_on`, plus the removals;
   - J7 features;
   - `j7_load_path`, including a synthetic FAIL with the keeper at 0.2.

   Update `test_hood_panel.py` and `test_tub.py`.
8. **Docs:** SPEC (J7 row, s9, turret rows), DESIGN, ASSEMBLY (7a-d, back focus, service), FASTENER-POLICY (A +3,
   F row), PRINT-GUIDE, MEASURED-PARTS (MP-CAM, G-CAM-2, G-LENS), LENS-ZOOM-CANDIDATES "Load path" (premise
   corrected), HANDOFF.

## 9. Weaknesses and risks

1. **Rests on an unconfirmed fact: that the tripod block unscrews from the housing.** If it is integral, J7 fails
   for every design (cooler collision).
   - **Plan B:** a split printed collar on the housing body plus this clip. It is friction-held at the bottom
     (≈1-1.4 N m before relaxation) and weaker in creep.
   - **Plan C:** move the Pi/cooler or the axis.
2. **Large ripple:** the J7 model, lens position, turret, path, bores, pins and docs all change. Most of it is
   forced by the real camera for any concept; the sag-specific part is 2 prints, 3 PT screws and holes.
3. **Chassis flex:** 0.36-0.72°/N m of aim through the 2.5 mm front wall, so ≈0.6° under hand load on a zoom.
   This design fixes focus sag and rocking, not frame shake. **Heavy zooms still want a base lens support**, or a
   stiffer wall.
4. **Nose-up ≈2.3 N m only just covers M_d.** Variant β (2 clip screws at (±11.5, 80.5)) gives ≈8 N m for one more
   screw.
5. **Insertion margins of 0.25-0.3** come from drawing reads; re-run them after G-CAM-2.
6. **The adapter comes off for insertion,** which risks the BFAR setting if the lock screw is loose. In-body
   touch-up needs the panel off and the head on +Y.
7. **PT and block-screw preload relaxes** in warm ASA. The joints then run in bearing: aim ≤ 0.1°, focus unaffected.
8. **Clip pilot is horizontal in print** (weak case); the policy B rules apply.
9. **Cradle sits 0.45-0.55 over the cooler/plenum;** airflow unmodelled.
10. **Roll ±0.5° worst.**
11. **Fujinon balance worsens** to ≈ -11.
