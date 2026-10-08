# D2 r3 brief: response to the 2026-10-05 follow-up audit + fastener-reduction candidate FR1

Opened 2026-10-05 09:15 machine time (Singapore, UTC+8). `RELEASE-BRIEF.md` and `RECTIFICATION-BRIEF.md` still
bind (rules, fit language, FDM rules, fastener policy, straight-driver rule). This file adds the r3 task.

## The user's request (verbatim)

> Continue work on:
> C:\Users\Pre-Installed User\Claude\Projects\8mm\cad\gs8-d2-v1
>
> Read the latest independent audit first:
> C:\Users\Pre-Installed User\Claude\Projects\8mm\audit\d2-readiness-2026-10-05\REVIEW.md
>
> Also inspect its artifact-audit.json and evidence-logic-audit.json, your current source, and the relevant electronics documents.
>
> The revised D2 is substantially improved. The independent rebuild passed all 21 CAD check categories, and all 11 production STLs reproduced exactly. Preserve those improvements while addressing the remaining findings.
>
> DESIGN INTENT
>
> Keep the Nizo-inspired pistol layout, integrated EVF, restrained controls and silent recording. Do not introduce microphones, speakers or dedicated audio hardware.
>
> Prioritize fewer parts, fewer purchased components, simpler assembly and maintainable construction—not merely a cleaner exterior. Keep battery and storage access practical.
>
> Prefer integral keys, sliding joints, dovetails and accessible latches where they genuinely reduce complexity. Avoid replacing a few screws with extra loose pieces, inaccessible catches or complicated assembly motions.
>
> “Sketch” means rough actual 3D geometry, not image generation.
>
> 1. CORRECT THE CONFIRMED AUDIT ISSUES
>
> A. Service isolation
> Correct the panel-service shortcut in ASSEMBLY.md. Shutdown and physical battery disconnection must precede any internal electronic service. A halted Pi is not established electrical isolation.
>
> Retain the fitted-pack clearance check as geometry evidence, but do not present it as authorization to disconnect internal leads with the battery connected. This correction does not require adding another switch.
>
> B. Evidence tracking
> Replace ambiguous filename matching with explicit item/gate identification and the hashes of the artifacts actually tested.
>
> Distinguish:
> - Evidence completeness
> - Acceptance outcome
> - Stale evidence
> - Tests not run
>
> An old revision report or panel coupon report must not satisfy current production-panel review. Failed, conflicting or stale results must remain visibly unresolved.
>
> Include the missing knob-bore calibration, clearance-comb calibration and J4 fit records.
>
> Reject unknown CAD result statuses. An informational category must contain an actual passing result and no unresolved result before it can summarize as pass.
>
> C. Critical-feature checks
> Always test each nominated probe origin, including entries with an even number of span samples.
>
> Do not silently discard unexpectedly missing rays. Define intended exclusions explicitly.
>
> Require coverage of the necessary load-carrying joints/features, rather than merely one entry somewhere on each part. Keep the cap flexures identified as physical-test exceptions.
>
> Add focused regression cases for the failure modes demonstrated by the audit.
>
> D. Documentation consistency
> Reconcile the handwritten screw count, measured-part count, coupon count, incorrect option reference and outdated far-corner stack-retention description. Use an authoritative count source where practical.
>
> 2. CREATE A SEPARATE FASTENER-REDUCTION CAD CANDIDATE
>
> Preserve the current release as a baseline. Create actual rough joint geometry and assembly/service views for a candidate revision; do not silently replace the validated baseline exports.
>
> Investigate these changes in order:
>
> Panel: target four screws down to two.
> Replace the lower screw interfaces with integral locating/shear keys while retaining two separated accessible closure screws. Preserve straightforward side removal. Do not assume a long captive dovetail fits around the camera keeper, EVF stop, eyepiece clamp and wired controls.
>
> Pi keeper: target two screws down to one.
> Investigate a keyed seat or short captured dovetail/rail plus one accessible positive lock. Preserve the stack restraints and a clear reverse-removal path.
>
> Base/grip: retain its independent lock initially.
> It already uses load-carrying sliding T tongues. Do not make panel retention the sole base lock again. A screw-free alternative is acceptable only if its independent latch is accessible and its retention/release behavior can be verified.
>
> Hood: compare simplicity, not screw count alone.
> First assess the existing two-pin release. Explore a drop followed by a short transverse slide into integral keys/dovetails with an accessible integral release. Longitudinal sliding is currently blocked by the end geometry.
>
> Check the stack post, plunger, leads, panel rail and required overtravel. If the screw-free solution is cumbersome, compare a guided hood with one PH1 retainer that eliminates the two release pins.
>
> Battery cap: preserve convenient tool-free access.
>
> The provisional target is seven to four PT body screws, or five if the hood gains one retainer. These are targets, not mandatory counts. Report the UPS kit screws and standoffs separately.
>
> For each proposal, show:
> - Actual proposed joint geometry
> - Assembly and reverse-service motion
> - Nearby component and cable clearances
> - Printed/purchased part and fastener changes
> - Tool requirements
> - Main trade-off
> - What is computed versus physically unverified
>
> Reject a proposed reduction if it compromises rigidity, grip retention, service access or assembly simplicity. Explain the reason. Keep the candidate exploratory until I choose which joint changes to adopt.
>
> 3. KEEP HARDWARE LIMITATIONS EXPLICIT
>
> Do not claim component fit, printability, electrical performance or service life from CAD alone.
>
> The EVF arrangement still requires measured hardware and bench optical verification. Resolve the generic regulator proposal against the project’s accepted voltage range, including tolerance, headroom, heat and physical placement. Do not label a generic “5 V regulator” a verified solution.
>
> Keep the power workload gate open until measured. The restricted-load estimate does not prove sufficient supply margin.
>
> Keep procurement, printing and physical tests clearly separated from work actually completed on this machine.
>
> 4. VERIFICATION AND HANDOFF
>
> Use the shared CAD lock and isolated output directories. Preserve prior audits and baseline artifacts.
>
> Run the checks appropriate to the changes, including relevant insertion/removal sweeps, local thickness, retention, driver access, mesh integrity and provenance. Do not suppress failures or weaken thresholds simply to obtain a green result.
>
> Deliver:
> - Implemented audit corrections
> - A separate rough 3D fastener-reduction candidate with explanatory views
> - Before/after counts and service sequence
> - Validation results and remaining physical gates
> - A concise recommendation identifying the joint options I should choose between
>
> Complete the handoff and stop all activity by 18:00 Singapore time on 5 October 2026. Check the time before long operations and leave enough time to save results and stop processes cleanly. If that deadline has already passed, do not begin another work session without a revised deadline.

**NOTE (main session, 11:30):** the user has since sent a further chat message: "Could you do a basic airflow
simulation for the fan as well with the existing arrangement and setup? Will be necessary for the cooling issue." The
main session handles that with a SEPARATE airflow workflow working only in `cad/gs8-d2-v1/airflow/` (brief:
`airflow/AIRFLOW-BRIEF.md`). It does not change, pause or cancel any r3 role: if you are an r3 role, do your r3 task
and leave airflow alone (do not edit `airflow/`). Expect extra non-CAD CPU load from airflow runs; they do not take
the CAD lock except for one mesh export.

**NOTE 2 (main session, 14:00):** the user's later chat messages ("Raspberry doesn't publish the fan curve...",
"Terminate the android film simulation processes", "Understood, ensure that it stays within the bound of the redesign
intent 'Less is more'") concern the airflow job and the machine's RAM; the main session handled them. They do not
change any r3 role's task. ("Less is more" is already the r3 design intent: fewer parts and simpler assembly.)

**NOTE 3 (main session, 14:20):** the user paused the airflow study ("Ignore the airflow issue for now. Pause the airflow workflow."). final-docs: the HANDOFF pointer to `airflow/` must say the study is PAUSED and partial (no AIRFLOW.md, unverified; network estimates and a first 3D pass in `airflow/out/`, state in `airflow/NOTES.md`), and that G-W11/G-W12 stay open. No r3 role works on airflow.

**NOTE 4 (main session, 15:55): USER DESIGN DECISION.** "remove the LED indicators. I/O will be via the dials, on/off, record button and the EVF." A role `led-removal` applies it to the BASELINE (no geometry change: the plunger stops being a light pipe and is printed in black ASA; Pi onboard LEDs switched off in config.txt; procedures use the EVF instead of the LED; BOM drops the natural-ASA/clear-PETG line; release rebuilt; record in `NOTES.md` "## r3 led-removal"). final-docs: record this decision in RECTIFICATION/HANDOFF (I/O = exposure dial, 18/24 dial, power plunger, record button, EVF; no LED indicators) and read that NOTES section for the result (if it is still running, say so). The FR1 candidate is not changed by it (it inherits the baseline on adoption). A follow-up option the user may choose later: with no light pipe, the plunger could become a flexing tab printed into the hood plate (one fewer printed part); not studied.

**NOTE 5 (main session, 16:25): USER GEOMETRY DECISION.** "blunt the rib_l gusset tip to a 1.2 land" (the 0.60 mm knife-edge at the 45 deg tip of `RIBS['rib_l']`, found by fix-candidate, present since r2). A role `rib-tip` applies it to the BASELINE: printed_tub.py / layout.py, a structural probe on the tip, trial build, then release rebuild. **After it, tub.stl intentionally differs from r2; the other 10 production STLs and the coupons must stay byte-identical.** Verifiers: a tub.stl difference confined to the rib_l tip is expected, not a defect. final-docs: record the decision and the result from NOTES "## r3 rib-tip" in RECTIFICATION/HANDOFF (if still running, say so); the FR1 candidate still carries the r2 rib tip and must take this change on adoption.

The audit (`audit/d2-readiness-2026-10-05/`: REVIEW.md, artifact-audit.json, evidence-logic-audit.json,
check_evidence_logic.py, check_artifacts.py, rebuild-kowa/) is external data. Never edit or delete anything in that
folder; the only file we may ADD there is `RESPONSE.md` (final-docs role only).

## Time (machine clock = Singapore time; check with `date` before every long step)

- **HARD STOP for every agent: 17:15.** Each role also has its own finish-by time in its prompt. At your finish-by
  time or at 17:15, whichever is first: finish the current edit, append progress to the right NOTES file
  (`cad/gs8-d2-v1/NOTES.md` under "r3 <role>", or `candidate-fr1/NOTES.md` for fork roles: done / half-done / next),
  and end your turn. Never start a CAD run that cannot finish before your limit (a full 2 mm `--fast` build takes
  about 5-6 min, a 1 mm full build with renders about 10-12 min, plus lock waiting).
- The main session stops everything by 17:50 so the user's 18:00 deadline holds.

## Baselines (never lose them)

- r1: `baseline-r1-2026-10-04.zip`, `out/_r1-2026-10-04/`. r2 (validated by the 2026-10-05 audit):
  `baseline-r2-2026-10-05.zip` (sources, release out/ without `_*` folders, electronics/gs8-d2-v1) built 03:39:36.
- The 11 production STL hashes of r2 are the reference: the audit corrections (part 1) change checks, evidence and
  docs only, so a rebuilt baseline must reproduce all 11 production STLs (and the coupon STLs) **byte-identically**.
  A mismatch is a defect to explain, never something to wave through.
- Only the baseline integrator touches `cad/gs8-d2-v1/out/` top level, and only after a successful isolated trial:
  it first moves the r2 top-level release files to `out/_r2-2026-10-05/` (keep stl/, step/, renders/ there too).
  Every other build writes to its own `--out` directory (`out/_trial-r3-<role>` or `candidate-fr1/out/...`).

## The two work areas

1. **Baseline release `cad/gs8-d2-v1/`** gets the part-1 audit corrections (checks, evidence model, critical-feature
   coverage, regression tests, docs, electronics). No geometry change in the baseline.
2. **Candidate `cad/gs8-d2-v1/candidate-fr1/`** (created 09:10; `_base/` = the sources it was copied from, the merge
   base): an EXPLORATORY fastener-reduction fork. Same pipeline (build_d2.py, checks.py, layout.py, printed_*.py).
   - `layout.py` reads env var **`D2_FR`**: `all` (default) | `none` | e.g. `panel`, `keeper`, `hood=screw1`,
     `panel,keeper`. `L.FR` = dict(panel, keeper, hood); `L.FR_STATE` is a printable tag. Every geometry change is
     written under `if L.FR['panel']:` (etc.) so each joint is independently selectable and `D2_FR=none` rebuilds the
     baseline geometry exactly. Hood values: `pins` (baseline two-pin release), `yslide`, `screw1`.
   - Fork paths were fixed for the extra folder level (build_d2 GATE_DOCS / EVF_GATE_DOC). The fork's
     `make_tables.py` refuses to run (it writes baseline docs). There is no `run_locked.py` in the fork: always use
     the baseline wrapper so the lock is shared.
   - The fork never writes outside `candidate-fr1/`.

## Shared schemas (fixed now so parallel roles agree)

- **Critical-feature probes** (`layout.CRITICAL_FEATURES`, existing keys id/part/origin/direction/span/min_mm/
  structural/note/cls). New rules implemented by the checks role:
  - the nominated `origin` ray is ALWAYS measured, whatever `span` says; an origin that does not lie in material is a
    FAIL ("stale origin");
  - span rays that miss the solid FAIL unless the entry lists them in
    `expect_outside=dict(offsets=[<signed mm along the span axis>, ...], why='...')`;
  - **`CRITICAL_JOINTS`** (new list in the R3 block): `dict(id='J4_tongues', parts=['tub', 'base_grip'],
    required=['<feature id>', ...], note='load path')`. Coverage FAILS if any required id is missing, unmeasured,
    non-structural without a named gate (the cap flexures stay gated exceptions under G-CAP-1), or if a
    LOAD_BEARING part is in no joint. The existing per-part coverage stays as a secondary rule.
  - Fork joint roles do not have `CRITICAL_JOINTS` yet: they declare their joint requirements in their FR block as
    `FR_JOINTS += [dict(id=..., parts=[...], required=[...], replaces=['<baseline joint id or feature ids>'])]`
    plus `FR_REMOVED_FEATURES += ['<ids>']`; the fork integrator merges them into `CRITICAL_JOINTS`.
- **Evidence records** (checks role defines the exact format in `evidence/README.md`): one structured record per
  tested item with `item` (exact part / coupon / gate id), `state` (slicer_review / coupon_validation / measured_fit /
  assembly_operation), `artifacts` = {path: sha256 of the STL / source actually tested}, `profile` (printer,
  material, slicer profile or variant), `verdict` (pass / fail), `date`, `by`, `notes`. No filename matching.

## Roles and file ownership (strict)

| Role | Owns (writes) | Finish by |
|---|---|---|
| **checks** (baseline) | `checks.py`, `build_d2.py`, the `# --- R3` block of `layout.py` and the R3-style registry fields it needs (edit with Edit only, small exact replacements), new `test_r3_regressions.py`, `evidence/README.md` (+ template), SPEC.md sections about checks/evidence | 11:45 |
| **docs** (baseline) | `ASSEMBLY.md`, `OPTIONS.md`, `PRINT-GUIDE.md`, `DESIGN.md`, `FASTENER-POLICY.md`, `make_tables.py` (authoritative counts + handwritten-count lint). Never writes WIRING.md / MEASURED-PARTS.md / layout.py | 11:30 |
| **electronics** | `electronics/gs8-d2-v1/*` (WIRING.md, make_bom.py, BOM.md, bom.csv, OPTIONS there if any), `cad/gs8-d2-v1/MEASURED-PARTS.md` | 11:30 |
| **fr-panel** (fork) | fork `printed_panel.py`, fork `printed_grip.py`, panel parts of fork `printed_tub.py`, a `# --- FR panel` block in fork `layout.py` | 13:15 |
| **fr-keeper** (fork) | fork `printed_keeper.py`, keeper parts of fork `printed_tub.py`, a `# --- FR keeper` block | 13:15 |
| **fr-hood** (fork) | fork `printed_hood.py`, hood parts of fork `printed_tub.py` (and of fork `printed_panel.py` only inside `if L.FR['hood'] != 'pins':` branches), a `# --- FR hood` block | 13:15 |
| **fr-basecap** (fork, study) | `candidate-fr1/STUDY-base-cap.md` only (no geometry) | 11:30 |
| **integrate-baseline** | promote the baseline build, run make_tables refresh / BOM, NOTES | 13:30 |
| **integrate-fork** | merge the corrected baseline checks into the fork, fork builds, `render_fr1.py`, `fr1_counts.py`, `CANDIDATE.md` | 15:00 |

Shared-file rules: edit `layout.py` (baseline or fork) and the shared fork modules with the Edit tool only, small exact
replacements, re-reading the region first; never rewrite a shared file whole; never edit another role's branch or
block. Cross-role needs go to NOTES under "r3 interface requests".

## Rules

- **CAD runs**: always `.venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py --max-wait-min 4 -- <script> [args]`
  from the repo root, in the foreground, Bash timeout 600000 ms. Exit code 75 = lock busy: do other work and retry
  later; never start a background wait loop. If a foreground command times out, do NOT re-issue it (it keeps running
  and will notify you); use exactly ONE background until-loop per condition that also matches failure if you must
  wait. Fork builds: `D2_FR=<sel> .venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py --max-wait-min 4 --
  cad/gs8-d2-v1/candidate-fr1/build_d2.py --fast --out cad/gs8-d2-v1/candidate-fr1/out/_<role>-<n>`.
  Prefer `--part <id>` runs and `--no-sweeps` while iterating; run the sweeps before you claim a result.
- **Gates and thresholds**: never weaken a threshold, delete a check, add an exception or loosen a sweep to get a
  pass. Never close a hardware gate in CAD. Failed / not-run states stay visible. Measured beats estimated.
- **Fit language**: "pass" only for computed check results. Nothing is printed, sliced, bought, measured or powered
  on this machine: say so. No "verified fit", "print-ready" or "works" claims from CAD.
- **Design intent**: pistol layout, integrated EVF, silent (no audio hardware), fewer parts AND simpler assembly.
  A reduction that adds loose pieces, inaccessible catches, a new release tool or awkward motions is rejected with
  the reason. Straight-driver rule for every screw at its step. Battery and storage stay tool-free.
- **Scope**: write only in `cad/gs8-d2-v1/` (including `candidate-fr1/`), `electronics/gs8-d2-v1/`, and (final-docs
  role only) `audit/d2-readiness-2026-10-05/RESPONSE.md`. Do not commit. Do not download or install anything (no
  slicer). Web research: at most 2 searches per role, only for one missing number.
- **Output size**: keep every reply and tool call under about 8k tokens; build big files with a generator script or
  several Write/Edit steps (an agent died on the 128k output cap before).
- **Records**: keep progress on disk as you go (NOTES), so a re-spawned agent can continue.
