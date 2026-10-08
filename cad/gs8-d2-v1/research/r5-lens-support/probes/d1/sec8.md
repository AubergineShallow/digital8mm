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

