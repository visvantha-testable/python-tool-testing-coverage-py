"""Ensure all Excel-mapped coverage.py techniques are implemented."""

import json
import pathlib

import pytest

from coverage_py_metrics import compute_metrics


CONFIG = pathlib.Path(__file__).resolve().parents[1] / "config" / "technique_coverage.json"

FIXTURE = {
    "files": {
        "a.py": {"summary": {"covered_lines": 50}},
        "b.py": {"summary": {"covered_lines": 35}},
    },
    "totals": {
        "percent_covered": 85.0,
        "percent_branches_covered": 70.0,
        "num_statements": 100,
        "covered_lines": 85,
        "missing_lines": 15,
        "num_branches": 20,
        "covered_branches": 14,
        "missing_branches": 6,
    },
}

BASELINE = {
    "files": {"a.py": {"summary": {"covered_lines": 40}}},
    "totals": {
        "percent_covered": 80.0,
        "percent_branches_covered": 65.0,
        "num_statements": 95,
        "covered_lines": 76,
        "missing_lines": 19,
        "num_branches": 18,
        "covered_branches": 12,
        "missing_branches": 6,
    },
}


def _write_json(path: pathlib.Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_all_technique_fields_present(tmp_path):
    cov = tmp_path / "coverage.json"
    base = tmp_path / "baseline.json"
    _write_json(cov, FIXTURE)
    _write_json(base, BASELINE)

    techniques = json.loads(CONFIG.read_text(encoding="utf-8"))["techniques"]
    metrics = compute_metrics(cov, baseline_json=base)
    payload = metrics.__dict__

    missing = [t["metric_field"] for t in techniques if t["metric_field"] not in payload]
    assert not missing, f"Missing fields: {missing}"

    null_without_baseline = [
        t["metric_field"]
        for t in techniques
        if not t.get("requires_baseline") and payload[t["metric_field"]] is None
    ]
    assert not null_without_baseline

    null_with_baseline = [
        t["metric_field"]
        for t in techniques
        if t.get("requires_baseline") and payload[t["metric_field"]] is None
    ]
    assert not null_with_baseline


def test_excel_aligned_formulas(tmp_path):
    cov = tmp_path / "coverage.json"
    _write_json(cov, FIXTURE)
    metrics = compute_metrics(cov)

    assert metrics.unreachable_paths == 15 + 6
    assert metrics.nested_logic_risk == 20 - 14
    assert metrics.loop_path_risk == pytest.approx(70.0)
    assert metrics.error_path_risk == pytest.approx(70.0)
    assert metrics.boolean_accuracy == pytest.approx(70.0)
    assert metrics.cross_function_coverage == 85
    assert metrics.full_path_coverage_proxy == pytest.approx(85.0 * 70.0 / 100.0)
    assert metrics.automation_readiness == pytest.approx(155.0)
    assert metrics.quality_gate_pass is False  # branch 70 < threshold 80


def test_quality_gate_requires_statement_and_branch(tmp_path):
    cov = tmp_path / "coverage.json"
    payload = dict(FIXTURE)
    payload["totals"]["percent_covered"] = 90.0
    payload["totals"]["percent_branches_covered"] = 60.0
    _write_json(cov, payload)

    metrics = compute_metrics(cov, quality_threshold=80.0)
    assert metrics.quality_gate_pass is False

    payload["totals"]["percent_branches_covered"] = 85.0
    _write_json(cov, payload)
    metrics = compute_metrics(cov, quality_threshold=80.0)
    assert metrics.quality_gate_pass is True
