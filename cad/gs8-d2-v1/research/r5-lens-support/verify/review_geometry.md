# r5 review: geometry and physics (reviewer: geometry)

Date 2026-10-06, about 16:50 to 17:05 SGT. The review was time-boxed and read-only. I ran no build and edited no repo
file except this one.

Evidence used:
- `layout.py`: `CAM`, `COLLAR`, `TUB_INSERT_BOSSES`, `LOAD_MODEL`, `LENSES`, the FPC keep-outs;
- `cots.gs_camera_parts`;
- `checks.check_lens_clamp`, `check_lens_support` and `check_inserts` (the depth rule);
- `out/checks.json`: `j7_float`, `lens_clamp`, `inserts`, `lens_support`, `mass_com`, `cable_routes`, `mate_overlap`,
  `critical_features`;
- the images `gs_side.png` and `kowa_zoom.png`;
- `dossier_external.md` sections 1-8.

Numbers marked "reproduced" come from a small Python recomputation of the layout values.

## Findings

### G1 (minor, plausible): the datum chain puts the image plane at or behind the PCB front at s_nom

- No sensor-plane datum or 17.526 check exists in `layout.py` or `checks.py`. A grep for 17.5, image_plane and
  sensor_plane found none. The dossier (s1 item 5) flagged this, and r5 did not add it.
- Reproduced from the CAM values (BFAR face -4.4, head 1.2, housing 10.35):
  - C flange to PCB front = 16.55 + s;
  - at s_nom 1.25 this is 17.80.
- Focus at infinity needs 17.526 + IR-plate shift (1.1 mm, n 1.5: 0.37) + die height above the PCB, which is 17.89 + d.
- So at s_nom the modelled image plane falls about 0.1 mm behind the PCB front face, which is physically impossible.
  A real s at infinity would be 1.34 / 1.84 / 2.14 for a die height of 0 / 0.5 / 0.8.
- The dossier's own s8.1 sanity check uses housing front + 7.5 to 8.3 at the CS standard. The model gives
  6.2 + 1.25 = 7.45, which is below that range.
- Fix: add a sensor-plane datum (PCB front + die height, `'unconfirmed'`) and a layout self-check. Treat s_nom as a
  derived value, not a fixed 1.25.

### G2 (minor, plausible): the drawing's 5.8 adapter element is read as 5.0 face to face, a 0.8 shift that eats the keeper gap

- `gs_side.png` shows the 30.75 element 5.8 long, visible in front of the 1.2 BFAR head.
- An adapter spigot threaded inside the BFAR cannot be visible in a side elevation. So in the drawn state, C flange is
  about housing front + 7.0, against the model's 6.2 at s 0.
- The drawing chain does not close exactly either: 5.8 + 1.2 + 10.35 + 1.4 + 6.49 = 25.24, against 25.07 overall.
- The 7.0 reading combined with sandyol's s ≈ 1.25 puts the image plane at about PCB front + 0.7, which is plausible.
  This supports 7.0 over 6.2 (see G1).
- If 7.0 is right, the camera body sits 0.8 further back relative to the lens and collar at every s. The effects:
  - The keeper catch gap at s_max goes from 0.5 (`j7_float` body s 3.0 panel 0.5, rule 0.4) to about -0.3, so the
    cover would touch the keeper whenever s > 2.2.
  - The lip gap grows from 0.5 to 1.3, which is benign.
- MP-CAM measures adapter face to face (5.00) and BFAR head thickness. Those do not detect a raised CS seat or a hidden
  offset.
- Fix: add to MP-CAM a direct caliper measurement of C flange (adapter front) to cover rear, at s 0 and at the set s.
  Every float gap depends on that number.

### G3 (minor, confirmed reading): the float gaps sit at or near their rules and depend on unmeasured ±0.5 drawing values

- `j7_float` body vs tub at s 0: axial 0.4, exactly at the 0.4 rule. Keeper at s 3.0: 0.5. BFAR vs lip: 0.5.
- The axial datum is the Kowa knurl rear edge, at +2.2 ±0.5 from the drawing (dossier s7.1). A +0.5 error closes the
  lip catch (0.5) and the body/tub gap at s 0 (0.4 → -0.1), turning catches into seats.
- G-LENS records the rear-face position to ±0.05. But neither MEASURED-PARTS nor the "If it fails" row says that a
  `LENSES` support-band update plus a rebuild is mandatory before printing the tub and panel.
- Fix: state in G-LENS that band x0/x1 must be updated and rebuilt, not just checked.

### G4 (minor, plausible): the insert preload from the specified torque is a large share of a short insert's pull-out

- The torque is `M3.torque_Nm` s_c1..s_c3 = 0.25 N m. With nut factor 0.2 to 0.3, that is about 280 to 420 N of
  preload (reproduced).
- That preload pulls each short (L 4.0) heat-set insert out toward the head. Short M3 inserts in ASA pull out at
  roughly a few hundred N [estimate; no source checked].
- Service loads are only 5.8 N at 5 g (`lens_clamp`).
- `check_inserts` checks geometry only: bore, depth, wall 1.706 to 2.0. The wall is measured from the 4.0 pilot, so it
  is about 0.3 less outside the 4.6 knurl.
- The same preload also loads the 7.0 washer on the printed foot at about 10 to 14 MPa, which invites creep at 50 °C.
- Fix: about 0.1 to 0.15 N m for s_c1..s_c3 (170 to 250 N), or a pull-out and creep step at G-COL-1 with the specified
  torque.

### G5 (minor/note, confirmed): the 3 bolted anchors do not enclose the lens axis

- Reproduced: the TL-TR-LL bolted-only margin is -8.80 (LL is now (28, 36), see the COLLAR comment). The 4-foot margin
  is 16.0, a pass.
- LR is compression-only, so the polygon rule holds only for loads that press LR into the wall.
- An axial pull on the lens (+X), or a rear-first knock, is reacted by prying about the TR-LL line, with TL in
  compression. That amplifies the bolt tension, and `anchor_tension_shock_N` ignores it: it uses
  moment / (z_top - z_min) only.
- Loads are small, so this is not a blocker. The check's pass hides it, though. It reports the margin "with LR" as the
  rule, against the brief's "keep the lens axis inside the anchor polygon".
- Fix: either a tension-capable LR (a 4th insert, if the pi5 box allows) or a prying factor in `anchor_tension`.

### G6 (note, confirmed math): M_sep = (pi/6) F L is right for a thin band under uniform pressure, but optimistic for this collar

- Derivation check: uniform hoop tension T gives p = T/(rL). The moment at which one end of the band starts to gap is
  M = pi p r L^2 / 6 = pi T L / 6. The formula matches; Kowa gives 0.1696 N m (reproduced).
- Two effects reduce it:
  - The collar is a thick ring (8.85 wall, `collar_wall_min`).
  - Capstan friction during tightening lowers the hoop tension away from the slit, to e^(-0.3 pi) = 0.39 at the far
    side. Mean pressure is about 0.6x.
- Ratio_static 2.97 then becomes about 1.8, which still clears sep_safety 1.5.
- Closing the 0.3 diametral clearance costs only about 5 N (curved-beam estimate), which is fine.
- The 5 g WARN (0.286 > 0.170 N m: the lens rocks elastically) is honest and stays.
- Fix: none required. Say in LOAD_MODEL that M_sep is an upper bound until G-COL-1.

### G7 (note, plausible): the GS drawing calls out dia 22.4, but the model's bores are 25.5

- The front view of `gs_side.png` has a dia 22.4 callout inside the adapter (a double circle at about 24.8 and 22.4).
- `CAM` uses 25.5 for the adapter, BFAR and throat bores (throat `'unconfirmed'`).
- The Kowa rear spigot is dia 22.5 and protrudes to C - 6.7 = x -6.1, which is 0.5 behind the housing front at s 0.
- If the dia 22.4 aperture (filter seat or BFAR shoulder) lies within about 1.7 behind the CS flange, the lens bottoms
  on it. The axial depth is unknown, so the outcome is plausible, not shown.
- r5 leaves filter clearance to G-LENS with no CAD check.
- Fix: model the 22.4 aperture as `'unconfirmed'` at the shallowest plausible depth, or add it explicitly to MP-CAM.

### G8 (note, plausible): the FPC is now the only external load on the floating camera

- `cable_routes` fpc: route 60.9 of 200 mm, slack 119.1.
- The slack sits in a 9-layer S-fold, `ko_fpc_loop` at x -42.5..-29.7, about 4 to 5 mm behind the cover rear.
- A packed fold acts as a spring on the cover's lower rear edge. 0.3 N at about 20 mm is about 6 N mm, roughly the
  camera's own weight moment (34 g x about 17.5 mm = 5.8 N mm).
- G-CAM-2 ("50 g on the cover") roughly bounds it.
- Fix: run G-CAM-2 with the real FPC fold installed.

### G9 (note, confirmed): a comment typo in the keeper gap

- `layout.py` line 261 says the keeper gap is "1.75 at nominal".
- The geometry gives 2.25, and `j7_float` body s 1.25 shows panel 2.25.

## Verified OK

- **CAM values against `gs_side.png`:**
  - 10.35 housing (104 px at 10.05 px/mm), 5.02 tab depth, 10.16 tab and 0.8 slot, tab top r about 22;
  - lock screw about 2.5 behind the housing front;
  - PCB 38 sq x 1.4, cover 39.5 sq x 6.49;
  - holes at ±15 (4 from the edge), dia 2.5;
  - BFAR dia 36, adapter dia 30.75;
  - the tripod block is not modelled, with removability gated at MP-CAM and a stop rule.
- **`gs_camera_parts`:**
  - housing, throat, tab and slot, lock-screw heads on both sides, PCB holes, cover and FPC recess built as described;
  - BFAR thread exposed only for s > 0.
- **Kowa segments against `kowa_zoom.png`:**
  - focus ring at the rear (10.6..22.4) and iris at the front (30.9..36.6);
  - the knurl is the rear-most large ring (about 5.2 long, 2.3..7.5 from the flange, measured on the image);
  - the Ø31.5 step at 0..2.2;
  - the 6.7 rear protrusion matches;
  - thumb screws at about 14.4 / 33.0;
  - the scale numerals sit next to the knurl, which is consistent with a fixed index there, but unconfirmed (G-LENS).
- **Collar against the lens:**
  - front 8.6 ≤ 9.2 (Kowa); 8.6 = 8.6 (Fujinon, 0 margin, band `'assumed'`);
  - bore 0.3 diametral;
  - collar vs adapter 3.32, BFAR 3.48, body 4.39 (`j7_float`);
  - `mate_overlap` hood/lens_collar 0 mm3, a clearance.
- **Hood foot holes:**
  - the feet (dia 7.6) clear the hood holes (dia 8.6), 0.5 radial;
  - hood_foot_hole land rows at 1.2;
  - the camera body to hood is 0.8 lateral (rule 0.5).
- **Lip:** lip vs adapter 0.825 radial (rule 0.6); the BFAR annulus overlap on the lip catch is about 1.8 radial.
- **Inserts:**
  - the `check_inserts` local-depth rule is insert + flush (4.1), so s_c3's 4.184 passes correctly;
  - every wall is ≥ 1.6 from the pilot.
- **Balance:**
  - Kowa +1.47 (brief about +1.4);
  - Fujinon -9.76 (brief about -11, about 1.2 better, plausibly from the 10 mm lens shift).
- **Clamp math reproduced:** M_sep 0.1696 N m; bolted-only margin -8.804.

## Not reviewed (deadline)

- A diff against `baseline-r4-2026-10-06.zip`.
- STL mesh probes with trimesh (hood plate thickness and stiffness without the turret, actual foot-to-hole rings).
- The `sweeps` collar_on / lens_in insertion paths and the hand-hold assembly order.
- `IMPL-NOTES.md` in full.
- The judges' documents beyond their s6-s7 references.
- The Fujinon band source.
- The roll-fin web geometry.
