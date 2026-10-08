# GS8 D2 release layer: working notes

This is a shared log for the spec owner, the 5 build owners and the integrator. Each owner appends under their own
heading. Interface requests go in the section at the bottom: never edit another owner's file or `layout.py`.

**Time:** the machine clock shows Singapore time; Batam (WIB) is 1 hour behind.
- **Hard stop at 15:20 machine time (14:20 WIB).** Finish the current edit, append done / half-done / next step here,
  and end the turn.
- Do not start a CAD run that cannot finish before the hard stop.

**Commands** (from the repo root `C:/Users/Pre-Installed User/Claude/Projects/8mm`):
- Layout self-check (plain Python, no CadQuery): `python cad/gs8-d2-v1/layout.py`. It runs 120 checks; 0 failed
  at 11:37.
- Helper smoke test: `.venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/test_common.py`.
  - Runtime: about 8 s, writing `out/test_common.json`.
  - Result: 18 of 18 helpers ok at 11:33.
  - The fillet fallback was exercised on purpose.
- Every CadQuery/OCP process goes through `run_locked.py`: in the foreground, Bash timeout up to 600000 ms, never a
  background wait.

## Spec owner (2026-10-04, 11:02-11:40 machine time)

**Done.**
- `layout.py`: the single source of truth, importable with no CAD dependency. It holds:
  - the frame;
  - the FDM rules;
  - body and part envelopes;
  - joints J1-J15;
  - 4 PT screw stations;
  - the lens parameter;
  - 20 COTS rows, 9 cables and 21 keep-outs;
  - `PARTS` (12 printed), `MATES`, `STEPS` (10), `INSERTIONS` and the `MODULE_CONTRACT`;
  - the helpers `present_at`, `screw_audit_set`, `mass_g` and `self_check`.
- `d2_common.py`:
  - FDM constants re-exported from the layout;
  - helpers: `box_solid`, `cyl_solid`, `pt_boss`, `counterbore`, `snap_hook`, `snap_strain`, `keyhole_tongue`,
    `keyhole_slot`, `dovetail`, `vent_slots`, `engrave`, `bed_chamfer`, `teardrop`, `safe_fillet`,
    `safe_chamfer`, `wp_of`, `to_print_pose`.
  - Each helper was tested once (`test_common.py`).
- `SPEC.md`:
  - frame and datums, parts, the interfaces table, print rules;
  - assembly order with the parts present at each step, the checks list;
  - decisions carried from the concept, every changed concept number (s9), bench gates;
  - ownership notes (s11).
- `FASTENER-POLICY.md` (D2 PT policy plus the M3 insert fallback and the X1203 kit).
- A box-level clash and sweep screen of the interface features. It found 2 real problems, now fixed:
  - rib_l top lowered to z 41;
  - the camera insertion path now runs 2 mm high.
  All remaining box overlaps are declared mates (tongue/groove, cap clamp, hook teeth over the X1203, lip notches).

**Half-done or left to the owners.**
- Real geometry inside the envelopes (the owners).
- The X1203 / camera / eyepiece hardware facts are proxies. See the bench gates in SPEC s10.

**Next step:** the build owners implement against `MODULE_CONTRACT`; `build_d2.py` runs SPEC s6.

## Watch-outs for the build owners (from the spec work)

- **tub** prints on its right wall, with +Y up.
  - Anything inside the tub that does not grow from the right wall needs a -Y face at 45 deg or steeper.
  - The tongue helper already chamfers its -Y end.
  - The lip needs 2 notches (`LIP_NOTCHES`), or the panel bosses cannot pass.
- **hood** drops straight down. Hooks hk1-hk4 are generated with `d2_common.snap_hook`; the test call in
  `test_common.py` shows the arguments for hk1.
  - The housing wall is 1.6 and its top wall 1.5. Keep 1.25 radial round the barrel.
  - The +Y window runs the full housing length.
- **panel** goes on along -Y. Every panel feature sweeps from y +70 to its final place:
  - keep the cap's clamp face inside its envelope;
  - the keeper finger stops 0.2 behind the camera cover (x -24.67).
- **base_grip** prints upside down.
  - The keyhole windows sit 10 mm AHEAD of the final tongue positions (`TONGUES[i]['base_window']`).
  - The nut pocket opens on the base top.
- **Pi hooks:** about 3 % strain at 0.65 reach. If the owner can lengthen the beam (deeper floor relief, U-spring),
  do it, and say so here.

## tub owner

**2026-10-04 12:40 (machine time). `printed_tub.py` built; part check `build_d2.py --part tub --fast` passes contract,
thin wall, bed, STL mesh, keep-outs, COTS interference and mate overlap. It fails only 2 sweeps, both caused by
layout interface numbers (requests below).**

Done:
- `tub`: one valid solid, 105 246 mm3. Mass is 112.6 g at 100 % and 95.7 g at the shell infill factor 0.85.
  Builds in 1.3 s.
- Print: face down -Y (the right wall on the bed). The print box is 151.3 x 101.0 x 70.0 and fits both beds.
- Supports: only 2 small paint-on blocks under the -Y wings of the 2 T-tongue heads. The T undercut faces the bed,
  and the 45 deg chamfer in `keyhole_tongue` leaves a 0.65 feather that still prints in mid-air, so the module calls
  it with `chamfer_minus_y=False`.
- Every other feature either grows from the right wall or has a 45 deg underside, or is a bridge of 20 mm or less.
- Features: shell (R5, with 45 deg flats where the R5 meets the bed), lip + 2 notches + a 45 deg lip gusset, 2
  tongues, floor holes, 2 s_b clearance holes, 4 Pi bosses, 4 Pi hooks, camera bore (teardrop) and 2 pins, rib_l,
  plunger hole, SD slot, 2 exhaust windows, 4 hood catch ledges, EVF teardrop bore + -Y half-collar (saddle) with a
  45 deg chin, OLED cell (window 10 x 8), EVF board slot (2 rails from the right wall), stick scoop + guide, 2 PT
  pads + counterbores, and right-wall vents. The bed edges get a 0.6 chamfer.
- Tests (all run through `run_locked.py`):
  - `test_tub.py` -> `out/test_tub.json`: 0 keep-out overlap and 0 overlap with non-mate COTS boxes.
  - `sweep_tub.py` -> `out/sweep_tub.json`: insertions against the tub alone. panel_on, board_in, oled_in,
    eyepiece_in and stick_in are all 0 mm3.
  - Pairwise at 12:43 against the current printed_hood / panel / grip / small modules: 0 mm3 with every part.
    The top board rail was lowered to z 94.0 (0.3 under the hood's right-edge lip, which overlapped by 5.3 mm3).

Deviations from the layout. All stay inside TUB_BOX and are recorded in the module docstring:
- Pi bosses: OD 7.0 -> 8.8. At 7.0 the dia 5.6 head pocket leaves a 0.7 wall, and the loaded zone needs 1.6.
- Pi hooks:
  - t 1.4 -> 1.6;
  - root z 1.0 -> 1.2, so the floor under the relief keeps 1.2;
  - each hook is a slab leaning 45 deg away from the board, so it prints with no support and its ramp is the lead-in;
  - the USB pair is tapered (-Y end at 45 deg).
  - Catch z 7.7, gap 0.25 and reach 0.65 are unchanged. Strain is 2.6 % (the layout's straight 6.7 beam gives 3.0 %).
- rib_l: a 45 deg gusset from the front wall out to the panel plane (y 24.1..32.2, z 2.5..41). It is notched
  x -6.7..-5.2, z 39.85..41 for the panel front locate rib, so it is compatible with hood_panel request 2 either way.
- rib_r: **omitted**. It lies in the Pi stack drop path (see request T3).
- BAFFLE: **not built**. Its box (x -9.4..-5.2) lies over the Pi PCB edge (x -6.0), so any wall there blocks the
  stack drop. The exhaust is the front-wall windows plus the right-wall slots.
- "Lens collar": the front wall's seat land round the dia 36.5 bore. A proud collar is impossible: the lands seat on
  X_FW_IN and the hood plate is 0.2 off the outer face. The 2 load ribs reduce to rib_l (see rib_r).
- EVF board slot:
  - the bottom rail's -X groove wall exists only for y 0.7..3.7, because the board's HDMI receptacle sweeps through
    it (same finding as cots_build 12:25);
  - the +X wall stops below y 1.8 (ko_5v_end) and above y 18.9 (the switch_1824 box);
  - the board is held by the top groove (both walls), the bottom floor and the +X wall. Add this to bench gate
    G-EVF-1.
- Stick guide: a 4-sided channel from the scoop back (x -144) to x -131.5 (ko_5v_up), then a floor rail with a
  45 deg +Y lip to x -94.5. The upper and -Y walls are not possible there: ko_usb_evf.
- Panel groove (named in the owner task): it is in the hood per SPEC s11, so the tub has none.
- Plunger: if `PLUNGER['flange']` x0 moves to -2.5 (grip_small request 3), the module cuts the 0.4 deep recess
  (hood-pocket footprint) in the front-wall outer face by itself (stop = flange x0 - travel).

Half-done / open:
- Thin-wall "min 1.199": the 1.2 floor skin under the hook reliefs. It passes the screen (share 0).
- The overhang screen reports 3592 mm2 of downward faces. These are bridges (slot and window tops, the scoop and
  hollow roofs, the counterbore shoulders, the cell -Y wall) plus the 2 tongue wings. No print sliced.
- Nothing is printed or measured. The X1203 / Pi / camera numbers are proxies (SPEC s10 gates).

Next step: the integrator decides T1-T3 below. With them, `--part tub` should pass all sweeps; `sweep_tub.py`
already shows 0 mm3 for both proposals.

## hood_panel owner

**2026-10-04, 11:40-12:20 machine time. Done:** `printed_hood.py` and `printed_panel.py` (MODULE CONTRACT: `build`,
`build_part`, `PRINT`, module `NOTES`), plus the owner test `test_hood_panel.py` (validity, volume, mass, envelope, print
pose and bed fit, overlap with every keep-out and non-mate COTS box, and sweeps: panel_on vs hood in 1 mm steps,
hood_on vs the plunger, eyepiece_in vs the hood; lens + camera cylinders vs the hood). All computed results are 0 mm3
overlap. `build_d2.py --part panel --fast`: pass. `--part hood --fast` (12:16): fails only on the envelope (request 1 below):
all keep-outs, COTS interference, thin wall, bed and mesh checks pass.

| part | volume | mass est. (x0.85) / 100 % | face down | print box | supports |
|---|---|---|---|---|---|
| hood | 66 911 mm3 | 60.9 g / 71.6 g | +Z (roof) | 178.7 x 67.3 x 99.7 | turret upper half; housing window sill (tree, from outside) |
| panel | 51 031 mm3 | 46.4 g / 54.6 g | +Y (face) | 150.3 x 94.4 x 65.4 | none |

**Hood features.**
- Roof band, with a 0.6 bed chamfer and a 3.0 x 45 deg front-top chamfer (concept fillet 5; no fillet on the bed).
- Front plate: R1.4 vertical edges and an R1.5 foot.
- Turret dia 60 / 57 with fillets 0.8 / 0.6. The bore is dia 36.5 with a 1.0 truncated-teardrop flat toward -Z and a
  0.5 front chamfer.
- Eyepiece housing, 16 deep:
  - R6 bottom corners and 3.0 top chamfers; 0.8 rim chamfer.
  - Interior: 45 deg flanks tangent to the 1.25 radial clearance circle, a 15.2 bridge, and top-corner gussets.
  - +Y window x full, z 66..90.
- 4 J1 hooks (snap_hook, 0.5 into the band; strain 1.6 %).
- J2 rail block: groove as the layout, back web to y 23.9, and 6 piers 3 wide that make the lip 21 mm bridges.
- Roof rib y 8.4..10. A down-turned right-edge flange (1.6 x 3), gapped 6 either side of hk1/hk2.
- Plunger: flange channel + pocket, opening, and a raised guard rim (1.0 proud, 1.2 wide, 0.8 chamfer; well 2.3 deep).
- SD slot; exhaust band + corner slots; roof inlet (7 slots).

**Panel features.**
- Wall with R5 ends (45 deg facet at the bed) and a 0.6 bed chamfer.
- 2 bosses (8 x 10.9). Their tabs fill the lip notches; PT pilots run 8.4 deep from z 2.6.
- 2 posts 8 x 8 with 4 mm root gussets (3.5 at the rear wall); pilots 11 deep from y -30.4.
- 5 tongue teeth with 0.4 lead-in.
- Encoder hole dia 7.5 and switch hole dia 10.0, both with a 0.4 countersink. Anti-rotation slot 1.7 x 3.0 x 2.0
  (blind, 0.8 skin) at r 7.9, 12 o'clock.
- Encoder cradle: 3 hooks, strain 1.5 %.
- J3 ribs. Keeper finger + root gusset (8 x 12). EVF cap: U clamp r 14.4 from x -151.4 to -148.2, then a solid OLED
  finger to -145.0.
- All 10 engraving items, 0.4 deep, in the bed face.

**Open issues (not changed; for the integrator).**
- The band's right edge (layout `HOOD['y'][0]` -32.0) leaves a 0.5 open slit to the right-wall inner face (-32.5)
  along the whole roof. The new flange stands behind it.
- The hood needs 2 tree supports (above). Every other overhang is bridged or at 45 deg.
- The 45 deg facet at the panel's R5 ends (2.1 long at the bed) does not match the tub lip's plain R5 below z 7.9.
- Not yet checked against the tub (`printed_tub.py` absent at 12:15): J1 ledges, J3 ribs vs the tub walls, the
  rail/flange vs tub internals at z > 90, the cap vs the OLED-cell walls (must stop at y <= 24.0).

**Next step.** Rerun `test_hood_panel.py` and `build_d2.py --part hood/panel --fast` once the tub module lands, and
adopt whatever the integrator decides on requests 1-5.

## grip_small owner

(2026-10-04, 11:40-12:20 machine time.) Files: `printed_grip.py` (base_grip, skirt_l, skirt_r, cap),
`printed_small.py` (plunger, knob_exp, knob_fps, eyecup, stick_sleeve), self-test `test_grip_small.py`
(`out/grip_small_test.json`; set `GS_PAIRS=1` to also test against the hood/panel/tub modules that exist).

**Done (computed, not printed or measured).**
- All 9 parts build as 1 valid solid each, in about 2 s together. `build_d2.py --part <id> --fast`:
  base_grip, knob_exp, knob_fps and eyecup pass; skirt_l/r and cap fail only the envelope check (requests 1-2);
  plunger and stick_sleeve fail only the thin-wall check (layout numbers, request 3).
- Volumes / mass at 100 %: base_grip 90 171 mm3 / 96.5 g (57.9 g at the 0.6 factor); skirt 3266 / 3.5 each;
  cap 6661 / 7.1; plunger 272 / 0.3; knob_exp 4801 / 5.1; knob_fps 1258 / 1.3; eyecup 4406 / 5.3 (TPU);
  stick_sleeve 1104 / 1.2. Every part fits both beds.
- Self-test: 38 feature probes pass. Interference is 0.000 mm3 for base/skirts, base/cap, base/both tongues, and
  for every part against hood and panel. The `base_on` sweep is 0 against both tongues. The `cap_on` and skirt slides
  show only the intended detent rub (0.13 and 1.3 mm3).
- Owner design choices (all inside my parts, documented in the module docstrings):
  - **J5 skirt joint.** The dovetail now has a diamond head with a straight neck: neck 0.4 at w 0.8, 45 deg out to
    w 1.6 at t 1.2, back to w 1.4 at t 1.4. This removes the 45 deg knife edges.
    - The groove has a true 0.25 normal clearance and is open at the rear. Its front end is closed at x **-7.0**
      (layout says -1.5), because the 5 mm front chamfer leaves no base under a groove ahead of x -5.5.
    - The key centre is z -4.2 (groove_z ~ -6.2..-2.2), leaving 1.95 of base under the groove.
    - The barb is 0.8 (layout 0.5): the flank play lets the key move 0.35 outward, so 0.5 would not retain.
  - **J6 cap.** 2 keys rise INSIDE the bay: web 1.6 at y +-10.65..12.25 (0.65 clear of the 20 mm pack) and a 1.0
    head into a groove in each side wall. The cap hangs on 45 deg lips 1.6 thick, with 1.5 of wall behind each
    groove.
    - The grooves stop at x -60, which is the closed stop. They run out forward through 2 notches at the front-bottom
      corners, which the keys fill when the cap is closed.
    - Detent: a 0.35 bump on each key tip clicks into a 0.3 dimple at x -57. It works by the side wall's free bottom
      edge flexing about 0.1 (bench gate).
  - **J13 run button.**
    - The switch drops straight into a cradle: a shelf and a rear stop (both bridges between the bay walls) plus
      45 deg side guides.
    - The red cap is pressed on from the front through the dia 13.6 hole. The hole has a teardrop pointing -Z, the
      print top. This needs a cap that comes off the switch stem (Q for the parts list).
    - A 0.75 pad boss inside the front wall keeps the wall at 1.75 behind the 1.5 deep pad.
    - The rear stop top is at z -20.2: above the press line (z -21) and below the XT30 box (z -20).
    - The base opening is shaped to the switch, run-lead and pigtail passages, all inside `BASE_OPENING`.
  - Base: R3 web fillet at the grip root, 1.0 heel chamfer, 0.6 bed chamfers, 1.0 rear chamfer, and 0.8 entry chamfer
    on the tripod hole.
  - Knobs:
    - knob_fps has 32 teeth (concept 40), because finer teeth failed the thin-feature screen.
    - The D bores have +0.1 on the diameter and +0.05 on the flat (press).
    - knob_exp has a bushing recess dia 11.5 that also clears an M7 nut. knob_fps has a nut recess dia 16 x 3.25
      (layout 3.0), 0.25 clear of the bushing end.
  - eyecup: a 2.0 TPU shell with a 15 deg flare, 3.0 sleeve (0.3 grip) and an inner lip to r 16.0 with a 1.2 flat tip
    and a 45 deg underside.
  - plunger: an engraved power symbol on the finger face (0.4 deep).
  - Every part reads its build numbers from the layout. The cap plate top is pinned at the grip heel - 0.1, and the
    skirt strip at the base side faces, so the envelope requests below change no geometry.

**Half-done / open.**
- Not rendered by me; the integrator's renders will show the parts.
- knob_fps: the switch shaft ends at y 43.0, which is 0.8 past the knob top (42.2). The shaft must be cut to y 42.0
  (request 4).
- cots_build:
  - The eyepiece proxy barrel (r 19.25) over x -174.3..-171.3 overlaps the eyecup sleeve by 1.2 radial. Model the
    eye-end body there at dia 36.7, as EYECUP says, so the declared 0.3 interference is what is measured.
  - The pack box with sharp corners touches the bay R6.5 corners (14 mm3 at x -26.5). A pack with corner radius
    0.5 or more clears.
- The `panel_on` vs skirt_l clash (cots_build request 12:04): confirmed at 135 mm3. I support option (a), skirt_l at
  step 8 after the panel. Computed: skirt_l sliding +X from x -150 to 0 hits 0 mm3 against panel + hood, and the
  groove is open at the rear.
- The xt30_pair box clash is gone on my side (rear stop top lowered to z -20.2), whatever the box decision.

**Next step:** after the integrator rules on the requests, re-run `build_d2.py --part` for skirt_l, skirt_r, cap,
plunger and stick_sleeve. Bench gates for my parts: cap detent click and pull-out, skirt barb retention, run-cap
press-on, knob press fits, eyecup grip.

## cots_build owner

**Status (12:31 machine time).**
- Done: `cots.py` (19 COTS proxies + the 4 PT screws; `pt_screws` is a mass/BOM row only), `checks.py` (SPEC s6
  checks 1-9 + contract, COTS containment, mate_overlap, STL mesh), `build_d2.py` (assembly, checks, STL/STEP/
  manifests/receipt with `blocking`, renders hero/exploded/xray/2 sections/print-poses/step-01..10, `--part`,
  `--fast`, `--lens`). Last full run 12:30 with all 5 modules real (no stubs): 75 s, peak 1049 MB; `--fast` about
  60 s; `--part <id> --fast` 1-18 s.
- Result 12:30: release_candidate false; blocking = contract (hood, skirts, cap envelopes), cots_containment
  (x1203_kit box), mate_overlap (tub vs hood 5 mm3), thin_wall (tub Pi hooks 1.4, plunger and sleeve 0.8), sweeps
  (pi_in vs rib_r, camera_in vs pin, board_in vs rail, panel_on vs skirt_l, pack_in XT30, hood_on 1.4 mm3).
  Most of these need the integrator's layout decisions (Interface requests, cots_build rows).
- Half-done: nothing in my files; the proxies are estimates where the layout says so.
- Next (integrator): decide the requests, rerun `build_d2.py` (non-fast), then make_tables.py / make_bom.py.

**Commands** (repo root):
- Full: `.venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/build_d2.py` (add `--fast` to skip
  STEP + renders, `--lens fujinon_hf6xa`, `--sweep-step 2.0`, `--no-sweeps`, `--no-thin`).
- One part: `... build_d2.py --part <id> --fast` -> `out/part-<id>.json` + `out/stl/<id>.stl` (printed id: contract,
  bed, thin wall, keep-outs, interference with the COTS; COTS id: volume, bbox, containment).
- A missing or failing printed module is replaced by its envelope box (2.0 shell when every side >= 10): status `stub`,
  never `pass`; `release_candidate` stays false while any stub is present.

**Check notes for module owners** (how build_d2.py reads your parts):
- `build(layout)` may return Workplanes holding several solids; the contract check then fails (`one_solid`).
- `mate_overlap` (stricter companion to SPEC s6.1, which excludes MATES): declared contact / slide / clearance pairs
  may touch but must not overlap (<= 0.05 mm3). Press, thread and interference mates stay excluded / depth-limited.
- Envelope tolerance is 1e-3 (contract 0.0). `PRINT[pid]['face_down']` must equal `PARTS[pid]['face_down']`.
- Thin-wall screen: ray thickness from 1500 surface samples. Pass = share under 1.2 <= 2 %, under 0.8 <= 0.5 %, and
  in loaded zones (panel bosses/posts, tub pads and Pi bosses, hood hook zones) share under 1.6 <= 2 %.
  `thinnest` in checks.json lists the 6 thinnest sample points.
- Clearance zones (SPEC s6.2) are boxes in `checks.clearance_zones()`. J1 hook zones stop 0.5 under the band
  (z 84.8..96.8) and need >= 0.09 (play 0.1); J2 >= 0.225; J4 >= 0.225; J7 >= 0.225; J8 >= 1.125; J10 >= 0.225.
  A zone with no material of one part reports "feature absent".
- Sweeps: mesh booleans (manifold3d) along `INSERTIONS` at 2 mm steps + 1.0 / 0.5 before the final pose; snap zones
  of the listed hooks are subtracted; a cable keep-out is an obstacle once one cable end is in the body and its plug
  step is earlier (cable ends: `checks.CABLE_ENDS`).
- Print manifest: an `overhang_screen` per part (info only): downward area steeper than 45 deg above the bed, plus
  `bed_contact_mm2` (first-layer area); also `filament_g_est`. The manifest key names asked for by docs are kept.
- **Build 12:26 findings, all 5 modules real (no stubs)** (`build_d2.py --fast`, 60 s; out/checks.json):
  - pass: interference (exact, 44 pairs), clearances J1-J10 (11 zones), keep-outs (63), bed fit, STL meshes, driver
    audit (bit 0.25 radial in each counterbore; s_b1 / s_b2 handles 12.3 / 24.2 mm from the grip), layout self-check.
  - contract: hood 0.25 past y -32 (hook teeth; interface request), skirt_l / skirt_r 2.2 past their y envelopes, cap
    3.6 above its envelope (grip_small requests 1-2).
  - mate_overlap: tub vs hood 5.0 mm3 at x -139.9..-135.4, y -32.0..-30.4, z 94.3..95.0 (a tub feature near the EVF
    board slot reaches into the hood's right-wall lip); hood_on sweep shows the same (1.4 mm3 at 0.5 mm). tub + hood
    owners.
  - thin wall: tub loaded zones 14 % under 1.6 (Pi hooks t 1.4 by layout: SPEC conflict request), plunger and
    stick_sleeve (layout 0.8 numbers: request). Knife edges on the skirts and eyecup are gone.
  - sweeps (interface requests): pi_in vs rib_r, camera_in vs camera pin, board_in vs bottom slot rail, panel_on vs
    skirt_l, pack_in xt30_pair vs base_grip (45 mm3 at x -36.8..-36.0 while the pack rises).
  - cots_containment: x1203_kit box (request). Mass/CoM: Kowa 882 g, CoM 4.1 ahead of the grip axis and 34.6 above
    the grip top; Fujinon 767 g, -8.5 / +29.6 (concept +1.5 / -8.3).
- Renders (non-fast runs), for the docs: `out/renders/hero.png`, `exploded.png`, `xray.png` (left side, printed
  parts at 16 % opacity), `print-poses.png` (every printed part on its bed face, labelled with face_down) and
  `step-01.png` .. `step-10.png` (ASSEMBLY.md: earlier parts ghosted, this step's parts in colour at 0.6 x the start
  of their insertion path; screws 25 mm back along their axis; bench steps pulled apart).

## docs owner

**2026-10-04, 11:39-12:00 machine time.**

**Done.**
- `electronics/gs8-d2-v1/WIRING.md`: files, block diagram, decisions W-1..W-8 (pigtail soldered to the X1203 pads,
  18 AWG + XT30U, **1N5817 in the EVF 5 V lead** (board window 4.25-4.90 V), PH junction at the board, GPIO26 /
  GPIO13 logic, 2 s power key, out-of-body charging, no added pull-ups), power path with planning currents (8.6 A at
  the X1203 limit near cut-off, 0.1 V drop), J8 header + I2C (0x36 gauge, 0x37 encoder), every cable (generated),
  plug order (generated), config.txt / cmdline / EEPROM (PSU_MAX_CURRENT=5000, POWER_OFF_ON_HALT=1) / logind +
  daemon / input notes, bench gates G-W1..G-W11, open items.
- `electronics/gs8-d2-v1/make_bom.py` -> `BOM.md`, `bom.csv`: 47 purchased lines (sections A-C, E, F), 12 printed
  parts (D), coverage of every layout COTS and cable id (G, 0 uncovered). Camera: SGD 775.74 from prices.json +
  329.10 estimates; the lens is unpriced on purpose (user review).
- `make_tables.py` (plain Python): refreshes the BEGIN/END blocks in WIRING.md (header, cables, plugs),
  PRINT-GUIDE.md (print, beds, engrave), ASSEMBLY.md (steps, screws) and DESIGN.md (parts, cots, checks), and writes
  `harness-schedule.csv`, `pi5-header.csv`, `wiring-d2.svg`. `--check` exits 1 if a block is stale. It reads
  `out/print-manifest.json` (stub rows fall back to a layout estimate) and `out/build-receipt.json`.
- Drafts: `PRINT-GUIDE.md` (settings, per-part table, bed fit, orientation/supports, hardware, post-processing,
  coupons, print order); `ASSEMBLY.md` (rules, 10 generated steps with tool, motion, harness and cable rows, checks per
  step, screw table, battery and storage use, service order); `DESIGN.md` skeleton (TODO sections for the integrator).

**Half-done.** Printed masses are layout estimates until the modules replace the stubs (the tables refresh by
themselves). The coupon geometry in PRINT-GUIDE s6 is not modelled. DESIGN.md text sections are TODO (integrator).

**Next step (integrator).** After the final `build_d2.py`: `python cad/gs8-d2-v1/make_tables.py` and
`python electronics/gs8-d2-v1/make_bom.py`; then fill the DESIGN.md TODO sections. Decide the 4 docs interface
requests below (fan cable row, EVF lead name + ko_5v_end, STEPS[0] solder text, manifest key names).

## Interface requests

(Format: date-time, requester, what to change in `layout.py`, why. The integrator decides.)

- 2026-10-04 11:55, cots_build: `COTS['x1203_kit']['box']` x range PX1-64.0..PX1-1.0 -> PX1-64.4..PX1-0.6. The
  M2.5 hex standoffs (5 AF, 5.77 across corners) at the Pi holes (x PX1-3.5 / PX1-61.5) stand 0.39 past the box in x
  with flats facing Y (in y with flats facing X). `cots_containment` fails on this until the box grows.
- 2026-10-04 11:55, cots_build: add `ends=(cots_id, cots_id)` to each `CABLES` row. checks.py carries the map
  `CABLE_ENDS` (from the frm/to text) to decide when a cable keep-out is in the body during the insertion sweeps;
  it should live in the layout.
- 2026-10-04 12:00, cots_build: `COTS['xt30_pair']['box']` x -62.0..-36.0 runs 1.0 past `KEEPOUTS['ko_xt30']` x
  -65.0..-37.0, so a grip wall that respects the keep-out still clashes with the COTS proxy (45 mm3 at x -36.85..-36).
  Make them agree: box x -> -63.0..-37.0 (preferred; keeps 26 mm for the mated pair, inside ko_xt30), or ko_xt30
  x1 -> -36.0 and the grip wall moves.
- 2026-10-04 12:04, cots_build (ASSEMBLY ORDER, computed): the `panel_on` sweep (step 8, -Y) drives both panel bosses
  (z 2.6..12, y 24.1..32.2) through `skirt_l` (y 35.2..36.8, z -8..8), which is fitted at step 3: 135 mm3 at
  x -109..-87, z 2.6..8.0 with the real grip and panel modules. The bosses pass the tub lip through the notches, but
  the skirt that "hides the notches" is already there. Options: (a) fit skirt_l at step 8 after the panel (it slides
  +X in the base dovetail below the panel wall, z 8.0 vs 8.2), i.e. move 'skirt_l' from STEPS[2]['adds'] and the
  base_on moving set to step 8 with its own insertion (+X); (b) notch skirt_l under the bosses (visible).
- 2026-10-04 12:04, cots_build: `HOOD_BOX` y0 -32.0 -> -32.5. The J1 hook rule (beam outer face = wall face + ledge
  + SLIDE, tooth 0.8 toward the wall) puts the hk1/hk2 tooth tips at y -32.25, so the hood module stands 0.25 outside
  its envelope by contract (computed on printed_hood.py at 12:02).
- 2026-10-04 12:04, cots_build (MIN_WALL): two layout numbers are below MIN_WALL 1.2 and fail the thin-wall check by
  design: `PLUNGER['flange']` 0.8 thick (finger-pressed, so a loaded part) and `STICK_SLEEVE['wall']` 0.8. Either raise
  both to 1.2 (flange: hood pocket and travel follow), or declare them as accepted exceptions in the layout (e.g. a
  `THIN_OK = {'plunger': dict(min=0.8, reason=...), 'stick_sleeve': dict(min=0.8, reason=...)}`; checks.py already
  reads `layout.THIN_OK` if it exists, and `CABLES[i]['ends']` if present). Until then they fail.
- 2026-10-04 12:25, cots_build (INSERTION, computed with printed_tub.py 12:22): `pi_in` is blocked by the
  front-right rib. The stack goes straight down (path z +45 -> 0) and the Pi/X1203/cooler plan footprint (x -94..-5.55,
  y -32.3..23.7) lies under `RIBS['rib_r']` (x -15..-5.2, y -32.5..-23.6, z 41..80): 200-300 mm3 per board at
  x -15..-6, z 41..61. Any tub feature above the Pi footprint blocks the drop. Options: drop rib_r (rib_l + the
  front wall carry the lens load), or move it outside the Pi plan (only 0.2-0.35 mm is free at the right and front
  walls, so in practice above-and-ahead is impossible), or make it a separate part fitted after step 4.
- 2026-10-04 12:25, cots_build (INSERTION, computed): `camera_in` start dx -11.1 is too short. On the -Y leg the CS
  ring (front at X_FW_IN + 10.8 - 11.1 = -5.5, r 15.375) sweeps through the camera pin at (y 15, z 75), which stands
  x -8.2..-5.2: 7.2 mm3 at x -8.2..-5.5. Needed: dx <= -(10.8 + 3.0 + SL) = -14.05, e.g. path
  [(-14.1, 60, 2), (-14.1, 0, 2), (-14.1, 0, 0), (0, 0, 0)] and `CAM['insert']['start_dx']` -14.1 (then re-check the
  space behind the camera; the FPC keep-outs are ignored for this insertion already).
- 2026-10-04 12:25, cots_build (INSERTION, computed): `board_in` (EVF board along -Y) drives the micro-HDMI receptacle
  (board lower edge, -X component side, y 4..17 final, z 64..68) along the -X lip of the bottom slot rail for
  y 17..28: 13.6 mm3 at x -139.9..-138.6, z 64..65.2. The `bottom_rail_gaps` (4..17) only clears the final pose.
  Options: no -X lip on the bottom rail (the +X lip and the top groove hold the board), or extend the gap to the
  open +Y end (y 4..28).
- 2026-10-04 12:14, cots_build (SPEC vs layout): SPEC s6.5 wants >= 1.6 at hooks, but `PI_HOOK['t']` is 1.4 (chosen
  for the 3 % strain). checks.py screens the Pi hook beams (z 2.5..7.4 in the 4 hook zones) at 1.6 as SPEC says, so
  the tub will fail there by design. Decide one: PI_HOOK t 1.6 with a longer beam (deeper relief), or a SPEC/THIN_OK
  exception for the Pi hooks at 1.4 (`THIN_OK['tub'] = dict(loaded_min=1.4, reason=...)`, already read by checks.py).
- 2026-10-04 11:56, docs: add a `fan` row to `CABLES`: dict(id='fan', name='Active Cooler fan lead (native,
  JST-SH 4)', frm='Active Cooler', to='Pi 5 FAN header', via=[], length=60 (estimate), steps=(1,)). WIRING lists every
  cable with both ends; no geometry change.
- 2026-10-04 11:56, docs: the EVF 5 V lead gets a 1N5817 in its + conductor and a JST PH 2-pin wire-to-wire junction
  at the board end (WIRING W-3: the board needs 4.25-4.90 V and a Pi USB port gives about 5.0-5.1 V; W-4: the board
  goes in at step 6 after the lead is plugged at step 4). (a) Rename `CABLES['usb_5v']['name']` to say so. (b) The
  heat-shrunk diode splice (about dia 6 x 25) and the PH junction (about 6 x 5 x 12) must lie in `ko_5v_up` /
  `ko_5v_end`; `ko_5v_end` is 5.5 x 25.5 x 6 (x/y/z), so they fit only lying along y. Grow `ko_5v_end` x by 1 mm,
  or confirm against the hood/panel geometry.
- 2026-10-04 11:56, docs: `STEPS[0]['action']`: add "Solder the EVF 5 V lead (1N5817 + PH junction, 3 joints) and the
  PH pigtail to the Rev I board EXT+/GND pads (2 joints)." and add "multimeter" to its tool. Bench solder joints become
  10 (+2 if the pack lacks an XT30); the concept counted 5 (+2 Rev I).
- 2026-10-04 11:56, docs (to cots_build): make_tables.py / make_bom.py read these print-manifest keys per part:
  `volume_mm3`, `mass_100pct_g`, `mass_est_g`, `print_time_est_h`, `print_bbox_mm`, `bed_fit`, `stub` (stub rows
  fall back to the layout estimate), and from build-receipt.json `summary`, `totals.mass_com`, `stubs`,
  `release_candidate`, `built_at`, `argv`. Please keep the names.
- 2026-10-04 12:15, hood_panel (1): `HOOD_BOX` y0 -32.0 -> -32.3. The hk1/hk2 teeth reach y -32.25: the beam outer
  face is -31.45 per J1 (wall face + ledge + SLIDE) and the tooth is 0.8. `build_d2 --part hood` fails
  `inside_envelope` (excess 0.25) until this changes. Trimming the tooth to fit would cut the catch from 0.55 to 0.30.
  Option for the same edit: `HOOD['y'][0]` -32.0 -> -32.35 (LOCATE 0.15 to the right-wall inner face) closes the
  0.5 open slit along the roof's right edge; the hood module follows `HOOD['y']` with no code change.
- 2026-10-04 12:15, hood_panel (2): `PANEL_LOCATE_RIBS[0]` z0 40.0 -> 41.3.
  - Why: the layout box overlaps the tub `rib_l` (top z 41, y 24.1..27.4), so the panel could not go on along -Y.
  - Modelled at 41.3.
- 2026-10-04 12:15, hood_panel (3): J2 printability.
  - (a) `HOOD_RAIL['box']` y0 25.5 -> 23.9: the layout left a 0.25 web behind the groove.
  - (b) Add `HOOD_RAIL['piers']`: 6 piers, 3.0 wide, starting at x -134.5, -110.5, -86.5, -62.5, -38.5 and -14.5.
  - (c) `PANEL_TONGUE` becomes 5 teeth: x -131.25..-110.75, -107.25..-86.75, -83.25..-62.75, -59.25..-38.75 and
    -35.25..-14.75 (SLIDE 0.25 to the piers).
  - Why: the hood prints roof down, so the groove lip was a 6.25 mm unsupported overhang. It now prints as 21 mm
    bridges.
  - Both modules compute this today with `rail_piers()`. The checks' J2 clearance zone still applies (0.25 everywhere).
- 2026-10-04 12:15, hood_panel (4): `PLUNGER['hood_pocket']` z0 16.3 -> 0.3. The pocket becomes a channel open at
  the plate foot.
  - Why: the flange (x -2.1..-1.3) lies inside the plate (x -2.5..0), so a hood dropping in step 5 hit it.
  - Modelled. The hood_on sweep vs the plunger is now 0 mm3. The flange still bears on the plate skin (x -1.3) and is
    held by the tub hole.
- 2026-10-04 12:15, hood_panel (5): `ENCODER['cradle_hooks_at_z']`.
  - Why: a hook under the PCB bottom edge (z 44.2) sits in `ko_hdmi_run` (z 39.6..44.0).
  - Modelled instead:
    - 1 hook over the top edge (w 8);
    - 2 hooks on the x edges at z 45..50 (w 5);
    - teeth 0.55 over the PCB back face, play 0.1.
  - Record this in the layout, keep the cots encoder proxy's back parts at least 1 mm in from the x edges at z 45..50,
    and add bench gate G-ENC-1: the 5880 back side is clear there (QT connectors).
- 2026-10-04 12:15, hood_panel (info, to docs): `ko_5v_end` +1 mm in x is clear of both the hood and the panel; no
  hood or panel solid lies within 3 mm of it.
- 2026-10-04 12:15, hood_panel (7, to cots_build): `--part hood` reported thin_wall 2 of 19 loaded samples below 1.55.
  - Calling `checks.thin_wall(L, 'hood', build_part(...).val(), loaded_boxes(L, 'hood'))` directly gives 14 loaded
    samples, 0 below: pass.
  - A 20000-sample replica gives 233 loaded, 0 below.
  - Please check which shape `run_part` passes (`as_shape`).
  - **Resolved 12:16:** the rerun of `--part hood --fast` passes thin_wall. Only the envelope (request 1) still fails.
- 2026-10-04 12:19, grip_small, request 1: `SKIRTS[...]['box']` y -> skirt_l (33.0, 36.8), skirt_r (-36.8, -33.0).
  The J5 dovetail key (1.4) + barb (0.8) must enter the base groove, i.e. leave the 1.6 strip envelope by 2.2. The
  geometry is pinned to `BASE['y']`, so the change only widens the envelope (no clash: base/skirt = 0 mm3).
  Also `SKIRT_JOINT`: groove_z -> (-6.2, -2.2), front_stop_x -1.5 -> -7.0 (no base under a groove ahead of x -5.5
  because of the 5 mm front chamfer), barb h 0.5 -> 0.8 (flank play 0.35).
- 2026-10-04 12:19, grip_small, request 2: `CAP['box']` z1 -110.1 -> -106.5. The cap's 2 keys must rise into the
  bay grooves (z -110.1..-106.5) or nothing holds the cap. `CAP_JOINT` rail_z -> (-108.6, -106.25) (grooves in the
  bay side walls, closed at x -60, out through the front). The plate top stays at -110.1 (pinned to `GRIP` z0 - 0.1).
- 2026-10-04 12:19, grip_small, request 3 (joins cots_build 12:04 MIN_WALL): plunger flange 0.8 and sleeve wall 0.8.
  - Preferred for the plunger: `PLUNGER['flange']` x -> (-2.5, -1.3) (1.2 thick). The tub owner adds a 0.4 deep
    counter-recess 14.2 x 8.4 round the plunger hole in the front-wall outer face (x -3.1..-2.7); the flange stops on
    its floor, so travel stays 0.6.
  - Otherwise put plunger and stick_sleeve in `THIN_OK` (both are non-structural, and 0.8 is at least MIN_FEATURE).
  - For the sleeve, `THIN_OK` is the cheap fix. A 1.2 wall would grow the section to 23.7 x 13.8 and change the tub's
    `STICK_GUIDE` sleeve_section.
- 2026-10-04 12:19, grip_small, request 4: `SWITCH_1824['shaft']` a1 43.0 -> 42.0 (cut the 1/4 in shaft to 6.8 mm
  above the panel face at step 2; add the cut to STEPS[1]). The knob_fps top is at y 42.2, and its through D bore
  then engages y 38.45..42.0.
- 2026-10-04 12:19, grip_small, request 5 (assembly text): STEPS[2] "Drop the run button into its cradle through the
  base opening, then press its red cap on through the grip-face hole" (the cap cannot pass the wall on the switch).
  With request (a) of cots_build, skirt_l moves to step 8: "slide skirt_l +X into the base groove until the barb
  clicks", after the panel and before s_b1/s_b2 (the driver path does not touch the skirt).

- 2026-10-04 12:40, tub, T1 (computed, `sweep_tub.py camera_slide_only`): `CAM['pins']` -> [(-15.0, 75.0), (15.0, 45.0)]
  (the other diagonal of the camera's own 4 holes). The current pin (15, 75) is hit by the CS ring on the -Y leg:
  7.2 mm3 at y +20..21. The swapped pair gives 0.0 mm3 on the unchanged 11.1 path; analytic margin 0.68 at (15, 45).
  Prefer this to cots_build's dx -14.1: at -14.1 the camera rear (x -38.6) crosses `ko_hdmi_run` (x <= -36.8,
  y 20..32, z 39.6..44) on the slide (camera bottom z 42.25).
- 2026-10-04 12:40, tub, T2 (computed, `sweep_tub.py pi_in_proposed`): `INSERTIONS['pi_in']` path
  -> [(-2.8, 2.1, 80), (-2.8, 2.1, 40), (-2.8, 0, 40), (-2.8, 0, 5), (0, 0, 5), (0, 0, 0)].
  - Change STEPS[3] to: lower the stack about 3 mm back from the front wall and 2 mm off the right wall; below the
    right-wall pads, move it to the right wall; just above the floor, slide it 2.8 forward and press down until the 4
    hooks click.
  - Why: a straight drop hits 3 things: the camera pin at (-15, 45) (PCB edge x -6.0 vs pin tip -8.2), the hk1 catch
    ledge (0.6 in y) and pad_r1 (1.8 in y, z 79.5..91.5). Entry from the open +Y side is blocked by rib_l.
  - Result: 0.0 mm3 before the final 5 mm press, with the x1203, pi5, cooler and kit COTS boxes.
  - With T1 the pins sit at z 45/75 either way, and the path clears both.
- 2026-10-04 12:40, tub, T3 (joins cots_build 12:25): delete `RIBS['rib_r']`. It sits over the Pi footprint and
  costs 255 mm3 in the drop. printed_tub.py already omits it (with a NOTE) while the layout overlaps the pi5 box plan.
  Also delete `BAFFLE`, or move it to the panel as a finger at y 16.9..18.1 entering from +Y at step 8 (hood_panel's
  choice). The layout box cannot be a tub feature for the same reason.
- 2026-10-04 12:40, tub, T4 (record only): `PI_BOSS['od']` 7.0 -> 8.8; `PI_HOOK` t 1.4 -> 1.6, root_z 1.0 -> 1.2,
  form "45 deg leaning slab", strain 2.6 %; `RIBS['rib_l']` y1 27.4 -> 32.2 (45 deg gusset) with the notch above.
  These are already modelled; the record keeps the layout and SPEC s3 true.
- 2026-10-04 12:40, tub, T5 (choice): the keyhole T-heads' -Y wings need 2 small supports in the -Y print. The only
  support-free option is a one-sided (+Y wing) tongue, or an L-hook pair, which changes the base pockets (grip_small)
  and the J4 load path. Recommend keeping the T and the 2 supports.

## integrator

**2026-10-04, 12:43-13:00 machine time. Done.**
- Decided every interface request above and wrote them into `layout.py` (marked `INTEGRATOR`; table in DESIGN.md s6):
  HOOD y0 -32.35 + HOOD_BOX y0 -32.5; skirt and cap envelopes, SKIRT_JOINT, CAP_JOINT; PANEL_LOCATE_RIBS z0 41.3;
  HOOD_RAIL web 23.9 + piers; CAM pins on the other diagonal (T1); pi_in L path (T2); rib_r and BAFFLE deleted (T3);
  PI_BOSS 8.8, PI_HOOK t 1.6 / root 1.2 (T4); T5 keep the T-tongues; plunger flange 1.2 + channel hood pocket;
  THIN_OK for stick_sleeve; encoder cradle_hooks record; 18/24 shaft y 42.0 (+ cut in STEPS[1]); x1203_kit and
  xt30_pair boxes; ko_5v_end x1 -130.0; fan cable row, usb_5v name, CABLE_ENDS + `ends` per cable; STEPS 1-4 and 8
  text; skirt_l moved to step 8 with insertion `skirt_l_in` (+X 125, snap zone `skb_l`).
- Module edits: `printed_tub.py` (rib_r optional, notch guard, plunger recess = flange + SEAM); `checks.py` (snap
  zones skb_l / skb_r); `make_bom.py` (fan cable covered by D2-02); PRINT-GUIDE tub/hood support rows; SPEC.md
  pointer note.
- Builds: full Kowa build 12:49 -> every check passes, 0 stubs, `release_candidate: true`; `--fast --lens
  fujinon_hf6xa --sweep-step 1.0` 12:52 -> every check passes (`out/checks-fujinon-sweep1mm.json`).
- DESIGN.md written (status, results, interfaces, decisions, balance, exports, open items, rebuild).

**Half-done:** nothing in the integrator scope. Open items and bench gates: DESIGN.md s9.

**Next step:** the user's lens choice; then the coupons (PRINT-GUIDE s6) and the bench gates.

## fixer

**2026-10-04, 13:16-14:17 machine time. Done.** Verifier findings P-P1..P-P11 and A-F1..A-F10 applied in severity
order. The table is in `HANDOFF.md` s4; the change list is in DESIGN.md s6b.
- **Geometry.**
  - Engraving text grows 0.15 per side.
  - Snap-hook root gussets; hood hooks 10.5 long with reach 0.40; cradle reach 0.40.
  - Pi port-edge tip chamfer; J2 groove 0.4 floor with rail z0 90.0.
  - Cap keys end 1.2 inside R9.
  - Knob bore offset 0.10.
  - microSD proxy; 6 cable-route keep-outs.
  - STEPS, INSERTIONS (`sd_in`, `evf_pair_in`) and the cable steps and lengths.
- **New checks.** `engrave_groove` and `boss_geometry`, plus 3 snap-strain self-check rows (`layout.snap_strains()`).
  The exact sweep fallback is guarded.
- **Coupons.** `make_coupons.py` writes 12 STLs to `out/stl/coupons/`.
- **Docs.** PRINT-GUIDE, ASSEMBLY (s1, s3, s7 service order), SPEC (counts, J1, J9, steps, s6.5 amendment, G-SNAP-2),
  FASTENER-POLICY B and H, WIRING s10, make_tables (CABLE_INFO, PLUG_ORDER, torque format) and make_bom (D2-04 linked;
  D2-25 200 mm; D2-27, D2-50, D2-69..71).
- **Stale outputs.** The old JSONs are in `out/_stale-2026-10-04/`.
- **Builds.**
  - Final full Kowa build 14:15:51: every check passes, `release_candidate: true`.
  - Fujinon 1 mm sweep run 14:00: every check passes (`out/checks-fujinon-sweep1mm.json`).
  - `make_tables --check`: no stale block.

**Half-done:**
- P-P7: a skirt key neck of 1.0 was tried and reverted. It hit the strap in the base strap slots, and the skirt minimum
  stayed at 0.68.
- P-P7: the panel R5 land is open.
- P-P3: the support-free tongue is open.
- A-F6 was closed by amending SPEC, not by geometry.

**Next step:** see `HANDOFF.md` s6. Start with the skirt key (wider neck, or move the strap slots), then the coupons
and the bench gates.

## r2 R3 API

**2026-10-05 00:02 machine time.** The registries are in `layout.py` section 9b (`# --- R3` block, owner R3). R1 and R2
append in their own empty blocks right after it (`# --- R1 registry entries` / `# --- R2 registry entries`), with
`+=`, never by editing the R3 block. checks.py reads them after layout.py is fully imported.

- `LOAD_BEARING_PARTS` (list of PARTS ids). Every member needs >= 1 CRITICAL_FEATURES entry, or the build FAILs
  (missing coverage). A new load-bearing part: `LOAD_BEARING_PARTS += ['pi_keeper']`. A part removed from PARTS (e.g.
  eliminated skirts) is reported `n/a` and needs no entry: remove it from the list too.
- `CRITICAL_FEATURES += [dict(id='skirt_key_neck_l', part='skirt_l', origin=(x, y, z), direction=(0, 0, 1),
  span=(5, 2.0, (1, 0, 0)), min_mm=1.2, structural=True, note='...')]`
  - origin: a point INSIDE the material at the narrowest section, assembly coordinates (final pose). If the origin is
    not inside the solid the entry FAILs as stale.
  - direction: across the section. Thickness = entry-to-exit length of the line through origin (OCP
    IntCurvesFace_ShapeIntersector on the built solid; exact B-rep, no mesh).
  - span (optional): n parallel rays centred on origin, stepped step_mm along axis; rays whose start point is outside
    the material are skipped and counted; the minimum is reported.
  - structural=True and measured < min_mm: FAIL. structural=False: measured and reported (info), never a pass basis.
  - Same id later in the file replaces the earlier entry (R3 seeds entries for current geometry; owners may replace them).
- `NONSTRUCTURAL_EXCEPTIONS += [dict(part='cap', id='detent_bump', measured_mm=0.70, why='...')]`: listed by name in
  checks.json; they do not count as coverage for a load-bearing part.
- `REMOVALS += [dict(id='pi_out', moving=['pi5', 'x1203', 'x1203_kit', 'cooler', 'pi_keeper'], reverse_of='pi_in',
  off=['panel', 'skirt_l', 's_b1', 's_b2', 's_r1', 's_r2', ...], unscrew=['s_k1', 's_k2'], release=[],
  keepouts=[], tool='PH1', note='...')]`
  - context = every id present after step 10, minus `moving`, minus `off`. Obstacles include remaining screws.
  - path: `reverse_of` an INSERTIONS id (its path reversed: from (0, 0, 0) outward) or an explicit `path` starting at
    (0, 0, 0). Sweep = manifold3d mesh boolean, 2 mm steps, tol 0.5 mm3 (same as the insertion sweeps).
  - release: snap_zones() ids (e.g. 'skb_l', 'pih1') or B() boxes where the stated tool deflects a latch; overlap is
    allowed only there, and the release must be described in `tool`/`note` (and ASSEMBLY.md).
  - unscrew: these screws get the straight-driver audit in the SERVICE state (context above), not the build state,
    and count as removed before the move (no need to repeat them in `off`).
- New screws: add them to `SCREWS` as usual (all fields: id, joins, into, head_part, head_point, axis, tip, engage,
  step). check_driver and check_bosses pick them up automatically.
- `SECTIONS += [dict(id='pi-keeper-y10', axis='y', at=10.0, window=(u0, u1, v0, v1), parts=[...], title='...')]`:
  build_d2.py renders out/renders/section-<id>.png (2D B-rep section, matplotlib). R1: add one through the keeper.
- `EVF_RESTRAINT` (R3): limit 0.6 per direction (+-X, +-Y, +-Z), arresting parts tub/panel/hood. R2's stop must be
  part of panel or tub (or add its id to `arrest` in the R2 block: `EVF_RESTRAINT['arrest'] += ['evf_stop']`).
- A row measured on a STUB part reports `stub` (never pass/fail). Feature entries for a part no longer in PARTS report
  `info` (not measured). A REMOVALS entry moving 'pi5' and one moving 'panel' must exist (coverage rows in `removals`).
- Quick check without the full build: `.venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py --
  cad/gs8-d2-v1/checks.py --critical [--parts tub,panel]` (builds only the listed printed modules; prints the table).

## r2 R4 (findings 4, 5, 7-docs)

**2026-10-05 00:17 machine time, R4 done (final entry; the items below were written 00:00-00:17).**
- Half-done: the BOM was regenerated at 00:17 with R1's keeper **not yet** in `layout.SCREWS`/`PARTS` (4 PT, 10
  printed). `make_bom.py` counts them automatically: **next step for the integrator/fixer: re-run
  `python electronics/gs8-d2-v1/make_bom.py` after R1's s_k1/s_k2 and `pi_keeper` land and after the r2 build** (expect
  6 PT used + 4 spare = 10, D2-33 qty 6, 11 printed parts). FASTENER-POLICY A/B, ASSEMBLY s1.1 and OPTIONS already
  carry R1's announced keeper (6 PT, +1 printed) and R2's skirt elimination.
- Not run: every gate (G-W1..G-W12, G-MP-*, G-FPC-1). Nothing measured. Pi 5 board figures are third-party
  published values (2 URLs in WIRING s4.2), the rest are estimates.
- Done: WIRING.md s4 (4.1-4.7: planning peak 27 W kept and shown as not served by the 25.5 W X1203; workload states
  S0-S4 with sourced/estimated loads; restrictions R-P1..R-P8; bound 14.8-19.1 W; fallback 2S1P + >= 7 A buck with
  its geometry impact; recommendation c); s8 config (arm_freq=1800 conditional, radios off); s9 G-W6 diode upper bound
  made explicit (X1203 +5 % source max), new G-W12 workload gate (P1-P7); s10 pointers.
- Done: MEASURED-PARTS.md (9 records, new gates G-MP-PACK/X1203/EVF/ENC/SW/STICK); OPTIONS.md (a) and (b) quantified,
  (c) waits for R2's notes; FASTENER-POLICY E (ISO 7045 PH1 only, no hex; repair tools), F (kit screws, switch nut),
  G (scope of "one PH1"); ASSEMBLY s1 Driver row + new s1.1 full toolset (12 tools, (a)/(b) column); DESIGN s2 line.
- Done: make_bom.py reads the PT screw count from `layout.SCREWS` (R1 keeper screws counted automatically), the
  printed count from PARTS, adds a "Build counts" block, D2-34 (contingency ISO 7045 M2.5), D2-72..74 tools.
  Regenerated: 56 lines, 10 printed parts (skirts gone, R2), coverage 0 uncovered.
- Finding status: 4 accepted (document-level mismatch; closure dependent on hardware, G-W12); 5 accepted, dependent
  on hardware (MEASURED-PARTS); 7 accepted (docs, toolset, insert repair); (a)/(b) presented, not applied.

### r2 interface requests (from R4)
- **R1 / integrator:** keeper screws that are PT 3.0 x 12 go into `layout.SCREWS` (make_bom counts them). Then
  `COTS['pt_screws']` name "4 x PT 3.0 x 12 PH1" and mass 3.2 need the new count (layout section 6, not an R block).
- **Integrator (DESIGN s9 / SPEC s10):** add G-W12 and G-MP-PACK, G-MP-X1203, G-MP-EVF, G-MP-ENC, G-MP-SW,
  G-MP-STICK (MEASURED-PARTS.md) to the gate lists; "G-W1 to G-W11" -> "G-W1 to G-W12".
- **Integrator:** re-run `python electronics/gs8-d2-v1/make_bom.py` after the r2 build writes `out/print-manifest.json`
  (printed masses currently come from the r1 manifest).
- **R1 / R2 (ASSEMBLY s7 service):** name tools from ASSEMBLY s1.1 by number; a new tool needs a row there and a
  `make_bom.py` line (tell R4 / the fixer).
- **R3:** `LOAD_BEARING_PARTS` still lists skirt_l / skirt_r although R2 removed them from PARTS.
- **R4 -> R1 (00:20, FASTENER-POLICY B):** the tub prints face down on -Y, so the vertical s_k1/s_k2 pilots are
  horizontal in the print (the weak case, like s_b). Policy: boss OD >= 7.0 (your 7.8 passes), pilot 2.5, engagement >= 7.0 + 1.0 tip
  reserve, >= 1.6 under the head (here the keeper), the 40 % modifier round the pilots (PRINT-GUIDE), and the M3
  insert fallback must fit (OD 7.8 keeps a 1.9 wall round the 4.0 insert pilot, >= 1.6). check_bosses must see s_k (R3).
- **R4 -> integrator:** ASSEMBLY s3 row 10 and DESIGN s9 say "G-W4 to G-W11" / "G-W1 to G-W11": add G-W12.

## r2 R1 options

**2026-10-05 00:15 machine time (R1, finding 1: destructive Pi service).** Today (r1): the X1203 + Pi 5 + cooler stack
sits on 4 floor bosses (top z 6.0; the kit screw heads in 5.6 x 2.4 pockets locate it in X/Y) and is held down by 4
floor snap hooks (pih1, pih2 on the USB edge x -91; pih3, pih4 on the port edge y 23.7). Their teeth catch under the Pi
PCB and their USB-edge beams sit under the jack overhang: no release path, removal breaks the tub. Counts are for the
whole camera (r1: 12 printed pieces, 4 PT screws).

| | A. Release windows for the 4 hooks | B. Relocated releasable latches | C. Removable keeper on PT 3.0 x 12 PH1 (chosen) |
|---|---|---|---|
| Printed parts | 12 (no change) | 12 (no change) | **13** (+ `pi_keeper`, black ASA, ~6 g est.) |
| Fasteners | 4 PT (no change) | 4 PT (no change) | **6 PT 3.0 x 12 PH1** (+2, same spec, same driver); kit M2.5 unchanged |
| Tools | 3 mm blade x4 + a second hand to lift | lever tool on 2-4 tabs | the existing straight PH1 driver only |
| Access (what must be off) | the USB-edge beams lie under the jacks and the stick-guide rail, the port beams under the HDMI/FPC plugs: the only line of sight is up through the floor, so the base, skirt_r **and** skirt_l, panel, hood come off | releasable latches fit only on the port edge (GPIO edge 0.2 and button edge 0.8 from the walls; USB edge under the jacks/rail): hood + panel off | hood + panel off (both come off before the stack in the r1 service order anyway); keeper slides out +Y through the open left side |
| Repeat-service effort | 4 beams deflected at once while lifting a 107 g stack with leads attached: poor | 2-4 levers held while tilting the stack | 2 screws out, slide keeper out; no flexure; 5 drives per boss, then the M3 insert fallback (FASTENER-POLICY) |
| Reuse class | 2.61 % nominal strain = one-time class; reusable (<= ~1.5-2 %) needs a longer beam than the 2.5 floor and 3.5 underfloor gap allow | needs >= 9 mm beams in the crowded 8.5 mm port strip | no snap: the keeper is rigid, clearance 0.1 over the X1203 |
| Positioning | bosses + pockets (unchanged) | port-only latches leave the stack to pivot about the port edge | bosses + pockets locate; keeper sits on its own 2 bosses, **0.1 above** the X1203 top and 0.25 off its edges: no positioning load |
| Print risk | floor windows under the boss field; hooks unchanged | long thin levers, high | low: prints top face down, no supports; tips 1.6 thick with a 45 deg back |
| CoM effect | nil | nil | + keeper ~6 g + 2 screws ~1.6 g, low (z 10-16) near x -85: a small rear/down shift (measured in the build) |

Not chosen variant C2: two single-screw keepers (USB edge, port edge): same screw count, one more part, and each needs
an anti-rotation key. **Choice: C**, one keeper with 4 fingers at the r1 hook stations (USB edge y -20, 12; port edge
x -80, -45), so the X1203 edge gate G-PI-1 keeps the same 4 zones, and the retention topology is not reduced.
Retention note (r1 and r2 alike): all 4 stations are on two adjacent edges (USB, port); the stack CoM (about x -47,
y -4) lies outside their hull, so an inverted 1 g load can tilt the button/GPIO corner up until it meets the parts
above. The GPIO edge (0.2) and button edge (0.8) leave no room for a finger. Recorded as open (R1-O1).

## r2 interface requests

- **R1 -> R2 (make_coupons.py), 00:16.** R1 deletes the 4 Pi floor hooks: `layout.PI_HOOKS` becomes `[]`, so
  `checks.snap_zones(L)` has no 'pih1' and `make_coupons.py` line 82 (`pz = zh['pih1']`) raises KeyError. Please
  drop the `pi_hook` coupon row (G-SNAP-1 is withdrawn with the hooks). R1 writes its keeper coupon in a separate
  `coupons_r1.py` (out/stl/coupons/coupon-pi-keeper*.stl), so make_coupons.py needs nothing else from R1.
- **R1 -> R4 (BOM / ASSEMBLY s7 tools), 00:16.** PT 3.0 x 12 PH1 quantity 4 -> **6** (s_k1, s_k2 hold the new
  printed `pi_keeper`); printed pieces 12 -> 13. `layout.COTS['pt_screws']` name/mass are updated in the R1 block
  (6 screws, 4.8 g est.). Tool for step 4 and service: the same straight PH1 driver; no new tool.
- **R1 -> R3 (checks.py), 00:16.** `L.PI_HOOK` stays defined (snap_strains guard), `L.PI_HOOKS = []`; checks.py
  lines 381-382 and 444 then skip cleanly. New screws s_k1/s_k2 (axis -Z, step 4, into 'tub', head_part
  'pi_keeper') are in SCREWS; insertion `keeper_in` (step 4) and removals `keeper_out`, `pi_out` in REMOVALS.
- **R1 status for the requests above (00:50).** R3 00:18 (`del` NameError): fixed 00:19. R4 (pt_screws count):
  done in the R1 block (6 screws, 4.8 g). R2 00:27 (panel_off vs keeper): the 00:24 keeper was an early draft; the
  current keeper keeps z >= 12.5 over both panel-boss sweeps and y <= 23.85 below that; R2's trial 00:47
  (out/_trial-r2) passes interference, sweeps, removals (keeper_out, pi_out, panel_off), driver and boss_geometry.
- **R1 -> integrator / docs (00:50).** (1) Run `coupons_r1.py` (3 STLs + `coupons-r1-manifest.json`, gate G-KEEP-1)
  after the out/ move; add its 3 coupons to PRINT-GUIDE s6. (2) PRINT-GUIDE: new part `pi_keeper` (black ASA, top
  face down +Z, no supports, 4 perimeters, 40 % gyroid); tub: 40 % modifier round the 2 keeper bosses. (3) DESIGN /
  SPEC J9 and the gate lists: G-SNAP-1 withdrawn (hooks deleted), new G-KEEP-1 (criteria in coupons_r1.GATE), G-PI-1
  now reads "X1203 edge parts clear of the 4 keeper finger zones" (same 4 stations, 0.65 over the edge, z 7.7-9.3).
  (4) Run `make_tables.py` once: R1 hand-edited only the step-4 block and the screws block to the generator's text.
- **R1 -> R4 (FASTENER-POLICY E, 00:50).** The M3 insert fallback (4.0 pilot) fits s_k1 (r 3.8: 1.8 wall). At s_k2
  (r 3.5 teardrop + 1.0 obround, clipped at the panel seam y 31.9) the +Y wall round a 4.0 pilot is 1.0 over the top
  2.2 mm (z 7.6-9.8, above the lip gusset), 2.0 elsewhere: list s_k2 as a marginal insert site (5 PT drives, then
  the insert with care, or a reprint of the tub).
- **R3 -> R1 (layout.py R1 block), 00:18.** `del _K, _sid, _x, _y, ...` (line ~874) raises NameError: list-comprehension
  variables (`_sid`, `_x`, `_y` in the SCREWS += [...] comprehension) do not leak in Python 3, so every import of
  layout.py fails (build, tests, checks). Please drop `_sid, _x, _y` from that `del`.
- **R3 -> R2, 00:18 (done).** checks.snap_zones adds skb_l/skb_r only while 'skirt_l' is in PARTS; SKIRTS/SKIRT_JOINT
  can go whenever test_common.py is clear. New optional `layout.SNAP_ZONES_EXTRA = {id: B(...)}` for latch zones a
  REMOVALS `release` can name.
- **R3 -> all, 00:18.** Trial builds: `build_d2.py --out cad/gs8-d2-v1/out/_trial-<role>` writes a full build to a
  side folder (the integrator's out/ and the r1 outputs stay untouched). `checks.py --critical/--evf/--removals
  [--parts a,b]` is the quick path (writes out/_quick/r3-quick.json).
- **R2 -> all, 00:25 (finding 3 decision).** skirt_l / skirt_r are ELIMINATED (table in "r2 R2 options"): gone from
  PARTS, MATES, STEPS 3 and 8, INSERTIONS (`base_on` moving list; `skirt_l_in` deleted) and LOAD_BEARING_PARTS (R2
  block). Printed pieces: 12 - 2 skirts + R1's keeper = **11**. `SKIRTS`, `SKIRT_JOINT` stay defined (marked) only for
  `test_common.py` line 54 (`L.SKIRTS['skirt_l']['box']` as a sample box): **integrator**, point that test at another
  box, then delete both dicts. `build_d2.py` explode offsets and `make_tables.py` keep harmless skirt branches.
- **R2 -> R3 (checks), 00:25.** R2 registry block: 28 CRITICAL_FEATURES (panel 11, base_grip 11, cap 6; ids
  `panel_end_land_front/_rear` replace your seeds because the land moved; your keyhole-lip seeds stay as they are), `EVF_STOP` (panel rib,
  gap 0.3), REMOVALS `panel_off` (the 4 screws are in both `off` and `unscrew`: drop them from the sweep context, audit
  them in the service state), SECTIONS `base-edge-x91` (the stop already shows in your `evf-board-x137`). The board's 6-direction arrest is written
  above EVF_STOP. NONSTRUCTURAL_EXCEPTIONS: none from R2 (the cap detent bump carries the closing load; measured 1.6
  along the slide). New physical gates: G-PANEL-1 (panel open/close with the PH1 only, coupons base_edge_*), G-EVF-2
  (stop gap 0.1-0.5 with the real board); G-CAP-1 now uses coupons cap_retention_*; G-SKIRT-1 is withdrawn.
- **R2 -> R4 / integrator (docs), 00:25.** ASSEMBLY steps 3 and 8 (generated block) were hand-edited to match the new
  STEPS text: re-run `make_tables.py` to regenerate. SPEC s2 table / s4 J5 / s6.5 list, DESIGN parts table and J5 row,
  PRINT-GUIDE skirt rows and OPTIONS (c) "applied" still mention the skirts. The look change (black band 16 -> 8 mm)
  is a user-visible decision: flag it in RECTIFICATION.md / RESPONSE.md; option (b) restores the band at +2 parts.
- **R2 -> integrator (coupons), 00:25.** `make_coupons.py` (+ `--out DIR` for trials) now writes 18 coupons: the
  pi_hook row is dropped (R1), and base_edge_base/_tub/_panel, cap_retention_grip/_cap, evf_stop_tub/_panel are new.
  Trial run 00:21 into scratch: all 18 valid. Run it into out/ only after the r1 outputs are moved.
- **R2 -> R1 (pi_keeper), 00:27.** R3 quick check 00:24: `panel_off` hits `pi_keeper` 228 mm3 at +Y 0.5, region
  x -105..-87, y 24.6..31.6, z 7.7..12 = the panel bosses boss_b1 (x -95..-87) and boss_b2 (x -109..-101), both
  y 24.1..35, z 2.6..12 (`layout.PANEL_BOSSES`). They also overlap at the final pose. Please keep the keeper at
  y <= 23.85 (boss y0 24.1 - SLIDE) wherever x is within -109.25..-86.75 and z < 12.25; the panel leaves along +Y, so
  nothing at y < 24.1 is in its path. All R2 features pass in that run; EVF restraint passes in all 6 directions.

## r2 R2 options

**2026-10-05 00:20 machine time. Finding 3: the panel opening depends on an inaccessible skirt barb (accepted).**
The cause: the 2 panel boss tabs (z 2.6..12) leave the tub lip notches along +Y straight through skirt_l (y 35.2..36.8,
z to +8), so skirt_l had to slide off -X 125 first, and its 0.8 barb sits inside the groove with no tool access. The
same J5 dovetail carries the 0.68/0.71 key necks and the 0.77 groove lips (finding 2), and a deeper key already hit
the strap slots (HANDOFF P-P7).

| | (a) accessible barb release | (b) skirt removable without forced flexure | **(c) eliminate the skirts (chosen)** |
|---|---|---|---|
| Change | a 3 mm blade slot from the base underside into the skirt_l barb dimple | skirt_l loses its barb, gets 2 U-notches round the boss tabs and is locked in X by the fitted panel; skirt_r keeps a fit-once barb | no skirts, no J5 grooves; plain base side faces; the existing boss tabs fill the lip notches flush |
| Printed parts | 12 | 12 | **10 (-2)**; J5 joints -2, barbs -2, assembly actions -2 |
| Access / tools to open the panel | PH1 + 3 mm blade from below, then slide skirt_l -X 125 | PH1 only | **PH1 only** (s_b1, s_b2 from below; s_r1, s_r2 from the right) |
| Repeat-opening effort | 4 screws + blade release + 125 mm slide + panel (7 operations); barb wear every cycle | 4 screws + panel (5); skirt_l is merely freed | **4 screws + panel (5)**; no flexing part, no wear item; limit = the PT screws (5 drives, then M3 inserts) |
| Print risk | the 0.68-0.77 key/groove sections stay unless the key is redesigned; the slot cuts the groove lip at the rear | same J5 thinness on both sides to fix | **removed with the joint**; lowest registered base_grip section 1.25 (cap detent arm at its dimple) |
| Strap | skirt_r groove 1.2 from the strap slots; a deeper key hits the strap (2.5 mm3, recorded) | same | **no interaction**: strap y -33.5..-21.5; the s_b drivers stand at y 27.85 (handle y 12.9..42.9) |
| Look | unchanged (black band z -8..+8) | band kept, 2 silver windows in it | **black band is the 8 mm base only**; the tub lip (z 0..7.9) and 2 flush boss tabs show silver on the left with 0.3 seams |

Choice (c): fewest parts, no flexure, no tool beyond the enclosure PH1, and it removes the thin J5 geometry instead of
thickening it inside an 8 mm base next to the strap. Grip/body separability (J4 keyholes + s_b1/s_b2), print
orientation (+Z, base top on the bed) and repair (base reprint alone) are unchanged. **User-visible:** the concept's
"1.6 mm skirts to z +8" band is gone (CONCEPT.md row "Under the body"); option (b) restores it at +2 parts if the
user prefers the band. Optics are not disturbed: the lens, eyecup, stick, cap and pack stay fitted for panel service;
the panel's EVF cap releases its spigot clamp (the eyepiece stays seated in the bore and half-collar).

Also in this pass (findings 2 and 6, R2 geometry), measured on the B-rep with OCP line intersection (scratch test,
not the release check; nothing printed): panel end land 1.30 (1.2 land square to the inner face, was a 0.67 feather;
it exposes a 0.82 x 1.2 strip of the tub wall end at each corner), cap key head tip 1.55 (was 0.8; key top -106.5 ->
-105.9), cap detent bump 1.6 along the slide and 1.2 tall (was 0.6), detent arm 1.50 / 1.25 at the dimple (dimple
13.8 -> 13.75), cap lips 1.70, key webs 1.6, keyhole lips 1.6, strap web 2.0, heel strap bar 2.5, tripod wall 2.3.
Found by the r2 trial screen and fixed (00:40-00:50): panel boss cap over the blind s_b pilot 1.0 -> 1.3 (boss top
12.0 -> 12.3); grip front wall at the run-pad recess top 1.0 -> 1.75 (pad boss to z -6, base opening stops at it);
0.2 boss slivers beside the dia 13.6 run hole removed (pad boss y +-7.0 -> +-8.3). Named NONSTRUCTURAL_EXCEPTIONS
(panel only): antirot_slot_skin 0.8 (face skin over the blind 18/24 tab slot) and badge_glyph_ridge 0.33 (ridge
between engraved badge strokes).
Also fixed (00:55-01:00, base_grip strap anchor and cap groove exit, pre-existing r1 geometry): the heel strap slots
moved from y -14..-1 to y -8.5..4.5 (they ended blind against the er 9 corner: 0.5-1.0 skins; now the bar measures
2.5-2.59 across the slot width); the cap-groove front-corner exit no longer leaves a feather (web passage from the
bottom only inside y 12.5; corner cut out to the outside forward of x -29.7; strip 1.275 at x -30). Trial screen
minima after the fixes: base_grip 1.435 (r1 0.77), cap 1.599 (r1 0.70), panel 0.799 = antirot_slot_skin (named).
EVF +Y stop: board contact starts between +0.30 and +0.35 of travel (gap 0.3, limit 0.6); panel/board 0 mm3.
panel_off at +Y 0.5..30: 0 mm3 against tub, hood and base_grip. cap_on: 0 closed, 0.1-0.26 mm3 while sliding (the
intended 0.1 detent interference).
- **R3 -> R2 / integrator, 00:36 (classification needed; informational, does not gate).** New
  `checks.unclassified_thin_spots` (checks.json `results.unclassified_thin_spots`, receipt `unclassified_thin_spots`)
  lists thin-wall screen samples under the wall threshold on LOAD_BEARING_PARTS farther than 2.5 mm from every
  CRITICAL_FEATURES origin/span and every NONSTRUCTURAL_EXCEPTIONS `at`. Trial build 00:31 (out/_trial-r3):
  - panel (-23.9, 35.0, 88.0) t 0.33: a 0.3 z-sliver at the face (looks like a ridge between engraved strokes): R2,
    a named exception with `at=` if cosmetic (note: 0.3 is under one 0.4 extrusion), else fix;
  - panel (-122.5, 34.2, 64.9) t 0.80 and (-89.9, 27.6, 11.0) t 1.00 (near the boss_b1 tab): R2 to classify;
  - base_grip (-25.5, +-2.6, -8.1..-8.5) t 1.00 (base-opening front edge, underside): R2 to classify;
  - hood (-43.0, -32.1, 87.8) t 1.05: the J1 hook TOOTH root (land 0.4 + 0.65 lead = 1.05 high at the beam face;
    the hook_hk* entries measure the 1.6 beam, not the tooth). No r2 owner for the hood: integrator/fixer decides
    (structural entry with a stated lug minimum, or grow the land). Not changed by R3.
- **R3 -> integrator (make_tables.py, unowned in r2), 00:49.** The receipt key `release_candidate` is renamed
  `cad_release_candidate`; make_tables.py line ~464 still reads `d.get('release_candidate')` (prints None). Please
  read `cad_release_candidate` and print `status_states` (cad_checks computed; slicer_review, coupon_validation,
  measured_fit, assembly_operation "not run") and `open_evidence` next to it.

## r2 R3 (findings 2-checks, 6-check, 8)

**2026-10-05 00:00-00:50 machine time. Done.** Owner files: checks.py, build_d2.py, layout.py `# --- R3` block.
- **Finding 2 (accepted, confirmed).** r1 `loaded_boxes()` gave base_grip and cap 0 loaded samples, and the share
  rule passed a part with a local 0.33 spot. Options compared: (a) more loaded boxes in the share screen; (b) a
  registry of named sections measured exactly. Chose (b): `check_critical_features` measures every CRITICAL_FEATURES
  entry with an exact B-rep chord (OCP IntCurvesFace_ShapeIntersector + BRepClass3d), FAILs structural < min_mm, a
  stale origin (outside the material) and a LOAD_BEARING_PARTS member without a structural entry. The share screen
  stays as a secondary screen: a fail still blocks, a pass proves nothing (`cad_release_candidate` also requires
  critical_features = pass); no loaded samples now reads None, not 0. `unclassified_thin_spots` (info) lists screen
  samples under the wall threshold that no entry or named exception covers (6 left, see interface requests).
- **Finding 6 (accepted, confirmed on r1 geometry).** `check_evf_restraint`: translation sweep of the board in
  +-X/+-Y/+-Z against tub/panel/hood, limit 0.6 (2 x SL + 0.1). r1 geometry: +Y 4.2 to the panel (FAIL). With R2's
  panel stop: +X 0.25, -X 0.25, +Y 0.30 (panel, PCB only), -Y 0.30 (tub; flag: 29 % of the contact on the HDMI
  receptacle proxy, verify on the real board), +Z 0.25, -Z 0.25. Sections: renders/section-evf-board-z78.png,
  -x137.png, section-pi-keeper-y-20.png (+ R1/R2 sections).
- **Findings 1/3 service paths.** `check_removals` (REMOVALS, service state, release zones only where named) and
  `service_driver` (straight-driver audit of `unscrew` screws in the service state); coverage rows require a path
  for 'pi5' and 'panel'. Trial: keeper_out, pi_out, panel_off pass; s_k1/s_k2/s_b1/s_b2/s_r1/s_r2 pass in service.
- **Finding 8 (accepted).** Receipt: `status_states` (cad_checks computed with totals + checks.json sha256;
  slicer_review / coupon_validation / measured_fit / assembly_operation "not run" unless files exist in
  evidence/<slicer|coupons|measured|assembly>/), `cad_release_candidate` + note (not a hardware or finished-camera
  claim), `open_evidence`, `hardware_gates` (29 G- ids from MEASURED-PARTS/SPEC/WIRING, all open), print time and
  mass labelled estimates (receipt + print-manifest), coupon STLs and coupon scripts hash-linked.
- **Builds.** `build_d2.py --out cad/gs8-d2-v1/out/_trial-r3`: 00:43 full build, 297 s, no stubs, every check
  passes (critical_features 72 rows: 66 entries + 6 coverage; evf_restraint 6; removals 5; service_driver 6),
  cad_release_candidate true. out/ and the r1 outputs were not touched.

**Half-done:** nothing in the R3 scope. The 6 unclassified thin spots need owner decisions (R2: panel x3, base x2;
integrator: hood hook tooth root 1.05).

**Next step (integrator):** move out/ to out/_r1-2026-10-04/, run the release build into out/, switch make_tables
to `cad_release_candidate`/`status_states`.

## r2 R1 (finding 1: destructive Pi service)

**2026-10-05 00:50 machine time. Finding 1: accepted.** Options table: "r2 R1 options" (above). Choice: C, one
removable printed keeper on 2 more PT 3.0 x 12 PH1.

**Done.**
- `layout.py` R1 blocks: J9 (`PI_KEEPER`; `PI_HOOKS = []`, r1 stations kept as `PI_HOOKS_R1`; Pi boss OD 8.8 -> 9.0,
  pocket wall 1.6 -> 1.7), step 4 (keeper + s_k1/s_k2, tool = the straight PH1), INSERTIONS (`pi_in` no snaps,
  new `keeper_in`), registry block (PARTS `pi_keeper`, MATES, SCREWS s_k1/s_k2, COTS pt_screws 6 x / 4.8 g,
  LOAD_BEARING_PARTS, 22 CRITICAL_FEATURES, REMOVALS `keeper_out`/`pi_out`, 2 SECTIONS), `snap_strains()` guard.
- `printed_tub.py`: hooks + floor reliefs deleted; 2 teardrop PT bosses (s_k1 at (-99.5, 16.0) r 3.8 behind the USB
  end; s_k2 at (-64.0, 28.9) r 3.5 + 1.0 obround, chin apex 0.25 off the X1203 edge, clipped at the panel seam).
  Both screws could not go behind the USB end: the bridge over the panel bosses is only 3.1 deep, so the port bar
  needs its own screw; the port-strip boss is placed so its chin stays a 45 deg teardrop (tub prints +Y up).
- `printed_keeper.py` (new): arm (under the stick rail), bridge (z >= 12.5 over boss_b1/b2), port bar, 4 fingers at
  the r1 stations; prints top face down, no supports.
- `test_keeper.py` (new, R1 stand-alone test), `coupons_r1.py` (new, 3 coupons, gate G-KEEP-1), `test_tub.py`.
- ASSEMBLY.md: s1 Snaps row, step-4 block (= generator text), s3 row 4, s4 heading + screws rows, s7 item 10
  (non-destructive service with tools 1 and 12).

**Computed results (CAD only; nothing printed or measured).** test_keeper 00:48 and R2 full trial 00:47
(out/_trial-r2): keeper valid, 6262 mm3, 6.7 g est., print 64.0 x 54.9 x 7.9 (both beds); keeper/tub contact,
0.000 mm3; keeper to X1203 0.10, to kit 1.25, to Pi 2.90; no keep-out overlap; sweeps pi_in and keeper_in 0 hits;
straight driver s_k1, s_k2 at step 4 pass (bit 1.23 from the counterbore wall), service driver pass; removals
keeper_out, pi_out pass; check_bosses s_k1/s_k2 pilot 2.5, depth 8.6 (need 8.5), wall 2.55/2.60 (need 2.25), under
head 4.5 (need 1.6); thin-wall screen keeper min 1.41, tub min 1.25 (secondary screen); critical features: finger
tips 1.70 (min 1.6), arm 5.8, bridge 3.1, bar 4.5, keeper bosses 2.55/2.75, Pi bosses 1.7 (port) / 4.0 (front),
pads 1.9, tongue necks 8.0, camera pins 1.9: all pass. CoM effect of keeper + 2 screws (8.3 g at about
(-85.6, 13.4, 12.4)): -0.40 x, +0.12 y, -0.13 z mm on the Kowa total. Coupons (out/_trial-r1): 3 valid STLs.

**Open (R1).**
- R1-O1 (new observation, applies to r1 too): all 4 retention stations are on 2 adjacent edges; the stack CoM
  (about (-54.5, -7.4)) lies 16 mm outside their hull, so an inverted load can tilt the GPIO/button corner up until
  it meets the parts above. No room for a finger on the GPIO edge (0.2) or button edge (0.8). Candidate: a stop on
  the hood or a right-wall PT keeper over the GPIO-side kit screw head; not attempted. Dependent on hardware
  (bench tilt test with the real stack).
- G-PI-1 (X1203 edge parts clear of the 4 finger zones) and G-KEEP-1 (coupons) are open; G-PT-1 covers the 2 new
  bosses (pilot horizontal in print, the weak case). s_k2 insert fallback marginal (see interface request to R4).
- The generated screws table prints "dia 7 ... z 14.3..15.6" for s_k2; it is a 7.0-wide spot-face notch across the
  bar, not a round counterbore.

**Next step.** Integrator: make_tables, coupons_r1 into out/, PRINT-GUIDE and DESIGN/SPEC J9 text (requests above).
Then print the 3 coupons and run G-KEEP-1; bench G-PI-1 with the real X1203.

## r2 R2

**2026-10-05 00:00-01:05 machine time. Done** (findings 3, 2-geometry, 6-geometry; nothing printed or measured).
- Finding 3 (accepted): option (c) chosen and built, skirts eliminated (table above). Panel opening = 4 PH1 screws +
  pull +Y, no blade, no flexure; `REMOVALS` panel_off passes with the strap, cap, pack, lens and stick fitted.
- Finding 2 geometry (accepted): skirt necks/groove lips removed with the joint; panel end land 1.30; cap retention
  >= 1.25 everywhere (head tip 1.55, bump 1.6, detent arm 1.50/1.25); plus the boss cap, pad-top wall, run-hole
  slivers, heel slots and groove-exit feather found by the trial screen. 28 R2 CRITICAL_FEATURES, all pass (R3
  check, trial build `out/_trial-r2` 00:57: every check passes, `cad_release_candidate` true, stubs none).
- Finding 6 geometry (accepted; physical part dependent on hardware): `EVF_STOP` panel rib, gap 0.3; R3's
  evf_restraint passes in all 6 directions; the section is R3's `evf-board-x137`.
- Coupons: make_coupons.py 18 (pi_hook dropped per R1; 7 new for G-PANEL-1, G-CAP-1, G-EVF-2), `--out` added, part
  builds cached. Trial output only in scratch; out/ untouched.
- ASSEMBLY.md: steps 3 and 8 text (generated block, hand-matched to STEPS), check row 3, s7 items 3-5 and 11.
- Files: printed_grip.py, printed_panel.py, make_coupons.py, test_grip_small.py (probes), layout.py (R2 lines marked
  `R2`: SKIRTS note, CAP box, CAP_JOINT, J3/J5 comments, PANEL_BOSSES z1 12.3, STRAP lower_slots, PARTS, MATES,
  STEPS 3/8, INSERTIONS, R2 registry block), NOTES.md, ASSEMBLY.md.

**Half-done:** none in R2 scope. Docs outside R2 scope still mention skirts (SPEC, DESIGN, PRINT-GUIDE, OPTIONS
status): requested from R4 / integrator above. `SKIRTS` / `SKIRT_JOINT` stay until test_common.py stops using them.

**Next step:** integrator: regenerate ASSEMBLY steps (`make_tables.py`), run `make_coupons.py` into out/ after the r1
outputs move, and flag the look change (black band 16 -> 8 mm) to the user. Physical: print the 7 new coupons; gates
G-PANEL-1 (5 open/close cycles, PH1 only), G-CAP-1 (20 slides, detent hold, 20 N pull-down), G-EVF-2 (stop gap 0.1-0.5
with the real board), all **not run**.

## r2 integrator

**2026-10-05 01:04-01:35 machine time. Done.**
- out/: the r1 build outputs (receipt, checks, manifests, renders, step, stl, Fujinon checks) moved to
  `out/_r1-2026-10-04/`. The r2 scratch folders `_trial-r1/-r2/-r3`, `_quick` were left in place (r2 work, not r1).
- Interface requests resolved: test_common.py samples a plain box, then `SKIRTS` / `SKIRT_JOINT` deleted from layout.py
  (make_tables skirt mass branch dropped); make_tables reads `cad_release_candidate` and prints `status_states` +
  `open_evidence`; R2's 2 NONSTRUCTURAL_EXCEPTIONS got `at=` (classifies the panel 0.80 spot); hood hook tooth root
  1.05 (no r2 owner): HOOK land 0.4 -> 0.6, catch_z 87.95 -> 88.15, tooth_top_z 87.85 -> 88.05 (length 10.5 kept, hk4
  tip clearance kept), new `# --- INTEGRATOR r2 registry` block with `hood_tooth_hk1..4` (1.22 / 1.2). build_d2.py
  `hardware_gates()` reports a gate as "withdrawn" when a gate doc says "<id>. Withdrawn" (G-SNAP-1, G-SKIRT-1).
  make_bom D2-41 text (no skirts).
- Builds: full 01:07 and final full 01:32:40: 19/19 checks pass, 496 rows, 0 stubs, `cad_release_candidate` true,
  `unclassified_thin_spots` none; Fujinon `--fast --sweep-step 1.0 --out out/_fujinon-r2` 01:15: all pass, copied to
  `out/checks-fujinon-sweep1mm.json`. Coupons: make_coupons 18 + coupons_r1 3 into out/stl/coupons. make_tables
  refreshed, `--check` stale none; BOM regenerated (11 printed, 6 PT).
- Renders read: hero keeps the D2 look; the visible change is the black band (16 -> 8 mm, skirts gone). Sections
  evf-board-x137 and pi-keeper-x80 checked.
- Docs: DESIGN (s1 r2 status box, s3, s4.1, s5 J1/J5/J6/J8/J9, s6b/6c, s7, s8, s9, s10), SPEC (r2 note, s2, s3 J1/J5/J9,
  screws s_k1/s_k2, s4, s5, s6 5/5c/5d/5e/9, s8, s9, s10 gates, s11), PRINT-GUIDE (material, tub, pi_keeper, s4, s5,
  s6 coupons, s7), ASSEMBLY row 10 G-W12, OPTIONS (c) note; `RECTIFICATION.md` written.

**Half-done:** none in the integrator scope. Not done here (other roles): HANDOFF.md update, audit RESPONSE.md (fixer).

**Next step:** fixer/verifiers: RESPONSE.md and HANDOFF.md from RECTIFICATION.md; user decisions (lens, black band,
OPTIONS a/b); then print the 21 coupons and run G-PT-1, G-KEEP-1, G-PANEL-1, G-CAP-1, G-EVF-2, G-SNAP-2.

## r2 fixer

**2026-10-05 01:47-03:30 machine time. Done** (all 21 verifier findings handled; nothing printed or measured).
- Geometry: s_k2 re-sited (-64, 28.25) r 3.6 with a flat chin at y 23.95 (wall 2.35 over the whole depth); hood hooks
  land 1.0, catch plane / tub ledges +0.4, ledge_h 1.7; hk1/hk2 dia 1.6 release holes (z 87.7) for 2 x dia 1.5 pins,
  hk3/hk4 45 deg return (`d2_common.snap_hook(ret_deg=)`, sloped ledge underside); panel boss tops 12.6, keeper bridge
  underside 12.85; EVF bottom rail gap 3..18, +X spine 0.6 off the plug envelope (+0.65 outward), top rail -X wall
  relieved 0.4 over the ZIF; cap key/groove top +0.1; J4 lock screw s_j (-111, -20) from below at step 3 (tub floor
  boss OD 8 to z 12.6; 7 PT screws); hood stack-stop post + fin over the far kit screw head (gap 0.15).
- Checks: `check_bosses` 7 levels 5-95 %; feature classes (`FEATURE_CLASS_RULES`, gated `flexure`); clearance J9;
  `evf_restraint` per zone + plug envelope; `removal_coverage` "parts taken off" + hood; `check_release_access`;
  `check_stack_retention` (hull + LP lift bound; without the post the LP gives 0.58 max lift, so r2's "hinge about
  kf1-kf4" was bounded by the boss tops, but the CoM lay 16 mm outside the hull).
- build_d2: whole-token gate match, per-item evidence with verdict lines, EVF-SELECTION gates (EVF-G*), Fujinon and
  coupons-r1 manifests hash-linked.
- Coupons: G-KEEP-1 whole keeper + floor coupon + 2 stand-in boards (`coupon-pi-keeper-board` moved to
  `out/_stale-r2-fixer/`); G-SNAP-2 adds `hood_hook_ret` / `hood_ledge_ret`.
- Docs: WIRING s4/s9/s10 (envelope 17.7-22.1 W, gate order, G-W5 8.6 A step, G-W12 B through the XT30, failure
  actions), FASTENER-POLICY (per-boss drill table, s_j, ISO 7045 k 2.1), MEASURED-PARTS (EVF-G ids, un-chosen variants,
  MP-FPC, cooler line), SPEC, PRINT-GUIDE, ASSEMBLY (s1.1 tool 9 = pins, s7 items 3/9/10/11), OPTIONS, BOM (7 PT,
  contingency, `%%`), DESIGN (s1, s2 wording, s3, s6d), RECTIFICATION (rewritten), HANDOFF (rewritten),
  `audit/d2-readiness-2026-10-04/RESPONSE.md`.
- Builds: trial builds in `out/_trial-fixer`; final coupons 03:28, Fujinon 03:34 and release build **03:39:36** (21/21, 526 rows,
  0 stubs, `cad_release_candidate` true); make_tables `--check` stale none; BOM regenerated. The integrator's 01:32
  JSONs are kept in `out/_r2-integrator-0132/`.

Late fix: the tub rear-wall feather at the panel seam (the bore's teardrop roof ran out through y 32.2; screen 0.25)
is notched 1.2 deep (`printed_tub._rear`); its temporary named exception was removed.

**Half-done / open:** the cap detent strip stays below 1.6 (gated flexure, G-CAP-1); the hood plunger-channel web 1.08 (named);
no per-joint coverage rule; ISO 7045 k checked against one table only (Engineers Edge).

**Next step:** the user's decisions (HANDOFF s4), then HANDOFF s5 in order: measure parts + EVF bench (with G-W6),
slice, coupons, geometry updates only where measurements differ, print set, service cycles, G-W12.

## r3 electronics (started 09:15; finish-by 11:30)

Progress log (a re-spawned electronics agent continues from here):
- 09:15 read R3-BRIEF, REVIEW (findings 4, "Gates that still control"), WIRING.md, MEASURED-PARTS.md. Plan: (1) EVF feed
  regulator requirement in WIRING s4.8 (new) + G-W6 fail path + MP-EVF + make_bom contingency line; (2) power wording;
  (3) status blocks; (4) MP-* counts; (5) BOM regen.
- 09:20 regulator analysis done: 4.55 V LDO (XC6210 class, [to confirm]) as the PRIMARY feed with the diode deleted
  (option C); diode in front fails headroom (3.95 V); new gate id **G-W13** (regulator bench qualification) + G-W6
  regulated-lead run. Box check: `out/_trial-r3-elec/reg_envelope.py/.json` (plain Python, not a CAD run):
  16 x 7.5 x 4.5 envelope inside ko_5v_up z 40..56, no keep-out/COTS overlap -> pass. 1 web search used (XC6210).
- 09:30 WIRING.md: status block (top), W-3/W-9, s4.1/4.4/4.6 power wording, new s4.8 (R-EVF-REG + comparison +
  recommendation), G-W6 fail path + regulated-lead run, new G-W13 row, s10 items. MEASURED-PARTS: status block, record
  count (10; cooler row relabelled "MP-X1203 (cooler line...)"), MP-EVF step 7 / gates / "If it fails". make_bom.py:
  kit counts from X1203_KIT, D2-16R/C/P candidate lines (qty 0), contingency row replaced, D2-63 joints derived, status
  line; BOM regenerated 09:29 (59 lines, totals unchanged; r2 copies in the session scratchpad bom-r2/).
- 09:25 BOM build counts point to DESIGN.md s1.1; BOM regenerated again (09:25); `make_tables.py --lint` 0
  disagreeing (counts(): pt 7, mp 10). Interface requests posted (docs, integrate-baseline/final-docs).

**Done (09:27):** (1) EVF feed regulator resolved as requirement **R-EVF-REG** (WIRING s4.8): setpoint 4.55 V, band
4.39-4.71 V (terminals 4.375-4.71: margins 0.125 / 0.19 V), input 4.715-5.355 V at the regulator, dropout <= 0.30 V
at 0.30 A (dropout case 4.40 V at the terminals), <= 0.29 W, rise <= 44 C at <= 150 C/W, ripple <= 50 mV p-p,
envelope 16 x 7.5 x 4.5 in `ko_5v_up` z 40..56 (box check pass). **Decision (candidate, user decides): option C,
LDO as the primary feed, diode deleted** (diode in front fails: 3.95 V; regulator as fail branch ends in C anyway).
Candidate device class Torex XC6210 [to confirm items listed]. **Gate: G-W13** (new) + G-W6 regulated-lead run + G-W7
re-run. (2) Power: 27 W vs 25.5 W kept, 17.7-22.1 W stated as not a demonstrated margin (W-9, 4.1, 4.4, 4.6, s10);
G-W12 open. (3) Status blocks in WIRING, MEASURED-PARTS, BOM. (4) MP count 10 derivable; kit 8 screws + 4 standoffs
derived from X1203_KIT apart from 7 PT. (5) BOM regenerated.
**Half-done:** none in my files. OPTIONS/ASSEMBLY/HANDOFF/DESIGN wording about the old "+1 part / +2 joints"
contingency is requested from their owners (interface requests 09:26).
**Next:** user decides option C; on receipt run G-W13, then G-W6 (regulated run); confirm the XC6210 [to confirm]
items from the full datasheet before ordering.

## r3 checks

(checks role, 2026-10-05, progress record; a re-spawned checks agent continues from here)
- 09:35 started. Plan: checks.py (critical features: origin always, expect_outside, CRITICAL_JOINTS; removal rows
  relabelled geometry-only when the pack stays fitted), build_d2.py (ROOT discovery, structured evidence records,
  summarize strictness, variant), layout R3 block (CRITICAL_JOINTS + missing probes), test_r3_regressions.py,
  evidence/README.md + template, SPEC checks/evidence text, trial build out/_trial-r3-checks.
- 09:40 code done (not yet trial-built): build_d2.py evidence block replaced (find_root/ROOT, load_records,
  evaluate_item, evidence_state, open_evidence_list, CALIBRATION_ITEMS G-KNOB-1/G-COMB-1/G-J4-1, summarize strict,
  variant); checks.py (feature_offsets, check_critical_features, check_joint_coverage, SERVICE_GEOMETRY_ONLY scope on
  fitted-pack removal/service_driver rows); layout R3 block (5 new probes, CRITICAL_JOINTS 12 joints,
  SERVICE_GEOMETRY_ONLY_NOTE); test_r3_regressions.py 18/18 pass. r2 copies: scratchpad build_d2.r2.py/checks.r2.py
  (and candidate-fr1/_base/). --part panel run: all panel probes pass (new: locate ribs 1.2, side hooks 1.6, b2 cap 1.6).
- 10:15 DONE (all 8 task items). Trial `out/_trial-r3-checks` (built 10:12:24, `--fast --sweep-step 1.0`): all 21
  categories pass (critical_features 118 rows: 109 pass, 9 info = 3 G-CAP-1 gated flexures + 6 named exceptions/
  coverage info; 12 CRITICAL_JOINTS pass), cad_release_candidate true, variant None. All 11 production STLs are
  byte-identical to out/stl/*.stl (sha256 listed in the checks role's final answer). Coupons are not rebuilt by
  build_d2.py (make_coupons.py); evidence reads them from out/stl/coupons. open_evidence = all four states "not run"
  (11 / 9 / 17 / 22 items). Nothing printed, sliced, measured or powered.
  First trial (09:3x) exposed one stricter-check result, not a geometry defect: `tub_evf_groove_wall_bot_px` span ray
  at offset -0.5 (y 1.5) misses the solid because printed_tub cuts the +X groove wall for y < ko_5v_end y1 + SEAM = 1.8
  (5 V lead end relief, by design; r2 skipped this miss silently). Declared in layout R3 block `EXPECT_OUTSIDE` with
  that reason (the rays at y 2.0/2.5 measure 1.3). No origin was stale: hood_groove_lower_lip origin now measured (pass).
  No existing entry or origin was edited; no threshold changed.
  New probes (R3 block): panel_locate_rib_f/_r (1.2, class wall: locating only; REVIEW whether the ribs should be
  treated as load-carrying lugs, which would need 1.6 = a geometry change), panel_encoder_hook_side_l/_r (1.6),
  panel_boss_b2_cap (1.6), base_sb2_head_floor, base_sj_head_floor (boss class). CRITICAL_JOINTS: J1, J2, J3, J4,
  J6 (flexures as G-CAP-1 gated exceptions, status info), J7, J8, J9 keeper, J9 stack stop, J12, J13 grip, J13 strap.
  Calibration ids: G-KNOB-1, G-COMB-1, G-J4-1 (CALIBRATION_ITEMS). Relabel: removals/service_driver rows with the
  pack fitted carry `scope` (SERVICE_GEOMETRY_ONLY_NOTE): panel_off, hood_off, camera_out, eyepiece_out, evf_out.
  Tests: `.venv-cad/Scripts/python.exe -B cad/gs8-d2-v1/test_r3_regressions.py --against-r2` -> 18/18 pass; the 7
  comparable cases show the defect in the r2 code (candidate-fr1/_base). Trial: `.venv-cad/Scripts/python.exe
  cad/gs8-d2-v1/run_locked.py --max-wait-min 4 -- cad/gs8-d2-v1/build_d2.py --fast --sweep-step 1.0 --out
  cad/gs8-d2-v1/out/_trial-r3-checks`. Half-done: none. Next: integrate-baseline promotes (full build with renders),
  integrate-fork copies build_d2.py/checks.py verbatim and merges FR_JOINTS into CRITICAL_JOINTS.

## r3 docs

(docs role, baseline, 2026-10-05, finish-by 11:30; progress record, a re-spawned docs agent continues from here)
- 09:14 started; read R3-BRIEF, REVIEW s1 + s4.
- 09:18 ASSEMBLY.md: isolation prerequisite P1-P4 at the head of s7 (every route, panel-only included); "Power last"
  row (s1) covers initial assembly; s6 microSD points to P1-P4; s7 items 2-11 reference item 1; `panel_off` sweep
  worded geometry-only; item 10 far-corner tilt = CAD restraint added (hood stack-stop post, `stack_retention`),
  physical tilt/knock test open (G-KEEP-1 follow-up). Steps block (generated from layout.STEPS) not touched.
- 09:20 make_tables.py: `counts()` + `blk_counts` (DESIGN.md s1.1 `counts` block, refreshed with `--docs design`),
  `lint_counts()` run by `--check` (and `--lint`), `--docs a,b` (CSV/SVG only when wiring is selected). Fixed
  OPTIONS (6->7 PT, 9->10 MP records), FASTENER-POLICY count, PRINT-GUIDE s6 heading (21->24), DESIGN s1 option ref.
- 09:26 PRINT-GUIDE s6.1: calibration/fit records G-KNOB-1, G-COMB-1, G-J4-1 (ids taken from the checks role's
  `build_d2.py` CALIBRATION_ITEMS; the brief's fallback CAL-* ids not used) + how to file an evidence record. DESIGN
  s6e records the r3 docs corrections. make_tables: `lint_selftest()` (the audit's r2 phrases must be flagged; run by
  --check/--lint); missing coupon output -> counts "n/a" + lint flags. Regression: lint on the r2 zip's docs flags
  exactly FASTENER-POLICY:13, OPTIONS:25, OPTIONS:31, PRINT-GUIDE:135. `--check`: stale none, lint 0, selftest ok.
- 09:26 electronics -> docs request done: OPTIONS.md solder-joint/contingency rows and r2 totals, ASSEMBLY s1.1 row 2
  now say "+11 joints, +3 parts under EVF-feed option C (WIRING s4.8)"; the r2 "+1 regulated module" is marked withdrawn.
  DESIGN s9 G-W1 to G-W13; ASSEMBLY s3 step 10 adds G-W13 if option C is adopted.
- State at 09:27: all 5 task items done; `make_tables.py --check` stale none, lint 0, selftest ok. Half-done: none.
  Next (integrator / final-docs): full make_tables refresh after the electronics role; HANDOFF/RECTIFICATION edits
  requested under "r3 interface requests"; if the checks role renames G-KNOB-1 / G-COMB-1 / G-J4-1, update
  PRINT-GUIDE s6.1 and DESIGN s6e.

## r3 interface requests

(shared section: each role appends its requests here, prefixed "<from> -> <to>")
- docs -> checks (09:23, updated 09:26): PRINT-GUIDE s6.1 names the three calibration/fit records with the ids of
  `build_d2.py` `CALIBRATION_ITEMS`: **G-KNOB-1** (knob-bore ladder), **G-COMB-1** (clearance comb), **G-J4-1** (J4
  tongue/keyhole fit), and tells the reader to file them per `evidence/README.md` (item = id, state coupon_validation,
  artifacts = {path: sha256}). If you rename them, post the new ids here (docs role until 11:30, else integrator).
- docs -> checks (09:23): ASSEMBLY s7 item 10 / DESIGN s6 call the far-corner stack tilt test "G-KEEP-1 follow-up"
  (bench tilt/knock + retention with the real stack under a printed hood). If you register a separate hardware gate id
  for it, post it here.
- docs -> integrate-baseline (09:23): DESIGN.md has a new generated block `counts` (s1.1). `make_tables.py --check`
  now also runs a handwritten-count lint (exit 1 on a disagreement). The full refresh (no `--docs`) rewrites WIRING.md
  and the electronics CSV/SVG: run it only after the electronics role is done. `--docs design,print,assembly` refreshes
  only those docs.
- docs -> final-docs / RECTIFICATION+HANDOFF owner (09:23): (1) RECTIFICATION.md:83 "`removals` panel_off (strap, cap,
  pack, lens, stick fitted)": label it geometry evidence only and cite ASSEMBLY s7 P1-P4 (pack out before any internal
  service; a halted Pi is not isolation). (2) HANDOFF.md:59-60 "R2 option (b) restores it": say "R2's finding-3
  option (b) (NOTES "r2 R2 options"), not OPTIONS.md (b) = shorter FPC". (3) Counts: point to DESIGN.md s1.1.
- docs -> electronics (09:23): no count mismatch found in electronics/gs8-d2-v1/*.md by the lint. Suggest BOM.md
  "Build counts" point to DESIGN.md s1.1 and list the X1203 kit screws/standoffs (8 / 4) as a separate row. If the
  EVF-feed change (diode deleted, LDO primary) lands, ASSEMBLY s1.1 row 2 ("10 joints") and the step-1 text, which is
  generated from `layout.STEPS` (not docs-owned), need the new joint list: post the new count here.
- electronics -> docs (09:26): EVF feed (WIRING s4.8): the r2 "+1 regulated EVF feed module / +2 joints if G-W6
  fails" wording is withdrawn (a 5.0 V output breaks the 4.90 V maximum). The resolved candidate is **option C: a
  4.55 V LDO on a carrier replaces the 1N5817 (net +3 parts, +11 solder joints), recommended as the primary feed, user
  decision, quantity 0 in the BOM (D2-16R/C/P)**. Please reword OPTIONS.md:23-24 and 36-37 and ASSEMBLY.md:39
  ("+2 if G-W6 calls for the regulated EVF feed") to "+11 joints, +3 parts under EVF-feed option C (WIRING s4.8)".
  The baseline joint count stays 10 (the diode lead is still the baseline); layout.STEPS step-1 text needs no change
  unless option C is adopted.
- electronics -> integrate-baseline / final-docs (09:26): (1) new open hardware gate **G-W13** (EVF feed regulator
  bench qualification) is in WIRING s9 and MEASURED-PARTS, so build_d2's gate scan will list it (open). (2)
  HANDOFF.md:34 and :85 still say "+2 if G-W6 calls for the regulated EVF feed" / "regulated feed (+1 part": point them
  to WIRING s4.8 option C. DESIGN.md:351 "G-W1 to G-W12" -> "G-W1 to G-W13". (3) BOM regenerated 09:25 with
  make_bom.py (writes only BOM.md and bom.csv); re-run it after any layout change. make_tables `--lint`: 0 disagreeing.
- electronics -> checks (09:26): none needed. layout `CABLES['usb_5v']` keeps its 1N5817 name (baseline unchanged).
- checks -> docs / integrate-baseline / fork (09:58): the calibration ids are final: **G-KNOB-1** (coupons
  knob_bore_ladder_enc + knob_bore_ladder_sw), **G-COMB-1** (clearance_comb), **G-J4-1** (tongue + keyhole_slot),
  required coupon_validation items in `build_d2.py` CALIBRATION_ITEMS and named in SPEC s6 item 10 and
  `evidence/README.md`. The far-corner stack tilt test: no separate gate id registered by the checks role (it stays
  "G-KEEP-1 follow-up"); if someone registers one, add it to a gate doc and the build lists it automatically.
- checks -> integrate-fork (09:58): build_d2.py and checks.py are now location-independent (ROOT = nearest folder with
  cad/ + electronics/; release docs from ROOT/cad/gs8-d2-v1; electronics docs from ROOT/electronics; evidence dir stays
  HERE/evidence; coupons from the build's --out dir, else HERE/out/stl/coupons). Copy them verbatim into the fork.
  The fork's FR_JOINTS / FR_REMOVED_FEATURES must be merged into `CRITICAL_JOINTS` (layout R3 block): a joint whose
  required id is gone FAILs (by design); replace the ids in that joint's `required` list (or the joint) per FR block.
  Removing a feature without updating CRITICAL_JOINTS = critical_features FAIL. `variant` = L.FR_STATE goes into the
  receipt and checks.json.
- checks -> docs (09:58): rows of `removals` / `service_driver` whose service state keeps the pack fitted now carry
  `scope` = "clearance with the cap and pack fitted; geometry only: electronic service still requires shutdown and
  XT30 disconnection first (ASSEMBLY s1)" (layout SERVICE_GEOMETRY_ONLY_NOTE). ASSEMBLY quotes may cite this field.
- integrate-baseline -> fork roles (10:58): the baseline promotion needs the CAD lock for two builds (Fujinon --fast
  1 mm, about 5 min; Kowa full release with renders/STEP at 1 mm, about 10-12 min). Since 10:16 the lock has been busy
  at every try. Between your runs please leave a short gap (a minute) so run_locked waiters can take the lock.
- integrate-fork -> checks / final-docs (13:55): (1) `summarize()` reports an EMPTY category as "pass" (fork
  release_access has 0 rows under hood=yslide/screw1: nothing to release). The brief's rule ("an informational category
  must contain an actual passing result") arguably applies; suggest status "n/a" for n == 0. Not changed in the fork
  (checks.py is a verbatim copy); CANDIDATE.md reports it as n/a. (2) `checks.clearance_zones` is hard-coded; the
  fork keeper asks for a zone "J9 keeper tongue in tub seat (0.15)" -> suggest a registry hook (e.g. layout
  `EXTRA_CLEARANCE_ZONES`). (3) Decision asked by checks (locate ribs 1.2): in the fork, the FR panel keys that carry
  the bottom-edge load are probed as lugs (1.6: panel_key_b*_shear 8.0, _tab 10.9) inside CRITICAL_JOINTS
  FR_panel_keys; the ribs stay locating walls.
- fix-baseline -> integrate-fork / final-docs (12:25): baseline checks.py now FAILs unless layout has
  `REQUIRED_JOINT_IDS` (12 baseline joint ids, R3 block) and every id is in CRITICAL_JOINTS or named in a fork joint's
  `replaces` (FR_JOINTS). When the fork merges this checks.py, also merge the REQUIRED_JOINT_IDS line into the fork
  R3 block, and make each FR joint that removes a baseline joint list that joint id in `replaces`. J6_cap_grip now
  reports `info` (rests on G-CAP-1), not `pass`; critical_features counts move from 109 pass / 9 info to 108 / 10.
  Evidence: new outcome `rejected`; measured_fit / assembly_operation records must name the gate doc (+ all production
  STLs for assembly) - see evidence/README.md. HANDOFF/RECTIFICATION/DESIGN edits by fix-baseline are listed in
  "r3 fix-baseline".

## r3 integrate-baseline

(integrate-baseline role, 2026-10-05, finish-by 13:45; progress record, a re-spawned integrator continues from here)
- 10:15 started; read R3-BRIEF, NOTES r2 integrator/fixer, r3 checks/docs/electronics/interface requests.
- 10:15 reconciled: layout SERVICE_GEOMETRY_ONLY_NOTE + checks.py fallback + SPEC s6 quote now cite 'ASSEMBLY s7 P1-P4' (was 'ASSEMBLY s1'; text only, no geometry); SPEC.md:353 + make_bom D2-64 'G-W1 to G-W13'; HANDOFF.md:34/:59-60/:85 (option C wording, R2 finding-3 option (b), counts -> DESIGN s1.1); RECTIFICATION.md panel_off geometry-only + regulated-feed withdrawn notes. Calibration ids agree (build_d2 CALIBRATION_ITEMS = PRINT-GUIDE s6.1 = SPEC s6 = evidence/README).
- 10:15 r2 top-level release outputs copied to out/_r2-2026-10-05/ (77 files incl. stl/ 11 + 24 coupons, step/, renders/); sha256 of every copy verified against out/ (out/_r2-2026-10-05/SHA256SUMS, sha256sum -c ALL_OK).
- 10:20 make_coupons.py (into out/): 20 coupons; all 20 coupon STLs and coupons-manifest.json byte-identical to the r2 copies.
- 10:31 coupons_r1.py (into out/): 4 coupon-pi-keeper STLs + coupons-r1-manifest.json byte-identical to r2. All 24 coupon STLs identical.
- 10:33-10:50 Fujinon build: lock busy (fork roles), exit 75 x4; retrying. Next: Fujinon --fast --lens fujinon_hf6xa --sweep-step 1.0 --out out/_fujinon-r3 -> copy checks.json to out/checks-fujinon-sweep1mm.json; then Kowa full build --sweep-step 1.0 into out/.
- 11:04-11:26 Fujinon: build_d2.py --fast --lens fujinon_hf6xa --sweep-step 1.0 --out out/_fujinon-r3 (got the lock 11:04, built_at 11:26:04, 1114 s; machine slow, low free RAM): 21/21 categories pass, 542 rows, critical_features 118 (109 pass, 9 info), cad_release_candidate true, stubs none; 11/11 Fujinon production STLs byte-identical to out/_fujinon-r2/stl (the r2 fixer's 03:34 Fujinon build). checks.json copied to out/checks-fujinon-sweep1mm.json (sha256 5737...8d0d). Next: Kowa full release build.
- 11:26-11:31 Kowa release build: exit 75 (free RAM < 700 MB, then fork lock); retrying.
- 11:47-11:55 Kowa release: build_d2.py --sweep-step 1.0 into out/ (built_at 2026-10-05 11:55:41 +0800, 341.5 s): 21/21 categories pass, 542 rows, cad_release_candidate true, stubs/blocking/unclassified none, variant None. STL compare (scratchpad cmp_stl.py vs out/_r2-2026-10-05): production 11/11 and coupons 24/24 byte-identical. Receipt: 4 states 'not run' (11/9/17/22), 0 records, 0 rejected; every hardware gate open; G-W13 listed.
- 11:56 test_common.py: lock busy (exit 75), not rerun. out/test_common.json stays the r2 file (byte-identical to the
  _r2 copy); its inputs d2_common.py and test_common.py are byte-identical to baseline-r2-2026-10-05.zip, so it is current.
- 11:56 make_tables.py (full refresh, no --docs; electronics role done 09:27): only DESIGN.md changed (receipt status
  block: built_at 11:55:41, 542 rows, critical_features 118/109/9 info, open_evidence with per-state counts); WIRING.md
  and the electronics CSV/SVG unchanged. `--check`: stale none, count lint 0, selftest ok.
- 11:56 make_bom.py: 59 purchased lines, 11 printed parts, SGD 775.74 + 340.61 estimate, 1 unpriced (totals unchanged);
  only change D2-64 "gates G-W1 to G-W13". `make_tables.py --check` again: stale none, lint 0, selftest ok.

**Done (12:02).**
- Commands (repo root): `.venv-cad/Scripts/python.exe -B cad/gs8-d2-v1/layout.py` (129 checks, 0 failed);
  `.venv-cad/Scripts/python.exe -B cad/gs8-d2-v1/test_r3_regressions.py` (18/18); `make_tables.py --check` (stale
  none, lint 0); then under `run_locked.py --max-wait-min 4 --`: `make_coupons.py` (10:20), `coupons_r1.py` (10:31),
  `build_d2.py --fast --lens fujinon_hf6xa --sweep-step 1.0 --out cad/gs8-d2-v1/out/_fujinon-r3` (built 11:26:04),
  `build_d2.py --sweep-step 1.0` (release, built **2026-10-05 11:55:41 +0800**); `make_tables.py`, `make_bom.py`,
  `make_tables.py --check`.
- Release receipt: 21/21 categories pass (contract 11, cots_containment 20, interference 55, mate_overlap 30, clearance
  12, keepouts 81, bed_fit 11, stl_mesh 11, thin_wall 11, critical_features 118 = 109 pass + 9 info [3 G-CAP-1 gated
  flexures + 6 named exceptions/coverage info], evf_restraint 6, driver 7, engrave_groove 10, boss_geometry 7, sweeps
  12, removals 11, service_driver 6, release_access 2, stack_retention 1, layout_self_check 129, mass_com pass); 542
  rows; cad_release_candidate true (computed checks only); stubs, blocking, unclassified thin spots none; variant None.
  Fujinon 1 mm: the same 21/21, 542 rows. Note: the r2 release was built with argv [] (2 mm sweep step); r3's release
  uses --sweep-step 1.0 as the task asked.
- STL comparison against out/_r2-2026-10-05 (sha256): 11/11 production STLs and 24/24 coupon STLs byte-identical
  (hashes = those in the checks role's answer); coupons-manifest.json, coupons-r1-manifest.json byte-identical; 11/11
  Fujinon STLs identical to out/_fujinon-r2. All geometry sources (printed_*, d2_common, cots, make_coupons,
  coupons_r1) are byte-identical to baseline-r2-2026-10-05.zip; layout.py differs only by the inserted R3 block.
- Evidence in the receipt: 0 record files, 0 rejected; slicer_review not run 11, coupon_validation not run 9
  (incl. G-KNOB-1, G-COMB-1, G-J4-1), measured_fit not run 17, assembly_operation not run 22; 50 gates scanned: 48
  open (no record, incl. G-W13), 2 withdrawn (G-SNAP-1, G-SKIRT-1). Nothing printed, sliced, bought, measured or powered.
- Decision asked by the checks role: the panel locating ribs (`panel_locate_rib_f/_r`, 1.2) stay classed as locating
  walls in the baseline (the 4 panel screws carry the closure load; no baseline geometry change allowed). If the
  fork's fr-panel turns the lower interface into integral shear/locating keys that carry load, those keys must be
  probed as load-carrying (1.6 mm) in CRITICAL_JOINTS.
**Open:** r2 out/ copy and its SHA256SUMS in out/_r2-2026-10-05/; out/_fujinon-r3 kept. final-docs: HANDOFF/RECTIFICATION
were only patched for the r3 interface requests (rewrite still theirs). User decisions unchanged (lens, black band,
OPTIONS a/b, EVF-feed option C). Every hardware gate stays open.

## r3 fix-baseline

(fix-baseline role, 2026-10-05, started 12:13, finish-by 15:45; progress record, a re-spawned copy continues from here.
Findings: code verifier V-H1, V-M1..M4, V-L1..L4; docs verifier VBD-1..16. Per-finding table at the end when done.)
- 12:13 started; read R3-BRIEF and r3 integrate-baseline. Next: code fixes in build_d2.py / checks.py / layout.py R3 block.
- 12:25 code edits done (pre-edit copies + sha256 in out/_fix-baseline/pre/): checks.py check_joint_coverage (V-L1 gated
  joint -> info, V-L2 non-pass status fails, V-M3 REQUIRED_JOINT_IDS rule); layout.py R3 block REQUIRED_JOINT_IDS (12);
  build_d2.py (V-H1 unknown-state records rejected on their item + unassigned_records; V-M1 'rejected' outcome,
  unmatched keeps state open; V-M2 required_artifacts_of + gate_doc + _canon_key; V-M4 empty category fails; V-L3
  step/parts + test_common.json hashed, carried_files); test_r3_regressions.py 27/27 (+9 cases); SPEC s6 item 10 and
  evidence/README.md updated. Next: docs findings VBD-*, then release rebuild.
- 12:25 docs edits so far: WIRING G-W11 row (option C regulator thermocouple, <= 90 C, 4.35-4.80 V), placement
  hash note, ko_5v_up "fits" -> box arithmetic (WIRING, make_bom D2-16P); make_bom D2-75 electronic load, D2-76 G-W13
  stand-ins; ASSEMBLY s1 gates/bench list, step 10 check (G-W8..12), P3/P4 swapped, panel service-life line, P1-P4
  summaries (ASSEMBLY s1/s6, FASTENER-POLICY, DESIGN, SPEC, layout/checks scope note); make_tables lint extended
  (nouns, paragraphs, MP, PT groups; selftest + 13 planted cases); PRINT-GUIDE :3 and s6.1 counts. Next: Kowa --fast
  trial -> Fujinon 1 mm -> release build.
- 12:40 Kowa --fast --sweep-step 1.0 trial (out/_trial-r3-fixbase): 21/21 pass, critical_features 118 = 108 pass + 10 info (J6 info), 11/11 STLs byte-identical to r2. Next: Fujinon 1 mm into out/_fujinon-r3fb.
- 12:51 Fujinon --fast --sweep-step 1.0 (out/_fujinon-r3fb, built 12:51:07): 21/21 pass, 551 rows, 11/11 STLs = out/_fujinon-r2; checks.json copied to out/checks-fujinon-sweep1mm.json (sha 8df943c5...). Next: Kowa release build --sweep-step 1.0 into out/.
- 13:02 Kowa release `build_d2.py --sweep-step 1.0` into out/ (built_at 2026-10-05 13:02:27 +0800, 353.6 s): 21/21
  pass, 551 rows = 541 pass + 10 info + 0 fail (critical_features 118 = 91 feature + 11 joint + 6 coverage pass; info:
  3 G-CAP-1 flexures, J6_cap_grip, 6 named exceptions), cad_release_candidate true, stubs none. checks.json sha256
  a27c5981...; 11/11 production and 24/24 coupon STLs + both coupon manifests byte-identical to out/_r2-2026-10-05.
  Receipt: 76 hashed files (64 + 11 step/parts + test_common.json, carried_files lists test_common inputs), all match
  disk; 16 sources + 4 gate docs match; 4 states not run (11/9/17/22), 50 gates (48 open, 2 withdrawn), 0 records.
- 13:03 make_tables.py (DESIGN generated blocks), make_bom.py (61 purchased lines, +D2-75/D2-76 tools; totals SGD
  775.74 + 340.61 unchanged), make_tables --check: stale none, lint 0, selftest ok (with the extended lint).
  Hand edits after: DESIGN s1 (current receipt), HANDOFF s1-s6, RECTIFICATION (r2 build state labelled history).

**Done (13:05).** Per-finding table:

| id | verdict | change | evidence |
|---|---|---|---|
| V-H1 | fixed | build_d2: a record with an unknown state is rejected on its item (outcome `rejected`); `unassigned_records()` lists unreadable / non-object / unknown-state+unknown-item records in `evidence.rejected_records`, `evidence.unassigned_records` and `open_evidence` | tests test_unknown_state_fail_record_stays_open, test_unreadable_record_is_listed_and_open |
| V-M1 | fixed | new outcome `rejected` (any rejected record keeps the item open unless fail/conflict); `unmatched_records` keep the state open; open_evidence names `rejected:` ids and `unmatched: N` | test_rejected_fail_beside_pass_stays_open, test_item_typo_keeps_state_open; 2 older tests now assert `rejected` instead of `not run` |
| V-M2 | fixed | `required_artifacts_of()` + `gate_doc()`: measured_fit names the gate doc; assembly_operation names the doc + every `stl/<part>.stl`; `_canon_key` accepts doc paths relative to cad/gs8-d2-v1; evidence/README + SPEC s6 item 10 | test_measured_and_assembly_records_name_doc_and_stls |
| V-M3 | fixed | layout R3 block `REQUIRED_JOINT_IDS` (12); check_joint_coverage FAILs a missing id unless a fork joint lists it in `replaces`, and FAILs a layout without the registry | test_deleted_joint_with_its_probes_fails, test_baseline_joint_ids_fixed; interface request to integrate-fork |
| V-M4 | fixed | summarize: empty category = fail ('no rows'); the stated service_driver override pops the error | test_empty_category_fails; release: all 20 row categories n > 0 |
| V-L1 | fixed | a joint with complete coverage and gated exceptions reports `info` + `exception` text naming G-CAP-1 | release J6_cap_grip info; critical_features 108 pass / 10 info |
| V-L2 | fixed | check_joint_coverage: any required feature status other than pass/info(gated) is a problem | test_joint_rejects_unknown_feature_status |
| V-L3 | fixed | receipt hashes step/parts/*.step written by the build and test_common.json (+ carried_files with its input hashes) | receipt files 76, all match |
| V-L4 | fixed (by correction) | integrator's 11:55 build: 551 rows = 542 pass + 9 info + 0 fail; current 13:02 build: 551 = 541 + 10 info | receipt summary |
| VBD-1 | fixed | HANDOFF step 7 (s2 steps 1-9, no pack) and step 8 (each cycle starts with P1-P4, pack last) | HANDOFF s5 |
| VBD-2 | fixed | HANDOFF steps 2/4/5/9 + closing sentence use the structured record model; G-KNOB-1/G-COMB-1/G-J4-1 in s3 list and step 5 | HANDOFF |
| VBD-3 | fixed | PRINT-GUIDE:3 "11 printed production parts (count: DESIGN s1.1)" | lint now flags "12 printed parts" |
| VBD-4 | fixed | make_tables lint: nouns parts/pieces/coupons/harnesses/cables/tools/steps/standoffs, paragraph joining, MP, PT groups only when named, delta phrases skipped, `G-KEEP-1` not a count; selftest + 13 planted cases | --check lint 0, selftest ok |
| VBD-5 | fixed | DESIGN s1 table from the 13:02 receipt; option C in decisions; calibration ids in Next gate; HANDOFF s5 ref | DESIGN s1 |
| VBD-6 | fixed | HANDOFF s1-s3 to the current receipt; RECTIFICATION build state labelled r2 history, per-joint rule, G-W13, option C | HANDOFF, RECTIFICATION |
| VBD-7 | fixed | ASSEMBLY P3 = pull the pack (junction follows), P4 = unplug the XT30; same order in ASSEMBLY s1/s6, FASTENER-POLICY, DESIGN, SPEC, layout/checks scope note | ASSEMBLY s7 |
| VBD-8 | fixed | panel line: no flexing latch; openings limited by the PT tally (provisional until G-PT-1), G-PANEL-1 not run | ASSEMBLY s7 item 4 |
| VBD-9 | fixed | DESIGN print set 292.9 g / 368.5 g / 15.7 h; "needs no support by the computed overhang check (slicer review not run)" | print-manifest totals |
| VBD-10 | fixed | WIRING G-W11 row: option C regulator thermocouple at ko_5v_up, case <= 90 C, EVF 4.35-4.80 V | WIRING s9 |
| VBD-11 | fixed | make_bom D2-75 electronic load, D2-76 G-W13 stand-ins (unpriced); ASSEMBLY s1.1 bench list | BOM.md |
| VBD-12 | fixed | HANDOFF s4 item 6 (EVF feed A/C), step 1 decides it, step 3.7 conditional | HANDOFF |
| VBD-13 | fixed | ASSEMBLY step 10: G-W8..G-W12 in the body; s1 Gates before assembly: G-W1..G-W7 + G-W13; HANDOFF G-W5 moved to bench step 2.3 | ASSEMBLY, HANDOFF |
| VBD-14 | fixed | HANDOFF FPC "length to confirm at G-FPC-1"; WIRING / BOM D2-16P "estimated envelope inside ko_5v_up by box arithmetic" | |
| VBD-15 | fixed | WIRING placement: run against old layout hash; layout changed only by the r3 registry block; ko_5v_up + COTS unchanged; r3 rows pass | |
| VBD-16 | fixed | PRINT-GUIDE s6.1 "Three coupon groups (...) had no record id" | lint 0 |
Open: none of the findings; fork must merge REQUIRED_JOINT_IDS with the new checks.py (interface request). test_common.py
not re-run (inputs unchanged, hash-linked as carried). Nothing printed, sliced, bought, measured or powered.

## r3 led-removal

(led-removal role, 2026-10-05, started 15:52, finish-by 16:50, hard stop 17:15. Task: user decision "remove the LED
indicators. I/O will be via the dials, on/off, record button and the EVF." No geometry change; all STLs must stay
byte-identical.)
- 15:55 started; read R3-BRIEF (NOTE 4) and r3 fix-baseline. Next: find every LED / light-pipe reference.
- 15:58 done: layout.py (J10 comment, PARTS['plunger'] material 'ASA' colour 'black'), printed_small.py (docstring,
  PRINT notes), PRINT-GUIDE (s1 material row, plunger row, plate line), SPEC parts row, WIRING (block label, s8
  dtparam LED lines + "No LED indicators" paragraph, "Status on the EVF" software requirement, G-W3/G-W4/G-W8 pass
  criteria additions), make_bom D2-42 deleted (D2-41 black spool now lists the plunger): 61 -> 60 purchased lines,
  camera estimates SGD 340.61 -> 305.73 (-34.88), prices.json part 775.74 unchanged; bom.csv 73 -> 72 lines, BOM.md
  176 -> 175 lines. Pre-copies in out/_ledrm-pre/. Next: ASSEMBLY procedures, DESIGN/SPEC/OPTIONS I/O statement.
- 15:58 ASSEMBLY step 10 / battery Remove / s7 P1 rewritten (EVF boot screen; shutdown screen then dark, wait 5 s; EVF dark expected from POWER_OFF_ON_HALT=1, bench-confirmed only at G-W4/G-W8; P3-P4 remain the isolation). I/O statement in DESIGN s1 controls, SPEC controls, OPTIONS header. layout self-check 129/0, test_r3_regressions 27/27, make_tables refresh done. _r3-1302/ receipts saved (a27c5981 / 8df943c5 / receipt 199fe140). Next: Fujinon 1 mm into out/_fujinon-r3led (started 15:59).

## r3 interface requests (addendum, fix-candidate 16:03) -- for the baseline checks / layout owner
- **Tub `rib_l` gusset tip is an unclassified thin spot (baseline geometry, also in r2).** The fork's hood=screw1 builds
  report `results.unclassified_thin_spots` = tub t 0.98 at (-12.95, 31.85, 20.75), nearest entry tub_pi_boss_1 (info).
  It is the 45 deg tip of `RIBS['rib_l']` (0.3 land at x -13, y 31.9..32.2, z ~2.5..41). A dense scan of the built STLs
  (`candidate-fr1/_thin_spot_rib_l.py` -> `candidate-fr1/out/_thin-spot-rib_l.txt`) gives min 0.60 there, identical in
  `out/stl/tub.stl` (r2) and every FR state; the seeded 1500-sample thin_wall screen just misses it on the r2 mesh.
  Owner decision needed (no exception added by the fork): a structural CRITICAL_FEATURES probe for rib_l, or blunt the
  tip (e.g. a >= 1.2 land), or a named NONSTRUCTURAL_EXCEPTIONS entry if the tip is truly non-structural.
- 16:06 Fujinon --fast 1 mm (out/_fujinon-r3led, 440.6 s): 21/21 pass, cad_release_candidate true, 11/11 STLs = out/_fujinon-r3fb; checks.json copied to out/checks-fujinon-sweep1mm.json (sha 8df943c5..., identical to the 12:51 file: checks carry no material). Next: Kowa release build into out/ (started 16:06).
- 16:16 Kowa release `build_d2.py --sweep-step 1.0` into out/ (built_at 2026-10-05 16:15:58 +0800, 492.3 s; the
  foreground call passed the 600 s Bash limit because of lock waiting and finished in the background, exit 0):
  21/21 categories pass, 551 rows = 541 pass + 10 info + 0 fail, cad_release_candidate true, stubs none, blocking
  none. checks.json sha256 a27c5981... (identical to 13:02: checks carry no material). 11/11 production and 24/24
  coupon STLs + coupons-manifest.json + coupons-r1-manifest.json byte-identical to out/_r2-2026-10-05/. Receipt:
  76 files all match disk (changed vs 13:02: the STEP files, renders, print/parts manifests: plunger colour and
  material), 16 sources match (changed: layout.py, SPEC.md, printed_small.py), 4 gate docs match (changed: SPEC.md,
  WIRING.md); states slicer_review / coupon_validation / measured_fit / assembly_operation not run (11/9/17/22);
  gates unchanged (50, 48 open, 2 withdrawn). Fujinon receipt (out/_fujinon-r3led, 16:05:12) also matches every
  current source, gate doc and output. make_tables refresh (DESIGN) + --check: stale none, lint 0, selftest ok.
  DESIGN s1 hand rows updated to the 16:15:58 / 16:05:12 builds.

**Done (16:18).**
- Files changed: cad/gs8-d2-v1/layout.py (J10 comment; PARTS['plunger'] material 'ASA', colour 'black'),
  printed_small.py (docstring, PRINT notes: black ASA from the hood spool, 100 %, no top pattern on the finger face,
  paint-fill the power symbol; orientation and supports unchanged), PRINT-GUIDE.md (s1 material row, plunger notes
  row, small-parts plate line; s2 table regenerated), SPEC.md (parts row; controls I/O line), DESIGN.md (controls
  I/O line; generated parts table; s1 build rows), OPTIONS.md (controls decision paragraph), ASSEMBLY.md (step 10
  check, battery Remove, s7 P1; generated step 5 parts row), electronics/gs8-d2-v1/WIRING.md (block label
  'printed plunger'; s8 config.txt LED lines and "No LED indicators" paragraph; "Status on the EVF" software
  requirement; G-W3, G-W4, G-W8 pass criteria extended, nothing closed), make_bom.py (D2-42 deleted; D2-41 lists the
  plunger), BOM.md, bom.csv (regenerated).
- config.txt lines (WIRING s8; polarity [to confirm on the bench] at G-W3; 1 web search found the parameter names in
  community guides, not in the official documentation page):
  `dtparam=pwr_led_trigger=none`, `dtparam=pwr_led_activelow=off`, `dtparam=act_led_trigger=none`,
  `dtparam=act_led_activelow=off`.
- BOM: 61 -> 60 purchased lines; camera build SGD 775.74 (prices.json) unchanged, estimates 340.61 -> 305.73
  (-34.88, the D2-42 USD 25 planning line); bom.csv 73 -> 72 lines, BOM.md 176 -> 175 lines.
- Procedures: power-on = EVF boot screen; shutdown = hold the plunger 2 s, EVF shutdown screen until halt, EVF dark,
  wait 5 s more; EVF dark expected from POWER_OFF_ON_HALT=1 (Pi USB 2 feeds the EVF) and only bench-confirmed by
  G-W4 (USB 2 < 0.5 V within 5 s of halt) and G-W8; P3-P4 pack disconnection stays the only isolation.
- Not studied (NOTE 4 follow-up option for the user): the plunger as a flexing tab printed into the hood plate.
- Half-done: none. Next (not this role): final-docs records the decision in RECTIFICATION / HANDOFF / RESPONSE; the
  FR1 candidate inherits it on adoption. Nothing printed, sliced, bought, measured or powered on this machine.

## r3 led-removal (verify)

(adversarial verifier, 2026-10-05 16:18-16:25; read-only except the one ASSEMBLY edit below.) Note for readers: the
led-removal role's entries from 16:06 on (builds, "Done (16:18)") sit below the "r3 interface requests" addendum
heading above, not directly under "## r3 led-removal".
- Holds: no LED-indicator or light-pipe dependency left in cad/gs8-d2-v1 (*.md, *.py; candidate-fr1/, airflow/ and
  out/ excluded) or electronics/gs8-d2-v1 (the `led` in printed_tub.py is the hook ledge solid; PI_LED is the proxy
  feature); every r2 LED/light-pipe site (ASSEMBLY step 10 + battery Remove, DESIGN parts row, layout J10 + PARTS,
  PRINT-GUIDE s1/s2/notes, printed_small, SPEC row, bom D2-42 + P-06, BOM.md, WIRING block label) is changed.
  layout.py / printed_small.py vs candidate-fr1/_base/: only the J10 comment, PARTS['plunger'] material/colour and the
  docstring/PRINT notes differ for the plunger (the other layout.py additions are the r3 checks blocks).
- Own sha256: 11/11 production + 24/24 coupon STLs and both coupon manifests = out/_r2-2026-10-05/; Fujinon
  out/_fujinon-r3led STLs = _fujinon-r3fb = _fujinon-r2. Both receipts: every source and output hash matches disk
  (Kowa 76 files, 16 sources; 4 gate docs match); 50 gates, 48 open, 2 withdrawn; states not run 11/9/17/22.
- BOM regenerated in the scratchpad from make_bom.py: bom.csv and BOM.md byte-identical to the committed copies;
  60 purchased lines (A20 B8 C5 E10 F17); SGD 775.74 + 305.73. make_tables --check: stale none, lint 0. layout
  self-check 129/0; test_r3_regressions 27/27 (re-run 16:21).
- Fixed (medium, doc only): ASSEMBLY s7 P1 told the user to "hold the plunger 2 s again" if the EVF stays lit; after
  halt that press boots the Pi (G-W8). P1 now separates "no shutdown screen" (press again) from "shutdown screen
  shown, EVF still lit" (do not press; wait 5 s, go on, record as a G-W4/G-W8 finding). make_tables --check clean.
- Left (low, WIRING.md is a receipt gate doc, so not edited here): the halted/standby state of the Pi 5 LED is not
  covered by the dtparam lines (firmware may light it at halt); the trigger value, not only the polarity, is
  unconfirmed; G-W3 says "the onboard LED" while s8 says "both". Suggested for the next WIRING edit + rebuild.

## r3 led-removal (main session, 16:23)
Applied the LED verifier's three low WIRING findings (V-LED-2..4) before the rib-tip release rebuild so the receipt
hashes the corrected gate doc: the whole s8 LED block is marked [to confirm on the bench, G-W3] with the fallback; G-W3
names both LEDs; G-W8 records light at the plunger/vents also in the halted standby state.

## r3 rib-tip

(role rib-tip, 2026-10-05 from 16:22; user decision NOTE 5 "blunt the rib_l gusset tip to a 1.2 land")
- 16:24 geometry: layout.py `RIBS['rib_l']` x0 -13.0 -> `X_FW_IN - (SPLIT - MIN_WALL - 24.1)` = -12.1 (printed_tub.py
  unchanged: its prism already ends in a land at x0, height SPLIT - (y0 + (X_FW_IN - x0)) = 1.2). Material is only
  removed (the 0.9 x 0.9 triangle tip + 0.3 land strip, z 2.45..41), so no new clearance can arise; print pose (+Y up)
  unchanged: 45 deg face, vertical land, flat top at SPLIT. Probe `tub_rib_l_tip` (cls land, min 1.2, origin x -12.05,
  y 31.6, z 24, dir +Y, span 5 x 6 mm along Z) added to the r3 CRITICAL_FEATURES block and to J7_camera.required.
  Next: trial build out/_trial-r3-rib.

## r3 final-docs

(final-docs role, 2026-10-05 from 16:29, finish-by 17:10; progress record, a re-spawned copy continues from here)
- 16:33 read R3-BRIEF, REVIEW s1-4, NOTES r3 sections (rib-tip still running at 16:30: trial build next), CANDIDATE.md,
  both receipts (baseline out/ 16:15:58: 21/21, 551 rows = 541 pass + 10 info; candidate out/ 15:26:25: 21/21, 544 rows
  = 534 pass + 10 info, critical_features 136 = 126 + 10). Airflow: no AIRFLOW.md; no airflow file changed since the
  14:20 pause. Plan: (1) RECTIFICATION r3 section (append), (2) audit RESPONSE.md (new), (3) HANDOFF rewrite s1-s5.
- 16:37 RECTIFICATION.md r3 section appended (R3-1..R3-5, user decisions, FR1 pointer, still open; placeholder
  RIB-TIP-STATE to fill), audit/d2-readiness-2026-10-05/RESPONSE.md written (placeholder RIB-TIP-RESPONSE), HANDOFF.md
  rewritten (s1-s9; placeholders RIB-TIP-HANDOFF and AIRFLOW-TIME). make_tables --check: stale none, lint 0. Pre-edit
  HANDOFF copy in %TEMP%. Next: wait for rib-tip result (NOTES "r3 rib-tip"), then fill placeholders and, if the
  release was rebuilt, update HANDOFF s1/s4, RECTIFICATION build state and RESPONSE numbers from out/build-receipt.json.
- 16:34 trial `build_d2.py --fast --sweep-step 1.0 --out out/_trial-r3-rib` (343 s, exit 0): 21/21 categories pass,
  stubs none, cad_release_candidate true, unclassified thin spots none. Probe tub_rib_l_tip: B-rep chord 1.25 at all 5
  rays (entry y 30.95, exit 32.2 at x -12.05). 10/11 production STLs byte-identical to out/stl and out/_r2-2026-10-05;
  tub.stl differs (683c74ec -> 0d4bbca8). (The --part tub iteration run was skipped for time; the full trial covers it.)
- Dense scan (`cad/gs8-d2-v1/_thin_spot_rib_l.py`, adapted; output out/_trial-r3-rib/_thin-spot-rib_l.txt), 10 points
  along the tip z 5..38: old min 0.598 (x -13, y 32.2, z 22.32), share < 1.15 up to 11 %; new min 2.384 at the tip
  (x -12.1, y 32.2; cone method), share < 1.15 = 0 at every point: no thin spot left, none new.
- Volume: old 105968.475, new 105946.656 mm3, delta -21.819. Boolean (manifold3d): old - new 22.547 mm3, one piece,
  bbox x -13.0..-12.1, y 31.01..32.2, z 6.69..41.0 (the tip; below z 6.7 the lip gusset is unchanged); new - old 0.728
  mm3 = float32 slivers on re-triangulated coplanar faces (62 triangles each side re-meshed; per-plane area deltas:
  front wall x -5.2 -0.002, floor z 2.5 -0.003 mm2; only the tip planes change: land x -12.1 +40.46, old land x -13
  -9.98, 45 deg face -43.1, top y 32.2 -29.79, rib top z 41 -0.65, lip-gusset face +0.93 where the tip used to sit).
- Coupons: `make_coupons.py --out out/_trial-r3-rib/coupons`: 20/20 coupon STLs byte-identical to out/stl/coupons and
  out/_r2-2026-10-05/stl/coupons (the 4 coupon-pi-keeper-* files come from coupons_r1.py, which make_coupons does not
  build). Step 3 passed; promoting. Pre-promotion receipts copied to out/_r3-1615/.
- 16:38 coupons_r1.py --out trial: coupon-pi-keeper-tub CHANGES (a1ab2c68 -> e0325d05: its tub cut x -106..-5.3,
  z 0..~10 contains the rib tip z 6.7..10); the other 3 keeper coupons identical. Regenerated coupons_r1.py into out/
  (old coupon + coupons-r1-manifest.json kept in out/_r3-1615/).
- 16:39-16:46 Fujinon `--fast --lens fujinon_hf6xa --sweep-step 1.0 --out out/_fujinon-r3rib` (412 s): 21/21 pass,
  cad_release_candidate true; tub.stl 0d4bbca8 (= trial); checks.json copied to out/checks-fujinon-sweep1mm.json
  (sha 7eeb5c20...). Current sources, so the Fujinon receipt is not stale.
- 16:46-16:54 Kowa release `build_d2.py --sweep-step 1.0` into out/ (built_at 2026-10-05 16:53:58 +0800, 468 s, exit 0):
  21/21 categories pass, stubs none, cad_release_candidate true; receipt: 94 hashed files all match disk (receipt sha
  4cf458f9..., checks.json 0e0de579...). vs out/_r2-2026-10-05: 10/11 production STLs and 23/24 coupon STLs
  byte-identical; tub.stl (0d4bbca8) and coupon-pi-keeper-tub.stl (e0325d05) changed, both only at the rib_l tip.
  Physical states stay not run. Nothing printed, sliced, bought, measured or powered on this machine.
- 16:55 docs: make_tables refresh (PRINT-GUIDE, DESIGN) + --check: stale none, lint 0. DESIGN s1 state row -> the
  16:53:58 receipt (checks 0e0de579...; "10 of 11 production STLs byte-identical to r2; tub changed at the rib_l tip by
  the r3 user decision", + coupon-pi-keeper-tub); Second-run row -> out/_fujinon-r3rib 16:45:57, checks 7eeb5c20...
  test_r3_regressions 27/27; layout self-check 129/0. Both receipts: every hashed file matches disk.
- NOT DONE (needs a rebuild): the SPEC.md s9 rib_l row. SPEC.md is hashed in the build receipt, so editing it after
  the 16:53:58 release made the receipt stale; the edit was reverted (receipt matches again). Row text to apply before
  the next release rebuild (main session / final-docs): `| rib_l | z 2.7..45 | z 2.5..41; 45 deg gusset to the panel
  plane ending in a 1.2 land at x -12.1, y 31.0..32.2 (r3 USER 2026-10-05: tip land 0.3 -> 1.2, was a 0.60 knife edge
  at x -13; probe tub_rib_l_tip in J7) | the camera's dia 36 ring passes over it at step 7; the tip was below MIN_WALL |`
- Files changed by rib-tip: layout.py (RIBS rib_l x0; probe tub_rib_l_tip in the r3 CRITICAL_FEATURES block;
  J7_camera.required), new _thin_spot_rib_l.py, DESIGN.md (s1 rows + generated blocks), PRINT-GUIDE.md (generated
  blocks), out/ (release, out/stl/coupons/coupon-pi-keeper-tub.stl + coupons-r1-manifest.json, checks-fujinon-
  sweep1mm.json), out/_r3-1615/, out/_trial-r3-rib/, out/_fujinon-r3rib/. printed_tub.py unchanged. The FR1 candidate
  still carries the r2 rib tip (x0 -13) and must take this layout change on adoption. Done (16:56).
- 16:58 final-docs DONE. Placeholders filled from the rib-tip result: all three files now cite the 16:53:58 release
  (21/21, 552 rows = 542 pass + 10 info + 0 fail, critical_features 119 = 109 + 10, checks 0e0de579...; Fujinon
  out/_fujinon-r3rib 16:45:57 21/21); own sha256 check: vs out/_r2-2026-10-05 only tub.stl and
  coupon-pi-keeper-tub.stl differ (rib_l tip, explained by rib-tip). Airflow: still no AIRFLOW.md at 17:00 and no
  airflow file newer than the 14:20 pause; HANDOFF s8 says report pending, basic simulation not measurement, G-W11/G-W12
  open. make_tables --check: stale none, lint 0, selftest ok. HANDOFF/RECTIFICATION are not hashed in the receipt.
  Open for the main session: SPEC.md s9 rib_l row (text in "r3 rib-tip") needs a release rebuild; if AIRFLOW.md
  appears later, update HANDOFF s8 (pointer only). Nothing printed, sliced, bought, measured or powered; no commit.

## r3 rib-tip (verify)

(adversarial verifier, 2026-10-05 16:56-17:07; read-only, no CAD runs; only this NOTES entry written.)
- (1) Sources: printed_tub.py = candidate-fr1/_base copy and = the 16:15 receipt hash (76bd9769). layout.py: removing the
  three rib-tip edits (RIBS rib_l x0, probe tub_rib_l_tip, J7_camera.required entry) from the current file reproduces
  the 16:15 receipt hash 154e0b9760f8 exactly, so nothing else changed in layout.py. x0 = -5.2 - (32.2 - 1.2 - 24.1)
  = -12.1; land y 31.0..32.2 = 1.2.
- (2) tub.stl vs out/_r2-2026-10-05: watertight both, vol 105968.475 -> 105946.656 (-21.819). Only 6 vertices
  differ on each side (STL frame X = x+154, Z = y+35): old land x -13 (y 31.9/32.2) -> new land x -12.1 (y 31.0/32.2),
  z 2.5..~36.8, plus one float-jitter vertex on the 45 deg face at the z 41 rib top (146.083 -> 146.08). So the change
  is confined to the rib_l tip. Own Moller-Trumbore rays on the new STL at x -12.05 along y: 1.25 at z 8, 12, 24 (no
  hit at z 36/40: the dia 36 ring cut, unchanged since r2). In-plane chord minimum near the corner 0.85-0.89, which
  is the corner effect of rays crossing the land/face corner (inscribed circle at the tip = 1.70 dia). No new thin
  spot. (Boolean diff not repeated: no manifold/networkx engine in .venv-cad trimesh; rib-tip's manifold3d result
  is consistent with the vertex diff.)
- (3) checks.json (out/, sha 0e0de579 = receipt): tub_rib_l_tip kind feature, structural, cls land, min 1.2, B-rep
  chord 1.25 on 5 rays (z 12..36), entry y 30.95, exit 32.2, pass; J7_camera lists it and passes.
- (4) Receipt 16:53:58: 21/21 categories pass, cad_release_candidate true; all hashed outputs/sources and the 4 gate
  docs (incl. SPEC.md 1674374c) match disk. vs r2: only tub.stl (683c74ec -> 0d4bbca8) and
  coupon-pi-keeper-tub.stl (a1ab2c68 -> e0325d05) differ; 10/11 production and 23/24 coupon STLs identical. The
  keeper-tub coupon change is not "coupon must stay identical" drift: it is a cut of the tub containing the tip.
- (5) No stale "11 of 11" in DESIGN/SPEC/PRINT-GUIDE; DESIGN s1 rows cite 16:53:58 / 16:45:57 and "10 of 11";
  make_tables --check: stale none, lint 0. OPEN (not fixed here, SPEC.md is a receipt gate doc): SPEC s9 line 334
  still the r2 rib_l row; apply the row text from "r3 rib-tip" and rebuild the release.

## r4 maturity pass (2026-10-05 evening, main session 2dc5a3f3; user: "take the next steps to improve the maturity of D2")
- Baseline r3 zipped first: baseline-r3-2026-10-05.zip (164 files: sources, docs, evidence, out/*.json, STL, STEP,
  renders, candidate-fr1 sources/docs, electronics/gs8-d2-v1).
- Audit `audit/d2-readiness-2026-10-05-r3/REVIEW.md` (17:23, unanswered until now) addressed:
  - logic 1 (whole-part evidence): build_d2 WHOLE_PART_TESTS splits G-SNAP-2 / G-KEEP-1 / G-PANEL-1 into the coupon item
    and an assembly_operation item '<gate>/whole' (doc + every production STL); apply_gate_outcomes passes the gate only
    when both pass; gate_doc strips '/whole'. SPEC s10 text says so.
  - logic 2 (malformed field types): build_d2 _key() + validate_record type checks; no TypeError, record rejected or
    unmatched and kept visible.
  - logic 3 (phantom replacement): checks.check_joint_coverage counts a replacement only from a validated
    CRITICAL_JOINTS entry; FR_JOINTS-only declarations waive nothing. test_deleted_joint_with_its_probes_fails updated
    (its FR joint is now merged into CRITICAL_JOINTS, as the real fork does).
  - tests: test_r3_regressions.py 27 -> 31 (malformed types, phantom replacement, whole-part split/stale, cable routes);
    the auditor's check_r3_logic.py re-run in scratch (not in the audit folder): no exception, phantom J4 fails.
  - FR1: HANDOFF hood removal direction (+Y, toward the open left side), coupons_fr_keeper.py GATE tip gap 0.25 -> 0.15
    (pocket y0 -29.9 vs tongue y0 -29.75), fr1_counts.py full-toolset note (12 -> 11 tools; column relabelled a subset).
  - WIRING G-W13(e): defined off rail (real VBUS + 100 ohm stand-in load), VOUT bias within the device ratings, log
    through shutdown; row C and the recommendation no longer say "met by design".
  - airflow: STATUS banner on out/variants/VARIANTS-tables.md + airflow/NOTES.md "r4 label"; nothing re-run.
- Wiring maturity: new check `cable_routes` (checks.py: continuity with a >= 1.0 x 1.0 passage, ends within 1.0 of both
  end parts, estimated route + max(10 mm, 10 %) <= length; bend radius NOT checked). It found the 4 gaps of the
  comparison (0.1 fpc, 0.2 + 2.0 hdmi, 10.0 qt/fps, 1.0 fps, 0.2 pigtail) and one more: run lead ko_run_rise ->
  ko_run_cross met only along an edge (4 x 0.4 window). 6 link keep-outs added (ko_fpc_link, ko_hdmi_link,
  ko_panel_link, ko_lead_link, ko_pig_link, ko_run_link); KEEPOUTS 27 -> 33; the gaps held no printed solid
  (part-STEP intersection before the change). Tightest cable: qt, 17.4 mm over route + allowance.
- Print maturity: layout.print_modifiers + build_d2.export_modifiers -> out/stl/modifiers/<part>__mod_<id>.stl (tub 7,
  panel 4, base_grip 4), FASTENER-POLICY rule (40 %, 4 perimeters, 8 mm round each pilot); check `print_modifiers`
  (overlap with the part); hash-linked in the receipt; slicer_review records must name them. The panel bosses had no
  modifier before (policy gap). PRINT-GUIDE s1.1 added, DRAFT header removed, "six pilots" -> seven.
- SPEC s9 rib_l row applied (text from "r3 rib-tip").
- Trial build out/_trial-r4 (--fast, 2 mm): 23 of 23 categories (keepouts 97, cable_routes 8 + 2 info, print_modifiers
  15); 11 of 11 production STLs byte-identical to the r3 release; gates 53 (3 '/whole' items).
- r4 research (subagent, desk only, 2026-10-05; full report kept in the session scratchpad, facts copied here):
  - Fuse: Littelfuse 0251015.MXL (PICO II 251, 15 A, 32 V, very fast): body 3.18 max x 7.11, cold 4.46 mohm, melting
    I2t 68.8 A2s, 300 A at 32 VDC, 25 % standard derating + temperature curve (98.5 % at 40 C) -> 11.1 A allowed at 40 C,
    8.6 A = 78 %; 12 A part rejected (1-3 % margin); DigiKey F2352-ND, 8,035 in stock, USD 1.45. Datasheet 251 rev VL
    09/26/24 (Littelfuse site refuses fetch; read from a verbatim copy). Second source OptiFuse FXG-15A (no resistance).
    Inrush estimate <= 0.35 A2s (X1203 input C unpublished, 100-1000 uF bracket); fault 120-200 A [est]. Fit: marginal in
    ko_pig_drop (7 x 7 x 15), comfortable in ko_xt30 under the XT30 pair -> placed there (layout.PIGTAIL_FUSE, drawn in
    the xt30_pair proxy so the pack_in sweep sees it). G-W5 drop 0.095 + 0.040 = 0.135 V vs 0.15 V; sleeve <= 70 C.
  - LDO: TI TLV75801P (adjustable, 500 mA), R1 11.5 k / R2 1.58 k 0.1 % -> 4.553 V; band 4.459-4.638 V from datasheet
    limits (TJ -40..125 C); dropout 130 mV max at 500 mA; limit >= 530 mA; VIN 6.0 V; SOT-23-5 176.9 C/W (TI board),
    WSON-6 80.3 C/W; no reverse blocking; DigiKey TLV75801PDBVJ 5,567 at USD 0.33, DRVR 54,465. Datasheet SBVS351D.
    Fixed alternative Torex XC6220B45BPR-G (4.55 V, SOT-89-5, 76.9 C/W): band 4.413-4.688 V with a typical-only tempco,
    0 stock, 112-week lead on sister codes, needs 10 uF + 10 uF. XC6210B45 rejected (no 0.3 A dropout max; MOQ 6,000).
    No pre-assembled 4.5 V board found. Clones of XC6220 exist: authorised distributors only.
- Fuse integration: layout.PIGTAIL_FUSE; cots.xt30_pair draws the dia 5 x 20 sleeve at z -23.5 under the pair (box z0
  -20 -> -26.5); WIRING W-10, power-path row, s4.7 drop + R-PACK-BMS, G-W1 (10 plug-ins), G-W5 (sleeve <= 70 C, drop
  with fuse); make_tables pigtail CABLE_INFO + PLUG_ORDER step-1 row; make_bom D2-14F, SOLDER_JOINTS +2 (12).
- Option C made concrete but NOT adopted: WIRING s4.8 candidate table; BOM D2-16R (TLV75801P), D2-16D (divider), D2-16C
  (values), D2-16P (copper carrier) at qty 0; REG_C_JOINTS_DELTA 11 -> 15; ASSEMBLY / OPTIONS / MEASURED-PARTS counts.
- The first Fujinon run (_fujinon-r4, started before the fuse edits) was stopped and discarded; rerun after all edits.
- make_tables run BEFORE the release build (WIRING.md is a receipt gate doc; its generated blocks changed with the
  cable vias and the fuse rows).
- Research report copied to electronics/gs8-d2-v1/RESEARCH-r4-fuse-ldo.md (sources with URLs).
- User decision 2026-10-05 evening: "I'd like to keep it as a switch" -> OPTIONS (a) (18/24 into the encoder menu) is
  DECLINED; switch_1824 + knob_fps + D2-11 stay. Recorded in OPTIONS.md, ASSEMBLY s1.1, DESIGN s1, HANDOFF s0/s6. No
  geometry or hashed source changed (no rebuild needed). OPTIONS (b) (150 mm FPC) stays open.
- 2026-10-05 ~23:00, Carousell SG second-hand snapshot (user request):
  - Report: electronics/gs8-d2-v1/SECONDHAND-CAROUSELL-2026-10-05.md.
  - 52 browser searches; workflow wf_46f37be6-af5 (7 assessors, 7 skeptics, 1 critic); listing pages opened for the finalists.
  - Picks: Pi 5 8 GB kit with a Cytron 5.1 V 5 A PSU S$220; official Active Cooler S$10; B6neo S$48 (shop); test-only
    official 6 mm CS lens S$25.
  - Tools: FX-951 S$200 or YIHUA S$25; Fluke 17B+ S$175; Tenma 72-2925 10 A S$250; Siglent SDS1202X-E S$350; heat gun S$19.
  - Rejected after the page check: TTi TSX3510P (sold as-is for repair) and the "SanDisk 256GB" (an SD card).
  - None found: GS camera, X1203, EVF kit, eyepiece, 6 mm C-mount lens, encoder.
  - The BOM D2-09 estimate (S$55.80) is likely low (about S$100-125 new per the agents); not yet changed in make_bom.
- 2026-10-06: BOM section H "Second-hand alternatives" was added. It is generated by make_bom.py (SECONDHAND,
  SH_OPTIONAL, sh_section) and also writes secondhand.csv.
  - The landed-cost model covers: transport S$4 per seller; a 3 % Buyer Protection fee allowance; a 2-10 % risk
    allowance; no duty in Singapore (GST already in the new prices); new-delivery shares; and 1.5 h per seller.
  - Recommended picks H1 + H4-H6 save a net S$315.63 (gross S$386.18) for about 6 h of the user's time.
  - The camera-only pick (H1) saves S$65.58 net. The plan of record is unchanged.
- 2026-10-06: parfocal C-mount zoom desk research (2 agents) -> LENS-ZOOM-CANDIDATES.md + research/ZOOM-*.md. Top: Computar H6Z0812 manual (8-48 f/1.2, 305 g, ~S$60-130 used, est CoM +15 mm); only 6 mm-wide true zoom: Optivaron 6-66 (~600 g, CoM ~+41). Not adopted; CAD unchanged.
- 2026-10-06: user question: plastic GS-camera mount on the PCB vs heavy lenses. Load-path analysis + options (ring clamp, lens support collar, chassis C-mount) + G-LENS extension added to LENS-ZOOM-CANDIDATES.md. Not applied.
- 2026-10-06: M12-on-GS + phone-anamorphic desk research (2 agents) -> LENS-M12-ANAMORPHIC.md + research/M12-*, ANAMORPHIC-*, m12-drawings/. Key unknown: GS throat-floor depth (8.5 mm window, 1.1 mm IR filter). M12 setup CoM est -19 mm (-13 with Moment 1.33x); needs ~170 g front ballast in the housing to reach +4. Not adopted.
- 2026-10-06: user question: non-rotating helicoid for M12 + anamorphic. Feasible (keyed 3-part helicoid); focus stroke only ~0.07-0.13 mm, so needs preload + machined/SLA parts; recommend anamorphic on the FIXED base (tab to front plate), carrier only moves the lens. Edmund C-mount helicoids sit too far forward for M12. Section added to LENS-M12-ANAMORPHIC.md; nothing modelled.

## r5 heavy-lens support (2026-10-06, main session; user: "Fix the sagging issue for the heavy lens first")
- Brief `R5-BRIEF.md` (J7-R float adopted); study and implementation log `research/r5-lens-support/` (`IMPL-NOTES.md`
  steps 1 geometry, 2 checks + build, 3 docs + release).
- 16:06 coupons r5 (`make_coupons.py`: + collar_tub_front, collar_hood_plate, collar_part for G-COL-1; 23 + 4 STLs;
  hood_ledge_ret re-triangulated only). `build_d2.STATE_GATES`: G-COL-1 coupon gate, G-CAM-2 assembly item.
- 16:16 Fujinon `--fast --sweep-step 1.0` (out/_fujinon-r5): 27/27, 729 pass + 17 info + 0 fail; copied to
  out/checks-fujinon-sweep1mm.json (83b55def...).
- make_tables (WIRING, PRINT-GUIDE, ASSEMBLY, DESIGN blocks) and make_bom (67 purchased lines, D2-35..39 M3 hardware,
  D2-74 heat-set tip now in every build) before the release build; SPEC, FASTENER-POLICY (s I), MEASURED-PARTS
  (MP-CAM + lens line) written first (hashed).
- 16:32:38 Kowa release `--sweep-step 1.0` into out/ (579.6 s): 27/27, 749 rows = 732 pass + 17 info + 0 fail;
  checks.json c9d748c8...; 17/17 sources, 101/101 outputs, 4/4 gate docs; 55 gates (53 open, 2 withdrawn). r4 outputs
  kept in out/_r4-2026-10-06/. test_r3_regressions 38/38; make_tables --check stale none, lint 0 (history count
  phrases reworded in DESIGN, HANDOFF, OPTIONS, PRINT-GUIDE, RECTIFICATION).
- Balance: Kowa 895 g +1.5; Fujinon 782 g -9.8 (mass_com rules unchanged). Collar Kowa 17.0 g / Fujinon 18.6 g.
- 2026-10-06: r5 heavy-lens support (user: "Fix the sagging issue for the heavy lens first"). Design workflow (2 dossiers, 3 designs, 3 judges) found the GS mount is aluminium and the r4 camera model ~10 mm wrong; adopted J7-R float + per-lens lens_collar (R5-BRIEF.md). Implemented + released 16:32 (27/27, 732 pass / 17 info / 0 fail; Fujinon 27/27). Time-boxed review 17:02: 0 blocker / 0 major, 10 minor + 13 notes, fix list in HANDOFF s0. User asked to wind down by 18:00; no build after 16:32.
- 2026-10-07: cloud-polish package (4 zips, fork r5-cloud-polish-20261007) verified and ADOPTED as the desktop baseline. Package = desktop r5 at 22:04 SGT 10-06 + 81-file patch; local rerun reproduces it (87 STLs geometrically identical, check outcomes identical); final desktop Kowa receipt 13:34:26, 27/27, 748 pass + 18 info, audit 20/85/4 all match; software 256/256 after a Windows test-path fix. Pre-adoption: out/_r5-2026-10-06, baseline-r5-2026-10-06.zip. Audit 10-06 M1-M3 still unanswered.

## r6 print order, orientation and audit 2026-10-06 minor findings (2026-10-08, main session; user: "Settle the print order and orientation. Fix the minor findings as well.")
- Work in the `digital8mm` repository (the D2-only GitHub copy). Response to the audit:
  `audit/d2-readiness-2026-10-06/RESPONSE.md`. HANDOFF has the r6 section at the top.
- Orientation trial first, on the 10-07 STLs (scratch scan, then the final layer-slice method): every face-down
  confirmed. Two undeclared overhangs were found: the s_k2 boss chin (2.9 x 7.3 off the floor wall) and the LL insert
  boss chin (3.3 x 2.4 off the front wall). Both are now declared supports in `PRINT_SUPPORT_ZONES`.
- B-3 re-checked on the code: the 3.4 clearance runs through each boss end, so bottoming was impossible. The 4.184
  local depth was the LL face on the RV 5 corner. Bore deepened 0.1 anyway; the check is tightened.
- X2 options weighed: locating feet (no room beside the screws), an LR pin (about a 0.1 gain), a two-cone gauge with
  the collar fitted before the camera (adopted: no fit clearance in the chain).
- Tests: test_r3_regressions 65 -> 82 cases (17 r6 planted-fault cases); focused unittests 73; test_collar.
- Release sequence (CLOUD-START-HERE), 15:41-16:11 SGT: test_common, make_coupons, coupons_r1, Kowa build 15:50 (321 s), make_tables, make_bom (a quoting slip fixed: make_bom is not a hashed source), Fujinon 15:56:46, copy, Kowa final 16:05:33 (522.6 s; 28 categories, 833 pass + 19 info + 0 fail), make_tables design + print, check (one historical '12 tools' phrase in RECTIFICATION reworded), audit_cloud_release --final-release pass 20/86/4, then test_r3 82/82, focused 73 OK (4 skips), test_collar PASS 151.8 s.
- New numbers: collar 17.3 g (was 17.0); centring gauge 22.0 g (44.5 x 44.5 x 24.5); tub insert bores 4.3 deep. Centring rows: roll fin 0.25 left with the gauge (-0.05 without it), BFAR 0.45 (0.15), adapter 0.525 (0.225). Lens gaps: tub 3.33, hood 2.57.
- Still open: M1 (collar clamp spring and thermal term), every physical gate, G-W12. Nothing committed yet.
