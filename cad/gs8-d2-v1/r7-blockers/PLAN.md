# PLAN: r7 blocker rectification, integration plan

Revision label: **GS8 D2 r7-20261009 (r6-20261008 + blocker review 2026-10-08 fixes)**

Status: integration plan, 2026-10-08 23:37 - 2026-10-09 01:10 MPST. Inputs: SPEC-C1 .. SPEC-C6 (final, reviewed) and
`guide/BLOCKERS-2026-10-08.md`. Each spec now ends with a "Plan edits" section; inline markers `[Plan edit Pn-k]` sit
at the places that changed. Where a spec and this plan differ, this plan wins. Nothing in the repo was changed except
the files in `r7-blockers/`. Hard deadline: 07:30 MPST 2026-10-09 (cease work).

Paths used below: `R` = `C:\Users\Pre-Installed User\Claude\Projects\digital8mm` (repo root, the only working copy);
`PY` = `C:\Users\Pre-Installed User\Claude\Projects\8mm\.venv-cad\Scripts\python.exe`; `SCR` = the session scratchpad
`...\b0b4646a-...\scratchpad`. Every CAD job goes through `cad/gs8-d2-v1/run_locked.py`, one at a time. Never delete
`.cad.lock`. No commits, no pushes.

## 1. Clusters, severities, owners

| cluster | items | severity | designer est. | agent wall-clock est. | can be dropped? |
|---|---|---|---|---|---|
| C1 | BX-1, C-16, BX-7, BX-9 | BLOCKER + 2 minor | 9.75 h | 75 min (with the shared infrastructure) | never |
| C5 | BX-5, BX-13, BX-14 | MAJOR + 2 minor | 6.25 h | 30 min | never (BX-5); rest_pose rows last |
| C2 | BX-2, BX-10 | MAJOR + minor | 8.5 h | 55 min | never (BX-2); header_housings check last |
| C3 | BX-3, BX-11, BX-16 | MAJOR + 2 minor | 7.1 h | 45 min | never (BX-3) |
| C4 | BX-4, BX-8, BX-15 | MAJOR + 2 minor | 9.5 h | 55 + 15 + 15 min | BX-4 never; BX-15, BX-8 yes |
| C6 | BX-6, BX-12, BX-17 | 3 minor | 9.5 h | 20 + 25 + 35 min | yes (whole cluster) |

The designer estimates add up to 50.6 h. That cannot fit in the 6 h 15 min between 01:15 and 07:30, even at agent
speed. Section 8 gives the schedule, the cut-off clock times and the drop order. The order below lands the BLOCKER
first, then the four MAJORs cheapest first, then the minors.

## 2. One design for connectors and leads (C1 + C2 + C3 merged)

The three specs each invented a "something fixed to a moving part" mechanism and a reach check. They become one.

**Data (layout.py), one source each:**
- `PLUGS` (C1): one entry per (cable, end) of `CABLE_ENDS` (20). It says what the connector is, where (box), whether
  it is rigid, and when it is mated (`('bench', s)`, `('before'|'after', insertion)`); optional in-situ `path`,
  `head`, `stroke`. Changed by the merge: `p_pig_pads` has `box=None, rigid=False`; `p_qt_enc` uses C2's
  `ko_qt_plug`.
- `MATE_POSES` (C2): one row per lead end mated in a pose other than its final pose. Each row names `plug=<PLUGS id>`
  (or `inline_of=<cable>` for the fps PH junction). Rows: `qt_enc`, `fps_ph`, `fpc_cam`, `oled_flex` (info) from C2;
  `usb_5v_evf` (C1, P1-4); `xt30` (C3, P3-1, `reach='pigtail'`). No `hdmi_evf` row (in-situ mate). The `mated` key
  and C2's INSERTIONS `mated` field are dropped.
- `ACCESS` + `FINGERTIP_MM` (C1): explicit hand and tool corridors for in-situ mates and service. `HAND_ENVELOPES`
  (C2) are generated pinch boxes at mating poses. Put the two next to each other under one "hands" comment.
- INSERTIONS fields: `riders` (C3, taped lead lanes that move with the part), `stowed` (C2), `hold` (C4).
  `KEEPOUT_KIND` (C1). `INSERTION_EXEMPT` (C6). `PIGTAIL` (C3). `reach_margin` is a checks.py helper.

**Checks, one routine each:**
- `check_sweeps` / `check_removals` get ONE carried-box routine. Carried boxes per insertion = rigid PLUGS boxes
  mated before it whose end moves (C1), plus `riders` (C3). Contact classes: kind 'plug' is hard against solids and
  'plug' keep-outs and soft (<= `CARRY_SOFT_MM` 1.0) against 'cable' keep-outs (C1); kind 'rider' is hard against
  everything (C3). A carried box ignores its own cable's route, lane and stow boxes and the end part. After its
  insertion, every carried box is a final-pose obstacle for later insertions of the same step (C3's rule,
  generalized). The rigid plug at the fixed end of a cable whose other end moves stays a hard obstacle (C1). The
  `stowed` boxes are obstacles from their waypoint, and stow boxes join `active_ko` (C2). Header housings are
  obstacles from step 5 (C2). The insertion-coverage row (C6) goes in the same function. Row fields: `carried`,
  `soft_contacts`, `fixed_end_obstacles`, `stowed`, `riders`.
- `mate_reach` (C2) is the only reach check. Margin: `reach_margin(L, length)` = max(MATE_MARGIN 10,
  ROUTE_ALLOWANCE[0], ROUTE_ALLOWANCE[1] x length), shared with `lead_access`. With ROUTE_ALLOWANCE (10.0, 0.10) this
  equals C3's allowance(L), so nothing is weakened. For the pigtail, the slack comes from C3's
  `_pigtail_face_out(L, pad)`, the same helper as `lead_access/pigtail_xt30_mouth`: one length model, one number.
- `mate_paths` (C1) keeps `plug_in`, `access` and `coverage`, and loses its `reach` kind. Coverage gains the general
  reach rule (P1-5): for every insertion J and every cable with exactly one end E moved by J, if the plug at E and
  the plug or inline junction at the other end are both mated before J, a MATE_POSES row for (cable, J) must exist.
  Rows whose both ends move are info. That rule is what would have caught BX-2 and BX-3 as a class. It lands in S3
  (with C2).
- `lead_access` (C3) keeps the pigtail-specific rows: mouth, pad range, store, lanes, run window, wrap clear.
  `cable_stow` (C2) covers qt and fps_lead. The pigtail has no `stow` key, because `pigtail_store` is the stricter
  check. The fpc info row points to C4's fold row.

## 3. Conflict register and resolutions

| # | conflict / dependency | resolution | spec edits |
|---|---|---|---|
| X-1 | `ko_qt_plug` defined twice with different boxes (C1: x -82.65..-74.65, z 53.5..60.5; C2: x -80.0..-75.7, z 51..61) | C2's box (owner of the QT lead, probed with the panel sweep and against COTS); C1 keeps KEEPOUT_KIND 'plug'; C1's planted test still holds (about 9.6 mm3 hit as plug, 0.8 soft as cable) | C1 P1-1 (inline), C2 P2-2 |
| X-2 | three carried-box mechanisms: C1 PLUGS carried, C2 INSERTIONS `mated`, C3 `riders` | one routine (s2); C2 `mated` dropped; C3 riders kept for taped lanes; `p_pig_pads` has no box, so ko_pig_wrap is swept once | C1 P1-2/P1-3, C2 P2-1, C3 P3-3 |
| X-3 | three reach checks: C1 `mate_paths/reach`, C2 `mate_reach`, C3 `lead_access` rows 1-2 + xt30 MATE_POSES row | `mate_reach` is the only reach function; C1's reach kind is removed (rows become `usb_5v_evf`, `fpc_cam`); the xt30 row uses the PIGTAIL model; one margin helper | C1 P1-4, C2 P2-4/P2-5, C3 P3-1/P3-2 |
| X-4 | C3 kept rows 1-2 out of mate_reach because of "C2's flat 10 mm margin" | stale: C2's final margin is max(10, 10, 0.1 L) = C3's allowance max(10, 0.1 L); rows 1-2 stay for the pad range and required_len, sharing the helper | C3 P3-2 |
| X-5 | C1 now mates the EVF 5 V PH junction outside the body before the slide; C2 assumed an in-situ mate ("no row needed") | new inline MATE_POSES row `usb_5v_evf` (C1-owned, pigtail credit 0 until MP-EVF), disp (0, 60, 0) with a new (0, 60, 0) start waypoint on evf_pair_in (at 45 the junction would be 13.8 beyond the opening, < 15); hand/out_of rows 'info' with gate MP-EVF | C1 P1-4, C2 P2-4 |
| X-6 | step-8 action string edited by C2 (panel), C4 (lens), C5 (screw pose, knobs) | merged text in s4, fragments tagged by owner | C2 P2-3, C4 P4-4, C5 P5-1 |
| X-7 | C2 "keep the body upright from here on" vs C5 hood-down pose for the panel screws | upright until the panel is fully home; after that the fold is closed in by the panel face (as in use), so the hood-down pose is fine | C2 P2-3 (inline), C5 P5-1 |
| X-8 | step 4 edited by C2 (header) and C3 (run lead, XT30); step 6 by C1 (replace) and C5 (append); step 10 by C3 and C4 | sentence-level merges in s4 | C3 P3-5, C1 P1-8 |
| X-9 | tool numbers: C1 pliers "next free", C4 fold card "15", C5 paper "next free", C6 comb "9" | fixed: 15 pliers (C1), 16 paper strips (C5), 17 inspection mirror, optional (C1), 18 FPC fold card (C4); 9 stays the hood release tool (comb if C6c lands) | all specs' Plan edits |
| X-10 | C4 adds a BOM row for the printed fold card; C6 adds none for the comb; tool 14 (gauge) has none | no BOM rows for printed tools; tool rows point to PRINT-GUIDE s3 | C4 P4-1 |
| X-11 | C1 and C6 said "edit bom.csv"; bom.csv and BOM.md are generated by make_bom.py `LINES` | every BOM edit goes into make_bom.py LINES (D2-24, D2-24B, D2-25, D2-26, D2-45, D2-46, D2-46R, D2-48, D2-50, D2-71, D2-77) | C1 P1-8, C2 P2-6, C3 P3-5, C6 P6-5 |
| X-12 | release_comb in printed_hood.py (C6) vs new printed_tools.py and export helper (C4) | both tools in printed_tools.py; one `export_tools()`; `TOOL_PREREQS = {'fpc_fold_card': (), 'release_comb': ('G-MP-REL',)}`; printed_tools.py becomes a receipt source | C4 P4-2, C6 P6-2 |
| X-13 | check_driver edited by C4 (`held`) and C6 (bit-length family) | family loop outer, held inside; if C6b is dropped, held runs on the r6 member | C4 P4-3, C6 P6-4b |
| X-14 | C6 INSERTION_EXEMPT lists foam_pad and the knobs, which C1 and C5 give INSERTIONS entries | exempt = {tub, eyecup}; a stale exemption fails | C6 P6-3 (inline), C5 P5-3 |
| X-15 | stale references: C3 "build together with C1's rail cut", C6 "C1 edits printed_tub.py", C6 "C4-A tools 15/16", C6 hood "roll fin" | void; only C3 changes the tub | C3 P3-4 (inline), C6 P6-4 (inline) |
| X-16 | STL/STEP "unchanged" claims per cluster contradict each other (C1/C5 "no STL hash changes"; C3 tub; C4 hood, gauge; C6 hood; C2 pi5 COTS solid) | the expected-change list in s7 replaces every per-cluster claim | C1 P1-7 |
| X-17 | category count: C1 "29", C2 "31", C3 "29", C6 "29th" | 28 + 8 = **36** (mate_paths, mate_reach, cable_stow, header_housings, lead_access, roll_catch, handling, plunger_capture); tests take the count from the build summary | all |
| X-18 | `summarize` rejects unknown row statuses; C1's 'lever' state, C3/C5/C6 info rows | 'lever' is a pass row with `push_method`; every new category is info_neutral | C1 P1-6 and the others |
| X-19 | guide TIPS['3b'] edited by C3 (BX-16) and C6 (BX-12 strap line); page 8b by C2 (QT) and C5 (knobs) | one docs pass per page, after the code lands | C3 P3-5, C6 P6-5 |
| X-20 | geometry neighbours checked: C2 stow vs C1 ACCESS / ko_5v_end / tuck corridor (x <= -130 vs >= -108: apart); C3 floor-hole extension vs C1/C4/C6 (plain floor, nothing above); C4 tines vs C6 hood lead-in (x -14.5..-8.2 vs -1.3..-0.5); C5 hood-down block vs knobs (4.0 clear); C2 hand box vs C5 knobs (opposite faces) | no clash; the trial builds T1/T2 re-check them as meshes | - |
| X-21 | roll_catch scan (C4) and the driver family (C6) add build time; the release runs three full builds | measure in trial build T1/T2; roll_catch budget about 3 min (P4-5); if the Kowa build passes 13 min, drop C6b before the release | C4 P4-5, C6 P6-6 |
| X-22 | integration box scan (layout boxes): C1 ACCESS boxes overlap `ko_hdmi_coil` (hand 2196, push 792, +X jaw 141 mm3) and the `switch_1824` COTS box; C4 tines and flanges overlap the gs_camera COTS *box* (68 / 83 mm3, they straddle the lock tab inside its envelope); `ko_fpc_stiff` overlaps the gs_camera box (149, inside ko_fpc_cam by design) | ACCESS rows get `ignore=['ko_hdmi_coil', 'ko_hdmi_evf']` with the sequence reason (coil laid after the mate, uncoiled first in service) and take their present set from the moment (panel off); S5 confirms that no check compares printed parts with the gs_camera bbox (j7_float/roll_catch use the camera solids); if one does, it must switch to the solid, not a widened tolerance | C1 P1-9 |

## 4. Merged texts (STEPS strings, hand-written ASSEMBLY rows, tool table)

Owner tags `[C2]` etc. mark fragments; if a cluster is dropped, its fragment keeps the r6 wording. The code step that
lands a cluster writes its fragments into `layout.STEPS`; make_tables regenerates the ASSEMBLY/DESIGN step tables only
in the release sequence (code steps never run make_tables).

**Step 4 action** (replaces the first two sentences and the header sentences; the stack and keeper middle is kept):
"[C3] Check that the run lead is still taped flat in its lane, with its socket end held out over the open +Y side.
Feed the XT30 end (long side front to back) down through the pigtail hole; the taped leg comes down with the stack.
Hold the stack's port edge away from the U (more than 10 mm from the W mark). [r6] Lower the stack ... drive s_k1
and s_k2 straight down: 0.35-0.5 N m, stop at head contact. Plug the HDMI (90 deg plug) on HDMI0, the FPC on CAM1
(camera end loose[C4-BX-8: ; creased at B0]), the EVF 5 V lead in the upper USB 2 port. [C2] With the top open and the
header in sight, plug the header ends, one housing at a time: QT lead (250 mm) on pins 1/3/5/6 (red on pin 1, 3V3),
the 18/24 lead on 33/34 and the run lead on 37/39 (count from pin 1; a housing one row over puts 5 V from pin 2 on
the QT 3V3 wire). Seat each housing straight down with closed tweezer tips on its top until it stops on the header
plastic. Fingers do not fit beside them. Then tug each wire straight up gently: no housing may lift. Use single
1-pin housings (a 1x2 only on 33/34 or 37/39); never a 1x3 or 2x3 shell. Run the QT and 18/24 leads along the right
wall and across behind the blower inlet (ko_lead_wall, ko_lead_cross), with the QT splice sleeve in the straight
part of the cross run, not in a corner; park their free ends out of the open left side. [r6] The run lead crosses
over the cooler shroud (ko_run_cross)."

**Step 6 action** = SPEC-C1 3.2-1 text with "Mate the 5 V PH junction (pull the lead ends out of the open left side)" read as "Mate the 5 V PH junction with the pair held about 60 mm (a hand's width) out of the open left side" (P1-4), then [C5]: "From now until the panel is on (step 8) keep the body level or
nose-down: only the panel's EVF cap stops the eyepiece moving rearward."

**Step 8 action** (adds += knob_exp, knob_fps [C5]):
"[C4] Lens, panel still off: fit s_c4 loosely. One fingertip on the centre of the camera cover, through the open left
side, presses the camera forward (+X) onto its lip catch: push only, never pinch or turn the cover. Pass the lens
through the collar. Screw it into the adapter with fingertips until it stops, with no extra snug. The camera turns
with it about 3 deg until its metal lock tab meets the hood tab catch, which holds it through metal. [r6] Set iris
and focus, tighten the 2 thumb screws; push the lens gently rearward until the knurl seats on the collar cone; the
camera now hangs on the lens (it touches neither the tub lip, the counterbore nor [C4] the tab-catch tines); snug
s_c4 straight down from above, 0.2 N m. [C2] Panel (knobs on since step 2 [C5]): hold it about a hand's width
(60 mm) off the body, inner face toward it. Pinch the QT plug and push it into the encoder's rear-side socket (the
one nearest the lead) until it latches, with a fingertip backing the encoder board. Mate the 18/24 PH junction in the
air. (The header ends went on at step 4.) Move the panel toward the body along -Y, body upright. At about 30 mm off,
lay the spare QT lead as a flat fold in the space between the encoder and the 18/24 switch, on top of the HDMI
cable; lay the 18/24 spare and its PH junction in the same space at the switch end; keep both away from the blower.
Keep the body upright until the panel is fully home. [r6] Push the panel on along -Y (tongue into the hood groove,
boss tabs into the lip notches, flush; the keeper finger is the camera's rear catch). [C5] Hold the panel home and
turn the camera over onto its hood roof on a folded cloth, grip up (the lead fold is now closed in by the panel, as
in use). Lay a flat block no taller than 25 mm (a closed paperback) on the cloth against the left side, between the
eyepiece and the lens: it bears on the hood band and the panel strip above the knobs and keeps the panel home. Drive
s_b1 and s_b2 first (now downward). Then drive s_r1 and s_r2 level from the right, the block taking the push; hold
the grip with your other hand. 0.35-0.5 N m, stop at head contact. Turn the camera base-down. Never lay the camera on
its left side: the exposure knob would carry it."

**Step 10 action**: "[C3] Draw the pigtail XT30 out of the grip mouth until its face is at least 15 mm out (estimate:
about 28 mm or more). If it does not reach, stop: never mate it inside the bay. Plug the pack XT30 into it, holding
both housings. Push the junction and the folded pigtail up into the bay ahead of the pack, then push the pack up;
nothing may hang in the gaps beside the pack. [r6] Slide the cap on (-X) until the detent clicks. Level check on live
view: if the horizon is off, loosen s_c4 half a turn, turn lens and camera together (window +-1.4 deg: [C4] the
lock-screw heads keep >= 0.3 off the tab-catch tines; computed `roll_catch` window), push the lens back onto the
cone, re-snug s_c4 0.2 N m."

Steps 1, 3 (C3), 2, 9 (C5), 5 (C6a) and 7 (C4) have one owner each: take the spec text.

**ASSEMBLY.md hand-written rows (merge list for the docs pass):**
- s3 row 3: C3 (threaded before lowering, taped in the lane). Row 4: C3 (run lead taped; U at the W mark, not under
  kf4 or the bar) + C2 (8 contacts, single housings, tops level, tugged). Row 2: C5. Row 5: C6a. Row 6: C1 + C5
  ("level or nose-down to step 8"). Row 7: C4 (FPC pack folded and taped [BX-8]). Row 8: C4 (tines, gap each side
  of the tab) + C5 (hood-down pose, never on the left side) + C2 (fold and junction laid before the last 30 mm).
  Row 9: C5 (no knobs). Row 10: C3 (XT30 face >= 15 out) + C4 (window wording).
- s7: item 2/3/4a/5 C5; item 4 C2 text + "the knobs ride out with it" (C5); item 6a, "To close", "Lens swap" C4;
  item 7 C1; item 9 C6c; P3 and the stack-out item C3.
- s1 lens rule row: C4. s2 B0: C4 (second paint mark; FPC crease [BX-8]). s5: C3 Fit bullet + C5 Handling bullet.

**Tool table (s1.1), final numbers:**

| no. | tool | change | owner |
|---|---|---|---|
| 7 | junior hacksaw + small flat file + caliper with depth rod + vise with soft jaws | measure P in place, cut off the panel | C5 |
| 8 | fine tweezers 120 mm | adds: PH junction tuck (6), PH junction lift (s7 item 7) | C1 |
| 9 | hood release tool | release comb + 2 dowels, made to G-MP-REL (only if C6c lands) | C6 |
| 10 | flat bar / steel rule | adds: HDMI push lever (6) | C1 |
| 13 | torque screwdriver | text = `DRIVER['spec']` (only if C6b lands) | C6 |
| 15 | smooth-jaw long-nose pliers, jaws >= 35, tips <= 2.0 thick | new: HDMI unplug (s7 item 7) | C1 (user decision U-1) |
| 16 | printer paper, 2 strips (about 0.2 mm together) | new: knob stop shim (2) | C5 |
| 17 | inspection mirror, head <= 15 mm (optional) | new: see the HDMI seat (6) | C1 |
| 18 | FPC fold card, printed (`stl/tools/fpc_fold_card.stl`) | new: crease (B0), paddle (7) (only if C4-BX-8 lands) | C4 |

The guide's own TOOLS list (guide_steps.py) takes the same numbers.

## 5. Implementation order

Rules for every step:
- **Snapshot first.** Before editing, copy every file the step touches to `SCR/r7/snap/S<n>/`, keeping the relative
  paths. If a step misses its cut-off, or breaks a check it cannot fix within 10 min, roll it back by copying the
  snapshot back. Never leave a half-landed cluster in the tree.
- **One CAD job at a time** (run_locked). Pure-Python checks and tests also go through run_locked, as the specs say.
- **No make_tables / make_bom / guide rebuild in code steps.** The release sequence regenerates the generated blocks.
  One docs agent works in parallel (keep the fan-out lean). It edits only hand-written regions: MEASURED-PARTS.md,
  SPEC.md, ASSEMBLY.md outside the `<!-- BEGIN/END -->` blocks, WIRING.md notes, guide/guide_steps.py, make_bom.py
  `LINES`, the make_tables.py harness-row data (text only, no run), HANDOFF.md and the BLOCKERS status lines. It
  starts a cluster's docs only after that cluster's step has passed its quick checks. Section 5 of each spec gives
  the exact wording; section 4 of this plan gives the merged sentences.
- **Quick-check harness** (written in S0): `SCR/r7/quick/r7_quick.py <check> [--only <insertion|screw>]
  [--rebuild tub,hood,...]`.
  - It loads `rows` from the r6 part STEPs in `out/step/parts`, using the loader from `SCR/blockers/plug.py` /
    `r7/C1-review/rv1.py`.
  - Ids listed in `--rebuild` are built in-process with `build_d2.build_printed(only=pid)`. COTS come from
    `build_d2.build_cots()`.
  - It runs one checks.py function and prints the rows as JSON.
  - Every quick check below is `"$PY" cad/gs8-d2-v1/run_locked.py -- SCR/r7/quick/r7_quick.py ...`.
- **Every step ends green:** `test_common.py` plus that step's new test file pass, and the quick checks match the
  spec numbers (tolerance 0.05 unless the spec says otherwise).

### S0 Prep (10 min; 01:15-01:25)

1. Copy the whole r6 `cad/gs8-d2-v1/out/` (60 MB) to `SCR/r7/r6-out-backup/`. This is the fallback release.
   Write r7_quick.py.
2. Record the r6 baselines from `out/checks.json` in `SCR/r7/baseline.json`: the cable_routes, sweeps, removals and
   driver rows.
3. Prove the harness: run r7_quick `sweeps --only evf_pair_in` on r6. Expect pass with 0 hits (the r6 defect is
   invisible).

### S1 Shared infrastructure + C1 (BX-1 BLOCKER, BX-7, BX-9, C-16) (75 min; to 02:40; cut-off 02:55)

Files:
- **layout.py:**
  - STEPS[6] = C1 text + C5 sentence (s4);
  - INSERTIONS evf_pair_in moving += foam_pad, path [(0, 60, 0), (0, 45, 0), (0, 0, 0)] (P1-4);
  - PLUGS (20 entries, with P1-2);
  - KEEPOUT_KIND; ko_fpc_stiff;
  - ko_qt_plug = C2's box (data only; the qt via changes in S3);
  - ACCESS + FINGERTIP_MM;
  - REMOVALS evf_out (moving, unplug, tool-15 text, eyepiece out of `off`) and pi_out unplug;
  - LATCH_FREE foam_pad; EVF board_slot comment;
  - empty-default support for `riders`, `stowed` and `hold`.
- **checks.py:**
  - the carried-box routine of s2 in check_sweeps and check_removals; its `riders`/`stowed` hooks do nothing until
    S3/S4;
  - CARRY_SOFT_MM;
  - the `reach_margin` helper;
  - `check_mate_paths` = plug_in, access and coverage (the PLUGS part; the MATE_POSES rule comes in S3);
  - evf_restraint support_span_final / support_span_prepanel.
- **build_d2.py:** register `mate_paths` (info_neutral).
- **Tests:** test_r7_c1.py (12 cases; test 5 uses the P1-1 box) and a new test_r7_integration.py skeleton.

Quick checks:
- layout imports; `check_cable_routes` is identical to the baseline.
- r7_quick `sweeps`, all insertions:
  - evf_pair_in passes with carried [] and foam_pad moving;
  - camera_in passes with one soft contact, ko_hdmi_run 0.75 +-0.05;
  - panel_on carried [p_qt_enc], 0 mm3;
  - every row has `fixed_end_obstacles`, all 0.
- Plant the r6 order: evf_pair_in fails with 60-66 mm3 of tub.
- `removals`: evf_out passes with the eyepiece as an obstacle.
- `mate_paths`: plug_in 0; six access rows 0; push room 10.0 >= 9.0 (push_method fingertip); coverage 20/20.
- `evf_restraint`: the six rows unchanged; support_span passes (y 1..3 and 18..28, gap 0.25).

Docs agent after S1: ASSEMBLY s3 row 6, s7 item 7 and tools 8, 10, 15, 17; MEASURED-PARTS MP-HDMI, MP-CAM and
G-EVF-3; the SPEC gate list; make_bom D2-45; make_tables harness rows 93-95 and line 49; guide pages 6b/6c.

### S2 C5 (BX-5 MAJOR, BX-13, BX-14) (30 min; to 03:10; cut-off 03:20)

Files:
- **layout.py:**
  - STEPS 2 (bench, tool, text);
  - STEPS 8: adds += knob_exp, knob_fps, plus the C5 fragment of s4;
  - STEPS 9;
  - INSERTIONS panel_on moving += knob_exp, knob_fps;
  - LATCH_FREE; PART_RATIONALE;
  - PRESS_FITS, SNAP_TOOTH_ZONES, REST_POSES, REST_FORBIDDEN.
- **checks.py:** `check_handling`.
- **build_d2.py:** register `handling`.
- **printed_small.py:** knob_exp note, text only.
- **Tests:** test_r7_c5_handling.py (16).

Quick checks:
- r7_quick `handling`:
  - encoder snap (V_rigid 0.0, V_zone 1.44); switch rigid (15.92); thumb column 0.0;
  - snap_basis passes (389 / 389 / 0.20);
  - rest poses: hood_down {hood} margin 2.7; base_down_8 {base_grip} 2.0; base_down_10 {cap} 6.0.
- `sweeps --only panel_on` with the knobs: 0 mm3.
- `driver` for s_b1, s_b2, s_r1, s_r2: bit gap >= 50.61, handle gap >= 86.04.
- No STL hash changes.

Drop order inside: the rest_pose and rest_cover rows (BX-13) go first. The BX-5 rows and the step-2 text are never
dropped.

### S3 C2 (BX-2 MAJOR, BX-10) + the general reach coverage rule (55 min; to 04:05; cut-off 04:20)

Files:
- **layout.py:**
  - ko_qt_tail, ko_lead_stow; ko_run_leads x0 -64.5;
  - CABLES qt (250, range, via += ko_qt_tail and ko_qt_plug, stow, od); CABLES fps_lead (pigtail, stow, od,
    junction_mm3);
  - ENCODER['qt_socket'], PLUG, qt_plug_point; PI header_rows_y; COTS pi5 gpio;
  - HDR_HOUSING, HEADER_HOUSINGS;
  - MATE_MARGIN, HAND_ENVELOPES;
  - MATE_POSES rows qt_enc, fps_ph, fpc_cam, oled_flex and usb_5v_evf (P1-4);
  - panel_on waypoints 60/30 and `stowed`;
  - the C2 fragments of STEPS 4 and 8.
- **cots.py:** encoder() reads qt_socket (same geometry); pi5() header block.
- **checks.py:**
  - the `_route_polyline` refactor (exact); `_plug_point`;
  - the cable_routes plug-point rule;
  - `check_mate_reach` using `reach_margin`; `check_cable_stow`; `check_header_housings`;
  - in sweeps: `stowed`, stow boxes in active_ko, the housings as obstacles from step 5;
  - the mate_paths coverage MATE_POSES rule (P1-5).
- **build_d2.py:** register mate_reach, cable_stow and header_housings.
- **Tests:** test_r7_c2_mate_reach.py (13; test 9 per P2-1); test_r7_integration.py gains a coverage-rule case.

Quick checks:
- cable_routes: qt 134.6 / 90.4; run_lead 171.1 / 53.9; fps_lead 132.6 / 47.4; the rest equal to the baseline.
- mate_reach:
  - qt_enc 35.2 at L 240;
  - fps_ph: 48.6 + 40.0 >= 60.2;
  - fpc_cam 108.2 +-0.5;
  - usb_5v_evf (inline, disp 60 on the new evf_pair_in waypoint): r1 about 110 >= d about 86; junction 28.8 beyond
    the opening; hand/out_of rows 'info' (gate MP-EVF).
- cable_stow 2288 <= 2542, blower distance 17.9.
- header_housings: cooler 0.68, wall 1.13, kit 0.75, hood 2.27.
- r7_quick `sweeps --only panel_on`: stow 0 mm3.
- `interference`: the pi5 header block sits 0.71 off the cooler.
- The encoder COTS solid volume and bbox are identical to r6.

Drop order inside: the header_housings check (BX-10) goes first. The ko_run_leads widening and the step-4 housing
text stay.

### S4 C3 (BX-3 MAJOR, BX-11, BX-16) + trial build T1 (45 + 10 min; to 05:00; cut-off 05:05)

Files:
- **layout.py:**
  - PIGTAIL; base_run_passage();
  - CABLES pigtail (200, od, cores, lanes) and run_lead (od, cores, lanes);
  - COTS xt30_pair name and mass;
  - ko_pig_wrap, ko_pig_under;
  - FLOOR_HOLES run_lead x0 -41.5; RUN_WINDOW_MIN;
  - pi_in riders; pack_in path with -110.2;
  - MATE_POSES xt30 row (P3-1);
  - STEPS 1 and 3, and the C3 fragments of STEPS 4 and 10.
- **printed_grip.py:** `_base_cuts` uses `L.base_run_passage()`.
- **checks.py:** `_route_points`, `_pigtail_face_out`, `check_lead_access` rows 1-6. The rider rules are already in
  the routine.
- **build_d2.py:** register lead_access.
- **Tests:** test_r7_lead_access.py (18).

Quick checks:
- lead_access: mouth 28.4 / required 190; range 17.4 (17.9 at 310); store 0.176, U-turn 19.2 <= 20; lanes; run
  window 3.5; wrap clear 0.000.
- cable_routes pigtail 86.6 / 93.4.
- mate_reach xt30: slack = face_out - 15 (13.4 at L 200, same helper).
- `build_d2.py --part tub --out cad/gs8-d2-v1/out/_trial-r7`, then `--part base_grip`. The base STL hash must be
  identical to r6.
- r7_quick `sweeps --rebuild tub` for base_on, pi_in, keeper_in and pack_in: 0 mm3.

Then trial build **T1**: `"$PY" cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/build_d2.py --skip-renders
--sweep-step 2.0 --out cad/gs8-d2-v1/out/_trial-r7`.
- It takes about 9-10 min. Run it in the background with one wait that matches the exit and `Traceback`.
- Pass = 0 fail in every category, 34 categories if S1-S4 all landed. Record the build time and the list of
  changed STLs.
- S5 does pure-Python work while T1 runs.

### S5 C4 (BX-4 MAJOR; then BX-15, BX-8) (core 55 min to 05:55; 5b 15 min; 5c 15 min; cut-off 05:55 for the core)

**5a, core BX-4.**

Files:
- **layout.py:**
  - HOOD: roll_fin and roll_webs out, tab_catch in; tab_catch_boxes();
  - CAM['tab'] tip_h and status; ROLL_CATCH; LENS_HOLD_FORBIDDEN;
  - CRITICAL_FEATURES hood_tab_catch_p/n, the class rule and the joint list;
  - LATCH_FREE['lens']; INSERTIONS lens_in hold; REMOVALS lens_off;
  - the C4 fragments of STEPS 7, 8 and 10; PRINT_PREREQ_WHY G-CAM-1; comments.
- **printed_hood.py:** `_tab_catch`.
- **cots.py:** gs_camera_parts 'metal' and 'pcb_cover'; 'body' unchanged.
- **checks.py:** `check_roll_catch`, including lens_hold and the lint.
- **build_d2.py:** register roll_catch.
- **test_hood_panel.py:** the roll-fin rows become tab-catch rows.
- **Tests:** test_r7_c4.py, cases 1-10 and 13.

Quick checks:
- `build_d2.py --part hood --out cad/gs8-d2-v1/out/_trial-r7`.
- r7_quick `roll_catch --rebuild hood`: 3.22 centred, 1.72..4.73; window 0.679 / 0.129; axial 1.40; tine 9.0 MPa.
- `j7_float --rebuild hood`: lateral 1.2, axial 1.45.
- `sweeps --rebuild hood` for camera_in (1.00) and hood_on (0.60 to the TL/TR bosses); `removals` lens_off.
- The gs_camera COTS STEP stays identical (it is built from 'body').
- Measure roll_catch's run time (budget about 3 min, P4-5).

**5b, BX-15.** printed_collar.py thumb dimple; COLLAR['gauge']['thumb']; STEPS 7 `held`; check_driver held (P4-3);
test_r7_c4.py case 11. Quick checks: `--part collar_gauge`; r7_quick `driver --only s_c1,s_c2,s_c3`: held_gap 15.9
or more, bits 27.6 or more.

**5c, BX-8.**
- Files: CABLES fpc fold; printed_tools.py `fpc_fold_card`; build_d2 `export_tools()` and the manifest;
  TOOL_PREREQS with the print_order 'tool' loop (P4-2); `_fold_rows` in cable_routes; make_tables crease-station
  table (data only); test_r7_c4.py case 12.
- Quick checks: cable_routes fpc fold: 9 layers, stack 17.35 <= 17.5, width 16 <= 19.4, estimate row; the card is
  2.0 thick and 10.5 wide.

Trial build **T2** (only if 5a landed and the clock is at or before 05:50): same command as T1. Pass = 0 fail; the
STL changes are exactly those of s7.

### S6 C6 (BX-6, BX-12, BX-17), only if ahead of schedule (6a 20 min, 6b 25 min, 6c 35 min)

**6a, BX-6.**
- Files: PLUNGER keys; STEPS 5 `orient` and action; INSERTIONS plunger_in (listed before hood_on and sd_in);
  INSERTION_EXEMPT = {tub, eyecup} plus the stale-exemption rule (P6-3); printed_hood `_plate_cuts` lead-in;
  printed_small `edge_chamfer` key; check_plunger_capture; the sweeps coverage row; register plunger_capture.
- Quick checks: `--part hood` and `--part plunger` (the plunger hash must be identical); r7_quick plunger_capture
  (1.1 >= 1.0); sweeps plunger_in and hood_on pass.

**6b, BX-12.**
- Files: DRIVER family, handle 250, spec; check_driver family loop with C4 held inside (P6-4b); check_collar_gauge
  family; make_tables screw table data; make_bom D2-77 from DRIVER['spec'].
- Quick checks: r7_quick `driver`: no hit for any member; s_j 5.69 at 60; family_rules pass. Measure the time; if a
  full build would then pass 13 min, drop 6b.

**6c, BX-17.**
- Files: HOOD_RELEASE push 0.50; RELEASE_COMB; printed_tools `release_comb`; export_tools; TOOL_PREREQS;
  release_access stack/comb rows; REMOVALS hood_off text; make_bom D2-71.
- Quick checks: release_access rows; the comb's print_overhang and thin_wall.

### S7 Freeze (hard at 06:20)

No code change after 06:20. Clusters that missed their cut-off are rolled back from their snapshots. They keep the
r6 behaviour and their guide interim wording (ISSUES/TIPS stay as written). The docs agent finishes the hand-written
text for the clusters that landed only.

## 6. Regression tests to add or update

| file | cases | runs in | owner step |
|---|---|---|---|
| test_r7_c1.py | 12 (r6 order fails at 60-66 mm3, r7 order passes, coverage gap, soft limit, synthetic plug/cable keep-out pair, fixed-end plant, mate_overlap row kept, 20 PLUGS, push room 'lever' as push_method, blocked access, B-cut support_span, pad moves with the pair) | run_locked, part slow | S1 |
| test_r7_integration.py (new, from this plan) | 6: one routine sweeps a carried plug and a rider in the same insertion; a carried box is an obstacle for a later same-step insertion; deleting MATE_POSES `usb_5v_evf` fails mate_paths coverage naming (usb_5v, evf_pair_in); deleting `xt30` fails it naming (pigtail, pack_in); `reach_margin` equals C3's allowance at 150/200/250/310; the category count equals len(order) + 1 (36 when all land) | fast | S1, S3, S4 |
| test_r7_c5_handling.py | 16 | fast + proxies | S2 |
| test_r7_c2_mate_reach.py | 13 (3 slow); test 9 per P2-1 | fast / slow | S3 |
| test_r7_lead_access.py | 18 | fast | S4 |
| test_r7_c4.py | 13 (11 with 5b, 12 with 5c) | slow | S5 |
| test_r7_c6.py | 19 (only the landed sub-items) | mixed | S6 |
| test_build_outputs.py | category count from the summary, not 28 | fast | S1 |
| test_hood_panel.py | roll_fin rows -> tab_catch rows | slow | S5 |
| validation/README.md | add the r7 test commands to the list | docs | S7 |

## 7. Full release sequence (after the freeze; about 35-45 min)

Run from `R` in Git Bash, `PY` as above, each command after the previous one finished. Every build gets one
background wait matching exit and `Traceback`; never a second wait for the same build.

```text
"$PY" cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/test_common.py
"$PY" cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/make_coupons.py
"$PY" cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/coupons_r1.py
"$PY" cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/build_d2.py --skip-renders --sweep-step 1.0
"$PY" cad/gs8-d2-v1/make_tables.py
"$PY" electronics/gs8-d2-v1/make_bom.py
"$PY" cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/build_d2.py --lens fujinon_hf6xa --skip-renders --sweep-step 1.0 --out cad/gs8-d2-v1/out/_fujinon-cloud-polish-20261007
"$PY" -c "import shutil; shutil.copyfile('cad/gs8-d2-v1/out/_fujinon-cloud-polish-20261007/checks.json','cad/gs8-d2-v1/out/checks-fujinon-sweep1mm.json')"
"$PY" cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/build_d2.py --skip-renders --sweep-step 1.0
"$PY" cad/gs8-d2-v1/make_tables.py --docs design
"$PY" cad/gs8-d2-v1/make_tables.py --check
"$PY" cad/gs8-d2-v1/audit_cloud_release.py --out cad/gs8-d2-v1/out --final-release --alternate-out cad/gs8-d2-v1/out/_fujinon-cloud-polish-20261007 --json validation/rebuilt-cad-integrity.json
```

Then from `R/cad/gs8-d2-v1`:

```text
"$PY" run_locked.py -- test_r3_regressions.py
"$PY" run_locked.py -- -m unittest -v test_mechanical_refinements test_datum_inputs test_panel_refinements test_collar_rear_land test_build_outputs test_print_stock_exports test_release_gates test_audit_cloud_release test_run_locked
"$PY" run_locked.py -- test_collar.py
"$PY" run_locked.py -- test_r7_c1.py      (and each landed test_r7_*.py, test_hood_panel.py)
```

Before the first build: move `out/_trial-r7` to `SCR/r7/trial-r7` so that out/ holds only release outputs. Set `layout.REVISION` (or the release label constant the receipt uses) to **GS8 D2
r7-20261009 (r6-20261008 + blocker review 2026-10-08 fixes)**. The guide re-render (`guide/build_guide.py`) runs only
if time remains after the tests. Otherwise HANDOFF records that the guide text was updated and the renders are
pending.

**Expected receipt deltas (replaces every per-cluster "unchanged" claim):**
- **STLs that change:**
  - tub (C3 floor hole);
  - hood (C4 tab catch; C6a lead-in);
  - collar_gauge (C4 5b);
  - new stl/tools/fpc_fold_card.stl (C4 5c) and stl/tools/release_comb.stl (C6c).
- **STLs that must stay byte-identical:** every other printed part, including base_grip (C3 decoupling), plunger
  (C6a key), panel and knobs.
- **COTS STEPs:** pi5 changes (C2 gpio block). Encoder and gs_camera stay identical.
- **Categories:** 28 + the landed new ones (36 if all land), 0 fail.
- **Physical gates added:** G-EVF-3, MP-QT/G-QT-1/G-HDR-1, the G-W2 and G-MP-PACK additions, the G-CAM-1/2
  additions, G-KNOB-1/G-ENC-1/G-MP-ENC/G-MP-SW texts, and (C6) G-PLG-2/G-MP-REL/G-MP-T13. The open-gate counts rise;
  that is not a fail.
- **Release build time:** about 10-13 min per Kowa/Fujinon build with roll_catch and the C6b family.
- **If a release build fails:** fix it only if the fix takes 10 min or less. Otherwise restore the failing
  cluster's snapshot and restart the sequence; a restart costs about 30 min.
- **After about 06:50 there is no time for a restart.** Then stop:
  - keep the r7 code;
  - copy the failing out/ to `SCR/r7/failed-release/`;
  - restore `SCR/r7/r6-out-backup` to out/;
  - write in HANDOFF: "r7 candidate (code in tree), release build failed at <category/row>; out/ is the r6 release".
  - Never claim a release that did not pass.

## 8. Time budget against the 07:30 deadline, and what to drop

The schedule assumes implementation starts at 01:15. The clock times are targets; the cut-offs are hard.

| slot | clock | content | if late |
|---|---|---|---|
| S0 | 01:15-01:25 | backup, harness, baselines | - |
| S1 | 01:25-02:40 (cut-off 02:55) | infrastructure + C1 (BLOCKER) | cannot be dropped; every later minor shifts out |
| S2 | 02:40-03:10 (cut-off 03:20) | C5 (BX-5 MAJOR) | drop the rest-pose rows (BX-13) first |
| S3 | 03:10-04:05 (cut-off 04:20) | C2 (BX-2 MAJOR) + the coverage rule | drop the header_housings check (BX-10) first |
| S4 + T1 | 04:05-05:00 (cut-off 05:05) | C3 (BX-3 MAJOR) + trial build | T1 cannot be dropped (it is the first full-geometry check) |
| S5a | 05:00-05:55 (cut-off 05:55) | C4 core (BX-4 MAJOR) | cannot be dropped; if it misses 05:55 by more than 15 min, roll back C4 and record BX-4 as open |
| S5b, S5c, T2 | 05:55-06:20 | BX-15, BX-8, second trial | dropped first |
| S6 | only if ahead | C6 minors | dropped first |
| freeze | 06:20 | no code change after this | - |
| release | 06:20-07:00 | s7 sequence (Kowa about 10, tables/bom 1, Fujinon about 10, Kowa about 10, tables/audit 3) | see the s7 fallback |
| tests | 07:00-07:15 | r3 suite, unittest list, test_collar (about 2.5 min), the r7 tests | - |
| wrap | 07:15-07:30 | HANDOFF top entry, BLOCKERS status lines, guide re-render only if time | stop at 07:30 sharp |

Code time available: 01:25-06:20 = 4 h 55 min. The full scope (S1-S6) needs about 6 h 10 min of agent time. The
expected outcome:
- S1-S5a land: the BLOCKER, all four MAJORs, and the minors BX-7, BX-9, BX-10, BX-11, BX-13, BX-14 and BX-16.
- BX-15 and BX-8 land only if the earlier steps run fast.
- C6 (BX-6, BX-12, BX-17) most likely stays open with its current interim guide wording.

**Drop order (first dropped first):**
1. C6c BX-17
2. C6b BX-12
3. C6a BX-6
4. trial build T2
5. C4 5c BX-8
6. C4 5b BX-15
7. C5 rest_pose / rest_cover rows (BX-13; the step-8 wording stays)
8. C2 header_housings check (BX-10; ko_run_leads and the housing text stay)

Never dropped: BX-1 (C1 core), BX-2, BX-3, BX-4, BX-5.

A dropped item keeps its r6 behaviour and its guide ISSUE/TIP text. HANDOFF lists it as "open, spec ready:
SPEC-Cn". Its spec and Plan edits stay valid for the next session.

## 9. Closure map (item -> step -> computed check -> physical gate)

| item | step | computed proof | gate |
|---|---|---|---|
| BX-1, C-16 | S1 | sweeps carried plugs (r6 order fails at 60-66 mm3), mate_paths plug_in/access, evf_restraint support_span | G-EVF-3 |
| BX-7, BX-9 | S1 | sweeps foam_pad mover; mate_paths acc_5v_tuck | G-EVF-1, G-EVF-3 |
| BX-5, BX-14, BX-13 | S2 | handling press_cover/press_fit/snap_basis (rest_pose/rest_cover) | G-KNOB-1, G-ENC-1, G-MP-ENC, G-MP-SW |
| BX-2, BX-10 | S3 | mate_reach qt_enc (out_of), cable_stow, cable_routes plug-point rule, coverage rule (header_housings) | MP-QT, G-QT-1, G-HDR-1 |
| BX-3, BX-11, BX-16 | S4 | lead_access rows 1-6, mate_reach xt30, sweeps riders | G-W2, G-MP-PACK, MP-RUN |
| BX-4 | S5a | roll_catch (first_contact, window, tine_strength, axial, lens_hold), j7_float | G-CAM-1, G-CAM-2 |
| BX-15 | S5b | driver held envelopes | - |
| BX-8 | S5c | cable_routes fpc fold | G-MP-FPC |
| BX-6, BX-12, BX-17 | S6 | plunger_capture; driver family + family_rules; release_access stack/comb rows | G-PLG-2, G-MP-T13, G-MP-REL, G-SNAP-2 |

Records: `guide/BLOCKERS-2026-10-08.md` stays the record. Append one status line per landed item, e.g. "r7: BX-1,
C-16, BX-7, BX-9 fixed in CAD (SPEC-C1)". Guide ISSUES are deleted only for landed items. HANDOFF.md top gets one r7
entry: the revision label, what landed, what was dropped, the category count, the build receipt and the user
decisions below.

## 10. User decisions

1. **U-1 (C1), pliers for service item 7.** Smooth-jaw long-nose pliers become tool 15, a hand tool with no BOM row.
   No finger fits the 6.6 mm gap on the -X side of the EVF HDMI plug. Default: included.
2. **U-2 (C2), how the QT lead is made.**
   - Default: splice Adafruit 4397 to Pololu #5521. Both are named parts; about USD 2 extra.
   - Option: buy an unverified one-piece JST-SH to 4 x 1-pin Dupont lead, 240-270 mm, after the MP-QT buy-check.
3. **U-3 (C4), FPC length.** Default: keep the 200 mm 22-to-15 FPC; the fold fits with a 0.15 mm margin on
   estimates, and G-MP-FPC confirms it. Option: source a 100-150 mm FPC.
4. **U-4 (C6), conditional.** Only if G-SNAP-2/whole fails: approve a hood strain stop behind hk1/hk2. Nothing to
   decide now.
5. **U-5 (C1), for the record.** Bench-mating the EVF HDMI (fix B) needs the tub cut, a panel heel and a
   right-wall-down rule. It is not recommended; reconsider only if G-EVF-3 fails on the first print.
6. **U-6 (integration), scope at the deadline.** At 07:30 the C6 minors (BX-6, BX-12, BX-17) and probably BX-8 and
   BX-15 stay open, with their current interim guide wording and ready specs. The alternative is to allow more time
   later.

Nothing is bought, printed or measured by this plan. New BOM lines (D2-24B Pololu 5521, D2-46R neutral-cure RTV)
are planning entries only.
