"""Read-only logic audit of D2 evidence and critical-feature bookkeeping.

Extracts selected functions with AST instead of importing the build/CAD modules.
Evidence fixtures exist only in TemporaryDirectory; no production files are edited.
Critical-feature probes below use a deliberately synthetic chord function, so their
results demonstrate checker behavior, not a defect in the current camera geometry.

Run: .venv-cad/Scripts/python.exe -B audit/d2-readiness-2026-10-05/check_evidence_logic.py
"""

import ast
import hashlib
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
CAD = ROOT / "cad" / "gs8-d2-v1"
OUTPUT = Path(__file__).with_name("evidence-logic-audit.json")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def extracted(path, names, namespace):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes} == set(names)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)
    return namespace


def main():
    build_tree = ast.parse((CAD / "build_d2.py").read_text(encoding="utf-8"))
    verdict_re = next(ast.literal_eval(n.value) for n in build_tree.body
                      if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == "VERDICT_RE" for t in n.targets))
    build_ns = extracted(
        CAD / "build_d2.py",
        {"_token_in", "_item_evidence", "evidence_state", "summarize"},
        dict(os=os, sha=sha, VERDICT_RE=verdict_re),
    )
    results = []
    with tempfile.TemporaryDirectory(prefix="d2-evidence-audit-") as td:
        sandbox = Path(td)

        def evidence_case(case, sub, filename, body, required):
            home = sandbox / case
            directory = home / "evidence" / sub
            directory.mkdir(parents=True)
            (directory / filename).write_text(body, encoding="utf-8")
            build_ns.update(HERE=str(home), EVIDENCE=str(home / "evidence"))
            return build_ns["evidence_state"](sub, "Synthetic audit fixture", required)

        failed = evidence_case(
            "failed", "coupons", "G-CAP-1-r1.md",
            "verdict: fail\nrevision: r1\n", ["G-CAP-1"],
        )
        results.append(dict(
            id="failed_verdict_completes_evidence_collection", observed=failed,
            retained_in_open_evidence=not failed["status"].startswith(
                "evidence with a recorded verdict for all"),
            source="build_d2.py:699-719,1065-1066",
            implication="A failed verdict completes evidence collection and removes the state from open_evidence.",
            qualification="The text explicitly does not judge evidence; this is not an explicit hardware-pass claim.",
            recommendation="Separate evidence completeness from outcome; retain failed/conflicting verdicts as unresolved.",
        ))

        stale = evidence_case(
            "stale", "coupons", "G-CAP-1-r1.md",
            "verdict: pass\nrevision: r1\nsource_sha256: " + "0" * 64 + "\n",
            ["G-CAP-1"],
        )
        results.append(dict(
            id="stale_revision_is_not_checked", observed=stale,
            source="build_d2.py:685-696,699-724",
            implication="The report hash is recorded but its tested revision/source hash is not checked.",
            recommendation="Require tested artifact/source hashes and invalidate affected evidence when those change.",
        ))

        coupon = evidence_case(
            "coupon_name", "slicer", "base_edge_panel.md",
            "verdict: pass\nartifact: stl/coupons/base_edge_panel.stl\n", ["panel"],
        )
        results.append(dict(
            id="coupon_filename_can_cover_production_part", observed=coupon,
            token_examples={name: build_ns["_token_in"]("panel", name)
                            for name in ("panel.md", "base_edge_panel.md", "old-panel-r1.md")},
            source="build_d2.py:680-693",
            implication="A review of a panel coupon can be counted as the complete panel's slicer evidence.",
            recommendation="Match explicit artifact_id and artifact_hash fields, not part tokens in filenames.",
        ))

    unknown = {state: build_ns["summarize"](
        "critical_features", [dict(status=state)], info_neutral=True)
        for state in ("not run", "error")}
    results.append(dict(
        id="unrecognized_status_passes_info_neutral_summary", observed=unknown,
        source="build_d2.py:776-784",
        implication="The group reports pass with zero passing rows if the sole non-info row has an unrecognized status.",
        qualification="No such status occurs in the current recorded critical-feature results.",
        recommendation="Require nonempty core and all(status == 'pass'); reject unknown statuses explicitly.",
    ))

    calls = []

    def synthetic_chord(shape, point, direction):
        calls.append(list(point))
        if all(abs(x) < 1e-12 for x in point):
            return None, None, None, "synthetic origin outside material"
        return 2.0, -1.0, 1.0, None

    check_ns = extracted(
        CAD / "checks.py", {"registry", "feature_class", "check_critical_features"},
        dict(np=np, chord=synthetic_chord, _r=lambda x, n=3: round(x, n)),
    )
    feature = dict(id="hood_groove_lower_lip", part="hood", structural=True,
                   origin=(0.0, 0.0, 0.0), direction=(0, 0, 1),
                   span=(4, 12.0, (1, 0, 0)), min_mm=1.6, cls="lip")
    layout = SimpleNamespace(PARTS={"hood": {}}, CRITICAL_FEATURES=[feature],
                             LOAD_BEARING_PARTS=["hood"], FEATURE_CLASS_MIN={"lip": 1.6})
    rows = {"hood": dict(shape=object(), stub=False)}
    even = check_ns["check_critical_features"](layout, rows)
    results.append(dict(
        id="even_span_does_not_test_nominated_origin", observed=even,
        queried_points=calls, origin_was_queried=[0.0, 0.0, 0.0] in calls,
        source="checks.py:832-846; layout.py:793-794; SPEC.md:176-179",
        implication="The nominated origin can be outside material without a stale-origin failure for even-length spans.",
        qualification="Synthetic geometry response only; the current hood's origin is not demonstrated to be outside.",
        recommendation="Always query the origin and validate expected span coverage; classify intentional missing rays explicitly.",
    ))

    # The required-part registry survives deletion of a designated feature entry.
    check_ns["chord"] = lambda shape, p, d: (2.0, -1.0, 1.0, None)
    keeper_feature = dict(id="remaining_feature", part="base_grip", structural=True,
                          origin=(1, 0, 0), direction=(0, 0, 1), min_mm=1.6, cls="lip")
    dropped_feature = dict(keeper_feature, id="base_keyhole_lip_f_l")
    layout = SimpleNamespace(PARTS={"base_grip": {}},
                             CRITICAL_FEATURES=[keeper_feature, dropped_feature],
                             LOAD_BEARING_PARTS=["base_grip"], FEATURE_CLASS_MIN={"lip": 1.6})
    layout.CRITICAL_FEATURES.remove(dropped_feature)
    missing = check_ns["check_critical_features"](
        layout, {"base_grip": dict(shape=object(), stub=False)})
    results.append(dict(
        id="missing_feature_is_not_missing_part_coverage", observed=missing,
        removed_feature="base_keyhole_lip_f_l", source="checks.py:869-875",
        implication="At-least-one-entry-per-part coverage cannot detect deletion of one required critical feature.",
        qualification="The current registry contains all four named base keyhole lip entries; this is a regression protection gap.",
        recommendation="Maintain required feature IDs or derive required checks from each joint/retention feature; test deletion explicitly.",
    ))

    recorded = json.loads((CAD / "out" / "checks.json").read_text(encoding="utf-8"))
    receipt = json.loads((CAD / "out" / "build-receipt.json").read_text(encoding="utf-8"))
    report = dict(
        scope="Read-only source extraction; temporary synthetic evidence; no CAD process or production mutation.",
        source_hashes={name: sha(CAD / name) for name in ("build_d2.py", "checks.py", "layout.py")},
        current_receipt_qualification="Current physical states are not run. These diagnostics do not disprove current CAD results.",
        current_row_counts={k: sum(s.get(k, 0) for s in recorded["summary"])
                            for k in ("n", "passed", "failed", "stub", "info")},
        current_coupon_evidence_items=receipt["status_states"]["coupon_validation"]["items"],
        coupon_evidence_coverage_note=(
            "The six required coupon gate IDs omit the knob-bore ladder, clearance-comb calibration and J4 fit "
            "record listed in PRINT-GUIDE.md:145-147,165-167; see build_d2.py:675,739."),
        cases=results,
    )
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(output=str(OUTPUT), cases=len(results),
                          current_row_counts=report["current_row_counts"]), indent=2))


if __name__ == "__main__":
    main()
