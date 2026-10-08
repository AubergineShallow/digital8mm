# candidate-fr1 notes (EXPLORATORY fastener-reduction fork of cad/gs8-d2-v1; see ../R3-BRIEF.md)

Created 2026-10-05 09:10 by the main session: sources copied from ../ (r2 release state, built 03:39:36); `_base/` holds
the same copies as the merge base. `layout.py` reads env var D2_FR (all | none | panel | keeper | hood=<pins|yslide|screw1>
| comma lists). Every joint change sits under `if FR['<joint>']` so D2_FR=none must rebuild the r2 geometry exactly.
Never run from here: make_tables.py (guarded). Always lock through ../run_locked.py.

## FR_VIEWS format (read by render_fr1.py, written by the integrate-fork role)

- section: dict(id, joint, kind='section', axis='x'|'y'|'z', at=<mm>, window=(u0, u1, v0, v1), caption)
  (same window convention as layout.SECTIONS in the baseline).
- motion:  dict(id, joint, kind='motion', moving=[part ids], path=[(dx, dy, dz) waypoints, last = (0, 0, 0) = final],
  context=[part ids shown solid], ghost=[part ids shown translucent] (optional), view='front'|'rear'|'left'|'right'|'top'|
  'bottom'|'iso_left_front'|'iso_right_rear'|..., caption). Removal = the path read backwards.
- closeup: dict(id, joint, kind='closeup', parts=[...], box=(x0, x1, y0, y1, z0, z1), view=..., caption)

## Progress (each role appends "## FR <role>" with done / half-done / next)

## FR keeper (fr-keeper, started 09:15; finish-by 13:15) -- WORKING NOTES, final summary appended at the end
- Design chosen (09:25): delete s_k1 + its floor boss; arm -Y end becomes a full-depth tongue (x -105..-97,
  y -29.75..-23, z 9.8..15.6) that slides -Y 3.0 into a keyed seat pocket grown from the tub right wall + floor
  (seat B(-106.85,-95.15,-32.55,-27,2.45,18.75), pocket B(-105.15,-96.85,-30,-26.9,9.65,15.75): LOCATE 0.15 in x/z,
  SLIDE 0.25 at the tip). s_k2 stays (one PT screw). New keeper_in path: (-1.2,63,0.5) (-1.2,3,0.5) (-1.2,3,0)
  (0,3,0) (0,0,0). Inline override sits right after "# --- R1 J9 end" in layout.py; registry fixes in "# --- FR keeper".
  (09:45: pocket tip gap changed to LOCATE 0.15, pocket y0 -29.9, so the seat stops the keeper before the finger
  faces (0.25) can touch the board.)
- 10:34 progress: D2_FR=none pi_keeper.stl sha256 eada966e... and tub.stl 683c74ec... = r2 (identical). D2_FR=keeper
  --part pi_keeper / --part tub (thin walls + 2 mm sweeps): both pass (out/_keeper-p1). Probe test_fr_keeper.py all
  pass. Coupons exported: out/stl/coupons-fr/coupon-fr-keeper-{seat,stub,tub,part,x1203,pi}.stl +
  out/coupons-fr-keeper-manifest.json. First full build was killed by my own `timeout 595` wrapper (rc 143, not a
  check failure); re-run 10:45 -> out/_keeper-1.
- r3 interface requests (fr-keeper -> integrate-fork):
  1. checks.clearance_zones: add 'J9 keeper tongue in tub seat' (pi_keeper vs tub, zone = PI_KEEPER['pocket']
     grown 0.5, stated FDM LOCATE 0.15) when 'pocket' in PI_KEEPER; probe today: min gap 0.15, overlap 0.
  2. FR_VIEWS motion entries from fr-keeper carry an optional `keepouts=[ids]` key (draw those KEEPOUTS boxes as
     translucent cable volumes); ignore it if render_fr1.py does not support it.
  3. FR keeper replaces the r2 "G-KEEP-1" gate with G-KEEP-1r (coupons_fr_keeper.py GATE) in the candidate.
- FINAL (10:56). DONE: keyed-seat keeper, PT body screws 7 -> 6 for this joint (s_k1 + boss deleted; UPS kit
  screws/standoffs unchanged). Joint-alone full `--fast` build with 2 mm sweeps, out/_keeper-1 (10:54:38): all 21
  categories pass, cad_release_candidate true (CAD only). D2_FR=none --part pi_keeper/tub sha256 = r2. Files:
  - layout.py: FR keeper inline block after "# --- R1 J9 end", and the "# --- FR keeper" block (CRITICAL_FEATURES
    with 7 new ids, FR_JOINTS J9_keeper_fr with 20 required ids, FR_REMOVED_FEATURES tub_keeper_boss_s_k1, 6
    FR_VIEWS, STEPS/REMOVALS/SECTIONS without s_k1);
  - printed_tub.py: _floor seat branch; printed_keeper.py: tongue branch + PRINT note;
  - test_fr_keeper.py (probe), coupons_fr_keeper.py (6 coupons, gate G-KEEP-1r), JOINT-keeper.md (verdict: recommend).
  HALF-DONE: none. NEXT (integrate-fork): interface requests 1-3 above; render the FR_VIEWS; physical G-KEEP-1r and
  G-PI-1 (port-finger approach strip) stay not run. test_keeper.py still names s_k1 (baseline harness, unused in FR).

## FR panel (fr-panel, 2026-10-05 10:25; details in JOINT-panel.md)

- DONE: concept A (straight-Y shear/seat keys key_b1/key_b2 = the old boss blocks without pilots, 1.0 lead chamfers,
  printed_panel._key_leads under FR['panel']); s_b1/s_b2 dropped from SCREWS/STEPS/REMOVALS under the toggle (base_grip
  counterbores, tub floor holes and pilots go data-driven); probes, FR_JOINTS (FR_panel_keys, FR_panel_closure),
  FR_REMOVED_FEATURES (4), FR_VIEWS (frp-sec-x91, frp-sec-z5, frp-motion-off, frp-bottom-after) in the `# --- FR panel`
  block. Concepts B (tilt-in hook) and C (detent keys) rejected with reasons (JOINT-panel.md s. 3).
- DONE: D2_FR=panel full --fast build with 2 mm sweeps `out/_panel-3`: all categories pass. D2_FR=none --part panel,
  tub, base_grip (`out/_panel-none`): sha256 equal to ../out/stl. Coupons: coupons_fr_panel.py ->
  out/stl/coupons-fr/coupon-frp-{tub-lip,panel-keys}.stl + out/coupons-fr-panel-manifest.json (gate G-FRP-1, not run).
- OPEN / interface requests (integrate-fork): make_coupons.py reads PANEL_BOSSES['boss_b1'] and SCREWS s_b1, so it fails
  under D2_FR=panel (drop the G-PANEL-1 base-edge rows / pt_boss_bottom when FR['panel']); merge FR_JOINTS into
  CRITICAL_JOINTS; render FR_VIEWS. Bottom-edge seam stiffness is a hand estimate only (0.3-0.7 mm/N): G-FRP-1.
- Not changed: lip notches (0.3 play), keeper bridge, s_r1/s_r2, J2/J3/J4, s_j. printed_tub.py and printed_grip.py
  were not edited (all tub/grip changes follow from SCREWS).

## FR hood (in progress; fr-hood role, started 09:15)
- 09:50 design chosen for study: 'yslide' = drop at +3.0 Y offset, push -3.0 Y. Right wall: 2 rigid STAPLES (hood: 2 legs +
  bridged bar) under 2 tub TABS (flat 90 deg catch) at x -45 / -125. Front (y 22) / rear (y -20) walls: one rigid 45 deg
  dovetail toe each under a tub ledge (lift reaction pushes the hood into the front-plate / housing end embrace).
  No flexures, no pins, no holes. Y lock in use: panel tongue in the J2 groove (0.25) + camera ring in the hood bore (0.25).
  Plunger channel widened 3.0 toward -Y (merges 1.6 mm with the SD slot inner layer). Implementation: layout inline
  override of HOOD_HOOKS (ids yk1..yk4, key fields) after its definition; registry in the "# --- FR hood" block.
- 09:58 progress: geometry in (layout inline + "# --- FR keeper" registry block, printed_tub.py _floor seat branch,
  printed_keeper.py tongue branch); pocket tip gap changed to LOCATE 0.15 (pocket y0 -29.9) so the seat stops the
  keeper before the finger faces (0.25) touch the board. Probe test_fr_keeper.py (D2_FR=keeper) all pass (sweeps 1 mm
  pi_in/keeper_in, removals, driver s_k2, boss, all FR_JOINTS required ids). D2_FR=none tub.stl sha256 = r2
  683c74ec... (identical). r2 pi_keeper.stl sha256 eada966e... (none-mode keeper build still to run: lock busy).
  JOINT-keeper.md drafted; coupons_fr_keeper.py written (not yet run). Next: none keeper hash, keeper --part builds
  with thin walls, coupons, joint-alone full --fast build with sweeps -> out/_keeper-1.
- 10:20 yslide BUILT and computed: out/_hood-3 (D2_FR=hood=yslide, --fast, 2 mm sweeps): all 21 categories pass
  (release_access has 0 entries: n/a for yslide). Iteration: dy 3.0 -> 2.5, tab proud 2.5 -> 2.0 (pi_in path), stack
  post x0 -10.7 -> -9.2 (cooler at the drop offset). Probe out/_hood-probe/fr-hood-motion.json (fr_hood_probe.py).
  Coupons out/stl/coupons-fr/coupon-fr-hood-*.stl (coupons_fr_hood.py). D2_FR=none hood/tub sha256 == ../out/stl.
  FR_DEFAULT hood -> 'yslide'. Next: JOINT-hood.md; screw1 geometry only if time allows.

## Main session note (10:30)
A follow-up role **fr-panel-2** (started 10:30, finish-by 12:40) studies the bottom-edge stiffness of concept A
(JOINT-panel.md s.5: 0.3-0.7 mm/N, ESTIMATE) and may replace A under FR['panel'] with a stiffer 2-screw arrangement.
integrate-fork: read "## FR panel-2" before merging; if it is still running, merge the other joints first and take the
panel files last.
- 10:50 screw1 BUILT (rough): out/_hood-s1-1 20/21 pass; removals pi_out failed only because s_h1 was not in the
  later service 'off' lists (registry omission, fixed: s_h1 added wherever the hood is off). Re-run -> out/_hood-s1-2.
  JOINT-hood.md written (sections 1-8). Interface note for fr-panel / integrate-fork: yslide's in-use Y lock is the
  panel tongue tip (PANEL_TONGUE y0 26.0) 0.20 from the hood groove floor (y 25.75) + the camera ring; keep the panel
  tongue and its -Y tip if the panel joint changes, and re-run fr_hood_probe.py on the merged fork.

## FR panel-2 (fr-panel-2, started 10:30; finish-by 12:40) -- WORKING NOTES
- 10:45 study done (ESTIMATE, one consistent grillage plate model, scratchpad fp2/grill.py + opts.py; numbers in
  JOINT-panel.md "r3 follow-up: bottom-edge stiffness"). Decision: concept A + an integral inner-face STIFFENING
  FRAME (bottom chord through both keys, diagonal tie key_b2 -> post_r, rear upright, front upright + link to post_f).
  Seam between the keys 0.24 -> 0.06 mm/N; worst bottom-edge point (front corner) 0.93 -> 0.47 (r2: 0.67); EVF cap
  0.085 -> 0.046 (r2 0.081). Rejected: rear-bottom screw from below (EVF cap 0.22-0.47, 2 drive directions), s_r1 + s_b2
  (EVF cap 0.73, base access). Same 2 PT screws, same -Y motion, same tool, no new part.
- 10:46 geometry in: layout `# --- FR panel` block (PANEL_FRAME after PANEL_KEY; 6 probes panel_frame_*, FR_JOINTS
  FR_panel_frame, panel_off note, FR_VIEWS frp2-sec-y29 / frp2-sec-x125 / frp2-motion-on); printed_panel._frame()
  fused after _key_leads under FR['panel']. printed_tub.py / printed_grip.py NOT touched.
- next: --part panel build (lock was busy 10:47-10:51), full D2_FR=panel --fast 2 mm sweeps -> out/_panel2-<n>,
  D2_FR=none --part panel sha256 vs ../out/stl/panel.stl, coupons_fr_panel.py check.
- 11:42 DONE: D2_FR=panel full --fast build, 2 mm sweeps -> out/_panel2-2: all 21 categories pass (critical_features
  109 = 103 pass + named exceptions; 6 new frame probes 4.4/4.4/3.0/3.0/3.0/3.0). 11:49 DONE: D2_FR=none --part panel
  (out/_panel2-none) sha256 db433e49... = ../out/stl/panel.stl. JOINT-panel.md s. 11 written (method, table,
  sensitivity, rejections, geometry, checks, decision). coupons_fr_panel.py: descriptions + GATE (c) updated.
- next: re-export coupons (D2_FR=panel coupons_fr_panel.py; lock busy at 11:53), then optional D2_FR=all build.
- 12:05 DONE. Final runs: yslide out/_hood-4 (all 21 categories pass, cad_release_candidate True); screw1
  out/_hood-s1-2 (all 21 pass after the s_h1 off-list fix); D2_FR=none hood/tub sha256 == ../out/stl (re-checked 12:03).
  JOINT-hood.md complete (verdict: recommend yslide; screw1 user choice; pins fallback). FR_DEFAULT hood = 'yslide'.
  Half-done / next (integrate-fork): render the FR_VIEWS (hood-yslide-*, hood-screw1-*); re-run fr_hood_probe.py on
  the merged D2_FR=all fork (Y lock relies on the panel tongue tip y 26.0, 0.20); release_access has 0 entries for
  yslide/screw1 (n/a, not a pass) - the corrected r3 checks may report it as not-run; G-YSLIDE-1 to the gate list.
- 11:57 DONE: coupons re-exported (D2_FR=panel coupons_fr_panel.py): out/stl/coupons-fr/coupon-frp-{tub-lip,
  panel-keys}.stl + out/coupons-fr-panel-manifest.json; the panel-keys coupon now carries the chord web between the keys
  and the diagonal-tie stub (cut from the real A2 panel). Gate G-FRP-1 text gains (c) (front corner, EVF cap, frame roots).
- r3 interface notes (fr-panel-2 -> integrate-fork): (1) FR_JOINTS += FR_panel_frame (parts ['panel']; if
  CRITICAL_JOINTS needs >= 2 parts, add 'tub'); (2) 3 new FR_VIEWS (frp2-sec-y29 section axis y at 28.7, window in
  x/z; frp2-sec-x125; frp2-motion-on); (3) the make_coupons.py PANEL_BOSSES['boss_b1'] issue from fr-panel still
  stands; (4) fr-hood's yslide Y lock relies on PANEL_TONGUE y0 26.0: untouched by A2.

## FR integrate-fork (integrate-fork role, started 12:05; finish-by 15:00) -- WORKING NOTES
- 12:06 plan: (1) backups in _premerge/; copy ../build_d2.py ../checks.py verbatim (baseline now location-independent);
  git merge-file layout.py; fold FR_JOINTS/FR_REMOVED_FEATURES into CRITICAL_JOINTS; (2) builds _none, all, per joint;
  (3) coupons + watertight; (4) render_fr1.py; (5) fr1_counts.py; (6) CANDIDATE.md. Progress lines follow.
- 12:20 merge DONE: ../build_d2.py + ../checks.py copied verbatim (fork copies in _premerge/); layout.py = git merge-file (clean, 0 conflicts; fork copy _premerge/layout.fork.py); new '# --- FR integrate' block after FR hood end folds FR_JOINTS into CRITICAL_JOINTS (FR_JOINT_SUPERSEDES) and, under FR panel, also removes the r3 twins panel_boss_b2_cap + base_sb2_head_floor. D2_FR=none registry (features, joints, SCREWS, STEPS, REMOVALS, EXPECT_OUTSIDE) == baseline ../layout.py. layout self-check 0 failed for none/all/panel/keeper/hood=yslide/hood=screw1; no missing required ids.
- 12:21 DONE: after the r3-checks merge, D2_FR=panel full --fast 2 mm sweeps -> out/_panel2-3: all 21 categories pass
  (critical_features 128 = 119 pass + named exceptions; joints FR_panel_keys / _closure / _frame pass). A D2_FR=all build
  started mid-merge (out/_panel2-all) failed only tub_evf_groove_wall_bot_px (r3 missing-ray rule) and the
  not-yet-merged CRITICAL_JOINTS registry: not panel issues; integrate-fork owns the merged all build.
- FINAL (fr-panel-2): A2 (A + stiffening frame) replaces A under FR['panel']; files changed: layout.py (FR panel block
  only), printed_panel.py (_frame + one call), coupons_fr_panel.py (text + GATE (c)), JOINT-panel.md (header + s. 11),
  NOTES.md. printed_tub.py / printed_grip.py untouched. Half-done: none. Next (integrate-fork / user): render the 3
  new FR_VIEWS; G-FRP-1 physical gate (not run).
- 12:27 build (a) DONE: D2_FR=none --fast --sweep-step 2 -> out/_none (built 12:26:42): 21/21 categories pass, critical_features 118 (109 pass, 9 info), cad_release_candidate True, variant 'FR1 hood=pins,keeper=False,panel=False'; 11/11 production STLs sha256 == ../out/stl (r2). Helper: _cmp_build.py <dir>. fr1_counts.py written+run (out/fr1-counts.json/.md). render_fr1.py written (not yet run).
- 12:34 build (b) DONE: D2_FR=all full build (renders, STEP, --sweep-step 1.0) -> out/ (built 12:33:44): 21/21 categories pass, critical_features 136 (127 pass, 9 info: 3 G-CAP-1 gated + 6 named exceptions), 14 CRITICAL_JOINTS pass, cad_release_candidate True; release_access 0 rows (n/a: no release under yslide; summarised as 'pass' by the copied checks - report as n/a). Changed STLs vs r2: base_grip, hood, panel, pi_keeper, tub; other 6 identical. Next: per-joint builds.
- 12:46 make_coupons.py (fork) patched: under FR panel / hood=yslide the rows cutting removed features are dropped (FR_DROPPED in manifest); D2_FR=none unchanged. Build (c) panel DONE: out/_int-panel (12:45:56) 21/21 pass, critical_features 128 (119 pass, 9 info); changed STLs base_grip/panel/tub.
- 12:56 build (c) keeper DONE: out/_int-keeper (12:56:28) 21/21 pass, critical_features 124 (115 pass, 9 info); changed STLs pi_keeper/tub.

## Main session note (13:08): baseline checks changed after the fork merge
fix-baseline (12:25-13:05) changed the baseline `checks.py`, `build_d2.py`, `test_r3_regressions.py` and the layout R3
block (`REQUIRED_JOINT_IDS`, joint-coverage rules V-L1/V-L2/V-M3, empty-category fail V-M4, evidence `rejected` /
unassigned records, step/parts hashing). The fork copies predate that. integrate-fork / fix-candidate: re-copy the
baseline checks.py and build_d2.py, merge the R3-block additions (REQUIRED_JOINT_IDS; fork joints that replace a baseline
joint must list it in `replaces`), and re-run the D2_FR=all and D2_FR=none builds before the final CANDIDATE.md numbers.
- 13:08 build (c) hood=yslide DONE: out/_int-hood-yslide (13:08:03) 21/21 pass (release_access 0 rows = n/a), critical_features 120 (111 pass, 9 info); changed hood/tub. _study42.py: STUDY s4.2 items 1-4,7 hold in _none/_int-panel/all (s_j driver/boss/interference pass, J4 clearances 0.25, base_on pass, J4 probe values identical); fr1_counts J4 independent lock = s_j in every state.
- 13:16 build (c) hood=screw1 DONE: out/_int-hood-screw1 (13:16:04) 21/21 pass, critical_features 120 (111 pass, 9 info); changed hood/tub. Next: render_fr1.py, coupons, fr_hood_probe on all.
- 13:36 render_fr1.py run x2 (2nd with closeup readability: translucent purchased parts/hood, orange cut faces, legend): 20 FR views + 13 before views, out/renders/fr1-*.png + fr1-index.md. fr1_validation.py -> out/fr1-validation.md. run_fr1_coupons.py written (coupons + make_coupons + fr_hood_probe on all + trimesh).
- 13:52 RE-MERGE after fix-baseline (main session note 13:08): fork checks.py/build_d2.py re-copied verbatim from the baseline (12:17/12:19 versions; previous fork copies in _premerge/*.r3a.py); fork layout R3 block replaced by the baseline R3 block (adds REQUIRED_JOINT_IDS; layout outside R3 identical to _base); FR integrate fold now sets replaces=[superseded baseline joint id] + the FR joint's replaces. D2_FR=none registry == baseline again; layout self-check 0 failed in all 6 states. Earlier build numbers (12:26-13:16) are with the pre-fix r3 checks; rebuilding all, none, then per joint.
- 14:15 (integrate-fork re-spawn, main-session continuation 14:12) the 14:04:50 D2_FR=all build (re-merged checks) gave 20/21: release_access FAIL = V-M4 empty category (yslide has no RELEASE_ACCESS; screw1 likewise). Fix (fork checks.py only, documented): `_no_release_row` - when RELEASE_ACCESS is empty, ONE computed row 'no_release_required' asserts no release holes, no 0 deg flexing catch (0 deg must be a rigid staple), hood_off tool names no pin and releases only 45 deg cam-out hooks, and the built tub right wall is solid (point-in-solid) at the old pin-hole centres. Baseline path (RELEASE_ACCESS non-empty) unchanged. Rule V-M4 untouched. Next: quick test, then rebuild all, none.
- 14:14 quick test _test_norelease.py (tub only): all -> pass; hood=screw1 -> pass; none (forced) -> fail with all 5 reasons (discriminating). Starting D2_FR=all full build (1 mm, renders, STEP) -> out/, log out/_build-all-1414.log (~14 min; foreground will time out at 10 min and keep running).
- 14:26 while the all build runs: fr1_counts.py re-run with the re-merged layout -> identical to 13:45 (0 differences; old copy out/_fr1-counts-1345.json); fr1_validation.py gains a 'checks version' column (current / re-merged-before-no-release-row / PRE-MERGE) and the release_access error text; out/_none (12:26, pre-merge) renamed out/_none-premerge; CANDIDATE.md s0/s8/s11 text updated for the no-release row; helper _splice_validation.py copies the validation table into CANDIDATE s8. Renders (13:36) are geometry-only; the 13:52 re-merge changed only the layout R3 check block, so the FR views are unaffected.
- 14:32 builds DONE with current checks: all full (out/, 14:25:36) 21/21, critical 126 pass / 10 info / 0 fail, joints 13/14 pass + J6_cap_grip info (G-CAP-1 gated, same as baseline ../out), release_access 1/1 no_release_required pass, STLs identical to the 12:33 all build; none --fast 2 mm (out/_none, 14:31:32) 21/21, 11/11 STLs == r2, release_access pin_hk1/pin_hk2 pass. Logs out/_build-*.log. Next: run_fr1_coupons.py (log out/_coupons-1432.log).
- 14:40 coupons DONE (run_fr1_coupons.py 14:32-14:39, final fork): 5 jobs rc 0, 24 coupon STLs all watertight; hood probe on all unchanged (lift 0.101, -Y 0.15, +X/-X 0.147). Next: per-joint rebuild hood=yslide -> out/_int-hood-yslide-r3m (current checks), then screw1 if time.
- 14:55 per-joint rebuilds with current checks: hood=yslide (out/_int-hood-yslide-r3m, 14:47:11) and hood=screw1 (out/_int-hood-screw1-r3m, 14:54:43) both 21/21, release_access no_release_required pass, STL hashes equal to the pre-merge builds. panel / keeper per-joint builds NOT rebuilt (pre-merge checks; covered by the current-checks all build). fr1_validation.py + _splice_validation.py -> CANDIDATE s8 refreshed; s9 coupon line refreshed.
- FINAL (integrate-fork, 14:56): done = merge (r3 checks re-copied; fork checks.py = baseline + _no_release_row), builds all (full 1 mm) / none (11 STLs == r2) / yslide / screw1 with current checks, coupons (24 watertight), counts (unchanged), renders (geometry unchanged), CANDIDATE.md. Half-done: none. Next (main session / user): rebuild D2_FR=panel and keeper with current checks if wanted; port _no_release_row to the baseline checks.py only if FR hood is adopted; user picks joint options (CANDIDATE s10). Nothing committed, printed or measured.
## verify-candidate (adversarial) started 14:55; read-only; scratch in session scratchpad
- 15:07 verify: built D2_FR=panel,keeper,hood=screw1 --fast into out/_verify-candidate-pks1: exit 0, see checks.json
- 15:11 verify: checks done (claims, suppression diff, none identity, combo build, forced no-release, probes, counts); writing findings
- 15:11 verify-candidate FINAL: no high findings; 4 medium (screw1 unreported 0.98 mm thin spot; s_b1/s_b2 removal drops 2 in-use base X restraints, not stated; grillage scripts only in temp scratchpad; microSD slot change missing from CANDIDATE), 7 low. Own build out/_verify-candidate-pks1 (panel,keeper,hood=screw1) 21/21 pass. Findings returned to orchestrator.

## FR fix-candidate (started 15:13; finish-by 16:45) -- WORKING NOTES
- 15:13 plan: M1 thin spot (investigate screw1 tub at (-12.95,31.85,20.75); fix geometry or structural probe; validation 'unresolved info' column), M2/M4/L1/L3/L7 doc fixes, M3 copy grillage scripts into estimates/, L2 s8 row for _verify-candidate-pks1, L4 --force in _test_norelease.py, L5 caption + re-render, L6 TOOL_WORDS + fr1_counts. Per-finding table appended at the end.
- 15:19 done: VC-M3 estimates/ (opts2 re-run reproduces s11.2), VC-L4 _test_norelease.py --force (log out/_test_norelease-force.log), VC-L5 caption computed in layout FR_VIEWS (1.75). M1 = baseline rib_l gusset tip (identical in r2), dispute FR attribution. Starting D2_FR=all full rebuild (layout hash changed) -> out/, log out/_build-all-1519.log; previous checks/receipt in out/_prev-all-142536/
- 15:38 all full rebuild (15:26:25) 21/21, critical 126/10/0, 11 STLs identical to 14:25 build (only layout.py source hash + STEP timestamps differ); render_fr1 --states=all and none re-run (x-45 caption 1.75); none rebuild out/_none (15:37:51) 21/21, 11/11 STLs == r2. Next: panel,keeper,hood=screw1 -> out/_int-pks1
- 15:51 out/_int-pks1 (15:44:56) 21/21 126/10/0; out/_int-panel-r3m (15:50:30) 21/21 118/10/0. Next keeper -> out/_int-keeper-r3m, then fr1_validation unresolved column + counts + docs. yslide/screw1 -r3m builds NOT rebuilt (layout.py differs only by the VC-L5 caption line).
- 15:59 done: fr1_validation.py (unresolved-info + layout.py columns, +3 builds), fr1_counts.py hacksaw (rerun: only tool_categories change), _thin_spot_rib_l.py + out/_thin-spot-rib_l.txt. Next: CANDIDATE/STUDY/JOINT-hood doc edits, splice s8, final table.
- 16:02 docs done: CANDIDATE s2 (L7 numbers, M2 second cost, M3 estimates link), s4 (M4 microSD, L1 inference, M1 note), s5 (M2), s8 (table + provenance bullet + L4), s9 gates (M2, M4, L1), s10 (L2, M2, M4); STUDY s0/s2/s4/s5 (M2); JOINT-hood s2 (L1); JOINT-panel s11.1 (M3). Next: baseline NOTES interface request for rib_l, final table.
- 16:08 VC-L1: fr_hood_probe.py gains a 'panel off' set; D2_FR=all -> out/_hood-probe-paneloff: +Y stop 0.243, lift at that stop 0.101 (camera fixed). Next: doc text for L1, final table.

## FR fix-candidate (fix-candidate role, 15:13-16:45): per-finding table
Nothing printed, sliced, bought, measured or powered; all results are computed CAD/numpy; no threshold, check or
exception changed; baseline release outputs untouched (only read). Builds use the shared lock.

| id | verdict | change | evidence |
|---|---|---|---|
| VC-M1 | partly disputed, kept visible | Not an FR defect: the spot is the 45 deg tip of the **baseline** tub gusset `rib_l` (0.3 land at x -13), identical in r2 and every FR state; the seeded 1500-sample thin_wall screen only lands on it in the screw1 tub mesh. No exception, no probe added in the fork (rib_l is baseline; the none registry must equal the baseline). fr1_validation.py gains an 'unresolved info rows' column (from results.unclassified_thin_spots) and a 'layout.py' column; CANDIDATE s4 + s8 report the spot; baseline owner asked in ../NOTES.md 'r3 interface requests (addendum)'. | `_thin_spot_rib_l.py` -> `out/_thin-spot-rib_l.txt` (min 0.598 at (-13, 32.2, 22.3) in ../out/stl/tub.stl, none, all, yslide, screw1); `out/fr1-validation.md` |
| VC-M2 | accepted | STUDY s0/s2/s4.1/s5 and CANDIDATE s2 ('second cost'), s5, s9 (G-J4-1 row), s10 now state that FR panel removes the in-use base clamp and X restraint of s_b1/s_b2, leaving s_j as the only in-use unlock-direction restraint; G-J4-1 gains an unlock-direction pull + EVF-first drop record with FR panel fitted. | text only (not a computed load case) |
| VC-M3 | accepted | grill.py, opts.py, opts2.py (+ sens.py, depth.py, depth.pkl, ribchk.py, show.py) copied byte-for-byte into `estimates/` with README; opts2.py re-run. JOINT-panel s11.1 and CANDIDATE s2 cite `estimates/`. | `estimates/opts2-output.txt` reproduces every number of JOINT-panel s11.2 (A2 = option '1e') |
| VC-M4 | accepted | CANDIDATE s4 side changes + trade-off + s10: widened channel opens the inner 1.2 mm of the microSD slot over 1.1 mm (sd_in sweep = geometry only); G-YSLIDE-1 gains 10 microSD insert/eject cycles, no catching. | JOINT-hood s3 line 60 |
| VC-L1 | accepted (computed, with a stated limit) | fr_hood_probe.py gains a 'panel off (tub, gs_camera, eyepiece, microsd)' set and the lift test at that stop; CANDIDATE s4 and JOINT-hood s2 cite it and state that gs_camera is a fixed obstacle (its own Y hold by the tub pins with the panel off is not computed); G-YSLIDE-1 gains a panel-off +Y push. | `out/_hood-probe-paneloff/fr-hood-motion.json`: +Y stop 0.243 by gs_camera, lift at stop 0.101 (keys engaged) |
| VC-L2 | accepted | built D2_FR=panel,keeper,hood=screw1 into `out/_int-pks1` (15:44:56): 21/21, critical 126/10/0; added to fr1_validation BUILDS and CANDIDATE s8/s10. | `out/_int-pks1/checks.json`, `out/_build-pks1-1538.log` |
| VC-L3 | accepted (rebuilt) | rebuilt panel and keeper (and, after the VC-L5 layout edit, hood yslide-r3m 16:21:14 and screw1-r3m 16:28:05, both 21/21, STLs unchanged) with the current checks/layout: `out/_int-panel-r3m` (15:50:30, 21/21, 118/10/0) and `out/_int-keeper-r3m` (15:57:44, 21/21, 114/10/0); STLs equal the earlier per-joint ones; s8 provenance bullet reworded ('pre-merge checks and the layout.py before the R3 re-sync'). | `out/fr1-validation.md` |
| VC-L4 | accepted (verifier's reading of the conditional was inverted, the defect was real) | the saved script ran check_release_access when RELEASE_ACCESS was EMPTY and the no-release row when it was not (inverted vs build_d2); now default = build logic, plus `--force` always calls `_no_release_row`. | `out/_test_norelease-force.log`: none forced -> fail with all 5 reasons; all / hood=screw1 -> pass |
| VC-L5 | accepted | FR_VIEWS caption computed from HOOD_YSLIDE (tab proud - staple wall_gap = 1.75, play 0.1); render_fr1 --states=all and --states=none re-run; D2_FR=all full build re-run (15:26:25) so the receipt matches the edited layout.py (11 STLs byte-identical to 14:25). | `out/renders/fr1-hood-yslide-x-45.png` (title 'overlap 1.75 (Y)'), `out/renders/fr1-index.md` |
| VC-L6 | accepted | TOOL_WORDS gains ('junior hacksaw + file', r'hacksaw|\bfile\b'); fr1_counts.py re-run: only tool_categories change (hacksaw now listed in every state; deltas unchanged). | `out/fr1-counts.json/.md` (old copy `out/_prev-all-142536/`) |
| VC-L7 | accepted | CANDIDATE s2 reworded: seam 0.001 (r2) -> 0.057 (A2); front corner 0.67 (r2) -> 0.47 (A2); all ESTIMATE. | `estimates/opts2-output.txt` |
- 16:21 yslide-r3m rebuilt (16:21:14) 21/21 110/10/0 with current layout. Starting screw1-r3m rebuild.
- FINAL (fix-candidate, 16:29): all 11 findings acted on (table above): 9 accepted and fixed, VC-M1 kept visible as an unresolved info row and attributed to baseline rib_l (interface request in ../NOTES.md), VC-L4 fixed (script logic was inverted). Builds with current sources: out/ (all, full 1 mm, 15:26:25), _none (15:37:51, 11/11 == r2), _int-pks1, _int-panel-r3m, _int-keeper-r3m, _int-hood-yslide-r3m, _int-hood-screw1-r3m: all 21/21. Renders re-run (all + none states). fr1-counts + fr1-validation regenerated and spliced into CANDIDATE s7/s8. Half-done: none. Next (baseline owner / user): rib_l thin-tip decision; user joint choices (CANDIDATE s10); all hardware gates NOT RUN. Nothing committed.

## r5 note (2026-10-06, baseline r5; note only, no fr1 code changed)
The baseline adopted the r5 J7-R float (`../R5-BRIEF.md`, `../RECTIFICATION.md` "r5"): a printed `lens_collar` on 3 M3
screws in tub inserts (s_c1..s_c3) + a pinch s_c4, the camera hanging on the lens, the hood turret and camera pins
deleted, a hood camera roll fin, the panel keeper moved to x -30.67..-27.34, and the real GS camera model. FR1 still
carries the r4 baseline geometry. On adoption: (1) the `hood=yslide` hood must slide +Y with the lens collar already
off (its 4 feet pass through the hood plate: `collar_off` first, so the yslide removal order becomes panel, lens,
camera, collar, then the hood); (2) the yslide hood must carry the r5 roll fin + webs and the 4 dia 8.6 foot holes (no
turret); (3) the FR panel keeps the r5 keeper position; (4) re-run the r5 checks (`j7_float`, `lens_support`,
`lens_clamp`, `inserts`) and the sweeps on every FR state. FR1 builds are not re-run for r5.
