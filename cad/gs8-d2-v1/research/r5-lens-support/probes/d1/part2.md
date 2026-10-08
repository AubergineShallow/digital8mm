
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
