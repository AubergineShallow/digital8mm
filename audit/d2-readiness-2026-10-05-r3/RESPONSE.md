# Response to the D2 r3 and FR1 follow-up audit (GS8 D2 r4)

Written 2026-10-05 evening. The reviewer's files in this folder are unchanged; this is the only file added here. Full
record: `cad/gs8-d2-v1/RECTIFICATION.md` section "r4"; state and next steps: `cad/gs8-d2-v1/HANDOFF.md` section 0;
log: `cad/gs8-d2-v1/NOTES.md` "r4 maturity pass". Every result below is a computed check, desk research from
datasheets or a document change. Nothing was printed, sliced, bought, measured, assembled or powered, and nothing was
committed.

**Baseline after r4.** Release receipt `cad/gs8-d2-v1/out/build-receipt.json`, built 2026-10-05 21:51:07 +0800 (Kowa,
`--sweep-step 1.0`): 23 of 23 categories (two new: `cable_routes`, `print_modifiers`), 593 rows = 581 pass + 12 info +
0 fail; 16 of 16 sources, 91 of 91 outputs and 4 of 4 gate docs match disk. All 11 production and 24 coupon STLs are
byte-identical to the 16:53:58 r3 release you reviewed. Fujinon run `out/_fujinon-r4`: 23 of 23.
`test_r3_regressions.py`: 31 of 31 (27 + 4 new cases for your diagnostics and the new route check). Your
`check_r3_logic.py` was re-run from a copy in a scratch folder (this folder's JSON was not overwritten): no exception
for either malformed record; the phantom replacement now leaves J4 failing.

| item | response | change | evidence |
|---|---|---|---|
| Hood removal direction (HANDOFF line 82) | accepted | now "2.5 mm toward the open left side, +Y, then lift"; the locking direction is named as such | HANDOFF s3 |
| Keeper coupon clearance 0.25 vs 0.15 | accepted | `coupons_fr_keeper.py` gate text: 0.15 tip gap (pocket y0 -29.9, tongue y0 -29.75); manifest regenerated | `candidate-fr1/out/coupons-fr-keeper-manifest.json`; 24 FR coupon meshes watertight |
| Full assembly tool count | accepted | `fr1_counts.py` labels its keyword column a subset and states the ASSEMBLY s1.1 count: 12 tools, 11 for any hood variant without pins; HANDOFF table corrected | `candidate-fr1/out/fr1-counts.md` |
| Logic 1: whole-hood evidence outlives changed parts | accepted, option "split" | G-SNAP-2, G-KEEP-1, G-PANEL-1 keep their coupon item; the whole-part cycles are new assembly_operation items `<gate>/whole` bound to the gate doc and every production STL; the gate reads pass only when both halves pass | `test_whole_part_test_is_split_and_goes_stale`; receipt gates 53 (3 `/whole`) |
| Logic 2: malformed field types crash | accepted | field types validated before any lookup; non-string keys never reach a dict/set; the record is rejected or unmatched and stays listed | `test_malformed_field_types_are_rejected_not_crashing` |
| Logic 3: declared replacement waives an unchecked joint | accepted | only a validated CRITICAL_JOINTS entry can replace a required joint; FR_JOINTS-only declarations waive nothing | `test_unvalidated_replacement_cannot_waive_required_joint` |
| G-W13 (e) open-input test | accepted | defined off rail: the real VBUS with a 100 ohm stand-in load; VOUT held at 4.90 V or VIN + the device's rated maximum, whichever is lower; reverse current and VBUS rise logged through shutdown, 3 times; G-W7 (c) kept | WIRING s9 |
| "Met by design" wording | accepted | withdrawn in row C and the recommendation: the bound is a device requirement until a selected part's datasheet and G-W13 show it | WIRING s4.8 |
| Regulator implementation not selected | partly addressed (desk research; still a user decision) | candidates named from datasheets: TI TLV75801P set to 4.553 V (band 4.459-4.638 V from datasheet limits; in stock) and Torex XC6220B45BPR-G fixed (no stock); XC6210 rejected; no pre-assembled 4.5 V board found; no candidate blocks reverse current, so G-W7 (c) with the regulator fitted decides. Option C counts updated: +5 parts, about +15 joints with the TLV75801P (+3 / +11 with the XC6220) | WIRING s4.8; `electronics/gs8-d2-v1/RESEARCH-r4-fuse-ldo.md`; BOM D2-16R/D/C/P at quantity 0 |
| Airflow tables mislabelled | accepted (label only) | STATUS banner on `VARIANTS-tables.md`: partial, superseded model output; UA 0.20 reuses UA 0.095 values; a printed FAIL is a model flag, not G-W11. No process was resumed | `airflow/NOTES.md` "r4 label" |
| FR1 package consolidation (coupons-fr outside the main receipt; shared SPEC/WIRING hashes) | accepted, deferred to adoption as you suggest | unchanged: the candidate stays exploratory; on adoption the chosen toggles are ported, the FR gates registered and one receipt issued | HANDOFF s3, s6 |

**Further maturity work done in the same pass (not audit items).**
- `cable_routes` check: continuity of every cable's keep-out chain (passage at least 1.0 x 1.0), both ends reaching
  their parts, and an estimated route length plus allowance within the cable. It found gaps of 0.1, 0.2, 2.0, 10.0,
  1.0 and 0.2 mm and a 4 x 0.4 mm run-lead edge contact; 6 link keep-outs close them (no printed solid was in the gaps).
  Bend radius is still not checked by CAD.
- A 15 A inline fuse (Littelfuse 0251015.MXL) in the battery pigtail, modelled in the XT30 junction proxy, with a pack
  protection requirement R-PACK-BMS; G-W1 and G-W5 extended (plug-in surge, sleeve temperature, drop 0.135 V estimated
  against 0.15 V).
- 15 slicer modifier meshes for the FASTENER-POLICY 40 % rule round every pilot (the panel's threaded bosses had no
  modifier before), checked, hash-linked and required in slicer-review records.

**Unchanged and still open:** every physical gate (51 open, 2 withdrawn); the 27 W planning peak against the X1203's
25.5 W (G-W12); airflow inconclusive; the cap detent strip, the hood web 1.08 and the s_k2 wall named in CAD; the
user's decisions (lens, band, OPTIONS, purchase variants, EVF feed, FR1 joints).
