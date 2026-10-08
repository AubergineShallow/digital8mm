# GS8 D2 r2 — follow-up audit, 5 October 2026

**Verdict: a meaningful improvement, suitable for slicer review and targeted coupon trials. It is still an unvalidated camera design.** The old destructive Pi retention, obstructing skirts and missing EVF stop have received real geometry changes. The more explicit physical gates are useful. Do not interpret passing CAD checks as permission to commit to the complete print set before the component interfaces and EVF arrangement are measured.

This is an audit and improvement brief for Claude, not a geometry revision. D2 source and release exports were left unchanged. The user's updated cutoff is **18:00 Singapore on 5 October**, superseding the earlier Batam countdown. The new preference for dovetails and fewer screws is incorporated below as proposed work, not verified fit.

## Evidence checked

Reviewed release: `cad/gs8-d2-v1/out/build-receipt.json`, built **2026-10-05 03:39:36 +0800**, against the previous 4 October audit and the revised source, instructions and exports.

- Independently recomputed **16 source hashes, 64 output hashes and 4 gate-document hashes**: all match.
- Independently loaded **11 production STL files and 24 coupon STL files**: all watertight, consistently wound and positive volume. Production inventory agrees with the print manifest; no leftover skirt STL is in the active production set.
- Ran `layout.py`: **129 checks, zero failures**. Ran `make_tables.py --check`: **no stale generated tables**. Handwritten documents still contain discrepancies described below.
- Supplied CAD results contain **21 passing categories, 526 passing rows and 6 informational rows**: 532 rows total, zero failed/stub rows. The informational rows are not physical passes.
- The supplied Fujinon 1 mm sweep receipt references the current source hashes, and its checks file matches the copy linked by the main receipt. This is provenance verification, not an independent Fujinon rebuild.
- Inspected the hero, exploded view and EVF board section. These are built CAD/proxy views; appearance does not establish fit or ergonomics.
- Independently rebuilt the Kowa geometry and ran the complete CAD checks with **1 mm insertion/removal sweeps**, through `run_locked.py`, into this audit folder. **All 21 categories passed; zero stubs; all 11 regenerated production STL hashes exactly match the supplied exports.** Runtime was 422 seconds. `--fast` omitted the full renders and STEP export; it did not skip thickness or sweep checks. Coupons were inspected from the supplied exports, not regenerated. [Independent rebuild receipt](<C:/Users/Pre-Installed User/Claude/Projects/8mm/audit/d2-readiness-2026-10-05/rebuild-kowa/build-receipt.json>).

Independent export evidence: [artifact-audit.json](<C:/Users/Pre-Installed User/Claude/Projects/8mm/audit/d2-readiness-2026-10-05/artifact-audit.json>). Reproduction script: [check_artifacts.py](<C:/Users/Pre-Installed User/Claude/Projects/8mm/audit/d2-readiness-2026-10-05/check_artifacts.py>).

No printing, slicing, procurement, measurement, electrical test or physical service trial was performed in this audit. All four physical evidence states correctly remain **not run** in the supplied receipt: slicer 0/11, coupon gates 0/6, measured fit 0/17 and assembly/operation 0/21.

## What happened to the previous eight findings

| Previous finding | Follow-up assessment |
|---|---|
| 1. Destructive Pi removal | **Addressed in CAD.** Floor hooks were removed; a separate screwed keeper and far-side hood stop now retain the stack. Access/removal checks exist. The hood's two release pins and complete service sequence still need physical trials. |
| 2. Thin-wall blind spots | **Substantially improved.** There are 87 structural probe entries, including 17 for the base/grip, 6 for the cap and 7 for the keeper, plus six part-coverage checks. Named cap flexures remain gated exceptions. The remaining coverage weaknesses below prevent calling this exhaustive thickness verification. |
| 3. Skirt blocking panel removal | **Addressed in CAD.** Both skirts are deleted. Panel removal is straight out; a separate base lock prevents that operation from freeing the grip/body joint. |
| 4. 27 W demand against 25.5 W supply | **Acknowledged and given a test plan, not physically resolved.** Restricted workload estimates and G-W12 are clearer. There is still no measured power margin. |
| 5. Unverified purchased interfaces | **Planning improved; fit remains open.** Measurement templates and EVF bench-first sequencing are appropriate. They are not measurements. |
| 6. EVF board restraint | **Addressed in CAD.** The panel stop is present and rails are relieved around connectors. Six-direction contact checks report PCB contact at roughly 0.25–0.31 mm. Actual board revision and fit still require G-EVF-2. |
| 7. Construction/control complexity | **Partially improved.** Two skirts removed, one keeper added: 12 → 11 prints. Screws increased 4 → 7 to make retention/service independent. Dedicated FPS control and nine-layer FPC fold remain. |
| 8. Over-broad release status | **Current wording improved.** `cad_release_candidate` and four physical states distinguish CAD from hardware. Future evidence ingestion still needs the corrections below. |

The release pins are already explicitly covered by the print guide and G-SNAP-2. I found no proved new hood collision and do not treat pin self-retention as an undisclosed defect. Test it early: its nominal 1.5 mm pin / 1.6 mm hole arrangement and spring contact are not a measured friction fit.

## Corrections worth making now

### 1. High priority: remove the battery-connected electronic service shortcut

[ASSEMBLY.md, line 267](<C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1/ASSEMBLY.md:267>) says panel-only EVF/encoder/camera/lead service starts at step 3 with the cap and pack fitted. That skips the shutdown and XT30 disconnection in step 1. Later steps unplug panel leads and EVF power/HDMI/flex.

The documented power button requests Pi shutdown; it is not a hard battery isolator. The instructions themselves acknowledge X1203 standby draw with the Pi halted. Downstream rail states are unmeasured, so the precise issue is **electrical isolation is not established**, rather than a claim that every connector must stay energized. The shortcut contradicts the pack-disconnection rule already present in the same document.

**Change:** make shutdown and physical pack disconnection a prerequisite to every electronic service path. The lens, eyecup and storage can remain fitted if their geometry permits. Preserve the loaded clearance check, but label it geometry-only. No additional switch is needed to correct the instructions.

**Acceptance:** someone following only the panel-service instructions disconnects the pack before unplugging any internal lead. Initial assembly and all reverse-service routes use the same prerequisite.

### 2. Medium priority: bind evidence to the actual item and revision, and keep failed tests visible

The current receipt is honest: there are no hardware results. The problem is how future results will be counted in [build_d2.py, line 680](<C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1/build_d2.py:680>).

- Filename token matching lets `base_edge_panel.md` and `old-panel-r1.md` count as evidence for the production `panel`.
- Hashing the report preserves the report's contents, but does not bind its result to the STL/source revision that was tested.
- A recorded `verdict: fail` counts as completed evidence. Once every item has a verdict, [the `open_evidence` calculation](<C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1/build_d2.py:1065>) removes the state from that list. It does not explicitly claim a hardware pass, but it can stop highlighting failed acceptance work.
- The six coupon gates omit explicit evidence requirements for the knob bore ladder, clearance comb and J4 tongue/keyhole fit, although the print guide requires those calibrations.
- `summarize(..., info_neutral=True)` accepts a nonempty unknown status such as `not run` as a passing category with zero passing rows. No such row is present in the current release; this is a future false-pass path.

**Change:** use structured records containing exact item/gate ID, tested artifact hashes, profile/variant, verdict and date. Track evidence completeness separately from acceptance (`pass`, `fail`, `stale`, `not run`). Register the three calibration records. Reject unknown CAD row statuses and require at least one actual pass for an informational category.

**Acceptance:** an r1 report or coupon report cannot close r2 production-panel review; failed and stale results remain visibly unresolved; all required calibration records appear; a category containing only `not run` cannot pass.

These behaviors and the probe-coverage cases below are reproduced in six isolated diagnostics: [check_evidence_logic.py](<C:/Users/Pre-Installed User/Claude/Projects/8mm/audit/d2-readiness-2026-10-05/check_evidence_logic.py>) and [evidence-logic-audit.json](<C:/Users/Pre-Installed User/Claude/Projects/8mm/audit/d2-readiness-2026-10-05/evidence-logic-audit.json>). Evidence fixtures use a temporary directory. Synthetic chord probes demonstrate checker behavior; they do not demonstrate a thin wall or stale origin in the actual hood.

### 3. Medium priority: make critical-feature coverage harder to lose accidentally

The new exact B-rep chord measurements are a substantial improvement over the old statistical screen. However, [checks.py, line 832](<C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1/checks.py:832>) uses evenly spaced offsets: an even-sized span does not include zero. `hood_groove_lower_lip` has a four-ray span, so its nominated origin is never checked despite the stated stale-origin rule. Noncentral rays outside the solid are silently skipped; one current EVF rail entry passes with one of three rays outside.

Also, [coverage at line 869](<C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1/checks.py:869>) requires at least one structural entry per load-bearing part, not a required set of joint/features. Deleting an entire joint's entries can leave that part green. The revised handoff admits this limitation; this audit has not demonstrated a new under-thickness part.

**Change:** always test the nominated origin; define expected valid spans, explicitly permit any intended outside samples, and require coverage for the load-carrying joints/features rather than only the parent parts. Add small regression cases for missing joint entries, stale origins and unexpectedly missing rays.

**Acceptance:** moving a required probe outside its feature or deleting all probes for a required joint fails clearly. Keep the cap's 1.25–1.50 mm flexures identified as G-CAP-1 exceptions, not ordinary 1.6 mm structural passes.

### 4. Low priority: reconcile the remaining handwritten counts

[OPTIONS.md](<C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1/OPTIONS.md:15>) still says six PT screws; the current model and BOM have **seven**, including `s_j`. It says nine measured-part records; there are **ten** including MP-FPC. [PRINT-GUIDE.md](<C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1/PRINT-GUIDE.md:135>) calls the coupon set 21 STLs in its heading, then correctly lists 20 + 4 below. [DESIGN.md](<C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1/DESIGN.md:23>) points to option (b) for the black band, but (b) is the shorter FPC.

Generate the shared counts or reference one authoritative table. A clean `make_tables.py --check` currently does not catch these handwritten mismatches.

Also update [ASSEMBLY.md, line 310](<C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1/ASSEMBLY.md:310>): it still describes far-corner stack tilt as an unaddressed geometry problem, although the hood stop has now been built. The accurate status is CAD restraint added, physical tilt/retention test open.

## Gates that still control whether a full camera print is sensible

**EVF first.** The separate panel, driver revision, flex and eyepiece arrangement remains the largest fit uncertainty. Follow the new bench sequence in [MEASURED-PARTS.md](<C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1/MEASURED-PARTS.md:97>) before freezing the rear carrier. The document expects the existing diode feed to fail its upper-voltage gate. A generic regulator contingency is not a selected, packaged solution: define output tolerance, dropout/headroom, load, heat and its physical envelope against the project's accepted 4.25–4.90 V range. The BOM's generic “5 V regulator” wording needs reconciling with that maximum. This is a critique against the project's own electrical limits, not a new vendor specification claim.

**Power remains a bench result.** [WIRING.md](<C:/Users/Pre-Installed User/Claude/Projects/8mm/electronics/gs8-d2-v1/WIRING.md:75>) correctly retains 27 W versus 25.5 W. The proposed 17.7–22.1 W restricted workload is an estimate, and the uncapped case has little margin to its test limit. G-W12 now has useful measurable criteria. Run them on the actual stack/loads; a fallback 2S pack plus generic converter is another design, not a verified drop-in replacement.

**Fit and print process remain open.** Measure the chosen pack, X1203 stack/pads, plugs, switch, camera mounting interface and EVF. Slice every final production part in its intended material/orientation. Run the keeper, hood, panel, cap, EVF and fastener coupons plus the calibration records above. Mesh watertightness says nothing about support removal, interlayer strength, flexure life or a comfortable eyepoint.

## Fewer screws: recommended joint study for Claude

Preserve the Nizo-style pistol layout. Prefer integral locating/load-carrying features and use a lock only to prevent separation or reverse sliding. **Dovetails are a candidate where the necessary sliding motion exists; they are not a universal replacement for screws.** The proposals below are unmodelled and unverified.

| Joint | Current arrangement | Preferred study | Likely benefit and condition |
|---|---|---|---|
| Side panel | Four PH1 screws; straight side insertion/removal; top tongue | Replace the two lower screw interfaces with short integral locating/shear keys. Retain two separated accessible closure screws. | **4 → 2 screws** if stiffness and retention pass. Keeps the wired panel's straight removal path. A captive full-length dovetail would add X/Z travel and must clear the EVF stop, eyepiece clamp, camera keeper and leads; do not assume it fits. |
| Pi keeper | Two PH1 screws | One keyed seat or short captured rail/dovetail, with one accessible positive lock | **2 → 1 screw** if it follows the existing insertion/removal path and supports the stack. No extra bracket or loose wedge. Recheck keeper restraint and driver access, then repeat G-KEEP-1. |
| Body to pistol grip/base | Two sliding T-shaped tongues plus independent `s_j` lock | Keep the load-carrying slide joint. Consider a short dovetail only if it improves the section/fit; retain one independent lock initially. | **1 → 1 screw** initially. Making the panel the only slide stop recreates the earlier service coupling. Zero screws requires a separate, accessible, deliberate-release latch and load/wear tests. |
| Hood | Four hooks, two steel release pins | First test the revised release coupons. Study a drop followed by a short transverse Y slide into integral keys/dovetails, locked by an accessible finger-release catch. Compare guided seats plus one PH1 retainer as the simpler fallback. | Already **zero screws**, but still involves two extra release tools. The transverse slide is speculative: recheck the stack post, plunger channel, leads, panel rail and end clearances. A longitudinal X slide is blocked by the front plate/rear housing wrapping the tub ends. |
| Battery cap | Sliding grooves plus detent | Preserve tool-free battery access; tune the existing captive slide/detent with its coupons. | Avoid adding a screw to routine battery changes. Verify pull retention, deliberate release and repeated sliding. |

The first two studies give a **provisional seven → four PT screw target**, or **five** if a one-screw hood replaces the pin release. These counts exclude the **eight M2.5 screws and four standoffs in the UPS kit**, which remain. They are targets, not achieved reductions.

For each changed joint, show the assembly and service motion with nearby electronics, connector bodies and cables present; use short printed male/female coupons in the intended orientations; verify sliding force, play, retention and repeated release. Add lead-ins and accessible ends. Do not trade three removed screws for inaccessible latches, long binding rails, extra printed keys or another release tool. Recheck all local wall sections and load paths after the change.

The proposed transverse hood motion is plausible enough to study because the hood currently installs before the camera/EVF, and those optics come out before hood service. Their barrels therefore need not slide sideways with the hood. This sequence does not establish that the remaining components clear the new motion.

The dedicated FPS switch and nine-layer FPC fold remain worthwhile independent simplifications. The existing proposal to move FPS into the push-encoder menu retains direct record/exposure operation and would remove a knob, switch hardware and a harness. A shorter verified FPC removes a fiddly folding operation. Those options may reduce assembly effort more than changing an already functional slide joint's profile.

## Comparison with the earlier rough concepts

D2 remains the more developed basis for the next prototype: it has actual enclosure geometry, service paths, exports, proxies and checks. The earlier A/B/C rough 3D objects explored a side tub, lift-off hood and rear cassette around a pistol grip. Their three-main-section targets never represented a verified whole-camera part count or a print-ready alternative.

The useful lesson from those concepts is architectural simplicity: keep the main access opening direct, make retention features integral, and make service motions obvious. The latest D2 moves closer by deleting the skirts, but its present **11 prints, seven PT screws, ten harnesses and twelve assembly-tool categories** still fall short of the original construction goal. Screws share PH1; complete assembly is not a one-screwdriver task.

## Suggested next work order

1. Correct electrical service isolation and evidence/probe tracking. These are small, reviewable changes.
2. Obtain and measure the interfaces that can force a body revision; prove the EVF optics/feed on the bench and establish the power path.
3. Show short joint studies for panel 4 → 2 and keeper 2 → 1, preserving pistol ergonomics, battery access and independent grip retention. Choose between the tested hood pin release and a simpler accessible retainer.
4. Freeze the measured geometry, slice and print the relevant coupons, then run a documented dry assembly before the full powered-camera claim.

Claude should report separately what changed in geometry, what has a test plan, and what has actually been measured. The r2 work addresses real causes. The next revision should prioritize a small number of dependable joints and verified interfaces.
