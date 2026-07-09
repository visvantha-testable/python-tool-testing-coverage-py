"""Tests for coverage.py metric extraction."""

import json
import pathlib
import subprocess
import sys

import pytest

from coverage_py_metrics import compute_metrics


FIXTURE = {
    "files": {
        "a.py": {},
        "b.py": {},
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
    "files": {"a.py": {}},
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


def test_compute_metrics_from_fixture(tmp_path):
    cov = tmp_path / "coverage.json"
    _write_json(cov, FIXTURE)

    metrics = compute_metrics(cov)
    assert metrics.statement_coverage_percent == pytest.approx(85.0)
    assert metrics.branch_coverage_percent == pytest.approx(70.0)
    assert metrics.dead_code == 15
    assert metrics.decision_coverage == pytest.approx(0.7)
    assert metrics.path_coverage_percent == pytest.approx(77.5)
    assert metrics.path_execution_proxy == 99
    assert metrics.quality_gate_pass is False


def test_coverage_delta_with_baseline(tmp_path):
    cov = tmp_path / "coverage.json"
    base = tmp_path / "baseline.json"
    _write_json(cov, FIXTURE)
    _write_json(base, BASELINE)

    metrics = compute_metrics(cov, baseline_json=base)
    assert metrics.coverage_delta_percent == pytest.approx(5.0)
    assert metrics.discovery_power == 4
    assert metrics.new_code_coverage == 9


def test_ast_patterns_on_sample(tmp_path):
    sample = tmp_path / "sample.py"
    sample.write_text(
        "def f(x):\n"
        "    for i in range(x):\n"
        "        if i:\n"
        "            return i\n"
        "    try:\n"
        "        return x\n"
        "    except ValueError:\n"
        "        return 0\n",
        encoding="utf-8",
    )
    cov = tmp_path / "coverage.json"
    _write_json(cov, FIXTURE)

    metrics = compute_metrics(cov, source_root=tmp_path)
    assert metrics.nested_condition_paths >= 1
    assert metrics.loop_paths >= 1
    assert metrics.exception_paths >= 1


def test_cli_runs(tmp_path):
    cov = tmp_path / "coverage.json"
    _write_json(cov, FIXTURE)
    result = subprocess.run(
        [
            sys.executable,
            str(pathlib.Path(__file__).resolve().parents[1] / "coverage_py_metrics.py"),
            "--coverage-json",
            str(cov),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Coverage.py Metrics Report" in result.stdout
