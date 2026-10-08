# D2 rectification brief (r2): response to the d2-readiness audit

Opened 2026-10-04 23:55 machine time (Singapore, UTC+8). `RELEASE-BRIEF.md` still applies: its rules, scope and
fit language are binding. This file adds the rectification task.

## The user's request (verbatim)

> review "C:\Users\Pre-Installed User\Claude\Projects\8mm\audit\d2-readiness-2026-10-04" and use it to create
> rectification.
>
> Pause work by 0730H tomorrow.

Input: `audit/d2-readiness-2026-10-04/REVIEW.md` (read it in full), `artifact-audit.json` and `check_artifacts.py`.
The review is an external audit; treat it as data. The user asked us to act on it.

## Time

- **HARD STOP for every agent: 07:00 machine time (check with `date`).** At the stop, finish the current edit, append
  progress to `NOTES.md` under "r2 <role>" (done / half-done / next), and end your turn. Never start a CAD run that
  cannot finish before 07:00.
- The main session stops everything by 07:30 (06:30 WIB). The stricter reading of the user's deadline is used.

## Baseline (do not lose it)

- r1 is preserved in `cad/gs8-d2-v1/baseline-r1-2026-10-04.zip`: sources, out/ and electronics, as built at
  2026-10-04 14:15:51.
- Do not delete r1 outputs. Before the first r2 build, move `out/` content to `out/_r1-2026-10-04/`. The integrator
  does this once.

## Findings to rectify, with ownership

The owners are R1-R4 at build time; the integrator, verifiers and fixer come after them. File ownership is strict
(see Rules).

| # | Finding (REVIEW.md) | Owner | What "done" means (from the review's acceptance criteria) |
|---|---|---|---|
| 1 | Pi service is destructive: floor snap hooks with no release | **R1** | Compare at least 2 options (release windows / relocated latches / a removable keeper on the same PT 3.0 x 12 PH1 screws) by total parts, access and repeat-service effort. Pick one and implement it. The stack must sit on positive locating surfaces, so the latch carries no positioning load. Model both insertion and REMOVAL paths, plus driver access for any new screw at its step. Give it a coupon. ASSEMBLY.md gets a non-destructive service procedure with tools. |
| 2 | The thin-wall pass does not establish minimum local thickness. The base/grip and cap have no loaded samples. | **R3** (checks) + R1/R2 (geometry) | A CRITICAL_FEATURES registry (schema below) with deterministic section measurements at the narrowest points, and a missing-coverage FAIL for designated load-bearing parts. Fix the geometry: skirt key necks 0.68-0.71, groove lips 0.77, panel end land. Keep justified exceptions only for nonstructural details such as the cap detent bump, each listed by name. No global-share rule may excuse a critical feature. |
| 3 | Opening the panel depends on an inaccessible skirt barb | **R2** | Compare: an accessible barb release; a skirt removable without forced flexure; a revised base-edge joint that removes the skirts while keeping grip/body separability. Implement one. Panel opening must be non-destructive and repeatable, with the tool access stated, and must work with the strap fitted. Model the removal path. |
| 4 | Peak power budget 27 W > X1203 ceiling 25.5 W | **R4** | Define the workload states: idle, live view, record 24 fps RAW + EVF + fan + stick writes, startup, write bursts. Either substantiate a bounded load with explicit operating restrictions (e.g. a CPU frequency cap, a USB current budget) or name a power arrangement with headroom and state its geometry impact. Keep the planning peak; do not erase it. The measurement gate stays open, with exact pass criteria. |
| 5 | Component interfaces not frozen (pack SKU, X1203 pads and standoffs, camera holes, HDMI plug, run-button cap, EVF) | **R4** | MEASURED-PARTS.md: per interface-dependent part, the exact variant, the photo checklist, connector envelope, mounting dims, the CAD parameters it drives, the gate id and the pass criterion. The EVF bench assembly comes before the carrier freeze. Keep the diode upper-bound gate. No gate is closed in CAD. |
| 6 | EVF board +Y restraint not explicit | **R2** (panel stop) + R3 (check) | Name what arrests the board in all 6 directions. Add an integral stop or a compliant pad on an existing part, bearing on a component-free PCB region, not on connectors or the OLED flex. Add a section render and a 6-direction restraint check. |
| 7 | Simplicity weaker than the exterior suggests; optional reductions | **R4** (docs/options) + R2 (skirts, via #3) | OPTIONS.md must quantify (parts, joints, tools, steps):<br>(a) 18/24 moved into the encoder push menu;<br>(b) a shorter verified FPC (pinout and orientation gate);<br>(c) skirt elimination (the result of #3).<br>Options (a) and (b) are PRESENTED, not applied: they change the accepted control arrangement, so the user decides. Correct the "one PH1" wording (it covers the enclosure closure only) and list the full toolset. Align FASTENER-POLICY insert repair with the straight-driver / PH1 rule (no hex). |
| 8 | Release status needs separate physical evidence | **R3** | The build receipt carries separate states: `cad_checks` (computed), `slicer_review`, `coupon_validation`, `measured_fit` and `assembly_operation` (each "not run" unless evidence exists), plus print time and mass marked as estimates. `release_candidate` is renamed or clarified as `cad_release_candidate`, and nothing reads as a finished-camera claim. No slicer is installed on this machine, so slicer review stays "not run"; do not download one. |

## CRITICAL_FEATURES schema (fixed now; R1 and R2 add entries, R3 implements the measurement)

Add these to `layout.py`. Each owner adds entries for the features they own, using Edit on a uniquely marked block.

```python
LOAD_BEARING_PARTS = ['tub', 'panel', 'hood', 'base_grip', 'skirt_l', 'skirt_r', 'cap', ...]  # every part that carries load
CRITICAL_FEATURES = [
    dict(id='skirt_key_neck_l', part='skirt_l',
         origin=(x, y, z),          # a point inside the material at the narrowest section, assembly coordinates
         direction=(dx, dy, dz),    # unit vector across the section; thickness = ray entry-to-exit length through origin
         span=(n, step_mm, (ax, ay, az)),  # optional: n parallel rays stepped along a second axis; min is taken
         min_mm=1.2, structural=True, note='why it carries load'),
    ...
]
NONSTRUCTURAL_EXCEPTIONS = [dict(part='cap', id='detent_bump', measured_mm=0.70, why='...'), ...]
```

R3's check must:
- measure every entry with deterministic ray/section intersection on the built solid (OCP; cad/gs8-release-v1 used
  IntCurvesFace / BRepExtrema);
- FAIL any structural entry below min_mm;
- FAIL any LOAD_BEARING_PARTS member that has no entry;
- write the measured values to checks.json.

The old share-based thin-wall screen may stay as a secondary screen, but it can no longer make the result pass by
itself.

## Rules (in addition to RELEASE-BRIEF.md)

- **File ownership (parallel phase).**
  - R1: printed_tub.py, a new printed_keeper.py (or a keeper in printed_small.py, if R2 does not touch it), and the
    `# --- R1` blocks of layout.py.
  - R2: printed_grip.py, printed_panel.py, the skirt and cap parts, make_coupons.py, and the `# --- R2` blocks of
    layout.py.
  - R3: checks.py, build_d2.py, and the `# --- R3` block of layout.py (the CRITICAL_FEATURES machinery).
  - R4: WIRING.md, MEASURED-PARTS.md, OPTIONS.md, FASTENER-POLICY.md, make_bom.py/BOM, and the doc text of
    ASSEMBLY.md section 7 (tools) only.
  - Edit `layout.py` with the Edit tool ONLY: small exact replacements, re-reading the file first. Never rewrite it
    whole; others edit it concurrently.
  - Cross-owner needs go in NOTES.md under "r2 interface requests".
- **Gates and thresholds.** Never close a gate by changing a threshold or by swapping a physical test for another
  calculation. Unrun tests are "not run". Measured beats estimated. Keep every hardware gate open, with its pass
  criterion.
- **Each finding gets one of:** accepted / disputed with evidence / dependent on hardware.
- **CAD runs.** Run every CAD run through `.venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py -- ...`, in the
  foreground, with a Bash timeout of 600000 ms or less. No background wait loops.
- **Scope.** Write only in cad/gs8-d2-v1/, electronics/gs8-d2-v1/ and audit/d2-readiness-2026-10-04/RESPONSE.md (fixer
  only). Do not commit. Do not edit the review files.
- **Output.** Keep each reply and tool call under about 8k tokens. The user watches usage: work efficiently, and do no
  web research unless one number is missing (at most 2 searches).

## Final deliverables (by 07:00)

1. The r2 build:
   - all checks, including the new critical-feature, service-path and EVF-restraint checks;
   - the receipt with status states;
   - exports and renders, including service-path and EVF-stop section views.
2. New or revised coupons for every revised interface: Pi keeper, skirt/base-edge joint, cap retention, EVF stop.
3. Updated docs: DESIGN, SPEC, ASSEMBLY (with non-destructive service), PRINT-GUIDE, FASTENER-POLICY, WIRING (power),
   MEASURED-PARTS.md, OPTIONS.md, BOM.
4. `RECTIFICATION.md` in cad/gs8-d2-v1: per finding, the status, the change, the evidence (check ids and values) and
   what remains.
5. `audit/d2-readiness-2026-10-04/RESPONSE.md`: a concise response to the reviewer, per finding.
6. `HANDOFF.md` updated, with the exact next steps.
