# GS8 D2 release layer: CAD specification (`cad/gs8-d2-v1`)

> **Integrator, 2026-10-04:** the build changed some numbers in s3, s5 and s7 (interface requests in NOTES.md). They
> are in `layout.py` (marked `INTEGRATOR`) and listed in DESIGN.md s5-s6. Where this file and `layout.py` differ,
> `layout.py` wins.
>
> **r2 rectification, 2026-10-05** (audit `audit/d2-readiness-2026-10-04/REVIEW.md`; per-finding record in
> `RECTIFICATION.md`): the 2 skirts and J5 are eliminated; the 4 Pi floor hooks are replaced by a removable printed
> `pi_keeper` on 2 more PT screws (s_k1, s_k2); a panel rib stops the EVF board in +Y; the hood hook tooth land is 0.6;
> s6 adds the critical-feature, EVF-restraint, removal and service-driver checks; s6.5 is no longer a pass basis.
>
> **r2 fixer, 2026-10-05 02:00-** (verifier findings on r2; `RECTIFICATION.md` "Fixer pass"): hood hooks land 1.0
> (catch plane z 88.45/88.55, ledges 1.7 tall), hk1/hk2 get pin release holes, hk3/hk4 a 45 deg return catch; s_k2
> boss re-sited (y 28.25, r 3.6); panel boss tops 12.6 and the keeper bridge underside 12.85; EVF rails cut back round
> the HDMI plug and the ZIF; cap key top -105.8; the J4 lock screw s_j (7 PT screws); a hood post over the far kit
> screw head; the rear-wall bore roof notched 1.2 at the seam; checks: feature classes, release access, stack
> retention, hood/camera/EVF removals.
> Where this file still quotes an older number, `layout.py` wins.
>
> **r5, 2026-10-06: heavy-lens support** (`R5-BRIEF.md`; study `research/r5-lens-support/`; record `RECTIFICATION.md`
> "r5"). The camera model is rebuilt to the official GS drawing (the C flange is at x +0.6, not +10.6), and J7 becomes
> the **J7-R float**: a printed, per-lens `lens_collar` clamps the lens on its fixed rear band and is anchored on the tub
> front wall by 3 M3 screws in brass heat-set inserts plus a compression foot. The camera (housing, back-focus ring,
> adapter, PCB, cover) hangs on the lens and touches no printed part in service; the tub lip, a hood roll fin and the
> panel keeper are catches with gaps. The 2 camera pins and the hood turret are deleted. Now 12 printed parts and
> 7 PT + 4 M3 screws (s1, s2, s3, s5, s6, s10).

Written 2026-10-04 by the spec owner for the five build owners. **`layout.py` is the single source of truth**: every
number in this file is quoted from it, and if the two disagree, `layout.py` wins. `python cad/gs8-d2-v1/layout.py`
runs plain-Python consistency checks (126 rows, 0 failed in the r2 build of 2026-10-05). Nothing here is printed, bought or measured.
Purchased parts are proxies, so a "pass" can only come from a computed check, never from hardware.

Sources: the D2 concept (`concepts/nizo-evf-2026-10-03/D2/CONCEPT.md`, `build_concept.py`, `out/*.png`),
`research/PALETTE.md`, `electronics/gs8-evf-v1/EVF-SELECTION.md`, the FDM rules of `cad/gs8-release-v1/release_common.py`,
and the GS camera record in `cad/gs8-stills-v1/SPEC.md` (R1 s1.1-1.2).

## 1. Frame and datums

| Datum | Value | Note |
|---|---|---|
| Axes | X forward (toward the lens), Y to the operator's left (panel side), Z up | as in the concept |
| Origin | x 0 = hood front-plate outer face; y 0 = body centre plane; z 0 = tub floor underside | concept x is shifted by -77 (`cx()`) |
| Body | 154 x 70 x 100: x -154..0, y -35..35, z 0..100 | the base and grip hang below z 0 |
| Tub | rear face x -154, front face x -2.7, wall 2.5, front-wall inner face **x -5.2**, wall tops **z 97.3** | right-wall inner face y -32.5 |
| Panel | y 32.2..35 (2.8 thick), z 8.2..97.0 | the tub/panel joint plane is y 32.2 |
| Optical axis | y 0, z 60 | |
| Camera stack (r5, J7-R) | tub lip land x -3.9..-2.7; lip gap 0.5; back-focus-ring (BFAR) face = CS flange **x -4.4**; C flange **x +0.6**; housing front x -5.6 - s (s = BFAR screw-out 0..3.0, nominal 1.25); cover rear x -23.84 / -25.09 / -26.84 at s 0 / 1.25 / 3.0 | r4 had lands on x -5.2 and the C flange at +10.6 (a camera model that does not match the official drawing). The lens's axial position comes from the collar's 45 deg cone on the rear edge of its fixed band; the camera sets nothing |
| EVF axis | y 16, z 78; flange datum **F = x -154.0** on the tub rear face; display plane F + 6.0 = **x -148.0** | the cup lip is at x -187.6 (33.6 proud) |
| Grip | x -71..-23, y -15..15, z -110..-8; axis x -47; grip top (web of the hand) z -8 | er 9 |
| Base | x -117..-0.5, y -35.2..35.2, z -8..0 | 5 mm front chamfer |
| Tripod | 1/4-20 socket at x -107, y 0 | nut z -5.7..-0.1 |

## 2. Parts

**Printed: 12 parts (r5).** The concept had 10. r1 had 12 (2 separate skirts); r2 removes the skirts (finding 3) and adds the `pi_keeper` (finding 1); r5 adds the `lens_collar` (one per lens with a support band: the release exports the default lens's collar; a `--lens` build exports its own).

| id | module | material, colour | face down | owner | envelope (layout `PARTS`) |
|---|---|---|---|---|---|
| tub | printed_tub.py | ASA satin silver | -Y (right wall) | tub | x -154..-2.7, y -35..35, z -3.65..97.3 |
| hood | printed_hood.py | ASA black | +Z (roof) | hood_panel | x -170.2..1.0, y -32.5..35, z 0.3..100 (r5: no turret; was x ..8.5) |
| panel | printed_panel.py | ASA satin silver | +Y (face) | hood_panel | x -154..-2.7, y -32.3..35, z 2.6..97.0 |
| base_grip | printed_grip.py | ASA black | +Z (base top) | grip_small | x -117..-0.5, y -35.2..35.2, z -110..0 |
| cap | printed_grip.py | ASA black | -Z | grip_small | x -71..-23, y +-15, z -116..-110.1 |
| plunger | printed_small.py | ASA black | +X | grip_small | x -5.3..-1.3 |
| knob_exp | printed_small.py | ASA black | +Y | grip_small | dia 28 x 9 |
| knob_fps | printed_small.py | ASA black | +Y | grip_small | dia 20 x 7 |
| eyecup | printed_small.py | TPU 95A black | +X | grip_small | dia 46 x 16.3 (13 cup + 3.0 sleeve over the eye-end body) |
| stick_sleeve | printed_small.py | ASA satin silver | -X | grip_small | 22.9 x 13 x 16 |
| pi_keeper | printed_keeper.py | ASA black | +Z (top face) | tub (R1, r2) | x -105..-41, y -23..31.9, z 7.7..15.6 |
| lens_collar (r5) | printed_collar.py | ASA black (PC if G-W11 finds the camera zone above 50 C) | +X (front face) | tub | x -2.7..8.6, y -35..33, z 30..95.5 (Kowa; per lens from `layout.collar_spec`) |

**Purchased: 22 COTS rows (incl. the microSD proxy, FIXER A-F2, and r5's `m3_hw` lens-collar hardware row) plus 10 cables** (layout `COTS`, `CABLES`; the fan lead is the 10th). These are:
- Pi 5, Active Cooler, X1203 and its kit (4 standoffs, 8 M2.5 screws);
- GS camera and the C-CS adapter (r5: modelled from the official drawing as tagged sub-solids, `cots.gs_camera_parts(L, s)`; the
  camera's tripod block comes off at bench step B0 and is not modelled);
- the lens, set by the `LENS` parameter: `kowa_lm6hc` (default, 215 g) or `fujinon_hf6xa` (100 g); r5 adds the
  Computar H6Z0812 zoom (305 g) as a data-only entry (`LENSES_DATA_ONLY`: checked by `lens_support` / `lens_clamp`,
  never built);
- 0PE039-16X eyepiece, HMX039 panel, EVF board and foam pad;
- SDCZ880 stick, Adafruit 5880 encoder, 18/24 rotary, run button;
- 1S2P pack, XT30 pair, tripod nut, strap and 7 PT screws (4 enclosure + 2 keeper, r2, + the J4 lock s_j, r2 fixer);
- r5: the lens-collar hardware (`m3_hw`): 4 M3 screws, ISO 7045 PH1 (s_c1..s_c3 M3 x 10, s_c4 M3 x 16), 4 ISO 7089
  washers and 4 brass heat-set inserts (3 short in the tub bosses, 1 L 5.7 in the collar's lower lug); FASTENER-POLICY I.

## 3. Interfaces

Each row names the part that carries each feature. Clearances are per side.

| Joint | Carrier and features | Mating part | Clearance | Motion |
|---|---|---|---|---|
| J1 hood-tub | hood: 4 cantilever hooks (L 10.5, t 1.6, w 8, tooth 0.65 = reach 0.40, land 1.0 (r2 fixer; tooth root 1.65; hk1/hk2 90 deg catch + pin release hole in the tub right wall, hk3/hk4 45 deg return catch), 45 deg lead-in, 0.8 x 45 deg root gussets; strain 0.87 % nominal, 1.31 % with Kt 1.5, `layout.snap_strains()`) at hk1 x -45 and hk2 x -125 (right wall), hk3 y 22 (front wall), hk4 y -20 (rear wall) | tub: catch ledges 0.8 proud, z 88.55..90.25 (r2 fixer: +0.4, 1.7 tall; hk3/hk4 underside sloped 45 deg), 45 deg top chamfer; 2 dia 1.6 release holes at z 87.7 (hk1, hk2) | beam to ledge 0.25; tooth play 0.1 | hood straight down -Z |
| J1 seat | hood band underside z 97.3 on the wall tops; plate inner face x -2.5 (0.2 off the front wall); housing front x -154.2 (0.2 off the rear face) | tub | contact / 0.2 | |
| J2 hood-panel | hood: rail block x -134.5..-11.5, y 25.5..32.0, z 90.15..97.3; groove open +Y, z 91.75..94.85, lower lip with a 45 deg outer face | panel: top tongue x -134..-12, y 26..32.2, z 92..94.6 | 0.25 (groove) | panel along -Y |
| J3 panel-tub | panel inner face on the tub wall ends at y 32.2; 2 locating ribs inside the front and rear walls | tub: 2 lip notches (x -91 and -105, +-4.3) let the panel bosses pass | LOCATE 0.15 | panel along -Y |
| J4 base-tub | tub: 2 T-tongues under the floor at x -18 and -79 (8 long; head 36 wide z -3.65..-1.85, neck 26 wide z -1.85..0; -Y ends 45 deg) | base: window 10 mm ahead, neck slot through 1.6 lips, head pocket z -3.9..-1.6 | 0.25 | base on 10 mm back, then +X 10; **r2 fixer: locked by s_j** (PT up through the base into a tub floor boss at (-111, -20), step 3), independent of the panel screws s_b1/s_b2 |
| J5 skirt-base | **eliminated in r2** (finding 3): no skirts, no grooves; the base side faces are plain and the 2 panel boss tabs fill the tub lip notches flush | - | - | - |
| J6 cap-grip | grip: 2 dovetail rails z -110..-107 on the side walls; rear stop lip | cap: grooves + detent 0.4 | 0.25 | cap -X to close (+X opens) |
| J7 camera (r5: **J7-R float**; r4's seat, pins and turret are deleted) | **lens_collar** (per lens): bore = support band + 0.3 diametral, a 45 deg cone that takes the rear edge of the lens's fixed band (Kowa: the dia 42 knurl at C + 2.2..7.6, seat x 2.8), front at least 2.0 behind the first moving ring, -Y slit 2.0 closed by s_c4 (M3 x 16, -Z from above, into an insert in the lower lug); 4 feet dia 7.6 through 4 dia 8.6 hood holes onto the tub front face: TL (11, 90.5), TR (-11, 90.5) and LL (28, 36) bolted by s_c1..s_c3 (M3 x 10 + washer, -X from the front, into heat-set inserts in 3 tub bosses x -7.6..-5.2), LR (-19, 44) compression only; the lens axis is 16.0 inside the anchor polygon (rule 10). **Catches, never seats:** tub lip dia 32.4 (land x -3.9..-2.7, 0.5 ahead of the BFAR face) and BFAR counterbore dia 37.5; hood roll fin + 2 webs beside the cover; panel keeper x -30.67..-27.34 (0.5 behind the cover at s 3.0); rib_l, rib_r | the lens (on the cone) carries the hanging camera unit: GS housing + BFAR + C-CS adapter + PCB + cover | collar bore 0.15 radial; catches (check `j7_float`, s 0 / 1.25 / 3.0): body axial >= 0.4, lateral >= 0.5; BFAR axial >= 0.4, radial >= 0.6; adapter radial >= 0.6 | step 7: camera -Y through the open left side 11.1 back and 2 high, down 2, then +X 11.1 past the lip; collar +X 30 onto the face. Step 8: lens +X 40 through the collar into the adapter |
| J8 EVF | tub: rear-wall bore dia 29.3 + -Y half-collar x -151.5..-149.6; OLED cell (front ledge x -148.0, open +Y); board slot (2 grooves 2.1 wide, the bottom one gapped at y 3..18 for the HDMI plug: r2 fixer, 1.0 clear of the receptacle/plug, +X spine 0.6 off the plug envelope; top rail -X wall relieved 0.4 over the ZIF) | panel cap x -151.4..-145.0 (clamp r 14.4 = 0.1 crush; OLED finger to y 24.0); hood housing (1.25 radial round the barrel; +Y window x full, z 66..90) | 0.15 bore; cap 0.1 interference | eyepiece +X from the rear; OLED, board -Y |
| J9 Pi-tub | tub: 4 bosses OD 9.0 to z 6.0 with head pockets dia 5.6 x 2.4 (positive location in X/Y/Z; nothing else positions the stack); **r2: no floor hooks**. r2 fixer: a hood post (x -10.7..-6.5, y -31.3..-27.6, z 22.0 up to a fin under the roof) stands 0.15 over the far kit screw head (-9.5, -28.8) as a lift stop (no positioning load). Removable `pi_keeper` (printed, rigid) on 2 tub bosses (s_k1 (-99.5, 16.0), s_k2 (-64.0, 28.25) r 3.6 (r2 fixer: was 28.9 / r 3.5, +Y wall 1.75 over the top 2 mm), top z 9.8): 4 fingers at the r1 stations (USB edge y -20, 12; port edge x -80, -45), 0.65 over the X1203 edge, tip 1.6, underside z 7.7 = 0.1 above the X1203 | X1203 + Pi stack | keeper 0.1 (z) / 0.25 (xy) | stack on the L path, then keeper -Y, +X 1.2, down 0.5 |
| J10 plunger | hood: pocket 14.2 x 8.4 x 1.2 (x -2.5..-1.3) + opening 11.6 x 6.6 (guard lip 1.3); tub: hole 11.6 x 6.6 | plunger: stem 11 x 6, flange 13.6 x 7.8 x 0.8, nib dia 2.5 on the button (y 5.3, z 21.0) | 0.3; nib 0.25 to the button; travel 0.6 (press 0.35 of 0.45) | in from the front before the hood |
| J11 stick | tub: rear scoop 29 x 20 x 10 deep; guide x -148.6..-94.5 (sleeve section to x -138) | sleeve: 0.8 wall, end flush x -154 | 0.25 | stick +X |
| J12 controls | panel: encoder cradle (2 hooks on the PCB back y 24.1), hole dia 7.5; switch hole dia 10.0 + anti-rotation slot 1.7 x 3.0 x 2.0 at 12 o'clock r 7.9; engraving 0.4 deep | encoder, switch (nut outside), knobs (D bores) | 0.25 | bench (step 2) |
| J13 grip | base_grip: run-button cradle behind the front wall (hole dia 13.6 in a 12 x 28 pad 1.5 deep); base opening x -45..-25.5, y -13..9; nut pocket AF 11.4 from the top (bearing wall 2.3); strap slots (2 in the base x -76.5/-82.0, 2 in the grip heel z -104/-97) | run button, nut, strap | 0.15-0.25 | bench (step 3) |
| J14 vents | hood: roof inlet x -71..-45, y -24..4 (7 slots); plate band y -26.5..17.5, z 25.9..29.7 (13 slots); corner field. tub: matching front-wall windows; right-wall slots (exhaust x -19..-5, X1203 x -65..-49); baffle | | slot 2.0, web >= 1.4 | |

**Screw stations** (layout `SCREWS`; `head_point` is the head bearing face; `axis` is the advance direction). r5: every
entry has a `kind`: **PT** (the 7 body screws, the first 7 rows; PT checks and counts apply to them only) or **M3** (the 4
lens-collar screws s_c1..s_c4, machine thread into brass heat-set inserts, checked by `check_inserts`). The
straight-driver audit applies to every kind.

| id | head point | axis | through / into | engagement | step |
|---|---|---|---|---|---|
| s_b1 | (-91, 27.85, -2.0) | +Z | base counterbore dia 7 x 6 deep, base 2.0, floor 2.5, then panel boss_b1 (z 2.6..12) | 7.4 | 8 |
| s_b2 | (-105, 27.85, -2.0) | +Z | as s_b1, into boss_b2 | 7.4 | 8 |
| s_j | (-111.0, -20.0, -2.0) | +Z | base counterbore dia 7 x 6, then the tub floor + J4 lock boss (OD 8, z 0..12.6), r2 fixer | 10.0 | 3 |
| s_r1 | (-31.5, -32.4, 85.5) | +Y | right wall + 2.0 pad, counterbore dia 7 x 2.6, then panel post_f (8 x 8) | 10.0 | 8 |
| s_r2 | (-143.5, -32.4, 47.5) | +Y | as s_r1, into post_r | 10.0 | 8 |
| s_k1 | (-99.5, 16.0, 14.3) | -Z | keeper counterbore dia 7, then tub keeper boss (top z 9.8), r2 | 7.5 | 4 |
| s_k2 | (-64.0, 28.25, 14.3) | -Z | keeper spot-face notch 7.0 wide, then tub keeper boss (marginal M3-insert site, FASTENER-POLICY E), r2 | 7.5 | 4 |
| s_c1 (M3, r5) | (3.3, 11.0, 90.5) | -X | M3 x 10 + washer: collar counterbore dia 7.5 (x 2.8..8.6), the TL foot, then the short insert in the tub TL boss (x -2.8..-6.8) | 3.9 | 7 |
| s_c2 (M3, r5) | (3.3, -11.0, 90.5) | -X | as s_c1, TR foot and boss | 3.9 | 7 |
| s_c3 (M3, r5) | (3.3, 28.0, 36.0) | -X | as s_c1, LL foot and boss | 3.9 | 7 |
| s_c4 (M3, r5) | (4.7, -31.3, 66.5) | -Z | M3 x 16 + washer on the upper-lug top (spot face), clearance 3.4 through the upper lug, across the slit, into the L 5.7 insert in the lower lug (z 50.1..55.8); the pinch; the last operation on the lens | 5.3 | 8 |

## 4. Print rules per part (all parts: the FDM rules in `layout.FDM` / `d2_common`)

- **tub (-Y, right wall on the bed).** Print-up is +Y.
  - Every internal feature grows from the right wall, or has its -Y faces at 45 deg or steeper: ribs, bosses, hooks,
    ledges, the saddle, the cell, the board rails, the guide and the baffle.
  - The tongues' -Y ends are already 45 deg in `keyhole_tongue`.
  - Horizontal holes over 8 mm in the walls need a teardrop roof toward +Y; the dia 29.3 bore and (r5) the dia 32.4
    lip and dia 37.5 counterbore are in X-normal walls, so the roof points +Y. The 3 r5 insert bosses are teardrop
    prisms (apex -Y) growing from the front wall; the LL boss has a flat chin at y 24.0.
  - No supports.
- **hood (+Z, roof on the bed).** The hooks and the rail block print upward. Supports only at the housing's interior
  ceiling (39 mm span). r5: the turret and its support are gone; the 4 collar foot holes (dia 8.6) are teardrops with
  the apex -Z, and the roll fin and its 2 webs grow from the roof. A 45 deg form that needs no support is also
  allowed. Roof slots are vertical holes.
- **lens_collar (+X, front face on the bed; r5).** No supports: the ears, lugs and feet grow -X, the cone prints as a
  45 deg inward step, and a 0.6 bed chamfer runs round the outer edge of the front face. The only downward faces are
  the 3 washer-seat bridges and the s_c4 holes (test_collar). Production/coupon STLs include print-only 0.2 mm membranes across the anchor holes; clear them to 3.4 mm before assembly. The STEP model and assembly checks use the cleared finished geometry. ASA; PC if G-W11 finds the camera zone above 50 C.
- **panel (+Y, face on the bed).**
  - The engraving is cut 0.4 deep into the bed face; text at least 3.0 high, strokes at least 0.6.
  - The posts, bosses, tongue, cradle, cap and keeper all grow upward.
- **base_grip (+Z, base top on the bed; the part prints upside down).**
  - The lips are the first 1.6 mm of the print. The head pocket ceiling bridges 18.5 mm the short way.
  - The nut pocket opens on the bed.
  - The grip column rises 102 mm, with the cap rails at its top.
  - Bay bridges stay at 30 mm or less.
- **pi_keeper** prints on its top face, no supports (finger backs 45 deg); **cap** prints on its bottom face; **plunger** prints on its front face.
- **Knobs** print on their top faces, with the knurl vertical.
- **eyecup** (TPU) prints on its base ring. The flare is 15 deg, so it needs no support.
- **sleeve** prints on its end face.
- **Beds.** Every envelope fits both beds (`layout.self_check`). The STLs are checked again by `build_d2.py`.

## 5. Assembly order (layout `STEPS`; parts present = the cumulative `adds`, `present_at(step)`)

| # | Step | Adds to the body | Tool | Motion / check |
|---|---|---|---|---|
| 1 | Bench: solder the XT30 pigtail (2 joints); stack the X1203 + Pi 5 with the kit (0.2 N m); fit the cooler; bridge encoder A0; solder the 18/24 lead (2) | (sub-assemblies) | iron; kit driver | |
| 2 | Bench, panel: paint-fill the engraving; snap in the encoder; fit the switch (tab in its slot) and its nut | (panel sub-assembly) | 1/2 in socket | |
| 3 | Base + grip: tripod nut pressed, run button in, strap threaded; base onto the tongues 10 mm back, then +X 10; only then the run lead up through the floor hole (tweezers) | tub, base_grip, tripod_nut, run_button, strap | tweezers | insertion `base_on` |
| 4 | Pi stack (microSD out): run lead in its channel, pigtail round the port edge and down its hole; stack on the L path onto its 4 bosses (nothing clicks); keeper in (-Y, +X 1.2, down 0.5), drive s_k1, s_k2; plug HDMI0, FPC (CAM1), EVF 5 V (USB 2 top) and the header ends of the QT (1/3/5/6), 18/24 (33/34) and run (37/39) leads | x1203, x1203_kit, pi5, cooler, pi_keeper, s_k1, s_k2 | PH1 (straight) | `pi_in`, `keeper_in`; driver audit |
| 5 | Plunger into its hole; hood straight down until the 4 hooks click; microSD home through the front slot | plunger, hood, microsd | tweezers | `hood_on` (snaps), `sd_in` |
| 6 | EVF: eyepiece +X from the rear; flex, HDMI and 5 V mated outside; OLED + board in together from the left (foam behind the OLED); coil the HDMI over the stick guide | eyepiece, hmx039, foam_pad, evf_board | tweezers | `eyepiece_in`, `evf_pair_in` |
| 7 | (r5) Bench B0 done first: camera tripod block off, adapter on, back focus set with the Kowa at infinity, lens off again. Camera + adapter: plug the FPC; in from the left 11.1 back, +X 11.1 past the tub lip; it rests in its cage; fold the FPC loop. Lens collar: feet through the 4 hood holes onto the tub face; s_c1, s_c2, s_c3 from the front, 0.15 N m provisional cap | gs_camera, c_cs_adapter, lens_collar, s_c1..s_c3 | PH1 (straight) | `camera_in`, `collar_on`; driver audit |
| 8 | (r5) Lens, panel still off: fit s_c4 loosely; lens through the collar, screwed into the adapter while a finger through the open left side presses the cover forward (+X) onto the temporary lip catch; thumb screws set; lens pushed back until the knurl seats on the cone (the camera now hangs on it); s_c4 straight down from above, 0.2 N m. Panel: plug the QT JST-SH at the encoder and mate the 18/24 PH junction; panel on along -Y (the keeper becomes the camera's rear catch); drive s_b1, s_b2 (from below), s_r1, s_r2 (from the right) | lens, s_c4, panel, encoder, switch_1824, 4 screws | PH1, hand | `lens_in`, `panel_on`; **driver audit** |
| 9 | Knobs, eyecup, stick with sleeve (r5: the adapter went in at step 7, the lens at step 8) | knobs, eyecup, usb_stick, stick_sleeve | none | `stick_in` |
| 10 | Pack: plug the XT30, push up, cap on (-X). r5 level check on live view: if the horizon is off, s_c4 half a turn, turn lens and camera together (window +-1.4 deg), push the lens back onto the cone, s_c4 0.2 N m | xt30_pair, pack, cap | PH1 (level check only) | `pack_in`, `cap_on` |

**r5 order rule (R5-BRIEF choice 7): never thread the lens into an unsupported camera.** The brief's preferred order is
used (no check broke): the collar and s_c1..s_c3 go on before the lens (with the lens fitted, the dia 30 driver handle
on s_c1..s_c3 hits the Kowa front barrel), and the lens before the panel (a finger holds the camera through the open
left side while the lens is screwed in).

**Straight-driver audit** (user rule): for each screw at its own step (r5: every kind), place a bit of dia 6.5 x 40 from `head_point` against
`axis`, then a handle of dia 30 x 100 beyond it. Both must clear every solid in `screw_audit_set(id)`, except:
- the part the screw passes through, and only inside its counterbore (the bit runs in a dia 7.0 counterbore with
  0.25 radial clearance);
- the screw itself.
Expected clearances:
- s_b1 / s_b2: the handle clears the grip by 12.3 / 24.2 mm (r2 build).
- s_k1 / s_k2 (step 4, from above, hood and panel off): bit 1.23 from the counterbore wall; handle 20.8 / 38.5 mm clear.
- s_r1 / s_r2: the driver comes in from the right; nothing is mounted there.
- r5: s_c1..s_c3 (step 7, along -X from the front, lens not yet fitted): the bit runs in the dia 7.5 counterbore with
  0.5 radial clearance. s_c4 (step 8, straight down from above, lens fitted): bit 0.25 off the collar body (trimmed to
  y >= -27.8 above the upper lug), handle 6.5 off the hood. s_c4 and the 4 panel screws also audit clean with the lens
  present (test_collar).

## 6. Checks `build_d2.py` must run (machine-readable, `checks.json`)

1. Exact boolean interference between every pair of solids. MATES pairs and screws are excluded or limited to the
   stated interference. A pair passes at 0.05 mm3 or less.
2. Minimum clearance for the declared sliding pairs, to at least 90 % of the stated clearance:
   - J1 hooks to ledges;
   - J2 groove;
   - J4 tongue to pocket;
   - J7 (r5, replaces "ring to bore", whose ring and dia 36.5 bore were the wrong camera model): BFAR in the tub
     counterbore (stated 0.5 = the lip gap), adapter in the tub lip (0.825), adapter in the hood plate bore (2.875);
   - J8 barrel to housing (1.25 radial);
   - J10 nib to button.
3. Printed solids against `KEEPOUTS`: overlap 0.05 mm3 or less.
4. Bed fit in print orientation on both beds (STL bounding box).
5. Thin-wall screen (secondary since r2): 1500 area-weighted surface samples per part, wall = max over a 30 deg cone
   of inward rays; share rule as amended 2026-10-04 (area share under 1.2 <= 2 %, under 0.8 <= 0.5 %, loaded zones under
   1.6 <= 2 %). **A fail still blocks; a pass proves nothing by itself** (review finding 2). Samples under the wall
   threshold that no critical feature or named exception covers are listed as `unclassified_thin_spots` (r2 build: none).
   r2 sampled minimums: tub 1.25, hood 1.30, panel 0.80 (named exception), base_grip 1.44, cap 1.60, pi_keeper 1.30,
   plunger 1.20, knob_fps 0.99 (index groove edge), eyecup 1.60; stick_sleeve 0.80 (`THIN_OK`, slider cover).
5c. Critical features (`critical_features`, r2): every `layout.CRITICAL_FEATURES` entry is measured on the built B-rep
   (exact line/face intersection through a point inside the material, optional parallel rays, minimum taken). FAIL: a
   structural entry under its required minimum, an origin outside the material (stale entry), or a `LOAD_BEARING_PARTS`
   member (tub, panel, hood, base_grip, cap, pi_keeper) without a structural entry. **r2 fixer:** the required minimum
   is max(entry `min_mm`, class floor) from `FEATURE_CLASS_RULES`: hook, lug, lip, boss, wing, pin, neck, bar 1.6
   (MIN_WALL_LOADED); wall, land 1.2; a structural entry with no class FAILs. Class `flexure` (the cap detent strip:
   grip_cap_detent_arm 1.5, _dimple_wall 1.25, _groove_corner 1.275) keeps 1.2 only with a named physical gate
   (`FEATURE_GATES`: G-CAP-1, not run) and is printed as an exception. `NONSTRUCTURAL_EXCEPTIONS` are named one by one
   (panel antirot_slot_skin 0.8, badge and "exposure" glyph ridges, the stick-rail lip tip) and never count as coverage.
   Parts left out of `LOAD_BEARING_PARTS` carry a named rationale (`PART_RATIONALE`: stick_sleeve, knobs, plunger,
   eyecup).
   **r3 (audit 2026-10-05 s3):** the nominated origin ray is always measured, also for an even span count (r2 skipped
   it), and an origin outside the material FAILs as a stale origin. Every span ray must hit the solid unless its signed
   offset is listed in `expect_outside=dict(offsets, why)` (on the entry, or `EXPECT_OUTSIDE[id]` for an entry built in
   another block); an unexpected miss FAILs, and a listed offset that is in material, is not a span ray or has no
   reason FAILs as a stale declaration. Declared now: `tub_evf_groove_wall_bot_px` offset -0.5 (y 1.5 lies in the
   ko_5v_end relief of the +X groove wall). Coverage is per joint: `CRITICAL_JOINTS` (12 joints: J1 hood hooks, J2 panel
   tongue, J3 panel-tub, J4 base-tub incl. s_j, J6 cap-grip, J7 camera, J8 EVF, J9 Pi keeper, J9 stack stop, J12
   encoder cradle, J13 grip, J13 strap) lists the required feature ids; a joint FAILs if any id is missing, unmeasured,
   on a part outside the joint, failed, or informational without a named physical gate, and a `LOAD_BEARING_PARTS`
   member in no joint FAILs. The flexures report status `info` as G-CAP-1 gated exceptions (not ordinary passes); J6
   lists them as gated. The per-part rule above stays as a secondary check. Regression cases:
   `test_r3_regressions.py` (pure python, synthetic chords and temporary evidence folders).
5d. EVF board restraint (`evf_restraint`, r2): the board is translated along +-X, +-Y, +-Z against tub, panel and hood;
   the gap to first contact must be <= 0.6 (the groove's own float 0.5 + 0.1) in each direction, and the contact is
   reported by board region (PCB laminate, connectors). Cables and the OLED are not stops. **r2 fixer:** the micro-HDMI
   plug envelope (`ko_hdmi_evf`) moves with the board, the first contact is found per zone, and a connector, ZIF or
   plug zone touching within the PCB's own first contact + 0.2 FAILs.
5e. Service paths (`removals`, `service_driver`, r2): each `REMOVALS` path (the reverse of an insertion, or explicit) is
   swept against everything still fitted in the service state; a deflected latch is allowed only in a named release
   zone with a named tool; screws removed at that step get the straight-driver audit in the service state. A path
   for the Pi stack, the panel and (r2 fixer) the hood must exist, and every non-screw part a path takes `off` needs
   its own path (hood_off, camera_out, eyepiece_out, evf_out) or a named `LATCH_FREE` reason. **r3:** a path whose
   service state keeps the pack (or the XT30 pair) fitted, and its service-driver rows, carry `scope`: "clearance with
   the cap and pack fitted; geometry only: electronic service still requires shutdown, pack removal and XT30
   disconnection first (ASSEMBLY s7 P1-P4)". These rows show that the parts clear each other; they do not authorise unplugging a lead with the
   battery connected.
5g. Stack retention (`stack_retention`, r2 fixer, verifier M-V-MPS-4): the Pi stack CoM (proxy solids x listed
   masses) must lie inside the plan hull of its retention points (keeper fingers kf1-kf4 + the hood stack-stop post
   over the far kit screw head, gap 0.15, measured 0.1-0.3), and the largest rigid lift at any boss pocket that the
   gaps allow (LP over small rigid motions, boss tops z >= 0) must be <= pocket depth - 0.5 = 1.9.
5f. Release access (`release_access`, r2 fixer): a dia 1.5 pin cylinder from outside through each right-wall hood
   release hole to the hook tooth + 0.55: 0 mm3 on every part but the hood, contact with the tooth, beam strain with
   Kt <= 2.5 %.
5a. Engraving groove width (`engrave_groove`): no glyph or stroke with more than 20 % of its area narrower than
   ENGRAVE_MIN_STROKE 0.6 (morphological opening of the face section).
5b. PT boss geometry (`boss_geometry`): solid-measured pilot dia, pilot depth, wall round the pilot and material under
   the head (FASTENER-POLICY H). r2 fixer: the wall is sampled at 7 levels over 5-95 % of the depth (r2 took 30/50/70 %
   and missed a 1.75 wall over the top of s_k2). **r5: kind PT only** (the same 7 rows and rules; the M3 rows have
   their own check, 5h).
5i. **Cloud-polish panel classification.** Encoder tooth-root shear sections are measured explicitly at 1.62 mm,
   against the unchanged 1.6 mm loaded-feature floor; the old 1.02 mm roots cannot pass by measuring their beams.
   The top and both side roots are mandatory J12 features. Any unclassified thin-wall sample now fails a required
   critical_features classification row and blocks the CAD-release claim. The glyph typeface is the included,
   hash-verified DejaVu Sans Bold file; no OS font substitution is accepted. The exact-section investigation is
   `research/cloud-polish/PANEL-THIN-SPOT-REVIEW.md`. No physical gate is closed by this correction.
5h. **r5 (J7-R) lens support** (`checks.py`, last section; R5-BRIEF choice 9; all four are J7 `required_checks`, so
   their rows gate `critical_features` through the J7 joint row):
   - `j7_float`: at s 0, 1.25 and 3.0 the camera body, the BFAR and the adapter are measured against every part of the
     final state except the hanging unit itself (camera, adapter, lens): overlap <= 0.05 mm3, lateral and axial gaps
     >= body 0.5 / 0.4, BFAR 0.6 (radial) / 0.4, adapter 0.6 (radial), and the plain minimum >= the smaller rule.
     The lens may touch only the collar, and never the camera at any s. A row downgrades to stub only if every actual offending obstacle is a stub; an unrelated stub cannot relabel a real failure. Per-s minima in `checks.json` and the receipt
     (`j7_float_min`).
   - `lens_support`, every lens incl. the data-only Computar: FAIL without a support band at any mass (the collar is the only J7-R anchor); the band is
     fixed (no moving segment over it), its clamped length >= 5 (a zoom >= 15), bore - band 0.2..0.4 diametral, the
     collar front >= 2.0 behind the first moving ring, the band inside the collar, the seat at C + band x0 on the cone.
     On each lens's own built collar: lens seated (0 mm3, gap <= 0.01), bore and seat radii by exact rays, 0 mm3 against
     the thumb-screw keep-outs. The rear bore has a 1.6 mm axial land, checked by exact chords 0.03 mm into the
     actual measured rear bore edge (not just the nominal corrected radius). This truncates the unused cone
     feather without changing the band seat. A production lens with insufficient room FAILs; the data-only
     Computar is explicitly unbuilt/unsupported pending a separate entry design and cannot export a collar.
     A band status other than `'measured'` is a WARN (an info row with a `warn` text).
   - `lens_clamp` (`layout.LOAD_MODEL`, estimates until G-COL-1 / G-CAM-2): FAIL if the lens axis is less than 10 inside
     the anchor polygon TL-TR-LR-LL, or if the slip moment M_sep = (pi / 6) F L (F = pinch 120 N x relaxation 0.5,
     L = clamped band length) is below 1.5 x the static moment of lens + camera + adapter about the band. WARN if
     M_sep is below the 5 g moment, if the 5 g aim change at the tub face exceeds 0.3 deg, or if the 5 g top-anchor
     tension exceeds the 100 N assumed relaxed allowance. The anchor screen now solves the three bolted feet with LR inactive,
     bounds simultaneous full axial and arbitrary-direction bending at 5 g, and applies a provisional prying factor 2.0.
     It exposes per-anchor reactions and retains the old nominal estimate for comparison. Invalid factors or a
     degenerate bolted support model FAIL; no computed number is a measured pull-out rating.
   - `inserts` (kind M3): bore dia 4.0 +-0.1 open at one end, depth >= insert + 0.2, wall >= 1.6, engagement >= 3.0,
     the tip and tip + 0.2 in a void (no bottoming), the washer seat, >= 1.6 under the washer, the head-side
     clearance hole.
   - `lens_support` and `lens_clamp` are info-neutral categories (>= 1 pass, no fail); their WARNs are listed in the
     category summary, the receipt (`warnings`) and the build log. They never block.
6. The straight-driver audit above.
7. Insertion sweeps for `INSERTIONS`. The snaps listed per insertion may deflect. Cables are ignored where listed.
8. Mass and CoM from the solids (ASA 1.07 g/cm3 x `INFILL_FACTOR`) plus COTS masses, for both lenses. Report:
   - the CoM ahead of the grip axis x -47;
   - its height above the grip top z -8.
   The concept estimates were +1.5 mm (Kowa) and -8.3 mm (Fujinon + sleeve); the lens now sits 1.1 mm further
   forward. **r5:** each lens is weighed with its own collar, and the real camera model puts the lens 10 mm further
   rearward (C flange x +0.6): Kowa 895 g, +1.5 (r4 +3.73); Fujinon 782 g, -9.8 (r4 -8.89). The mass_com rules are
   unchanged (R5-BRIEF choice 10); judge 3's proposed WARN band outside 0..+8 is **not** added (the Fujinon would
   WARN at -9.8).
9. `layout.self_check()` passes. `cad_release_candidate` (r2 name; was `release_candidate`) is true only if every
   check passes, `critical_features` passes and no printed part is a stub. It is a computed CAD state only: the receipt
   carries `status_states` (`cad_checks` computed; `slicer_review`, `coupon_validation`, `measured_fit`,
   `assembly_operation` from evidence records) and print time and mass are labelled estimates. **r3 summaries:** a row
   status other than pass / fail / stub / info is rejected (category fail, listed in `unknown_statuses`); an
   informational category (`critical_features`, `removals`) passes only with at least one pass row and no fail or stub
   row. The receipt and `checks.json` carry `variant` (`layout.FR_STATE`; None for the baseline).
10. **Evidence (r3, audit 2026-10-05 s2).** Hardware evidence is a structured JSON record per tested item under
   `evidence/` (format: `evidence/README.md`, template `evidence/_record-template.json`): `item` (exact part id or gate
   id), `state`, `artifacts` {path: sha256 of the STL / source actually tested}, `profile`, `verdict` (pass / fail),
   `date`, `by`, `notes`. File names are never read as evidence. Per item the build reports completeness (a current,
   valid record exists) and the outcome: pass, fail, conflict (current records disagree), stale (a recorded hash differs
   from the current production STL, coupon STL or source; r1 and earlier records are stale) or not run. A slicer-review
   record must name the part's current production STL (`stl/<part>.stl`); a coupon artifact never satisfies a
   production part. A coupon record must name every coupon STL of its gate (`coupons-manifest.json`). Required items:
   slicer_review = every printed part (r5: 12, with the lens collar); coupon_validation = G-PT-1, G-KEEP-1, G-PANEL-1,
   G-CAP-1, G-EVF-2, G-SNAP-2, (r5) G-COL-1 and the PRINT-GUIDE s6 calibrations **G-KNOB-1** (knob D-bore ladders), **G-COMB-1** (clearance comb), **G-J4-1** (J4
   tongue + keyhole slot); measured_fit and assembly_operation = the remaining gate ids of the gate docs (r5: G-CAM-1
   and G-LENS are measured_fit; G-CAM-2, the sag acceptance on the assembled camera, is assembly_operation, so it is
   bound to every production STL; `build_d2.STATE_GATES`). A state stays
   in `open_evidence` until every item has a current pass; failed, conflicting and stale item ids are named there.
   The build reports person-recorded verdicts; it never judges them, and it never closes a hardware gate.
   **r3 fix-baseline (verifier review of the r3 baseline):** a measured_fit record must name its gate's acceptance doc
   (repo-root path from `build_d2.gate_doc`: EVF-G* -> `electronics/gs8-evf-v1/EVF-SELECTION.md`, G-W* ->
   `electronics/gs8-d2-v1/WIRING.md`, else `cad/gs8-d2-v1/MEASURED-PARTS.md` or `SPEC.md`); an assembly_operation
   record must name that doc and every production STL `stl/<part>.stl`, so a doc or geometry change makes it stale.
   Any rejected record of an item gives the outcome `rejected` and keeps the item open (a malformed FAIL never
   disappears behind a valid pass); a record of a valid state naming an unknown item (`unmatched_records`) keeps that
   state open; a record that reaches no state (unreadable JSON, unknown state and unknown item) is listed in
   `evidence.rejected_records` / `unassigned_records` and in `open_evidence`. An empty check category summarizes as
   fail (`service_driver` keeps its explicit, stated override). `CRITICAL_JOINTS` must contain every
   `layout.REQUIRED_JOINT_IDS` id (12) unless a fork joint names it in `replaces`; a joint whose coverage is complete
   but rests on a physical gate (J6, G-CAP-1 flexures) reports `info`, not `pass`.
   **r4 (audit 2026-10-05-r3):** (a) a record field of the wrong type (an array `state`, an object `item`, a non-text
   `profile` / `date` / `by`) is rejected and kept visible, never a crash; (b) a fork joint can stand in for a required
   joint only if it is itself a `CRITICAL_JOINTS` entry with required features that validated (a pass, or complete
   coverage resting on a named physical gate); a replacement declared only in `FR_JOINTS` waives nothing; (c) the
   coupon gates that also cycle whole printed parts are split: `G-SNAP-2/whole`, `G-KEEP-1/whole` and
   `G-PANEL-1/whole` are assembly_operation items (doc + every production STL), and the gate reads `recorded pass`
   only when its coupon item and its `/whole` item both pass; (d) a slicer-review record must also name the part's
   modifier meshes (`stl/modifiers/<part>__mod_<id>.stl`, exported by the build from `layout.print_modifiers`).
   New check categories: `cable_routes` (every cable route is one continuous chain of keep-out boxes with a passage
   >= 1.0 x 1.0 between neighbours, its ends reach both end parts within 1.0, and an estimated route length plus a
   service allowance of max(10 mm, 10 %) fits the cable; bend radius is not checked by CAD) and `print_modifiers`
   (every modifier mesh overlaps its part).

## 7. Cables and keep-outs

There are 10 cables (layout `CABLES`), each with both ends, its keep-out chain and the steps when it is plugged. There
are 27 internal keep-outs (`KEEPOUTS`; FIXER A-F4 added ko_lead_wall, ko_lead_cross, ko_run_cross, ko_fps_up,
ko_pig_wrap and ko_pig_under so that every lead body has reserved space; oled_flex and fan have none: the flex moves
with the tethered OLED + board pair and the fan lead stays on the cooler). They are the concept's keep-outs shifted by -77 in x, with these changes:
- y is clipped to 32.0, inside the panel;
- ko_sd is extended through the hood plate;
- ko_fpc_cam is moved to the new camera rear face (x -29.7..-24.67); r5: re-derived from the real cover over the
  whole s range, x -32.07..-24.04, y -8..8, z 39.4..47.0.
- r5 adds `ko_lens_thumb_focus` (x 13.1..16.9) and `ko_lens_thumb_iris` (x 31.7..35.5), +-24 round the axis: the swept
  envelopes of the default lens's 2 M2 thumb screws, which the collar must clear (KEEPOUTS now 35).

The 2 exterior keep-outs are the tripod clamp and the driver model.

## 8. Decisions carried from the concept (unchanged)

- **Look.** Silver ASA tub and panel; a black hood (roof, eyepiece housing, front plate; r5: the turret is gone and the
  black lens collar takes its place and look); a black 8 mm base
  and grip. (r2: the concept's 16 mm black band, base + skirts to z +8, is now the 8 mm base only, because the skirts
  are eliminated; a user-visible change, see RECTIFICATION.md finding 3.)
- **Proportions.**
  - Body 154 x 70 x 100 with R5 vertical edges.
  - Lens axis z 60; EVF axis y 16 / z 78; dial line z 57.
  - Dials at x -63 (exposure, 28 mm) and x -123 (18/24, 20 mm).
- **Grip and base.** Grip 30 x 48, er 9, front face 23 mm behind the plate, z -8..-110, with a cap that slides
  forward to open. Base to x -0.5 with a 5 mm chamfer; (r1: skirts 1.6 thick to z +8; eliminated in r2).
- **Pi stack.** Flat on the floor, USB end to the rear, X1203 below: x -91..-6, y -32.3..23.7.
  - The Pi edge stands 0.8 mm behind the front wall.
  - The stick leaves through a rear scoop; the microSD through a front slot.
- **Fasteners.** 4 x PT 3.0 x 12 PH1 in the concept positions (r2 adds 2 more of the same, s_k1/s_k2, for the Pi keeper):
  - s_b1 / s_b2 at x -91 / -105, y 27.85, driven up through 6 mm counterbores;
  - s_r1 / s_r2 driven from the right.
  - X1203 kit hardware.
- **Controls.**
  - Run: red cap 2.5 mm proud in a 12 x 28 pad.
  - Exposure: endless encoder, I2C 0x37.
  - 18/24 rotary.
  - Power: a plunger onto the Pi button, plus the logind/2 s daemon (electronics layer).
  - I/O = exposure dial (encoder, with its push switch), 18/24 dial, power plunger (on/off), run (record) button and the EVF; **no LED indicators** (user decision 2026-10-05: the plunger is black ASA, no light pipe; the Pi 5 onboard LEDs are switched off in config.txt; power-on and shutdown are shown on the EVF, WIRING s8).
- **Thermal.** Roof inlet over the blower; exhaust in line with the fins (front band, corner field, right-wall slots,
  baffle).
- **Tripod and strap.** Socket at x -107 (concept -30). Hand strap on the right side, from the base edge to the
  grip heel.

## 9. Concept numbers changed, and why

| Item | Concept | D2 release | Why |
|---|---|---|---|
| Frame origin | x 0 at mid-length | x 0 at the front-plate face (x - 77) | task datum; `cx()` converts |
| Hood assembly | slides back over the mount ring | drops straight down (-Z), 4 snap hooks | the front plate and the eyepiece housing embrace the tub ends, so no X slide is possible |
| Step order | camera 5, EVF 6, hood 7 | hood 5, EVF 6, camera 7 | a dropping hood cannot pass a mounted camera ring; the camera now goes in from the open left side |
| Camera stack | 38 sq body, dia 30 mount ring, collar bore dia 30.4 | r1-r4: 39.5 sq lands, dia 36 back-focus ring (rotating) + dia 30.75 CS ring + 5 mm C-CS adapter; wall/plate/turret bore dia 36.5. **r5:** the official GS drawing: adapter dia 30.75 x 5.0 face to face, BFAR head dia 36 x 1.2 on a fine thread (about dia 28.8), round housing dia 35.5 x 10.35 with a split lock tab on top, PCB 38 sq x 1.4, plastic rear cover 39.5 sq x 6.49; tub lip dia 32.4 + counterbore dia 37.5, hood plate bore dia 36.5 over x -2.8..+0.3 only | r1-r4 followed the stills R1 record, which has no front 39.5 land (39.5 is the rear cover); r5 follows the Raspberry Pi drawing (research/m12-drawings/gs_side.png) |
| C flange / lens | x +9.5 | r1-r4 x +10.6; **r5 x +0.6** | r4: the 15.8 mm stack ahead of a seat that does not exist; r5: BFAR face x -4.4 + the 5.0 adapter |
| Camera retention | pins + collar | r1-r4: 2 pins (dia 1.9) + a panel keeper finger 0.2 behind the cover. **r5: J7-R float**: the lens collar holds the lens; the camera hangs on the lens; lip, roll fin and keeper are catches with gaps | r4's pins ended about 7 mm short of the real PCB and located nothing; a heavy lens hung on the camera's own mount (R5-BRIEF) |
| Eyepiece flange F | x -154.2 | x -154.0 (on the rear face) | F must seat on a datum face; display plane x -148.0 |
| Eyepiece housing | 43 x 44, 2.0 walls, closed +Y side with a 10 mm cut | 43 x 45 (z 55..100), walls 1.6 / top 1.5, +Y window x full, z 66..90; 0.2 gap | 1.25 radial round the knurl (EVF-SELECTION risk 5); the barrel stands 0.25 past y 35 |
| Hood band | z 97.5..100 (0.2 above the walls) | z 97.3..100 (rests on the wall tops) | defined seat |
| Turret bore | dia 30.4 | r1-r4 dia 36.5; **r5: no turret** (the lens collar replaces its look and envelope) | back-focus ring; r5: the collar carries the lens |
| Panel tongue | x -142..-12 | x -134..-12 | clears the EVF board slot |
| Base joint | 2 tongues 6 x 48 x 2.7 at x -29 / -79 | T-tongues 8 long (head 36, neck 26) at x **-18** / -79 | the old front tongue sat on the run-lead floor hole; a T section is needed for lips |
| Base top | z 0.2 | z 0.0 (contact with the floor) | sketch overlap |
| Skirts | one print with the base | r1: 2 separate strips on dovetails; **r2: eliminated** | base + skirts + grip has no support-free orientation; r2: the skirt barb made panel opening depend on an inaccessible latch and the J5 key/groove was 0.68-0.77 thick (findings 2, 3) |
| Panel bosses / posts | 7 wide / 7 x 7 | 8 / 8 x 8; boss bottom z 2.6 (0.1 gap); post ends 0.1 off a 2.0 wall pad | PT boss OD 8 (M3 insert fallback needs 7.6) |
| Lip | 2.5 thick, plain | 2.8 thick (flush with the panel), 2 notches for the bosses | the panel bosses must pass the lip as the panel goes on along -Y |
| Pi retention | bosses + "posts" | r1: 4 bosses with head pockets + 4 floor snap hooks; **r2: the same bosses + a removable printed keeper on 2 PT screws** | nothing held the stack down; r2: the hooks had no release access (finding 1) |
| Floor pigtail hole | 7 x 7 | 11 x 9 | the XT30 plug must pass |
| Plunger | face 2.5 behind the plate, axis y 8.5 z 21.5 | face 1.3 behind, axis y 9.0 z 20.5, flange in a hood pocket | the 0.2 hood gap and 0.8 Pi gap leave no room for a stop flange; SD slot and exhaust web >= 1.2 |
| Exhaust band | z 25.6..29.8 | z 25.9..29.7 | 1.2 web over the plunger pocket; below the turret (r1-r4) |
| Tripod nut | z -7.2..-1.6 | z -5.7..-0.1, pressed from the top | 2.3 mm bearing wall under the nut (the tripod pulls the nut down) |
| Strap upper anchor | slot at x -77 near the base edge | 2 slots at x -76.5 / -82.0, y -34..-21 + webbing recess; 2 heel slots | a real webbing loop; clear of the tongue pocket |
| Engraving text | 2.2-2.7 high | 3.0 minimum | 0.4 nozzle on the bed face |
| Eyecup | cup only, 0.3 off the barrel lip | + 3.0 mm sleeve over the eye-end body (dia 36.7), 0.3 interference | nothing held the cup on |
| rib_r | y -27.4..-23.6 | y -32.5..-23.6 (grown from the right wall) | prints without support |
| rib_l | z 2.7..45 | z 2.5..41; 45 deg gusset to the panel plane ending in a 1.2 land at x -12.1, y 31.0..32.2 (r3 USER 2026-10-05: tip land 0.3 -> 1.2, was a 0.60 knife edge at x -13; probe tub_rib_l_tip in J7) | the camera's dia 36 ring passes over it at step 7; the tip was below MIN_WALL |

## 10. Open items and bench gates (CAD cannot close these)

- **G-LENS (Q1; r5 extended; MEASURED-PARTS MP-CAM lens line; before tub/hood/panel/collar printing).** Mark the Kowa knurl and
  turn focus and iris end to end: the knurl must not rotate, and a dial indicator on its rear face must read <= 0.02
  axial. Record the knurl OD (+-0.02), its rear-face position from the flange (+-0.05) and edge chamfer, the
  thumb-screw envelope, the CoM (knife edge), and that the 6.7 rear protrusion clears the camera's filter at the
  recorded s. The same for the Fujinon (its band is `'assumed'`) and for any zoom (fixed band >= 15 mm). Pass: inside
  the measured band x0/x1, OD/chamfer, moving-ring/thumb envelopes and CoM are recorded in LENSES and rebuilt,
  with band status 'measured'. Rerun all float/support/insertion/service checks and regenerate affected tub, hood,
  panel and collar before printing. Existing minimum gaps cannot absorb an unrecorded drawing-to-part offset. FAIL: no collar for
  that lens; fallback: a collar on the locked focus ring (refocus by unpinching), or Plan B below.
- **G-CAM-1 (r5: rewritten as MP-CAM; before the CAD is frozen).** Calipers on the real GS camera: BFAR head OD and
  thickness; the exposed BFAR face annulus outside the adapter (>= 0.8 radial for the lip catch); adapter OD and face
  to face (5.00 +-0.05); direct C flange to cover rear at s = 0 and at the set s (CAM.optics), so a hidden flange
  offset cannot silently consume the keeper gap; housing OD; lock tab width, top radius and depth, the lock-screw head side and size; the
  tripod block comes off with its 2 screws and leaves nothing below r 18; PCB and cover size and centring (+-0.2); s at
  Kowa infinity (bench step B0) and the total BFAR travel. Pass: all inside the `CAM` values (every `CAM['status']`
  entry), or CAM updated and rebuilt. Sensor height above PCB and filter focus shift stay unknown unless independently
  measured/sourced. The 1.25 nominal is an unconfirmed geometry sample; known optical inputs derive the nominal and
  known direct-stack measurements must agree within the declared 0.10 mm diagnostic tolerance. (r4's G-CAM-1 measured the hole diameter for the 2 pins; the pins are deleted.)
- **G-COL-1 (r5, coupons `collar_tub_front`, `collar_hood_plate`, `collar_part`; cloud-polish refinement).**
  Record the exact short/lug insert part and measured OD/length, filament, print orientation/settings and torque tool.
  Clear the collar's three print-only 0.2 mm membranes to 3.4 mm by hand; washer seat planes must remain flat.
  Assemble the actual coupon stack: tub front with inserts, hood plate, collar. The feet clear the dia 8.6 holes by
  >= 0.3. Torque s_c1..s_c3 first, at no more than the provisional 0.15 N m cap, then apply the s_c4 pinch at 0.2 N m.
  The order matches assembly; a freely deforming unbolted collar is not an equivalent clamp test. Record full washer
  contact, no cracked boss/ear/lug, and insert migration before and after a 100 N added axial proof load at each anchor
  for 60 s. This validates only that tested coupon/part/material, not a universal insert rating.
  With s_c4 loose the measured fixed band slides in. At 0.2 N m pinch require no slip under 1.0 N m roll or 50 N axial;
  3x lens mass at the lens CoM: a dial at the lens front reads <= 0.02 and returns. Repeat after 24 h at 50 C, recording
  movement and residual torque before any re-seating; no crack after 20 pinch cycles. Record actual torque/retention
  rather than increasing torque until an unknown insert strips. These results replace LOAD_MODEL estimates
  (pinch 120 N, relaxation 0.5, anchor allowance 100 N). M_sep assumes uniform pressure and is an upper-bound estimate;
  the bolted-anchor screen excludes compression-only LR and uses an explicitly provisional prying factor of 2.0.
  G-COL-1 and G-CAM-2 must resolve the Kowa 5 g warning; neither estimate is physical proof.
- **G-CAM-2 (r5, sag acceptance on the assembled camera).** Live view, f/1.8, slanted-edge or Siemens chart at about
  1 m, with the real production FPC length and fold installed (its spring load acts on the floating camera). Record best focus (or MTF50) at the centre and the 4 corners. Then (a) 3x lens mass hung at the lens front for
  10 min; (b) a 15 N side push at the focus ring; (c) 50 g hung on the camera cover; (d) 1 h at 50 C with (a). Pass:
  the corner-vs-centre focus difference changes by <= 4 um (1/3 of the depth of focus, about 0.1 deg) in every case;
  the aim shift is recorded (target <= 0.3 deg under (a)). Repeat once with the BFAR lock screw loose, to show that the
  camera carries no lens load.
- **Plan B (r5, documented only, not built).** If G-LENS shows that the Kowa band moves, judge 2's housing clamp is
  used instead (`research/r5-lens-support/design_2.md`, `judge_2.md` s2.2): a printed cradle in the tripod-block seat
  and a clip over the lock tab, 3 PT screws from the front, clamp the camera housing to the tub. It bypasses the
  housing-to-PCB joint but leaves the lens moment on the camera's own adapter and BFAR threads.
- **G-EVF-1.** Spigot pull-out at least 20 N with the cap clamp; the diopter turns freely; focus range with the foam pad.
- **G-PI-1.** X1203 edge parts clear of the 4 keeper finger zones (same 4 stations, 0.65 over the edge, z 7.7-9.3).
  Kit standoff length (10.9 assumed). Kit screw head at most dia 5.0 x 2.0.
- **G-PLG-1.** Pi button height (z 21.0 assumed) and travel. The plunger presses 0.35 of 0.45.
- **G-PT-1.** PT strip torque in printed ASA bosses on a test coupon. Sets the 0.35-0.5 N m range; see
  FASTENER-POLICY. Covers the 2 keeper bosses (pilot horizontal in the print, the weak case).
- **G-SNAP-1.** Withdrawn in r2: the Pi floor hooks are deleted.
- **G-KEEP-1 (r2; whole keeper since the r2 fixer).** `coupons_r1.GATE`: the whole printed keeper, a tub floor coupon
  with both keeper bosses and the 4 Pi bosses, and 2 flat stand-in boards on the real X1203 kit: 5 full service cycles
  (keeper in along its path under the Pi board, s_k1 and s_k2 in and out), finger gaps 0.05-0.3 at all 4 fingers, 20 N
  lift of the stand-in with no finger set. **r4 split:** the coupon part above is the coupon item `G-KEEP-1`; the
  5 keeper cycles on the real Pi + X1203 stack in the printed tub and the far-corner tilt test are the separate
  assembly item **`G-KEEP-1/whole`** (bound to this document and every production STL). The gate passes only when both
  have a current recorded pass.
- **G-SNAP-2.** Hood hook + ledge (hk1 with its release hole; r2 fixer adds hk3 with the 45 deg return) and one
  encoder cradle hook: 5 click/release cycles each, no whitening or set (beams print along Z, bending across the
  layers); the 1.5 pin holds hk1 open by friction and comes out by hand; hk3 cams out under a straight pull. **Plus 5
  remove/refit cycles of the whole printed hood on the tub** (s7 item 9). (The r1 skirt barb part is withdrawn.)
  **r4 split:** the hook, ledge and cradle coupons are the coupon item `G-SNAP-2`; the 5 whole-hood cycles are the
  separate assembly item **`G-SNAP-2/whole`** (bound to this document and every production STL, so a changed hood or
  tub makes it stale). The gate passes only when both have a current recorded pass.
- **G-PANEL-1 (r2).** Panel open/close with the PH1 only, 5 cycles, strap fitted (coupons base_edge_*). **r4 split:**
  the base_edge coupon fit is the coupon item `G-PANEL-1`; the 5 cycles of the whole printed panel on the assembled
  body with the strap fitted are the separate assembly item **`G-PANEL-1/whole`**. The gate passes only when both pass.
- **G-CAP-1.** Cap detent: 20 slides, detent hold, 20 N pull-down (coupons cap_retention_*).
- **G-EVF-2 (r2).** EVF +Y stop: feeler 0.1-0.5 between the panel rib and the real board edge; the stop bears on bare
  laminate, not on the HDMI receptacle or the OLED flex. With the real micro-HDMI plug fitted, push the board -Y, +X
  and +Z by hand: the PCB edge must stop first (r2 fixer: in CAD the rails stand >= 0.6 off the plug envelope and
  0.75 off the ZIF; the r2 -Y contact share on the receptacle is gone).
- **G-SKIRT-1.** Withdrawn in r2 (no skirts).
- **G-RUN-1, G-ENC-1** (DESIGN s9) and the purchased-part gates G-MP-PACK, G-MP-X1203, G-MP-EVF, G-MP-ENC, G-MP-SW,
  G-MP-STICK (`MEASURED-PARTS.md`); electronics G-W1 to G-W13 (WIRING s9; G-W12 = the full-workload power test; G-W13 = the EVF feed regulator bench qualification, r3).
- **G-HDMI.** The 90 deg plug stands at most 8.5 mm off the board (Q2). Also the encoder shaft length and the
  rotary-switch bushing and tab (estimates).
- **Mock-ups.** Nose at the 33.6 mm cup, strap length, warm exhaust on the left palm (concept Q4).

## 11. Ownership notes for the build owners (where this contract differs from the owner task text)

- **The panel groove is in the hood, not the tub** (J2). The tub has no top member on the left. The "rebate holding
  the hood's left edge" (panel task) is the same joint, seen from the panel.
- The tub carries the 2 right-wall pads and counterbores. The posts belong to the panel.
- `printed_grip.py` builds 2 ids: `base_grip`, `cap` (r2: the skirts are eliminated). `printed_keeper.py` builds `pi_keeper`.
- r5: `printed_collar.py` builds `lens_collar` (owner tub) for any lens with a `support` band
  (`build_part(L, 'lens_collar', lens=None)`, default `L.LENS`). The 3 tub insert bosses, the lip and the counterbore
  are tub features; the 4 foot holes and the roll fin are hood features; the camera keeper stays a panel feature.
- The camera keeper finger and the EVF cap are panel features. The EVF cell, saddle bore and board slot are tub
  features.
- The plunger flange pocket is a hood feature; the plunger stem hole is a tub feature.
