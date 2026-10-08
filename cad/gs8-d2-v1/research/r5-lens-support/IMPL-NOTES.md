# r5 implementation notes (shared log)

Shared log for the r5 implementation agents (J7-R float, [R5-BRIEF.md](../../R5-BRIEF.md)). Each step APPENDS its own
section; never rewrite another step's section. Frame and units as `layout.py` (mm, assembly frame, lens axis y 0, z 60).

## r5 step 1 (geometry), 2026-10-06

Scope: layout, cots, tub / hood / panel / new collar geometry, probes, owner tests. Not touched: build outputs in `out/`
(only a scratch fast build in `out/_r5s1`), docs, BOM, the stills fork, candidate-fr1, the airflow study, WIRING.

### 1. What changed (files, names, APIs)

**`layout.py`**
- **`CAM` rebuilt** (real GS stack, judge 3 s6.1). Keys: `lip_x` -3.9, `lip_d` 32.4, `lip_gap` 0.5, `cb_d` 37.5,
  `cb_x` (-5.3, -3.9), `adapter` {d 30.75, ff 5.0, d_in 25.5, mass 4.0}, `bfar` {d 36.0, t 1.2, d_in 25.5,
  thread_d 28.8}, `s_nom` 1.25, `s_range` (0, 3.0), `housing` {d 35.5, depth 10.35, throat_d 25.5, throat_depth 3.0},
  `tab` {w 10.16, depth 5.02, top_r 22.1, slot 0.8, screw_dx 2.5, screw_z 79.4, head_d 4.0, head_h 2.0} (head envelope
  on BOTH sides), `pcb` {sq 38, t 1.4}, `cover` {sq 39.5, t 6.49}, `holes` (30 square) + `hole_d` 2.5, `fpc_socket`,
  `tripod_block` {removed: True, ...}, `insert` (path text), `status` (per value: 'drawing' / 'unconfirmed' /
  'estimate' for MP-CAM), derived `bfar_head` and `adapter_cyl` (CYL), `keeper` B(-30.67, -27.34, 4.0, 32.2, 66, 76).
- **Deleted CAM keys** (KeyError on purpose): `seat_x`, `lands`, `depth`, `rear_x`, `ring`, `cs_ring`, `c_adapter`,
  `pins`, `pin_d`, `pin_len`, `pin_tip_chamfer`, `wall_bore_d`.
- **Datum chain**: `BFAR_FACE_X` = `CS_FLANGE_X` = -4.4; `C_FLANGE_X` = +0.6 (r4 +10.6); `S_MAX` 3.0; functions
  `cam_hf_x(s)` (housing front, -5.6 - s) and `cam_cover_rear(s)` (-23.84 / -25.09 / -26.84 at 0 / nom / max).
- **New dicts**: `COLLAR` (feet TL (11, 90.5), TR (-11, 90.5), LL **(28.0, 36.0)**, LR (-19, 44); bolted TL/TR/LL,
  LR compression; foot_d 7.6, hole_d 3.4, hood_hole_d 8.6, foot_x (-2.7, 0.3), flange_x (0.3, 2.8), body_r 30,
  **ear_r 5.0**, cbore_d 7.5, bore_clear 0.3, cone 45 deg, cone_drop 2.0, front_gap_min 2.0, band_end_margin 0.4, slit
  2.0 on -Y, `lug` {x (1.0, front), y_out -35.0, upper_z (61, 66), lower_z (50, 59), screw_y **-31.3**, screw_x 4.8,
  bit_relief_y -27.8}); `M3` (ISO 7045 PH1 spec, head 5.6 x 2.4, clear 3.4, cbore 7.5, engage_min 3.0, washer ISO 7089
  3.2 x 7.0 x 0.5, insert L 4.0 bore 4.0 flush 0.1, insert_lug L 5.7, masses, torques s_c1..3 0.25 / s_c4 0.2 N m);
  `TUB_INSERT_BOSSES` {TL, TR, LL: c, od 8.0, x (-7.6, -5.2), bore_x (-2.7, -6.9), clear_x (-6.9, -7.6), chin_y (LL
  24.0)}; `LOAD_MODEL` (judge 3 s6.9 numbers for `check_lens_clamp`, step 2).
- **New functions**: `pt_screw_ids()`, `lens_spec(name)` (now also `id`, `moving_abs`, `first_moving_x`,
  `support_abs`; reads `LENSES_DATA_ONLY` too; `segments_abs` stays a 4-tuple list), `lens_thumb_keepouts(name)`,
  `collar_spec(name)` (seat_x/r, bore_r, cone_x0/r0, cone_x1, rear_x, front_x, band, band_d, status, first_moving_x,
  rear_step_r; None without a support), `screw_mass(s)`.
- **`LENSES`**: segments are now 5-tuples (r, x0, x1 from the flange, label, moves False/'rot'/'trans'/'trans?'),
  contiguous. Kowa per judge 3 s6.2 (focus rear 10.6..22.4, iris 30.9..36.6, knurl 2.2..7.6 fixed), `thumb_screws`
  (14.4 focus, 33.0 iris; r_max 24, w 3.8) replace `lock_screws` (deleted), `support` {d 42, x0 2.2, x1 7.6,
  edge_chamfer 0.3, status 'drawing'}. Fujinon: rear step r 17.0 (0..2.0) + band r 19.5 (2.0..7.8) + fixed barrel
  (7.8..10.0) + rings (10.0..51.0), support {d 39, 2.0..7.8, 'assumed'}, no thumb screws (unconfirmed).
  **`LENSES_DATA_ONLY`** = {computar_h6z0812} (305 g, CoM 40 guessed, support d 48.5 x 1.0..25.5 'drawing', 3 thumb
  screws, segments from dossier_external s7.2; `data_only` True).
- `HOOD`: `turret`, `turret_b` deleted; new `bore_d` 36.5, `bore_x` (-2.8, +0.3), `foot_holes` {d 8.6, ring_min 1.2},
  `roll_fin` B(-23.5, -19.5, -22.8, -20.55, 41.0, 97.8), `roll_webs` (2 boxes to the stack fin). `HOOD_BOX` x1 8.5 -> 1.0.
- `SCREWS`: every entry has `kind` ('PT' for the 7 existing). New kind 'M3' rows `s_c1`..`s_c3` (M3 x 10 + washer,
  axis -X, head_point (3.3, y, z), tip (-6.7, y, z), engage 3.9, step 7, cbore {part lens_collar, d 7.5, x (2.8, 8.6)},
  `insert` {part tub, x (-2.8, -6.8)}, `spec`, `length`, `washer`, `torque_Nm`) and `s_c4` (M3 x 16 + washer, axis -Z,
  head_point (4.8, -31.3, 66.5), tip z 50.5, engage 5.3, step 8, cbore d 0.0 (spot face, see TODO), insert in the
  collar z 50.1..55.8). `COTS['pt_screws']` recounted over kind PT (7, unchanged); new `COTS['m3_hw']` (box None, 4.84 g
  carried by the s_c rows).
- `COTS`: `gs_camera` box B(-26.84, -4.4, -19.75, 19.75, 40.25, 82.1) (union over s), features changed; `c_cs_adapter`
  step 9 -> **7**, mass 6 -> 4.0, box from CAM; `lens` step 9 -> **8**, box = union of the built LENSES
  B(-6.1, 57.2, -27, 27, 33, 87).
- `KEEPOUTS`: `ko_fpc_cam` re-derived B(-32.07, -24.04, -8, 8, 39.4, 47.0); new `ko_lens_thumb_focus`
  B(13.1, 16.9, +-24) and `ko_lens_thumb_iris` B(31.7, 35.5, +-24) (default lens at import; a `--lens` run keeps them).
- `PARTS['lens_collar']` (module printed_collar.py, ASA, black, face_down +X, owner tub, infill small, envelope
  B(-2.7, 8.6, -35.0, 33.0, 30.0, 95.5) computed from COLLAR); `OWNERS['tub']` += printed_collar.py; hood `supports`
  text (turret support gone). `LOAD_BEARING_PARTS` += lens_collar.
- `MATES`: tub/gs_camera contact -> **clearance**; added panel/gs_camera clearance, tub/lens_collar contact,
  hood/lens_collar clearance, lens/lens_collar contact, tub/c_cs_adapter, hood/c_cs_adapter, lens_collar/c_cs_adapter,
  tub/lens, hood/lens, panel/lens (all clearance). The last 4 exist because the COTS *boxes* of the adapter and lens
  (lens thread to C - 6.7) now overlap those parts' boxes; clearance mates are still checked on the solids by
  `check_mate_overlap` (<= 0.05 mm3), the same threshold as `check_interference`, so nothing is weakened.
- `STEPS` 7 / 8 / 9 / 10 (adds and text, see s4 decision 4); `INSERTIONS`: camera_in moving += c_cs_adapter; new
  `collar_on` (step 7, +X 30) and `lens_in` (step 8, +X 40, listed before panel_on).
- `REMOVALS`: camera_out moving [gs_camera, c_cs_adapter], off = panel set + lens; new `collar_off` (reverse of
  collar_on, unscrew s_c1..s_c3, off lens + s_c4); every removal whose `off` has 'hood' (keeper_out, pi_out) and
  hood_off get off += lens_collar, s_c1..s_c4. `LATCH_FREE`: lens / c_cs_adapter texts, lens_collar 'see collar_off'.
- `CRITICAL_FEATURES`: tub_cam_pin_0/1 deleted; replaced tub_front_wall_seat (now at the TL boss root (-3.95, 11, 86))
  and panel_cam_keeper (x -29.0); new tub_lip, tub_insert_boss_tl/tr/ll, collar_foot_tl/tr/ll/lr, collar_lug_upper/
  lower, collar_wall_min, hood_foot_hole_tl/tr/ll/lr, hood_cam_roll_fin (+ FEATURE_CLASS_RULES). `CRITICAL_JOINTS
  J7_camera`: parts [tub, panel, hood, lens_collar], required = those 19 ids.
- `SECTIONS` += j7-y0 (y 0, x -30..12, z 30..100) and j7-z90 (z 90.5).
- `self_check`: PT rows per kind; M3 rows (engage >= 3.0, length = entry length, tip inside the insert); the 2 turret
  rows replaced by 25 r5 rows (see s3). Result: 183 layout checks, 0 failed.

**`cots.py`**: new `gs_camera_parts(L, s=None) -> {body, bfar, s, hf_x, cover_rear_x}` (body = housing with a front
throat + split tab + lock-screw heads both sides + PCB with 4 holes + cover with the FPC recess; bfar = head tube +
exposed fine thread for s > 0); `gs_camera` = fuse at s_nom; `c_cs_adapter` from `CAM['adapter_cyl']` (bore 25.5);
`lens_proxy` = corrected segments, support band rear edge chamfered 0.3 x 45 deg (seats on the cone), no lock-screw
solids; `screw(L, s)` kind-aware (M3: shank + head 5.6 x 2.4 + washer + insert tube, one solid per row);
`build_one` note for box-None rows (pt_screws / m3_hw); `build_all` masses: PT rows pt_screws mass / n PT (0.8 as r4),
M3 rows `L.screw_mass` (1.09 g s_c1..3, 1.57 g s_c4).

**`printed_tub.py`**: `_front` cuts the lip (dia 32.4, x -5.3..-2.5) and BFAR counterbore (dia 37.5, x -5.3..-3.9)
teardrops (up +Y) instead of the dia 36.5 bore; the 2 pins are gone; new `_insert_boss(L, b) -> (boss, [cuts])` (OD 8
teardrop prism apex -Y, x -7.6..-5.2; LL chin flat at y 24.0; insert bore 4.0 from the outer face to x -6.9,
clearance 3.4 to -7.6). PRINT notes (modifier count 7 -> 10: s_c1..s_c3 get 40 % modifiers through
`print_modifiers`, automatic).

**`printed_hood.py`**: `_turret`, `TURRET_R_FILLET`, `BORE_CHAMFER` deleted; `_bore_tool` = dia 36.5 + truncated
teardrop over x -2.8..+0.3 only; new `_collar_foot_holes` (4 x dia 8.6 teardrop apex -Z) and `_roll_fin` (fin + 2
webs); PRINT supports/notes (1 tree support, footprint 171.2).

**`printed_panel.py`**: comment only (the keeper already reads `CAM['keeper']`, now x -30.67..-27.34).

**`printed_collar.py` (new)**: `PRINT`, `NOTES`, `build_part(layout, 'lens_collar', lens=None)` (any lens with a
support; default `L.LENS`), `build(layout)`. Body r 30 x 0.3..front, ears r 5.0 hulled (exact tangent webs), 4 feet,
revolved bore/cone, -Y slit, external lugs, s_c4 clearance + insert bore, bit relief, 0.6 bed chamfer on the outer wire
of the +X face only. Kowa 15.88 cm3 / 17.0 g; Fujinon 17.35 cm3 / 18.6 g.

**Minimum changes outside step 1 ownership (for step 2, owner checks/build/tables)**:
- `checks.py` `clearance_zones` (crashed on CAM `wall_bore_d`/`ring`, HOOD `turret_b`): the 2 "camera ring in tub/hood
  bore" zones replaced by the real-model ones of judge 3 s6.9: "J7 BFAR in tub counterbore" (gs_camera/tub, stated
  0.5 = lip gap), "J7 adapter in tub lip" (c_cs_adapter/tub, 0.825), "J7 adapter in hood plate bore"
  (c_cs_adapter/hood, 2.875). **RECTIFICATION r5 item.**
- `make_tables.py` `estimate_volume('hood')`: turret term = 0.0 (KeyError otherwise). No `lens_collar` branch yet.
- `test_common.py`: the cyl_solid(tube) smoke test uses `CAM['bfar_head']` instead of `HOOD['turret']`.
- `sweep_tub.py`: camera set = `cots.gs_camera_parts(L)` body + bfar + adapter (was CAM box + ring cylinders).

### 2. Numbers used and why
- Datum chain exactly judge 3 s6.1 (lip -3.9, gap 0.5, BFAR face -4.4, C +0.6, housing front -5.6 - s, tab gap 0.4 + s,
  cover rear -23.84 / -25.09 / -26.84, keeper x1 = -26.84 - 0.5). Kowa CoM now x 28.9 (r4 38.9).
- **LL anchor (24.5, 36) -> (28.0, 36)** (brief choice 4: "if LL cannot clear, move it"). At y 24.5 an OD 8 boss
  overlaps the pi5 COTS box (y <= 23.7, z <= 36.1) for any teardrop or round profile; raising it above z 40.1 runs
  into the panel front locate rib (x -6.55..-5.35, y 24..32.2, z >= 41.3). y 28.0 (boss y 24.0..32.0, inside rib_l)
  leaves 0.3 to the pi5 box. Anchor polygon TL-TR-LR-LL: signed edge distances 30.5 / 16.0 / 18.96 / 19.6 (rule >= 10;
  the axis is inside). Note: the 3 bolted points alone (TL-TR-LL) never enclose the axis (also with judge 3's LL); LR
  (compression) closes the polygon.
- **Collar ear r 4.4 -> 5.0**: judge 3's r 4.4 round a dia 7.5 counterbore left a 0.65 wall (MIN_WALL 1.2); 5.0 gives
  1.25. Envelope y1 33.0, z1 95.5.
- **Pinch inside |y| <= 35** (brief choice 5; judge 3 had lugs to y -38 and the screw at y -33.5): screw axis y -31.3
  so the lower-lug insert wall outboard is 1.7 (lug 1.6) and the upper-lug hole wall 2.0; washer dia 7 spans y
  -34.8..-27.8. The dia 6.5 audit bit (edge y -28.05) would clip the body disc between z 69 and 70.4, so the body above
  the upper lug is trimmed to y >= -27.8 (bit gap 0.25, measured). Insert L 5.7 at z 50.1..55.8 (bore 4.0 z 50..56,
  insert + 0.2), clearance 3.4 above; engage 5.3.
- Tub inserts: L 4.0 (judge 3: 3.0-4.0 procure), flush 0.1 -> x -2.8..-6.8, bore depth 4.2 (insert + 0.2), engage 3.9
  (judge [4.0]). Boss wall 2.0 everywhere (measured 2.01).
- Collar per lens (`collar_spec`): Kowa seat x 2.8 r 20.7, cone (0.8, 18.7) -> (3.25, 21.15), bore r 21.15, front 8.6
  (band front 8.2 + 0.4; focus ring at 11.2 - 2.0 = 9.2 allows it). Fujinon seat x 2.6 r 19.2, cone (0.7, 17.3) ->
  (3.05, 19.65), front 8.6. Cone drop = min(2.0, seat_r - (rear step r + 0.3)).
- Housing throat r 12.75 x 3.0 (unconfirmed): the Kowa rear protrusion (C - 6.7 = x -6.1) is 0.5 inside the housing
  front at s 0; the real filter clearance is G-LENS. Adapter and BFAR bores 25.5.
- s_c1..s_c3 head bearing x 3.3 (washer seat 2.8 + 0.5), M3 x 10 -> tip -6.7.

### 3. Checks whose premise was the wrong camera model (for RECTIFICATION r5)
1. `layout.self_check` 'turret bore clears ring' and 'lens clears turret front' -> r5 rows: lip - adapter 0.825
   (>= 0.75), counterbore - BFAR 0.75 (>= 0.7), lip gap 0.5 (>= 0.4), tab gap 0.4 at s 0 (>= 0.3), keeper 0.5 behind
   the cover at s_max, plate bore - adapter 2.875 (>= 2.0); per lens: collar front <= first moving - 2.0, seat = C +
   x0, bore - band 0.3 (0.2..0.4), cone 0.3+ off the step, rear face ahead of the plate; insert bosses x0 >= -7.6 and
   wall >= 1.6; hood hole tops <= 95.3; axis >= 10 inside the anchor polygon; lugs and washer inside |y| <= 35.
2. `checks.clearance_zones` 2 ring zones -> 3 real-stack zones (s1).
3. J7 required probes: tub_cam_pin_0/1 (pins locate nothing) -> the collar / anchor / catch probes; the
   tub_front_wall_seat probe moved from the plain wall 30 below the axis to the TL boss root.
4. `test_hood_panel` ring / cs_ring / c_adapter cylinders vs hood -> BFAR + body at s 0/nom/max, adapter, both lenses.
5. MATES tub/gs_camera contact -> clearance (the camera no longer seats).

### 4. Decisions where the brief left room
1. Assembly order: **the brief's preferred order is kept** (no check broke). Step 7 = camera + adapter, then the
   collar + s_c1..s_c3 (panel off); step 8 = lens through the collar (finger on the cover through the open left
   side) + s_c4, then the panel + 4 screws; step 10 = level check on live view (loosen s_c4 half a turn). The collar
   screws must precede the lens: with the lens present the s_c1..s_c3 handle (dia 30 from x 45.8) hits the Kowa
   front barrel. s_c4 and s_b1/s_b2/s_r1/s_r2 audit clean with the lens present (test_collar).
2. Computar is a separate `LENSES_DATA_ONLY` dict (not in `LENSES`), so `--lens`, `lens_rows`/mass_com and the
   collar build never see it; `lens_spec` / `collar_spec` accept it.
3. Fujinon segment split (rear step r 17.0 so the band has a rear edge; fixed barrel to +10.0 so the band fits inside
   the collar) is ASSUMED, like its band (G-LENS).
4. Inserts are not separate COTS solids: each M3 SCREWS row's solid includes its washer and insert (exempt from
   interference with the parts it joins via the s_ prefix); `COTS['m3_hw']` is the BOM/mass row (box None).
5. Thumb-screw keep-outs are square boxes round the full sweep ring (conservative), 2 KEEPOUTS entries.
6. s_c4 has no counterbore (head + washer on the upper-lug top); its `cbore` row is a zero-depth spot face (d 0.0).

### 5. Probes and results (`probes/r5s1/p_geom.py` -> `p_geom.json`, 525 s)
- Insert bosses (TL, TR, LL standalone) vs `pi_in` sweep (real pi5/cooler/x1203/x1203_kit proxies, 2 mm steps +
  1.0/0.5): **0 mm3**; vs pi5/cooler/x1203/x1203_kit COTS boxes: **0 mm3** each (LL to the pi5 box 0.3, TL/TR 50.4);
  vs `hood_on` sweep **0 mm3** (final gap to the hood 2.4); vs `camera_in` sweep (body + bfar + adapter) at s 0 / 1.25 /
  3.0: **0 mm3** each.
- Hood foot-hole rings (point-in-solid rays at x -0.1 / -1.25 / -2.4): TL 2.35, TR 2.35, LL 1.85 (at the +Y plate edge
  fillet, x -0.1), LR 2.30 (toward the lens bore) - all >= 1.2.
- Collar (Kowa) vs ko_lens_thumb_focus / _iris: 0 mm3, gaps 4.5 / 23.1.
- Camera float, min gap / overlap (0 mm3 everywhere) at s 0 / 1.25 / 3.0: body-tub 0.40 / 1.65 / 3.40 (lock tab to the
  wall), body-hood 0.80 (roll fin) at every s, body-panel 3.50 / 2.25 / 0.50 (keeper), body-collar 4.39 / 5.30 / 6.76,
  body-pi5 13.8, body-cooler 9.75; BFAR-tub 0.50 (lip, axial; radial 0.75) and BFAR-hood 1.92 at every s.
- Adapter: tub 0.825 (lip), hood 2.875 (plate bore), collar 3.33 (Kowa) / 1.93 (Fujinon). Lens: collar 0.0 gap and 0
  mm3 (cone contact) for both lenses; Kowa to the hood 2.57, tub 3.33; lens vs camera (nominal s) 0 mm3.
- C flange stack: adapter x -4.4..+0.6, C - BFAR face = 5.0.

### 6. Tests (all through `run_locked.py`)
- `layout.py` self-check: 183 checks, 0 failed. `test_r3_regressions.py`: 31 of 31 pass. `test_common.py`: ALL OK.
- `test_tub.py` (r5 section, exit 1 on fail): PASS. Valid single solid, in envelope, no keep-out or non-mate COTS box
  overlap; lip r 16.2 and counterbore r 18.75 (7 rays each), lip land x -2.7..-3.91 (1.21), no pins, insert bores r
  2.0 / depth 4.2 / walls >= 2.01 / clearance r 1.7, the sweeps above 0 mm3. Tub 106229 mm3, 96.6 g.
- `test_hood_panel.py` (r5 rows, exit 1 on fail): PASS. Hood x max 1.0 (no turret), proxies vs hood 0 mm3 (adapter,
  both lenses, BFAR + body at 3 s), fin-to-cover 0.80 at every s, foot-hole rings 2.35 / 2.35 / 1.85 / 2.30;
  keeper-to-cover 3.50 / 2.25 / 0.50. Hood 56878 mm3, 51.7 g. Pre-existing, not r5: the hood stack-stop post
  (FIXER r2) sits inside the pi5 COTS *box* (219.1 mm3, box only; the real pi5 proxy is clear).
- `test_collar.py` (new): PASS (162 s). Both collars: valid, in envelope, beds, no keep-out / COTS box overlap, print
  pose downward faces only the 3 washer-seat bridges (106.3 mm2) and the s_c4 holes (38.3 mm2), feet x0 -2.7 dia 7.6,
  bore / seat / cone radii per collar_spec, lens contact 0.0 / 0 mm3, collar-hood 0.3, collar-tub contact 0 mm3;
  driver audit s_c1..s_c3 pass (bit gap 0.5 in the 7.5 counterbore), s_c4 pass (bit 0.25, handle 6.5 to the hood);
  sweeps camera_in, collar_on, lens_in, panel_on pass; removals camera_out, collar_off (+ service driver s_c1..s_c3)
  pass; all 19 J7 CRITICAL_FEATURES pass (tub_lip 1.2, insert bosses 2.0, collar feet 2.1 / 7.6, lugs 2.0 / 1.7,
  collar wall 8.85, hood rings 2.5 / 2.5 / 2.686 / 2.289, roll fin 2.25, keeper 3.33, front wall 2.5, rib_l tip 1.25).

### 7. TODO for step 2 (checks / build / tables / BOM / docs)
1. `checks.check_bosses`: filter kind PT (it now measures s_c1..s_c4 as PT bosses and FAILs: pilot 4.0 / 3.4);
   add `check_inserts` (kind M3: bore 4.0 +-0.1, depth >= insert + 0.2, wall >= 1.6, tip inside the insert; data in
   each row's `insert`). `check_driver` uses `L.PT['head_h']` for every kind (M3 head_h is also 2.4).
2. New checks per judge 3 s6.9 / brief choice 9: `check_j7_float` (use `cots.gs_camera_parts(L, s)` at s 0 / nom / max;
   numbers in s5 are the expected values), `check_lens_support` (iterate `LENSES` and `LENSES_DATA_ONLY`; use
   `collar_spec`; FAIL > 150 g without support, WARN unless 'measured'), `check_lens_clamp` (`LOAD_MODEL`; polygon
   order TL, TR, LR, LL), `mass_com` WARN outside 0..+8; add the float check to J7 `required` handling; thin_wall
   `loaded_boxes` += insert bosses and collar lugs; `test_r3_regressions` synthetic FAILs.
3. `build_d2.py`: EXPLODE lens_collar (+40, 0, 0) (defaults to 0 now); mass_com for the Fujinon uses the build's
   lens_collar (Kowa collar, +1.6 g) unless it builds `printed_collar.build_part(L, 'lens_collar', lens=n)` per lens;
   the 2 new SECTIONS render through the existing loop; `screws=len(L.SCREWS)` (1420) counts both kinds (11).
4. `make_tables.py`: `estimate_volume('lens_collar')` (KeyError without a manifest row); screws table needs a kind
   column and per-kind drive/torque (it prints PT torque for every row; s_c4 cbore prints 'dia 0'); `C['pt']` value
   (line 580) and the steps' "n x PT" line (424-426) must count kind PT only (`L.pt_screw_ids()`).
5. `electronics/gs8-d2-v1/make_bom.py`: a LINES row for `m3_hw` (3 + 1 inserts, 3 x M3 x 10, 1 x M3 x 16, 4 washers),
   INCLUDED_IN gs_camera "tripod block + 2 screws (removed at B0)". PT_USED already excludes the M3 rows (they carry a
   `spec` not starting with PT); prefer `kind`.
6. Docs per brief choice 14 (SPEC, DESIGN, ASSEMBLY B0 + steps 7-10, FASTENER-POLICY s I, PRINT-GUIDE collar row,
   MEASURED-PARTS MP-CAM / G-LENS / G-COL-1 / G-CAM-2 incl. every CAM['status'] value, RECTIFICATION r5 from s3 above,
   LENS-ZOOM-CANDIDATES load path, HANDOFF, NOTES, candidate-fr1 note).
7. Full release build (both lenses, sweep-step 1.0) and the r5 output list (tub, hood, panel, lens_collar STLs; tub
   modifiers 7 -> 10; renders). The scratch fast build of this step is in `out/_r5s1` (see s8).

### 8. Scratch fast build (checks.py / build_d2.py still run end to end)
`run_locked.py -- build_d2.py --fast --out cad/gs8-d2-v1/out/_r5s1` (671 s, exit 0; `out/` release files untouched;
delete `out/_r5s1` when step 2 builds). Every check passes except **boss_geometry 4 fail = s_c1..s_c4** (expected:
PT boss rules applied to M3 inserts, TODO 1). contract 12/12, cots_containment 20/20, interference 62/62,
mate_overlap 40/40, clearance 13/13 (the 3 new J7 zones measure 0.5 / 0.825 / 2.875), keepouts 97/97, driver 11/11,
sweeps 14/14, removals 12/12, service_driver 9/9, critical_features 124 pass + 10 info (as r4: 10 info of 119),
thin_wall 12/12, print_modifiers 18 (tub 7 -> 10), layout_self_check 183/183. mass_com: Kowa 895 g, CoM +1.5 ahead
of the grip axis (r4 +3.73; brief expects about +1.4); Fujinon 780 g, -9.9 (r4 -8.89; brief about -11).

## r5 step 2 (checks + build), 2026-10-06

Scope: `checks.py`, `build_d2.py`, `make_tables.py`, `electronics/gs8-d2-v1/make_bom.py`, `test_r3_regressions.py`, two
small `layout.py` edits (J7 `required_checks`; s_c4 `screw_x`). Not touched: docs, the release outputs in `out/` (the
fast builds went to `out/_r5s2` and `out/_fujinon-r5`; `out/_r5s1` deleted), BOM.md / bom.csv (generator changed, not
re-written: see s7), the stills fork, candidate-fr1, the airflow study, WIRING.

### 1. New and changed checks (`checks.py`, "r5 (J7-R) lens support" section at the end)
- **`check_j7_float(L, rows, s_values=None, parts_of=None)`** (J7 required). For s 0 / 1.25 / 3.0 the camera `body` and
  `bfar` (`cots.gs_camera_parts(L, s)`) and the C-CS adapter are measured against every row of the final state except
  the hanging unit (`J7_FLOAT_EXCLUDE` = gs_camera, c_cs_adapter, lens; the FPC has no solid), obstacles pre-cropped to
  the movers' box + 6 mm (`J7_REACH`). Per mover: overlap <= 0.05 mm3; **lateral** gap (obstacle material level with
  the mover, inside its x range) and **axial** gap (obstacle material in its y/z shadow, ahead or behind) against
  `J7_FLOAT_RULES` (judge 3 s6.9): body lateral 0.5 / axial 0.4, BFAR lateral (counterbore) 0.6 / axial (lip) 0.4,
  adapter lateral 0.6; the plain minimum must also reach the smaller rule (a diagonal gap cannot slip through). Tolerance
  1e-3 (OCP distance noise). Plus: the lens overlaps nothing but `lens_collar`, and the lens does not overlap the camera
  at any s. Rows carry per-obstacle gaps and the per-s minima (checks.json; receipt `j7_float_min`). 11 rows.
- **`check_lens_support(L, rows=None, collars=None, lens_shapes=None)`**, every `LENSES` + `LENSES_DATA_ONLY` entry:
  `support` (FAIL if mass > `LOAD_MODEL['support_mass_g']` 150 g without one), `band_fixed` (no moving segment over the
  band), `band_length` (clamped length = band from its seat to min(band end, collar front) >= `band_min` 5.0, a zoom
  >= `zoom_band_min` 15), `bore_clearance` 0.2..0.4 diametral, `collar_front` <= first moving - 2.0, `band_in_collar`
  (>= 0.2 behind the rear face; >= 0.2 inside the front unless the front sits at the moving-ring limit), `seat_x`
  (= C_FLANGE_X + x0, on the cone). Built collars (each lens's own) are measured: `lens_seated` (0 mm3, gap <= 0.01),
  `bore_measured` and `seat_measured` (exact B-rep rays, 13 directions, the -Y slit skipped; +-1e-3), `thumb_keepouts`
  (0 mm3 vs that lens's `ko_lens_thumb_*`; info when the lens lists none). `status` row: pass only if 'measured', else
  an info row with `warn` (the brief's WARN). 32 rows (Kowa 12, Fujinon 12, Computar 8).
- **`check_lens_clamp(L, rows=None, collars=None)`** from `LOAD_MODEL`: `anchor_polygon` (TL-TR-LR-LL hull; axis
  margin >= 10 or FAIL); per lens with a support: F = 120 x 0.5 = 60 N, M_sep = (pi/6) F L (L = clamped length),
  M_static about the clamped band centre = g x sum(m |lever|) of lens + camera (COTS mass at the gs_camera solid's
  centroid) + adapter (conservative |lever| sum). FAIL if M_sep < 1.5 x M_static; WARN (info) if M_sep < the 5 g
  moment, if the 5 g aim at the tub face (|M_wall| x 0.146 deg/N m) > 0.3 deg, or if the 5 g top-anchor tension
  (|M_wall| / (z TL-TR 90.5 - lowest foot z 36)) > `anchor_N` 100 N. Collar mass and centroid from each lens's built
  collar. 4 rows.
- **`check_inserts(L, rows)`** (kind M3), exact rays on the solids: bore dia = `bore_d` +-0.1; bore open at exactly one
  end on 4 axis-parallel lines at r 1.85; depth from the boss face plane (the face crossing nearest the open side on
  lines at r 2.4) >= insert + 0.2, and per line >= insert + flush (an edge chamfer may recede the face locally); wall
  round the bore >= 1.6 over 5 levels x 12 directions; engagement >= `M3['engage_min']`; tip and tip + 0.2 in a void
  (no bottoming); washer seat at the head point - washer t (+-0.05); under the washer >= 1.6; head-part clearance hole
  r >= 1.7 - 0.025. 4 rows.
- **`check_joint_checks(L, R)`** + `layout.CRITICAL_JOINTS['J7_camera']['required_checks']` = j7_float, lens_support,
  lens_clamp, inserts (judge 3 s6.7 "+ the new j7_float check"): each needs rows, no fail / stub, >= 1 pass (a WARN row
  neither passes nor blocks). The row goes into `critical_features` (the release gate). J7 joint row and joint_check
  row: pass.
- **Kind handling:** `check_bosses` measures kind PT only (same 7 rows, same rules); `check_driver` takes the head
  height from the kind (M3 2.4 = PT 2.4); the driver audit, `screw_pierces` and `check_interference` already cover
  every kind (s_c1..s_c4 audit clean). `loaded_boxes`: tub += the 3 insert bosses; lens_collar = 4 feet + the pinch-lug
  block (thin_wall still 12/12).
- **`mass_com`: function and reporting unchanged** (brief choice 10). The build now passes each lens's own collar
  (Fujinon 18.6 g instead of the Kowa 17.0 g). Judge 3's "WARN outside 0..+8" is NOT added (brief: existing rules,
  unchanged); with it the Fujinon -9.8 would WARN. Docs step: say so in SPEC/DESIGN.
- `clearance_zones` (step 1's J7 zones) measure 0.5 / 0.825 / 2.875 against need 0.45 / 0.742 / 2.587: pass.

### 2. Replaced or re-scoped checks (RECTIFICATION r5, with step 1 s3)
1. `boss_geometry` measured every SCREWS row by PT rules (pilot 2.5, wall 2.25), so s_c1..s_c4 failed (premise:
   every body screw is a PT). Now kind PT only (the 7 PT rows are measured exactly as before) and kind M3 gets
   `check_inserts` with insert rules. Not a weakening.
2. `make_tables.counts()['pt']` counted all SCREWS (11) -> kind PT (7, unchanged value); `_pt_groups` (lint sub-groups)
   are PT only (step 7 / 8 groups no longer mix M3); new `m3` count (4: step 7 = 3, step 8 = 1) and an "M3 / collar
   screws" lint kind; an unqualified "<n> screws" may also equal the all-kinds total 11.
3. The lint selftest planted "12 printed parts" / "12 printed pieces" as wrong; 12 is now correct, so the plants are
   derived (count + 1, the same off-by-one). New plants: "5 M3 collar screws", "11 PT screws" (flagged); good: "4 M3
   screws", "the 3 collar screws", "11 screws in all" (pass). Selftest ok.

### 3. Geometry change (layout.py, owner step 1): s_c4 `COLLAR['lug']['screw_x']` 4.8 -> 4.7
`check_inserts` found 1.585 of wall (< 1.6 loaded) toward +X round the lug insert's bottom 0.3 mm: the collar's 0.6 bed
chamfer on the +X face outer wire runs along the lower lug's bottom edge. At x 4.7 the walls are 1.70 (-X) and 1.685
at the chamfer (+X, measured). test_collar re-run: PASS (driver s_c4 bit gap unchanged, it is in y; lugs 2.0 / 1.7).
s_c4 head point is now (4.7, -31.3, 66.5); step 1's s1/s2 texts say 4.8.

### 4. Build, tables, BOM, tests
- `build_d2.py`: `EXPLODE['lens_collar']` (+40, 0, 0) and `c_cs_adapter` 45 -> 58 (so it is not drawn inside the
  exploded collar); M3 screws explode with their head part (collar) then 30 back along the axis; new `lens_collars(rows)`
  (each built lens's collar via `printed_collar.build_part(L, 'lens_collar', lens=n)`); R['inserts'], R['j7_float'],
  R['lens_support'], R['lens_clamp']; joint-check rows appended to critical_features; summary order += inserts,
  j7_float, lens_support, lens_clamp (the last two info_neutral); `warnings` in those summaries, in the receipt
  (`warnings`) and in the log ("WARN ..."); receipt `totals.screws_by_kind` {M3 4, PT 7} and `j7_float_min`. The two
  r5 SECTIONS render through the existing loop (`renders/section-j7-y0.png`, `section-j7-z90.png`; y0 checked by eye:
  cone seat on the knurl, camera clear of lip / counterbore / keeper). Manifest / print pose / modifiers needed no
  code: lens_collar rides the PARTS registry; tub modifiers 7 -> 10 come from `print_modifiers` (collar infill 'small':
  none).
- `make_tables.py`: `estimate_volume('lens_collar')` (15.2 cm3; built 15.9); `name_of` and the new `_kind_of`;
  screws table gets a **Kind** column, per-kind drive and torque (s_c1..3 0.25, s_c4 0.2 N m), zero-depth counterbore
  prints the row's note; steps block lists PT and M3 fasteners and torques apart; counts / lint as s2.
- `make_bom.py`: PT_USED / PT_IDS from `pt_screw_ids()` (7, unchanged); new D2-35 (3 + 2 spare short inserts, ref
  `m3_hw`), D2-36 (1 lug insert L 5.7), D2-37 (3 + 1 M3 x 10), D2-38 (1 + 1 M3 x 16), D2-39 (4 + 2 ISO 7089 washers),
  counts from the kind M3 rows; D2-05 note + `INCLUDED_IN['tripod_block'] = 'D2-05'`. Dry run: 0 uncovered ids.
- `test_r3_regressions.py` +7 cases: j7_float real datums pass (BFAR axial 0.5 / radial 0.75, keeper 0.5 at s_max);
  FAIL at lip_gap 0 (BFAR only) and at a 0.2 keeper gap (body at s_max only); lens_support FAILs a 300 g lens without
  support and passes a 120 g one; lens_clamp FAILs with LR moved above the axis; PT count ignores M3 (layout, COTS,
  make_tables, check_bosses / check_inserts row sets); J7 joint fails on a j7_float fail, no insert rows, or WARN-only
  lens_clamp. Synthetic tub = lip ring + counterbore ring (from X_FW_IN) built from CAM, the real camera proxy.

### 5. Results (all through `run_locked.py`)
- `test_r3_regressions.py` **38 / 38** (31 + 7); `test_common.py` ALL OK; `test_collar.py` PASS (264 s, after s3);
  layout self-check 183 / 183; probes `probes/r5s2/p_checks.py`, `p_inserts.py` (+ `p_checks.json`).
- **Kowa --fast** (`out/_r5s2`, 459 s, exit 0): every category pass, `cad_release_candidate` True, blocking none, rows
  **732 pass / 0 fail / 17 info** (10 critical_features, 2 cable_routes, 4 lens_support, 1 lens_clamp). contract 12,
  cots_containment 20, interference 62, mate_overlap 40, clearance 13, keepouts 97, cable_routes 8 + 2 info, bed_fit 12,
  stl_mesh 12, print_modifiers 18, thin_wall 12, critical_features 125 + 10 info (135 incl. the J7 joint_check),
  evf_restraint 6, driver 11, engrave_groove 10, boss_geometry 7, **inserts 4**, **j7_float 11**, **lens_support 28 +
  4 info**, **lens_clamp 3 + 1 info**, sweeps 14, removals 12, service_driver 9, release_access 2, stack_retention 1,
  layout_self_check 183, mass_com pass.
- **Fujinon --fast** (`out/_fujinon-r5`, 509 s, exit 0): the same, rows **729 / 0 / 17** (interference 59 pairs).
- j7_float minima (both builds; gap / rule): body s 0: axial 0.40 (tab-wall, tub) / 0.4, lateral 0.80 (roll fin, hood)
  / 0.5; body s 1.25: axial 1.65, lateral 0.80; body s 3.0: axial 0.50 (keeper, panel), lateral 0.80; BFAR every s:
  axial 0.50 (lip), lateral 0.75 (counterbore) / 0.6; adapter lateral 0.825 (lip) / 0.6, axial 3.325 Kowa collar /
  1.925 Fujinon collar. Lens: 0 overlaps; lens vs camera 0 mm3 at every s.
- lens_clamp: polygon margin 16.01 (>= 10; the bolted triangle alone -8.80). Kowa M_sep 0.170 N m, static 0.057 (ratio
  2.97 >= 1.5), 5 g 0.286 -> **WARN**; M_wall 0.063 N m, aim 5 g 0.046 deg, top-anchor 5.8 N. Fujinon 0.182 / 0.028
  (6.55), 5 g 0.139 pass, aim 0.018 deg, 2.3 N. Computar (data only) 0.707 / 0.094 (7.55), pass, 11.7 N.
- inserts: s_c1 / s_c2 depth 4.2 (need 4.2), wall 2.0; s_c3 4.2 (locally 4.184 at the tub's +Y edge chamfer, need >=
  4.1), wall 1.706; s_c4 depth 6.0 (need 5.9), wall 1.685; engagement 3.9 / 5.3; tips in voids; under washer 5.5 / 5.0.
- **Balance** (each lens with its own collar; mass_com unchanged): Kowa **895 g, CoM +1.5** ahead of the grip axis
  (brief about +1.4; r4 +3.73), +34.9 above the grip top; Fujinon **782 g, -9.8** (brief about -11; r4 -8.89), +30.1.
- **Collar:** Kowa 15879 mm3, **17.0 g**; Fujinon 17352 mm3, **18.6 g** (ASA, infill 'small'). Printed total 297.2 g /
  16.0 h (Kowa build) against r4 292.9 g / 15.7 h.
- **STLs against the r4 release in `out/`** (sha256): CHANGED tub (lip + counterbore, 3 insert bosses, no pins; 96.4 ->
  96.6 g), hood (turret gone, 4 foot holes, roll fin; 64.6 -> 51.7 g), panel (keeper moved to x -30.67..-27.34; 46.5 g);
  NEW lens_collar (one per lens: the default build exports the Kowa collar, the Fujinon build its own) and modifiers
  `tub__mod_s_c1..3`; the other 15 modifier STLs and base_grip, cap, eyecup, knob_exp, knob_fps, pi_keeper, plunger,
  stick_sleeve are byte-identical. Coupons not rebuilt (no coupon geometry changed in r5 so far).

### 6. Open WARNs (listed, not blocking)
1. lens_support: support band not measured: Kowa 'drawing', Fujinon 'assumed', Computar 'drawing' (G-LENS).
2. lens_clamp Kowa: M_sep 0.170 N m < 5 g moment 0.286 N m (static ratio 2.97). A knock rocks the lens elastically in
   the collar (aim only). G-COL-1 sets the real pinch / relaxation; judge 1's PC / ASA-CF collar is the upgrade path.
3. lens_support Fujinon thumb_keepouts: info (no thumb screws listed, [unconfirmed]).

### 7. Decisions where the brief left room
1. Lateral vs axial is decided by where the obstacle material lies (a slab level with the mover / its y-z shadow
   ahead or behind), not by the closest-point direction; the plain minimum must still reach the smaller rule.
2. WARN = an 'info' row with a `warn` text; lens_support / lens_clamp are info_neutral categories (>= 1 pass, no fail)
   and their WARNs are listed in the summary, the receipt and the log. Data-only lenses are FAIL-able (no exemption).
3. Clamped length (band from its cone seat to min(band end, collar front)) is used for M_sep and band_length (Kowa 5.4
   = judge 1's L). M_static sums |lever| moments (conservative; the camera's tail-down moment is not subtracted).
4. Added WARN beyond the judges: 5 g top-anchor tension > relaxed anchor preload (LOAD_MODEL `anchor_N`).
5. `band_in_collar`: judge 1's 0.2 front margin unless the collar front is at its moving-ring limit (Computar: band runs
   2.0 past the front; the clamped-length rule governs, 22.5 >= 15).
6. Insert depth from the face plane, plus a per-line floor of insert + flush (s3 of check_inserts).
7. s_c4 moved 0.1 in x instead of dropping the bed chamfer on the lug edge (FDM rule) or recessing the insert.
8. Fast builds to scratch dirs: the Kowa build to `out/_r5s2` (not `out/`, so r4's release set stays whole until the
   full r5 release build), the Fujinon build to `out/_fujinon-r5` as asked.

### 8. TODO for the docs step (step 3)
1. Full release builds (Kowa to `out/`, both lenses, sweep 1.0; Fujinon sweep-1mm checks file), then
   `make_tables.py` (refresh) and `make_bom.py` (write) so the blocks and BOM.md / bom.csv use the r5 manifest.
   `make_tables.py --check` now reports stale WIRING, PRINT-GUIDE, ASSEMBLY, DESIGN (expected) and 15 handwritten count
   phrases at 11 printed parts / STLs: DESIGN 21, 354; HANDOFF 62, 74, 94, 105; OPTIONS 39; PRINT-GUIDE 3; RECTIFICATION
   16, 26, 36, 191, 300; SPEC 247 (history lines may need an "r4" qualifier rather than a new number). Delete
   `out/_r5s2` (and `out/_r5s2.log`) after the release build.
2. SPEC s6: the 4 new checks + joint checks, boss_geometry kind PT, WARN rows and `warnings`; mass_com unchanged (no
   0..+8 band; Fujinon -9.8). RECTIFICATION r5: step 1 s3 + this s2. FASTENER-POLICY s I: M3 torques, BOM lines
   D2-35..39, s_c4 at x 4.7. DESIGN: balance, collar masses, the STL change list above. MEASURED-PARTS: G-COL-1 sets
   `LOAD_MODEL` pinch_N / pinch_relax / anchor_N (the Kowa 5 g WARN), G-LENS the band status.

## r5 step 3 (docs + release), 2026-10-06

Scope: the docs of R5-BRIEF choice 14 / judge 3 s6.11 + s7, the HANDOFF s9 release sequence, and three small code
changes the release needed (below). Not touched: the stills fork, candidate-fr1 code (note only), the airflow study,
WIRING.md (its generated blocks were refreshed by `make_tables.py`; no hand edit), geometry.

### 1. Code changes (all logged here for RECTIFICATION r5 item 8)
- `make_coupons.py`: 3 G-COL-1 coupons (judge 3 s7: "collar + tub-front coupon with 3 inserts + hood-plate coupon"):
  `collar_tub_front` (tub cut x X_FW_IN-3.0..XT1+0.1, y -24..33, z 30..ZT1+0.1; 7.6 g), `collar_hood_plate` (hood cut
  x -2.6..1.1, same y, z 30..97; 6.6 g), `collar_part` (the whole default-lens collar, as `cap_retention_cap`; 17.0 g).
  23 + 4 coupon STLs (r4 20 + 4), 83 g at 100 % (r4 52 g).
- `build_d2.STATE_GATES`: `COL` added to the coupon_validation pattern (G-COL-1 binds its 3 coupon STLs); the
  measured_fit pattern `G-CAM-` narrowed to `G-CAM-1$`, so G-CAM-2 (assembled sag test) is an assembly_operation item
  bound to its doc + every production STL (stricter, not weaker).
- `electronics/gs8-d2-v1/make_bom.py` D2-74: the M3 heat-set tip is needed in every build (4 collar inserts); the
  drills stay fallback-only.

### 2. Docs
SPEC (r5 header note; s1 camera-stack datum row; s2 parts incl. lens_collar, COTS 22 rows, m3_hw, Computar data-only;
s3 J7-R row; screw stations with kind + s_c1..s_c4; s4 tub / hood / collar print rules; s5 steps 7-10 + the order rule
+ driver audit for M3; s6 J7 clearance zones, 5b PT-only, new 5h (j7_float, lens_support, lens_clamp, inserts), item 8
balance (no 0..+8 band), item 10 G-COL-1 / G-CAM-2 states; s7 keep-outs; s8 look; s9 history rows; s10 G-LENS
extended, G-CAM-1 rewritten as MP-CAM, G-COL-1, G-CAM-2, Plan B; s11 ownership). FASTENER-POLICY (intro, F lens +
tripod block rows, G scope / audit list / clearances, H records, new s I). MEASURED-PARTS (r5 status; MP-CAM rewritten
with every `CAM['status']` value and a lens line). DESIGN (header, s1 status table from the receipt, s2, s4.1, s5 J7
row, new s6f, s7 balance, s8 exports, s9 gates). ASSEMBLY (header, s1 rules incl. M3 torque and the lens rule, s1.1
tools 1 / 2 / 12, bench steps B0 + B1, s3 checks 7-10, s4, s6, s7 removal order, camera / lens / collar items 6a-6c,
hood item 9, lens swap). PRINT-GUIDE (head, s1 material / supports, s1.1 tub modifiers, s3 tub / hood / collar rows,
s4 inserts, s5 items 1 / 2 / 6, s6 G-COL-1 rows and counts, s7 order). HANDOFF (new s0 r5; old s0 -> s0b; s2, s5, s6,
s7 steps 3 / 7 / 8; commands unchanged). RECTIFICATION (new "r5" section R5-1..R5-5). LENS-ZOOM-CANDIDATES (r5
correction block in "Load path"; r4 text labelled). OPTIONS (totals line). NOTES (r5 log). candidate-fr1/NOTES (note).
History count phrases (11 printed / 24 coupon STLs) were reworded so the lint reads them as history, not changed.

### 3. Release sequence (all through `run_locked.py`, foreground; one background wait for the main build)
1. `make_coupons.py --out out` (16:03-16:06): 23 coupons; `coupons_r1.py --out out` (16:06): 4. vs r4: 23 identical,
   3 new, `hood_ledge_ret` changed in triangulation only (34 -> 36 facets, volume 526.004 and bounds identical: the TL
   insert boss's +Y edge lies on its cut plane y 15).
2. Fujinon `--lens fujinon_hf6xa --fast --sweep-step 1.0 --out out/_fujinon-r5` (16:07-16:16, 516 s; replaces step
   2's run in that folder): 27 / 27, rows 729 pass / 17 info / 0 fail; copied to `out/checks-fujinon-sweep1mm.json`
   (sha 83b55def...).
3. `make_tables.py` (WIRING, PRINT-GUIDE, ASSEMBLY, DESIGN refreshed) and `make_bom.py` (67 purchased lines, 12 printed
   parts, 0 uncovered) before the main build (SPEC, FASTENER-POLICY, MEASURED-PARTS written first: hashed).
4. Kowa release `build_d2.py --sweep-step 1.0` into `out/` (built 2026-10-06 16:32:38 +0800, 579.6 s, exit 0): 27 / 27
   categories, 749 rows = 732 pass + 17 info + 0 fail, 0 stubs, `cad_release_candidate` true, blocking none;
   checks.json c9d748c8...; receipt: 17 / 17 sources, 101 / 101 outputs, 4 / 4 gate docs match disk (re-verified after
   all doc edits); 55 gates (53 open, 2 withdrawn); states not run: slicer 12, coupons 10, measured 17, assembly 26.
   Every release STL and modifier is byte-identical to step 2's `out/_r5s2` fast build (30 of 30).
5. `make_tables.py` again (DESIGN checks block from the new receipt; WIRING unchanged, sha 3a42141b) and `make_bom.py`;
   `make_tables.py --check`: stale none, lint 0, selftest ok.
6. `test_r3_regressions.py`: 38 / 38.
r4 release outputs (STLs incl. coupons and modifiers, receipt, checks, manifests) copied to `out/_r4-2026-10-06/`
before the release build.

### 4. Decisions where the brief left room
1. **MP-LENS = the lens line of MP-CAM**, not an 11th `## MP-` record: WIRING.md (a gate doc I may not hand-edit)
   states "10 records", and the cooler line of MP-X1203 is the precedent. G-LENS stays the gate id.
2. **G-CAM-1 keeps its id** and is rewritten as the MP-CAM measurement list (judge 3 s7 "G-CAM-1 / MP-CAM").
3. **Bench steps B0 / B1** are hand-written in ASSEMBLY s2 before the generated block (not in `layout.STEPS`; the step
   count stays 10). B1 sets the 3 tub inserts before step 3 and the lug insert before step 7.
4. **Lens swap with the panel on** is documented (as `LATCH_FREE['lens']` allows): the camera rests in its cage (lip,
   keeper, roll fin), one hand carries the lens; a lens with another band needs the panel-off collar swap.
5. **Tripod-block drive** left unconfirmed (MP-CAM); if hex, it is a once-only bench exception (FASTENER-POLICY F).
6. Coupons for G-COL-1 were added (judge 3 names them) rather than leaving G-COL-1 a coupon gate with no STLs.

### 5. Open (user / next session)
- Bench first: MP-CAM (B0: tripod block, back focus s with the Kowa at infinity, every `CAM['status']` value), G-LENS
  (Kowa knurl fixed and measured; Fujinon band assumed), then G-COL-1 (sets `LOAD_MODEL` pinch / relaxation / anchor,
  decides the Kowa 5 g WARN), then G-CAM-2 on the assembled camera; G-W11 decides ASA or PC for the collar.
- 4 WARN rows stay listed (3 band status, 1 Kowa clamp at 5 g).
- `out/_r5s2` (+ `_r5s2.log`), step 2's scratch fast build, is still on disk (byte-identical STLs to the release);
  delete when convenient. Nothing committed.
