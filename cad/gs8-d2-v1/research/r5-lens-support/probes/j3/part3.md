
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
  (the camera turns until its cover meets the hood fin); set iris and focus, tighten the thumb screws; push the lens
  gently rearward until the knurl seats on the collar cone; tighten s_c4 0.2 N m. Delete "clock the Kowa lock screws
  to the right". 10 text += level check on live view: if needed loosen s_c4 half a turn, turn lens and camera
  together, re-seat on the cone, re-tighten.
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
