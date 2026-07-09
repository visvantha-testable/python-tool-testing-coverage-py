"""Write platform-facing files to the repository root."""

from __future__ import annotations

import json
import pathlib
import shutil
import sys
from dataclasses import asdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from coverage_py_metrics import compute_metrics, export_dashboard_payload  # noqa: E402
from platform_coverage_fixup import apply_platform_branch_scale  # noqa: E402


def export() -> None:
    training = ROOT / "artifacts" / "training"
    coverage_json = training / "coverage.json"
    baseline_json = training / "coverage_baseline.json"
    source = ROOT / "sample_subject" / "app"

    metrics = compute_metrics(coverage_json, source_root=source, baseline_json=baseline_json)
    dashboard = export_dashboard_payload(metrics)
    payload = asdict(metrics)
    payload["normalized_scores"] = {
        name: float(score) for name, score in dashboard["scores"].items()
    }
    payload["dashboard_export"] = dashboard

    # Top-level L4 keys for platforms that map classification name -> score.
    platform_flat: dict = {
        "tool": "coverage.py",
        "target_repository": "sample_subject",
        "percent_covered": metrics.statement_coverage_percent,
        "percent_branches_covered": metrics.branch_coverage_percent,
        "covered_branches": metrics.covered_branches,
        "num_branches": metrics.num_branches,
        "missing_branches": metrics.missing_branches,
        "covered_lines": metrics.covered_lines,
        "num_statements": metrics.num_statements,
        "missing_lines": metrics.missing_lines,
    }
    for name, score in dashboard["scores"].items():
        platform_flat[name] = int(round(score))

    # Excel derivation aliases (0-100 scale, not 0-1 ratios).
    platform_flat.update(
        {
            "boolean_accuracy": int(round(metrics.boolean_accuracy)),
            "control_flow_integrity": int(round(metrics.control_flow_integrity)),
            "loop_boundary_risk": int(round(metrics.loop_boundary_risk)),
            "edge_case_risk": int(round(metrics.edge_case_risk)),
            "branch_coverage_percent": int(round(metrics.branch_coverage_percent)),
            "decision_coverage": int(round(metrics.decision_coverage)),
            "statement_coverage_percent": int(round(metrics.statement_coverage_percent)),
            "branch_misdirection": metrics.branch_misdirection,
            "branch_misdirection_score": int(round(metrics.branch_misdirection_score)),
            "decision_gap_score": int(round(metrics.decision_gap_score)),
        }
    )

    # Enrich coverage JSON so platforms that derive from totals get 0-100 scores, not 0-1 ratios.
    coverage_data = json.loads(coverage_json.read_text(encoding="utf-8"))
    coverage_data = apply_platform_branch_scale(coverage_data)
    totals = coverage_data.setdefault("totals", {})
    totals.update(
        {
            "boolean_accuracy": int(round(metrics.boolean_accuracy)),
            "control_flow_integrity": int(round(metrics.control_flow_integrity)),
            "loop_boundary_risk": int(round(metrics.loop_boundary_risk)),
            "edge_case_risk": int(round(metrics.edge_case_risk)),
            "branch_coverage_percent": int(round(metrics.branch_coverage_percent)),
            "decision_coverage": int(round(metrics.decision_coverage)),
            "branch_misdirection_score": int(round(metrics.branch_misdirection_score)),
            "decision_gap_score": int(round(metrics.decision_gap_score)),
        }
    )
    coverage_data["platform_metrics"] = platform_flat
    coverage_data["platform_scores"] = {
        name: int(round(score)) for name, score in dashboard["scores"].items()
    }

    root_files = {
        ROOT / "coverage.json": coverage_json,
        ROOT / "coverage_baseline.json": baseline_json,
        ROOT / "coveragepy_metrics.json": payload,
        ROOT / "dashboard_metrics.json": dashboard,
        ROOT / "platform_metrics.json": platform_flat,
        ROOT / "metrics.json": platform_flat,
    }

    (ROOT / "coverage.json").write_text(json.dumps(coverage_data, indent=2), encoding="utf-8")
    (ROOT / "coverage_baseline.json").write_text(
        baseline_json.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (ROOT / "coveragepy_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (ROOT / "dashboard_metrics.json").write_text(json.dumps(dashboard, indent=2), encoding="utf-8")
    (ROOT / "platform_metrics.json").write_text(json.dumps(platform_flat, indent=2), encoding="utf-8")
    (ROOT / "metrics.json").write_text(json.dumps(platform_flat, indent=2), encoding="utf-8")

    testable_dashboard = {
        "tool": "coverage.py",
        "target_repository": "sample_subject",
        "execution_status": "Completed",
        "metrics": dashboard["metrics"],
    }
    (ROOT / "testable_dashboard.json").write_text(
        json.dumps(testable_dashboard, indent=2), encoding="utf-8"
    )

    platform_dir = ROOT / "platform"
    platform_dir.mkdir(exist_ok=True)
    shutil.copy2(ROOT / "coverage.json", platform_dir / "coverage.json")
    shutil.copy2(ROOT / "coverage_baseline.json", platform_dir / "coverage_baseline.json")
    shutil.copy2(ROOT / "platform_metrics.json", platform_dir / "platform_metrics.json")
    shutil.copy2(ROOT / "dashboard_metrics.json", platform_dir / "dashboard_metrics.json")
    shutil.copy2(ROOT / "metrics.json", platform_dir / "metrics.json")
    shutil.copy2(ROOT / "testable_dashboard.json", platform_dir / "testable_dashboard.json")

    print("Exported platform bundle:")
    for path in root_files:
        print(f"  {path.name}")


if __name__ == "__main__":
    export()
