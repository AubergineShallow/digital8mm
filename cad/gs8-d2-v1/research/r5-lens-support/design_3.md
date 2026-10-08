# D2 heavy-lens sag fix: designer 3, "lens support" (2026-10-06)

**Scope.** This is read-only design work: no repository file was edited, and build_d2.py and run_locked.py were not run.

**Evidence (all in `scratchpad/sag/`):**
- `d3_plate.py`, `d3_plate2.py`, `d3_plate3.py` (+ `.json`): an ACM plate finite-element model of the tub front wall. It was validated against beam theory (within 4-9 %).
- `d3_probe.py` (+ `d3_probe_d2.json`, `d3_probe_xf2.5.json`): a CadQuery build of the proposed parts, checked against the release STEP parts, the COTS proxies, the keep-outs and the existing sweeps.
- `d3_loads.py` (+ `.json`): load-path arithmetic.

**Frame.** Coordinates are D2 assembly coordinates, with C_FLANGE_X = +10.6 unless stated. Every lens-side coordinate is derived from C_FLANGE_X, so it moves with the stack correction described below.

## 0. Premises checked first (they change the design)

1. **The camera's lens mount is aluminium, not plastic.** Sources: the HQ/GS briefs and the RPi filter-removal procedure (dossier_external s1).
   - The compliant link is the **housing-to-PCB joint**: 2 M2 screws with nylon washers on a sticky gasket.
   - Per the GS rear-cover holes, the 2 screws sit on the horizontal centreline, so a nose-down pitch moment is resisted mainly by the gasket. That joint is the creep path, together with the unpreloaded J7 rocking (about 0.8 deg).
2. **D2's stack is very likely wrong.** I measured `gs_side_zoom.png` at about 20 px/mm:
   - The front 5.8 element is about 31 tall: it is the C-CS adapter.
   - The 1.2 serrated element is about 36 tall: it is the back-focus ring (BFAR) head.
   - D2 models a dia 36 x 5.8 ring plus a 5 mm "CS ring", so the real C flange is probably about 8 mm further back (x about +2.5, not +10.6).
   - Probe `d3_probe.py 2.5`: at that stack, the corrected Kowa's dia 42 knurl collides with today's hood turret (1169 mm3 overlap). The turret has to change anyway.
3. **D2's Kowa segment table is reversed.** The Kowa drawing (`kowa_zoom.png`, checked) has, from the flange:

   | x from flange | Feature |
   |---|---|
   | 0..2.2 | dia 31.5 spigot |
   | **2.2..7.6** | **dia 42 knurled ring**: the only section that neither rotates nor translates (inferred) |
   | 10.6..22.4 | focus ring dia 41.7, with an M2 thumb screw at 14.4 |
   | 23.1..29.2 | label barrel |
   | 30.9..36.6 | iris ring, thumb screw at 33.0 |
   | 41.7..50.5 | dia 54 front barrel |

   D2 has r 27 at 5..15 and lock screws at 10/34.
4. **Today no chassis feature preloads J7.** The pins, lands and keeper (0.2 gap) let the module rock, and every lens moment crosses the gasket joint.

## 1. Concept (5 lines) and why it fixes the sag

1. **Carry the lens; hang the camera on it.** A per-lens printed **Lens Collar Bearing (LCB)** replaces the hood turret. It bolts straight onto the tub front-wall outer face and pinches the lens's non-rotating barrel band in a split sleeve, after back focus is set and locked.
2. The LCB's D-shaped rear face (57 wide) bears on the tub wall over almost its whole width, between the right-wall fold and the panel. It is held by s_l1 (into a new tub boss) and by s_l2/s_l3 (through the wall into 2 new panel bosses, which also tie the wall's free left edge).
3. Lens moment path: lens band -> LCB -> tub front wall -> right wall, floor, panel -> base/grip.
4. **The camera (34 g) hangs on the lens through its own adapter and BFAR threads, and the chassis neither preloads nor locates its PCB.** The following stop carrying the lens moment:
   - the adapter-to-BFAR and BFAR-to-housing threads;
   - the housing-to-PCB gasket joint and the PCB;
   - the J7 pins, lands and keeper;
   - the hood hooks.
   They now carry only the module's own weight (about 0.003 N m, against 0.09-0.42 N m today).
5. Heavy zooms get their own LCB, with a long sleeve on their fixed rear barrel (Computar dia 48.5 x 22). Hand loads go through the same rigid path. The short Kowa band is the weak case.

**Departures from the suggested starting angle, and why:**
- *Rigid, set-then-lock, not compliant.* A spring cradle carries the weight, but a hand load (the priority) just deflects the spring and passes into the camera.
- *No axial preload of the module.* Once the chassis holds the lens, preloading the module onto the wall would create a second, parallel path through the module. The pinched chain is already fixed. The keeper stays as a 0.2 shock backstop.
- *Anchor: tub wall + panel, not the base or the hood.*
  - A base-mounted yoke under the lens would block the plunger, SD slot and exhaust (front face x 0, z 15.9-38) and the grip fingers.
  - The hood floats on 4 hooks (0.1 play, cam-out return on hk3).
  - FE result: a 57 mm rigid disc on the 2.5 wall rotates 0.079 deg/N m, against 0.48-0.74 for today's r 20 seat.
- *Cradle and strap in one.* The sleeve is a 360 deg split clamp, so it takes loads in every direction, including lift.

## 2. Geometry (D2 assembly frame)

**Definitions.**
- XF = C_FLANGE_X: +10.6 today, about +2.5 if premise 0.2 holds.
- Kowa support band = (r 21.0, flange +2.2..+7.6). This becomes a new `LENSES[...]['support']` entry.
- TRAVEL = 1.5: the BFAR/lens back-focus range allowed inside the sleeve.
- **Outline "D":** a circle r 28.5 about (y 0, z 60) above its 45 deg tangent points (y +-20.15, z 39.85), then 45 deg flanks down to a flat at z 33.0 (y +-13.3). The flat keeps the part clear of the out_band and out_corner exhaust.

### 2.1 New printed part `lcb` (ASA, black)

- **Print:** rear face on the bed (`face_down '-X'`). The rear face is also the datum.
- **Supports:** none.
- **Infill:** shell (0.85).
- **Mass and envelope:**
  - D2 stack: 22.0 g by probe, plus about 1 g for the pinch boss; envelope B(-2.7, 19.7, -31.6, 33.2, 32.5, 93.7).
  - Real stack (XF 2.5): 11.6 g; x -2.7..11.6.

| Feature | Geometry (D2 numbers; formula) |
|---|---|
| Body | Outline D extruded x -2.7 .. x_front = XF + 7.6 + 1.5 = **19.7** |
| Rear face | x -2.7: bears on the tub front-wall outer face (contact land ~1270 mm2 + ears). Bed face: 0.6 x 45 deg bed chamfer, no fillets |
| Rear bore | dia **37.5**, x -2.7 .. x_s0 = XF + 2.2 - 1.5 = **11.3** (0.75 radial round the D2 ring r 18; 3.75 to the adapter) |
| Sleeve bore | dia **42.3** (band 42.0 + 2 x 0.15 LOCATE), x 11.3..19.7 (8.4 long; the 5.4 band sits anywhere within +-1.5). Front at flange +9.1: **1.5 clear of the Kowa focus ring** (flange +10.6) and 3.4 clear of its thumb-screw sweep |
| Slit | 2.0 wide at **3 o'clock** (plane z 59..61, y <= -21.15 out through the boss), x 10.3..19.7 |
| Relief | circumferential slot 1.5 wide, x 9.8..11.3, over 150 deg centred on 3 o'clock, bore to OD. The sleeve becomes a C-ring hinged on its +Y 210 deg; it closes 1 mm with about 4 N |
| Pinch boss | outline grows to y -31.5 for z 49..71, x 11.3..19.7. Screw **s_lp** axis (0, 0, -1) at (x 15.5, y -26.25): cbore dia 7 from z 71 to **z 63.0** (head face); clearance dia 3.4 z 63..61 (jaw 2.0 under head); pilot dia 2.5 z 59..50. Walls: cbore 1.8 / 1.75, pilot 4.45 / 4.0 |
| Ears | S1 (y 0, z 88.5), S2 (y 27.0, z 74.0), S3 (y 27.0, z 46.0): discs r 4.7 + 9.4-wide webs, x -2.7..+0.3 (3.0 thick, 0.3 proud of the plate face). Clearance dia 3.4 from x -2.7 to **-0.85** (head face; 1.85 under the head); cbore dia 7 from -0.85 forward, open through the body. This gives an open 3.5-deep channel at 12 o'clock for S1 and 1.5-deep scallops on the OD for S2/S3 |
| Lip (recommended) | 1.0-wide flange round outline D at x 0.15..1.15 (0.15 off the plate face), 45 deg underside. It retains the hood plate's lower section and hides the opening gap |

Overhangs in print (axis vertical):
- the ears sit at the base;
- the sleeve is an inward step;
- the slit, relief and boss are vertical walls;
- the lip has a 45 deg underside;
- the pinch pilot is horizontal, dia 2.5 (< 8, so no teardrop).

Stress directions: the hoop and pinch stresses are in-layer. The axial bending stresses from the lens moment cross the layers but are about 0.1-0.3 MPa (section 3).

### 2.2 Hood (`printed_hood.py`)

**Delete** `_turret`, `_bore_tool`, HOOD `turret`/`turret_b` and the turret tree-support note.

**Cut the lens opening:**
- Shape: outline D offset **+0.5**, plus ear notches r 5.2 with small teardrops toward assembly -Z (print-up).
- Front edge: 45 deg x 1.0 bevel to nest the lip.
- Webs (`d3_opening.py`):

  | To | Web |
  |---|---|
  | out_band | 2.8 |
  | out_corner | 1.41 |
  | plunger pocket | 7.8 |
  | SD slot | 13.9 |
  | left plate edge | 2.9 |
  | right plate edge | 3.35 |
  | top | 3.4 |

- Print (roof down): the flat becomes a **27 mm bridge** (< 30) with 45 deg flanks. **No supports are needed any more.**
- The plate no longer touches any lens load.

### 2.3 Tub (`printed_tub.py`)

- **Lens bore:** teardrop r 18.25 -> **18.75** (dia 37.5; apex +Y at y 26.5, z 60). The BFAR head/ring then floats 0.75 radially.
- **boss_l1** for s_l1:
  - dia 8 along X at (y 0, z 88.5), x -5.2..-13.85;
  - pilot dia 2.5 from the wall's outer face x -2.7 to -13.85, open end (11.15 deep, engage 10.15);
  - a 45 deg corbel under its print-down (-Y) side: triangle (x -5.2, y -12.65), (x -13.85, y -4.0), (x -5.2, y -4.0), z 84.5..92.5.
  - It sits in free zone F1, above the camera_in sweep: probe gives 0 mm3 against the sweep and the hood drop, and 2.69 to the hood.
  - It is 4.5 above the real top tab and its lock screw.
- **Clearance holes:** dia 3.4 along X through the wall at (27.0, 74.0) and (27.0, 46.0) for s_l2/s_l3. They are 13 mm from the bore teardrop flank and 3.5 from the wall's left edge.
- **Auto cuts:** none trigger (`_right` handles +Y screws, `_floor` handles +Z).

### 2.4 Panel (`printed_panel.py`)

- **New bosses:** PANEL_BOSSES `boss_l2` B(-13.85, -5.35, 22.5, 32.7, 70, 78) and `boss_l3` B(-13.85, -5.35, 22.5, 32.7, 42, 50).
  - They merge with the existing front locate rib (x -6.55..-5.35, z 41.3..70).
  - Front faces sit 0.15 behind the tub wall (LOCATE).
  - Pilots dia 2.5 along X at y 27.0, from x -5.35 to -13.85 (8.5 deep).
- **Print:** they grow -Y from the inner face, vertical in print, no overhang.
- **Clearances:**
  - 1.0 above rib_l (top z 41.0);
  - 2.75 from the camera proxy (y 19.75);
  - panel_on sweep 0 mm3 against the camera, tub and hood (probe).
  - They pass outside the camera silhouette exactly as the keeper does.

### 2.5 Screws (all PT 3.0 x 12, PH1; 4 new, total +4)

| id | joins / into | axis | head_point | tip | engage | step | driver |
|---|---|---|---|---|---|---|---|
| s_l1 | lcb, tub / tub boss_l1 | (-1,0,0) | (-0.85, 0, 88.5) | (-12.85, 0, 88.5) | 10.15 (wall 2.5 + boss) | 9 | +X from the front through the S1 channel, lens not yet fitted |
| s_l2 | lcb, tub, panel / panel boss_l2 | (-1,0,0) | (-0.85, 27.0, 74.0) | (-12.85, 27.0, 74.0) | 7.5 | 9 | as s_l1. The handle (dia 30) sits in front of the body: nothing there before the lens |
| s_l3 | lcb, tub, panel / panel boss_l3 | (-1,0,0) | (-0.85, 27.0, 46.0) | (-12.85, 27.0, 46.0) | 7.5 | 9 | as s_l1 |
| s_lp | lcb (pinch) / lcb pinch boss | (0,0,-1) | (15.5, -26.25, 63.0) | (15.5, -26.25, 51.0) | 8.0 | 9 | from above. Bit z 63..103, handle z 103..203 at x 0.5..30.5: clear of the body (x <= 0) and the lens (r <= 21). Real stack: x 7.4, handle above z 100 |

**Torques:**
- s_l1..3: 0.35-0.5 N m (policy).
- s_lp: **0.25 N m, snug.** That gives about 200 N of clamp force, 3.2 MPa in-layer hoop stress initially, about 1.8 MPa band pressure.

**Counterbores.**
- s_l1..3: d 7.0 in `lcb`, x -0.85..x_front. The `cbore` dict needs an x range; today it supports y/z only.
- s_lp: d 7.0, z 63..71.

**Reuse.** All 4 obey the 5-reuse rule. The LCB is per lens, so s_l1..3 cycle once per lens swap. After 5 swaps, use the policy E insert fallback; OD 8 leaves a 2.0 wall.

### 2.6 Other lens variants (same outline, ears, screws; only the sleeve changes)

| Lens | Support band (from flange) | Sleeve bore | Sleeve | Status |
|---|---|---|---|---|
| Fujinon HF6XA-5M | dia 39.0, +1.0..+8.0 | 39.3 | XF-0.5..XF+9.5 | **placeholder** (G-LENS) |
| Computar H6Z0812 | dia 48.5 fixed rear barrel, +1..+25.5 | 48.8 | XF-0.5..XF+24.0 (1.5 before the iris gear) | drawing; it fits the same outline (wall 4.1) |
| Adapter-clamp fallback "LCB-A" (any C lens) | C-CS adapter knurl dia 30.75, about 5 long | 31.05 | over the adapter | for lenses without a usable fixed section. It bypasses the BFAR, housing and PCB, but loads the lens's own C thread (not for zooms) |

## 3. Load path with numbers

### Model
- **Moments.** M_wall is taken about the LCB/wall interface (x -2.7). M_sleeve is taken about the band centre.
- **Lens data.** Kowa CoM is flange +28.3 (D2 value; balance-check it). Zoom CoM and arms follow LENS-ZOOM-CANDIDATES: Computar CoM +39.2, Optivaron +55.2 (band assumed +2..+22).
- **Hand load.** Kowa and Fujinon: 15 N at flange +50/+45. Zooms: 20 N at +70/+80.
- **Wall.** ACM plate FE of the 2.5 tub front wall:
  - right and bottom edges clamped (wall folds);
  - left edge simply supported (S2/S3 tie it to the panel; "free" gives the upper bound);
  - top edge free;
  - exhaust windows, plunger hole and SD slot modelled as holes;
  - the LCB face modelled as a rigid disc r 28.5.
- **Wall FE results:**
  - pitch: **0.079 deg/N m** (0.146 with a free left edge);
  - yaw: 0.0075 deg/N m;
  - wall stress per N m: 2.3 MPa along Z (in-layer for the tub print), local peak 4.7 MPa along Y (across layers, in the strip next to S2).
  - Today's r 20 seat: 0.48-0.74 deg/N m and 5.0-9.8 MPa/N m.
- **Sleeve.** Tilt stiffness k = 0.5 x (E/t)(pi/2) r L^3/12 (Winkler; factor 0.5 for the knurl and slit), with E 2000 and t 3.5:
  - Kowa (L 5.4): 1.2e5 N mm/rad;
  - Computar (L 22): 9.7e6 N mm/rad.
- **Creep.** 1000 h at 45-50 C: x 2.2 on the static case (creep modulus about 900 MPa).

### Results (aim = whole lens+camera chain relative to the body; it does not tilt focus)

| Lens | Case | M_wall N m | M_sleeve N m | Aim deg (FE nominal..bound) | Wall stress MPa (Z..Y peak) |
|---|---|---|---|---|---|
| Kowa 215 g | static | 0.088 | 0.049 | 0.030..0.036 (creep 0.066..0.079) | 0.2..0.4 |
| | 5 g | 0.44 | 0.25 | 0.15..0.18 | 1.0..2.1 |
| | hand 15 N | 0.95 | 0.68 | 0.39..0.45 (elastic) | 2.2..4.5 |
| Fujinon 100 g | static / 5 g / hand | 0.038 / 0.19 / 0.88 | 0.02 / 0.10 / 0.61 | 0.008 / 0.04 / 0.21..0.27 | <= 4.1 |
| Computar 305 g | static | 0.157 | 0.081 | 0.013..0.023 (creep 0.029..0.051) | 0.36..0.74 |
| | 5 g | 0.79 | 0.41 | 0.064..0.117 | 1.8..3.7 |
| | hand 20 N | 1.67 | 1.16 | 0.14..0.25 | 3.8..7.8 |
| Optivaron 600 g | static | 0.40 | 0.25 | 0.033..0.060 (creep 0.073..0.13) | 0.93..1.9 |
| | 5 g | 2.02 | 1.27 | 0.17..0.30 | 4.6..9.5 |
| | hand 20 N | 1.87 | 1.36 | 0.16..0.28 | 4.3..8.8 |

**Today (Kowa static):**
- 0.093 N m on the r 20 seat, giving 0.045-0.069 deg of wall flex;
- plus up to **0.83 deg** of free rocking before the keeper touches;
- plus the full moment through the gasket joint.

For the 600 g zoom, today's seat would put 0.42 N m through the gasket joint.

### How much of the moment reaches the camera

**Path.** The LCB is the only chassis support of the lens+camera chain. The module has no parallel path:
- J7 gives at least 0.45 mm radial float (section 4);
- the keeper keeps its 0.2 gap;
- the seat lands lie inside the LCB's rigid-disc region of the wall, so they move with it.

**What remains:**
- **Module on the BFAR thread:** 0.034 kg x 9.81 x about 10 mm = **0.0033 N m** static, 0.017 N m at 5 g.
- **Housing-to-PCB joint:** only the PCB, sensor and cover (about 15 g at about 5 mm) = **0.0007 N m**. That is about 1 % of today's Kowa load and 0.2 % of today's 600 g zoom load.

### Critical printed sections (allowables)

**Allowables:**
- Sustained, creep-derated, 45-50 C: 4-5 MPa in-layer, 2-3 MPa across layers.
- Short-term: 44 / 32 MPa best case; I use 22 / 16 (factor of safety 2).

| Section | Load | Stress | Verdict |
|---|---|---|---|
| Tub wall (strip next to S2, across layers) | 600 g zoom static, 0.40 N m | <= 1.9 MPa | OK. The FE peak sits on the simply-supported line S2/S3 really clamp, so it is conservative |
| Tub wall | 5 g / hand | <= 9.5 MPa | OK, short-term |
| LCB ring and sleeve in bending (Z about 12,700-14,800 mm3, axial = across layers) | 2.0 N m | 0.14-0.3 MPa | trivial |
| Pinch hoop (in-layer) | 200 N over 7.35 x 8.4 | 3.2 MPa initial | OK; it relaxes |
| Pinch jaw under the head | head bearing | 10.5 MPa | relaxes. Accepted for a snug clamp; re-torque check in G-LCB-1 |
| s_l1..3 | 600 g at 5 g, LCB pivoting on its flat (arms 55.5 / 41 / 13) | 23 / 17 / 5 N per screw | trivial against about 600 N pull-out and the 100-300 N preload |
| Joint gapping | preloaded face; screw preload relaxed to about 100 N each | gaps above about 3 N m (fresh about 9 N m) | above all cases |

**Kowa sleeve gapping.** After relaxation (p about 1 MPa) the band clamp starts to gap at M_sleeve about 0.16 N m (about 0.5 N m fresh).
- Static (0.05) holds.
- 5 g and hand loads open one edge elastically: the band rocks in the pinched bore with lower stiffness and no slip.
- Rotation capacity is 4.5 N m by friction alone, plus the knurl's form fit, against <= 0.2 N m ring torque.

### Image-plane (lens-vs-sensor) tilt

- The joint's tilt stiffness is unknown, about 1e5-1e6 N mm/rad (G-CAM-1).
- **Today:** 0.12 N m at the joint gives 0.007-0.07 deg, and up to about 0.2 deg after creep. That is most of the 0.3 deg budget.
- **With the LCB:** <= 0.003 N m gives **< 0.002 deg** static and < 0.01 deg at 5 g, whatever the lens.
- The whole budget is left for the camera's and lens's own build tilt.

## 4. Alignment: the camera keeps the lens-sensor geometry; the chassis only fixes the aim

**How the lens-sensor geometry stays the camera's own.** The image-plane geometry is set entirely inside the metal chain:
- the lens flange on the adapter;
- the adapter on the BFAR;
- the BFAR, locked by the camera's split-tab screw;
- the housing, gasket and PCB.

The LCB never touches it. Three rules keep any forced displacement out:

1. **The pinch is the last operation (set then lock).** Before it, the sleeve has 0.15 radial clearance, so the lens sits wherever the camera put it. Pinching grips the band; it cannot change the lens-sensor distance or tilt, because those are internal to the threads.
2. **The module must follow the lens, not resist it.** The pinch centres the band on the sleeve axis. The offset between the sleeve axis and the camera's lens axis is:

   | Contribution | Amount |
   |---|---|
   | LCB position (3 screws, dia 3.4 holes on 3.0) | +-0.20 |
   | Sleeve bore print | +-0.10 |
   | Camera seat/pins | +-0.15 |
   | **Total** | **<= 0.45** |

   - **Requirement on J7 (for J7's owner):** after the pinch, no chassis feature may constrain the module radially tighter than 0.5 mm, or touch the PCB or cover except the 0.2 keeper backstop.
   - In the D2 model: pins dia 1.9 -> **1.6** (pin class floor) in the drawing's dia 2.5 holes gives 0.45 radial. The tub bore at 0.75 radial and the LCB rear bore at 0.75 radial never touch the BFAR head.
   - For the real camera, where D2's pins do not reach the PCB 10 mm behind the housing front, the roll key can be loose (for example tines beside the top tab). It only has to hold the module against BFAR torque **before** the pinch. After the pinch, roll is fixed by the chain.
   - Image roll relative to the body: about +-0.4 deg, set at assembly. That is acceptable, and the body is levelled anyway.
3. **No second support moves relative to the LCB.**
   - The seat lands (x -5.2, r <= 22) lie inside the 28.5 rigid-disc zone that the LCB clamps, so they move with the LCB and the lands stay passive.
   - Thermal: ASA sleeve on an aluminium band, about 0.08 mm diametral loosening at +30 K. The module floats, so nothing is forced; the clamp just relaxes slightly (knurl form fit; check in G-LCB-1).

**Aim tolerance (lens axis relative to the body).** It is constant and irrelevant to image quality:
- rear face (bed face) on the wall: +-0.1 deg;
- sleeve bore squareness: +-0.1 deg;
- centring: +-0.3 mm.

## 5. Assembly and service

### Step table rows (layout.STEPS; no renumbering)

| Step | Change |
|---|---|
| 5 | Hood: unchanged process. The plate now has the lens opening, not a turret |
| **7** | Camera as today. **Add `c_cs_adapter`**: after the camera is seated, screw the adapter on **from the front** through the hood opening. New INSERTIONS `adapter_on` [(+20,0,0),0] as a later mover in step 7: it cannot ride on the camera, because during the -Y slide it would cut the tub wall. **Then bench back focus** (below) |
| 8 | Panel as today; it now carries boss_l2/l3 |
| **9** | In this order:<br>1. **LCB** in from the front: INSERTIONS `lcb_on` [(+40,0,0),0]; ears through the opening; rear face onto the wall. Drive **s_l1, s_l2, s_l3** (+X driver, 0.35-0.5 N m).<br>2. **Lens:** `lens_on` [(+60,0,0),0], s_lp backed off. Screw the lens through the sleeve into the adapter until it seats. Check focus on live view (the BFAR is already locked).<br>3. Drive **s_lp** from above, 0.25 N m.<br>4. Then the knobs, eyecup and stick as today.<br>Delete "clock the Kowa lock screws to the right": the thumb screws sit on the rotating rings, so their clock follows the focus/iris setting |

### Back-focus procedure (bench, end of step 7, panel off)

1. Fit a lens to the adapter. It hangs on the camera temporarily, as D2 does today.
2. Power the Pi from a bench supply and open live view.
3. Loosen the BFAR lock screw on the top tab from the open left side, with a small flat driver.
4. Turn lens + adapter + BFAR as one unit.
   - Always finish with an **outward** (unscrewing) motion. The thread reaction then pulls the module onto its seat and takes up backlash.
5. Tighten the lock screw. Unscrew **only the lens**; the adapter stays.
6. Later in step 9 the lens goes back onto the same adapter flange (17.526 reference), so focus repeats. Re-check on live view before pinching.

**Re-setting later:** unpinch s_lp, then turn the lens inside the open sleeve. The lock screw needs:
- (a) the panel off: s_l2/s_l3 out first, s_l1 may stay; or
- (b) if MP-CAM shows the lock-screw head faces +Y: a dia 6 plugged access hole in the panel at (x about -7.8, z about 80).

### Lens swap

1. Unpinch s_lp; unscrew the lens.
2. s_l1..3 out; LCB off.
3. Fit the new lens's LCB; s_l1..3 in.
4. Lens through the sleeve; check focus. Re-set back focus only if the new lens needs it.
5. Pinch.

### Camera removal (REMOVALS `camera_out`)

- `off` = lens, c_cs_adapter, panel. `unscrew` += s_l2, s_l3.
- The LCB may stay on s_l1: the camera leaves -X 11.1, then +Y, behind the wall.

### Hood removal (Pi service)

- `off` += lens, lcb. `unscrew` += s_l1..3.
- Add `lcb_off` (reverse of lcb_on) to REMOVALS. Add a lens LATCH_FREE note: "unpinch s_lp, then unscrew".

## 6. Interactions

- **Fujinon variant:**
  - Builds from `LENSES['fujinon_hf6xa']['support']`, currently a placeholder of dia 39 at +1..+8.
  - 100 g gives the lowest loads.
  - Balance is already at -8.9 mm with or without the LCB (an existing, separate issue).
- **Kowa lock screws:** they ride on the focus (+14.4) and iris (+33.0) rings, at any clock position. Distances from the sweep envelope (r <= 24, flange +12.5..16.3):
  - sleeve front (+9.1): 3.4;
  - pinch boss (x <= flange +9.1): clear.
  - Add keep-out `ko_lens_lock_sweep` so nothing ever grows into it.
- **Turret and hood:**
  - The turret disappears; the LCB takes its look and place. In the D2 stack the "turret" grows 8.5 -> 19.7 long; in the real stack it is about 11.6.
  - J1 drop-on is unchanged: nothing protrudes from the tub at step 5. Hood-drop sweep against the S1 boss is 0 mm3.
  - The plate's lower section is held by 2.9/3.35 side strips and the LCB lip.
- **Hand clearance:**
  - The LCB (dia 57) ends 1.5 behind the Kowa focus ring (dia 41.7) and acts as a finger stop.
  - The pinch boss is on the right (y -31.5, z 49..71), away from the left-hand focus grip.
  - The right hand stays on the grip (x <= -23, z <= -8).
- **FPC, Pi stack, EVF, cables:** untouched. The new bosses are at x >= -13.85; the FPC keep-outs are at x <= -24.67. Probe: 0 mm3 against every KEEPOUTS box, the Pi, cooler and microSD proxies, and the camera_in, panel_on and hood sweeps.
- **rib_l:** unchanged; the boss_l3 bottom is 1.0 above its top.
- **Keeper finger:** unchanged. It is now only a shock backstop; it must keep >= 0.2 gap.
- **Vents, plunger, SD slot:**
  - The LCB bottom flat (z 33) clears the out_band jet (z <= 29.7) better than the turret did (z 30).
  - The 45 deg flank keeps the out_corner slots unshadowed (1.41 web).
  - The plunger guard and SD slot are 7.5+ away.
- **Balance:**
  - D2 stack: the LCB (about 23 g at x 6.0) replaces the turret (about 14 g) and a 2.8 g plate disc, net about +6 g at x +6. Kowa CoM +3.73 -> **about +4.1 mm** (target 0..+8).
  - Real stack: lighter, about +0 g.
  - Zooms stay as in LENS-ZOOM-CANDIDATES (+15 / +41); their balance is a grip/tripod question, not this fix.
- **candidate-fr1 (FR1 J1/J3 changes):** the LCB does not depend on the hood or hooks, and S2/S3 only need panel material at the front-left. Re-run the panel_on sweep on FR1.

## 7. Unknowns to measure (extend the gates) and how the design tolerates them

### G-CAM-1 / MP-CAM additions

1. **Stack** at the infinity BFAR setting for each lens:
   - the C flange position relative to the housing front plane;
   - BFAR pitch and travel.
   This sets C_FLANGE_X. Everything lens-side is derived from it, so the LCB is regenerated, not redesigned.
2. **Housing envelope:**
   - OD (about 35);
   - top tab: front face, lock-screw size and **which side its head faces**;
   - tripod block: kept or removed (if kept, it collides with the cooler/plenum);
   - PCB position.
   s_l1 sits 4.5 above the tab and the panel bosses sit at y >= 22.5, so both are clear whether the D2 proxy or the corrected envelope holds.
3. **Module masses:** housing+BFAR versus PCB+cover+FPC end, for the residual-load figure.
4. **Joint compliance:** dial indicator at the lens front with 3 x the lens mass hung on the lens, measured two ways:
   - module held by its PCB holes;
   - lens held in the LCB.
   This confirms the about-100x reduction.

### G-LENS additions

1. **Kowa knurl:**
   - crest diameter, length and flange position;
   - confirm it neither rotates nor translates while turning focus and iris;
   - CoM by knife edge;
   - rear protrusion 6.7 against the GS filter;
   - thumb-screw height (sweep envelope).
   If the knurl turns, use **LCB-A** (adapter clamp).
2. **Fujinon:** locate a fixed section (diameter, position) and its rings and lock screws. Replace the placeholder.
3. **Zooms:** H6Z0812 fixed rear barrel dia 48.5 (+1..+25.5) and CoM; any future zoom needs a fixed section >= 15 mm long to get its own LCB.
4. **Load test** (pass criteria):
   - Hang 3 x the lens mass. Static aim change <= 0.1 deg; returns to <= 0.02 deg after unloading; edge-to-edge focus unchanged within DoF.
   - Push 15-20 N on the focus/zoom ring. No slip at the pinch; returns.
   - Repeat after 1 h at 45 C.

### New gate G-LCB-1 (FEATURE_GATES, for the relief flexure)

- The pinch closes the slit and holds 0.5 N m ring torque without slip at 50 C.
- Re-torque check after 24 h at 50 C.
- No cracking at the relief root after 20 pinch cycles.

### How the design tolerates the unknowns

- Every lens-side dimension comes from C_FLANGE_X and `support`, so a new stack or band means a reprint of one 12-23 g part.
- The sleeve takes +-1.5 mm of back-focus or stack error.
- The S-screws and bosses do not depend on the camera internals.
- The module float tolerates up to 0.45 mm of centring error.

## 8. Implementation plan

### `layout.py`

- **LENSES:**
  - Correct the Kowa segments to the drawing.
  - Lock screws at 14.4 / 33.0.
  - Add `support=dict(r, x0, x1, kind, status)` to every lens (Kowa measured from the drawing; Fujinon placeholder).
  - Optional `computar_h6z0812`.
- **New `LCB` dict:** rear_x XT1, r 28.5, z_flat 33, bore_d 37.5, band_clr 0.15, travel 1.5, ears {S1, S2, S3}, ear_r 4.7, ear_t 3.0, slit 2.0, relief (1.5, 150 deg), pinch (y -26.25, z 63.0), lip (1.0, gap 0.15).
- **New function** `lcb_outline(off)`, shared by the LCB and the hood opening.
- **HOOD:** drop turret/turret_b; add `lens_opening` = outline + 0.5 + ear notches.
- **CAM:** `wall_bore_d` 37.5; `pin_d` 1.6 (or the J7 owner's float solution).
- **PARTS['lcb']:** module printed_lcb, ASA, black, face_down -X, infill shell, envelope as in 2.1, supports none. Owner `tub`, or a new `lens` OWNERS key.
- **SCREWS block** (s_l1, s_l2, s_l3, s_lp), with the `COTS['pt_screws']` recount line repeated. `cbore` gets an x range.
- **PANEL_BOSSES:** boss_l2, boss_l3. New `TUB_BOSSES['boss_l1']`.
- **STEPS / INSERTIONS / REMOVALS / LATCH_FREE / MATES** as in section 5. MATES:
  - lcb/tub: contact;
  - lcb/hood: clearance 0.5;
  - lcb/lens: clearance 0.15 (pinched in service);
  - c_cs_adapter at step 7.
- **Registries:**
  - LOAD_BEARING_PARTS += lcb.
  - CRITICAL_JOINTS J7: parts += lcb; required += lcb_sleeve_wall, lcb_ear_s1/s2/s3 (lug 1.6), lcb_pinch_jaw (lug), tub_boss_l1, panel_boss_l2/l3 (boss), lcb_rear_land (land, area >= 1000 mm2).
  - FEATURE_GATES: G-LCB-1.
  - KEEPOUTS: `ko_lens_lock_sweep`.
  - SECTIONS: `section-lcb-y0` and `section-lcb-x15` (pinch).
- **self_check:** replace the turret checks with:
  - LCB rear bore - ring r >= 0.6;
  - tub bore - ring r >= 0.6;
  - sleeve front <= first rotating segment - 1.0;
  - band inside the sleeve for XF +- travel;
  - engage >= 7 for s_l*.

### New and changed modules

- **`printed_lcb.py` (new):** PRINT, `build(L)`, `build_part`. It builds the outline prism, bores, slit + relief, pinch boss, ears and counterbores, the lip with a 45 deg underside and the 0.6 bed chamfer. Imports only math, cadquery and d2_common.
- **`printed_hood.py`:** remove `_turret` and `_bore_tool`; add `_lens_opening` (bevel, teardropped ear notches); PRINT supports -> housing strip only.
- **`printed_tub.py`:** bore r 18.75; boss_l1 + corbel + pilot; s_l2/3 clearance holes.
- **`printed_panel.py`:** the boss_l2/3 blocks. Pilots come from the existing `_cuts` "panel ..." rule; verify it.
- **`cots.py`:** lens proxy from the corrected segments.

### `checks.py`

- **New `lens_support` check:**
  - every LENSES entry has `support`;
  - band within the sleeve over the travel;
  - sleeve-band clearance 0.1-0.3;
  - J7 float >= 0.45;
  - keeper gap >= 0.2.
  It FAILs for lenses > 150 g and WARNs otherwise.
- **New `load_path` check:** uses `LOAD_MODEL` in layout (wall 0.079 / 0.146 deg/N m; stress 2.3 / 4.7 MPa/N m; creep 2.2; sleeve Winkler formula; allowables). FAIL if static aim with creep > 0.15 deg or static wall stress > 2.5 MPa across layers. WARN if the 5 g sleeve moment exceeds the gapping moment.
- **Clearance zones:** "ring in tub bore" target 0.75; replace "in hood bore" with "in LCB bore".
- **`mass_com`:** assert 0..+8 for the default lens (WARN for the others).
- The driver and boss checks run automatically from SCREWS. s_lp joins only `lcb`, so confirm that `screw_pierces`, `check_bosses` and the explode logic accept a single-part screw.

### Other files

- **`build_d2.py`:** EXPLODE lcb +X 40; STEP_VIEWS unchanged.
- **`make_tables.py`:** `estimate_volume('lcb')`; PT count text.
- **`electronics/gs8-d2-v1/make_bom.py`:** PT_USED +4.
- **Tests:**
  - new `test_lcb.py`: envelope, bed face, keep-outs, pair overlaps (lcb/hood 0, lcb/lens 0, bores >= 0.6), sweeps (adapter_on, lcb_on, lens_on), removals (lcb_off, hood order), critical features; **both LENS values**;
  - update `test_hood_panel.py` (opening, panel bosses) and `test_tub.py` (boss_l1, bore).
- **Docs:**
  - SPEC.md (J7 contract: "the LCB carries the lens; the camera hangs on it; no chassis feature locates or loads the PCB");
  - DESIGN.md (J7, parts, mass/CoM);
  - ASSEMBLY.md (steps 7/9, back focus, lens swap, removal);
  - FASTENER-POLICY.md (+4 PT, s_lp torque 0.25, reuse);
  - PRINT-GUIDE.md (LCB print; hood without turret supports);
  - LENS-ZOOM-CANDIDATES.md (Load path -> adopted fix; zoom requirement: fixed section >= 15 mm);
  - MEASURED-PARTS.md (MP-CAM / MP-LENS items);
  - HANDOFF.md, NOTES.md.
- **Order:** do this after, or together with, the J7 stack correction (MP-CAM), because C_FLANGE_X drives everything.

## 9. Honest weaknesses and risks

1. **The Kowa band is short (5.4 mm).**
   - Sleeve tilt stiffness is about 1.2e5 N mm/rad (+-2x: knurl, slit, Winkler estimate).
   - After relaxation the clamp gaps at about 0.16 N m: 5 g knocks and 15 N hand pushes rock the lens elastically by 0.15-0.45 deg of aim (no slip, no focus tilt).
   - Zooms with long fixed barrels are 70x stiffer at the sleeve.
2. **The Kowa knurl's "fixed" status is inferred from a photo index mark.** If it turns, the Kowa needs LCB-A (adapter clamp, short again) or stays on the camera.
3. **Aim stiffness rests on a 2.5 mm printed wall** (0.08-0.15 deg/N m).
   - The 600 g zoom sags 0.07-0.13 deg static after creep, and 0.3 deg at a 5 g knock (elastic).
   - A 3.5 wall would give about 2.7x, but moves X_FW_IN.
   - The FE is a coarse Kirchhoff model with idealized edges and a rigid-disc contact; treat it as +-50 %.
4. **The PT clamp and preload relax in warm ASA.** Mitigations: the knurl form fit, the snug-torque spec, the re-check in G-LCB-1.
5. **Per-lens part.** Each swap costs one reuse of s_l1..3 (5 cycles, then inserts) and takes longer (3 screws + pinch).
6. **Back focus needs a powered Pi with the panel off** (bench supply). Re-setting with the panel on depends on which side the lock-screw head faces.
7. **Hood changes:**
   - The hood plate loses its turret and gets a 58 mm opening.
   - Its lower section hangs on 2.9/3.35 side strips; the lip mitigates this.
   - The look changes: the front ring belongs to the lens and changes length per lens.
8. **Dependency on J7.** The design assumes J7 gives the module >= 0.45 mm radial float and keeps the PCB untouched. If J7's owner preloads or clamps the module (another designer's concept), the two concepts over-constrain the chain. Choose one primary support.
9. **Numbers use the D2 stack.** If MP-CAM confirms the C flange about 8 mm further back:
   - arms shrink by about 8 mm (loads fall about 10-20 %);
   - the LCB shortens to 11.6 g;
   - the conclusions are unchanged.
10. **Not modelled:**
    - the lens's own internal sag (front group on its helicoid) is unchanged by any chassis fix;
    - the FPC pull on a floating module (small, but unmeasured).
