
**Deviation from the starting angle.** I clamp the lens's fixed rear barrel, not the C-CS adapter.
- The real adapter is a 5 mm band at x -4.3..+0.7, inside the tub lip and the hood plate.
- That band is too short to take a moment, and a tub-grounded part cannot reach it through the hood.
- The axial job the adapter clamp would have done is taken by the lip on the BFAR face. That face is metal, concentric,
  and independent of back focus.

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

1. **Measure first:** MP-CAM and G-LENS. Then work through items 2-11.
2. **`layout.py`**
   - `CAM` -> `CAM_R` (bfar, adapter, housing, tab, pcb, cover, s_nom 1.25, s_max 3.0, `LIP_X` -4.3, lip_d 32.4,
     cb_d 37.5). Derive `C_FLANGE_X` = `LIP_X` + 5.0 and `CS_FLANGE_X` = `LIP_X`. Delete `pins`. Move the keeper.
   - New `COLLAR`: bolt and foot positions, nut pocket, bore rule, slit and pinch.
   - `LENSES`: add `fixed_band` and `collar` per lens. Correct the Kowa segments to its drawing. Replace
     `lock_screws` with thumb-screw rings.
   - `HOOD`: remove turret/turret_b; add `collar_holes` and `cam_roll_fin`.
   - New `FASTENERS_M3` (kind 'M3+nut', engage = nut). Repeat the hardware mass lines.
   - `STEPS` 3/7/8/9 as in s.5.
   - `INSERTIONS`: `camera_in` moving + c_cs_adapter; collar_on [(25,0,0),(0,0,0)]; lens_in [(30,0,0),(0,0,0)].
   - `REMOVALS`: collar_off; `hood_off` += lens_collar and s_c1..3; `camera_out` off = panel set + lens. Update the
     `LATCH_FREE` lens text ("pinch loosened, then thread").
   - `MATES`: tub/gs_camera contact (lip); lens_collar/tub contact; lens/lens_collar contact; lens_collar/hood
     clearance.
   - `KEEPOUTS`: re-derive `ko_fpc_cam`.
   - `PARTS` lens_collar; `LOAD_BEARING_PARTS`; `CRITICAL_FEATURES` and J7 `required`: tub_lip 1.6/land,
     tub_nut_boss_TL/TR/LL, collar_wall_min, collar_foot, collar_pinch_wall, hood_cam_roll_fin, panel_cam_keeper.
   - `self_check`: the two turret items become:
     - lip - adapter >= 0.75;
     - counterbore - BFAR >= 0.675;
     - tab-wall >= 0.3 for s 0..s_max;
     - keeper-cover >= 0.5 at s_max;
     - collar front <= first rotating ring - 2.0;
     - boss x >= drop front + 0.5;
     - channel to tube >= 0.2.
3. **`cots.py`**
   - Real `gs_camera`: BFAR, housing + tab, PCB, cover, no tripod block, sub-shapes tagged body or bfar.
   - Adapter dia 30.75 x 5.0.
   - Corrected `lens_proxy`.
   - M3 screw, nut and washer builders.
4. **`printed_tub.py`:** lip and counterbore teardrops; remove the pins; add `_collar_nut_bosses`.
5. **`printed_hood.py`:** remove `_turret`, `TURRET_R_FILLET` and the support note; bore tool to x 0.3; add
   `_collar_holes` (teardrop -Z) and `_cam_roll_fin`.
6. **`printed_panel.py`:** keeper from `CAM_R`.
7. **New `printed_collar.py`:** `PRINT` face_down +X; builds for `L.LENS`; imports only math, cadquery and d2_common.
8. **`checks.py`**
   - New `check_j7r_float`: every camera-body sub-shape at least 0.2 from all printed parts and COTS. The only allowed
     contact is the BFAR face on the lip.
   - New `check_lens_clamp`: conservative M_sep at least 1.5x static for every `LENSES` entry, with the 5 g ratio
     reported.
   - New `check_mount_polygon`.
   - Replace the J7 clearance zones.
   - Let `check_driver`, `screw_pierces` and `interference` accept M3 entries; add `check_nut_pockets`.
   - `mass_com`: warn outside 0..+8 for the release lens.
9. **`build_d2.py`:** J7-R section (cuts y 0 and z 92); explode entry; mass_com builds the collar for each lens.
10. **`make_tables.py` / `make_bom.py`:** collar rows; BOM lines m3_screw, m3_nut_thin, m3_washer; M3 count text.
11. **Tests**
    - `test_tub`: lip, no pins, bosses against pi_in.
    - `test_hood_panel`: no turret, holes, fin, keeper; update the lens and camera cylinders.
    - New `test_collar`: contract, overhangs, bore against band, slit, channels, pinch walls.
    - `test_r3_regressions`: the new checker logic.
12. **Docs**
    - SPEC s.9/s.10 and DESIGN J7.
    - ASSEMBLY: B0, steps, lens swap, service.
    - FASTENER-POLICY: a new section for the M3 exception. Reasons:
      - the Pi drop column leaves 2.8 mm behind the wall, and PT needs at least 8;
      - the collar and pinch are cycled at every lens change, and PT allows 5 reuses;
      - the screw is the same M3 pan PH1 family as the existing insert fallback.
    - PRINT-GUIDE: the collar row; the hood supports.
    - MEASURED-PARTS: MP-CAM, G-CAM-2, G-COL-1.
    - LENS-ZOOM-CANDIDATES "Load path": correct the premise and record the resolution.
    - HANDOFF.
    - Build with `run_locked.py` only.

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
