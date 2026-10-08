# D2 r5 audit: verification-system integrity (logic dimension)

Auditor: logic / check integrity. Date 2026-10-06. Scope: `cad/gs8-d2-v1` r5 (receipt 16:32:38). Read-only on cad/,
electronics/ and docs. I did not run any CadQuery build. Scratch files: `logic_planted.py` (30 planted-fault probes;
pure logic plus small `cq.Solid.makeBox` primitives; no part module is built) and `logic-audit.json` (its results).
I formed my own view first and only then read `research/r5-lens-support/verify/review_integrity.md` (F1-F6).

## 1. Runs requested

| Command | Result |
|---|---|
| `.venv-cad/Scripts/python.exe -B cad/gs8-d2-v1/test_r3_regressions.py` | **38 of 38 cases pass**, exit 0 |
| `python cad/gs8-d2-v1/make_tables.py --check` | `stale: none`; `count lint: 0 disagreeing phrase(s); selftest ok`; exit 0 |
| Re-hash of `out/build-receipt.json` (python, read-only) | 17/17 `sources`, 101/101 `files` and 4/4 gate docs match the files on disk |
| r4 vs r5 category diff (`out/_r4-2026-10-06/checks.json` vs `out/checks.json`) | no category lost rows or changed status; 4 new categories added |
| `logic_planted.py` | 30 probes: 17 caught, 13 missed (the missed ones are listed below; several are latent or by design) |

## 2. Verdict

**The 27/27 and `cad_release_candidate: true` can be trusted as a computed CAD claim for the geometry as modelled.
I found no blocker and no major issue.**
- No r4 check was removed or loosened. One r4 probe was relocated by an id override (L5).
- The release logic is sound: an empty category FAILs; info-only categories FAIL; unknown statuses FAIL; any stub or
  non-pass blocks the release; the J7 joint requires its 4 r5 checks, each with >= 1 pass and no fail or stub.
- Evidence records go stale when the collar, tub or coupon hashes change (P19, P20, P22).

The 27 count overstates the coverage in a few places:
- one category is vacuous (`mass_com`, L9);
- the WARN gate is a string in layout.py (L6);
- `j7_float` samples only 3 back-focus positions (L2);
- several latent rule gaps would let a future fault pass (L1, L3, L4, L7).

## 3. Planted-fault results (summary; full data in logic-audit.json)

Caught as expected:
- P4 control pass.
- P5 camera body touching the tub: FAIL.
- P6 axial gap 0.39 vs rule 0.40: FAIL.
- P9 no obstacle within 6 mm: FAIL.
- P12 lens overlapping the hood: FAIL.
- P15 info-only lens_clamp: FAIL.
- P16 empty j7_float: FAIL.
- P17 unknown status `n/a`: FAIL.
- P18 inserts with no solids: FAIL x4.
- P19 current G-COL-1 record: pass. P20 the same record after a collar-coupon hash change: stale.
- P22 G-CAM-2 bound to the gate doc + all 12 production STLs (collar, tub, hood and panel included).
- P23/P24 G-CAM-1 and G-LENS bound to MEASURED-PARTS.md.
- P25 malformed records (list artifacts, upper-case hex, list item, bad verdict): rejected.
- P26 every live coupon gate (10, G-COL-1 included) has coupon STLs bound.
- P27 G-CAM-1/G-LENS -> measured_fit, G-COL-1 -> coupon_validation, G-CAM-2 -> assembly_operation.

Missed, each with its finding:

| Probe | Planted fault | Observed | Finding |
|---|---|---|---|
| P1 | 140 g data-only lens, no band, no collar | `support: pass` | L1 |
| P2 | default-lens collar solid absent | 3 measured items silently skipped, no fail | L3 |
| P3 | `support.status='measured'` set with no G-LENS record | WARN cleared, `pass` | L6 |
| P7 | clash only at s = 2.0 (between the samples) | missed at s 0/1.25/3.0; FAIL when s 2.0 is added | L2 |
| P8 | real clash beside an unrelated stub obstacle | `stub` | L8 |
| P10 | no `lens` row | lens rows absent, no fail | L3 |
| P11 | lens barrel touching the hood (0 gap) | `pass` | L4 |
| P13 | anchor polygon closed only by the LR compression foot | `pass`, bolted-only margin -8.8 not gated | L7 |
| P14 | every per-lens clamp row WARN | J7 joint `pass` (the anchor-polygon row is the 1 pass) | L7 |
| P21 | coupon gate missing from the manifest | required `[]`, a record naming only SPEC.md -> `pass` | L10 |
| P25e | record with `date: "not a date"` | accepted | L12 |
| P28 | item id `MP-CAM` | not a registered gate (fails safe: unmatched) | L12 |
| P29 | two CRITICAL_FEATURES with the same id | silently de-duplicated, last wins | L5 |
| P30 | `mass_com` rule | `pass` if total mass > 0 | L9 |

## 4. Findings

**L1 (minor, latent): a light lens without a band or collar passes `lens_support`. Under J7-R nothing would hold it.**
- Where: checks.py:1817 (`need = d['mass'] > LM['support_mass_g']`); checks.py:1914 (`lens_clamp`: `if cs is None:
  continue`); layout.py:1765 (the self-check carries the same 150 g rule).
- test_r3_regressions.py:465 asserts that the 120 g no-band lens *passes*, which locks the gap in.
- Reproduction: P1.
- Failure scenario: an M12 or other light lens is added to LENSES or LENSES_DATA_ONLY. The camera and lens then float
  inside the catches with no anchor, and every r5 check stays green.
- Fix: under J7-R, FAIL every lens without `support` (or a Plan-B anchor), whatever its mass. Invert the test.
- CONFIRMS F1.

**L2 (minor): `j7_float` samples only s = 0 / s_nom / s_max. A clash between the samples passes.**
- Where: checks.py:1715.
- Reproduction: P7. A 0.55 lateral fin (BFAR rule 0.6) level with the BFAR at s 2.0 is missed at the three default
  s values. It FAILs once s 2.0 is added.
- Failure scenario: the gap to a fixed feature is not monotone in s for a short mover, because the BFAR head is
  1.2 long against a 3.0 travel. A local feature (a rib, a screw head, or a keeper edge moved by G3) between two
  samples is never measured.
- Fix: sample s at <= 0.5 mm (s_range / 6), or at the build's `--sweep-step`. Better: check the swept envelope of
  the BFAR head and the body over s_range.
- NEW.

**L3 (minor): `lens_support` and `j7_float` skip their lens and collar measurements without a row when the solid is absent.**
- Where: checks.py:1843 (`if col is not None and name in L.LENSES`); checks.py:1727 (`if lens is not None`).
- Reproduction: P2 and P10. Statuses stay pass/info, and `lens_seated`, `bore_measured`, `seat_measured`, the lens
  overlap and lens-vs-camera rows simply disappear.
- Mitigation today: a stub collar blocks the release through `stubs`. A missing `lens_collar` part would FAIL the J7
  feature probes (collar_* required in J7_camera).
- Failure scenario: a refactor drops the `lens` COTS row, or `lens_collars()` returns `{}` for a non-stub reason. The
  category still passes.
- Fix: for L.LENS, emit a `fail` row ("collar / lens solid not provided") instead of skipping.
- NEW.

**L4 (minor): the lens row in `j7_float` is overlap-only. Any zero-gap contact between the lens and a chassis part passes.**
- Where: checks.py:1727-1736 (VOL_TOL 0.05 mm3, no minimum gap).
- Reproduction: P11 (lens box touching a hood plate: `pass`). P12 (0.5 mm overlap) FAILs.
- Failure scenario: the lens barrel or a moving ring rests on the hood plate or the tub lip. That is a second,
  unintended support path, which defeats the J7-R float and drags on focus. Under the lens's own tolerance or
  G-LENS dimensions it becomes real contact.
- Fix: give the lens (fixed band excluded, moving rings especially) a minimum gap to every part except
  `lens_collar` and the adapter, e.g. >= 0.5.
- NEW.

**L5 (minor): `registry()` silently de-duplicates CRITICAL_FEATURES by id, last wins. r5 used this to relocate an r4 probe.**
- Where: checks.py:837-846. layout.py:1049 (r4 `tub_front_wall_seat` at y -20, z 30, the plain front wall) is
  overridden by layout.py:1589 (TL boss root, y 11, z 86).
- Reproduction: P29.
- RECTIFICATION R5-3.3 says the probe "moved", but the original line is still in layout.py and only the override
  hides it.
- Consequence: the plain front wall is no longer probed. The LR compression foot (feet LR = (-19, 44)) bears on that
  wall, and no tub probe sits under it (the tub boss probes are TL/TR/LL only).
- Failure scenario: a later accidental id collision deletes a probe with no row and no error. For example, a
  plain-wall thinning near the LR foot passes the critical gate.
- Fix:
  - make a duplicate id a FAIL row in `check_critical_features` (or raise);
  - delete layout.py:1049;
  - add a `tub_front_wall_lr_foot` probe under the LR foot to J7_camera.
- NEW (the internal review's "no r4 check weakened" missed it).

**L6 (minor): the only gate that clears the "band not measured" WARN is a string in layout.py, not an evidence record.**
- Where: checks.py:1871 (`if sp.get('status') == 'measured'`).
- Reproduction: P3. Editing `'drawing'` to `'measured'` turns the info row into a pass. Nothing ties it to a current
  G-LENS record.
- Failure scenario: after G-LENS someone sets status 'measured' without updating x0/x1/OD (G3). The WARN vanishes, and
  the tub and panel are printed against unmeasured band data.
- Fix: derive the status from `status_states.measured_fit.items['G-LENS'].outcome == 'pass'`, or require a
  `measured_ref` with the record's sha. Also make the release gate list "G-LENS before tub/panel/collar slicer
  records" explicitly. Today nothing orders evidence states.
- NEW (related to the geometry reviewer's G3).

**L7 (minor): the anchor polygon passes only through the compression-only LR foot. The bolted-only margin is computed but never gated.**
- Where: checks.py:1890-1899 (`bolted_only_margin_mm` -8.8 is reported; `status` uses the 4-foot hull, margin 16.0).
  The joint rule in checks.py:2111 accepts a category with >= 1 pass.
- Reproduction: P13 and P14. P14: with every per-lens clamp row a WARN, the J7 joint still passes on the
  anchor-polygon row alone.
- Failure scenario: a prying load lifts the LR foot, which only works in compression. The bolted triangle does not
  enclose the axis, and the check cannot see it.
- Fix: add a prying-factor row (FAIL if the moment about the bolted-triangle edge exceeds the bolt preload x a
  factor), or WARN when `bolted_only_margin < 0`. Require each lens in `lens_clamp` to have a non-fail row of its own
  (a per-lens "pass or info", not one pass per category).
- CONFIRMS the geometry reviewer's G5 (internal review_geometry.md); its integrity side is NEW.

**L8 (minor): `j7_float` downgrades a real FAIL to `stub` when any obstacle within 6 mm is a stub.**
- Where: checks.py:1745-1747.
- Reproduction: P8.
- The release stays blocked (stubs block `rc`), but the offending part is misreported.
- Fix: downgrade only if every offender (`over` plus the `to` of each failing minimum) is a stub.
- CONFIRMS F2.

**L9 (note): `mass_com` is one of the 27 "passing" categories but has no rule.**
- Where: build_d2.py:1385 (`mc_ok = all(m['total_g'] > 0 ...)`).
- Reproduction: P30.
- HANDOFF says the balance "rules [are] unchanged", but no check enforces CoM limits. Kowa +1.5 / Fujinon -9.8 are
  reported only. This predates r5.
- Fix: gate CoM against the stated balance rule, or relabel the category 'info' so it does not count toward 27/27.
- NEW.

**L10 (minor, latent): a coupon gate with no coupons in the manifest accepts any current artifact.**
- Where: build_d2.py:1041-1042 (`cmap.get(it, [])`). In `evaluate_item`, required `[]` means "any current artifact".
- Reproduction: P21. G-COL-1 with an empty map: a record naming only SPEC.md at its current hash gives `pass`.
- Today every live coupon gate is bound (P26).
- Failure scenario: a manifest gate-text typo (e.g. "G-COL1") silently unbinds a gate, and a person-recorded pass on
  an unrelated file closes it.
- Fix: in `required_artifacts_of('coupon_validation')`, return a sentinel that rejects every record when the map is
  empty, and list "coupon gate with no coupons" as a build error.
- NEW.

**L11 (minor): coupon and Fujinon provenance are hash-linked but not source-linked.**
- Coupons:
  - `coupons-manifest.json` has no source or part hashes, so the main build cannot tell whether the coupons were cut
    from the current parts.
  - Today they were: the coupons were written at 16:06, after the last source edit (16:03), and
    `stl/coupons/collar_part.stl` sha == `stl/lens_collar.stl` sha (`d38f9dd7...`).
  - Failure scenario: someone edits printed_collar.py, rebuilds the parts but not the coupons. A G-COL-1 record on the
    old coupons stays current while the production collar differs.
  - Fix: write `sources` into the coupon manifest, and FAIL the main build if they differ from `source_hashes()`. Or
    assert `collar_part.stl` == `lens_collar.stl` (and the tub/hood crops) in the build.
- Fujinon:
  - The main receipt hashes `checks-fujinon-sweep1mm.json` but does not compare the Fujinon receipt's sources.
  - Today the code is identical; SPEC.md and FASTENER-POLICY.md differ (16:16 vs 16:32 builds).
  - Fix: record the Fujinon receipt's sources and flag a mismatch.
- Separately, G-COL-1 covers only the default (Kowa) collar. The Fujinon collar (18.6 g) has no coupon item.
- NEW.

**L12 (note): receipt and evidence coverage gaps.**
- (a) `source_hashes()` (build_d2.py:1130) omits the tests and the evidence rules:
  - test_r3_regressions.py, test_collar.py and the other test_*.py, run_locked.py and evidence/README.md are not
    hashed, so "38/38" is not bound to the receipt;
  - out/test_tub.json and out/test_hood_panel_hood_panel.json sit in out/ unhashed (only test_common.json is
    carried);
  - printed_collar.py *is* hashed (17 sources = 9 fixed + 7 part modules + coupons_r1.py).
- (b) `validate_record` does not check `date` or `by` (P25e).
- (c) MEASURED-PARTS uses MP-CAM as a record name, while evidence items must be G-CAM-1 / G-LENS. A record filed as
  `MP-CAM` would be unmatched (it fails safe: the state stays open). Say so in evidence/README.md.
- (d) evidence/README.md:45 still says the tub has 7 modifiers. r5 has 10 (s_c1..s_c3 added), and make_tables lint
  does not cover that file.
- (e) Several r5 values sit exactly at their rules, so the computed pass has zero margin on 'unconfirmed' camera
  data: j7 body axial 0.40 / 0.40, keeper 0.5 / 0.5, insert boss x0 -7.6 / -7.6, lug |y| 35.0 / 35. Some r5
  self-checks are tautological (layout.py:1770 seat_x = C + x0 by construction; also the pre-existing
  layout.py:1748). That is fine as a guard, but they inflate the 183 count.
- NEW (e partly CONFIRMS the geometry reviewer's G3).

## 5. Internal review cross-reference (read after forming the above)

| Internal finding | My label | Comment |
|---|---|---|
| F1 light lens without band passes | CONFIRMS F1 (= L1) | also locked in by test_r3_regressions.py:465; self-check layout.py:1765 has the same rule |
| F2 stub relabel | CONFIRMS F2 (= L8) | P8 reproduces it; release still blocked |
| F3 missing planted-fault regressions | CONFIRMS F3 | add P2/P7/P10/P11/P21/P29 cases too |
| F4 DESIGN pin rows | not in my dimension | fixed 17:05 outside the hashed docs (HANDOFF s0) |
| F5 LENS-M12 note | not in my dimension | links to L1 |
| F6 candidate-fr1 / airflow stale | not in my dimension | - |
| "No r4 check weakened" | DISAGREES (partly) | L5: the r4 plain-wall probe was dropped by an id override; nothing loosened its tolerance, but coverage under the LR foot is gone |
| "Fujinon sources identical, `--fast`" | CONFIRMS | `--fast` skips only STEP and renders (build_d2.py:1335); see L11 for the missing cross-check |

New relative to the internal review: L2, L3, L4, L5, L6, L7 (integrity side), L9, L10, L11, L12.

## 6. Fix priority before the next release build
1. L1 + L5 + L4: three small checks.py/layout.py edits with regression tests (FAIL any lens without a collar; FAIL on a
   duplicate feature id and add an LR-foot tub probe; give the lens a minimum gap).
2. L2: sample s finely in `j7_float`.
3. L6 / L7: tie the band WARN to the G-LENS record; gate the bolted-only margin or add a prying row.
4. L10 / L11: refuse an empty coupon map; source-link the coupons and the Fujinon run.
5. L9 / L12: gate or relabel mass_com; hash the tests; fix the README count.
