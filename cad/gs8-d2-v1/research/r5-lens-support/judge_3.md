# Judge 3 review: D2 heavy-lens sag fix (optics and tolerance lens), 2026-10-06

Read-only review. No repo file was edited, built or re-run. My only probe is
`scratchpad/sag/j3/p_pidrop.py` (+ `.json`): the `pi_in` sweep (real `cots` proxies pi5, cooler, x1203, x1203_kit,
path `layout.INSERTIONS['pi_in']`, 2 mm steps) against the tub bosses proposed by designs 1 and 3.

## 1. Scores (0-100; total = 0.30 bypass + 0.20 alignment + 0.20 buildability + 0.15 robustness + 0.10 generality + 0.05 impl_risk)

| Design | Bypass | Alignment | Buildability | Robustness (camera internals) | Generality (300-600 g) | Impl risk (high = low risk) | **Total** |
|---|---|---|---|---|---|---|---|
| 1 lens collar + floating camera (J7-R) | 85 | 55 | 50 | 75 | 75 | 35 | **67** |
| 2 housing cradle + clip (camera held at its aluminium housing) | 55 | 70 | 55 | 35 | 40 | 50 | **53** |
| 3 lens collar bearing (LCB) on tub + panel | 75 | 40 | 40 | 60 | 75 | 40 | **57** |

**Recommendation: Design 1's architecture (lens held at its fixed barrel, camera body floats), corrected and
hybridised (s.5).** The decisive optics argument: in designs 1 and 3 every printed-part creep, preload loss and
chassis flex moves the lens *and* the sensor together (aim only), so it cannot tilt focus. In design 2 the lens moment
still crosses the camera's own BFAR fine thread and two hand-tight C/CS threads, so focus tilt under load depends on
unknown thread play. Design 1 beats design 3 because it already gives the camera an explicit float cage, keeps its
anchors out of the Pi drop, and handles roll and back focus cleanly. Both lens-collar designs share one hidden flaw (an
axial over-constraint), which I fix by moving the axial datum into the collar.

## 2. What I verified (and how)

| Claim | Result | Evidence |
|---|---|---|
| The real camera's front 5.8 element is the adapter (dia ~31), the thin 1.2 element is the BFAR head (dia ~36.6) | **Confirmed** | `gs_side_zoom.png` at 20.1 px/mm (from the 39.5 cover): front element 625 px = 31.1; serrated element 735 px = 36.6; housing 208 px = 10.35; PCB 27 px = 1.34 |
| Top tab top ~22 above the axis; tripod block bottom ~31 below | **Confirmed** | same image: 442 px / 626 px from the cover centre |
| Tripod block collides with the Active Cooler and `ko_exhaust` if the housing front sits at x -5.2 | **Confirmed** | block x -17.24..-5.2, z ~29..; cooler B(-72.8, -9.5, -25.55, 16.95, 20.2, 36.3); ko_exhaust z <= 36.2 (`layout.py:485-487, 592`) |
| D2 pins (tips x -8.2) do not reach the real PCB (front x ~ -15.6) | **Confirmed** | `printed_tub.py:195-198`; arithmetic |
| With the block off, today's J7 lets the real module pitch ~5 deg nose-down (pivot on the tab, keeper 1.23 behind the real cover, 14 below) | **Confirmed** (arithmetic) | `layout.py:212` keeper; design 2 s0.2 |
| The real stack puts the Kowa dia 42 knurl inside the turret (x 0..8.5, bore 36.5) | **Confirmed** | C flange +0.2..+2.3 in any real-stack reading; turret `layout.py:97-98` |
| Driver audit: bit dia 6.5 x 40 + handle 30 x 100, checked against every part present at the screw's step (own part included) | **Confirmed** | `checks.py:470-514`; `layout.screw_audit_set` 777-780 |
| `COTS['pt_screws']` counts `len(SCREWS)` | **Confirmed**: any non-PT entry added to SCREWS miscounts PT | `layout.py:980, 1252` |
| Hood = band + front plate only (no side walls); plate front-top chamfer 3.0 from (x 0, z 97) to (x -3, z 100) | **Confirmed** | `printed_hood.py:37, 136-138` |
| Design 1 nut bosses (x -7.6..-5.2) clear `pi_in` | **Confirmed 0 mm3** | `j3/p_pidrop.json` |
| Design 3 `boss_l1` (dia 8, x -13.85..-5.2 at y 0, z 88.5 + corbel) clears the Pi | **Refuted: 106 mm3** at path offset (-2.8, 2.1, 68) | `j3/p_pidrop.json` |
| FASTENER-POLICY already sanctions M3 heat-set inserts + ISO 7045 M3 PH1 (insert fallback) | **Confirmed** | `FASTENER-POLICY.md` s E.3-E.4, G |
| Policy: joint gap closed by a screw <= 0.1 | **Confirmed** | `FASTENER-POLICY.md` s B table |

Accepted from the dossiers without independent web checks: the housing/BFAR/adapter are aluminium; housing to PCB is 2
M2-class screws with nylon washers on a sticky gasket; the BFAR moves ~0.75-0.8 mm per turn; the Kowa dia 42 knurl at
flange +2.2..+7.6 is *inferred* fixed (`kowa_zoom.png`: the focus thumb screw sits on the plain distance-scale barrel,
not on the knurl, which supports the inference; it remains gate G-LENS).

## 3. Refuted or corrected claims

### Design 1
1. **"The adapter-BFAR face joint is clamped further, not opened" (s3.2) is backwards.** The lip pushes the BFAR face
   toward -X while the collar holds the lens (and through it the adapter). The adapter shoulder presses the BFAR face
   toward -X too, and the thread pulls it +X; an extra -X load on the BFAR therefore *unloads* the shoulder joint. On
   heating the ASA loop grows ~0.7 um/K more than the metal (design 1's own figure), so the lip load rises with
   temperature.
2. **"Concentric compression" is unlikely.** Squareness of the collar bore to the lip plane (two printed parts, two
   seats) is of order 0.1-0.2 deg, i.e. 0.06-0.12 mm runout over a dia 34 face, more than the 28 um thermal
   interference. The contact will be one-sided, so the 10-15 N becomes a 0.17-0.25 N m moment at r ~17 on the
   adapter-BFAR joint, which is in the lens-to-sensor chain and is preloaded only by hand torque (~20-60 N at
   0.1-0.3 N m on a 1"-32 thread). That is 2-3x the Kowa static moment the design set out to remove. The lip must not
   be a final-state contact.
3. **Hood foot holes TL/TR (dia 9 at z 92) leave a 0.35-0.5 mm ligament** under the front-top chamfer (hole top 96.5;
   chamfer plane z + |x| = 97). That violates MIN_WALL 1.2 / MIN_FEATURE 0.8 (`layout.py:44-57`).
4. **Pinch head in a dia 6.0 channel fails the driver audit** (bit dia 6.5; the collar is in the step-9 audit set) and
   the policy counterbore rule (dia 7.0).
5. **Pinch counterbore (dia 7) at x 5.6 on a 5.8-long tube (x 2.7..8.5)** is wider than the tube: it breaks out of both
   ends, and its open-top channel (y -25.5 +- 3, from z 64 up to the OD at z ~80) removes almost the whole tube wall
   above the upper jaw: the hoop path survives only through ~1.3 mm inside the channel. Put the screw on external lugs.
6. Minor: an open-rear hex pocket does not retain the nut when the bolt is out (admitted: "a lost nut means taking the
   hood off"); the Kowa collar bore 42.1 (0.05 radial) is tighter than FDM bore accuracy (~+-0.1).

### Design 2
1. **"No plastic is in this path ... the focus sag is gone" overclaims.** The lens moment and every focus/iris ring
   torque still run lens -> C thread -> adapter -> CS thread -> BFAR -> BFAR-housing fine thread (locked only by the
   split-tab pinch). The 2000 N m/rad chain stiffness is an unsupported estimate; the external dossier reports wobble
   with few threads engaged and a BFAR that turns unless locked. Gasket creep is removed; thread play is not.
2. The cradle copies "the removed block's mating faces and its 2 screw holes", which are **unknown** (block removability
   is unconfirmed and its interface unmeasured). The cradle cannot be drawn before MP-CAM.
3. The hood plate becomes part of the J7 screw stack (pads + 0.05 closure): J1 (hook-on hood) gains a screwed front
   joint and a creeping 2.0 under-head layer. Not wrong, but undeclared as a J1 change.
4. Driver-probe artefact: "overlap only the dia 7 x 0.5 cbore itself (16.6 mm3)" means the probe did not cut the
   counterbore; with it cut, the bit (dia 6.5) clears.

### Design 3
1. **`boss_l1` lies in the Pi stack drop path: 106 mm3 overlap with the `pi_in` sweep** (probe). Behind the front wall
   the Pi column leaves only x -5.2..-8.35 for y -32.3..25.8 at z > 41, so a PT boss with engage >= 7 (needs >= 8 of
   material behind x -2.7) cannot exist anywhere along the top. The S1 anchor as specified is infeasible; this is why
   rib_r and the baffle were deleted (`printed_tub.py:207-216`).
2. **"No axial preload of the module" is contradicted by its own procedure and model.** The seat (housing front plane /
   lands at x -5.2) stays a declared contact, and the back-focus step says to "finish with an outward motion ... pulls
   the module onto its seat". After the pinch this is a closed loop wall -> tab -> housing -> BFAR-housing thread ->
   BFAR -> adapter -> lens -> LCB -> wall. Heating pushes the tab into the wall by (alpha_ASA - alpha_Al) x ~10 mm x
   25-50 K = 18-36 um, so the force through an off-axis tab (r ~20) puts a tilting moment on the BFAR thread that can
   exceed today's Kowa static moment. "Seat lands inside the rigid-disc zone" addresses wall flex only.
3. **Roll key with the real camera is unspecified.** Pins dia 1.6 do not reach the real PCB (7 mm short); "tines beside
   the top tab" is not designed.
4. Panel bosses sit 0.15 behind the tub wall, so s_l2/s_l3 close 0.15 > the policy's 0.1.
5. "s_l1 sits 4.5 above the real top tab": it is 2.4-2.9 (boss bottom z 84.5 vs tab top z 81.6-82.1).
6. The D opening (58 wide) leaves 2.9/3.35 strips holding the whole lower plate (plunger guard, SD slot, exhaust
   slots) of an L-section hood with no side walls; it is retained only after step 9 by the LCB lip.
7. Per-lens LCB on PT screws: every lens swap is one of the 5 policy re-assemblies of s_l1..s_l3.

## 4. Assessment through the optics and tolerance lens

**Image-plane budget.** f/1.8, CoC 2 px = 6.9 um, depth of focus +-12.4 um; over the IMX296 half-width (2.51 mm)
that is ~0.27 deg of lens-to-sensor tilt for the whole build. Only *relative* lens-sensor tilt spends it. Rigid
motion of lens + camera together is aim (framing), not focus.

**The lens-to-sensor chain** is lens flange -> C thread -> adapter -> adapter shoulder on BFAR face (hand preload) ->
CS thread -> BFAR -> BFAR-housing fine thread (split-tab lock) -> aluminium housing -> 2 M2 + nylon washers + gasket ->
PCB -> sensor. A fix is good to the degree that, after assembly, *no chassis load path enters this chain at two
points*.

| | Design 1 | Design 2 | Design 3 |
|---|---|---|---|
| Where the chassis touches the chain | lens fixed band (collar) **and** BFAR face (lip, one-sided, thermally preloaded) | housing (tab + cradle) | lens fixed band (LCB) **and** housing tab (seat, thermally preloaded) |
| Joints carrying the lens moment | none (camera body hangs) | C thread, CS thread, BFAR-housing thread | none in principle; the seat loop loads the BFAR-housing thread when warm |
| Joints carrying a forced (over-constraint) load | adapter shoulder (unloaded by the lip) | none (cradle compliance absorbs misfit) | BFAR-housing thread via the tab |
| Focus/iris ring torque path | collar (outside the chain) | through the C/CS threads (can unscrew adapter) | LCB (outside the chain) |
| Printed creep affects | aim only | aim only | aim only (plus the seat preload) |
| Depends on unknown camera internals | BFAR face annulus (lip), block removable | block interface, coplanarity, BFAR-thread play, lock-screw side | roll key, tab, lock-screw side |
| Back focus | bench, before step 7; immune to s (lip datum) | bench; adapter removed for insertion (risks the setting) | in-body, powered Pi, panel off, needs the lock screw on +Y |

**Design 1** is the right architecture: it is the only one that states the float as a checkable requirement (every
cage gap listed), has anchors that clear the Pi drop, decouples back focus from the collar, and supplies roll control
(hood fin) for the real camera. Its defects (s3.D1) are local and fixable; the lip over-constraint is fixed by making
the collar, not the lip, the axial datum.

**Design 2** is the best answer to "stop the module rocking" and the cheapest in new parts per lens, and it does remove
the most creep-prone joint (gasket/washers). But it leaves the lens moment, hand loads and ring torques on three
threads inside the optical chain, it is blocked until the tripod-block interface is measured, and for 300-600 g zooms
it needs a second (lens) support anyway (its own risk 3). It scores well on alignment and poorly on robustness and
generality.

**Design 3** has the best analysis (plate FE of the wall, sleeve stiffness, load table) and the best lens-data hygiene
(`support` dicts, thumb-screw sweep keep-out, adapter-clamp fallback LCB-A), but as specified its top anchor is
unbuildable (Pi drop), its module keeps a preloaded housing seat (the over-constraint that the concept exists to
avoid), and its hood opening weakens the plate. Its useful parts are grafted below.

## 5. Recommendation and grafts

**Final design: "J7-R float" = design 1 with five corrections**
1. **Axial datum in the collar, not the lip.** The collar bore ends in a 45 deg cone seat that the lens's fixed band
   rear edge (Kowa: knurl rear face, flange +2.2) is pushed back onto before the pinch. The tub lip and the panel
   keeper become *catches with gaps* (lip 0.5 axial, keeper >= 0.5 at s_max). In the final state the camera body, BFAR
   and adapter touch nothing in the chassis; the only chassis contact of the optical unit is lens band / collar.
2. **Anchors = M3 heat-set inserts (FASTENER-POLICY E hardware) in 3 short tub bosses** (x -7.6..-5.2, probe 0 mm3
   against `pi_in`), M3 x 10 ISO 7045 PH1 + washer from the front. No loose nuts, unlimited lens-swap cycles.
3. **TL/TR anchors moved to (+-11, 90.5) and hood holes reduced to dia 8.6** (feet dia 7.6): full 1.2 ring of plate
   round every hole (probe `j3/p_hood.json`), bosses 2.4 from the hood, 0 mm3 in the hood drop.
4. **Pinch on external lugs outside the ring** (screw at y -33.5, M3 x 5.7 insert in the lower lug), so the driver
   channel no longer cuts the hoop path and the dia 6.5 audit bit clears.
5. **Collar bore = band + 0.3 diametral** (FDM-realistic), C-ring closes with a few N.

**Grafts**
- From design 3: `LENSES[...]['support']` band data and corrected Kowa segments; `ko_lens_thumb` sweep keep-out
  replacing the clocked `lock_screws`; a `LOAD_MODEL`-driven load/clamp check (its wall FE coefficients 0.079-0.146
  deg/N m as the documented aim stiffness); the G-LCB-1-style warm re-torque gate; the requirement "a lens needs a
  fixed band >= 5 mm (>= 15 mm for zooms) to get a collar"; optional left-edge panel tie (one PT through the wall into
  a panel boss at (27, 74)) only if G-COL-1 shows zoom aim > 0.3 deg.
- From design 2: the real-camera sub-solid model (cover, PCB, housing, tab, lock-screw envelope, BFAR, adapter;
  tripod block removed) and its `j7_load_path` idea of "every printed solid >= x from the PCB+cover sub-solid", with a
  synthetic FAIL test; the BFAR/adapter ring-clamp rejection arithmetic for the docs; the G-LENS dial-indicator
  protocol with the lock screw loose and tight.
- From design 1 (kept): float cage, hood roll fin, keeper as rear catch, adapter moved to step 7 with the camera, bench
  back focus (B0) with the measured s, parametric s 0..3, M3 hardware rationale, mount-polygon check, collar per lens.

## 6. Implementation spec (J7-R float)

Order: (0) MP-CAM + G-LENS measurements, then (1) layout, (2) cots, (3) printed parts, (4) checks/build/tables, (5)
tests, (6) docs. Build only through `run_locked.py`. Every number below is a `layout.py` parameter; values in
brackets are placeholders that MP-CAM / G-LENS overwrite.

### 6.1 Datum chain (assembly frame; `layout.py`, replaces `CAM` fields, keep the dict name `CAM`)
| Name | Value | Rule |
|---|---|---|
| `X_FW_IN`, `XT1` | -5.2, -2.7 | unchanged |
| `CAM['lip_x']` | -3.9 | lip rear face; lip land x -3.9..-2.7 (1.2, land class) |
| `CAM['lip_d']` | 32.4 | lip opening; `dc.teardrop`, up +Y (as today's bore) |
| `CAM['cb_d']`, cb x | 37.5, x -5.3..-3.9 | counterbore round the BFAR head; teardrop up +Y |
| `CAM['lip_gap']` | 0.5 | BFAR face to lip in the final state (catch, never a seat) |
| `BFAR_FACE_X` = `CS_FLANGE_X` | lip_x - lip_gap = **-4.4** | derived |
| `CAM['adapter']` | d [30.75], ff [5.00], mass [4.0] | MP-CAM |
| `C_FLANGE_X` | BFAR_FACE_X + ff = **+0.6** | derived (was +10.6) |
| `CAM['bfar']` | d [36.0], t [1.2] | head x -5.6..-4.4 |
| `CAM['s']` | nom [1.25], range (0, 3.0) | BFAR screw-out at Kowa infinity (bench B0) |
| `x_hf(s)` | BFAR_FACE_X - t - s = -5.6 - s | housing front plane; tab gap to wall = 0.4 + s |
| `CAM['housing']` | d [35.5], depth 10.35 | x x_hf-10.35..x_hf |
| `CAM['tab']` | w 10.16, depth 5.02, top_r [22.1] | lock screw transverse at (x_hf-2.5, z 79.4); head envelope dia 4 x 2 modelled on **both** sides until MP-CAM |
| `CAM['pcb']`, `CAM['cover']` | 38 sq x 1.4; 39.5 sq x 6.49 | cover rear = x_hf - 18.24: -23.84 / -25.09 / -26.84 at s 0 / nom / max |
| tripod block | removed at bench B0 (its 2 screws bagged; BOM INCLUDED_IN gs_camera) | |
| `CAM['keeper']` | B(-30.67, -27.34, 4.0, SPLIT, 66, 76) | x1 = cover_rear(s_max) - 0.5 (rear catch only) |
| `ko_fpc_cam` | B(cover_rear(s_max) - 5.23, cover_rear(0) - 0.2, -8, 8, 39.4, 47.0) | spans the s range |
| `CAM['pins']`, `pin_*` | **deleted** (they do not reach the real PCB) | |

### 6.2 Lens data (`layout.LENSES`)
- Kowa segments from the Kowa drawing, contiguous, (r, x0, x1 from flange, label, moves): (12.7, -6.7, 0, thread,
  no), (15.75, 0, 2.2, spigot, no), (21.0, 2.2, 7.6, knurl, **no**), (19.5, 7.6, 10.6, groove, no), (20.85, 10.6,
  22.4, focus, rot), (19.3, 22.4, 30.9, label, trans?), (19.25, 30.9, 36.6, iris, rot), (20.75, 36.6, 41.7, step,
  trans?), (27.0, 41.7, 50.5, front barrel, trans), (25.0, 50.5, 56.6, front, trans). Keep mass 215, com 28.3
  (G-LENS).
- `support` = dict(d=[42.0], x0=2.2, x1=7.6, edge_chamfer=[0.3], status='drawing') (Kowa); Fujinon dict(d=[39.0],
  x0=[2.0], x1=[7.8], status='assumed'); optional `computar_h6z0812` (305 g, com [40], support d 48.5, x0 1.0, x1
  25.5).
- Replace `lock_screws` by `thumb_screws=[dict(x_from_flange=14.4, r_max=24.0, w=3.8), dict(x_from_flange=33.0,
  ...)]`; new keep-out `ko_lens_thumb` = rings r 0..24 over flange +12.5..+16.3 and +31.1..+34.9 (printed parts only).

### 6.3 New part `lens_collar` (`printed_collar.py`; copy the `printed_keeper.py` skeleton)
PARTS: material ASA (PC if G-W11 shows > 50 C at the camera), colour black, face_down '+X', owner tub, infill
'small', supports none, envelope (Kowa) B(-2.7, 8.6, -38.0, 30.0, 30.0, 95.0). One collar per `LENSES` entry with a
`support`; the build uses `L.LENS`. Mass ~18 g.

| Feature | Geometry (Kowa; formulas in brackets) |
|---|---|
| Body | disc OD 60 (r 30, as the old turret), x 0.3..8.6 [front = C_FLANGE_X + first moving segment x0 - 2.0 at most = 9.2] |
| Ear lobes | TL (11, 90.5), TR (-11, 90.5), LL (24.5, 36.0): discs r 4.4 hulled to the body, full length x 0.3..8.6 (solid from the bed, so no overhang); each with a dia 7.5 counterbore along X from x 8.6 down to the washer seat at x 2.8 |
| Feet | dia 7.6 posts x -2.7..0.3 at TL, TR, LL (through dia 3.4) and LR (-19.0, 44.0) (solid, compression only); rear faces x -2.7 are the datum on the tub outer face |
| Cone seat | 45 deg, from (x 0.8, r 18.7) to (x 3.25, r 21.15); r 18.7 cylinder x 0.3..0.8 [seat x = C_FLANGE_X + x0 = 2.8 at r = d/2 - edge_chamfer = 20.7]; prints as a 45 deg inward step (print-up is -X) |
| Bore | d 42.3 [support.d + 0.3], x 3.25..8.6 |
| Slit | 2.0 wide, z 59..61, -Y side, bore to the lug tips, x 0.3..8.6 |
| Pinch lugs (external) | x 1.0..8.6, y -38.0..-28.0 (merged into the body), upper lug z 61..66, lower lug z 50..59. Keep the screw outside the ring so no channel cuts the hoop path (design 1's in-wall channel nearly severs the upper jaw) |
| s_c4 | M3 x 16 ISO 7045 PH1 + ISO 7089 washer, axis (0,0,-1), head_point (4.8, -33.5, 66.5), tip (4.8, -33.5, 50.5); clearance dia 3.4 z 66..55.7; M3 x 5.7 insert from the lower-lug underside, drill dia 4.0 z 50.0..55.7 (walls 1.8 in x, 2.5 in y); bit inner edge y -30.25 clears the body (|y| <= 29.3 above z 66.5) by 0.95 |
| Bed | 0.6 x 45 deg bed chamfer on the +X face edges; no fillets there |

### 6.4 Tub (`printed_tub.py:_front`)
- Replace the dia 36.5 bore cut by two `dc.teardrop` cuts (up +Y): lip_d/2 over x -5.3..-2.5 and cb_d/2 over x
  -5.3..-3.9.
- Delete the pin loop (lines 195-198) and their CRITICAL_FEATURES rows (`layout.py:1011`).
- 3 insert bosses OD 8.0, x -7.6..-5.2, at (11, 90.5), (-11, 90.5), (24.5, 36.0); outer profile teardrop apex -Y (45
  deg print-down side); LL merges into the rib_l gusset. Insert bore from the outer face: dia 4.0 x -2.7..-6.9, then
  dia 3.4 through to x -7.6. Probes: 0 mm3 vs `pi_in` (p_pidrop_j3), 0 vs `hood_on`, 2.4 to the hood.
- Inserts: M3 short heat-set, length 3.0-4.0 [procure; G-COL-1], set flush -0.1 from x -2.7 at the bench before step 3.

### 6.5 Hood (`printed_hood.py`, `layout.HOOD`)
- Delete `turret`, `turret_b`, `_turret`, `TURRET_R_FILLET`, `BORE_CHAMFER`; `_bore_tool` cuts dia 36.5 + -Z drop over
  x -2.8..+0.3 only. HOOD_BOX x1 8.5 -> 1.0. Remove the turret tree support from PARTS['hood'] and PRINT.
- 4 foot holes dia 8.6, teardrop apex -Z, through x -2.8..+0.3 at TL, TR, LL, LR (positions from `COLLAR['feet']`).
- Roll fin (design 1): B(-23.5, -19.5, -22.8, -20.55, 41.0, 97.3+EPS) hanging from the band; webs B(-23.5, -19.5,
  -27.6, -22.8, 44.5, 48.5) and (..., 75.0, 79.0) to the stack fin. Gap to the cover -Y face 0.8.

### 6.6 Panel (`printed_panel.py`)
- Keeper finger from `CAM['keeper']` (x -30.67..-27.34); gusset follows. No other change.

### 6.7 Registries (`layout.py`)
- **New `COLLAR` dict:** feet {TL (11, 90.5), TR (-11, 90.5), LL (24.5, 36.0), LR (-19.0, 44.0)}, foot_d 7.6, hole_d
  3.4, hood_hole_d 8.6, flange_x (0.3, 2.8), body_r 30, bore_clear 0.3, cone 45, lug dict (s.6.3), insert dims.
- **SCREWS** (new block; add `kind` to every entry, existing = 'PT'):

| id | kind/len | joins / into / head_part | axis | head_point | tip | engage | step |
|---|---|---|---|---|---|---|---|
| s_c1 | M3 x 10 + washer | lens_collar, tub / tub insert TL / lens_collar | (-1,0,0) | (3.3, 11.0, 90.5) | (-6.7, 11.0, 90.5) | [4.0] | 8 |
| s_c2 | M3 x 10 + washer | same, TR | (-1,0,0) | (3.3, -11.0, 90.5) | (-6.7, -11.0, 90.5) | [4.0] | 8 |
| s_c3 | M3 x 10 + washer | same, LL | (-1,0,0) | (3.3, 24.5, 36.0) | (-6.7, 24.5, 36.0) | [4.0] | 8 |
| s_c4 | M3 x 16 + washer | lens_collar / collar lug insert / lens_collar | (0,0,-1) | (4.8, -33.5, 66.5) | (4.8, -33.5, 50.5) | 5.2 | 9 |

  `cbore` for s_c1..3: part lens_collar, d 7.5, **x range (2.8, 8.6)** (extend the cbore schema to x). Recount
  `COTS['pt_screws']` (lines 980, 1252) over kind PT only; new COTS `m3_hw` (3 short inserts, 1 M3 x 5.7 insert, 3 M3 x
  10, 1 M3 x 16 ISO 7045 PH1 A2, 4 ISO 7089 washers, ~4.5 g, step 8). Torques: s_c1..3 0.25 N m, s_c4 0.2 N m.
- **STEPS:** 7 adds [gs_camera, c_cs_adapter] (text: adapter already on, tripod block off, back focus set at B0; push
  +X 11.1 until the adapter has passed the lip; the camera rests in its cage). 8 adds += [lens_collar, s_c1, s_c2, s_c3]
  (text: collar feet through the 4 hood holes onto the tub; s_c1..s_c3 with washers from the front, 0.25 N m). 9 adds:
  remove c_cs_adapter, add s_c4; text: back s_c4 off; pass the lens through the collar and screw it into the adapter
  (the camera turns until its cover meets the hood fin); turn lens and camera back about 1 deg so the cover leaves the
  fin; set iris and focus, tighten the thumb screws; push the lens gently rearward until the knurl seats on the collar cone; tighten s_c4 0.2 N m. Delete "clock the Kowa lock screws
  to the right". 10 text += level check on live view: if needed loosen s_c4 half a turn, turn lens and camera
  together (window +-1.4 deg: the single fin spans both cover corners, 0.8 gap = +-2.3 deg, keep >= 0.3), re-seat on
  the cone, re-tighten.
- **INSERTIONS:** camera_in moving += c_cs_adapter (path unchanged); new collar_on (step 8, [lens_collar],
  [(30, 0, 0), (0, 0, 0)]); new lens_in (step 9, [lens], [(40, 0, 0), (0, 0, 0)]).
- **REMOVALS / LATCH_FREE:** new collar_off (reverse collar_on, unscrew s_c1..s_c3, off [lens]); hood_off and every
  service path that takes the hood off: off += lens_collar, unscrew += s_c1..s_c3; camera_out moving [gs_camera,
  c_cs_adapter], off = panel set + lens (the collar may stay). LATCH_FREE lens: loosen s_c4 one turn, unscrew by hand;
  c_cs_adapter: rides with the camera (camera_out).
- **MATES:** (tub, gs_camera) contact -> **clearance**; add (panel, gs_camera, clearance), (tub, lens_collar, contact),
  (hood, lens_collar, clearance), (lens, lens_collar, contact), (tub, c_cs_adapter, clearance), (hood, c_cs_adapter,
  clearance); keep the two thread mates.
- **LOAD_BEARING_PARTS** += lens_collar. **PARTS[lens_collar]** per s.6.3.
- **CRITICAL_FEATURES:** delete tub_cam_pin_0/1; add tub_lip (land 1.2), tub_insert_boss_tl/tr/ll (boss 1.6, wall round
  the insert), collar_foot_* (pin 1.6), collar_lug_upper/lower (lug 1.6), collar_wall_min (wall 1.2),
  hood_foot_hole_* ring (land 1.2), hood_cam_roll_fin (wing 1.6). Move the tub_front_wall_seat probe to the TL boss
  root (-3.95, 11, 86).
- **CRITICAL_JOINTS J7:** parts [tub, panel, hood, lens_collar]; required = the features above + panel_cam_keeper +
  tub_rib_l_tip + the new j7_float check.
- **KEEPOUTS:** ko_lens_thumb (s.6.2); ko_fpc_cam (s.6.1). **SECTIONS:** section-j7-y0 (cut y 0, x -30..12, z
  30..100) and section-j7-z90 (cut z 90.5).
- **self_check** (replace the 2 turret rows): lip_d/2 - adapter_d/2 >= 0.75; cb_d/2 - bfar_d/2 >= 0.7; lip_gap >= 0.4;
  0.4 + s_min >= 0.3; keeper x1 <= cover_rear(s_max) - 0.5; collar front <= first moving segment - 2.0 for every lens
  with a support; insert-boss x0 >= -7.6; |head_point - tip| = 12 for PT and = length for M3; hood hole top <= 95.3.

### 6.8 `cots.py`
- `gs_camera`: build from CAM at s (default s_nom): body = housing cylinder + tab + lock-screw envelopes (both sides)
  + PCB (4 dia 2.5 holes on the 30 square) + cover (FPC socket recess); BFAR head tube r 18 / 12.7. Export
  `gs_camera_parts(L, s) -> {body, bfar}` for the float check. COTS box = union over s 0..3: B(-26.84, -4.4, -19.75,
  19.75, 40.25, 82.1), widened in y for the lock screw.
- `c_cs_adapter`: tube r 15.375 / 12.7, x -4.4..+0.6; mass 4.0.
- `lens_proxy`: corrected segments; drop the lock-screw cylinders. COTS lens box from the segments.

### 6.9 `checks.py`, `build_d2.py`, tables, BOM
- **New `check_j7_float`** (J7 required): for s in (0, s_nom, s_max) build body/BFAR at s (adapter and lens fixed);
  against every printed part and COTS of the final state except the camera's FPC end, the adapter and the lens:
  body >= 0.5 lateral and >= 0.4 axial; BFAR >= 0.4 axial (lip) and >= 0.6 radial (counterbore); adapter >= 0.6
  radial; the lens overlaps nothing but lens_collar. Store per-s minima in checks.json.
- **New `check_lens_support`:** every LENSES entry with mass > 150 g has `support` (FAIL if missing; WARN unless status
  is measured); band inside the bore; seat x = C_FLANGE_X + x0; bore - d in 0.2..0.4; collar vs ko_lens_thumb 0 mm3.
- **New `check_lens_clamp`** from a `LOAD_MODEL` dict (pinch 120 N relaxed x 0.5 derate, M_sep = (pi/6) F L; anchors
  100 N relaxed; wall 0.079..0.146 deg/N m from design 3's FE): FAIL if M_sep < 1.5 x the static moment about the band
  centre; WARN if below the 5 g moment or if the 5 g aim exceeds 0.3 deg; FAIL if the lens axis is not inside the anchor
  polygon.
- `check_bosses` filters kind PT; new `check_inserts` (kind M3: bore dia 4.0 +-0.1, depth >= insert + 0.2, wall >= 1.6,
  tip inside insert or extension). `clearance_zones`: replace the 2 ring zones by BFAR-in-counterbore (stated 0.5),
  adapter-in-lip (0.825), adapter-in-plate-bore (2.875). `mass_com`: WARN outside 0..+8. thin_wall `loaded_boxes` +=
  insert bosses and collar lugs.
- `build_d2.py`: EXPLODE lens_collar (+40, 0, 0); the 2 sections; mass_com builds the collar of each lens.
- `make_tables.py`: `estimate_volume('lens_collar')`; prints +1; screws table gets a kind column; the "n PT screws"
  lint counts PT only. `make_bom.py`: m3_hw lines; INCLUDED_IN gs_camera "tripod block + 2 screws (removed at B0)";
  PT_USED filters PT.

### 6.10 Tests
- `test_tub.py`: lip and counterbore radii/x; no pins; insert bosses 0 mm3 vs pi_in, hood_on, camera_in; insert bore
  depth and wall.
- `test_hood_panel.py`: no turret, hood x1 <= 1.0; 4 hole rings >= 1.2; fin-to-cover >= 0.6 and keeper-to-cover >= 0.5
  at s 0 and s_max; replace the ring/cs_ring cylinders (lines 80-84) by BFAR/adapter/lens (0 mm3 vs hood).
- New `test_collar.py`: one valid solid in its envelope; print pose (no downward face steeper than 45 deg except the
  bed); feet coplanar; cone and bore per lens; driver audit pass for s_c1..s_c4; sweeps collar_on, lens_in; removal
  collar_off.
- `test_r3_regressions.py`: check_j7_float FAILs with lip_gap 0 and with a keeper gap of 0.2 at s_max;
  check_lens_support FAILs for a 300 g lens without support; the pt_screws count ignores M3 entries.

### 6.11 Docs
SPEC (J7 contract: the lens collar holds the lens at its fixed band and sets its axial position; camera body, BFAR and
adapter touch no chassis part; lip and keeper are catches; the hood fin limits roll while fitting; real camera stack;
turret rows out; new part), DESIGN (J7, parts, mass/CoM: Kowa about +1.4, Fujinon about -11 WARN), ASSEMBLY (B0 bench,
inserts before step 3, steps 7-10, lens swap, camera and hood removal order), FASTENER-POLICY (new s I: M3 inserts +
ISO 7045 PH1, torques; reasons: the Pi drop leaves 2.4 mm behind the wall, the collar cycles at every lens swap; G audit
list += s_c1..s_c4; PT count unchanged), PRINT-GUIDE (collar row; hood without turret supports; tub insert bosses),
MEASURED-PARTS (gates below), LENS-ZOOM-CANDIDATES "Load path" (premise corrected; adopted fix; a zoom needs a fixed
band >= 15 mm), HANDOFF, NOTES.

## 7. Bench gates (text for MEASURED-PARTS.md)
- **G-CAM-1 / MP-CAM (before CAD freeze):** calipers on the real GS: BFAR head OD and thickness; exposed BFAR face
  annulus outside the adapter (>= 0.8 radial for the lip catch); adapter OD and face-to-face (5.00 +-0.05); housing OD;
  tab width, top radius, depth, lock-screw head side and size; the tripod block comes off with its 2 screws and leaves
  nothing below r 18; PCB and cover size and centring (+-0.2); s at Kowa infinity and the total travel. Pass: all
  inside the CAM values, or CAM updated and rebuilt.
- **G-LENS / MP-LENS (before printing a collar):** mark the Kowa knurl; turn focus and iris end to end: the knurl must
  not rotate, and a dial indicator on its rear face must read <= 0.02 axial. Record knurl OD (+-0.02), rear-face
  position from the flange (+-0.05) and its edge chamfer, the thumb-screw envelope, the CoM (knife edge), and that the
  6.7 rear protrusion clears the camera filter at s. Same for any zoom (fixed band >= 15 mm). FAIL: no collar for that
  lens; fallback = a collar on the locked focus ring (refocus by unpinching).
- **G-COL-1 (coupon):** collar + tub-front coupon with 3 inserts + hood-plate coupon. Feet pass the holes with >= 0.3;
  the band slides in with s_c4 loose; at 0.2 N m no slip at 1.0 N m roll or 50 N axial; 3x lens mass at the CoM:
  lens-front dial <= 0.02 and returns; repeat after 24 h at 50 C (re-torque check; no lug crack after 20 cycles).
- **G-CAM-2 (sag acceptance, assembled camera):** live view, f/1.8, slanted-edge or Siemens chart at about 1 m. Record
  best focus (or MTF50) at the centre and 4 corners. Then (a) 3x lens mass hung at the lens front for 10 min; (b) 15 N
  side push at the focus ring; (c) 50 g hung on the camera cover; (d) 1 h at 50 C with (a). Pass: the corner-vs-centre
  focus asymmetry changes by <= 1/3 of the depth of focus (about 4 um, about 0.1 deg) in every case; aim shift recorded
  (target <= 0.3 deg under (a)). Repeat once with the BFAR lock screw loose to prove the camera carries no lens load.
- **G-W11 (existing):** camera-zone air temperature; above 50 C, print the collar in PC.
