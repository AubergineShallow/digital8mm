# FR1 study: base/grip lock (J4) and battery cap (J6)

Role fr-basecap, 2026-10-05 (Singapore time), per `../R3-BRIEF.md`. **Study only: no geometry, no CAD run, no CAD
edit.** Sources read: fork `layout.py` (J4 block, `J4_LOCK`/`s_j`, `SCREWS`, `CAP`/`CAP_JOINT`, `STRAP`, critical
features), fork `printed_grip.py` (`CAP_KEY`), baseline `SPEC.md` (J4, J6, G-CAP-1), `DESIGN.md` (mass/CoM table),
`PRINT-GUIDE.md` (coupons), `ASSEMBLY.md` (tools), `out/checks.json` and `out/parts-manifest.json` (r2 release,
built 03:39:36). Nothing here is printed, sliced, bought, measured or powered; load figures are hand estimates
from the CAD masses (proxies), not results. "pass" below only quotes computed r2 check rows.

Status: complete (written 09:14-09:20). A re-spawned copy has nothing left to do here; the follow-ups for other roles are in s8.

## 0. Conclusion (short)

- **J4 base/grip: retain `s_j` for FR1, unchanged.** It is the only element that resists the base sliding back
  out of its keyholes, and it is not touched by any service step. A screw-free latch is a *later option* (s3), best
  form an integral positive-stop tab in the base window, with its own gates (s3.2). None of the latch forms removes
  a part without adding a release action or an unverified printed load path, so none is proposed for FR1.
- **The panel 4 -> 2 change (s_b1/s_b2 removed) keeps the service-state load path but reduces in-use base
  restraint** (corrected 15:59 by fix-candidate, VC-M2): since the r2 fixer, s_b1/s_b2 are removed at every panel
  service and the base is then held by the tongues + `s_j` alone. **In use**, however, their shanks pass the base
  counterbores and the 2.0 base floor (dia 3.4 holes) and also clamp the base and restrain it in X (after about
  0.2 mm hole play). FR panel removes that: **in use `s_j` becomes the only restraint in the J4 unlock direction**
  (1 of 3 in-use X restraints remains) and the +Y edge clamp goes. This is a grip-retention trade-off for the user,
  not a computed load case; G-J4-1 gains an unlock-direction pull / EVF-first drop record with FR panel fitted (s5).
  One critical feature becomes stale (s4).
- **J6 battery cap: preserve as is** (tool-free +X slide, 2 integral keys, 0.35 detent, G-CAP-1 open).
- **Counts for these two joints are unchanged** (s6): J4 = 2 integral tongues + 1 PT screw (`s_j`); J6 = 0 screws,
  0 loose parts; the X1203 UPS kit (8 x M2.5 x 5, 4 standoffs) is unchanged and counted separately.

## 1. J4 as built (r2 / fork with D2_FR=none)

- Tub floor carries 2 keyhole T-tongues at x -18 (`tongue_f`) and x -79 (`tongue_r`): 8 long, neck 26 wide
  (z -1.85..0), head 36 wide (z -3.65..-1.85). Base (z -8..0, plate y +-35.2) has, per tongue, a window 10 mm ahead,
  a neck slot through 1.6 lips and a head pocket z -3.9..-1.6; clearance 0.25 (`SL`).
- Assembly (step 3, `base_on` sweep): base placed 10 mm behind its final position, lifted 15, raised onto the
  tongues through the windows, then slid **+X 10 mm**. **Unlock direction = base -X relative to the tub** (tub +X
  relative to the base); in the locked position each tongue sits 0.25 from the -X end of its slot and the empty
  window lies right behind it.
- `s_j`: PT 3.0 x 12 PH1, up through a base counterbore dia 7 (z -8..-2) at (-111, -20) into a tub floor boss
  (OD 8, z 0..12.6), engage 10, 0.35-0.5 N m, step 3. Head bears at z -2, so it sits 3.6 recessed in the base
  underside (a tripod plate still sits flat).
- r2 computed rows touching J4 (all pass): clearance `J4 tongue_f/tongue_r in base pocket` (min gap 0.25);
  critical features `tub_tongue_*_wing_*` (1.6), tongue necks, `base_keyhole_lip_*` (1.6), `tub_j4_lock_boss`;
  `boss_geometry s_j` (wall 2.748 vs 2.25 needed, pilot 11.0); `driver s_j` step 3 (bit gap 0.25, handle gap 2.35 to
  the strap); `layout_self_check` engage/length/step for `s_j`; interference `s_j`/hood, `s_j`/panel = 0; sweep
  `base_on`. Physical: the J4 coupon record (`tongue` + `keyhole_slot`: drop in, slide 10, no rock) is **not run**.

### 1.1 What `s_j` does

1. **Blocks the 10 mm return slide.** Nothing else resists base -X relative to the tub: the tongue heads and lips
   are free to slide in that direction until the tongues reach the windows and drop out.
2. **Clamps** the base floor (2.0 under the head, z -2..0) to the tub floor: preload removes the 0.25 joint play
   (the "no rock" requirement) and adds friction on the slide.
3. Secondary pull-off path (10 mm thread in the boss); the primary pull-off path is the 4 tongue wings under the lips.
4. **Independent of every service path**: it is driven at step 3 and is not in the `off` list of `panel_off`,
   `hood_off`, `keeper_out`, `pi_out`, `camera_out` or `eyepiece_out` (r2 removals rows). That is the r2 fixer's
   answer to verifier M-V-MPS-5 (r2 had made s_b1/s_b2 the only base lock, so panel service freed the base).

## 2. Loads on J4 (hand estimates, proxies; not results)

Masses (`parts-manifest.json`, `DESIGN.md`, Kowa default): whole camera 887 g, CoM (-43.3, 0.8, 26.6). Below J4
(base_grip 58.4, pack 105, strap 15, cap 7.2, tripod nut 4, run button 4, about half the XT30 pair 6) is about
**200 g**, so the body above J4 is about **690 g (6.8 N)** with its CoM at about **x -42, z +52** (5 mm ahead of the
grip axis x -47, 52 mm above the J4 plane z 0). Tongue pitch 61 mm (x -18 / -79); tongue wings at y +-15.5.

| Case | What J4 sees | Carried by | Order of size |
|---|---|---|---|
| Hand-held, level | compression 6.8 N, pitch moment 0.03 N m | base top in contact | negligible |
| Lens pointed down (or tripod head tilted forward 90 deg) | **shear in the unlock direction** 6.8 N, moment 6.8 x 0.052 = 0.35 N m | **`s_j` (shear + clamp friction)**; moment by the tongue pair (about 6 N per tongue) | x3 handling: 20 N shear on `s_j`, 1.1 N m |
| Lens pointed up | shear 6.8 N toward the slot ends | slot -X ends (tongue face on printed base) | small |
| Camera on its side (roll 90 deg) | moment 0.35 N m about X | tongue wings across y +-15.5 (about 11 N on one side) | x3: about 34 N |
| Strap: camera hangs from the hand strap, swung | J4 tension = body weight, the strap is all on `base_grip` (upper slots in the base, heel slots on the grip) | 4 tongue wings + 4 lips (+ `s_j` thread) | static 6.8 N; a 5 g jerk about 34 N |
| Tripod (nut in the base at x -107), level | body CoM 65 mm ahead of the tripod screw: 0.44 N m pitch | front tongue in compression, rear tongue in tension (about 7 N) | small |
| Drop, lens first (+X impact) | base (200 g) runs on +X relative to the tub = locking direction | slot -X ends | 200 g x 100 g = about 200 N on printed slot ends |
| **Drop, EVF/eyecup first (-X impact)** | base (200 g) runs on -X relative to the tub = **unlock direction** | **`s_j` alone** with the panel off (r2) and, with FR panel, in use too; in r2 in use the s_b1/s_b2 shanks share it (s4, VC-M2) (bearing in the 2.0 base floor round a 3.4 hole, plus clamp friction) | about 200 N at 100 g; a hard-floor hit can exceed that |
| Drop, grip heel first (-X/-Z) | tub (690 g) runs on -X relative to the base = locking direction | slot ends + tongue wings | several hundred N |

Reading: in normal use J4 loads are tens of newtons. The two cases that load the unlock direction (lens-down
orientation, rear-first drop) are carried only by `s_j`. Its weakest point is estimated to be the 2.0 base floor
under the head bearing on the shank (about 6 mm^2 of printed ASA, order 200 N) and the clamp friction, which relaxes
with ASA creep. This is the same order as an EVF-first drop estimate, so **J4 drop retention is a physical gate
whatever the lock is** (s5). Any screw-free replacement must at least match `s_j` in the unlock direction.

## 3. Screw-free J4 latch candidates (later option, not for FR1)

Requirement (user): retain the independent lock initially; never make panel retention the sole base lock again; a
screw-free alternative only if its independent latch is accessible and its retention/release can be verified.
Design-intent filter (brief): no extra loose piece, no inaccessible catch, no new release tool, no awkward motion.
Common constraint: the base underside is where the tripod plate, the hand and the strap sit; the latch must not be
pressed, blocked or released by a tripod quick-release plate (the 50 x 50 x 15 clamp in the fork `layout.py` keep-outs).

| Candidate | Geometry (idea) | Access / deliberate release | Retention in the unlock direction | Failure modes | Extra parts / tools | Verdict |
|---|---|---|---|---|---|---|
| **A. Integral positive-stop tab in the base window** | A cantilever cut in the base plate behind one tongue (the empty 8.5 x 36.5 window +X of `tongue_f` or `tongue_r`); its square tooth springs up into the window once the tongue has slid past and stands against the tongue head end face. Stop face 90 deg (a positive stop, not a ramp); only the lead-in face is 45 deg. | From below through a release hole in the 8 mm base plate: press the tab with the PH1 shaft already in the kit, hold, slide the base back 10 mm. Two hands. Visible from below: tab flush = engaged. | Shear of the tooth root, not spring force: about 200 N needs about 10-12 mm^2 of tooth (8 wide x 1.5) at a guessed 15-20 MPa; the base prints face-down +Z, so the tab lies in the layer plane (good for a cantilever). | Tab creep or set (ASA, hot car); tooth wear after cycles; a half-engaged state that looks closed; tripod plate or fingers holding it pressed; debris in the window; root cracking if over-deflected on release; the 0.25 slot play is no longer clamped (rattle). | -1 PT screw, -1 boss, +0 parts; tool: the existing PH1 shaft (so not tool-free) | Best later option. Not for FR1: retention and release unverified, loses the `s_j` clamp; needs the gates of s3.2. |
| B. Quarter-turn stud (bayonet / cam) | A printed or purchased stud through the base into a bayonet socket in the tub floor, turned 90 deg. | From below with a coin or the driver; a slot shows the position. | Printed bayonet ears in shear, or a new purchased quarter-turn fastener. | Vibration turns it; printed ears wear; the stud is lost when out; a coin is a new tool. | +1 loose printed or purchased part for -1 screw | Reject: swaps a screw for a loose or new purchased part; no simplification. |
| C. Captive slider (printed bolt in a dovetail track, pushed across behind a tongue) | A separate printed slider in a track in the base, pushed sideways into the empty window behind a tongue, held by a detent. | From the base side or from below; tool-free if a grip tab protrudes. | Slider in shear (a good section is possible); the detent only keeps it in place. | Detent wear lets it walk out under vibration (silent unlock); a loose piece during assembly; must be fitted before the base goes on; a protruding tab snags the strap or hand. | +1 printed part, -1 screw; tool-free | Reject for FR1: adds a loose piece and a step for one screw, and a silent-unlock mode the screw does not have. |
| D. Panel or hood retention as the base lock | (the r2 state before the fixer) | | | Panel service frees the base. | | **Excluded by the user.** |

### 3.1 Why `s_j` stays for FR1

- One purchased screw of the type already used 6 other times, driven with the one PH1 at step 3 from below in a
  straight line (computed `driver s_j` pass), never removed in service: zero service cost.
- It clamps the joint (no rock) and carries the unlock-direction load in steel and a 10 mm thread; a printed latch
  carries it in a printed root whose strength and creep are unknown until coupons exist.
- Candidate A saves one screw and one boss but adds a release hole, a two-handed release motion and a new physical
  gate set; the brief rejects a reduction that compromises grip retention or simplicity without evidence.

### 3.2 What a later latch study (candidate A) would need

CAD (computed, in a later fork under its own toggle; nothing written now):
- tab geometry and a deflection sweep (the tongue head passes the tab during the +X 10 slide; tab deflection within
  a stated flexure limit) and a positive-stop contact check in the locked state;
- critical features: tab root (class `flexure`, gated), tooth shear section (structural, 1.6), lips and wings as now;
  an `FR_JOINTS` entry `J4_latch` with `replaces=['s_j', 'tub_j4_lock_boss']`;
- release access: a straight path from below to the tab (like `driver`), and a keep-out showing that a 50 x 50
  tripod plate centred on the tripod nut cannot touch or hold the tab;
- the independent-lock rule of s4.2 item 6 (the latch counts only if no service removal touches it).

Physical gates (all not run; nothing printed):
- **G-J4L-1 retention**: coupon (tongue + base window with tab, printed as in production) pushed in the unlock
  direction to failure; accept at least the `s_j` value from G-J4-1 (s5) and at least 3 x the estimated EVF-first
  drop load; record the failure mode.
- **G-J4L-2 deliberate release**: release with the PH1 shaft, 20 lock/release cycles, no whitening or cracking at
  the root, engagement still positive; one person, no third hand.
- **G-J4L-3 state**: no half-engaged state that looks engaged (flush tab visible), checked every cycle.
- **G-J4L-4 creep/heat**: engaged coupon under a constant unlock-direction load (for example 20 N) at 60 deg C for
  2 h, then retention re-tested and tab set measured.
- **G-J4L-5 tripod/hand**: with a real quick-release plate and a hand grip the tab cannot be pressed or held.
- Then the whole-camera record G-J4-1 with the latch instead of `s_j`.

## 4. Panel 4 -> 2 (s_b1/s_b2 removed): effect on base retention

### 4.1 Finding

- s_b1/s_b2 run up through base counterbores at (-91, 27.85) and (-105, 27.85) into the panel bosses (joins
  base_grip + tub, step 8). They are in the `off` list of `panel_off`, `hood_off`, `keeper_out`, `pi_out`,
  `camera_out` and `eyepiece_out` (r2 removals rows), so in every r2 service state the base is already held by the
  tongues + `s_j` only. Removing them does not change the **service-state** load path: the unlock-direction slide
  is carried by `s_j`, pull-off by the tongue wings and lips, exactly as in r2 service.
- **In use it does change (fix-candidate VC-M2):** in the closed r2 camera the two shanks also bear in the base
  floor holes (3.4 round a 3.0 screw: about 0.2 play) and so restrain the base in X together with `s_j`. With FR
  panel the in-use unlock direction (-X: EVF-first drop, about 200 N at 100 g, s2 table) is carried by `s_j` alone in
  use as well, not only in the panel-off service state. The s2 'drop, EVF first' row is therefore the FR-panel in-use
  case. Not computed; recorded as a trade-off and added to G-J4-1 (s5).
- What does change: in the closed r2 camera they also clamped the base's **+Y edge** (y 27.85) to the panel bosses.
  The base plate spans y +-35.2 and the tongue heads only y +-18, so with FR panel the +Y edge (17 mm outboard) is
  free within the 0.25 tongue play and clamped only by `s_j` on the -Y side (y -20). That is a **fit/rattle and
  squeeze-stiffness item, not retention**; it belongs in the physical J4 record (no rock) in the FR panel state. If
  fr-panel adds integral keys at the old boss notches, they may also steady the base edge (fr-panel's choice).

### 4.2 Checks that must show it (fork, D2_FR=panel and D2_FR=all)

1. `SCREWS` still holds `s_j` with joins [base_grip, tub], step 3; `layout_self_check` engage/length/step pass.
2. `boss_geometry s_j`, `driver s_j` (step 3), interference `s_j`/panel and `s_j`/hood: pass, values unchanged.
3. Critical features `tub_tongue_*_wing_*`, the tongue necks, `base_keyhole_lip_*`, `tub_j4_lock_boss`: measured
   and pass; the `CRITICAL_JOINTS` entry `J4_tongues` (tub + base_grip) complete after the integrate-fork merge.
4. Clearance `J4 tongue_f/tongue_r in base pocket` (0.25) and sweep `base_on`: pass.
5. Stale items from the removed screws are named, not left to fail or to pass silently: critical feature
   `base_sb1_head_floor` (origin under the s_b1 head) goes into `FR_REMOVED_FEATURES` if fr-panel fills or removes
   the counterbores; the section "Base edge at s_b1" and the G-PANEL-1 `base_edge_*` coupons describe the r2 joint
   and are stale for the FR panel state.
6. **Proposed computed rule** (absent from r2 `checks.py`; for checks / integrate-fork): *J4 has an independent
   lock* = at least one screw or latch joining base_grip and tub that is in no service removal's `off` list. r2 and
   FR1 both meet it through `s_j`; the pre-fixer r2 would have failed it. Today it is stated only in docs.
7. STL comparison D2_FR=none vs D2_FR=panel: tub tongues, `s_j` boss and base pockets unchanged.

## 5. J4 physical gates that stay open (FR1 = r2 here)

- **J4 record** (`tongue` + `keyhole_slot` coupons): drop in, slide 10, no rock. Not run.
- **G-J4-1 (proposed name)**: assembled camera, panel off (the FR worst case) and closed: the base cannot slide back
  with `s_j` in; `s_j` holds 0.35-0.5 N m over 5 reuses (PT `reuse_max` 5); no rock at the +Y edge; a rear-first
  drop record only after G-PT-1. With FR panel fitted (fix-candidate VC-M2): an unlock-direction (-X) pull on the
  base with the closed camera, `s_j` the only X restraint, and the EVF-first drop record in that state. Not run.
- **G-PT-1** covers the `s_j` boss thread (strip torque, pull-out). Not run.

## 6. Battery cap J6: preserve

As built: the cap (ASA, prints on its bottom face, 7.2 g) has 2 integral keys inside the bay (web 1.6, 45 deg head
1.0 into a groove in each grip side wall) and slides **+X 52** by hand to open; the grooves are closed at x -60 (stop)
and run out through 2 front notches; a 0.35 bump on each key tip clicks into a 0.3 dimple near the rear while the
side-wall strip outside the groove (the detent arm, 1.25-1.5) flexes about 0.1. The strip is below the 1.6 loaded
rule and stays a **gated `flexure` exception (G-CAP-1)**, also in `CRITICAL_JOINTS` (brief). r2 computed: mate overlap
base_grip/cap 0, interference pack/cap 0, sweep `cap_on`, cap thin-wall min 1.599, the cap critical features pass or
are the named gated flexure entries. No change proposed: already screw-free and tool-free.

**G-CAP-1 coupon tests** (`cap_retention_grip` + `cap_retention_cap`; not run, nothing printed):
1. Pull retention: cap closed, 20 N pull-down (the 105 g pack at several g); no release, no lip whitening; then to
   failure with the failure mode recorded.
2. Detent hold: the cap stays closed when the coupon is tapped with the cap down and with +X (opening) down; the
   thumb opening force measured with a spring scale; the acceptance band is set from the first coupons (no number
   is claimed here).
3. Deliberate release: one thumb in the thumb grooves slides it open; no tool, no fingernail pry.
4. Repeated sliding: 20 open/close cycles; the detent still clicks; no cracking at the dimple; keys not loose.
5. Proposed extras (not in the r2 gate text): repeat 1-2 after 2 h at 60 deg C (ASA creep of the strip), and once
   with the real pack fitted.

Tuning parameters if G-CAP-1 fails (`printed_grip.CAP_KEY`, `layout.CAP_JOINT`; change only after a coupon result,
never to make a CAD row pass): `bump` 0.35 (detent height), dimple depth 0.3 and `dimple_y` 13.75 (sets the arm,
1.25 at the dimple), `bump_x` -57 (position), `bump_z` (-107.2..-106.0, 1.2 tall), `groove_y` 13.5 / `head_y` 13.25
(head engagement), clearance SL 0.25, groove top -105.55 / key top -105.8, `dovetail_deg` 45. Too weak: raise the
bump or thicken the arm (then re-check slide force). Too stiff or cracking: lower the bump or lengthen the free strip.

## 7. Counts and tools for these two joints (before = r2 / D2_FR=none; after = FR1 recommendation)

| Item | Before | After FR1 | Note |
|---|---|---|---|
| J4 integral features | 2 T-tongues (tub), 2 windows/pockets (base) | same | load path unchanged |
| J4 PT screws | 1 (`s_j`) | 1 (`s_j`) | s_b1/s_b2 are counted under the panel joint (4 -> 2 there) |
| J4 bosses | 1 tub floor boss | 1 | |
| J4 extra loose/printed parts | 0 | 0 | latch options B/C would add 1 (rejected) |
| J6 screws / loose parts | 0 / 0 (the cap is the only part) | 0 / 0 | |
| J6 integral features | 2 keys, 2 grooves, 2 detents | same | G-CAP-1 open |
| Tools | J4: the straight PH1 (`s_j`, step 3, from below); J6: none | same | the PH1 is already the only enclosure tool |
| **UPS kit (separate from the PT body screws)** | 8 x M2.5 x 5 pan PH (4 down through the Pi, 4 up through the X1203), 4 x M2.5 F-F hex standoffs 5 AF, 0.2 N m, step 1 at the bench | unchanged | PH1 if cross-recess; ISO 7045 PH1 substitute if the kit ships hex (ASSEMBLY tools) |

For the 7 -> 4 (or 5) PT body-screw target, J4 and J6 contribute nothing in FR1: `s_j` is one of the remaining 4
(or 5). If latch A is adopted later it could go one lower, at the cost of the s3.2 gates.

## 8. Open / hand-offs (this role writes no other file)

- integrate-fork: merge `J4_tongues` into `CRITICAL_JOINTS` unchanged; mark `base_sb1_head_floor`, the "Base edge
  at s_b1" section and the G-PANEL-1 `base_edge_*` coupons stale for the FR panel state; run s4.2 items 1-5 and 7.
- checks role (or later): consider the "J4 independent lock" rule (s4.2 item 6).
- fr-panel: optional integral key at the old boss notches to steady the base +Y edge (s4.1).
- Physical, not run: J4 record, G-J4-1 (proposed), G-PT-1 (`s_j` boss), G-CAP-1 (+ proposed heat repeat).
