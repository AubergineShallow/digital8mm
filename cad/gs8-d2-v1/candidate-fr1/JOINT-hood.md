# FR1 joint study: hood to tub (J1)

Owner: fr-hood, 2026-10-05 (Singapore time). This is part of the EXPLORATORY fork `candidate-fr1/`. The baseline
release in `../` is unchanged. Select a variant with `D2_FR=hood=<pins|yslide|screw1>`. `D2_FR=none` rebuilds r2:
the hood and tub STLs are sha256-identical to `../out/stl/hood.stl` and `../out/stl/tub.stl`
(`out/_hood-none/`).

Nothing has been printed, sliced, bought, measured or assembled. "pass" means a computed CAD check result, and
nothing more.

**Verdict: recommend `yslide`** (now `FR_DEFAULT['hood']`). It is the only variant with no flexure, no tool, no
loose part and no screw. `screw1` is built as the comparison. `pins` is kept as the baseline. The user chooses.

## 1. Baseline `pins` (r2 J1): assessment

Source: `layout.HOOK`, `HOOD_HOOKS`, `HOOD_RELEASE`, `RELEASE_ACCESS`, REMOVALS `hood_off`, ASSEMBLY.md item 9.

- **Parts.** The hood has 4 cantilever snap hooks (t 1.6, length 10.5, w 8). hk1/hk2 on the right wall have a
  90 deg positive catch. hk3/hk4 on the front/rear walls have a 45 deg return. The tub has 4 catch ledges plus
  2 dia 1.6 release holes through the right wall, which are visible on the right side.
- **Tools.** Two loose dia 1.5 steel pins (dowel 1.5 x 16 or drill shanks). This is the only J1-specific service
  tool kit.
- **Motions.**
  - Assembly: one straight drop, and 4 clicks.
  - Removal: push pin 1 about 3 mm in (it holds the hook open by friction), then push pin 2, then lift straight up
    60. hk3/hk4 cam out at the insertion strain. Then pull both pins.
- **Access.** Straight from the right, at z 87.7 (9.6 below the seam). Computed: the pin reaches the tooth with
  0 mm3 on any other part.
- **Retention in use.**
  - hk1/hk2 are positive.
  - hk3/hk4 only hold by spring force (45 deg return).
  - The left edge is held by the J2 panel tongue.
- **Computed margins.** Insertion strain 0.87 % (1.31 % with Kt). Pin hold-open strain 1.51 % (2.26 % with Kt,
  against a 2.5 % limit). The release is the most strained state.
- **Failure modes (untested).**
  - A pin can slip out mid-lift, so the hook re-latches.
  - A pin pushed too far over-deflects the hook. Only 0.15 of clearance is designed in, and nothing positive stops
    the pin.
  - Pins get lost.
  - The 4 snap beams whiten or creep after repeated service. ASSEMBLY.md already says "replace-on-service print".
  - hk3/hk4 corners can pop under a knock (spring-held only).
- **Physical gate.** G-SNAP-2 (hook coupons + 5 remove/refit cycles): not run.

## 2. `yslide` (recommended): drop, then a 2.5 mm push toward the right wall

### Geometry

Source: `layout.HOOD_YSLIDE`, `printed_hood._yslide_keys`, `printed_tub._yslide_tub`.

The 4 hook stations are kept, renamed yk1-yk4. Every key is rigid.

| Key | Hood feature | Tub feature | Catch |
|---|---|---|---|
| yk1 x -45, yk2 x -125 (right wall) | STAPLE: 2 legs 2.0 x 3.5 from the band + a bar 2.0 thick bridged 6.5 between them (bar top z 89.9) | TAB 6.0 wide x 2.4 thick (z 90.0-92.4), 2.0 proud of the wall inner face | flat 90 deg; bar under tab overlap 1.75 (Y) x 6.0; play 0.1 |
| yk3 front wall y 22, yk4 rear wall y -20 | leg 2.0 x 4.0 + 45 deg dovetail TOE 1.8 toward the wall (tip 1.6 thick, toe top z 88.5 at the tip) | LEDGE 1.8 proud, 45 deg underside parallel to the toe (normal gap 0.1), flat top z 91.8, root 3.5 long, -Y end 45 deg in plan | 45 deg; about 3.1 mm2 projected; the lift reaction pushes the hood away from the wall, into the end embrace (front plate on the tub front wall / housing rim on the rear wall, 0.15 computed) |

Other changes, all under `FR['hood'] == 'yslide'`:

- The plunger flange channel in the front plate is widened 2.5 toward -Y, because the flange enters it at the drop
  offset. The channel now meets the inner 1.2 of the microSD slot over 1.1 mm. The outer plate layer and the tub
  wall slot still guide the card.
- The stack-stop post x0 moves from -10.7 to -9.2. At the drop offset its corner met the cooler proxy. It still
  covers the kit head with a computed gap of 0.15.

The 4 hooks, 4 old ledges and 2 release holes are deleted. Hood mass is unchanged at 64.6 g; the tub is 96.4 g.

Print (both parts keep their orientation):

- Staple bar: a 6.5 bridge.
- Toe: 45 deg off the leg.
- Tab: grows straight up off the right wall on the bed.
- Ledge: 45 deg underside and flat top are vertical in print; the -Y end is 45 deg.

### Assembly and reverse service

The step 5 text is rewritten in the layout:

- **Assembly.** Hold the plunger in its hole. Lower the hood straight down 2.5 left (+Y) of its place until the band
  sits on the front/rear wall tops. Push it 2.5 toward the right wall (-Y) until it stops. Nothing clicks. Then the
  microSD goes in.
  - INSERTIONS `hood_on`: path (0, 2.5, 60) -> (0, 2.5, 0) -> (0, 0, 0), snaps none.
- **Removal (REMOVALS `hood_off`).** Same "off" set as the baseline: panel, camera, eyepiece, EVF pair and microSD
  out. Then push the hood 2.5 toward the open left side and lift straight up 60. Tool: none (hands).

**Why it stays put.** Free travel of the fitted hood was computed with `fr_hood_probe.py` (mesh booleans, results in
`out/_hood-probe/fr-hood-motion.json`):

| Direction | Service state (tub only) | In use (+ panel, camera, eyepiece, microSD) |
|---|---|---|
| +Z lift | 0.101 (keys) | 0.101 (keys) |
| +Y (unlock) | free (no contact within 6) | **0.20 (panel tongue in the J2 groove)**; 0.243 camera ring in the hood bore |
| -Y | 0.15 (right edge flange on the right wall) | 0.15 |
| +-X | 0.147 (front plate / housing rim end embrace) | 0.147 |
| lift with the hood held at its +Y stop | 0.101: all 4 keys still engaged | |

The unlock slide is therefore blocked by parts that are already there:

- The panel, which is screwed.
- The camera ring in the bore.

No catch is needed. A flexing detent or finger catch was considered and rejected. It would add a flexure and a
gate, it is not needed in use, and it is not needed in the assembly window between steps 5 and 7: gravity does not
slide the hood, and the camera at step 7 locks it.

If the user wants a click anyway, an integral detent can be added later. It needs its own flexure gate.

### Nearby components, cables and clearances (D2_FR=hood=yslide, `out/_hood-3/checks.json`)

All 21 categories pass (`--fast`, 2 mm sweeps). `cad_release_candidate: True`, no blocking items.
`release_access` has 0 entries; for yslide it is not applicable because there is no release.

| Check | Value |
|---|---|
| sweeps `hood_on` (34 positions) | 0 mm3 against tub, base_grip, Pi stack, cooler, pi_keeper, plunger and 25 cable keep-outs (ko_lead_wall, ko_qt_lead, ko_run_leads, ko_usb_evf, ko_5v_up and the others) |
| removals `hood_off` (34 positions) | 0 mm3, service state |
| sweeps `pi_in` | pass: the yk1 tab tip at y -30.5 clears the stack's 2.1 mm right-wall offset |
| sweeps `camera_in`, `evf_pair_in`, `eyepiece_in`, `sd_in`, `panel_on` | pass: the front key yk3 and the rear key yk4 clear the camera / EVF / eyepiece / panel paths |
| clearance `J1 hook yk1..yk4 to ledge` | min gap 0.10 each (play 0.1), 0 mm3 |
| clearance `J2 panel tongue in hood groove` | 0.25 |
| clearance `J7 camera ring in hood bore` | 0.25 |
| stack_retention | post gap 0.150 (window 0.1-0.3); max lift at the bosses 0.189, allowed 1.9; CoM hull margin 16.7 |
| critical_features (new) | tub_tab_yk1/2 = 2.4; hood_staple_bar_yk1/2 = 2.0; hood_staple_leg_yk*_n/p = 2.0; hood_key_toe_yk3/4 = 2.35; hood_key_leg_yk3/4 = 2.0; tub_dovetail_yk3/4 = 2.5; hood_stack_post = 3.7 (re-probed on the narrowed post). All pass against the 1.6 hook/lug class. |
| thin_wall hood / tub | pass |
| interference, keepouts, bed_fit, stl_mesh | pass |

Registry, in the `# --- FR hood` block plus an inline override after `HOOD_HOOKS`:

- `FR_JOINTS` `J1_hood_yslide` has 14 required ids.
- `FR_REMOVED_FEATURES` lists hood_hook_hk1-4, hood_tooth_hk1-4 and tub_ledge_hk1-4.
- `FR_VIEWS`:
  - `hood-yslide-x-45`: section through staple yk1.
  - `hood-yslide-y22`: section through the front dovetail.
  - `hood-yslide-z89`: plan section of all 4 keys.
  - `hood-yslide-motion`: drop + push, with the stack, keeper and plunger.
  - `hood-yslide-closeup`.

### Part and fastener changes (before -> after)

| Item | pins (r2) | yslide |
|---|---|---|
| Printed parts | hood, tub | hood, tub (same 2 parts) |
| Purchased parts | none | none |
| Body PT screws for J1 | 0 | 0 |
| Loose service tools | 2 x dia 1.5 pins | none |
| Flexures (snap beams) | 4 (G-SNAP-2) | 0 |
| Exterior holes | 2 x dia 1.6 in the right wall | none |

### Main trade-off

What yslide gives:

- No tool, no flexure, no loose pieces.
- Positive flat catches on the right wall.
- Front/rear catches that are positive through the end embrace. In r2 these corners were spring-only.

What it costs:

- One extra 2.5 mm push on assembly and on removal.
- In use, the hood relies on the panel tongue and the camera ring to block the unlock slide. When the panel is off
  for panel-only service, the camera ring still blocks it: computed 16:07 by a new 'panel off' probe set
  (`out/_hood-probe-paneloff`, D2_FR=all: +Y stop 0.243 on gs_camera, lift at that stop 0.101, keys engaged), but with
  gs_camera treated as a FIXED obstacle; the camera's own Y hold by the tub pins with the panel off is not computed
  (fix-candidate VC-L1; the panel-off +Y push added to G-YSLIDE-1 covers it physically). The slide
  is only free once the camera is also out, which is already the hood-service state.
- The rigid keys depend on the print holding the computed play: 0.1 in Z and 0.25 to the walls. Elephant's foot on
  the tab or ledge would bind the slide. G-YSLIDE-1 checks this.

## 3. `screw1` (comparison): straight drop + one PH1 retainer

Source: `layout.HOOD_SCREW1`, `printed_hood._screw1_boss`, the `screw1` part of the FR hood block.

- **Geometry.**
  - The same straight drop as r2.
  - All 4 hooks become 45 deg RETURN hooks. hk1/hk2 change from 90 deg; the ledges follow automatically. With 45 deg
    returns they cam out on a straight lift with no tool.
  - The 2 release holes go.
  - ONE PT 3.0 x 12 PH1 screw `s_h1` goes in from the right at x -85, z 91. It passes through the right wall and a
    new dia 12 x 2.0 pad (`pad_h1`, like s_r1), into a hood boss: od 8, D section hanging from the band, blind
    pilot 2.5 x 11.5, engagement 9.85.
  - The right edge flange stops 7 mm either side of the pad.
- **Assembly.** Drop, 4 clicks, then drive s_h1 straight from the right with the PH1 driver at step 5, 0.35-0.5 N m.
- **Removal.** s_h1 out, then lift straight up. The 4 return hooks cam out.
- **Tools.** The PH1 driver, which the panel and keeper already need.
- **Retention.** One positive screw at mid right edge, plus 4 spring-held 45 deg returns, plus the panel tongue.
- **Body screw count.** 4 -> 5.

## 4. Side by side

| | pins (r2 baseline) | **yslide (recommended)** | screw1 |
|---|---|---|---|
| Printed parts | hood + tub | hood + tub | hood + tub |
| Purchased / loose parts | 2 release pins (service tools) | none | +1 PT 3.0 x 12 PH1 screw |
| Body PT screws (FR1 target) | 4 | 4 | 5 |
| Tools to fit | none | none | PH1 driver (already in the kit) |
| Tools to remove | 2 x dia 1.5 pins | none (hands) | PH1 driver |
| Assembly motion | drop (4 clicks) | drop 2.5 off-place, push 2.5 -Y | drop (4 clicks) + drive 1 screw from the right |
| Removal motion | 2 pins in (hold-open), lift, 2 pins out | push 2.5 +Y, lift | unscrew 1, lift (4 return hooks cam out) |
| Access | 2 holes, straight from the right, z 87.7 | hood edges by hand, open left side | 1 screw head, straight from the right, z 91 |
| Retention | hk1/hk2 positive, hk3/hk4 45 deg spring, panel tongue | 2 flat staples + 2 dovetails with end embrace (all rigid); unlock slide blocked by the panel tongue (0.20) and the camera ring (0.243) | 1 screw (positive) + 4 x 45 deg spring returns + panel tongue |
| Flexures (physical gate) | 4 (G-SNAP-2) | 0 | 4 (G-SNAP-2) |
| Exterior marks | 2 dia 1.6 holes | none | 1 counterbored PH1 head (dia 7) |
| Highest computed strain | 2.26 % with Kt at pin hold-open (limit 2.5 %) | none (rigid) | 1.31 % with Kt (insertion / cam-out) |
| Computed (this machine) | r2 checks, all pass (../out) | 21 categories pass (`out/_hood-3`), probe (`out/_hood-probe`) | 21 categories pass (`out/_hood-s1-2`); no coupon of its own (PT boss = G-PT-1, return hooks = G-SNAP-2) |
| Physically untested | hook strain/whitening, pin hold-open, cycles | slide fit/binding, play, tab/ledge/staple strength, cycles | hook cam-out cycles, PT boss in the hood, head seat on pad_h1 |

## 5. Computed versus physically unverified

**Computed here.** CadQuery geometry; sweeps along the stated insertion and removal paths (2 mm steps, mesh
booleans); clearance zones; critical-feature chords; thin wall; bed fit; mesh integrity; stack retention; the
free-travel probe.

**Not established by CAD:**

- that the printed tab, staple, toe and ledge hold their nominal size;
- that the 2.5 mm slide does not bind (elephant's foot, warp of the 154 mm band);
- the lift strength and creep of the ASA keys;
- the real hand force;
- that the panel tongue and camera ring really carry a +Y knock;
- fatigue over service cycles;
- that the proxies (cooler, Pi stack, camera ring) match the real parts. The cooler clearance at the drop offset is
  0.3 against a proxy box (MEASURED-PARTS).

**Physical gates needed for yslide:**

- **G-YSLIDE-1 (new, proposed, not run).** Coupon pairs `out/stl/coupons-fr/coupon-fr-hood-{tub,hood}-{yk1,yk3}.stl`
  (`coupons_fr_hood.py`; manifest `out/coupons-fr-hood-manifest.json`):
  - slide force <= 10 N with no binding;
  - lift play <= 0.3;
  - 40 N lift for 60 s with the slide clamped, with no crack or whitening and set <= 0.2;
  - 10 cycles.
- **Whole-hood check.** Then 5 on/off cycles of the whole hood on a printed tub, with the panel and camera fitted,
  plus a +Y push on the roof to show that the panel tongue stops it. This replaces G-SNAP-2 for J1. G-SNAP-2 still
  applies to the encoder cradle hook.
- **Cooler.** The real Active Cooler outline near (-9.5, -25.5) at the drop offset: measure it before printing.

## 6. Verdict and reasons

1. **yslide: recommend.**
   - It removes the 2 release pins and the 2 holes without adding a screw.
   - It deletes all 4 snap flexures. G-SNAP-2 is no longer needed for J1.
   - It replaces spring-held corners with rigid keys.
   - Fitting and removal need only hands.
   - The unlock slide is short (2.5 mm). It needs no catch, because parts already present block it in use: the
     panel tongue, which is screwed, and the camera ring.
   - Every computed check passes, including the stack, plunger, cable and camera/EVF paths.

   Rejection criteria were checked and not met:
   - The catch is not inaccessible.
   - There is no new tool and no loose piece.
   - The travel does not bind in CAD: free +Y travel in the service state, 0.1 play.
   - No section is under 1.6 (smallest new probe 2.0).
2. **screw1: valid user choice, not recommended.**
   - It removes the pins too, with one straight-driver screw and a familiar motion.
   - It keeps the 4 flexures (now all 45 deg returns, so the corners are spring-held only).
   - It adds a purchased screw (body total 5 instead of 4) and a visible head on the right side.
   - It is simpler to describe than yslide, but it is not fewer parts or simpler service.
3. **pins: keep only as the fallback.**
   - It has the most delicate service step: 2 loose pins, a friction hold-open, and the highest strain in the joint.
   - It is still the validated r2 state.

**If G-YSLIDE-1 fails** (binding, set or cracking at the keys), fall back to screw1 rather than pins.

## 7. screw1 computed results (D2_FR=hood=screw1)

Build `out/_hood-s1-1` (`--fast`, 2 mm sweeps): 20 of 21 categories pass.

- `driver` s_h1 at step 5: pass. Bit 6.5 x 40 + handle 30 x 100 along +Y from the right, nearest 0.25 to the tub
  counterbore, no hits.
- `service_driver` (hood_off): pass.
- `boss_geometry` s_h1: pass.
  - pilot 2.5, depth 11.5 against 10.85 needed;
  - wall 2.75 against 2.25 needed;
  - 1.90 under the head on pad_h1.
- critical features: hood_boss_h1 2.75, tub_pad_h1 4.3, the 4 return hooks/teeth/ledges as r2. All pass.
- sweeps `hood_on` (straight drop, snaps hk1-hk4): pass.

The one failure was in `removals` `pi_out`. The Pi stack's reverse path met s_h1 (60 mm3). The cause: s_h1 was not
listed as already removed in the later service states, although it comes out with the hood.

That was a registry omission, not a geometry clash. It was fixed by adding s_h1 to the `off` list of every removal
that has the hood off. No check, threshold or path was changed.

Re-run `out/_hood-s1-2` (`--fast`, 2 mm sweeps): all 21 categories pass, `cad_release_candidate: True`,
no blocking items.

## 8. Files

- **layout.py**: inline `HOOD_YSLIDE` / `HOOD_SCREW1` after `HOOD_HOOKS`, the `# --- FR hood` block, and the
  `FR_DEFAULT` hood value.
- **printed_hood.py**: `_yslide_keys`, `_screw1_boss`, plus FR branches in `build_part`, `_edge_flange` and
  `_plate_cuts`.
- **printed_tub.py**: `_yslide_tub` and the FR branch in `build_part`. screw1 needs no tub code: pad_h1 and the s_h1
  counterbore come from the registries.
- **coupons_fr_hood.py**: writes `out/stl/coupons-fr/`.
- **fr_hood_probe.py**: writes `out/_hood-probe/fr-hood-motion.json`.
- **Builds:**
  - `out/_hood-3` and `out/_hood-4` (final re-run 12:03, all 21 pass): yslide.
  - `out/_hood-s1-1` and `out/_hood-s1-2`: screw1.
  - `out/_hood-none`: D2_FR=none hash check.
