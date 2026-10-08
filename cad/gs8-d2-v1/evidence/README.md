# GS8 D2 evidence records (r3)

Nothing in this folder exists until someone slices, prints, measures or assembles real hardware. The build machine
has no slicer, printer or parts: `build_d2.py` only reads the records here and reports them; it never judges them and
never closes a hardware gate.

## One record per tested item

A record is a JSON object (a file may hold one object, a list, or `{"records": [...]}`) in any `*.json` file under
`evidence/` (by convention `slicer/`, `coupons/`, `measured/`, `assembly/`). Copy `_record-template.json`. Files whose
name starts with `_` or contains `template`, and this README, are skipped. Any other non-JSON file (a photo, a `.md`
report) is listed as `ignored_files` in the receipt: keep it as an attachment and name it in `notes`, but it is not
evidence by itself. **File names are never matched**: `panel.md`, `base_edge_panel.json` or `old-panel-r1.md` say
nothing to the build.

| Field | Content |
|---|---|
| `item` | the exact item id: a printed part id for `slicer_review` (`panel`, `tub`, ...), a gate id otherwise (`G-CAP-1`, `G-KNOB-1`, `G-W6`, `EVF-G2`, ...) |
| `state` | `slicer_review`, `coupon_validation`, `measured_fit` or `assembly_operation` |
| `artifacts` | `{path: sha256}` of every artifact actually tested: `stl/<part>.stl` (production STL), `stl/coupons/<coupon>.stl`, or a source/doc path relative to `cad/gs8-d2-v1/` or the repo root |
| `profile` | printer, nozzle, material, slicer + version + profile (or the measuring tool / variant) |
| `verdict` | `pass` or `fail` (nothing else) |
| `date`, `by` | when and who |
| `notes` | optional: settings, values, observations, attachment names |

sha256 of a file: `python -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" out/stl/panel.stl`
(the receipt `out/build-receipt.json` `files` lists the current hashes).

## What the build reports (receipt `status_states`, `open_evidence`, `hardware_gates`)

- **Completeness** per item: a current, valid record exists (`evidence_complete`).
- **Outcome** per item: `pass`; `fail`; `conflict` (current records disagree); `stale` (every record names an artifact
  whose sha256 differs from the CURRENT production STL, coupon STL or source, or that no longer exists: r1 and older
  records are stale); `rejected` (the item has a rejected record: it stays open until that record is corrected or
  removed, whatever the other records say); `not run`.
- Rejected records (listed with the reason, never counted as a pass): missing field, bad hash, verdict other than
  pass/fail, unknown state, a coupon artifact on a production-part item, a record that does not name the required
  artifacts. A record of a valid state whose `item` is not a required id (e.g. `Panel` for `panel`) is listed in that
  state's `unmatched_records` and keeps the state open. A file that is not readable JSON, or a record with an unknown
  state AND an unknown item, is listed in `evidence.unassigned_records` (and `rejected_records`) and named in
  `open_evidence`.
- Required artifacts (artifact keys: production / coupon STLs as `stl/...`; docs and sources as repo-root paths, e.g.
  `cad/gs8-d2-v1/MEASURED-PARTS.md`; a path relative to `cad/gs8-d2-v1/` is accepted and converted):
  - `slicer_review`: `stl/<item>.stl` and (r4) every modifier mesh of that part,
    `stl/modifiers/<item>__mod_<id>.stl` (tub 7, panel 4, base_grip 4; the slice must load them);
  - `coupon_validation`: every coupon STL of its gate (from `out/coupons-manifest.json`, `coupons-r1-manifest.json`)
    or calibration;
  - `measured_fit`: the gate's acceptance doc (`electronics/gs8-evf-v1/EVF-SELECTION.md` for EVF-G*,
    `electronics/gs8-d2-v1/WIRING.md` for G-W*, else `cad/gs8-d2-v1/MEASURED-PARTS.md` if it names the gate, else
    `cad/gs8-d2-v1/SPEC.md`); also name any printed STL the part was fitted to (it is hash-checked too);
  - `assembly_operation`: that doc AND every production STL `stl/<part>.stl` (the assembly, service or bench test
    belongs to that release geometry; a geometry change makes the record stale).
- A state stays in `open_evidence` until EVERY required item has a current pass; failed, conflicting and stale item ids
  are named there. A rebuild that changes an STL or source makes the records for it stale: re-test and add a new
  record (keep the old one; it stays as history).

## Required items

- `slicer_review`: the 11 printed parts (`base_grip`, `cap`, `eyecup`, `hood`, `knob_exp`, `knob_fps`, `panel`,
  `pi_keeper`, `plunger`, `stick_sleeve`, `tub`).
- `coupon_validation`: G-PT-1, G-KEEP-1, G-PANEL-1, G-CAP-1, G-EVF-2, G-SNAP-2 and the PRINT-GUIDE s6 calibrations
  **G-KNOB-1** (`knob_bore_ladder_enc` + `knob_bore_ladder_sw`), **G-COMB-1** (`clearance_comb`), **G-J4-1** (`tongue`
  + `keyhole_slot`).
- `measured_fit`, `assembly_operation`: every other gate id named in MEASURED-PARTS.md, SPEC.md, WIRING.md and the
  EVF-SELECTION gate table (the receipt lists them in `hardware_gates`).
- **r4 split items** (`assembly_operation`): `G-SNAP-2/whole` (5 remove/refit cycles of the whole hood on the tub),
  `G-KEEP-1/whole` (5 keeper cycles on the real stack in the printed tub + the far-corner tilt test) and
  `G-PANEL-1/whole` (5 panel cycles on the body, strap fitted). Name the gate's doc (SPEC.md) and every production
  STL. The gate itself reads `recorded pass` only when its coupon item AND its `/whole` item have a current pass.
- **Field types (r4):** `item`, `state`, `verdict`, `profile`, `date`, `by` must be JSON strings and `artifacts` an
  object; a record with another type is rejected and listed (it never stops the build).
