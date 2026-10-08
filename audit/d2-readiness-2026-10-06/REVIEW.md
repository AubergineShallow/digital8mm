# GS8 D2 r5 audit (heavy-lens support, J7-R float)

**The r5 release is reproducible and its computed checks can be trusted for the geometry as modelled. The camera model now matches the GS drawing, and the lens never loads the camera at any back-focus setting tested. One physical weakness is serious enough to fix before printing the collar: the ASA split collar has almost no elastic follow-up, so heat or creep can let the clamp go slack.** There are no blockers. There are 3 major findings, about 20 minor and a set of notes. Most of the minor findings repeat or extend the internal r5 review (G1-G9, A1-A8, F1-F6) that HANDOFF s0 already schedules.

Reviewed 6 October 2026, 22:10-22:45, against the 16:32:38 release. Nothing has been changed since the 17:05 wind-down. This audit was read-only for every design file. Instructions in project documents were treated as source material. Nothing was printed, sliced, measured or bought.

Detailed notes, numbers and file:line evidence: [notes-geometry.md](notes-geometry.md) (X1-X9), [notes-builder.md](notes-builder.md) (B-1 to B-14), [notes-logic.md](notes-logic.md) (L1-L12).

## Independent verification

| Check | Result |
|---|---|
| Provenance | 17/17 source, 101/101 output and 4/4 gate-document hashes match ([artifact-audit.json](artifact-audit.json), [check_artifacts.py](check_artifacts.py)). The Fujinon checks file is the one the receipt hashes. |
| Meshes | All 57 STLs (production, coupons, modifiers) are watertight, consistently wound, positive volume, and linked by the receipt. Against r4: tub, hood, panel and one coupon changed; collar, 3 collar coupons and 3 tub modifiers are new. This matches HANDOFF s0. |
| Independent rebuild | Kowa, `--fast --sweep-step 1.0`, through `run_locked.py` into `rebuild-kowa/` (484.6 s). **27/27 categories, 0 stubs, `cad_release_candidate` true; all 12 production STL hashes match the release exactly; the source hashes are identical.** |
| Tests | `test_r3_regressions.py` 38/38; `make_tables.py --check` stale none, lint 0. |
| Planted faults | 30 probes on the pure-logic functions, 17 caught as expected. The misses are findings L1-L4 and L10 ([logic-audit.json](logic-audit.json), [logic_planted.py](logic_planted.py)). |
| Geometry recompute | Float gaps were recomputed from the STLs against an analytic GS camera model ([geo_float.py](geo_float.py)) and agree within 0.02 mm. The slip and knock moments (0.170 / 0.286 N m) and the balance (Kowa 895 g at +1.47 mm; Fujinon 782 g at -9.76 mm) recompute exactly ([geo_clamp.py](geo_clamp.py)). The collar gives no vignetting, and the focus and iris rings stay accessible. |

## Major findings

### M1. The collar clamp has no spring (X1, NEW)

The split ring is solid ASA, 73.5 mm2 of hoop section, pinched by one M3. The ring is the stiffest-acting compliance only in the wrong sense: the elastic radial interference at the modelled 60-120 N is 0.009-0.017 mm. Heating from 20 to 50 C, the G-W11 condition, opens the bore about 0.046 mm relative to the aluminium band (ASA about 95e-6/K against 23e-6/K). That equals a hoop-tension loss of about 270-320 N, more than the 0.2 N m pinch can supply (about 220-330 N). The relaxed model state of 60 N goes slack at roughly +7 K. ASA creep at 50 C acts in the same direction.

Once slack, the lens can tilt about 0.9 deg over its 5.4 mm band. That is 0.5-0.8 mm at the catches, the same size as the 0.4-0.8 mm float gaps. Lens-down, the stack then slides onto the lip, and the camera joints carry the lens again: the condition r5 exists to remove. `check_lens_clamp` has no thermal or creep term, and G-COL-1 does not ask for hot slip tests.

**Fix before printing the collar:**
- Add elastic follow-up: a disc-spring stack under s_c4, or a printed flexure lug, sized to keep at least 60 N through the 0.05 mm of thermal plus creep travel.
- Add a thermal and relaxation term to `check_lens_clamp`.
- Make G-COL-1 run its slip and knock tests at 50 C after a soak, with the collar assembled in production order (ears first, pinch last; X7).

PC or CF-filled filament reduces the mismatch but does not replace a spring. The current "PC if G-W11 finds over 50 C" fallback can't trigger in time (B-8): G-W11 runs after full assembly, and it does not measure near the camera.

### M2. The print order allows body parts before the camera is measured (B-1, extends G3)

PRINT-GUIDE s7 (lines 218-227) and the HANDOFF "do first" list (lines 46-51) let the tub, hood and panel be printed before MP-CAM / G-CAM-1. Only MEASURED-PARTS:13 states the dependency. All three parts carry camera-derived features, and the float gaps sit exactly at their rules (body 0.40 axial, BFAR 0.50).

The tub, hood and panel STLs are byte-identical between the Kowa and Fujinon builds. So the *camera* measurement, not the lens, gates the body prints. G-LENS gates only the collar and, through `LENSES` x0/x1, the axial position (X3: the band chamfer alone moves the seat ±0.3 mm on the 45 deg cone).

**Fix:** one ordered gate list in PRINT-GUIDE s7 and HANDOFF: MP-CAM, then rebuild, then the body prints; G-LENS, then rebuild, then G-COL-1 coupons, then the collar print.

### M3. None of the D2 fork is under version control (process, NEW)

`git ls-files` returns 0 files for `cad/gs8-d2-v1`, `electronics/gs8-d2-v1` and `concepts/`. That is 540 MB across five revisions (r1-r5) in two days, kept only as baseline zips and `out/_rN` copies. Every receipt states "no git commit". A lost or overwritten working tree would lose the whole fork, and reviewers cannot diff revisions. Large outputs could go in Git LFS or stay ignored. The sources, docs and receipts are small.

**Fix:** commit the sources, docs, receipts and checks.json on `codex/evf-design` or a dedicated D2 branch, after the user approves.

## Minor findings

**Geometry and physics**
- **X2, NEW:** nothing centres the collar on the tub lip; only screws in 3.4 mm clearance holes locate it. The worst-case lateral offset is 0.60 mm (RSS 0.31) against the 0.75 mm BFAR gap. Add two locating feet or an assembly centring plug.
- **X4, confirms G1/G2:** at s_nom 1.25 the datum chain puts the image plane at or behind the PCB front, which is impossible. Back-focus screw-out past 3.0 (real travel is about 4.9) would drive the cover into the keeper. Add the sensor datum, and measure C flange to cover rear at MP-CAM.
- **X5, confirms G4; B-6:** 0.25 N m on short heat-set inserts gives 280-420 N, close to their pull-out strength. "By hand" will exceed it. Use 0.12-0.15 N m and add a torque driver to the BOM.

**Builder readiness**
- **B-2, NEW:** at a lens swap, the hand-tight C-CS adapter can come out with the lens. The next C lens then threads 5 mm deeper, and its 6.7 mm rear protrusion can hit the filter. Mark the adapter at B0 and check the mark at every swap.
- **B-3, NEW:** each M3 x 10 collar screw ends 0.18-0.2 mm short of its blind-bore floor. With normal length tolerance it can bottom out before the head seats. Deepen the 3.2 mm relief by 0.5 mm, which stays inside the -7.6 mm limit.
- **B-4, confirms A4:** B0 hangs the 215 g lens on a bare camera, contrary to the r5 rule, and gives no live-view setup.
- **B-5, confirms A5:** step 8 says to back s_c4 off before s_c4 has ever been fitted.
- **B-7, NEW:** the lens-swap steps hold the camera by its cover or against the roll fin. Lens thread torque then passes through the housing-to-PCB joint. Specify holding the collar or the lens band.
- **B-9 / B-10, NEW:** stale counts.
  - evidence/README: 11 printed parts, 7 tub modifiers and no G-COL-1; it should be 12, 10 and G-COL-1 present.
  - PRINT-GUIDE:45: hood infill 100 %; it should be 25 %.
  - DESIGN:284: 10 solder joints; it should be 12.

**Verification logic** (these let a *future* fault pass; none hides a current one)
- **L1, confirms F1:** a lens under 150 g with no collar passes `lens_support`, and a regression test asserts that pass. Make a lens without a collar fail and invert the test.
- **L2, NEW:** `j7_float` samples back focus only at 0, 1.25 and 3.0. A planted clash at 2.0 passed. Sweep at no more than 0.25 mm over the full measured range (see X4).
- **L3 / L4, NEW:**
  - A missing collar or lens solid drops its rows instead of failing.
  - The lens is checked only for overlap, so a 0-gap contact with the hood passes.
- **L5, NEW (disagrees with the review's "no r4 check weakened"):** duplicate probe IDs silently overwrite each other. That is how the r4 probe on the plain tub front wall disappeared, and that wall now sits under the compression-only LR foot. Reject duplicate IDs and restore the probe.
- **L6 / L7 (L7 confirms G5):**
  - The "band not measured" warning clears when a status string in `layout.py` is edited, not when a G-LENS record exists.
  - The anchor-polygon check passes only because of the LR foot. The bolted-only margin (-8.8) is reported but never checked. X6 judges this a note while the preload holds, but M1 is exactly the case where it doesn't hold.
- **L8, confirms F2:** a real `j7_float` fail is relabelled as a stub when any neighbouring part is a stub.
- **L10 / L11, NEW:**
  - A coupon gate missing from the manifest would accept any file.
  - The receipt cannot show that the coupons and the Fujinon run came from the current sources. Today they did.

## Notes

- X6: the prying pivot should be the LL-LR line.
- X8 / G9: the keeper gap at nominal s is 2.25 mm; the comment says 1.75.
- X9: the leveling range is about ±2.3 deg before the cover meets the roll fin.
- L9: `mass_com` passes whenever the mass is above 0, so no balance rule is enforced, even though BRIEF-D2 sets 0..+8 mm.
- L12: the tests and evidence/README are not hashed sources.
- B-11 to B-14: the service driver check skips s_c4 and s_j; the heat-set tip is unspecified; the PRINT-GUIDE dry fit spends a hood snap cycle; back the 2.5 mm front wall while heat-setting.

## What holds

- The premise correction in r5 is right, and the camera model matches the GS drawing.
- The back-focus direction is correct.
- The float gaps reproduce from the exported meshes.
- No r4 check category lost rows or status. L5 is a single probe, not a category.
- Builder documents carry no leftover r4 wording (pins, turret, front lands, the 36.5 bore).
- The collar screw and insert counts agree across the BOM, the manifests and the docs.
- The print totals (297 g / 16.0 h) and the 18 modifier meshes are consistent.

## Recommended sequence

1. Commit the D2 sources and records (M3, with approval).
2. Design in the clamp spring and thermal term (M1), the centring feature (X2) and the screw relief (B-3). Fold these into the scheduled G1-G5 / A1-A4 / F1-F3 fix list together with L2-L5.
3. Fix the print and gate order (M2), the stale counts (B-9 / B-10) and the swap and holding instructions (B-2, B-7).
4. Rebuild through the HANDOFF s9 sequence, then do the bench work: MP-CAM, then G-LENS, then the hot G-COL-1 coupons, before any body or collar print.
