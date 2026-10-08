# D2 J7 lens/camera support: code dossier (read-only, 2026-10-06)

Scope: `cad/gs8-d2-v1` (paths below are relative to it unless prefixed). Nothing in the repo was edited, built or
re-run. Numbers were read from the code; numbers marked **[probe]** come from my read-only probes
(`scratchpad/sag/probe1.py`, `probe2.py`, `probe3.py`) on the release STEP parts `out/step/parts/*.step` (assembly frame,
confirmed by their bounding boxes) and the `cots.py` proxies. Frame: +X forward, +Y left (panel), +Z up; lens axis
(y 0, z 60).

## 0. Findings a designer needs first

1. **The camera proxy is a box plus two tubes.** It omits the split lock tab, the tripod tab, the mount screws, and
   any mount-base/PCB/cover split (`cots.py:147-159`). The real lock tab reaches about z 80-82 and the tripod tab
   about z 29-30, both outside the proxy box z 40.25..79.75. No D2 document says the tripod tab is removed.
2. **The drawing does not support the D2 ring model (pixel reading, needs MP-CAM).** In
   `research/m12-drawings/gs_side.png`, I measured the black outlines at 0.0993 mm/px (from the 39.5 cover).
   - The front 5.8 mm element is about **31.1 mm tall** (dia 30.75 class).
   - The 1.2 mm element behind it is about **36.5 mm tall**, with a serrated edge (the dia 36 knurl).
   - D2 instead models a dia 36 x 5.8 ring (x -5.2..+0.6) plus an extra dia 30.75 x 5.0 "CS ring" (x +0.6..+5.6)
     (`layout.py:205-206`).
   - D2's module depth is `CAM['depth']` 19.27 = 25.07 - 5.8 (`layout.py:204`). So the D2 "lands" face is the front
     of the 1.2 element, not the square mount-base face.
   - If the 1.2 element is round (dia 36), it enters the dia 36.5 bore, and the module would seat about 1.2 mm
     further forward.
   - The 5.8 element (dia 30.75) would then sit in the bore with about 2.9 mm radial clearance. **The "bore catches
     the ring after 0.25" mechanism would not exist.**
   - The mount base reads about 35.2-35.7 mm tall. A face that size has an inscribed circle smaller than the dia
     36.5 bore, so it would touch the wall only at its 4 corners.
   - D2 stack: CS flange 30.07 ahead of the cover rear, C flange 35.07 ahead. With C = 17.526, the sensor plane
     would sit about 9.6 mm in front of the PCB front face (7.89 from the rear), which cannot be right. The drawing's
     front face at 25.07 is consistent with the C flange (adapter fitted).
   - **The lens may therefore be modelled about 5-10 mm too far forward.** That changes the moment arms, the
     balance, and every support position below. Verify on the part (MP-CAM, `MEASURED-PARTS.md:74-83`) before you
     design.
3. **There are no seat preload, no clamp and no screw at J7.** Only these restrain the module:
   - the seat face (contact);
   - 2 pins dia 1.9 x 3 (shear);
   - a panel finger 0.2 behind the cover (`layout.py:212`);
   - the bores, **[probe]** first contact of the dia 36 ring after 0.26 mm in every direction, except tub +Y 0.36
     (teardrop) and hood -Z 0.36 (truncated teardrop).
   - Nothing preloads the module. My arithmetic in s9: it can rock about 0.83 deg nose-down under the lens weight
     before the keeper touches, 0.32 deg nose-up, and 0.29 / 0.73 deg in yaw. That is aim shift (sensor and lens move
     together). The lens-vs-sensor creep is a separate effect inside the camera.
4. **No check asserts the CoM target or any lens load.** `mass_com` only reports. It passes when total mass > 0 and
   there are no stubs (`build_d2.py:1344-1345`). The 0..+8 mm target exists only in `LENS-ZOOM-CANDIDATES.md:60`.
   Nothing in checks.py models force, moment or stiffness.
5. **The J7 probes do not look at the load zones.**
   - `tub_front_wall_seat` measures the plain front wall at (-3.95, -20, 30), 30 mm below the axis
     (`layout.py:835-836`). It does not touch the seat land round the bore.
   - **[probe]** Tub seat land inside the 39.5 square is 479 mm2 of 1560 (-Y half 257, +Y half 222, lower half 240,
     upper half 240).
6. **Stack and steps.** The hood drops on at step 5, before the camera (step 7). The panel goes on at step 8.
   Adapter and lens follow at step 9 and have **no insertion sweep**. A support fitted at steps 7-9 needs its own
   INSERTIONS/REMOVALS entries.
7. **Free volumes confirmed empty by [probe]** (no printed part, no proxy, no keep-out) are listed in s8. The
   biggest: above the camera, right of it, left of it (panel side) and a 3.75 mm slab under it.
   - Two annuli are also free: the turret-bore annulus round the CS ring and adapter (r 15.4..18.2, x 0.6..8.5),
     and the 2.1 mm axial gap between the turret front (x 8.5) and the Kowa rear face (x 10.6).
   - Outside, the space below the lens (x 0..67, z 0.3..33) holds only the turret and the plunger guard rim.

## 1. Geometry inventory (x -30..+70 near the axis; front zone x -3..+70, z 0..60, |y| <= 35)

### 1.1 Datums (`layout.py`)
| Item | Value | Line |
|---|---|---|
| X_FRONT, X_REAR, T | 0.0 (hood plate outer face), -154.0, wall 2.5 | 66-68 |
| XT1 / X_FW_IN | -2.7 tub front-wall outer face / -5.2 inner face = camera seat | 69-70 |
| ZT1, YR/YL, Y_RW_IN, SPLIT | 97.3 wall tops; +-35; -32.5; 32.2 panel inner face | 72-75 |
| LENS_AXIS | (y 0, z 60) | 78 |
| TUB_BOX / HOOD_BOX / PANEL_BOX / GRIP_BASE_BOX | envelopes (contract: 0.001 tolerance) | 84, 102, 87, 117 |
| GRIP axis_x / top_z | -47.0 / -8.0 | 110-113 |

### 1.2 Camera stack J7 (`layout.py:200-223`) and proxies
| Feature | Value (assembly frame) | Line | Owner |
|---|---|---|---|
| seat_x | -5.2 (declared contact tub/gs_camera, MATES `layout.py:661`) | 203 | tub face |
| lands, depth, rear_x | 39.5 sq, 19.27, cover rear -24.47 | 204, 215 | proxy |
| ring | CYL x, r 18.0, x -5.2..+0.6 ("rotates; never clamped") | 205 | camera |
| cs_ring | r 15.375 (dia 30.75), x +0.6..+5.6; CS_FLANGE_X +5.6 | 206, 217 | camera |
| c_adapter | r 15.0 (OD 30 estimate), x +5.6..+10.6; C_FLANGE_X +10.6 | 207, 216 | c_cs_adapter |
| holes | (y,z) (+-15, 45/75), dia 2.2 (stills R1; palette 2.7; drawing dia 2.5) | 208, 495 | camera |
| pins | (-15, 75) and (15, 45), dia 1.9, len 3.0, tip chamfer 0.4 | 209-210 | tub |
| wall_bore_d | 36.5 (tub wall, hood plate, turret) | 211 | tub/hood |
| keeper | B(-28.0, -24.67, 4.0, 32.2, 66.0, 76.0), 0.2 behind the cover | 212 | panel |
| insert | path -Y at 2 mm high, down 2, +X 11.1 | 213, 759-760 | - |
| COTS gs_camera | 34 g, box B(-24.47, 5.6, -19.75, 19.75, 40.25, 79.75), step 7 | 493-496 | cots |
| COTS c_cs_adapter | 6 g, box B(5.6, 10.6, -15, 15, 45, 75), step 9 | 497-498 | cots |
| COTS lens | box B(6.1, 67.2, -32, 27, 33, 87), mass from LENSES, step 9 | 499-500 | cots |

**What `cots.gs_camera` models** (`cots.py:147-159`):
- a 39.5 x 39.5 box x -24.47..-5.2, with 4 dia-2.2 through holes;
- the FPC socket as a **recess** B(-24.47, -23.47, -8.5, 8.5, 41.25, 46.25);
- the ring as a tube r 18 / r_in 12.7 at x -5.2..0.6;
- the cs_ring as a tube r 15.375 / 12.7 at x 0.6..5.6.

Not modelled: the lock tab, tripod tab, 1.2 knurl/flange, mount-base/PCB/cover split, mount screws and the throat
dia 22.4. Other proxies:
- `c_cs_adapter` is a tube r 15 / 12.7 (`cots.py:162-165`).
- `lens_proxy` (`cots.py:168-180`) revolves the `lens_spec` segments and adds the Kowa lock screws as Y-cylinders
  r 2.6 from y (-28.8 - 3.2) = -32.0 to -26.0, cut with a front recess.
- Mass/CoM of the lens comes from `lens_spec` (`layout.py:465-470`; `cots.py:324-327`).

**Lens table** (`layout.py:449-462`); segments are (r, x from the C flange); absolute = +10.6:
- Kowa LM6HC, 215 g, CoM 28.3 from the flange (x 38.9):
  - thread r 12.7, x 6.1..10.6 (the rear protrusion, 0.5 ahead of the CS flange);
  - rear r 25.5, 10.6..15.6;
  - iris ring r 27, 15.6..25.6;
  - mid r 26, 25.6..33.6;
  - focus ring r 27, 33.6..55.6;
  - front r 26.5, 55.6..67.2;
  - lock screws d 5.2 at x 20.6 and 44.6, y -28.8. They sit on the iris and focus rings, so their real clock
    position moves with those rings.
- Fujinon HF6XA-5M, 100 g, CoM 25.3 from the flange (x 35.9): thread as Kowa; body r 19.5, x 10.6..61.6; no lock
  screws.
- Non-rotating sections by proxy label only (unverified): Kowa rear x 10.6..15.6, mid 25.6..33.6, front 55.6..67.2.

### 1.3 Tub front wall and its features (owner tub, `printed_tub.py`)
| Feature | Geometry | Code |
|---|---|---|
| wall | x -5.2..-2.7, y -35..32.2 (above the lip), z 0..97.3; part of `_shell` (R5 vertical edges, 45 deg bed flats on -Y corners) | `printed_tub.py:75-90` |
| lens bore | `dc.teardrop(18.25, -0.1, T+0.2, (-5.2, 0, 60), +X, up=+Y)`: x -5.3..-2.5; 45 deg roof toward **+Y**, apex y +25.8 at z 60 (print up) | 193-194; `d2_common.py:323-334` |
| 2 pins | cyl r 0.95 from x -5.15 along -X 2.65 + cone 0.4 to r 0.55; tips at x -8.2 | 195-198 |
| rib_l | xy prism (-5.15, 24.1), (-5.15, 32.2), (-12.1, 32.2), (-12.1, 31.0), z 2.45..41.0 (45 deg gusset, 1.2 tip land) | 199-202; `layout.py:218-223` |
| locate-rib notch | built only if the panel rib z0 - LOCATE < 41 (it is 41.3, so none) | 203-206 |
| rib_r | deleted (lay in the Pi drop path) | 207-216 |
| plunger hole | B(-5.2, -2.7, 3.2, 14.8, 17.2, 23.8) through | 217-218; `layout.py:321` |
| plunger flange recess | x -3.1..-2.6 outer face, y 1.9..16.1, z 16.3..24.7 | 219-223 |
| SD slot | B(-5.2, 0, -11.5, 0.5, 15.9, 18.6) through tub wall and hood plate | 217-218; `layout.py:323` |
| exhaust windows | out_band y -26.5..17.5, z 25.9..29.7; out_corner y -31..-21, z 32..38 (x -6.2..-2.6) | 224-226; `layout.py:375-378` |
| hk3 catch ledge | front wall y 17..27, 0.8 proud (x -6.0..-5.2), catch z 88.55, 45 deg return, -Y end 45 deg | 159-185; `layout.py:152` |
| bed chamfer | 0.6 on the bed-face (-Y) edges along X | 365-372 |

### 1.4 Hood front plate, turret, bore (owner hood_panel, `printed_hood.py`)
- **Plate:** x -2.5..0, z 0.3..100, y -32.35..35, from `_shell` (`printed_hood.py:126-155`; `layout.py:94-95`). It
  stands 0.2 from the tub wall (no contact). Front-top chamfer 3.0; plate foot fillet 1.5 (`PLATE_FOOT_R`); vertical
  edge fillet 1.4 (lines 38-42).
- **Turret** (`printed_hood.py:182-192`): a dia 60 x 6 (x -0.5..6, fused 0.5 into the plate) plus a dia 57 x 2.5
  (x 6..8.5). Fillets 0.8 at the step and 0.6 at the front (`TURRET_R_FILLET`, line 51). Turret bottom z 30 (x 0..6)
  / 31.5 (x 6..8.5).
- **Bore tool** (`printed_hood.py:195-208`):
  - a dia 36.5 cylinder, x -2.8..8.8;
  - a truncated teardrop toward **-Z** (print up), tangent at 45 deg, flat `BORE_FLAT` 1.0 below the circle (z 40.75,
    flat 13.1 wide);
  - a front cone chamfer 0.5 at x 8.0..8.8.
- **Plunger well and guard** (`printed_hood.py:239-248, 266-280`; `layout.py:313-322`):
  - pocket x -2.5..-1.3, y 1.9..16.1, z 0.3..24.7;
  - opening y 3.2..14.8, z 17.2..23.8;
  - guard rim 1.2 wide x 0..1.0 proud (y 2.0..16.0, z 16.0..25.0).
- **Exhaust slots:** out_band (y -26.5..17.5, z 25.9..29.7) and out_corner (y -31..-21, z 32..38), 2.0 slots on
  3.4 pitch through the plate (`printed_hood.py:276-279`).
- **hk3 hook** (front wall, y 22):
  - beam t 1.6, x -7.85..-6.25, y 18..26, hanging from the band to z 86.8, tooth +X;
  - J1 clearance zone x -9.2..-4.7, y 16.5..27.5, z 83.3..96.8 (`printed_hood.py:211-225`; `checks.py:146-155`).
- **Roof rib and stack stop:**
  - roof rib B(-132, -10, 8.4, 10, 94.3, 97.8) (`printed_hood.py:45, 290`);
  - edge flange y -32.35..-30.75, z 94.3+ (line 46, 251-263);
  - **stack stop** post B(-10.7, -6.5, -31.3, -27.6, 22.0, 45.5) + fin B(-24.0, -6.5, -31.3, -27.6, 45.0, 97.8)
    (`layout.py:1271-1276`; `printed_hood.py:292-295`).
- **Load path of anything on the hood:** hood -> 4 hooks (0.1 play; hk3/hk4 have a 45 deg return that cams out) and
  the band on the wall tops -> tub. The plate does not bear on the tub front wall.

### 1.5 Panel features near the camera (owner hood_panel, `printed_panel.py`)
- **Keeper finger** (`printed_panel.py:142-149`):
  - box x -28.0..-24.67, y 4.0..32.7 (0.5 into the wall), z 66..76;
  - root gusset polygon (-28, 32.7), (-36, 32.7), (-36, 32.2), (-28, 20.2), z 66..76 (`KEEPER_GUSSET` (8, 12),
    line 42).
  - It is a 3.33 (x) x 10 (z) cantilever reaching from the panel to y 4. It is compliant in X and touches only the
    +Y half of the cover (y 4..19.75). Gap 0.2 **[probe]**. Probe `panel_cam_keeper` measures 3.33 (lug).
- **Front locate rib:** B(-6.55, -5.35, 24.0, 32.7, 41.3, 70.0). z0 is raised to 41.3 by `LOCATE_FRONT_Z0`
  (`printed_panel.py:43, 167-172`; `layout.py:171`).
- **post_f** B(-35.5, -27.5, -30.4, 32.2, 81.5, 89.5): it spans the full body width behind and above the camera.
  s_r1 enters it from the right at (-31.5, 85.5) (`layout.py:428-430, 440`).

### 1.6 Base front (owner grip_small, `printed_grip.py:100-118`)
- Slab x -117..-0.5, y +-35.2, z -8..0. Front underside chamfer 5 x 45 deg, (x -5.5, z -8) to (x -0.5, z -3)
  (`layout.py:103-106`). Rear chamfer 1.0; 0.6 bed chamfers. The base is 0.5 behind the hood plate face.
- Grip column x -71..-23, y +-15, z -110..-8 (er 9). The right hand's fingers wrap the grip front face x -23. There
  is no hand keep-out in the layout.
- The base prints top-down (+Z face on the bed), so nothing can rise above z 0 on this part.

### 1.7 Interior neighbours of the camera (all `layout.py`)
| Item | Box / value | Line |
|---|---|---|
| Pi 5 COTS box | B(-94.0, -5.55, -32.3, 23.7, 16.0, 36.1); pcb z 18.5..20.1 | 477-484 |
| Active Cooler | B(-72.8, -9.5, -25.55, 16.95, 20.2, 36.3) | 485-487 |
| microSD | B(-12.4, -3.5, -11.0, 0.0, 16.9, 17.9) | 529-532 |
| ko_exhaust (plenum) | B(-9.4, -5.3, -27.4, 16.9, 22.6, 36.2) | 592 |
| ko_sd | B(-5.8, 0, -11.5, 0.5, 16.1, 18.4) | 583 |
| ko_fpc_cam | B(-29.7, -24.67, -8, 8, 39.4, 47.0) | 591 |
| ko_fpc_loop | B(-42.5, -29.7, 2, 19.5, 36.6, 56.0) | 590 |
| ko_run_cross | B(-27, -21, -32.3, 24.1, 36.6, 39.8) | 602 |
| ko_run_rise / ko_run_link | B(-26, -22, 24.1, 31, 2.7, 37) / B(-26, -22, 23, 25.5, 35.5, 38.5) | 594, 615 |
| ko_qt_lead / ko_lead_wall | B(-21, -11, -31.7, -25.8, 28.8, 40) / B(-64, -11, -32.3, -26, 36.6, 44) | 578, 600 |
| ko_hdmi_pi | B(-36.6, -27, 24, 32, 17, 41) | 584 |
| FPC cable | 200 mm, via ko_fpc_up, run, link, loop, cam; steps (4, 7) | 538-539 |
| right-wall vents out_wall | x -19..-5, z 21..37 | 379-380 |
| pad_r1 / s_r1 | dia 12 at (-31.5, 85.5), y -32.5..-30.5 | 442 |
| EXTERIOR_KEEPOUTS | ko_tripod_clamp B(-132, -82, -25, 25, -23, -8) only | 617-621 |

## 2. Print orientation and FDM rules

**FDM** (`layout.py:44-57`, re-exported in `d2_common.py:28-35`):
- NOZZLE 0.4, LAYER 0.2.
- MIN_WALL 1.2, MIN_WALL_LOADED 1.6, MIN_FEATURE 0.8.
- SLIDE 0.25, LOCATE 0.15, SEAM 0.3 (per side).
- MAX_OVERHANG_DEG 45, MAX_BRIDGE 30, TEARDROP_ABOVE_D 8.0, BED_CHAMFER 0.6.
- ASA_DENSITY 1.07e-3.
- INFILL_FACTOR shell 0.85, base_grip 0.6, small/tpu/thin 1.0 (`layout.py:61`).

**MODULE_CONTRACT** (`layout.py:1300-1322`):
- Inputs: one solid, inside the envelope, outside every KEEPOUT and non-mate COTS box.
- Walls >= 1.2 (1.6 loaded).
- Bed rules: 45 deg bed chamfers, no fillets on the bed face, overhangs <= 45 deg unless bridged (<= 30) or listed in
  supports.
- Teardrops on horizontal holes > 8. PT bosses via `dc.pt_boss` (pilot 2.5, OD 8, depth engage + 1).
- Imports only math, cadquery, d2_common.

**Feature class floors** (`layout.py:1150-1153`): hook, lug, lip, boss, wing, pin, neck and bar 1.6; wall, land and
flexure 1.2 (flexure needs a FEATURE_GATES gate).

**Helpers** (`d2_common.py`):
- `teardrop(r, t0, t1, origin, axis, up)` (323-334);
- `pt_boss` (106-118), `counterbore` (120-130), `bed_chamfer` (309-321);
- `safe_fillet` / `safe_chamfer` (336-358);
- `FACE_DOWN_ROT` and `to_print_pose` (366-378).

| Part | face_down (PARTS, `layout.py:625-652`) | Consequence for J7 work | Supports |
|---|---|---|---|
| tub | -Y (right wall on the bed) | The front wall is vertical. The X bores are horizontal, so the teardrop apex points +Y. The pins are horizontal cantilevers. Anything grown from the front wall's inner face toward -X is a horizontal overhang that needs 45 deg undersides on its -Y faces. | 2 paint-on under the T-tongue wings (`printed_tub.py:39-50`) |
| hood | +Z (roof on the bed) | The plate is vertical. The turret's top half (assembly +Z) is print-down and already needs **tree supports** (8.5 overhang). The bore teardrop points -Z. | tree: turret upper half + housing strip (`printed_hood.py:21-34`) |
| panel | +Y (face on the bed) | Every feature grows from the inner face toward -Y; the keeper finger, ribs and posts print vertically. | none (`printed_panel.py:24-36`) |
| base_grip | +Z (base top on the bed) | Nothing can rise above z 0; the column grows "up" in print. | none (`printed_grip.py:44-54`) |
| pi_keeper | +Z | - | none |
| small parts (plunger +X, knobs +Y, eyecup +X TPU, stick_sleeve -X) | `layout.py:639-651` | the pattern for a small new part | none |

PRINT-GUIDE per-part table: `PRINT-GUIDE.md:52-62`. Modifier meshes: s1.1. Datum faces are not post-processed
(seat x -5.2): `PRINT-GUIDE.md:113-121`.

## 3. Assembly sequence, insertion paths, screws

**STEPS** (`layout.py:678-747`):

| Step | Adds | Line |
|---|---|---|
| 3 | tub on base (+ s_j, `layout.py:1253-1259`) | - |
| 4 | Pi stack + keeper + s_k1/s_k2; FPC plugged at the Pi, camera end loose | 699-716 |
| 5 | plunger + hood + microSD | 718-721 |
| 6 | EVF | 722-728 |
| **7** | **camera** (FPC plugged first) | 729-733 |
| 8 | panel + s_b1, s_b2, s_r1, s_r2 | 734-739 |
| 9 | knobs, eyecup, **c_cs_adapter + lens** ("clock the Kowa lock screws to the right"), stick | 740-743 |
| 10 | pack, cap | - |

`present_at(step)` (768-774) and `screw_audit_set` (777-780) derive the state at each step.

**INSERTIONS** (`layout.py:748-765`): waypoints are offsets of the moving set relative to its final pose.
- `hood_on`: [(0, 0, 60), 0], snaps hk1..hk4 (755).
- `camera_in`: [(-11.1, 60, 2), (-11.1, 0, 2), (-11.1, 0, 0), 0], with ignore [ko_fpc_loop, ko_fpc_cam] (759-760).
  - During the -Y slide the camera occupies x -35.57..-5.5, z 42.25..81.75.
  - It clears rib_l (top z 41) by 1.25 and the hk3 beam (z >= 86.8) by about 5.
  - The cs_ring front stops 0.3 behind the wall face before the +X 11.1 push.
- `panel_on`: [(0, 70, 0), 0] (761). gs_camera is an obstacle in this sweep: **any panel feature must slide -Y past
  the camera's x/z silhouette**, as the keeper does behind the cover.
- **No entry for c_cs_adapter or lens** (or the knobs and eyecup): they are never swept.

**REMOVALS:**
- `camera_out`: reverse of camera_in, with the panel, lens and adapter off; tool "none" (`layout.py:1220-1223`).
- LATCH_FREE: lens and adapter "unscrewed by hand"; gs_camera "see camera_out" (1232-1241). Every part named in any
  `off` list needs a REMOVALS path or a LATCH_FREE reason (`checks.removal_coverage`, `checks.py:1355-1374`).

**How sweeps are checked** (`checks.check_sweeps`, `checks.py:554-648`):
- Positions: path points every 2 mm, plus 1.0 and 0.5 before the final pose (`_path_points` 538-551).
- Obstacles: everything `present_at(step)` except the movers, later movers of the same step and screws.
- Keep-outs: those of every cable plugged at an earlier step with an end already in the body, minus `ignore`.
- Skipped: mates of kind press, thread or interference.
- Method: manifold3d boolean, tolerance 0.5 mm3. Only listed snap zones may overlap.
- Current state: camera_in, panel_on and hood_on pass with 0 hits; camera_out passes (`out/checks.json`).
- Service sweeps use the same machinery against the final state minus `off` (`check_removals`, 1232-1305).

**Screws.**
- PT spec (`layout.py:412-416`): 3.0 x 12, head 6.0 x 2.4, pilot 2.5, clear 3.4, cbore 7.0, boss OD 8 (min 7),
  engage >= 7, tip reserve 1.0, 0.35-0.5 N m, 5 reuses.
- DRIVER (417-418): bit 6.5 x 40, handle 30 x 100.
- SCREWS entry fields (421-434; later blocks 974-979, 1248-1251):
  - `id` (prefix `s_` matters: interference exemption, explode, audit filter);
  - `joins`;
  - `into` (first word = the part that receives the thread);
  - `head_part`;
  - `axis` (advance direction);
  - `head_point` (the face the head bears on);
  - `tip`. The distance from head_point to tip must be 12.0 (`self_check` 1373-1376);
  - `engage` (>= 7);
  - `step` (the id must also be in that step's `adds`);
  - `cbore` (part, d, z or y range);
  - `note`.
- Consumers of a screw entry:
  - `layout.self_check` (1373-1384);
  - `print_modifiers` (798-814: an r 8 cylinder from head - 7 to tip + 1.5 for every shell/base_grip part named in
    into/head_part/cbore/joins);
  - `checks.screw_pierces` + `check_interference` (62-114);
  - `check_driver` (470-514): a bit and handle cylinder coaxial from head_point backwards, checked against
    `screw_audit_set` (or the service context);
  - `check_bosses` (748-803): pilot 2.5 +-0.05, depth >= engage + 1, wall >= 2.25 and under-head >= 1.6, measured on
    the solids;
  - `cots.screw` (306-313) and `build_all` (343-348);
  - `COTS['pt_screws']` name and mass, recomputed after each SCREWS block (`layout.py:980, 1252`): repeat that line
    in any new block;
  - `explode_of` (`build_d2.py:374-379`);
  - `make_bom.py:31-34` (PT_USED);
  - the make_tables screws/counts blocks and the "n PT screws" text lint (`make_tables.py:568-607, 664-737`);
  - FASTENER-POLICY s A count text (`FASTENER-POLICY.md:13-23`).
- **Owners derive some screw cuts automatically by pattern:**
  - `printed_tub._right` counterbores *every* screw with axis (0, 1, 0) (`printed_tub.py:328-333`);
  - `printed_tub._floor` cuts clearance for (0, 0, 1) screws into the panel (140-142);
  - `printed_panel._cuts` makes pilots for every `into` that starts with "panel" (keyed by PANEL_BOSSES/POSTS name,
    `printed_panel.py:216-230`);
  - `printed_grip._base_cuts` counterbores every screw with head_part base_grip (`printed_grip.py:190-194`).
  - A new screw that matches one of these patterns gets those cuts whether or not you want them.
- Policy: FASTENER-POLICY A (one spec, PH1 by hand), B (boss rules, layer orientation), G (straight-driver rule and
  audit model), H (records) (`FASTENER-POLICY.md:7-151`). Memory rule: grip any M4 from below. Long bits and plugged
  holes are allowed.

## 4. Adding a new printed part end to end (template: R1's pi_keeper)

1. **Module** `printed_<x>.py` must provide:
   - `PRINT = {pid: dict(face_down, supports, notes)}`;
   - `build(layout) -> {pid: cq.Workplane}` (one valid solid, assembly frame, final pose);
   - optional `build_part(layout, pid)`.
   - Imports are limited to math, cadquery and d2_common. Copy `printed_keeper.py` (header 1-27, build_part 70-88)
     or the dispatcher in `printed_small.py:205-214`.
2. **layout.PARTS[pid]** (pattern `layout.py:968-971`):
   - fields: module, material, colour (must be a `build_d2.COLOURS` key: satin silver, black or clear/natural,
     `build_d2.py:319`), face_down, owner (an OWNERS key, 653-655/972), infill (shell, base_grip, small, tpu or
     thin), envelope (a B box; contract excess <= 0.001), supports;
   - `build_d2.build_printed` (112-145) loads it by module and stubs it if the import or build fails.
3. **Registries:**
   - MATES (658-672; kinds contact, slide, press, "interference 0.1", clearance);
   - STEPS adds (+ STEP_VIEWS in build_d2 if it is a new step);
   - INSERTIONS (and REMOVALS or LATCH_FREE);
   - LOAD_BEARING_PARTS (818/981);
   - CRITICAL_FEATURES with a class (FEATURE_CLASS_RULES regex, 1155-1168/1277);
   - CRITICAL_JOINTS: add the part to J7's `parts` and its probes to `required` (932-934). A load-bearing part in no
     joint FAILs (`checks.py:1062-1065`). REQUIRED_JOINT_IDS is fixed (954-955).
   - Optional: SECTIONS (879+), EXPLODE (`build_d2.py:364`), `loaded_boxes` for the thin-wall screen
     (`checks.py:446-466`).
4. **Exports are automatic:** STL in print pose, STEP, print-manifest row (mass = volume x density x infill),
   modifier meshes if the part has screws and shell/base_grip infill (`build_d2.py:201-273`), and a slicer_review
   evidence item (`state_items`, `build_d2.py:997-1010`).
5. **Tables and BOM:**
   - `make_tables.printed_rows()` (`make_tables.py:195-227`) takes volume and mass from the manifest. Without a
     manifest row it calls `estimate_volume(pid)`, which **raises KeyError for an unknown id**
     (`make_tables.py:126-164`): build first, or add a branch.
   - Also update SETTINGS (221) for a new infill class.
   - Blocks: `make_tables.py:760-763` (DESIGN parts/cots/checks/counts, PRINT-GUIDE print/beds, ASSEMBLY
     steps/screws). The count lint checks "n prints/STLs/screws" text.
   - BOM: `electronics/gs8-d2-v1/make_bom.py` reads `MT.printed_rows()` (157-167). Printed parts need no BOM line;
     a new COTS id needs a LINES row with ref = the id, or an INCLUDED_IN entry (117-136), else it shows "not
     covered".
6. **Tests:**
   - pattern `test_keeper.py` / `test_tub.py` (envelope, beds, keep-outs, COTS boxes, pair overlaps, its sweeps and
     removals, its CRITICAL_FEATURES), run through `run_locked.py`;
   - `test_hood_panel.py:80-84` checks the lens/camera cylinders against the hood;
   - `test_r3_regressions.py` tests checker logic only.
   - Exploratory forks use `candidate-fr1` (FR_JOINTS with `replaces`, `checks.py:1039-1061`). FR1 changes J1 (hood
     yslide), J3 (panel A2) and J9, so any hood- or panel-borne J7 support interacts with it.

**New COTS proxy:**
- `layout.COTS[id]` = dict(name, pn, src, mass, step, box, features) (476-536);
- a builder `f(L, c)` in `cots.py` plus a BUILDERS entry (316-319). The shape must stay inside its box (+0.02,
  `build_d2.cots_containment` 186-194);
- MATES, STEPS adds, CABLE_ENDS if a cable ends there, a BOM line or INCLUDED_IN, COTS_COLOUR (optional), and
  LATCH_FREE/REMOVALS if it appears in an `off` list.
- A heavy lens is a new LENSES entry (segments, mass, com_from_flange, lock_screws) (449-462). `build_d2.py --lens`
  sets `L.LENS` (1462, 1471); mass_com runs for every LENSES entry (1291-1294).

## 5. Every check that touches J7 or the lens (what it asserts)

| Check | Code | Asserts (current result in `out/checks.json`) |
|---|---|---|
| layout self-check | `layout.py:1392-1394` | turret r_in - ring r >= 0.25 (0.25); C_FLANGE_X - 8.5 >= 1.0 (2.1); also every step/mate id known, bed envelopes (1385-1412) |
| contract | `build_d2.py:148-170` | printed part = 1 valid solid inside its PARTS envelope, PRINT entry with matching face_down |
| cots_containment | `build_d2.py:186-194` | gs_camera / c_cs_adapter / lens proxies inside their COTS boxes (+0.02) |
| interference | `checks.py:71-114` | any non-mate pair <= 0.05 mm3; `interference d` mates by depth 2V/A. gs_camera-panel, lens-hood and adapter-hood have no mate, so they must not overlap (all 0.0). tub/gs_camera contact, hood/gs_camera clearance and the thread mates are excluded. |
| mate_overlap | `checks.py:117-138` | contact/slide/clearance mates <= 0.05 mm3 (tub/gs_camera 0.0, hood/gs_camera 0.0) |
| clearance zones | `checks.py:163-168, 183-205` | "J7 camera ring in tub bore" and "in hood bore": zone x -5.15..8.5, +-18.75 about the axis; min gap >= 0.9 x 0.25 = 0.225. Measured 0.25 / 0.25 pass. The zone includes the cs_ring. A collar or clamp inside the bore would have to change this stated clearance. |
| keepouts | `checks.py:209-221` | every printed part vs every KEEPOUTS box <= 0.05 mm3 (ko_fpc_cam, ko_fpc_loop, ko_run_cross, ko_exhaust, ko_sd, ko_qt_lead, ko_lead_wall near J7) |
| cable_routes | `checks.py:239-290` | fpc chain continuity (>= 1.0 passage), the end box within 1.0 of the gs_camera box (ko_fpc_cam stops 0.2 behind the cover), route estimate + allowance <= 200 mm |
| thin_wall (screen) | `checks.py:376-466` | area share < MIN_WALL <= 2 %. The tub loaded zones are the pads, Pi bosses and lip, **not** the seat or pins. |
| critical_features + joints | `checks.py:888-1066`; registry `layout.py:932-934` | J7_camera (parts tub, panel) requires tub_front_wall_seat (2.5 vs 1.6), tub_cam_pin_0/1 (1.9 vs pin 1.6), panel_cam_keeper (3.33 vs lug 1.6) and tub_rib_l_tip (1.25 vs land 1.2). All pass. A required id that is missing or failing FAILs J7. Deleting J7 FAILs (REQUIRED_JOINT_IDS). |
| driver | `checks.py:470-514` | no J7 screw today; a new one is audited at its step |
| boss_geometry | `checks.py:748-803` | only for SCREWS entries |
| sweeps | `checks.py:554-648` | camera_in (step 7) and panel_on (step 8, camera as obstacle) 0 hits. Adapter and lens are not swept. |
| removals | `checks.py:1232-1374` | camera_out passes (context = final minus panel, lens, adapter); LATCH_FREE coverage |
| mass_com | `checks.py:652-678`; `build_d2.py:1291-1294, 1344-1345` | reported for each LENSES entry; status pass if total > 0 and no stubs. **No balance limit.** |
| owner tests | `test_hood_panel.py:80-84` | lens segments + ring/cs_ring/c_adapter cylinders vs hood: 0 mm3 |
| renders | `build_d2.py:385` | section-lens-axis view (cut y 0); there is no J7 entry in SECTIONS (`layout.py:879-885`) |

Not checked anywhere: forces, moments, stiffness, creep, contact pressure, preload; the real camera tabs; the
lens-ring rotation envelope (lock screws modelled at one clock position); hand clearance round the lens.

## 6. Mass and centre-of-mass model

- **Printed parts:** solid volume x ASA 1.07e-3 x INFILL_FACTOR (`layout.py:783-787`).
- **COTS:** listed mass at the proxy centroid; the lens uses `lens_spec()['com']` (`checks.py:652-678`).
- Reported: `com_ahead_of_grip_axis = com_x - GRIP['axis_x'] (-47)` and height above GRIP top_z (-8)
  (`checks.py:676-677`). Spec: `SPEC.md:227-231`. Target "0 to +8 mm": `LENS-ZOOM-CANDIDATES.md:60`.
- **Release values** (`out/checks.json`; `DESIGN.md:109-112, 346-349`):
  - Kowa: 887.7 g, CoM (-43.27, 0.84, 26.57), **+3.73**.
  - Fujinon: 772.7 g, (-55.89, 0.97, 21.60), **-8.89**.
  - Items: gs_camera 34 g at (-13.1, 0, 60); c_cs_adapter 6 g at (8.1, 0, 60); Kowa 215 g at (38.9, 0, 60).
- **Sensitivity (my arithmetic):** adding m g at x_s moves the Kowa CoM by m(x_s + 43.27)/(887.7 + m).
  - 10 g at x 0 gives +0.48 mm; 20 g at x +20 gives +1.39 mm.
  - About 64 g at x +20 reaches the +8 limit.
  - A lens moved by dx moves the CoM by 0.242 dx. If s0.2 is right (lens about 5-10 back), Kowa becomes about +1.3
    to +2.5.
- **Zoom estimates** (`LENS-ZOOM-CANDIDATES.md:62-68`): Computar 305 g about +15; Optivaron 600 g about +41.

## 7. Thermal context (creep)

- The camera dissipates 0.4 W in every workload state (`airflow/params.json` heat S1/S2/S3; placed in the "camera
  box"). The board total is 8.0 / 12.3 / 22.1 W (S1/S2/S3).
- **Network model** (`airflow/out/network.md:7-26, 75-85`; ambient 30 C, well-mixed body node):
  - covered fins, open plenum, walls UA 0.20 W/K: body air **45.3 / 53.7 / 70.3 C** (S1/S2/S3); adiabatic 59 / 75 /
    106 C;
  - proxy as drawn: 57.5 / 72.6 / 105.6 C with walls.
  - The plenum recirculates 35-87 %. Line 15 names "the camera above the plenum" as a detail that moves the result.
- **3D LBM study:** PAUSED by the user, partial and unverified (`airflow/NOTES.md:330-345`; r4 banner: superseded
  output).
  - Its camera probe (1230 cells; mean speed 0.15 m/s, mean air age 23 s) reports S2 UA0.20 mean 120 C / max 382 C
    (`airflow/out/metrics-2.0-finaxis.json` thermal.*.probes.probe__camera). These are model flags, not
    temperatures.
- **Geometry:** the camera underside (z 40.25) sits 4 mm above the exhaust plenum `ko_exhaust` (z <= 36.2) and the
  cooler top (36.3), at the front wall. The Active Cooler fin exit points +X toward it (`layout.py:487`).
- **Gate:** G-W11 (10 min at 30 C ambient, SoC < 80 C; `airflow/AIRFLOW-BRIEF.md:16`).
- **Conclusion for creep design: assume 45-70 C air round the mount in use (network, walls).** The real value is
  open until G-W11 / thermocouples. The mount plastic grade is unknown.

## 8. Free-space map ([probe]: 0 mm3 against tub, hood, panel, base_grip, pi_keeper, plunger STEP + gs_camera, c_cs_adapter, lens, pi5, cooler, microsd proxies; no KEEPOUTS overlap unless stated)

**Inside the body round the camera module** (camera box x -24.47..-5.2, y +-19.75, z 40.25..79.75):

| Id | Box B(x0, x1, y0, y1, z0, z1) | Bounded by | Who could own a feature there |
|---|---|---|---|
| F1 above | (-24.47, -5.2, -27.3, 16.5, 80.0, 94.0) | hk3 hook/ledge zone y >= 16.5 (z 83.3-96.8), roof rib y 8.4-10 at z >= 94.3, stack fin y <= -27.6. The real lock tab reaches z about 80-82 (unmodelled). | hood (drops at step 5, before the camera: keep z > 81.75 + SLIDE over the camera_in path, which runs at z +2), or panel (slides -Y at step 8 above the camera) |
| F2 right | (-24.0, -5.2, -27.3, -19.75, 44.0, 80.0) | hood stack fin/post y <= -27.6; ko_lead_wall below z 44 (y <= -26); right wall y -32.5 (vents out_wall z 21-37 below) | hood (fin is already there, x -24..-6.5), or tub right wall (prints on the bed: features grow +Y, the easy direction), or a screw from the right (axis +Y; `printed_tub._right` auto-counterbores) |
| F3 left | (-24.47, -6.6, 19.75, 32.2, 41.0, 79.75) | panel locate rib x >= -6.55; rib_l below z 41; keeper x <= -24.67. **This is the camera's insertion lane at step 7** (sweep at z 42.25-81.75). | panel only (goes on after the camera, slides -Y; it must stay y > 19.75 + clearance or pass outside the camera silhouette) |
| F4 under | (-21.0, -5.2, -25.5, 19.75, 36.5, 40.25): a 3.75 mm slab | cooler top 36.3, ko_exhaust top 36.2, ko_run_cross x <= -21, ko_qt_lead y <= -25.8, stack post y <= -27.6 | panel only (a -Y sliding shelf). A tub feature here blocks the Pi drop (step 4), which is why rib_r and the baffle were deleted (`printed_tub.py:207-216`). |
| F5 behind | (-27.5, -24.67, -19.75, 3.5, 47.5, 79.75) | keeper finger y >= 4 (z 66-76), ko_fpc_cam z <= 47, post_f x <= -27.5 (z 81.5-89.5) | panel (as the keeper) |
| bore drop | hood truncated teardrop under the ring: z 40.76-41.74, y +-6.5, x -2.5..8.5 (empty) | - | hood |

**Round the ring, CS ring and adapter (inside the bores):**
- The dia 36 ring (proxy) sits in the dia 36.5 bores: 0.25 radial; tub teardrop void toward +Y (apex y 25.8); hood
  drop toward -Z.
- **Turret annulus** r 15.4..18.2, x 0.6..8.5: empty (round the cs_ring r 15.375 and the adapter r 15.0). At most
  2.9 radial and 7.9 long.
- **Turret front to Kowa rear:** x 8.5..10.6, annulus r 15.0..25.5 (2.1 axial) is empty. Inside it are the adapter
  (r 15) and the lens thread (r 12.7).
- The tub-to-plate gap x -2.7..-2.5 (0.2) holds the ring, the plunger stem and ko_sd.

**Outside, in front of the body** (x >= -0.5):

| Id | Box | Contents / blockers |
|---|---|---|
| F8a below lens | (8.5, 67.2, -32, 32, 0.3, 33.0) | empty. Kowa bottom z 33 (Fujinon z 40.5). |
| F8b below turret | (1.0, 8.5, -32, 32, 0.3, 29.9) | empty. Behind it, the plate face (x 0) carries the plunger guard (x 0..1, y 2-16, z 16-25), the SD slot (y -11.5..0.5, z 15.9-18.6; tweezers from +X), out_band exhaust slots (y -26.5..17.5, z 25.9-29.7) and out_corner (y -31..-21, z 32-38). **Anything here sits in the exhaust jet and in the finger/tweezer path.** |
| F8c in front of the base | (-0.5, 67.2, -35.2, 35.2, -8.0, 0.3) | empty. Base front x -0.5 with a 5 mm 45 deg underside chamfer. Grip fingers below z -8 behind x -23 (no keep-out). Tripod clamp keep-out only at x -132..-82. |
| F9 right of lens | (0, 67.2, -35, -27, 33, 87) | turret (x 0..8.5) and the **Kowa lock screws** y -32..-26, x 18-23.2 and 42-47.2. They rotate with the iris/focus rings (envelope not modelled). |
| F11 left / F12 above lens | (0, 67.2, 27, 35, 33, 87) / (0, 67.2, -27, 27, 87, 100) | only the turret (x 0..8.5). Left is the panel/dial side. |

**Access by direction:**
- **Front (+X):** the only fixed parts are the hood plate and turret.
  - A support reaching the lens from the body must come from the hood plate/turret (hood path via hooks with 0.1 play
    and a 45 deg return on hk3) or from the base front (base prints top-down: a new part, or a bolt-on).
  - Keep clear of the plunger finger opening, SD slot, exhaust slots and the lock-screw sweep.
  - The tripod nut is far behind (x -107, under the grip region).
- **Below (inside):** blocked by the Pi stack/cooler (drops from above at step 4), the plenum and the run lead. Only
  the 3.75 mm slab F4 is free, reachable only by a -Y sliding panel feature.
- **Right (-Y):** the tub right wall is the bed face in print, so ribs grow +Y easily.
  - A +Y screw through the right wall works like s_r1/s_r2 (counterbore auto-cut).
  - The hood stack fin already stands at y -31.3..-27.6, x -24..-6.5, z 45..97.8.
  - The driver audit needs the bit 6.5 x 40 + handle 30 x 100 clear to the right: open space outside, as for s_r1.
- **Left (+Y, panel side):** open until step 8 (camera insertion lane); closed by the panel. Panel features slide
  -Y; the keeper finger is the precedent.
- **Above:** hood roof (hk3 at y 22, roof rib at y 8.4-10, stack fin at y <= -27.6). A hood feature must clear
  camera_in (camera at z +2 during the -Y slide) and the real lock tab.
- **Behind:** keeper finger, FPC exit and loop, post_f.

## 9. Load-path facts in the code (and my arithmetic)

- **Moment arm to the seat** (x -5.2): Kowa CoM x 38.9 gives 44.1 mm. Static 0.215 x 9.81 x 0.0441 = **0.093 N m**;
  at 5 g, 0.47 N m. Fujinon 41.1 mm gives 0.040 / 0.20 N m.
  - The arm to the mount-to-PCB interface is longer. If the PCB front is about 11.5 behind the seat in this frame
    (10.35 mount base + 1.2), the arm is about 56 mm and Kowa static is about 0.12 N m.
  - If s0.2 holds (lens about 5-10 back), subtract 5-10 mm from every arm.
- **Rigid-body freedom with no preload** (the module is only pushed onto the seat by whatever the lens load does;
  the pins are along X and do not resist lift-off):
  - **Nose-down (lens weight):** pivot on the upper land edge (z 79.75). The lower part lifts -X until the keeper's
    lower edge (z 66, 13.75 below the pivot) closes its 0.2 gap: **0.2/13.75 rad = 0.83 deg**. Without the keeper,
    the ring front end (5.8 ahead) would reach the bore after 0.25/5.8 rad = 2.5 deg.
  - **Nose-up:** pivot on the lower edge (z 40.25); the keeper top (z 76, 35.75 above) closes at 0.32 deg.
  - **Yaw:** the keeper covers only y 4..19.75. Tip toward -Y pivots on y -19.75 (keeper 23.75-39.5 away): 0.29 deg.
    Tip toward +Y pivots on y +19.75 (keeper 0-15.75 away): 0.73 deg.
  - Friction and the FPC stiffness are ignored. Under the Kowa's own weight, the module can therefore sit up to
    about 0.8 deg nose-down on its upper land edge.
  - **Rigid rocking moves the sensor and lens together.** It shifts the aim: 0.83 deg is about 1.8 % of the 45 deg
    horizontal field (6 mm on 5.02 mm), about 27 px. It does not tilt focus.
  - The focus-tilt budget (about +-12 um over 5 mm, i.e. 0.27-0.3 deg; `LENS-ZOOM-CANDIDATES.md:97-99`) applies to
    lens-vs-sensor tilt, which is mount deflection and creep. The doc's "0.25 mm = about 0.8 deg" assumes a
    different pivot.
  - A bore contact before the seat rotates loads the mount directly.
- **Seat land inside the 39.5 proxy square** [probe]: 479 mm2, evenly split by quadrant. The probe for it
  (`tub_front_wall_seat`) measures elsewhere. The front wall is a 2.5 plate (64.7 x 95 free span), restrained by the
  right wall, floor, rib_l (bottom-left) and the panel end lands.
- **Ring rotation:** "never clamped" (`layout.py:205`). D2 has no back-focus procedure or access in its docs (grep:
  only `ASSEMBLY.md:216` "turns freely" and the G-CAM-1 check). The real camera's lock tab and its screw (the
  maker's back-focus lock) are not modelled, and their access is not considered.

## 10. Open items to settle before the CAD

1. **MP-CAM measurements** (`MEASURED-PARTS.md:74-83`), extended to cover:
   - which element is dia 36 and which is dia 30.75, and their lengths;
   - the mount-base front-face size and shape (does it clear the dia 36.5 bore?);
   - the lock tab and tripod tab (is the tripod tab removable?);
   - the 4 hole diameters, and whether the mount screws occupy those holes;
   - the CS flange position from the cover rear;
   - whether the adapter OD is 30;
   - which part carries the lens thread (needed for "clamp the ring" option 1).
2. **Kowa non-rotating barrel sections and the lock-screw sweep:** the segment labels are proxy-only
   (`layout.py:453-457`).
3. **Interior air temperature at the camera** (G-W11 + thermocouple). The study is paused.
4. **A load criterion in code** (none exists): any new support needs a CRITICAL_FEATURES entry, a J7 `required`
   probe, a section view and (if wanted) a balance assertion. `mass_com` asserts nothing today.
