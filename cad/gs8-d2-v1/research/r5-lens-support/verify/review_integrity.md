# r5 lens-support review: code, check integrity and docs (reviewer: integrity)

Time-boxed review, 2026-10-06 16:50-17:00 +0800. Read-only: no build and no repo edits apart from this file. The r4
baseline was extracted to the session scratchpad (outside the repo). My probe `p_rev.py` (in the scratchpad) ran once
under `run_locked.py`, took 24 s and loaded the r5 STEP parts in memory only. `verify/p_integrity.py` / `.json` were
already in this folder (written 16:48-16:49, before this review started, probably by an earlier spawn of this
reviewer). I use their results as supporting evidence and re-ran two of their cases myself.

## Verdict

None of the r4 checks has been weakened or made unable to fail. The 4 new checks (`j7_float`, `lens_support`,
`lens_clamp`, `inserts`) all FAIL on planted faults. The receipt re-hashes cleanly, and `make_tables --check` and
the regression suite are clean. There are 3 minor findings (one latent rule gap, one misreported status, missing
regression tests) and 3 note-level doc items. Nothing blocks the release.

## Findings

**F1 (minor, confirmed): a light lens without a support band passes every r5 check, but under J7-R nothing anchors it.**
r5 deletes the camera pins and the turret: the camera hangs on the lens and the lens collar is the only anchor.
`check_lens_support` FAILs a missing band only above `support_mass_g` 150 g (checks.py 1815-1821), and
`check_lens_clamp` skips any lens with no collar (`if cs is None: continue`).
- Probe: a synthetic 20 g data-only lens with no `support` gives lens_support `[('support', 'pass')]` and 0 lens_clamp rows.
- No current lens triggers it: Kowa, Fujinon and Computar all have bands.
- It becomes live if an M12 lens (LENS-M12-ANAMORPHIC: 10-20 g) is adopted.
- The 150 g rule came from the brief, which predates "the collar is the only anchor".
- Fix: under J7-R, FAIL any LENSES entry without a collar (or Plan-B anchor), whatever its mass, and add a regression test.

**F2 (minor, confirmed): `check_j7_float` relabels a real fail as 'stub' when any measured obstacle is a stub.**
At checks.py 1745-1747 the downgrade fires if any part in `per_obstacle` (every obstacle within 6 mm) is a stub, not only the part that caused the fail.
- Probe: a hood bump 0.3 mm over the body gives `body fail` ("lateral gap 0.300 to hood < 0.50").
- With an unrelated `tub` flagged stub, the same row reads `stub`.
- The category still blocks `cad_release_candidate` (any non-pass blocks, build_d2.py 1477), so this misattributes the problem but does not hide it.
- Fix: downgrade only when every offending obstacle (the `over` list and the `to` of each failing minimum) is a stub.

**F3 (minor, confirmed): the new checks lack planted-fault regression tests for most failure modes.**
`test_r3_regressions.py` (38/38 pass) has:
- 3 `j7_float` tests (real datums, lip gap 0, keeper 0.2 at s max);
- 1 `lens_support` test (300 g, no band);
- 1 `lens_clamp` test (axis outside the polygon);
- for `check_inserts`, only a screw-set assertion (`test_pt_count_ignores_m3`), with no geometry fault.

The checks do work today. In `verify/p_integrity.json` each of these planted faults FAILs:
- inserts: bore 4.4, wall 1.2, tip bottoming, shallow bore 3.7, collar hole r 1.45;
- lens_support: bore +0.3, collar +-0.3 x, thumb keep-out bump, band over a moving ring;
- lens_clamp: 1.5 kg lens, 20 N pinch;
- j7_float: lateral, diagonal and axial faults, and the lens hitting the hood.

But nothing in the suite would catch a later regression in them.
- Fix: port these cases into `test_r3_regressions.py`.

**F4 (note, confirmed): DESIGN.md s5 still lists the camera pins as built geometry.**
- Line 247 ("J7 camera -> tub | pins at (y -15, z 75) and (15, 45)...") and line 272 ("cots_build: camera_in pin; tub T1") have no r1-r4 label.
- Row 248 and line 283 do say the pins were deleted in r5.
- Fix: mark both rows "(r1-r4; deleted r5)".

**F5 (note, confirmed): LENS-M12-ANAMORPHIC.md has no r5 note and argues from the r4 stack.**
Lines 50 and 128 talk about the load "on the plastic mount". Under r5 the lens is held by its collar and the camera
floats, and an M12 lens would need a collar (see F1). This is out of scope for r5 but now rests on the old stack.

**F6 (note, confirmed): two pre-r5 studies still model the turret and pins and carry no r5 marker.**
- `candidate-fr1` (exploratory FR1): its own `layout.py`, `checks.py`, `printed_hood.py` and `printed_tub.py` reference `turret` / `wall_bore_d`, and `CANDIDATE.md` never mentions r5.
- `airflow/network.py` (paused study) references the turret.
- Adopting either requires rebasing it on r5.

## Verified OK

- **Regression suite:** `test_r3_regressions.py` passes 38 of 38 (13.5 s).
- **Tables:** `make_tables.py --check` reports stale none, 0 count-lint disagreements, selftest ok.
- **Receipt hashes:**
  - all 17 `sources` match;
  - 43 of the 101 `files` sampled (25 random plus every tub and lens_collar entry), all match;
  - the `checks.json` sha matches `cad_checks.checks_json_sha256`;
  - the 4 `hardware_gates.source_docs` match.
- **checks.py diff vs r4 (7 lines removed, 526 added):**
  - The 2 "camera ring in tub/hood bore" zones (0.25 clearance) are replaced by 3 real-stack zones: BFAR counterbore with lip gap 0.5, adapter in the tub lip 0.825, adapter in the hood plate bore 2.875.
  - `j7_float` adds a lateral 0.5 / 0.6 and axial 0.4 rule, checked at s 0 / 1.25 / 3.0.
  - The boss audit is now PT only, and M3 screws go to `check_inserts`; the driver audit uses the M3 head height.
  - No tolerance was loosened.
- **layout.py:** only the deleted turret's self-checks are gone. The PT engage and length checks are kept under the kind branch. 183 layout checks, 0 failed. The tub/gs_camera mate changed from contact to clearance, which is stricter.
- **build_d2.py:**
  - The 4 new categories are in the summary order.
  - `info_neutral` needs at least 1 real pass, and the J7 joint test fails on a category with info rows only.
  - Any non-pass status blocks the release.
  - STATE_GATES: `G-CAM-` is narrowed to `G-CAM-1$`, G-CAM-2 moves to assembly_operation and COL joins the coupon gates. This is consistent with the receipt's gate list.
- **Real assembly:** `j7_float` obstacles include screws (`s_r1`) as well as the hood, collar, panel and tub. The minima are body 0.4 axial and BFAR 0.5.
- **Fujinon variant:** the `out/_fujinon-r5` receipt has 27 of 27 pass. Its code sources are identical to the release; only SPEC.md and FASTENER-POLICY.md differ. It was built with `--fast`.
- **Kowa lens_clamp WARN:** M_sep 0.170 is below the 5 g moment 0.286 (static ratio 2.97). It is an info row and is disclosed in HANDOFF:37 and RECTIFICATION:437.
- **Doc grep:** SPEC, MEASURED-PARTS, HANDOFF s0 and LENS-ZOOM-CANDIDATES mark the r1-r4 facts as superseded: C flange +10.6, 39.5 lands, dia 36.5 ring bore, pins, turret. HANDOFF's "11 printed parts" appears only in sections labelled r3 or FR1-vs-r2. The hood plate bore of dia 36.5 is current (adapter clearance), not stale.

## Not reviewed (deadline)

- The LOAD_MODEL physics: the M_sep formula and the pinch and relax numbers.
- The `cots.py` camera and lens proxies against `gs_side.png` and `kowa_zoom.png`.
- `test_collar.py`, `test_hood_panel.py` and `test_tub.py`, which were not run (CadQuery).
- What `--fast` omits in the Fujinon variant.
- The remaining 58 receipt files.
- The `printed_collar.py` code and the collar coupons.
- The judge/dossier cross-check.
