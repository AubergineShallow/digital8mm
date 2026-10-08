
### 6.2 Printed parts
- **`printed_tub.py`**
  - Replace the lens-bore teardrop with the counterbore and lip teardrops (`dc.teardrop`, up +Y).
  - Delete the pins.
  - Add the 3 nut blocks with their slots and crush ribs. LL merges into rib_l; check the `tub_rib_l_tip` probe.
  - The `_right`/`_floor` auto-cuts do not trigger (axis -X).
- **`printed_hood.py`**
  - Delete `_turret`, `TURRET_*`, its fillets and the "turret upper half" tree-support note; supports become the
    housing strip only.
  - Cut the bore tool x -2.8..+0.3.
  - Add the 4 holes (dia 9.0, teardrop toward -Z) and the roll fin with its webs, hanging from the band.
- **`printed_panel.py`:** keeper and gusset from `CAM_R['keeper']`.
- **`printed_collar.py`** (new; pattern `printed_keeper.py`; imports math, cadquery, d2_common only)
  - `PRINT = {'lens_collar': dict(face_down='+X', supports=[], notes=...)}`; `build(L)` uses `L.LENS`.
  - Geometry: flange, feet, cone, tube, slit, pinch boss and nut slot, ear gussets and dia 7.5 channels, the c4 head
    channel dia 7.0, and 0.6 bed chamfers on the +X face.
  - Must build for every LENSES entry that has a `support`.

### 6.3 cots.py
- `gs_camera` from the `CAM_R` sub-solids at `s_nom`. Tag them 'body' (housing, tab, pcb, cover) or 'lensside'
  (bfar), so the checks can split them.
- `c_cs_adapter` as above.
- `lens_proxy` from the corrected segments, with the thumb screws at one clock and the sweep kept as a keep-out.
- Add `nut_m3_square`, M3 pan screw and washer builders, and their BUILDERS entries.

### 6.4 checks.py
1. **`check_j7_float`.** At s_min, s_nom and s_max: camera 'body' sub-solids >= 0.2 from every printed part (tab to
   wall 0.6 + s, keeper 0.5, fin 0.6, nut blocks >= 2). 'lensside' to tub: radial >= 0.5, axial >= 0.05. Any
   contact FAILs.
2. **`check_lens_support`.**
   - Every LENSES entry has a `support`.
   - The band lies inside the tube with >= 0.2 each end.
   - Bore minus band = 0.2..0.4 diametral.
   - Tube front <= first rotating segment - 2.0.
   - The collar overlaps `ko_lens_thumb` by 0 mm3.
   - FAIL if a lens has no `support`; WARN if status != 'measured'.
3. **`check_clamp_capacity`.** F0 = T/(0.2 d) = 250 N at 0.15 N m; F = 0.25 F0 (relaxation x asymmetry);
   M = pi F L/6, which is 0.177 N m for the Kowa. Assert M >= 1.5 x the static moment about the band centre; WARN
   if M < the 5 g moment. Report it per lens.
4. **`check_mount_polygon`.** TL, TR, LL and LR enclose the axis in yz; the distance from the axis to every edge is
   >= 10.
5. **`load_path` report** from `LOAD_MODEL` (k_wall 500 N m/rad, range 300-800; creep x 2.2). FAIL if the static
   aim after creep is > 0.15 deg.
6. **`mass_com`:** FAIL outside 0..+8 for the default lens, WARN for the others.
7. **Clearance zones.** Replace the two "ring in bore" zones with: "BFAR in tub counterbore" >= 0.675, "adapter in
   lip" >= 0.74, "adapter in plate bore" >= 2.5.
8. **M3 screws.** `check_driver`, `screw_pierces` and `interference` handle kind M3 (the s_ prefix already
   exempts them). `check_bosses` skips kind M3. A new `check_nut_slots` asserts the slot size, front skin >= 1.6,
   rear skin >= 1.2, bolt coaxial with the slot +-0.05, and the tip >= 1.0 past the nut.
9. **Existing sweeps** re-check `pi_in` against the new tub blocks and `hood_on` against the blocks and fin
   automatically. Add collar_on, lens_in, collar_off and the new camera_in.

### 6.5 Tests
- `test_tub`: lip and counterbore present, pins gone, slots, `pi_in` 0 mm3.
- `test_hood_panel`: no turret, 4 holes, fin, keeper position; lens/camera cylinders against the hood at the new
  stack.
- New `test_collar`: contract, bed face, both lenses build, bore-band, slit, pinch walls, nut slots, sweeps and
  removals.
- `test_r3_regressions`: a synthetic FAIL for each of: `check_j7_float` (keeper 0.2 from the cover),
  `check_lens_support` (a lens without support) and `check_nut_slots` (rear skin 0.8).

### 6.6 build_d2.py, make_tables.py, make_bom.py
- **build_d2:** EXPLODE lens_collar +X 40; STEP_VIEWS; the J7-R sections; `mass_com` runs for each lens with its
  collar.
- **make_tables:** an `estimate_volume('lens_collar')` branch (about 15 cm3); counts are +1 print, PT unchanged,
  +4 M3. Update the text lints.
- **make_bom:** LINES for M3 x 12 (3), M3 x 16 (1), ISO 7089 M3 (3), DIN 562 M3 (4); the collar as a printed row.
