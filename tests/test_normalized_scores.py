"""Verify normalized dashboard scores reach 100% on fully covered sample."""

import json
import pathlib
import subprocess
import sys

import pytest

from coverage_py_metrics import compute_metrics, compute_normalized_scores


ROOT = pathlib.Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "sample_subject"


@pytest.fixture(scope="module")
def sample_coverage_files():
    subprocess.run(
        [sys.executable, "-m", "coverage", "erase"],
        cwd=SAMPLE,
        check=True,
    )
    subprocess.run(
        [sys.executable, "-m", "coverage", "run", "--branch", "-m", "pytest", "tests/test_flow_demo.py", "-q"],
        cwd=SAMPLE,
        check=True,
    )
    cov = SAMPLE / "coverage.json"
    subprocess.run(
        [sys.executable, "-m", "coverage", "json", "-o", str(cov.name)],
        cwd=SAMPLE,
        check=True,
    )
    return cov, SAMPLE / "app"


def test_sample_subject_100_percent_coverage(sample_coverage_files):
    cov_path, source = sample_coverage_files
    metrics = compute_metrics(cov_path, source_root=source)
    assert metrics.statement_coverage_percent == pytest.approx(100.0)
    assert metrics.branch_coverage_percent == pytest.approx(100.0)
    assert metrics.missing_lines == 0
    assert metrics.missing_branches == 0


def test_branch_metrics_emit_0_to_100_scale(sample_coverage_files):
    cov_path, source = sample_coverage_files
    metrics = compute_metrics(cov_path, source_root=source)
    assert metrics.boolean_accuracy == pytest.approx(100.0)
    assert metrics.control_flow_integrity == pytest.approx(100.0)
    assert metrics.loop_boundary_risk == pytest.approx(100.0)
    assert metrics.branch_coverage_percent == pytest.approx(100.0)
    assert metrics.decision_coverage == pytest.approx(100.0)


def test_normalized_scores_all_pass(sample_coverage_files):
    cov_path, source = sample_coverage_files
    metrics = compute_metrics(cov_path, source_root=source)
    scores = compute_normalized_scores(metrics)

    failing = {name: score for name, score in scores.items() if score < 100.0}
    assert not failing, f"Scores below 100: {failing}"
