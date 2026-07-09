"""White Box metrics extracted from coverage.py JSON reports.

Covers Cyclomatic Complexity, Statement Coverage, Branch Coverage,
Path Coverage, and Coverage Delta groups from Testable Strategy v3.0.
"""

from __future__ import annotations

import argparse
import ast
import json
import pathlib
import sys
from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass
class CoveragePyMetrics:
    # Cyclomatic / decision
    decision_coverage: float

    # Statement coverage
    granularity_proxy: float
    dead_code: int
    coverage_gap: float
    basic_validation: float
    statement_coverage_percent: float

    # Branch coverage
    boolean_accuracy: float
    control_flow_integrity: int
    loop_boundary_risk: int
    edge_case_risk: float
    branch_misdirection: int
    decision_gap: float
    branch_coverage_percent: float

    # Path coverage
    path_execution_proxy: int
    full_logic_validation: bool
    full_path_coverage_proxy: float
    partial_path_gaps: int
    nested_logic_risk: int
    loop_path_risk: int
    nested_condition_paths: int
    loop_paths: int
    unreachable_paths: int
    error_path_risk: int
    exception_paths: int
    cross_function_coverage: int
    multi_function_paths: int
    automation_readiness: float
    quality_gate_pass: bool
    path_coverage_percent: float

    # Coverage delta (optional baseline)
    coverage_delta_percent: float | None
    discovery_power: int | None
    impact_ratio: float | None
    new_code_coverage: int | None
    quality_improvement: float | None
    branch_delta_percent: float | None

    # Raw totals
    num_statements: int
    covered_lines: int
    missing_lines: int
    num_branches: int
    covered_branches: int
    missing_branches: int
    file_count: int
    ast_decision_points: int
    ast_loop_nodes: int
    ast_try_except_nodes: int


def compute_normalized_scores(metrics: CoveragePyMetrics) -> dict[str, float]:
    """Map raw metrics to 0-100 dashboard scores per Excel normalisation formulas."""
    stmt = metrics.statement_coverage_percent
    branch = metrics.branch_coverage_percent
    dead_code_pct = (metrics.dead_code / max(metrics.num_statements, 1)) * 100.0
    coverage_gap_pct = metrics.coverage_gap * 100.0
    decision_gap_pct = metrics.decision_gap * 100.0
    edge_case_pct = metrics.edge_case_risk * 100.0
    path_gap_pct = (
        metrics.partial_path_gaps / max(metrics.num_statements + metrics.num_branches, 1)
    ) * 100.0
    boolean_pct = metrics.boolean_accuracy * 100.0
    nested_pct = (
        (metrics.num_branches - metrics.nested_logic_risk) / max(metrics.num_branches, 1)
    ) * 100.0
    path_exec_pct = min(
        100.0,
        (metrics.path_execution_proxy / max(metrics.num_statements + metrics.num_branches, 1))
        * 100.0,
    )
    cross_function_pct = min(
        100.0,
        (metrics.cross_function_coverage / max(metrics.num_statements, 1)) * 100.0,
    )
    granularity_pct = min(100.0, stmt)

    return {
        "Decision Coverage": branch,
        "Unit Testing Support": granularity_pct,
        "Dead Code Detection": max(0.0, 100.0 - dead_code_pct * 25.0),
        "Test Completeness Evaluation": max(0.0, 100.0 - coverage_gap_pct),
        "Basic Logic Validation": stmt,
        "Code Execution Verification": stmt,
        "Conditional Logic Testing": boolean_pct,
        "Control Flow Validation": boolean_pct,
        "Loop Condition Testing": branch,
        "Edge Case Detection": max(0.0, 100.0 - edge_case_pct * 50.0),
        "Logic Error Detection": max(0.0, 100.0 - metrics.branch_misdirection * 20.0),
        "Test Case Completeness": max(0.0, 100.0 - decision_gap_pct),
        "Decision Outcome Verification": branch,
        "Path Execution Tracking": path_exec_pct,
        "Complete Coverage Path Verification": metrics.full_path_coverage_proxy,
        "Partial Path Coverage Detection": max(0.0, 100.0 - path_gap_pct),
        "Nested Condition Path Testing": nested_pct,
        "Loop Path Detection": branch,
        "Unreachable Path Detection": max(0.0, 100.0 - path_gap_pct * 25.0),
        "Exception Path Handling": branch,
        "Multi-Function Path Tracking": cross_function_pct,
        "CI/CD Integration Test": min(100.0, metrics.automation_readiness / 2.0),
        "Path Detection Testing": metrics.path_coverage_percent,
    }


def _load_totals(path: pathlib.Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    totals = data.get("totals", {})
    files = data.get("files", {})
    cross_function_coverage = 0
    for file_data in files.values():
        summary = file_data.get("summary", {})
        cross_function_coverage += int(summary.get("covered_lines", 0))
    if cross_function_coverage == 0:
        cross_function_coverage = int(totals.get("covered_lines", 0))
    return {
        "percent_covered": float(totals.get("percent_covered", 0.0)),
        "percent_branches_covered": float(totals.get("percent_branches_covered", 0.0)),
        "num_statements": int(totals.get("num_statements", 0)),
        "covered_lines": int(totals.get("covered_lines", 0)),
        "missing_lines": int(totals.get("missing_lines", 0)),
        "num_branches": int(totals.get("num_branches", 0)),
        "covered_branches": int(totals.get("covered_branches", 0)),
        "missing_branches": int(totals.get("missing_branches", 0)),
        "file_count": len(files),
        "cross_function_coverage": cross_function_coverage,
    }


def _count_ast_patterns(source_root: pathlib.Path) -> tuple[int, int, int]:
    decision_points = 0
    loop_nodes = 0
    try_except_nodes = 0

    for path in sorted(source_root.rglob("*.py")):
        if any(part.startswith(".") for part in path.parts):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.IfExp, ast.Match)):
                decision_points += 1
            elif isinstance(node, (ast.For, ast.While, ast.AsyncFor)):
                loop_nodes += 1
            elif isinstance(node, ast.Try):
                try_except_nodes += 1

    return decision_points, loop_nodes, try_except_nodes


def compute_metrics(
    coverage_json: pathlib.Path,
    source_root: pathlib.Path | None = None,
    baseline_json: pathlib.Path | None = None,
    quality_threshold: float = 80.0,
) -> CoveragePyMetrics:
    current = _load_totals(coverage_json)
    baseline = _load_totals(baseline_json) if baseline_json and baseline_json.exists() else None

    decision_points = loop_nodes = try_except_nodes = 0
    if source_root and source_root.is_dir():
        decision_points, loop_nodes, try_except_nodes = _count_ast_patterns(source_root)

    num_branches = current["num_branches"]
    missing_branches = current["missing_branches"]
    covered_branches = current["covered_branches"]
    num_statements = current["num_statements"]
    missing_lines = current["missing_lines"]
    file_count = max(current["file_count"], 1)

    percent_covered = current["percent_covered"]
    percent_branches = current["percent_branches_covered"]

    coverage_delta = branch_delta = discovery_power = new_code = quality_improvement = impact = None
    if baseline:
        coverage_delta = percent_covered - baseline["percent_covered"]
        branch_delta = percent_branches - baseline["percent_branches_covered"]
        discovery_power = baseline["missing_lines"] - current["missing_lines"]
        new_code = current["covered_lines"] - baseline["covered_lines"]
        quality_improvement = (coverage_delta + branch_delta) / 2
        impact = abs(coverage_delta) / max(baseline["percent_covered"], 0.01)

    quality_gate_pass = (
        percent_covered >= quality_threshold and percent_branches >= quality_threshold
    )

    return CoveragePyMetrics(
        decision_coverage=covered_branches / max(num_branches, 1),
        granularity_proxy=num_statements / file_count,
        dead_code=missing_lines,
        coverage_gap=missing_lines / max(num_statements, 1),
        basic_validation=percent_covered,
        statement_coverage_percent=percent_covered,
        boolean_accuracy=covered_branches / max(num_branches, 1),
        control_flow_integrity=covered_branches - missing_branches,
        loop_boundary_risk=missing_branches,
        edge_case_risk=missing_branches / max(num_branches, 1),
        branch_misdirection=missing_branches,
        decision_gap=missing_branches / max(num_branches, 1),
        branch_coverage_percent=percent_branches,
        path_execution_proxy=current["covered_lines"] + covered_branches,
        full_logic_validation=percent_covered >= 90.0 and percent_branches >= 90.0,
        full_path_coverage_proxy=percent_covered * percent_branches / 100.0,
        partial_path_gaps=missing_lines + missing_branches,
        nested_logic_risk=num_branches - covered_branches,
        loop_path_risk=missing_branches,
        nested_condition_paths=decision_points,
        loop_paths=loop_nodes,
        unreachable_paths=missing_lines + missing_branches,
        error_path_risk=missing_branches,
        exception_paths=try_except_nodes,
        cross_function_coverage=current["cross_function_coverage"],
        multi_function_paths=file_count,
        automation_readiness=percent_covered + percent_branches,
        quality_gate_pass=quality_gate_pass,
        path_coverage_percent=(percent_covered + percent_branches) / 2,
        coverage_delta_percent=coverage_delta,
        discovery_power=discovery_power,
        impact_ratio=impact,
        new_code_coverage=new_code,
        quality_improvement=quality_improvement,
        branch_delta_percent=branch_delta,
        num_statements=num_statements,
        covered_lines=current["covered_lines"],
        missing_lines=missing_lines,
        num_branches=num_branches,
        covered_branches=covered_branches,
        missing_branches=missing_branches,
        file_count=file_count,
        ast_decision_points=decision_points,
        ast_loop_nodes=loop_nodes,
        ast_try_except_nodes=try_except_nodes,
    )


def _print_report(metrics: CoveragePyMetrics, repo_url: str | None) -> None:
    print("=" * 72)
    print("Coverage.py Metrics Report")
    print("=" * 72)
    if repo_url:
        print(f"Target repository: {repo_url}")
    print()

    sections = [
        ("Cyclomatic Complexity", [
            ("Decision Outcome Verification", f"{metrics.decision_coverage:.2%}"),
        ]),
        ("Statement Coverage", [
            ("Test Case Granularity (proxy)", f"{metrics.granularity_proxy:.2f}"),
            ("Unreachable Logic (dead code lines)", metrics.dead_code),
            ("Coverage Gap Analysis", f"{metrics.coverage_gap:.2%}"),
            ("Surface-Level Correctness", f"{metrics.basic_validation:.2f}%"),
            ("Statement Coverage %", f"{metrics.statement_coverage_percent:.2f}%"),
        ]),
        ("Branch Coverage", [
            ("Boolean Accuracy Check", f"{metrics.boolean_accuracy:.2%}"),
            ("Sequence Integrity Mapping", metrics.control_flow_integrity),
            ("Iteration Boundary Verification (missing branches)", metrics.loop_boundary_risk),
            ("Boundary Failure Identification", f"{metrics.edge_case_risk:.2%}"),
            ("Branch Misdirection Discovery", metrics.branch_misdirection),
            ("Decision Coverage Gap Analysis", f"{metrics.decision_gap:.2%}"),
            ("Branch Coverage %", f"{metrics.branch_coverage_percent:.2f}%"),
        ]),
        ("Path Coverage", [
            ("Path Execution Proxy", metrics.path_execution_proxy),
            ("Full Logic Validation (>=90%)", metrics.full_logic_validation),
            ("Full Path Coverage Proxy", f"{metrics.full_path_coverage_proxy:.2f}%"),
            ("Gap Identification", metrics.partial_path_gaps),
            ("Deep Logic Probing (nested logic risk)", metrics.nested_logic_risk),
            ("Deep Logic Probing (AST decisions)", metrics.nested_condition_paths),
            ("Iterative Route Analysis (loop path risk)", metrics.loop_path_risk),
            ("Iterative Route Analysis (AST loops)", metrics.loop_paths),
            ("Ghost Code Discovery", metrics.unreachable_paths),
            ("Error Flow Verification (error path risk)", metrics.error_path_risk),
            ("Error Flow Verification (try/except AST)", metrics.exception_paths),
            ("Cross-Component Mapping (covered lines)", metrics.cross_function_coverage),
            ("Cross-Component Mapping (files)", metrics.multi_function_paths),
            ("Automated Quality Readiness", f"{metrics.automation_readiness:.2f}%"),
            ("Automated Quality Gate", metrics.quality_gate_pass),
            ("Path Coverage % (proxy)", f"{metrics.path_coverage_percent:.2f}%"),
        ]),
    ]

    for title, rows in sections:
        print(title)
        print("-" * len(title))
        for label, value in rows:
            print(f"  {label:<44} {value}")
        print()

    if metrics.coverage_delta_percent is not None:
        print("Coverage Delta")
        print("--------------")
        delta_rows = [
            ("Coverage Delta %", f"{metrics.coverage_delta_percent:+.2f}%"),
            ("Discovery Power Assessment", metrics.discovery_power),
            ("Deployment Readiness Guard", metrics.quality_gate_pass),
            ("Ripple Effect Mapping", f"{metrics.impact_ratio:.4f}" if metrics.impact_ratio is not None else "N/A"),
            ("Fresh Logic Proofing", metrics.new_code_coverage),
            ("Structural Health Benchmarking", f"{metrics.quality_improvement:+.2f}%" if metrics.quality_improvement is not None else "N/A"),
        ]
        for label, value in delta_rows:
            print(f"  {label:<44} {value}")
        print()

    print("Raw totals")
    print("----------")
    print(f"  statements={metrics.num_statements} covered={metrics.covered_lines} missing={metrics.missing_lines}")
    print(f"  branches={metrics.num_branches} covered={metrics.covered_branches} missing={metrics.missing_branches}")

    scores = compute_normalized_scores(metrics)
    print()
    print("Normalized Dashboard Scores (0-100)")
    print("---------------------------------")
    for name, score in scores.items():
        status = "PASS" if score >= 80.0 else ("WARN" if score >= 60.0 else "FAIL")
        print(f"  {name:<42} {score:6.2f}/100  {status}")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage-json", type=pathlib.Path, required=True)
    parser.add_argument("--source", type=pathlib.Path, default=None)
    parser.add_argument("--baseline-json", type=pathlib.Path, default=None)
    parser.add_argument("--quality-threshold", type=float, default=80.0)
    parser.add_argument("--repo-url", default=None)
    parser.add_argument("--output-json", type=pathlib.Path, default=None)
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not args.coverage_json.is_file():
        print(f"Coverage JSON not found: {args.coverage_json}", file=sys.stderr)
        return 1

    metrics = compute_metrics(
        args.coverage_json,
        source_root=args.source,
        baseline_json=args.baseline_json,
        quality_threshold=args.quality_threshold,
    )
    _print_report(metrics, args.repo_url)

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(metrics)
        payload["normalized_scores"] = compute_normalized_scores(metrics)
        args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote {args.output_json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
