"""Focused read-only r3 logic audit; no CAD construction or production writes.

Runs the existing synthetic regression suite and additional synthetic bookkeeping
cases. Evidence fixtures live only in TemporaryDirectory. The only saved result
is this audit's r3-logic-audit.json. Run with the CAD Python and -B.
"""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
CAD = ROOT / "cad" / "gs8-d2-v1"
sys.path.insert(0, str(CAD))

import build_d2 as B
import checks as CK
import test_r3_regressions as T


def capture(fn):
    try:
        return dict(returned=fn())
    except Exception as exc:
        return dict(exception=type(exc).__name__, message=str(exc))


def main():
    regression = []
    for name in sorted(n for n in vars(T) if n.startswith("test_") and callable(getattr(T, n))):
        result = capture(getattr(T, name))
        regression.append(dict(test=name, passed="exception" not in result, **result))

    cases = []
    for name, change in (("array_state", dict(state=["slicer_review"])),
                         ("object_item", dict(item={"part": "panel"}))):
        record = dict(item="panel", state="slicer_review", artifacts={"stl/panel.stl": "a" * 64},
                      profile="synthetic audit", verdict="fail", date="2026-10-05", by="audit")
        record.update(change)
        with tempfile.TemporaryDirectory(prefix="d2-r3-audit-") as td:
            (Path(td) / "record.json").write_text(json.dumps(record), encoding="utf-8")

            def process():
                records, ignored, hashes = B.load_records(td)
                return B.evidence_state("slicer_review", "slicer", "synthetic", ["panel"], records,
                                        {"stl/panel.stl": "a" * 64}, lambda _: ["stl/panel.stl"])

            outcome = capture(process)
        cases.append(dict(id="malformed_field_" + name, fixture=record, observed=outcome,
                          source="build_d2.py:727-743,880-882",
                          implication="Syntactically valid JSON with an invalid field type raises instead of being rejected.",
                          recommendation="Check item/state/profile/date/by field types before membership lookups; retain a rejected record."))

    layout = SimpleNamespace(
        PARTS={"hood": {}}, LOAD_BEARING_PARTS=["hood"],
        CRITICAL_JOINTS=[dict(id="J1", parts=["hood"], required=["f"])],
        REQUIRED_JOINT_IDS=["J1", "J4"],
        FR_JOINTS=[dict(id="FR_phantom", parts=["hood"], required=[], replaces=["J4"])],
    )
    measured = [dict(kind="feature", id="f", part="hood", status="pass", measured_mm=2.0)]
    phantom = CK.check_joint_coverage(layout, measured)
    cases.append(dict(
        id="unvalidated_replacement_waives_required_joint", observed=phantom,
        all_rows_pass=all(r["status"] == "pass" for r in phantom),
        source="checks.py:970-983",
        implication="An FR_JOINTS declaration absent from CRITICAL_JOINTS can waive a required baseline joint without being checked.",
        qualification="The actual candidate merges its replacements into CRITICAL_JOINTS; this demonstrates a regression gap, not a current geometry failure.",
        recommendation="Only validated entries actually in CRITICAL_JOINTS may replace a required joint; require usable feature coverage."))

    # G-SNAP-2 includes whole-hood/tub service cycles in SPEC.md:353-356, but
    # required_artifacts_of currently binds only its local coupon STL files.
    coupon_hashes, coupon_map, _ = B.coupon_artifacts(str(CAD / "out"))
    required = B.required_artifacts_of("coupon_validation", coupon_map)("G-SNAP-2")
    artifacts = {k: coupon_hashes[k] for k in required}
    snap_record = dict(item="G-SNAP-2", state="coupon_validation", artifacts=artifacts,
                       profile="synthetic audit", verdict="pass", date="2026-10-05", by="audit")
    records = [dict(file="synthetic.json", index=0, rec=snap_record, errors=B.validate_record(snap_record))]
    current = dict(coupon_hashes)
    current.update({"stl/hood.stl": B.sha(str(CAD / "out" / "stl" / "hood.stl")),
                    "stl/tub.stl": B.sha(str(CAD / "out" / "stl" / "tub.stl"))})
    before = B.evaluate_item("coupon_validation", "G-SNAP-2", records, current, required)
    changed = dict(current, **{"stl/hood.stl": "0" * 64, "stl/tub.stl": "1" * 64})
    after = B.evaluate_item("coupon_validation", "G-SNAP-2", records, changed, required)
    cases.append(dict(
        id="whole_hood_test_bound_only_to_local_coupons", required_artifacts=required,
        recorded_artifacts=list(artifacts), before_outcome=before["outcome"],
        after_simulated_production_change_outcome=after["outcome"],
        source="build_d2.py:967-977; SPEC.md:353-356",
        implication="A G-SNAP-2 record can remain current after whole hood/tub geometry changes outside its coupon cuts.",
        qualification="All current physical evidence is not run; no existing physical result was invalidated by this audit.",
        recommendation="Split coupon and whole-assembly subtests, or require the full hood/tub STL hashes and acceptance-document hash for this gate."))

    candidate_receipt = json.loads((CAD / "candidate-fr1" / "out" / "build-receipt.json").read_text(encoding="utf-8"))
    report = dict(
        scope="Pure logic/synthetic tests only; no production edits, CAD construction, slicing or physical testing.",
        source_hashes={name: hashlib.sha256((CAD / name).read_bytes()).hexdigest()
                       for name in ("build_d2.py", "checks.py", "test_r3_regressions.py")},
        regressions=dict(total=len(regression), passed=sum(r["passed"] for r in regression), results=regression),
        cases=cases,
        candidate_physical_states={k: {field: v.get(field) for field in ("items_required", "items_pass", "open", "status")}
                                   for k, v in candidate_receipt["status_states"].items() if k != "cad_checks"},
        candidate_artifact_binding_note=(
            "build_d2.py:1321-1322 resolves STL hashes from this build's output files and coupons; "
            "RELEASE_DIR shares acceptance docs, not baseline production STL hashes."),
    )
    output = Path(__file__).with_name("r3-logic-audit.json")
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(output=str(output), regressions_passed=report["regressions"]["passed"],
                          regression_total=len(regression), additional_cases=len(cases)), indent=2))


if __name__ == "__main__":
    main()
