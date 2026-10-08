# GS8 D2: fastener and joint policy (binding for every threaded joint in `cad/gs8-d2-v1`)

This policy replaces the release rule "no self-tapping into ASA" for D2 only. The user accepted thread-forming screws
in the concept: one screw type for the whole body. Numbers come from `layout.PT` and `layout.SCREWS`. The torques and
the strip margin are **not measured**. Bench gate G-PT-1 sets them. **r5:** one exception to the one-screw-type rule:
the lens collar is held by M3 machine screws in brass heat-set inserts (section I); every PT rule below applies to
the PT kind only (`SCREWS[...]['kind']`).

## A. The screw

- **Screw:** PT 3.0 x 12 thread-forming screw for plastics, pan head, PH1 drive.
  - Class: EJOT PT K30x12 WN 1411 or Delta PT 30x12 (30 deg flank).
  - Material: steel zinc-plated or A2.
  - Head proxy dia 6.0 x 2.4. Confirm the head on receipt; the counterbores allow a head up to dia 6.5.
- **Count:** every PT body screw is of the one spec; the total and the ids are generated from `layout.SCREWS` in
  DESIGN.md s1 (`counts` block; `make_bom.py` reads the same list). The X1203 kit M2.5 screws and standoffs are counted
  separately there (section F). By step:
  - step 3, J4 base lock (r2 fixer): s_j up through the base counterbore into the tub floor lock boss;
  - step 8, enclosure closure (r1):
    - s_b1, s_b2: up through the base into the panel bosses;
    - s_r1, s_r2: through the right wall into the panel posts;
  - step 4, Pi keeper (r2, R1, audit finding 1): s_k1, s_k2 down (-Z) through the printed `pi_keeper` into 2 tub floor
    bosses. They replace the 4 one-time floor hooks, so the stack comes out without damage (ASSEMBLY s7). The geometry
    values are R1's in `layout.SCREWS` and the build's `boss_geometry` record; section B's rules apply unchanged.
  - Service: s_j stays in for panel and Pi service; every screw comes out only after the isolation prerequisite of
    ASSEMBLY s7 (shut down, cap off, pack out, XT30 parted).
- **Driver:** PH1, by hand only. Never a power driver, which strips printed bosses and melts ASA.

## B. Printed bosses (s_b and s_r engage the panel; s_k engage the tub floor, r2)

The table gives the r1 values for the 4 enclosure screws. The s_k1/s_k2 tub bosses (r2) and the s_j J4-lock boss (r2
fixer, tub floor from below, engage 10.0) follow the same rules; their
values are measured by `checks.check_bosses` in the r2 build (`boss_geometry` in `checks.json`).
**Layer orientation of s_k:** the tub prints face down on -Y, so the vertical s_k pilots lie **horizontal in the print**
(the weak case, like s_b): the boss OD rule (>= 7.0), the 40 % modifier and the insert fallback apply, and G-PT-1
covers them with the horizontal coupon. Boss radii (r2 fixer): s_k1 r 3.8 (OD 7.6), s_k2 r 3.6 (OD 7.2, re-sited to
y 28.25 so its +Y wall is 2.35 over the whole engaged depth; it was 1.75 over the top 2 mm). The insert walls are in E.

| Rule | Value | D2 |
|---|---|---|
| Pilot dia | 2.5 (0.83 d, ASA) | 2.5, 0.4 x 45 deg entry chamfer (`d2_common.pt_boss`) |
| Boss OD | >= 7.0 (wall >= 2.25 round the pilot) | 8.0 nominal (boss_b1/b2 8 x 8.1; posts 8 x 8). Solid-measured wall: posts 2.75; boss_b1/b2 2.5 on the -Y side (the screw axis y 27.85 sits 3.75 from the boss face y 24.1), i.e. OD-equivalent 7.5 |
| Thread engagement | >= 7.0 | s_b 7.4 (z 2.6..10.0), s_r 10.0 (y -30.4..-20.4) |
| Pilot depth | engagement + 1.0 tip reserve | s_b 8.4 blind (r2 fixer: boss top 12.0 -> 12.6 leaves 1.6 over the pilot end); s_r 11.0 blind in the post |
| Material under the head | >= 1.6 | s_b 2.0 (base), s_r 1.9 (wall 2.5 + 2.0 pad, minus a 2.6 deep counterbore) |
| Counterbore | dia 7.0 (head + 0.5 per side; the bit is dia 6.5 max) | s_b 6.0 deep in the base; s_r 2.6 deep, flush head |
| Joint gap closed by the screw | <= 0.1 | boss bottom z 2.6 over the floor 2.5; post end 0.1 off the pad |
| Print setting round the bosses | 4 perimeters, 40 % infill modifier, 8 mm round each pilot; r4: exported as meshes (`out/stl/modifiers/`, `layout.print_modifiers`) for tub, panel and base_grip | PRINT-GUIDE s1.1 |

**Layer orientation.**
- The s_r posts' pilots run along print-up (the panel prints face down; the posts grow upward). The hoop stress stays
  in the layer plane, which is the strong case.
- The s_b bosses' pilots are horizontal in the print. Their hoop stress crosses layer lines, the weak case. That is
  why they have OD 8, the 40 % modifier and the insert fallback (section E).
- G-PT-1 tests both orientations.

## C. Torque (provisional until G-PT-1)

- **First drive (thread forming):** expect a drive torque Td of about 0.3-0.6 N m. Stop at head contact.
- **Seating torque:** T_spec = **0.35-0.5 N m**, applied by hand. A small PH1 driver gives about 0.4 N m with firm
  fingers.
- **G-PT-1 (bench):** print 3 bosses of each orientation as coupons, in the release settings.
  - Record Td and the strip torque Ts.
  - Require Ts >= 2 Td.
  - Set T_spec = Td + 0.3 (Ts - Td), capped at 0.5 N m.
  - If Ts < 2 Td, use the insert fallback from the start.
- **No threadlocker** on ASA (it causes stress cracking). Do not re-torque later: ASA creeps, and re-torquing only
  strips the thread.

## D. Re-assembly limit

- **5 re-assemblies or fewer** per boss. On each re-insertion:
  1. turn the screw backwards until it drops into the existing thread (a click);
  2. then drive it to T_spec.
- After the 5th cycle, a strip, or a screw that spins at less than Td: switch that boss to the insert fallback.
- Keep a tally on the bench sheet (ASSEMBLY.md).

## E. Insert fallback (M3 heat-set, per boss)

1. Remove the panel. All 4 panel boss entry faces are then reachable from the panel's inner side. For an s_k boss
   (tub floor): hood and panel off, keeper and stack out (ASSEMBLY s7); the boss top is then open from above. For
   s_j (r2 fixer): s_j, s_b1 and s_b2 out and the base slid off (ASSEMBLY s7 item 11); the boss entry (floor
   underside) is then open from below.
2. Drill per boss (r2 fixer, verifier E-V-E3: one depth for all bosses drilled through the tub floor at s_k and
   through the boss cap at s_b). Insert drill dia 4.0 x 6.7 from the entry face for every boss; the dia 3.2
   extension only where the M3 x 10 tip would otherwise form a thread in the 2.5 pilot:

   | Boss | Entry face | Insert (M3 x 5.7) | Insert drill dia 4.0 to | Dia 3.2 extension | M3 x 10 tip | Material left past the deepest drill | Wall round the 4.0 drill |
   |---|---|---|---|---|---|---|---|
   | s_b1, s_b2 (panel boss, from below) | z 2.6 | z 2.6..8.3 | z 9.3 | **none** (the tip stays in the insert) | z 8.0, 5.4 into the insert | boss top z 12.6: **3.3** (never drill past z 11.6) | 1.75 on the -Y side (axis y 27.85, face y 24.1) |
   | s_r1, s_r2 (panel post, from the right) | y -30.4 | y -30.4..-24.7 | y -23.7 | to y -19.9 (10.5 from the entry; the old pilot ends at y -19.4) | y -22.4, 2.3 past the insert in the 3.2 bore | the post runs on to the panel | 2.0 (post 8 x 8) |
   | s_k1 (tub floor boss, from above) | z 9.8 | z 9.8..4.1 | z 3.1 | **none** | z 4.3, inside the insert | floor underside z 0: **3.1** (never drill below z 1.0) | **1.8** (r 3.8) |
   | s_j (J4 lock: tub floor boss, from below; r2 fixer) | z 0.0 (floor underside) | z 0.0..5.7 | z 6.7 | to z 10.5 (the tip would otherwise form in the 2.5 pilot) | z 8.0, 2.3 past the insert in the 3.2 bore | boss top z 12.6: **2.1** | 2.0 (OD 8) |
   | s_k2 (tub floor boss, from above) | z 9.8 | z 9.8..4.1 | z 3.1 | **none** | z 4.3, inside the insert | as s_k1 | **1.6** (r 3.6; +Y wall min(3.6, 31.9 - 28.25) - 2.0 = 1.6) |

   **s_k2 is a marginal insert site:** its 1.6 wall is exactly the 1.6 minimum above z 7.6 (below z 7.6 the lip gusset
   backs it); a cracked boss there means a tub reprint. Prefer re-tapping s_k2 with a fresh PT screw within the reuse
   limit, and use the insert only after a strip.
3. Heat-set an M3 x 5.7 insert (Ruthex/CNC Kitchen standard class, pilot 4.0). Walls round the 4.0 drill are in the
   table above (minimum 1.6; the release `INSERT['M3']` boss_od is 7.6).
4. Use an M3 x 10 pan-head A2 screw, **ISO 7045 cross recess H, size PH1**, in the same counterbore, at 0.5 N m,
   driven with the same straight PH1 driver. **No hex or socket-head screw** (ISO 7380, ISO 4762): the straight-driver
   rule (G) and ASSEMBLY s1 exclude L-keys and hex bits (r2, audit finding 7). The ISO 7045 M3 head (dia 5.6 x 2.4)
   is no larger than the PT head proxy (dia 6.0 x 2.4) on the same axis, so the existing driver audit and the dia 7.0
   counterbore still cover it.
   - s_b: the tip reaches z 8.0, 5.4 mm into the insert.
   - s_r: the tip reaches y -22.4. The insert ends at -24.7, so the tip runs 2.3 mm on into the 3.2 drill.
   - s_k: under the 4.5 keeper, the tip reaches z 4.3, inside the insert (z 9.8..4.1).
5. Tools for the repair (all used straight along the boss axis): a hand drill or pin vise with 4.0 and 3.2 mm
   drills, the soldering iron with an M3 heat-set tip, then the PH1 driver. No power driver on the screw.
6. Opening the panel for the repair follows the non-destructive service procedure of ASSEMBLY s7.

## F. Other threaded parts (not PT)

| Part | Hardware | Rule |
|---|---|---|
| X1203 + Pi stack | kit: 4 M2.5 F-F standoffs (10.9 assumed), 8 M2.5 x 5 pan screws | metal to PCB only, **0.2 N m**, at the bench (step 1). The 4 lower heads sit in the floor-boss pockets (dia 5.6 x 2.4); no printed part is clamped. Driver: the same straight PH1 if the kit screws are cross-recess (record at G-W2). If the kit ships hex-socket screws, replace them with 8 x M2.5 x 5 cross-recess PH1 A2 pan heads (BOM D2-34); no L-key. **r2 fixer (verifier E-V-E11):** ISO 7045 allows an M2.5 head of dk 5.0 x **k 2.1 max** (Engineers Edge ISO 7045 table), above the G-PI-1 limit 5.0 x 2.0 (r2 had "5.0 x 1.7"). So order a low-head cross-recess pan listed at k <= 2.0, or measure each head on receipt (k <= 2.0; G-PI-1 records it). A 2.1 head still sits 0.3 inside the 2.4 pocket, but the gate limit is not relaxed here. Hold the standoffs by hand. |
| 18/24 rotary switch | its own nut + washer (outside the panel, under the knob) | finger-tight + 1/8 turn (about 0.3 N m on a 1/2 in socket). The anti-rotation tab in the panel slot carries the switching torque, not the nut. This nut is the one threaded part in the camera that is not driven by the PH1: it needs the socket (ASSEMBLY s1.1, tool 6). OPTIONS.md (a) would remove it. |
| Tripod socket | 1/4-20 UNC steel hex nut, pressed into the base from the top (step 3), z -5.7..-0.1 | 2.3 mm ASA bearing wall below it, hole dia 6.6. The tub floor above traps it. A tripod screw of 6.5 mm or less ends in the nut (z -1.5). Clamp by hand. |
| Lens | C thread into the C-CS adapter, adapter into the camera's CS thread (BFAR) | by hand. r5: the lens is screwed in through the lens collar (ASSEMBLY step 8) while the camera is held; the Kowa's 2 M2 thumb screws (focus at the rear, iris at the front) are set after focus and iris; the collar pinch s_c4 (section I) is the last operation |
| GS camera tripod block (r5) | 2 small screws of the camera's own (drive unconfirmed: MP-CAM) | removed once at bench step B0 and bagged (the block collides with the Pi envelope as D2 places the camera). If the drive is hex, this is the one bench exception to the straight-driver toolset (a key from the camera's own kit, used once off the body); record it at MP-CAM |

## G. Straight-driver rule (user)

- Every screw is drivable with a straight driver along its own axis at its assembly step.
- **Scope (r2):** the PH1 is the only screwdriver of the build: the enclosure screws, any PT keeper screws, (r5) the
  4 lens-collar M3 screws, the M3 insert-fallback screws and (if cross-recess, else replaced) the X1203 kit screws. It is not the only tool: the full
  toolset is ASSEMBLY s1.1 (soldering iron, socket for the 18/24 nut, saw and file, tweezers, release blade, the 2
  hood release pins and more).
- **Audit model:** a bit of dia 6.5 x 40, then a handle of dia 30 x 100, coaxial with the screw. It is checked
  against every part present at the screw's own step: step 3 for s_j, step 4 for s_k1/s_k2, (r5) step 7 for
  s_c1/s_c2/s_c3, step 8 for s_b1/s_b2/s_r1/s_r2 and s_c4
  (`layout.screw_audit_set`), and again in the service state (`service_driver`). The audit applies to every kind.
- Long bits and plugged holes are allowed, but none are needed in D2.
- Expected clearances:
  - s_b1 / s_b2 from below: the handle clears the grip's rear face by about 5 mm.
  - s_r1 / s_r2 from the right: open space.
  - s_k1 / s_k2 from above at step 4 (hood not yet on, panel off): the audit runs them against the parts present at
    step 4 (R1/R3 record the clearance in `checks.json`).
  - r5: s_c1..s_c3 along -X from the front at step 7 (lens not yet fitted): bit 0.5 off the dia 7.5 counterbore wall.
    s_c4 straight down from above at step 8 (lens fitted): bit 0.25 off the collar body, handle 6.5 off the hood.
- Only `build_d2.py` may report a pass.

## H. Records

- `build_d2.py` writes the driver audit and the solid-measured boss check `boss_geometry` to `checks.json`
  (`checks.check_bosses`: exact local intersect of the receiving part, 0.01 mm mesh, rays along and across each
  `SCREWS` axis). Per screw it records:
  - pilot dia (2.5 +-0.05);
  - pilot depth from the boss entry (>= engagement + 1.0 tip reserve);
  - minimum wall round the pilot (>= 2.25, the boss OD 7.0 rule);
  - material under the head on the counterbore shoulder (>= 1.6).
- The layout self-check adds the layout-level rows (engagement >= 7 from `SCREWS['engage']`, boss OD constant, boss
  and post section boxes); those are layout checks, not solid measurements.
- r5: `boss_geometry` measures kind PT only; the kind M3 rows are measured by `check_inserts` (section I).
- ASSEMBLY.md carries T_spec, the re-assembly tally and the fallback procedure.
- Nothing here is hardware-verified.

## I. Lens collar: M3 screws in heat-set inserts (r5, lens collar only)

The r5 lens collar (J7-R float, `R5-BRIEF.md`) is the one place in D2 where a machine screw goes into a brass heat-set
insert in the normal build. Everywhere else the PT rules of A-E stand unchanged.

**Why not PT here:**
- **No depth for a PT boss.** The tub bosses may reach no deeper than x -7.6 behind the front wall (the Pi stack drops
  in past them: the `pi_in` sweep leaves about 2.4 mm behind the wall). A PT 3.0 needs >= 7.0 of engagement plus a
  1.0 tip reserve (section B); a short insert needs 4.2.
- **Reuse.** The pinch s_c4 is loosened and re-tightened at every lens swap and every level check, and s_c1..s_c3 come
  out for a collar swap or for hood / Pi service. A machine thread in brass has no 5-drive limit (section D).
- **A defined clamp.** The collar's grip on the lens band and its anchor preload are set by torque on a machine
  thread; a thread-forming screw in ASA would add the forming torque and creep to that number.

**Hardware** (`layout.M3`, `layout.SCREWS` kind M3; BOM D2-35..D2-39):

| Screw | Size | Into | Insert | Torque (N m) | Step | Drive |
|---|---|---|---|---|---|---|
| s_c1, s_c2, s_c3 | M3 x 10 ISO 7045 PH1 A2 + ISO 7089 washer 3.2 x 7.0 x 0.5 | through a collar foot (counterbore dia 7.5, clearance 3.4) into a tub boss TL (11, 90.5), TR (-11, 90.5), LL (28, 36) | short brass insert L 4.0 (OD 4.6 class), bore 4.0, x -2.8..-6.8 (0.1 below the face); engagement 3.9 | 0.15 maximum, provisional until G-COL-1; stop at head contact | 7 | along -X from the front |
| s_c4 (the pinch) | M3 x 16 ISO 7045 PH1 A2 + washer | clearance 3.4 through the upper lug, across the 2.0 slit | brass insert L 5.7 in the lower lug, z 50.1..55.8; engagement 5.3 | 0.2; the last operation on the lens | 8 | straight down (-Z) from above |

- The head (dia 5.6 x 2.4) is the PT head size class, so the driver model and the bit (dia 6.5) are the same. PH1
  only; no hex or socket head (section G).
- Cloud-polish A1: s_c4 sits at y -31.0; the upper-lug rear edge is x 0.7 and its upper bearing edge is not chamfered. The same ISO 7089 washer has a full flat bearing footprint including 0.2 screw float and 0.2 edge allowance; the relief wall is y -27.0. No additional washer type or part is required.
- s_c4 sits at x 4.7 (r5 step 2: at x 4.8 the collar's 0.6 bed chamfer left 1.585 of wall next to the lug insert;
  at 4.7 the walls are 1.70 and 1.685).
- **Setting the inserts** (ASSEMBLY B1, before step 3 for the tub, any time before step 7 for the collar): the
  soldering iron with an M3 heat-set tip (BOM D2-74), pressed straight along the bore axis until the insert stands
  0.1 below the face; let it cool before any load. The tub bosses are reached from the front with the tub empty; the
  lug insert goes in from below the lower lug.
- **Computed measurements** (`checks.check_inserts`, release build): bore dia 4.0 +-0.1, open at one end; depth from
  the boss face >= insert + 0.2 (s_c1 / s_c2 / s_c3 4.2; s_c4 6.0); wall >= 1.6 (s_c1 / s_c2 2.0, s_c3 1.706, s_c4
  1.685); engagement >= 3.0 (3.9 / 5.3); the tip and tip + 0.2 in a void (no bottoming); >= 1.6 of material under
  each washer.
- **Provisional anchor torque:** s_c1..s_c3 are capped at 0.15 N m in this fork, reduced from r5's 0.25. The simple T/(K d) estimate with K = 0.2..0.3 gives 167..250 N preload, not measured insert capacity. The nominal 100 N relaxed anchor allowance remains an assumption until G-COL-1 tests the actual short insert, print orientation and material. Never interpret the computed service-load screen as a pull-out test.
- **Not measured:** the pull-out and torque-out of a short insert in printed ASA, the pinch force at 0.2 N m and its
  relaxation, and the anchor preload. G-COL-1 (SPEC s10) measures them on the collar coupons and replaces the
  `layout.LOAD_MODEL` estimates (pinch 120 N, relaxation 0.5, anchor 100 N).
- **Counts:** the PT counts and checks of A-H are unchanged (7 PT screws); the 4 M3 screws are counted on their own
  (DESIGN s1.1). Spares: 2 short inserts, 1 screw of each length, 2 washers (BOM); a spare lug insert comes from the
  D2-32 pack.
