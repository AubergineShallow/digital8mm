# D2 r5 audit: geometry and physics of the lens support and camera stack

Auditor: geometry/physics (one of three). Date 2026-10-06. Read-only. No CadQuery build was run.

**Evidence:**
- Code: `layout.py` (CAM 218-262, COLLAR 267-283, M3 287-295, LENSES 548-576, collar_spec 626-647, LOAD_MODEL 1641),
  `cots.py` (gs_camera_parts 148-181, lens_proxy 202-219), `printed_collar.py`, `checks.py` (J7_FLOAT_RULES 1634,
  check_j7_float 1707, check_lens_clamp 1879-1964);
- Outputs: `out/checks.json`, `out/parts-manifest.json`, `out/stl/{tub,hood,panel,lens_collar}.stl`;
- Research: `research/r5-lens-support/dossier_*.md`, `gs_side_zoom.png`;
- Docs: SPEC s10 (G-COL-1, G-CAM-2), PRINT-GUIDE.
- My scripts, in this folder:
  - `geo_float.py`: an analytic GS stack against the production STLs, which I moved back from print pose into the
    assembly frame;
  - `geo_clamp.py`: the clamp, thermal, insert and tolerance-stack numbers.

I formed my view first, and only then read `research/r5-lens-support/verify/review_geometry.md` (G1-G9) to label each
finding.

## Summary of severities

| id | sev | label | one line |
|---|---|---|---|
| X1 | **major** | NEW | The ASA collar clamp has almost no elastic follow-up. ASA-vs-aluminium expansion over +30 K removes about 270-320 N of hoop tension, against the 60-120 N the model assumes, so the clamp can go slack at the G-W11 50 C condition |
| X2 | minor | NEW | No centring feature between the collar bore and the tub lip. The worst-case lateral stack (0.60) uses most of the 0.75 BFAR counterbore gap |
| X3 | minor | CONFIRMS G3 (extends) | The axial float hangs on the band-edge geometry. The chamfer alone moves the seat ±0.3 on the 45 deg cone, on top of the ±0.5 drawing value |
| X4 | minor | CONFIRMS G1 / G2 | The datum chain puts the image plane at or behind the PCB front at s_nom 1.25 |
| X5 | minor | CONFIRMS G4 | An anchor torque of 0.25 N m gives a 280-420 N preload on short L4 inserts in ASA |
| X6 | note | DISAGREES G5 (severity) | Prying on the bolted-only triangle does not matter while the preload lasts (6.4 N demand against more than 170 N preload). It matters only if X1 or X5 relaxation removes the preload |
| X7 | note | extends G6 | The 3 ears are bolted before the pinch, so the bore cannot close uniformly. The uniform-pressure M_sep model does not describe this collar |
| X8 | note | CONFIRMS G9 | Keeper gap at nominal s: 2.25 measured on the STL; the comment at layout.py:261 says 1.75 |
| X9 | note | NEW | Optics and access: no vignetting is possible, and the focus/iris rings and thumb screws are clear. Leveling range before the cover meets the roll fin is about ±2.3 deg |

Verified OK is at the end.

---

## X1 (major, NEW): thermal and creep relaxation of the collar pinch. The float relies on a clamp that has no spring.

**Evidence:**
- `printed_collar.py` builds a solid ASA split ring: bore r 21.15, outside r 30, x 0.3..8.6, giving a hoop section of
  8.85 x 8.3 = 73.5 mm2.
- The pinch is one M3 x 16 through stubby lugs (`COLLAR['lug']`, layout.py:279). Nothing in the joint is a spring.
- The material is ASA (PRINT-GUIDE row 12). The lens band is aluminium (Kowa knurl). LOAD_MODEL assumes pinch 120 N
  and relax 0.5 (layout.py:1641).

**Numbers (`geo_clamp.py`):**
- Thermal mismatch, ASA about 95e-6/K against Al 23e-6/K, ΔT 30 K (20 to 50 C):
  - radial mismatch at the bore is 0.046 mm;
  - the elastic radial interference that a 60 N hoop tension produces is only 0.009 mm (0.017 mm at 120 N);
  - the ring is the dominant compliance in the joint (screw about 9e4 N/mm, lugs about 1e4 N/mm, ring hoop about
    900 N/mm in slit terms).
- Hoop-tension loss is E·A·Δα·ΔT = **270-320 N** for +30 K, and about 106 N for only +10 K.
- Compared with what the joint can have:
  - the s_c4 torque of 0.2 N m gives 220-330 N at most (K 0.2-0.3);
  - the model's relaxed value is 60 N.
- The joint therefore goes slack somewhere between about +7 K (relaxed state) and +30 K (fresh).
- ASA stress relaxation at 50 C acts in the same direction. A creep strain of 0.1 % in the hoop direction is 0.02 mm
  radial, already twice the elastic interference at 60 N.

**Failure scenario:**
- At 50 C, or after some weeks, the lens sits in a bore 0.09 mm larger in diameter than the band, held only by the
  rearward cone.
- Free tilt over the 5.4 band is about 0.9 deg. That is 0.5 mm at the cover rear and 0.8 mm at the lens front: the
  same size as the 0.4-0.8 catch gaps.
- Lens-down, gravity pushes lens and camera forward (2.5 N at 1 g, 12.4 N at 5 g). With friction gone, they slide
  until the BFAR face lands on the lip catch, 0.5 mm away.
- The lens weight then runs lens → adapter → BFAR → lip, and the camera's tail rests on catches. That is exactly the
  camera-joint loading J7-R exists to remove (focus tilt), and the aim depends on how the camera is held.
- Roll slip under the focus-ring torque also returns: 2.4 N m of friction capacity at 60 N, but 0 when slack.

**Gates:**
- G-COL-1 (SPEC.md:430) only says "repeat after 24 h at 50 C (re-torque check)". It does not say the slip and
  stiffness tests run while hot.
- G-CAM-2 (d) runs 1 h at 50 C, but it measures focus tilt, which a slack lens hanging free may not show.
- Neither gate measures the remaining pinch force.
- `lens_clamp` does not model temperature.

**Fix (pick one):**
- Add elastic follow-up to s_c4: 2-3 M3 disc springs (DIN 2093 class, about 0.3 mm stroke at 150-250 N) under the
  washer, or a longer screw with a spring stack. This needs a FASTENER-POLICY note.
- Or make the collar from a low-CTE material: CF-PA or CF-PETG at about 20-40e-6/K. PC at about 65e-6/K helps only
  partly.
- Or put a thin stainless band clamp around the collar.

In every case:
- run the G-COL-1 slip tests (1.0 N m roll, 50 N axial, 3x mass) **at 50 C** and again after cooling;
- add a thermal term to LOAD_MODEL and `check_lens_clamp` (hoop loss = E·A·Δα·ΔT against the pinch);
- G-CAM-2 should record the aim and a "lens-down, tap" case at 50 C.

## X2 (minor, NEW): nothing centres the collar on the lip axis

**Evidence:**
- The collar is located only by 3 M3 screws in 3.4 clearance holes (layout.py:288) over heat-set inserts.
- The feet (dia 7.6) sit in hood holes dia 8.6, which locate nothing.
- The camera then hangs wherever the lens axis is. The pinch also pushes the lens to one side of the 0.3 diametral bore
  clearance (see X7).

**Stack (`geo_clamp.py`):**

| Contribution | mm |
|---|---|
| screw clearance | 0.2 |
| insert position after heat-setting | 0.15 |
| bore pinch offset | 0.15 |
| printed hole and bore error | 0.1 |
| **worst case** | **0.60** |
| **RSS** | **0.31** |

- Measured on the STLs (`geo_float.py`), the gaps it eats are BFAR to counterbore 0.75 (0.73), adapter to lip bore
  0.825 (0.805) and cover to hood fin 0.81.
- The worst case leaves 0.15 at the BFAR, below the 0.6 rule. The hood's own tolerance in Y/Z, from the hook joint,
  adds to the fin gap.

**Failure scenario:** the BFAR head bears on the counterbore wall. The camera is then side-loaded by the chassis, and
nobody can see it, because the contact is inside the tub.

**Fix:**
- Add a printed centring plug for assembly step 2: a spigot in the lip bore dia 32.4 plus a ring in the collar bore.
  Tighten s_c1..s_c3 with the plug in place, then remove it.
- Or give 2 of the feet a locating spigot, with 0.1 clearance, in reamed holes in the tub face.
- Add a check that the collar bore axis is coaxial with the lip within 0.1 (as designed it is 0, so the check only
  guards against regressions).

## X3 (minor, CONFIRMS G3 and adds the chamfer term): the axial datum is the band's rear edge on a 45 deg cone

**Evidence:**
- `collar_spec` (layout.py:637-642) seats the band edge at r = d/2 - edge_chamfer = 20.7, with chamfer 0.3
  `'drawing'` (layout.py:564).
- On a 45 deg cone, an error Δr in the contact radius moves the lens, and the hanging camera, by Δr axially:
  - a square edge (chamfer 0): contact at r 21.0, so the lens sits **0.30 further forward** (rear-edge contact at
    r 21.0 on the cone);
  - a 0.5 chamfer or radius: 0.2 further back;
  - a knurl-peak OD 41.8: 0.1 back.
- The ±0.5 band position from the drawing adds to this.
- Gaps it eats, measured on the STLs: BFAR to lip 0.5 (0.48), tab to tub wall at s 0 0.4 (0.38), cover to keeper at
  s 3 0.5 (0.50).
- Knurl peaks seating on the ASA cone will also indent it under the push-back and the pinch, a small rearward settle.

**Fix:**
- G-LENS must record the band OD (peak), rear-edge form (chamfer or radius), and edge-to-flange distance.
- `LENSES[..]['support']` must be updated and the tub, collar and panel rebuilt before any of them is printed (G3).
- Consider a 30-37 deg cone, or a flat axial shoulder plus a radial bore. A flat shoulder makes the seat insensitive to
  chamfer and OD.

## X4 (minor, CONFIRMS G1 / G2): the stack is not anchored to the sensor plane

**Evidence:**
- C flange to PCB front = 5.0 + 1.2 + s + 10.35 = 16.55 + s.
- At s_nom 1.25 (layout.py:225) that is 17.80.
- Infinity focus needs 17.526 plus the IR plate shift (about 0.37) plus the die height above the PCB: 17.90 + die.
- So the modelled image plane lies at or behind the PCB front, which is impossible.
- The GS spec's back-focus range "12.5-22.4" (dossier_external s2) would also put s at infinity near 0. At least one of
  housing 10.35, adapter 5.0 / 5.8 (G2) or s_nom is off by about 1 mm.

**Consequence:**
- The float rows at s 0 / 3 still bound the camera only if the real s at infinity lies in 0..3.
- With G2's 0.8 shift, the keeper gap at s_max becomes negative.
- `s_range` 0..3 is also narrower than the inferred BFAR travel of about 4.9. A user who screws the BFAR out past 3
  (macro focusing) drives the cover into the keeper.

**Fix:**
- Add a `CAM['sensor']` datum (`'unconfirmed'`) and derive s_nom from it.
- MP-CAM should measure C flange to cover rear directly (G2).
- Document "never set s > 3" at B0, or size the keeper for the full travel.

## X5 (minor, CONFIRMS G4): anchor torque against short-insert pull-out and ASA creep

**Evidence and numbers:**
- 0.25 N m (layout.py:295) gives 280-420 N per screw.
- The inserts are L 4.0, bore depth 4.2 (checks.json inserts), loaded in the pull-out direction (installed from the
  head side). s_c3's wall is 1.706 at the pilot, about 1.4 outside the knurl.
- Short M3 inserts in ASA typically pull out at a few hundred N (estimate), so SF is about 1.
- The washer bearing on the printed ear: 350 N on (7.0² - 3.4²)π/4 = 29 mm² is 12 MPa. ASA creeps there at 50 C, so
  the preload decays. That is acceptable only because the service demand is 6.4 N (X6).
- s_c4 is reverse-mounted (the screw pulls the insert deeper), which is the strong direction. That joint is fine.

**Fix:** 0.12-0.15 N m (170-250 N), plus a G-COL-1 pull-out-to-failure on one coupon insert.

## X6 (note, DISAGREES with G5 on weight): prying on the anchors

**Numbers:**
- The 5 g pitch moment about the tub face is 0.316 N m (`lens_clamp` M_wall 0.063 x 5).
- The real pitch pivot is the LL-LR line, at z 40.8 on the axis. `checks.py:1909` uses min z 36, which gives
  5.8 N; my figure is 6.4 N.
- Even with G5's prying factor of 2-3, demand stays at or below 20 N, against a preload of at least 170 N per screw.
  A bolted joint does not open, and the polygon criterion is irrelevant while the preload exists.
- It only matters after relaxation (X1 creep, X5).

**Fix:** use the LL-LR line as the pivot (a one-line change), and leave the rest.

## X7 (note, extends G6): the pinch acts on a ring that is already bolted at TL, TR and LL

**Evidence:**
- Assembly order (R5-BRIEF choice 7): s_c1..s_c3 are tight before s_c4.
- Angles from +Y: slit 180 deg, TR 110 deg, TL 70 deg, LL -41 deg, LR (compression only) 220 deg.
- The upper arc from the slit to TR is only 70 deg, short and stiff. The lower arc to LL is 140 deg and compliant. Its
  only support is the unbolted LR foot, which will slide or lift as the arc flexes.

**Consequence:**
- The bore closes unevenly. Contact concentrates near the slit lips and on the far wall, and the lens shifts up to
  0.15 off the axis (X2).
- The (π/6)FL uniform-pressure result (checks.py:1925) is not the governing model.

**Fix:**
- G-COL-1 must use the production order (ears torqued first) and measure the pinch force (for example a load washer,
  or turn-of-nut against a calibrated coupon).
- Treat M_sep as an upper bound (G6).

## X8 (note, CONFIRMS G9)

- STL measurement: cover to panel keeper is 2.254 at s 1.25, and 0.504 at s 3.0.
- The keeper comment at layout.py:261 says "1.75 at nominal". Fix the comment.

## X9 (note, NEW, mostly a pass): optics and access

- **Vignetting.**
  - The image path is rear element → adapter bore dia 25.5 → BFAR → housing throat.
  - No printed part lies inside the adapter, BFAR or housing bores.
  - Every printed part ends behind x 8.64 (manifest), while the lens front is at x 57.2. The sensor's 27.7 deg field
    half-angle cannot reach any of them.
  - **No obstruction possible.**
- **Ring access.**
  - Kowa focus ring x 11.2..23.0 (r 20.85) and iris x 31.5..37.2. Collar front 8.6 (2.6 behind the focus ring); collar
    r 30 against ring r 20.85.
  - The rear 2-3 mm of the focus ring is partly shadowed for a fingertip, but usable.
  - The thumb-screw keep-outs show 0 mm3.
  - Fujinon: front 8.6 equals its limit 8.6 (0 margin, band `'assumed'`).
- **Leveling.**
  - The lens and camera rotate together in the bore before the pinch.
  - The cover corner meets the hood roll fin (0.81 gap at about 20 mm lever) after about ±2.3 deg of roll. That is
    enough for leveling, but the Kowa's scales end up at a random clock (cosmetic).
- **Computar (data-only).** cone_x0 -0.4 lies behind the collar rear 0.3, and front_margin is -2.0. It cannot be built
  as is. Note it before anyone adds it to `LENSES`.

## Verified OK (independently)

- **Camera model against the GS drawing.**
  - gs_side_zoom: adapter element 5.8, thin scalloped BFAR head, housing, PCB 1.4, curved cover 6.49 max, top tab with
    a transverse lock screw.
  - `gs_camera_parts` builds this in the right order, and the sign of s is right: the housing moves -X as the BFAR
    screws out, while the BFAR face, adapter and lens stay fixed.
  - The tripod block is not modelled.
- **Float gaps reproduced from the STLs** (assembly frame; my numbers read about 0.02 low because of the OCC bbox
  padding):

| Gap | s 0 | s 1.25 | s 3 |
|---|---|---|---|
| tab to tub wall | 0.38 | 1.63 | 3.38 |
| BFAR to lip / counterbore | 0.48 | 0.48 | 0.48 |
| adapter to lip | 0.805 | 0.805 | 0.805 |
| cover to hood fin | 0.81 | 0.81 | 0.81 |
| cover to keeper | 3.50 | 2.25 | 0.50 |
| collar to any camera part | at least 3.26 | at least 3.26 | at least 3.26 |

  These match `checks.json` j7_float (0.40 / 0.50 / 0.825 / 0.80 / 0.50).
- **Lens vs camera:** 0 mm3 at every s. The Kowa rear (x -6.1) sits in the throat at s 0, with r 12.7 against 12.75.
- **Clamp numbers reproduced:**
  - M_sep 0.1696 N m; M_static 0.0572 (lens 0.049 + camera 0.007 + adapter, as |lever| sums); 5 g 0.286 N m;
  - axial friction about 113 N and roll friction about 2.4 N m at 60 N, μ 0.3 (room temperature only, see X1).
- **Mass and CoM:**
  - item sums give 895.0 g, x -45.53, so +1.47 from the grip axis -47.0;
  - Fujinon: 781.6 g, -9.76;
  - a delta check from the Fujinon to the Kowa build closes.
  - The Kowa CoM of 28.3 from the flange is unverified. A heavy front group may put it at 30-33, adding about 0.5 mm
    of system CoM and about 8 % of moment.
- **G-CAM-2 4 um criterion:** 4 um over a 3.15 mm half-diagonal is about 0.07 deg, about 1/3 of ±12 um DOF (f/1.8,
  c 2 px). Sensible.
