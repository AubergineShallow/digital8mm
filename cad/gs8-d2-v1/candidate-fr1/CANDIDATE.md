> Cloud-polish fork note (2026-10-07 SGT): this pre-r5 study is historical and has not been rebased on the J7-R
> floating-camera/collar geometry. Its turret/pin assumptions cannot authorize adoption or a current thermal claim.
> Re-export and validate current geometry before resuming; physical airflow/power gates remain open.

# GS8 D2 fastener-reduction candidate FR1

**Status: EXPLORATORY, not adopted; the baseline release and its exports are unchanged.** (`cad/gs8-d2-v1/out/` is the
r3 release; nothing in this folder writes there.) Written by the integrate-fork role, 2026-10-05, from the joint
studies [JOINT-panel.md](JOINT-panel.md), [JOINT-keeper.md](JOINT-keeper.md), [JOINT-hood.md](JOINT-hood.md) and
[STUDY-base-cap.md](STUDY-base-cap.md). Every result below is a computed CAD check or a hand ESTIMATE. Nothing was
printed, sliced, bought, measured, assembled or powered. "Pass" means a computed check only. It does not mean a
verified fit.

## 0. What FR1 is and how to build it

- This is a fork of the r2/r3 D2 sources with every joint change under a toggle. `layout.py` reads `D2_FR`, which takes
  `all` (default = panel + keeper + hood=yslide), `none`, `panel`, `keeper`, `hood=pins|yslide|screw1`, or a comma
  list. **`D2_FR=none` rebuilds r2 exactly:** all 11 production STLs are sha256-identical to `../out/stl` (build
  `out/_none`, section 8).
- The fork uses the corrected r3 machinery. `build_d2.py` is a byte copy of the baseline, and `checks.py` is a byte copy plus the `no_release_required` row (section 8) (r3 checks:
  structured evidence, strict summaries, origin-always probes, `expect_outside`, `CRITICAL_JOINTS`). They were re-copied
  at 13:52 after the fix-baseline role's changes: `REQUIRED_JOINT_IDS`, the joint-coverage rules, and an empty category
  now FAILs. `layout.py` is a clean 3-way merge (`git merge-file`, 0 conflicts) of the baseline r3 block into the fork,
  and that R3 block was then re-synced to the current baseline. A new
  `# --- FR integrate` block folds each joint's `FR_JOINTS` / `FR_REMOVED_FEATURES` into `CRITICAL_JOINTS` for every
  toggle state (rule in section 8).
- Commands (repo root, CAD lock):
  `D2_FR=<sel> .venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py --max-wait-min 4 -- cad/gs8-d2-v1/candidate-fr1/build_d2.py --fast --out <dir>`.
  Also: `render_fr1.py` (views), `run_fr1_coupons.py` (coupons + trimesh + hood probe), `fr1_counts.py` (counts, no
  CAD), `fr1_validation.py` (table, no CAD).
- Views: [out/renders/fr1-index.md](out/renders/fr1-index.md) lists all 33 FR1 images with captions. There are 20
  FR views (sections, motions with waypoint ghosts, the path line and nearby cable keep-outs, and close-ups) and 13
  'before' images of the same windows at `D2_FR=none`. The full-build renders and STEP of the `all` state are in
  `out/renders/` and `out/step/`.

## 1. Summary of the proposals

| joint | r2 baseline | FR1 option(s) | PT screws | loose parts / tools | flexures | physical gate | verdict |
|---|---|---|---|---|---|---|---|
| Side panel (J3) | 4 PT (s_b1, s_b2 from below; s_r1, s_r2 from the right) | **A2**: 2 integral shear/seat keys + inner stiffening frame + s_r1, s_r2 | 4 -> 2 | PH1 only, from one side | 0 | **G-FRP-1** | user choice; recommended if G-FRP-1 passes |
| Pi keeper (J9) | 2 PT (s_k1, s_k2) | keyed tongue in a tub seat at the arm end + s_k2 | 2 -> 1 | PH1 only | 0 | **G-KEEP-1r** (+ G-PI-1) | recommend |
| Hood (J1) | 4 snap hooks + 2 loose release pins | **yslide**: drop, push 2.5 toward the right wall into 4 rigid keys | 0 -> 0 | no pins, no tool | 4 -> 0 | **G-YSLIDE-1** | recommend |
| | | **screw1**: drop onto 4 return hooks + 1 PH1 retainer s_h1 | 0 -> 1 | no pins; PH1 | 4 | G-PT-1, G-SNAP-2 | alternative |
| Base/grip (J4) | 2 T-tongues + lock screw s_j | unchanged (study only) | 1 -> 1 | PH1 | 0 | G-J4-1, G-PT-1 | keep s_j |
| Battery cap (J6) | dovetail keys + detent, tool-free | unchanged | 0 | none | detent arm | G-CAP-1 | keep |

PT body screws: **7 -> 4** with `D2_FR=all` (panel + keeper + yslide), or **7 -> 5** with screw1 for the hood. This
meets the user's provisional target (7 -> 4, or 5 with one hood retainer). The UPS kit is unchanged in every state: 8
M2.5 x 5 screws and 4 M2.5 standoffs, reported separately (section 7).

## 2. Panel: 4 -> 2 screws (concept A2, `FR['panel']`)

- **Geometry.** The 2 lower boss blocks become plain keys `key_b1` / `key_b2`. They have no pilot hole and a 1.0 x 45 deg
  lead chamfer on the -Y end. They sit in the existing tub lip notches with 0.3 side play, so the J3 ribs remain the
  only X locators. They seat 0.1 above the tub floor and pass under the keeper bridge with 0.25 clearance. fr-panel-2
  added an integral inner-face stiffening frame: a bottom chord through both keys, a diagonal tie to post_r, and 2
  uprights. s_b1 and s_b2 are deleted, together with the base counterbores, the floor holes and the boss pilots.
  Renders:
  [key section x -91](out/renders/fr1-frp-sec-x91.png) (before: [r2](out/renders/fr1-frp-sec-x91-before.png)),
  [keys at z 5.4](out/renders/fr1-frp-sec-z5.png) ([before](out/renders/fr1-frp-sec-z5-before.png)),
  [frame section y 28.7](out/renders/fr1-frp2-sec-y29.png) ([before](out/renders/fr1-frp2-sec-y29-before.png)),
  [frame x -125.5](out/renders/fr1-frp2-sec-x125.png), [base underside](out/renders/fr1-frp-bottom-after.png)
  ([before](out/renders/fr1-frp-bottom-after-before.png)).
- **Motion.** Assembly is one straight -Y push of 70 mm with the wired encoder and the 18/24 switch riding along, then
  s_r1 and s_r2 from the right. Removal is the reverse. No base screw, so a tripod plate need not come off. Renders:
  [removal +Y](out/renders/fr1-frp-motion-off.png), [insertion](out/renders/fr1-frp2-motion-on.png).
- **Clearances (computed).**
  - Sweeps `panel_on` and `panel_off`: 0 hits, with strap, s_j and base fitted.
  - Keys to the keeper bridge: 0.25 (clearance).
  - key_b1 to the X1203 envelope: 0.4.
  - Nearest cable keep-outs to the keys: 24.5 (ko_lead_cross).
  - The frame's front upright is 0.25 from the run-lead crossing keep-out.
  - Driver and service_driver for s_r1 and s_r2: pass.
  - Probes: keys 8.0 / 10.9, lip web 5.4, cheeks 5.47, post_r wall 2.75, frame bars 3.0-4.4 (min 1.6).
- **Parts / fasteners / tools.** -2 PT screws, -2 base counterbores. About +5 g ASA. One tool (PH1) and one drive
  direction instead of two.
- **Trade-off.** A straight-Y key cannot hold the bottom edge against an outward pull, so the edge is stiff rather than
  held. ESTIMATE (all mm/N outward): the seam between the keys is 0.001 in r2 (s_b1/s_b2 clamp it), 0.24 with keys
  only (A) and 0.057 with the frame (A2), so the seam is the real cost; the front bottom corner is 0.67 in r2 and
  0.47 in A2 (A2 is better there). Scripts and output: [estimates/](estimates/README.md) (`opts2.py`, re-run output
  `opts2-output.txt` reproduces the JOINT-panel s. 11.2 table).
  **Second cost (grip retention, fix-candidate VC-M2):** in r2 the shanks of s_b1/s_b2 pass the base counterbores and
  the base floor (dia 3.4 holes) into the panel bosses, so in use they also clamp the base to the tub and restrain it
  in X (after about 0.2 mm hole play) besides s_j. FR panel removes both, so **in use s_j is the only restraint in the
  J4 unlock direction** (1 of 3 in-use X restraints remains; the T tongues still carry Z and Y). In r2 this was
  already the state with the panel off; under FR panel it is the state in use too. Not computed as a load case;
  it is a trade-off for the user and is added to gate G-J4-1 / G-FRP-1 (section 9). The tilt-in hook (B) and the
  detent (C) were rejected (section 6).
- **Unverified.** Every stiffness number (hand/grillage ESTIMATE, no FEA), key fit and floor seat, print quality of the
  ribs, PT post pull-out. Gate **G-FRP-1** covers key coupon fit, seam gap under 2 N / 5 N between the keys, panel
  bow, front corner, EVF cap and frame roots.

## 3. Pi keeper: 2 -> 1 screw (`FR['keeper']`)

- **Geometry.** s_k1 and its floor boss are deleted. The keeper's USB-edge arm ends in a full-depth tongue (8 x 5.8 x
  6.75, with 0.6 lead-ins) that slides -Y 3 mm into a pocket in a new block on the tub's right wall and floor. The
  pocket has a 3.0 ledge bridged on 3 sides, 1.7 side walls, a lower jaw and a 5.1 back, with 0.15 fit on every side.
  s_k2 stays (straight PH1 from above, step 4). Renders:
  [x -101](out/renders/fr1-fr-keeper-sec-x101.png) ([before](out/renders/fr1-fr-keeper-sec-x101-before.png)),
  [y -28.5](out/renders/fr1-fr-keeper-sec-y285.png) ([before](out/renders/fr1-fr-keeper-sec-y285-before.png)),
  [z 12.7](out/renders/fr1-fr-keeper-sec-z127.png) ([before](out/renders/fr1-fr-keeper-sec-z127-before.png)),
  [close-up](out/renders/fr1-fr-keeper-closeup.png) ([before](out/renders/fr1-fr-keeper-closeup-before.png)).
- **Motion.** Slide -Y 60 from the left as in r2, then down 0.5, +X 1.2, -Y 3 into the seat, then s_k2. Removal is
  the exact reverse after s_k2 is out. Nothing flexes, and there is no latch or new tool. Renders:
  [keeper in](out/renders/fr1-fr-keeper-in.png), [Pi stack out](out/renders/fr1-fr-keeper-pi-out.png) (6 cable
  keep-outs drawn).
- **Clearances (computed).**
  - Tongue in seat: 0.15 with no overlap.
  - Seat to Pi 5: 1.77. Seat to X1203: 4.15. No keep-out overlaps the seat.
  - Sweeps `keeper_in` and `pi_in`, and removals `keeper_out` and `pi_out`: pass.
  - s_k2 driver and boss: pass.
  - Stack retention: worst boss lift 0.189 of 1.9 allowed. It is 0.24 if the full 0.15 seat play is added (JOINT-keeper
    s4 only; the official check still models a 0.1 gap).
  - The longest finger lever drops from 36.8 to 18.4 mm.
- **Parts / fasteners / tools.** -1 PT screw, -1 floor boss, +1 integral seat block. Mass: keeper +0.4 g, tub +0.4 g
  (estimates).
- **Trade-off.** The clamped screw at the arm end becomes a printed 0.15 fit, so a tight print could bind and a loose one
  rattle. **G-KEEP-1r** decides this: fit and play in ASA, ledge-root strength, rattle and 20 cycles. G-PI-1 must also
  cover the 3 mm -Y approach of fingers kf3 and kf4, which pass 0.1 above the X1203.

## 4. Hood: two-pin release assessed; yslide and screw1 compared (`FR['hood']`)

- **r2 pins, assessed.** Release needs 2 loose dia 1.5 pins held in by friction. The joint has 4 flexures under
  G-SNAP-2. Its highest computed strain, 2.26 % with Kt against a 2.5 % limit, occurs at pin hold-open. There are 2
  release holes in the right wall. Failure modes are in JOINT-hood s1.
- **yslide geometry (recommended).** The hood drops 2.5 mm off its place and is then pushed 2.5 mm toward the right wall
  (-Y).
  - Right wall: 2 staples on the hood (two legs and a bar) close under 2 tabs on the tub, with a flat catch.
  - Front and rear walls: 2 angled 45 deg toes slide under matching ledges. The front plate and the eyepiece housing
    embrace them, which stops cam-out.
  - Removed: the 4 snap hooks, both pins and both holes. Nothing flexes.
  - Side changes: the plunger channel is widened 2.5 mm toward -Y, and the stack-stop post x0 moves from -10.7 to -9.2
    to clear the cooler during the drop. The widened channel opens the inner 1.2 mm of the microSD slot over 1.1 mm
    (JOINT-hood s. 3); the outer plate layer and the tub wall slot still guide the card (fix-candidate VC-M4). The
    `sd_in` sweep passes, but it is a geometry check only: card guidance and catching are physically unverified.
  - In use, the unlock slide is blocked by the panel tongue tip (0.20) and the camera ring (0.243). At that stop all 4
    keys still engage (0.101 lift travel).

  Renders: [x -45](out/renders/fr1-hood-yslide-x-45.png) ([before](out/renders/fr1-hood-yslide-x-45-before.png)),
  [y 24](out/renders/fr1-hood-yslide-y22.png) ([before](out/renders/fr1-hood-yslide-y22-before.png)),
  [z 89](out/renders/fr1-hood-yslide-z89.png) ([before](out/renders/fr1-hood-yslide-z89-before.png)),
  [close-up yk1](out/renders/fr1-hood-yslide-closeup.png) ([before](out/renders/fr1-hood-yslide-closeup-before.png)),
  [drop + push](out/renders/fr1-hood-yslide-motion.png).
- **yslide clearances (computed).**
  - Key clearances at yk1-yk4: 0.10 (clearance rows "J1 hook yk* to ledge").
  - Every hood sweep passes against the 25 cable keep-outs: drop/push, removal, Pi stack, camera, EVF pair, eyepiece,
    microSD and panel.
  - Stack retention gap: 0.15.
  - Cooler at the drop offset: 0.3, against a proxy box only.
  - Free-travel probe: see section 8.
- **screw1 geometry (alternative).** A straight drop onto 4 hooks, all changed to 45 deg returns, then one PH1 screw
  `s_h1` from the right into a hood boss over the tub pad `pad_h1`. The pins and holes are gone. Probes: hood boss 2.75,
  pad 4.3. Renders: [section x -85](out/renders/fr1-hood-screw1-x-85.png), [motion](out/renders/fr1-hood-screw1-motion.png).
- **Counts and tools.** yslide: 0 screws, 0 pins, 0 flexures, no tool. screw1: +1 PT screw, 0 pins, 4 flexures, PH1
  (already in the kit). pins: 2 loose pins as the service tool, 4 flexures.
- **Trade-off.**
  - yslide adds one 2.5 mm push on assembly and on removal. Its in-use lock relies on the panel tongue and the camera
    ring. With the panel off (fix-candidate VC-L1, new probe set in `fr_hood_probe.py`, D2_FR=all ->
    [out/_hood-probe-paneloff](out/_hood-probe-paneloff/fr-hood-motion.json)): the +Y slide stops at 0.243 on gs_camera
    and the 4 keys still engage there (lift 0.101). That treats the camera as fixed; the camera's own Y hold by the
    tub pins with the panel off is NOT computed, so the panel-off lock remains partly an inference. It also narrows the microSD slot guidance on its inner side (above),
    and storage access is a stated priority. The rigid keys depend on the print holding 0.1 Z play
    and 0.25 to the walls, and elephant's foot would bind them.
  - screw1 keeps 4 spring hooks and adds a visible screw head.
- **Unverified.** Slide force, play, tab/ledge/staple strength and cycles. Gate **G-YSLIDE-1**: coupon pairs with slide
  force at most 10 N, lift play at most 0.3, 40 N lift for 60 s and 10 cycles, then 5 whole-hood cycles with the panel
  and camera fitted, plus a +Y push on the roof, plus a +Y push with the panel off (the inferred camera-ring stop),
  plus 10 microSD insert/eject cycles with no catching on the channel edge. The real Active Cooler must also be
  measured near (-9.5, -25.5).
- **screw1 unresolved info row (fix-candidate VC-M1).** The screw1 builds list one unclassified thin spot on the tub,
  t 0.98 at (-12.95, 31.85, 20.75) (status info, needs an owner decision). It is **not an FR change**: it is the 45 deg
  tip of the baseline tub gusset `rib_l` (x -13..-5.2, y 24.1..32.2; a 0.3 land at x -13), and a dense scan of the
  built STLs gives the same minimum 0.60 there in r2 (`../out`), FR none, all, yslide and screw1 (identical tub
  geometry in that region; [_thin_spot_rib_l.py](_thin_spot_rib_l.py) -> [out/_thin-spot-rib_l.txt](out/_thin-spot-rib_l.txt)).
  The thin-wall screen samples 1500 seeded random points per part, so only the screw1 tub mesh happens to put a sample
  on it. It stays visible as unresolved (validation table, section 8); no exception was added. Owner action for the
  **baseline** (rib_l is baseline geometry): a structural CRITICAL_FEATURES probe at the gusset or a geometry fix of
  the tip (raised in ../NOTES.md 'r3 interface requests').

## 5. Base/grip (J4) and battery cap (J6): kept (study, no geometry)

- **J4 keeps the lock screw s_j for FR1.** Nothing else stops the base sliding 10 mm back out of its keyholes. Two cases
  load that direction (hand ESTIMATES): holding the camera lens-down (about 7 N, 20 N with handling) and an EVF-first
  drop (about 200 N). In r2 with the panel fitted, the s_b1/s_b2 shanks share it with s_j; with the panel off (r2) or
  with FR panel fitted (in use), s_j carries it alone (VC-M2).
  - Three screw-free latches were assessed. The integral positive-stop tab is the best later option, with proposed
    gates G-J4L-1..5. The quarter-turn stud and the captive slider were rejected because they add loose or purchased
    parts and can unlock silently.
  - Removing s_b1 and s_b2 leaves the panel-off service-state load path unchanged, but **in use** their shanks also
    restrained the base in X and clamped its +Y edge: with FR panel `s_j` alone holds the base in the unlock direction
    in use (section 2 'second cost', VC-M2; G-J4-1). Not computed as a load case.
  - The STUDY s4.2 checks hold in `_none`, `_int-panel` and `all` (`_study42.py`): s_j driver, boss and interference
    pass; the J4 tongue/pocket clearances are 0.25; the `base_on` sweep passes; and the J4 probe values are identical
    across the three states.
  - The proposed rule "J4 has an independent lock" is computed in `fr1_counts.py`. It is s_j in every state. The stale
    r2 items were removed under FR panel: `base_sb1_head_floor`, `base_sb2_head_floor`, and the G-PANEL-1 `base_edge_*`
    coupons.
- **J6 cap is kept as it is.** It is tool-free and unchanged. Its detent arm stays a gated flexure exception under
  G-CAP-1 (20 N pull-down, detent hold, thumb release, 20 cycles, and a proposed 2 h at 60 °C repeat).

## 6. Rejected reductions (reasons)

| proposal | rejected because |
|---|---|
| Panel B: tilt-in bottom hook | needs a 4.24 deg two-stage arc; the post tips move 4.5-4.6 mm in z next to the right-wall pads, and the EVF cap clamp and the camera keeper finger arrive off-axis; not straightforward side removal |
| Panel C: keys + detent | adds a flexure with its own gate; the only pull-off grip is the push-on knobs |
| Panel 2-screw alternatives: rear-bottom screw from below; s_r1 + s_b2 | EVF cap 3-9x softer than r2; a second drive direction and base access (JOINT-panel s11.3) |
| Panel long captive dovetail | does not fit around the camera keeper, EVF stop, eyepiece clamp and wired controls (brief) |
| Keeper: key at the front of the bar | the J4 lock boss limits the stroke to < 1.75 mm |
| Keeper: s_k1 alone, no key | leaves a 55 mm bar cantilever |
| Keeper: long dovetail along the slide; panel rib; snap latch | longer sliding fit around the stack, or panel-dependent / flexure retention (JOINT-keeper s2) |
| Hood: longitudinal slide | blocked by the end geometry (brief) |
| Base: quarter-turn stud, captive slider | a loose or purchased part; silent unlock if the detent wears |
| Base: panel as the only base lock | forbidden by the brief (the r1 defect) |

## 7. Before/after counts and service sequences (computed from the layout: `fr1_counts.py`)

Each column is computed from `layout.PARTS` / `SCREWS` / `COTS` / `X1203_KIT` / `STEPS` / `REMOVALS` / `RELEASE_ACCESS` in a fresh process per `D2_FR` value. Full data: [out/fr1-counts.json](out/fr1-counts.json); the table and the full action lists are in [out/fr1-counts.md](out/fr1-counts.md). "Purchased lines" counts COTS rows, and the PT screws are one row, so a screw reduction does not change it. The release pins in r2 are a service tool (a dowel or drill shank), not a BOM part.

| D2_FR | printed parts | PT body screws | UPS kit M2.5 screws | UPS kit standoffs | purchased lines (COTS) | loose release pins | assembly steps | PT screw ids | J4 independent lock | tool categories |
|---|---|---|---|---|---|---|---|---|---|---|
| none | 11 | 7 | 8 | 4 | 21 | 2 | 10 | s_b1, s_b2, s_r1, s_r2, s_k1, s_k2, s_j | s_j | ESD strap, PH1 screwdriver, junior hacksaw + file, multimeter, paint pen, release pins (2 x dia 1.5), socket / spanner, soldering iron, tweezers |
| panel | 11 | 5 (-2) | 8 | 4 | 21 | 2 | 10 | s_r1, s_r2, s_k1, s_k2, s_j | s_j | ESD strap, PH1 screwdriver, junior hacksaw + file, multimeter, paint pen, release pins (2 x dia 1.5), socket / spanner, soldering iron, tweezers |
| keeper | 11 | 6 (-1) | 8 | 4 | 21 | 2 | 10 | s_b1, s_b2, s_r1, s_r2, s_k2, s_j | s_j | ESD strap, PH1 screwdriver, junior hacksaw + file, multimeter, paint pen, release pins (2 x dia 1.5), socket / spanner, soldering iron, tweezers |
| hood=yslide | 11 | 7 | 8 | 4 | 21 | 0 (-2) | 10 | s_b1, s_b2, s_r1, s_r2, s_k1, s_k2, s_j | s_j | ESD strap, PH1 screwdriver, junior hacksaw + file, multimeter, paint pen, socket / spanner, soldering iron, tweezers |
| hood=screw1 | 11 | 8 (+1) | 8 | 4 | 21 | 0 (-2) | 10 | s_b1, s_b2, s_r1, s_r2, s_k1, s_k2, s_j, s_h1 | s_j | ESD strap, PH1 screwdriver, junior hacksaw + file, multimeter, paint pen, socket / spanner, soldering iron, tweezers |
| all | 11 | 4 (-3) | 8 | 4 | 21 | 0 (-2) | 10 | s_r1, s_r2, s_k2, s_j | s_j | ESD strap, PH1 screwdriver, junior hacksaw + file, multimeter, paint pen, socket / spanner, soldering iron, tweezers |
| panel,keeper,hood=screw1 | 11 | 5 (-2) | 8 | 4 | 21 | 0 (-2) | 10 | s_r1, s_r2, s_k2, s_j, s_h1 | s_j | ESD strap, PH1 screwdriver, junior hacksaw + file, multimeter, paint pen, socket / spanner, soldering iron, tweezers |

Service sequences: every internal service starts with **shutdown, cap off, pack out and XT30 unplugged** (ASSEMBLY s7 P1-P4; a halted Pi is not isolation). The fitted-pack removal sweeps are geometry evidence only (`scope` field). Action counts include those 4 preamble steps:

| service | none (r2) | all (FR1 recommended) | panel,keeper,hood=screw1 |
|---|---|---|---|
| panel off | 9 | 7 | 7 |
| hood off | 25 | 22 | 24 |
| Pi stack out | 30 | 27 | 28 |

- r2 panel off: 4 screws (2 from below, 2 from the right), so the tripod plate must come off. FR1: s_r1 and s_r2 from the right only.
- r2 hood off: 2 loose pins into the right wall (hold-open), then lift. yslide: push 2.5 +Y, then lift, by hand. screw1: s_h1 out, then lift.
- Pi stack out: r2 removes s_k1 + s_k2. FR1 removes s_k2, then the keeper backs out of its seat (+Y 3, -X 1.2, up 0.5, +Y 60).
- Assembly steps stay at 10 in every state. The tool categories drop the release pins in every hood variant except pins.

## 8. Validation (computed checks only; `fr1_validation.py` -> [out/fr1-validation.md](out/fr1-validation.md))

| build dir | D2_FR | mode | built_at | checks version | categories pass | critical features (pass / info / fail) | joints | sweeps | removals | driver | service driver | release_access | unresolved info rows (unclassified thin spots) | layout.py | STLs changed vs r2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| out/_none-premerge | none | --fast, sweeps 2 mm | 2026-10-05 12:26:42 +0800 | PRE-MERGE r3 checks (before 13:52) | 21/21 | 109 / 9 / 0 | 12/12 pass | 12/12 | 11/11 | 7/7 | 6/6 | 2/2 | none | older | none: all 11 identical to r2 |
| out/_none | none | --fast, sweeps 2 mm | 2026-10-05 15:37:51 +0800 | current (re-merged r3 + no-release row) | 21/21 | 108 / 10 / 0 | 11/12 pass | 12/12 | 11/11 | 7/7 | 6/6 | 2/2 | none | current | none: all 11 identical to r2 |
| out/_int-panel | panel | --fast, sweeps 2 mm | 2026-10-05 12:45:56 +0800 | PRE-MERGE r3 checks (before 13:52) | 21/21 | 119 / 9 / 0 | 14/14 pass | 12/12 | 11/11 | 5/5 | 4/4 | 2/2 | none | older | base_grip 68418346, panel f335e0d9, tub 416bb1d0 |
| out/_int-keeper | keeper | --fast, sweeps 2 mm | 2026-10-05 12:56:28 +0800 | PRE-MERGE r3 checks (before 13:52) | 21/21 | 115 / 9 / 0 | 12/12 pass | 12/12 | 11/11 | 6/6 | 5/5 | 2/2 | none | older | pi_keeper 630d80c7, tub d376d352 |
| out/_int-hood-yslide | hood=yslide | --fast, sweeps 2 mm | 2026-10-05 13:08:03 +0800 | PRE-MERGE r3 checks (before 13:52) | 21/21 | 111 / 9 / 0 | 12/12 pass | 12/12 | 11/11 | 7/7 | 6/6 | n/a (0 rows: nothing to release) | none | older | hood e02f09fd, tub 55c1ab4d |
| out/_int-hood-screw1 | hood=screw1 | --fast, sweeps 2 mm | 2026-10-05 13:16:04 +0800 | PRE-MERGE r3 checks (before 13:52) | 21/21 | 111 / 9 / 0 | 12/12 pass | 12/12 | 11/11 | 8/8 | 7/7 | n/a (0 rows: nothing to release) | tub t 0.98 at (-12.95, 31.85, 20.75) (near tub_pi_boss_1) | older | hood 9848ee09, tub 31f99d82 |
| out/_int-hood-yslide-r3m | hood=yslide | --fast, sweeps 2 mm | 2026-10-05 16:21:14 +0800 | current (re-merged r3 + no-release row) | 21/21 | 110 / 10 / 0 | 11/12 pass | 12/12 | 11/11 | 7/7 | 6/6 | 1/1 (no_release_required row) | none | current | hood e02f09fd, tub 55c1ab4d |
| out/_int-hood-screw1-r3m | hood=screw1 | --fast, sweeps 2 mm | 2026-10-05 16:28:05 +0800 | current (re-merged r3 + no-release row) | 21/21 | 110 / 10 / 0 | 11/12 pass | 12/12 | 11/11 | 8/8 | 7/7 | 1/1 (no_release_required row) | tub t 0.98 at (-12.95, 31.85, 20.75) (near tub_pi_boss_1) | current | hood 9848ee09, tub 31f99d82 |
| out/_int-panel-r3m | panel | --fast, sweeps 2 mm | 2026-10-05 15:50:30 +0800 | current (re-merged r3 + no-release row) | 21/21 | 118 / 10 / 0 | 13/14 pass | 12/12 | 11/11 | 5/5 | 4/4 | 2/2 | none | current | base_grip 68418346, panel f335e0d9, tub 416bb1d0 |
| out/_int-keeper-r3m | keeper | --fast, sweeps 2 mm | 2026-10-05 15:57:44 +0800 | current (re-merged r3 + no-release row) | 21/21 | 114 / 10 / 0 | 11/12 pass | 12/12 | 11/11 | 6/6 | 5/5 | 2/2 | none | current | pi_keeper 630d80c7, tub d376d352 |
| out/_int-pks1 | panel,keeper,hood=screw1 | --fast, sweeps 2 mm | 2026-10-05 15:44:56 +0800 | current (re-merged r3 + no-release row) | 21/21 | 126 / 10 / 0 | 13/14 pass | 12/12 | 11/11 | 5/5 | 4/4 | 1/1 (no_release_required row) | none | current | base_grip 68418346, hood 9848ee09, panel f335e0d9, pi_keeper 630d80c7, tub f30db9d8 |
| out/ | all (panel A2, keeper, hood yslide) | full: renders, STEP, sweeps 1 mm | 2026-10-05 15:26:25 +0800 | current (re-merged r3 + no-release row) | 21/21 | 126 / 10 / 0 | 13/14 pass | 12/12 | 11/11 | 4/4 | 3/3 | 1/1 (no_release_required row) | none | current | base_grip 68418346, hood e02f09fd, panel f335e0d9, pi_keeper 630d80c7, tub 093d116a |

- **Toggles are clean.** With `D2_FR=none`, all 11 production STLs are sha256-identical to `../out/stl`. The `none` registry (CRITICAL_FEATURES, CRITICAL_JOINTS, SCREWS, STEPS, REMOVALS, EXPECT_OUTSIDE) equals the baseline `../layout.py`.
- **Joint coverage fold** (layout `# --- FR integrate`). Rule: an FR joint that supersedes a baseline joint (`FR_JOINT_SUPERSEDES`: FR_panel_keys > J3, J9_keeper_fr > J9_pi_keeper, J1_hood_yslide / J1_hood_screw1 > J1) replaces it by the union of its own required ids and the baseline ids that were not declared removed. Other FR joints (FR_panel_closure, FR_panel_frame) are added. Only ids explicitly in `FR_REMOVED_FEATURES` leave a joint, so an undeclared loss still fails. Merge finding: r3 added `panel_boss_b2_cap` and `base_sb2_head_floor` (b2 twins of probes fr-panel had removed). Under FR panel they describe geometry that is not built, so the fold removes and declares them. With `D2_FR=all` there are 14 joints and all pass. The 3 G-CAP-1 flexures stay gated exceptions.
- **release_access without pins (fork-only addition to `checks.py`).** The re-merged r3 rule V-M4 makes an empty category FAIL, and the first `all` build with the re-merged checks (14:04:50) failed release_access for exactly that reason: yslide and screw1 have no RELEASE_ACCESS entry. The rule was kept. Instead `checks._no_release_row` adds one computed row, `no_release_required`, whenever RELEASE_ACCESS is empty. It passes only if (1) no hood hook keeps a release hole; (2) no hood hook is a flexing 0 deg catch (a 0 deg hook must be a rigid yslide staple); (3) the `hood_off` removal exists, its tool names no pin, and it lists only 45 deg cam-out hooks under `release`; and (4) the built tub right wall is solid (OCP point-in-solid) at both baseline pin-hole centres. A forced run on `D2_FR=none` fails on all five reasons, so the row discriminates. The baseline never reaches this path, because its RELEASE_ACCESS has 2 entries. The fork `checks.py` is therefore the baseline copy plus this one function and its 2-line call.
- **Which numbers come from which checks** (refreshed 16:05 by fix-candidate). Built with the current fork checks (the
  re-merged r3 checks plus the no-release row): the final candidate `out/` (full, 1 mm; rebuilt 15:26 after the VC-L5
  caption edit, its 11 STLs byte-identical to the 14:25 build), `out/_none` (rebuilt 15:37, 11/11 STLs == r2),
  `out/_int-panel-r3m` and `out/_int-keeper-r3m` (15:50 / 15:57, VC-L3), `out/_int-pks1` (panel + keeper +
  hood=screw1, the 5-screw alternative, 15:44, VC-L2; the verifier's own `out/_verify-candidate-pks1` gave the same
  result), and `out/_int-hood-yslide-r3m` / `out/_int-hood-screw1-r3m` (rebuilt 16:21 / 16:28 with the current
  layout.py; same STL hashes as their 14:47 / 14:54 builds). All pass 21/21 and all show `layout.py` 'current'.
  `out/_int-panel`, `out/_int-keeper`, the older `_int-hood-*` and `_none-premerge` used the PRE-MERGE r3 checks and the
  layout.py from before the R3 re-sync (their panel/keeper STLs equal the current ones); they are kept as history.
  The only joint row that is not a pass is J6_cap_grip, which is `info` (G-CAP-1 flexures gated), as in the baseline
  `../out`. **Unresolved info rows:** the column 'unresolved info rows' lists `results.unclassified_thin_spots`; only
  the screw1 builds have one (tub t 0.98 at (-12.95, 31.85, 20.75)), the baseline `rib_l` gusset tip that exists
  identically in every state including r2 (section 4, VC-M1). It is not cleared and not excepted.
- **No-release row reproducible** (VC-L4): `_test_norelease.py --force` calls `_no_release_row` whatever
  RELEASE_ACCESS says; on D2_FR=none it fails with all five reasons, on all and hood=screw1 it passes
  ([out/_test_norelease-force.log](out/_test_norelease-force.log)).
- The joint roles' own earlier builds (pre-merge r2 checks) also passed all categories: `out/_panel2-2`, `out/_keeper-1`, `out/_hood-4`, `out/_hood-s1-2`.
- `cad_release_candidate: True` in these receipts is the pipeline's computed flag only. The candidate is exploratory, and every hardware gate is open.

## 9. Remaining physical gates and coupons (all NOT RUN; nothing printed or measured)

- **Coupons.** `run_fr1_coupons.py` was re-run on the final fork at 14:32-14:39 with `D2_FR=all`. All 5 jobs returned 0, and it exported 24 coupon STLs. trimesh found
  every one watertight, winding-consistent and with positive volume
  ([out/fr1-coupons-check.json](out/fr1-coupons-check.json)).
  - FR coupons in `out/stl/coupons-fr/`:
    - panel: `coupon-frp-tub-lip`, `coupon-frp-panel-keys` (G-FRP-1);
    - keeper: `coupon-fr-keeper-seat`, `-stub`, `-tub`, `-part`, `-x1203`, `-pi` (G-KEEP-1r);
    - hood: `coupon-fr-hood-tub-yk1`, `-hood-yk1`, `-tub-yk3`, `-hood-yk3` (G-YSLIDE-1).
    The manifests are `out/coupons-fr-*-manifest.json`.
  - The r2 set is in `out/stl/coupons/`, cut from the FR parts (12 coupons). These include the calibration coupons
    G-KNOB-1 (`knob_bore_ladder_enc` / `_sw`), G-COMB-1 (`clearance_comb`) and G-J4-1 (`tongue`, `keyhole_slot`).
    `make_coupons.py` (fork) drops, and lists under `fr_dropped` in `out/coupons-manifest.json`, the rows whose features
    FR removed:
    - `pt_boss_bottom` and `base_edge_*` (the G-PANEL-1 base edge), under FR panel;
    - `hood_hook*` and `hood_ledge*`, under yslide.
  - The r1 keeper coupons (`coupons_r1.py`) describe s_k1 and are not run for the fork; G-KEEP-1r replaces them for the
    candidate.
- **Hood probe on the merged fork** (`fr_hood_probe.py`, D2_FR=all, `out/_int-hood-probe`). The result is unchanged from
  fr-hood's own run:
  - in use: +Y stop 0.20 (panel tongue), +-X 0.147, -Y 0.15, lift 0.101;
  - at the +Y stop: lift 0.101, so all 4 keys still engage.

  This confirms that the yslide in-use lock survives the A2 panel change.
- **Gates.**

| gate | covers | state |
|---|---|---|
| G-FRP-1 | panel key fit and floor seat; seam gap at 2 N / 5 N outward between the keys; panel bow; front corner, EVF cap and frame roots | not run (new) |
| G-KEEP-1r | 0.15 seat fit/play in ASA, ledge-root strength, rattle, 20 cycles | not run (new; replaces G-KEEP-1 for the candidate) |
| G-PI-1 | as r2, plus the 3 mm -Y approach of kf3/kf4 0.1 above the X1203 | not run |
| G-YSLIDE-1 | coupon pairs: slide force at most 10 N, lift play at most 0.3, 40 N lift for 60 s, 10 cycles; then 5 whole-hood cycles with the panel and camera fitted, and a +Y roof push; a +Y push with the panel off (inferred camera-ring stop, VC-L1); 10 microSD insert/eject cycles with no catching on the widened channel edge (VC-M4) | not run (new) |
| G-PT-1, G-SNAP-2 | screw1 only: hood boss, 4 return hooks | not run |
| G-J4-1, G-PT-1 (s_j), proposed G-J4L-1..5 | J4 tongue/keyhole fit, s_j over 5 reuses, rear drop; with FR panel fitted: unlock-direction (-X) pull and EVF-first drop record with s_j as the only in-use X restraint (VC-M2); the later latch option | not run |
| G-CAP-1 (+ proposed 60 °C repeat) | cap pull-down, detent, thumb release, 20 cycles | not run |
| Active Cooler measurement near (-9.5, -25.5) | yslide drop clearance (0.3 to a proxy) | not measured |
| every r2/r3 gate | EVF optics, power workload, wiring, measured parts | unchanged: open |

## 10. Recommendation: the choices for the user

All options below pass the computed checks (section 8 table, including the 5-screw combination panel + keeper +
hood=screw1 in `out/_int-pks1`). None is physically verified, and adoption should wait for the named gate.

1. **Hood: `yslide` (recommended), `screw1`, or keep `pins`.** yslide is the real simplification. It removes the 2
   loose pins, the 4 flexures and the 2 wall holes, with no screw and no tool, at the cost of a 2.5 mm push and a print
   fit that G-YSLIDE-1 must confirm, and a widened plunger channel that opens the inner 1.2 mm of the microSD slot over
   1.1 mm (card guidance unverified; G-YSLIDE-1 microSD cycles). screw1 trades the pins for one visible PH1 screw and keeps the 4 spring hooks.
   Keep pins only if G-YSLIDE-1 fails.
2. **Panel: A2 2-screw keys (recommended if G-FRP-1 passes), or keep the r2 4-screw panel.** A2 gives one drive
   direction, no base screws and no tripod-plate removal for panel service. The costs: an ESTIMATED softer seam
   between the keys (0.001 -> 0.057 mm/N), an edge that is stiff rather than held (G-FRP-1 decides it), and **less
   in-use grip retention**: s_b1/s_b2 also restrained the base in X in use, so with A2 `s_j` alone holds the base
   in the unlock direction (G-J4-1 with FR panel fitted decides it).
3. **Pi keeper: keyed seat + s_k2 (recommended), or keep s_k1 + s_k2.** It halves the finger lever and needs no new
   tool. It adds one printed 0.15 fit (G-KEEP-1r).
4. **Base/grip and battery cap: no change** (keep s_j and the tool-free cap). A screw-free J4 tab is a later study.

Resulting PT body screws: all recommended = **4** (s_r1, s_r2, s_k2, s_j). With screw1 = **5**. r2 = 7. The UPS kit
(8 M2.5 screws, 4 standoffs) is unchanged.

## 11. Open items from the integration (not fixed here)

- The fork receipt's gate scan reads the baseline gate docs (`../MEASURED-PARTS.md`, `../SPEC.md`, WIRING). The new
  gates G-FRP-1, G-KEEP-1r and G-YSLIDE-1 are listed only here, in the JOINT files and in the coupon manifests. They
  would enter `open_evidence` only if the candidate is adopted and the gates are written into the release gate docs.
- The keeper's requested clearance zone "J9 keeper tongue in tub seat (0.15)" is not in `checks.clearance_zones`. The
  list is hard-coded in the copied r3 `checks.py`, and a registry hook is needed. The 0.15 gap is covered by
  `test_fr_keeper.py` (probe), not by the build.
- release_access with no pins: the re-merged r3 checks fail an empty category (V-M4). The fork adds the computed
  `no_release_required` row (section 8). If FR is adopted, the baseline `checks.py` needs the same function, or an
  equivalent one.
- The receipt `sources` lists `SPEC.md` / `FASTENER-POLICY.md` as 'missing'. `source_hashes()` hashes only files in the
  build folder, and the fork reads those docs from `..`. Only the provenance hash is affected. The gate scan reads the
  parent docs.
- `test_keeper.py` (the baseline harness copied into the fork) still names s_k1 and is not used for FR builds.
  `coupons_r1.py` is not run for the fork.
- Not studied: a lower s_r2 post (a possible positive bottom-edge hold for the panel), and the screw-free J4 tab.
