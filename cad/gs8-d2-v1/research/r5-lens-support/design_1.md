# Design 1: lens-side bypass for the D2 heavy-lens sag ("collar + floating camera", J7-R)

Designer 1, 2026-10-06. Read-only work. Repo untouched. Probes are in `scratchpad/sag/d1/p1..p5.py`; they ran against the
release STEP parts and the `cots.py` proxies.

## 0. What I verified first (it changes the brief)

1. **The mount is aluminium, not plastic.** The dossier sources (the HQ/GS briefs, the filter-removal doc) say so.
   - The compliant links are the two M2 screws, the **nylon washers and the sticky gasket** between the housing and
     the PCB, and the back-focus ring (BFAR) fine thread. The BFAR thread is locked only by the split top tab.
   - "Plastic creep" is really gasket/washer relaxation plus BFAR thread rock. The fix is the same: keep the lens
     moment out of the camera.
2. **D2's camera stack is about 10 mm too long** (`layout.py:203-217`).
   - I read `research/m12-drawings/gs_side.png` myself (10.08 px/mm on the 39.5 cover). The 25.07 total includes the
     C-CS adapter: 5.8 front element at dia about 31, then a 1.2 scalloped BFAR head (dia 36), housing 10.35, PCB 1.4,
     cover 6.49.
   - The bare module is 19.8 deep (GS brief, `gs_p3.png`). D2 has 30.07. The real C flange is about 5.0 ahead of the
     BFAR face, not +10.6.
3. **The real camera does not rest on a 39.5 square land.**
   - The housing is round, dia about 35.5 (r 17.8 measured), so it passes into a dia 36.5 bore. Only the top split tab
     (10.16 wide, to r 22.1) and the tripod block reach the wall.
   - D2's 2 pins (tips x -8.2) end about 7 mm in front of the real PCB, which sits at about x -15.6 or further back.
     **They locate nothing.**
   - The real tripod block (to z about 29, 12.04 deep) collides with the cooler and `ko_exhaust`, so it must come off.
     It is labelled optional.
   - With the tripod block off, today's J7 is a single tab contact plus a keeper about 1.2 behind the cover. Under the
     Kowa the module can pitch several degrees, and the couple (tab at the front, keeper at the cover) runs straight
     through the gasket joint.
4. **With the real stack, the Kowa cannot be mounted in the released hood.**
   - Its fixed dia 42 knurl (flange +2.2..7.6, Kowa drawing) would sit at x about 3..9.
   - That is inside the turret (x 0..8.5, bore 36.5).

So the design below re-datums J7 on the real geometry ("J7-R"). It is parametric. If MP-CAM proves the old stack, only
the lip depth and the collar's x-range move (s.7).

## 1. Concept (5 lines)

1. A **tub-grounded lens collar** (new printed part, one per lens) clamps the lens on its **non-rotating rear barrel**.
   It replaces the hood turret, and its feet pass through 4 holes in the hood plate onto the tub front wall (3 M3 bolts
   into captive nuts, plus 1 compression foot).
2. The camera's **BFAR front face seats on a tub lip** (x -4.3). This contact is concentric, metal-side and axial
   only. It fixes the C flange at x +0.7 whatever the back-focus setting.
3. The **camera body (housing, tab, PCB, cover) touches nothing** in the final state. It hangs from the lens through
   adapter -> BFAR (its own 34 g). A hood fin stops roll while the lens is screwed in, and a panel finger is the rear
   catch, both with clearance.
4. The lens moment goes **lens -> collar -> tub**. The housing/PCB/gasket joint and the BFAR-housing thread **stop
   carrying it**, and so does every printed part that could creep into focus tilt. Printed creep now moves only the aim
   of the whole optical unit.
5. Roll is **set optically** (rotate lens + camera in the open collar while watching a level target), then one pinch
   screw locks it. Back focus is set on the bench, then locked.

**Deviation from the starting angle.** I clamp the lens's fixed rear barrel, not the C-CS adapter.
- The real adapter is a 5 mm band at x -4.3..+0.7, inside the tub lip and the hood plate.
- That band is too short to take a moment, and a tub-grounded part cannot reach it through the hood.
- The axial job the adapter clamp would have done is taken by the lip on the BFAR face. That face is metal, concentric,
  and independent of back focus.

## 2. Geometry (assembly frame: +X forward, +Y left, +Z up; axis y 0, z 60)

### 2.1 J7-R datum and real-camera model (layout `CAM_R`; values for s = BFAR screw-out from fully in)

| Item | Value | Notes |
|---|---|---|
| Lip rear face (BFAR seat) `LIP_X` | x -4.3 | tub; declared contact tub / gs_camera (BFAR face only) |
| CS flange / C flange | -4.3 / **+0.7** (`C_FLANGE_X = LIP_X + 5.0`) | independent of s |
| BFAR head | dia 36 x 1.2, x -5.5..-4.3; exposed face r 15.4..18 | MP-CAM |
| C-CS adapter | dia 30.75 x 5.0, x -4.3..+0.7, fitted at the bench | moves to step 7 |
| Housing front plane | x -5.5 - s (s nom 1.25 -> -6.75; design range s 0..3) | tab clears the wall by 0.3 + s |
| Housing | dia 35.5 x 10.35; top tab 10.16 wide to z 82.1, 5.02 deep | lock screw in the tab |
| PCB / cover | 38 sq, x -15.85-s..-17.25-s / 39.5 sq x 6.49 to x -23.74-s | cover rear -24.99 at s 1.25 |
| Tripod block | **removed** at the bench (2 screws) | gate |
| Camera mass split (est.) | body 31 g, BFAR 3 g; adapter 4-6 g | |

### 2.2 Tub (owner tub, `printed_tub.py`; prints face_down -Y, so +Y is print-up)

| Feature | Geometry | Print / FDM |
|---|---|---|
| Lens bore, replaced | **Lip**: opening dia 32.4, x -4.3..-2.6 (1.6 land). **Counterbore**: dia 37.5, x -5.3..-4.3. Both are `dc.teardrop` with up +Y, as today. | The lip is part of the vertical wall. The teardrop removes the lip only in the +Y +-45 deg sector, so the BFAR bears on about 270 deg. |
| 2 pins | **deleted** | They do not reach the real PCB. |
| 3 nut bosses (TL, TR, LL) | Centres (y, z) (+11.0, 92.0), (-11.0, 92.0), (+24.5, 36.0). OD 8.8, x -5.2..-7.6. Stepped pocket: washer seat dia 7.4 x 0.5 (x -5.2..-5.7), then a hex AF 5.55 x 1.9 (x -5.7..-7.6) with a vertex toward +Y. Through hole dia 3.4 (x -2.7..-5.2). | Outer profile is a teardrop, apex -Y, so the underside is 45 deg. The apex line is a 2.4 mm cantilever. LL merges into the rib_l gusset (y >= 24.1). |
| Compression-foot land (LR) | (-19.0, 44.0) on the outer face; plain wall | none |

Probes (p2/p3/p5), all 0 mm3:
- each boss in the final state;
- the `pi_in` sweep. The stack front is x -8.35 during the drop, so the boss ends 0.75 short;
- the `hood_on` sweep;
- the `panel_on` sweep;
- the real-camera `camera_in` sweep with the adapter fitted;
- the M3 tips (x -7.5..-9.3).

### 2.3 Hood (owner hood_panel, `printed_hood.py`; prints face_down +Z, print-up -Z)

| Feature | Geometry |
|---|---|
| Turret (dia 60 x 6 + dia 57 x 2.5) | **deleted**, with its fillets and the "turret upper half" tree support. The plate bore (dia 36.5, truncated teardrop -Z) stays, with the bore tool cut x -2.8..+0.3. |
| 4 foot holes | dia 9.0 through the plate (x -2.5..0) at TL, TR, LL and LR (-19.0, 44.0). Teardrop apex -Z. Ligaments: 2.1 to the bore (LR), >= 1.5 to the out_corner slots (LR), 0.5 under the front-top chamfer (TL/TR). |
| Camera roll fin (new) | B(-23.5, -19.5, -22.8, -20.55, 41.0, roof). Webs to the existing stack fin: B(-23.5, -19.5, -27.6, -22.8, 44.5, 48.5) and B(..., 75.0, 79.0). Fin to cover -Y face: 0.8 gap at zero roll (s.4). It hangs from the roof (vertical in print, no support). |

Probes: the fin final and its 60 mm drop sweep hit no part. The low web was raised from z 41 to 44.5 to clear
`ko_lead_wall` (now 0).

### 2.4 Panel

- **Keeper finger** moves from x -28.0..-24.67 to **x -30.57..-27.24** (y 4.0..32.7, z 66..76; gusset follows).
- That is 0.5 behind the cover rear at s = 3, and 2.25 at s nominal. It is now only a rear catch.
- It stays clear of post_f (z 81.5+) and ko_fpc_loop (z <= 56).

### 2.5 Lens collar (new part `lens_collar`, module `printed_collar.py`, ASA black)

- Print: face_down **+X** (front face on the bed), infill solid ("small"). No supports: the inner cone and the ear
  gussets are 45 deg, and the feet are at the print top.

| Element | Geometry (all lenses) |
|---|---|
| Flange | x 0.3..2.7, outline dia 60 plus a top ear (y -16..16 to z 96.4) and an LL ear (round 24.5, 36.0, R 4.4, blended). Inner surface is a 45 deg cone from r 18.7 (x 0.3) to the bore r (x 2.7). |
| Feet | dia 8.0 posts, x -2.7..+0.3, at TL, TR, LL (hole dia 3.4) and LR (solid, compression only). They pass the dia 9.0 hood holes with 0.5 radial clearance and bear on the tub outer face at x -2.7. The 0.3 gap to the plate face stays open. |
| Ear gussets | 45 deg on the +X side of both ears, reaching r 30 by x 8.2. Driver channels dia 7.5 along X at TL/TR (r 33.8) and LL (r 34.3): bit dia 6.5 clears the tube OD by 0.6 / 1.05. |
| Clamp tube | OD 60, x 2.7..x_front, bore = fixed-band OD + 0.1 (0.05 radial) |
| Slit | 2.0 wide, horizontal (z 59..61) on the -Y side, through tube and flange from bore to OD (3 o'clock). It sits on the free 136 deg arc between TR and LL; LR is unbolted and slides. No relief cut is needed. |
| Pinch | M3 x 12 tangential, axis -Z, at (x 5.6, y -25.5). Head seat z 64.0 in a dia 6.0 channel open from the tube top; thin nut in a hex pocket z 53.0..54.8, inserted from below. The tube wall itself is the lug (wall >= 2.1 round the hole), so there is no bending lever. Computar: local boss to r 33, screw at y -27.5. |

| Lens (`LENSES[...]['collar']`) | Fixed band (from flange) | Bore | Tube x | Clamp length | Mass (est.) |
|---|---|---|---|---|---|
| Kowa LM6HC (release) | dia 42 knurl, +2.2..+7.6 (inferred fixed) | 42.1 | 2.7..8.5 | 5.4 | 15.5 g |
| Fujinon HF6XA-5M | dia 39 rear, +2.0..+7.8 (**assumed**) | 39.1 | 2.7..8.5 | 5.8 | 17 g |
| Computar H6Z0812 (option) | dia 48.5 rear barrel, +1..+25.5 | 48.6 | 2.7..24.2 | 21.2 | 30 g |

- The tube front stays at least 2.0 behind the first rotating ring. Kowa: focus ring at x 11.3, collar front 8.5.
- Thumb screws ride their rings at x >= 13: clear.

### 2.6 Fasteners (exception to the PT rule; see s.8)

| Id | Joins | head_point (bearing face) | axis | Tip | Engagement | Step | Driver |
|---|---|---|---|---|---|---|---|
| s_c1 / s_c2 | collar -> tub nut | (2.7, +11.0 / -11.0, 92.0) | (-1, 0, 0) | x -8.8 | thin nut 1.8, tip 1.2 past | 8 | from +X down the channel. Handle from x 42.7 in free air (no lens yet). |
| s_c3 | collar -> tub nut | (2.7, 24.5, 36.0) | (-1, 0, 0) | x -8.8 | as above | 8 | as above |
| s_c4 (pinch) | collar slit | (5.6, -25.5, 64.0) | (0, 0, -1) | z 52.0 | thin nut 1.8 | 9 | from above. The bit passes beside the lens (r <= 24.3); the handle starts at z 104, 4 above the hood top. |

- Parts: M3 x 12 ISO 7045 pan, PH1, A2 (x4); ISO 4035 M3 thin nut (x4); ISO 7089 M3 washer (x6: 3 under heads, 3 in
  the tub pockets).
- Torque: mounts 0.25 N m, pinch 0.15-0.2 N m. Hardware is about 4.3 g.

## 3. Load path with numbers

### 3.1 Moments

Real stack, C flange x +0.7. Assumed CoM from the flange: Kowa 28.3 (D2's value, unverified), Computar about 40
(guess), Optivaron about 50 (guess).

| Lens (weight) | Today: hung on the camera, about the tab at x -5.2 (static / 5 g) | New: at the collar clamp centre (static / 5 g) | New: into the tub at x -2.7 (static / 5 g / hand) |
|---|---|---|---|
| Kowa 215 g (2.11 N) | 0.072 / 0.36 N m | 0.049 / 0.25 | 0.067 / 0.33 / 0.2 (10 N on the focus ring) to 1.0 (20 N on the front barrel) |
| Computar 305 g (2.99 N) | 0.137 / 0.69 | 0.082 / 0.41 | 0.130 / 0.65 / 1.71 (20 N on the focus gear, x 83) |
| Optivaron 600 g (5.89 N) | 0.33 / 1.65 | 0.22 / 1.11 | 0.31 / 1.57 / 1.67 (20 N at x 80) |

### 3.2 What still reaches the camera mount (gasket joint and BFAR thread)

- **Only the camera's own body and the FPC load it.**
  - Body weight: 31 g about 6.5 mm behind the BFAR thread, so 0.002 N m static and 0.01 N m at 5 g.
  - FPC drag: 0.1-0.3 N, so at most 0.006 N m.
  - Total: at most 0.008 N m static and 0.02 N m at 5 g, **whatever lens is fitted**.
- Today the Kowa puts 0.072 N m through the joint. That is at least 9 times more. The Computar would be 17 times
  more, the Optivaron 40 times.
- **Stiffness argument.** In the final state the camera body has no second path to the chassis. Every cage gap is open:
  - tab to wall 0.3 + s;
  - BFAR head to counterbore 0.75 radial;
  - adapter to lip 0.8;
  - cover to roll fin 0.8;
  - cover to keeper at least 0.5;
  - housing to nut bosses at least 2.6.

  So the fraction of the lens moment through the housing is zero, not merely small. To close a gap, the collar/tub
  must rotate by gap/lever, for example 0.8/27 rad = 1.7 deg at the cover. That is more than 5 times the worst 5 g
  zoom case below.
- **The one remaining contact is the lip.** It touches the BFAR front face, which is lens-side metal. Its reaction
  loops BFAR -> adapter -> lens -> collar -> tub and never enters the housing, the gasket or the BFAR-housing thread.
- **Thermal effect on that loop.** It has 9.9 mm of ASA against 9.9 mm of metal: +0.7 um/K, so 28 um at +40 K, about
  10-15 N.
  - The load is concentric compression on the BFAR face only. The adapter-BFAR face joint is clamped further, not
    opened.
  - Cooling opens a micrometre gap.

### 3.3 Capacities

- **Clamp.** Separation moment M_sep = (pi/6) F L, with hoop pressure F/(r L).
  - Assumptions: pinch 250 N at first. "Conservative" means relaxed to 120 N and derated 50 % because the ring is
    bolted asymmetrically.

  | Lens | M_sep initial / conservative | Static margin | 5 g |
  |---|---|---|---|
  | Kowa | 0.71 / 0.17 N m | 3.5x | 0.25 > 0.17: the lens may rock inside its 0.05 clearance (at most 1 deg, aim only, recovers) |
  | Fujinon | 0.76 / 0.18 | about 7x (0.025 N m static) | OK |
  | Computar | 2.78 / 0.67 | 8x | 1.6x; a hard 1.4 N m grip on the focus gear exceeds it (rock within clearance) |

  - Roll slip (conservative): mu x 2 pi F r = 2.4 N m (Kowa), against ring torques of 0.05-0.2. Axial slip: 113 N.
- **Mount joint.** Three M3 bolts at about 150 N relaxed preload each, plus the LR compression foot.
  - The 4 points enclose the axis. Checked by cross products: the axis and LR lie on the same side of the TR-LL line;
    TL lies opposite.
  - Opening needs at least 8 N m (nose-up) or 15 N m (nose-down). The maximum load is 1.7 N m, so the joint never
    opens and the tub wall is the compliance.
- **Aim stiffness.**
  - Estimate k_rot about 300-800 N m/rad. It is lowest at the top bolts, which sit 5.3 mm below the free wall top at
    z 97.3.
  - Kowa static: 0.005-0.013 deg. Optivaron at 5 g or a Computar hand load: 0.1-0.33 deg, transient, **aim only**.

### 3.4 Stress against creep-derated ASA

Allowables: sustained 4-5 MPa in XY and 2-3 MPa in Z; short-term about 20 MPa at 50 C.

| Section | Load | Stress | Verdict |
|---|---|---|---|
| Collar hoop at the pinch, Kowa (8.95 x 5.8) | 250 N | 4.8 MPa, XY | at the sustained limit. It relaxes, and the design needs 25 % of it |
| Collar hoop, Computar (5.7 x 21.5) | 250 N | 2.0 | OK |
| Pinch head seat, no washer (dia 5.6 / 3.4) | 250 N | 16 MPa bearing | relaxes; re-torque at the first lens change |
| Collar feet (41 mm2) | 300-400 N | 7-10 MPa compression along print Z | compression; relaxes to about 4 |
| Tub wall under the nut washer (34 mm2) | 300-400 N | 9-12 MPa, in-plane | keeps at least 100 N after relaxation |
| Tub wall bending at the top bolts | Optivaron 5 g, about 16 N per bolt | about 7 MPa transient | OK. Kowa static: 0.2 MPa |
| Tube-flange junction (full ring) | Kowa 5 g, 0.25 N m | < 0.1 MPa | trivial |
| Tub lip, 1.6 land | 15 N thermal + 5 N pull | about 0.3 MPa | OK |

**Where printed creep can now act:** the bolt and pinch preloads, and the aim of the whole optical unit. **None of
these creep paths changes lens-to-sensor tilt.**

### 3.5 Estimated image-plane tilt

- **Lens against sensor.** New tilt is about 0.11 x today's Kowa tilt, constant for heavier lenses.
  - Example: a soft gasket joint at 20 N m/rad tilts 0.21 deg today (Kowa static) and 1.0 deg at 5 g.
  - New: 0.02 deg static and 0.06 deg at 5 g, against the 0.3 deg budget.
  - G-CAM-2 measures the real joint.
- **Whole-unit aim.** Per s.3.3, not part of the focus budget.

## 4. Alignment

- **The camera sets lens-to-sensor alignment.** The chain lens flange -> adapter -> BFAR (locked) -> housing ->
  M2/gasket -> PCB -> sensor is entirely the camera's own.
  - The chassis touches only the lens's fixed barrel (collar) and the BFAR front face (lip: axial, concentric).
  - No displacement is forced into the chain.
- **Tolerance stack for the float (worst case).**
  - Collar on the tub: bolt clearance +-0.2 plus hole position +-0.15, so +-0.35.
  - Lens in the collar: 0.05 bore clearance plus pinch shift +-0.1.
  - So the lens axis sits within +-0.45 of the lip axis.
  - Remaining gaps: adapter-lip at least 0.35; BFAR-counterbore at least 0.3; cover-fin at least 0.15 (with +-0.2
    cover centring). Nothing closes.
- **Axial.** The lip is the only datum, which makes C flange - lip = 5.000 (adapter). Back focus s moves only the
  camera body, so the collar needs no change when s changes.
- **Roll.**
  - Set optically at step 9 within the fin's +-2.3 deg window, then held by thread friction and the pinch.
  - The fin reacts only the screw-in torque.
  - Today nothing sets roll: the pins miss the PCB.
- **Accepted over-constraint.** Lip and collar both fix the lens-side metal axially. The cost is the thermal 10-15 N in
  s.3.2: concentric, and outside the housing.

## 5. Assembly and service

| Step | Change (ASSEMBLY / `STEPS`) | adds |
|---|---|---|
| **B0 bench (new, before 7)** | Remove the camera's tripod block (2 screws). Fit the C-CS adapter hand-tight. Reference lens on a target at infinity: set the BFAR and tighten its lock screw. Measure the BFAR protrusion and record s = protrusion - 1.2 as `CAM_R['s']`. Remove the lens; leave the adapter on. | - |
| 3 | Also pull 3 M3 thin nuts and washers into the front-wall pockets with an M3 x 12 from the front (the hood is not on yet). | nuts_c1..c3 |
| 5 | Hood as before. It now has no turret, 4 holes and the roll fin. | - |
| 7 | Camera with its adapter, same path (in at +2, down 2, +X 11.1), until the BFAR face stops on the lip. | gs_camera, **c_cs_adapter** (from step 9) |
| 8 | Panel and its 4 PT screws, then the **lens collar**: feet through the 4 hood holes, then s_c1..s_c3 with washers from the front, 0.25 N m, PH1. | + lens_collar, s_c1..s_c3 |
| 9 | Knobs, eyecup, stick. **Lens:** screw it into the adapter through the collar (the camera turns until its cover meets the fin). Set focus and iris and lock the thumb screws. Pull the lens lightly forward (BFAR onto the lip). On live view with a level target, turn lens and camera together to level. Tighten s_c4 from above, 0.15-0.2 N m. | lens, s_c4, nut_c4 |
| 10 | Power, unchanged. | - |

- **Lens swap (PH1 only).**
  1. Loosen s_c4 by one turn and unscrew the lens (the fin reacts the torque).
  2. If the next lens uses another collar: remove s_c1..s_c3, swap collars, refit at 0.25 N m.
  3. Screw in the next lens, pull it forward, level, pinch.
  4. If the adapter comes out with the old lens: start it one turn onto the next lens, then screw both in together.
  - The M3 screws go into steel nuts, so reuse is unlimited. Total: 1 or 4 screws.
- **Camera removal.**
  - Take the lens off; the collar may stay. Take the panel off.
  - Reverse `camera_in`: -X 11.1, up 2, +Y 60. The adapter passes back through the lip opening (dia 32.4).
- **Hood removal.** Lens, collar, panel and camera come off first, then the hood lifts.
  - Today's `hood_off` already requires the lens and camera off; add the collar and s_c1..s_c3.
- **Back focus.**
  - Bench only, because the BFAR sits behind the lip. Set, then lock.
  - Because the lip fixes the C flange, a new s needs only the camera out and back. The collar and the keeper
    (designed for s 0..3) stay.

## 6. Interactions

- **Fujinon variant.**
  - It builds with `collar_fujinon`. Its band is assumed; see G-LENS.
  - It has no thumb screws to clear.
  - CoM moves from -8.89 to about -10.0.
- **Kowa thumb screws.**
  - D2's `lock_screws` (y -28.8, x 20.6/44.6) are wrong. The real M2 thumb screws ride the focus ring (flange +14.4,
    x 15.1) and the iris ring (+33.0, x 33.7), at r up to 24, at any clock position.
  - Model them as sweep rings. The collar front (8.5) is 4.7 behind the first one.
  - The pinch driver (x 5.6) passes behind them. "Clock to the right" can go.
- **Hood and J1.**
  - The turret goes. The hooks and the drop path are unchanged: the holes take no material on the drop path, and the
    fin's drop sweep hits nothing.
  - The hood no longer needs its turret tree support.
  - The collar (dia 60, x 0.3..8.5) recreates the turret silhouette.
- **Hand clearance.**
  - The pinch sits inside the tube wall, so nothing protrudes beyond the old turret except the top ear (z <= 96.4) and
    the LL ear (y 20..29, z 31..41). Both stay inside the body width.
  - The focus ring stays fully exposed.
- **FPC.**
  - The cover rear moves from -24.47 to -24.99 at s nominal, and to -26.74 at s 3.
  - Re-derive `ko_fpc_cam` from the cover. The route grows by 0.5-2.3 mm; re-run `cable_routes` against the 200 mm
    budget.
- **rib_l.** The LL boss merges into its gusset. The tip land probe is unchanged.
- **Keeper finger.** It moves back 2.57 and stays 3.33 deep, so the `panel_cam_keeper` probe still reads 3.33.
- **Vents, plunger, SD.**
  - The plate slots, plunger guard and SD slot are unchanged. The collar bottom stays at z 30, as the turret's did.
  - The LL ear is outside out_band (y <= 17.5). The LR foot is under the collar disc.
  - Probe: the hood holes remove only plate material.
- **Pi stack and EVF.**
  - The bosses end at x -7.6; the stack front passes at -8.35 (0 mm3).
  - EVF, hooks and the panel slide are untouched (probes 0).
- **Balance** (0..+8 target).
  - Kowa: +3.73 -> **about +1.6**. The lens moves 9.9 back (-2.4). The net +7 g (collar 15.5 + hardware 4.3 + tub
    0.5 - turret 13.1) sits near x 0 (+0.3). Camera and adapter: -0.1.
  - Fujinon: about -10.0.
  - Computar: about +13. Optivaron: about +36. These need a battery or counterweight move whatever the support.

## 7. Unknowns and gates

- **G-CAM-1, extended (MP-CAM).** Measure:
  - the BFAR head: OD, thickness, flatness, and the front-face annulus exposed outside the adapter shoulder (need at
    least 1.0 radial);
  - the adapter: OD, shoulder, and face-to-face 5.00;
  - the housing OD, and the tab size and lock-screw head side and size;
  - that the tripod block comes off with its 2 screws and leaves nothing below r 18;
  - the cover: 39.5 square, centred on the axis within +-0.2;
  - s at infinity with the Kowa, and the s range;
  - the FPC exit and the mass split.

  How the design tolerates them: lip x, counterbore, fin, keeper and FPC keep-outs are layout parameters. The cage gaps
  are sized for s 0..3 and a 0.45 lens offset.
- **G-CAM-2 (new), joint compliance.**
  - Clamp the lens in a collar coupon. Hang 0, 50 and 100 g on the camera cover. Read the edge-focus change on a
    target. Repeat after 1 h at 50 C.
  - Pass: less than 0.05 deg. This confirms the float and replaces the sag measurement in today's G-LENS text.
- **G-LENS, extended.**
  - Kowa: the dia 42 knurl does not turn or translate with focus or iris. Measure its OD (+-0.02) and its rear face at
    flange +2.2 (+-0.2). Find the CoM on a knife edge. Map the thumb-screw envelope.
  - Fujinon: find a non-rotating band at least 5 mm long within 10 mm of the flange. If there is none, the fallback
    collar clamps the locked iris ring and the iris is set before pinching.
  - Computar: confirm the rear barrel is fixed over flange +1..+25.
- **G-COL-1 (new, print coupon).** Collar + tub-front coupon + plate coupon.
  - The feet fit the holes and pockets.
  - Clamp slip at 0.15 N m: at least 1 N m in roll and 50 N axial.
  - It holds 5x the lens weight at the CoM without rock.
  - After 24 h at 50 C: re-check the pinch angle and the hold.
- **G-W11 (existing).** The real interior temperature sets the creep derating.
- **If MP-CAM confirms D2's original stack** (front land, C flange +10.6):
  - keep the bolts, nuts, holes, fin, keeper logic and collar flange;
  - set the lip to the measured seat;
  - extend the collar tube to the band (Kowa x 12.8..18.2).

## 8. Implementation plan

Measure first (MP-CAM, G-LENS), then:

- **`layout.py`**
  - `CAM` -> `CAM_R` (bfar, adapter, housing, tab, pcb, cover, s_nom 1.25, s_max 3.0, `LIP_X` -4.3, lip_d 32.4,
    cb_d 37.5). Derive `C_FLANGE_X` = `LIP_X` + 5.0. Delete `pins`. Move the keeper.
  - New `COLLAR` dict.
  - `LENSES`: add `fixed_band` and `collar`; correct the Kowa segments; replace `lock_screws` with thumb-screw rings.
  - `HOOD`: no turret; add `collar_holes` and `cam_roll_fin`.
  - New `FASTENERS_M3` (kind 'M3+nut', engage = nut).
  - `STEPS` 3/7/8/9 as in s.5.
  - `INSERTIONS`: camera_in + adapter; collar_on [(25,0,0),(0,0,0)]; lens_in [(30,0,0),(0,0,0)].
  - `REMOVALS`: collar_off; `hood_off` += collar and s_c1..3; camera_out off = panel set + lens. Update `LATCH_FREE`.
  - `MATES`, `KEEPOUTS` (`ko_fpc_cam` from the cover), `PARTS`, `LOAD_BEARING_PARTS`.
  - J7 `required` probes: tub_lip, tub_nut_boss_x3, collar_wall_min, collar_foot, collar_pinch_wall,
    hood_cam_roll_fin, panel_cam_keeper.
  - `self_check` replaces the two turret items with:
    - lip - adapter >= 0.75;
    - counterbore - BFAR >= 0.675;
    - tab-wall >= 0.3 over s 0..3;
    - keeper-cover >= 0.5;
    - collar front <= first rotating ring - 2;
    - boss x >= Pi-drop front + 0.5;
    - channel to tube >= 0.2.
- **`cots.py`**
  - Real `gs_camera`: BFAR, housing + tab, PCB, cover; no tripod block; sub-shapes tagged body or bfar.
  - Adapter dia 30.75 x 5.0; corrected `lens_proxy`; M3 screw, nut and washer builders.
- **Printed parts**
  - `printed_tub.py`: lip and counterbore teardrops; remove the pins; 3 nut bosses.
  - `printed_hood.py`: remove `_turret`, its fillets and the support note; bore tool to x 0.3; add holes (teardrop -Z)
    and the roll fin.
  - `printed_panel.py`: keeper from `CAM_R`.
  - New `printed_collar.py`: face_down +X; builds for `L.LENS`.
- **`checks.py`**
  - New `check_j7r_float`: camera-body sub-shapes at least 0.2 from everything. The only allowed contact is the BFAR
    face on the lip.
  - New `check_lens_clamp`: conservative M_sep at least 1.5x static for every lens; report the 5 g ratio.
  - New `check_mount_polygon`.
  - Replace the J7 clearance zones.
  - M3 entries in `check_driver`, `screw_pierces` and `interference`; new `check_nut_pockets`.
  - `mass_com` warns outside 0..+8.
- **Build and tables**
  - `build_d2.py`: J7-R section (cuts y 0 and z 92); explode entry; collar for each lens in mass_com.
  - `make_tables.py` / `make_bom.py`: collar rows and M3 BOM lines.
- **Tests**
  - `test_tub`: lip, no pins, bosses against pi_in.
  - `test_hood_panel`: no turret, holes, fin, keeper; updated lens and camera cylinders.
  - New `test_collar`.
  - `test_r3_regressions`: the new checker logic.
- **Docs**
  - SPEC s.9/s.10, DESIGN J7, ASSEMBLY (B0, steps, lens swap).
  - FASTENER-POLICY: new M3 section. Reasons:
    - the Pi drop column leaves 2.8 mm behind the wall, and PT needs at least 8;
    - the collar and pinch are cycled at every lens change, and PT allows 5 reuses;
    - it is the same M3 pan PH1 family as the insert fallback.
  - PRINT-GUIDE, MEASURED-PARTS (G-CAM-2, G-COL-1), the LENS-ZOOM-CANDIDATES "Load path" section, HANDOFF.
- Build only with `run_locked.py`.

## 9. Honest weaknesses and risks

1. **It rests on my reading of the drawings.** The stack about 10 mm shorter, the round housing, the tripod block
   coming off and the BFAR face being exposed all come from drawings. It is parametric. But if the adapter shoulder
   covers the BFAR face, the lip loses its seat, and the fallback (seat on the tab) is s-dependent and weaker.
2. **One collar per lens.** Each needs a confirmed non-rotating band.
   - The Kowa's band is only 5.4 mm, and that it is fixed is inferred.
   - The Fujinon band is assumed.
3. **Clamp margins are thin under shock and hand load.**
   - After relaxation the Kowa clamp is marginal at 5 g. The lens rocks within 0.05 mm: aim, not focus.
   - Zoom hand loads exceed the conservative clamp. Heavy zooms should still get a front support for aim steadiness.
4. **A fastener-policy exception.** It adds 14 hardware pieces, and the captive nuts go in at step 3. A lost nut means
   taking the hood off.
5. **The top bolts are the softest point.** They sit 5.3 mm below the free wall top. I found no room for a stiffener:
   hood material fills x -8..-5.2 above z 97.3 and round the hooks.
6. **No in-body back-focus adjustment.** It is bench only, so a lens that needs a different back focus means removing
   the camera.
7. **Screw-in torque still loads the BFAR lock** before the fin catches, as it does today. Roll depends on the user
   levelling at step 9.
8. **A deliberate concentric over-constraint at the lip.** It puts 10-15 N of thermal load into the adapter-BFAR face
   joint.
9. **A large change set with nothing built or checked in the real suite.**
   - It touches J7, the proxies, the hood, the tub, the panel, a new part, new fasteners and 4 steps.
   - Only my probes ran (p1-p5: bosses, Pi drop, hood drop, panel slide, real-camera insertion, fin, screw tips). The
     CAD was not built and the check suite was not run.
10. **Balance gets worse for the Fujinon (-10.0)**, and zooms stay far forward.
