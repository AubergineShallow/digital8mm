# GS8 D2 r3 and FR1 follow up audit

**The r3 corrections are substantial, and FR1 is a credible candidate for prototype testing.** The screw reduction is implemented in real geometry: seven body screws become four, and the sliding hood removes two loose release pins and four flexing hooks. It remains an exploratory candidate; the baseline has not adopted these joints.

My recommendation is to trial the keyed keeper and sliding hood first, then decide on the two-screw panel from stiffness and grip-retention tests. The panel has the largest structural trade-off. None of the files establishes a physically validated camera or a complete print-ready build.

Reviewed 5 October 2026, after the 16:53 baseline release and 15:26 FR1 candidate. This audit reads the handoff, response, joint studies, source, exports and partial airflow outputs. Instructions and reports of decisions inside those documents were treated as source material, not instructions to adopt geometry or resume simulations. Design files and release outputs were left unchanged.

## Independent verification

| Check | Result |
|---|---|
| Current baseline provenance | All 16 source, 76 output and four gate-document hashes match. |
| Baseline meshes | 11 production plus 24 coupon STLs: all watertight, consistently wound and positive volume. Compared with saved r2, only the tub and its keeper-floor coupon differ. This verifies the changed-file count, not an independent proof that every changed triangle belongs to the rib tip. |
| FR1 provenance | All 17 present source files and 61 recorded outputs match. The two local policy/spec files are recorded as missing; acceptance documents are shared with the baseline. Two shared document hashes have changed since the candidate build, as discussed below. |
| FR1 meshes | 11 production plus 24 coupon STLs: all pass the same mesh checks. The separate coupon-check file's 24 hashes also match. |
| Independent FR1 rebuild | Rebuilt `D2_FR=all` in an isolated audit directory through the CAD lock, with 1 mm sweeps. **21/21 categories pass, no stubs, all 11 regenerated production STL hashes match Claude's exports exactly.** Runtime 307 seconds. `--fast` omitted the full renders and STEP; thickness and insertion/removal checks ran. |
| Logic regressions | All 27 supplied r3 cases pass. Four additional synthetic cases reproduce the remaining bookkeeping defects below. |
| Generated documentation | `make_tables.py --check`: no stale tables, count lint reports zero disagreements. This does not catch the FR1 tool-count omission below. |
| Visual review | Inspected representative hood section/motion, keeper section and panel-frame views of built geometry. |

Evidence: [artifact audit](<C:/Users/Pre-Installed User/Claude/Projects/8mm/audit/d2-readiness-2026-10-05-r3/artifact-audit.json>), [independent rebuild receipt](<C:/Users/Pre-Installed User/Claude/Projects/8mm/audit/d2-readiness-2026-10-05-r3/rebuild-fr1/build-receipt.json>), [logic diagnostics](<C:/Users/Pre-Installed User/Claude/Projects/8mm/audit/d2-readiness-2026-10-05-r3/r3-logic-audit.json>). Reproduction scripts are [check_artifacts.py](<C:/Users/Pre-Installed User/Claude/Projects/8mm/audit/d2-readiness-2026-10-05-r3/check_artifacts.py>) and [check_r3_logic.py](<C:/Users/Pre-Installed User/Claude/Projects/8mm/audit/d2-readiness-2026-10-05-r3/check_r3_logic.py>).

The current baseline reports 542 passing and ten informational rows. The FR1 candidate reports 534 passing and ten informational rows. The informational cap exceptions remain physical-test dependencies. No slicing, printing, measurement, procurement, electrical test or physical service trial was performed here. The baseline was checked from its supplied exports rather than rebuilt again in this pass.

## Previous findings now addressed

- **Battery isolation:** the service instructions now require shutdown, cap removal, pack extraction and XT30 disconnection before every internal service route, including panel-only service. This closes the previous instruction defect. The EVF shutdown indication remains bench-dependent.
- **Evidence handling:** exact record IDs and artifact hashes replace filename matching. Failed, stale, conflicting and rejected records remain visible. The three missing calibration records are registered. Current physical states remain correctly marked not run.
- **Thickness coverage:** nominated origins are always tested, unexpected missing rays fail, and required joints have explicit feature lists. The cap's flexures and dependent joint remain informational exceptions rather than ordinary structural passes.
- **Baseline document corrections:** the earlier screw/coupon/measurement counts and far-corner restraint wording were addressed. The later rib-tip change is present in the baseline exports, while the candidate still carries the older tip as disclosed.

These are real closures. The remaining checker issues below should not be used to imply that the current geometry has failed or that the earlier corrections did nothing.

## Corrections before handing the candidate to a builder

### Hood removal direction

[HANDOFF.md, line 82](<C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1/HANDOFF.md:82>) says to push the hood toward the right wall and lift. That is the locking direction. Removal requires **2.5 mm toward the open left side, +Y, then lift**. The candidate source and detailed instructions agree on this reverse motion: [layout.py, line 1616](<C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1/candidate-fr1/layout.py:1616>).

Correct the summary and any derived service diagram. A builder should not need to resolve conflicting direction instructions by forcing the joint.

### Keeper coupon clearance

[coupons_fr_keeper.py, line 29](<C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1/candidate-fr1/coupons_fr_keeper.py:29>) and its generated manifest still describe a **0.25 mm tip gap**. The current tongue/pocket coordinates give **0.15 mm**, consistent with the joint study. Update the source instruction and regenerate the manifest. The geometry agrees with the intended revised fit; the acceptance guidance is stale.

### Full assembly tool count

The handoff's nine-to-eight tool comparison is a subset presented as the full count. [fr1_counts.py, line 11](<C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1/candidate-fr1/fr1_counts.py:11>) omits the stripper/cutter, heat gun and flat bar/steel rule that the main assembly list still requires. On that same full-build scope the change is **12 to 11 tool categories**, with the release pins removed. The screw interface uses PH1, but the whole camera is still not a one-screwdriver assembly.

Use the authoritative tool list or label the narrower count explicitly; a keyword scan is not a complete bill of tools.

## Candidate assessment

| Joint | What is actually improved | Trade-off and next decision |
|---|---|---|
| Keyed Pi keeper | An integral seat and tongue replace one screw. The reverse path is explicit; no destructive flexing or extra loose part. | **Best first coupon trial.** It adds a short seating motion and depends on a 0.15 mm printed fit. Verify binding, play, finger clearances and load retention on the real stack before adoption. |
| Sliding hood | Rigid staples and dovetail toes replace four snap hooks, two pins and their holes. Drop and transverse slide are modelled. | **Worth trialling.** Its withdrawal stop uses the panel tongue/camera ring, and the panel-off assessment assumes a fixed camera. Test the complete assembly, repeated release, roof push, real cooler clearance and microSD guidance. Hood service removes the optics first, so no circular teardown dependency was found. |
| Two-screw panel | Two integral lower keys and a stiffening frame preserve direct side removal. The tripod plate can remain attached. | **Conditional choice.** The keys do not hold the lower edge against outward pull. The quoted stiffness is an estimate, not measured performance. Removing the lower screws also leaves `s_j` as the sole in-use base withdrawal lock. Test the full panel and loaded grip, not just key fit. |
| Base/grip | The sliding T tongues and independent lock remain. | Keep the independent lock. Fewer redundant restraints make its acceptance test more consequential. Do not use the panel as the only base lock. |
| Battery cap | Existing slide/dovetail and detent remain tool-free. | Preserve access; the known cap flexure gate still needs a physical result. |

The joint studies already contain useful proposed acceptance criteria: panel seam movement under 2/5 N; keeper pull and permanent-set limits; hood lift, permanent-set and repeated-cycle limits. They have not been run. This is the right stage for a small set of coupons followed by a complete closure/service mock-up, rather than another round of purely numerical confidence.

Four body screws is an achieved CAD count, not yet a reason to prefer every joint. Eleven printed pieces, ten harnesses and the UPS kit's eight screws/four standoffs remain. A failed panel test should be allowed to retain more screws without discarding the useful keeper and hood improvements.

## Remaining validation code issues

The additional diagnostics are synthetic and do not establish a defective current part. Fix these before relying on the system to track physical acceptance:

1. **Whole-hood evidence can outlive changed whole parts.** G-SNAP-2 includes complete hood service cycles, but [required_artifacts_of](<C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1/build_d2.py:967>) requires only local coupon hashes for that gate. A synthetic passing record remains current after changing the production hood/tub hashes. Split coupon and whole-assembly tests or also require the full tested parts and acceptance-document hash. Apply the same distinction to candidate whole-assembly tests.
2. **Malformed record field types can crash evaluation.** An array-valued `state` or object-valued `item` raises `TypeError` instead of producing a rejected record. Validate field types before lookups and preserve the bad record as unresolved. See [validate_record](<C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1/build_d2.py:727>).
3. **A declared replacement can waive an unchecked joint.** [checks.py, line 978](<C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1/checks.py:978>) accepts a replacement listed only in `FR_JOINTS`, even if it is absent from the validated `CRITICAL_JOINTS` set. The actual candidate merges its replacements correctly; the reproduced hole is a future regression path. Only an actually validated replacement with required features should satisfy the missing-joint check.

Acceptance tests should demonstrate that changed complete parts invalidate complete-assembly evidence, malformed records do not abort a build, and an unvalidated replacement cannot hide a required joint.

## Electrical and airflow limits

The 4.55 V EVF feed requirement is clearer than the former generic 5 V regulator proposal. It still lacks a selected, built and measured implementation. Its net **three extra parts and about eleven extra solder joints** also need to be counted when judging total assembly simplicity. Prefer an exact suitable assembled carrier if one can be verified; do not assume one exists or that its package fits.

One test needs correction: [G-W13(e)](<C:/Users/Pre-Installed User/Claude/Projects/8mm/electronics/gs8-d2-v1/WIRING.md:444>) leaves VIN open while applying power to VOUT. An open input can charge without representing sustained backfeed into an off USB rail. Specify a defined off-rail load/clamp, within the selected device's ratings, and measure reverse current and rail rise through shutdown. Retain the installed G-W7(c) test. This is a test-procedure gap, not evidence that the proposed circuit actually backfeeds.

The regulator option's upper bound is a requirement that an implementation must meet; avoid calling it unconditionally “met by design” before selecting that implementation. The 27 W versus 25.5 W power issue remains a hardware gate, and EVF optical fit and battery/component interfaces remain unmeasured.

**Airflow remains inconclusive.** No completed `AIRFLOW.md` was present at review. The partial [variant tables](<C:/Users/Pre-Installed User/Claude/Projects/8mm/cad/gs8-d2-v1/airflow/out/variants/VARIANTS-tables.md:24>) label a UA 0.20 case but reuse UA 0.095 values, and print thermal-gate “FAIL” beside extreme interim model temperatures. Relabel these as superseded/partial model outputs, not hardware failures. Notes acknowledge omitted buoyancy, corrected wall-loss scaling and significant finer-grid uncertainty. Those results can motivate a cooling investigation; they do not establish actual camera temperatures, a completed variant comparison, or a passed/failed physical G-W11. No airflow process was resumed in this audit.

## Before adopting selected joints

The candidate's main receipt does not include the twelve new `coupons-fr` STLs. They do have matching hashes in a separate coupon-check file, but that file is not connected to the main receipt. The candidate's shared SPEC/WIRING hashes also predate later baseline edits. Its local SPEC and fastener-policy source entries say missing; the current acceptance documents are shared rather than frozen with the candidate.

This does not invalidate the reproduced candidate geometry. It means the candidate package needs consolidation when a direction is selected: bring across the later baseline rib-tip and recorded LED changes, register the FR-specific gates, bind the new coupons/manifests and full-assembly tests to the selected geometry, and issue one coherent receipt and instruction set. The FR-specific physical gates currently appear in the studies, not the release's automatic gate registry, as the handoff discloses.

Recommended next sequence: correct the builder-facing instructions and test definitions, choose which joint trials to run, measure the electronics interfaces, then slice/print the small trials. Adopt successful joints individually and rebuild once into the release. Keep the baseline available until those choices are supported by physical evidence.
