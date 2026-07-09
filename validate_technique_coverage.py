"""Validate that all Excel-mapped coverage.py techniques are implemented."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

from coverage_py_metrics import compute_metrics


def load_techniques(config_path: pathlib.Path) -> list[dict]:
    data = json.loads(config_path.read_text(encoding="utf-8"))
    return data["techniques"]


def validate(
    coverage_json: pathlib.Path,
    config_path: pathlib.Path,
    source_root: pathlib.Path | None = None,
    baseline_json: pathlib.Path | None = None,
) -> tuple[bool, list[str]]:
    techniques = load_techniques(config_path)
    metrics = compute_metrics(coverage_json, source_root=source_root, baseline_json=baseline_json)
    payload = metrics.__dict__
    errors: list[str] = []

    for entry in techniques:
        field = entry["metric_field"]
        if field not in payload:
            errors.append(f"Missing metric field: {field} ({entry['l3']} / {entry['l5']})")
            continue
        value = payload[field]
        if entry.get("requires_baseline") and value is None:
            errors.append(f"Baseline required but {field} is null ({entry['l5']})")
        elif not entry.get("requires_baseline") and value is None:
            errors.append(f"Expected value for {field} but got null ({entry['l5']})")

    return len(errors) == 0, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage-json", type=pathlib.Path, required=True)
    parser.add_argument(
        "--config",
        type=pathlib.Path,
        default=pathlib.Path(__file__).parent / "config" / "technique_coverage.json",
    )
    parser.add_argument("--source", type=pathlib.Path, default=None)
    parser.add_argument("--baseline-json", type=pathlib.Path, default=None)
    args = parser.parse_args()

    ok, errors = validate(args.coverage_json, args.config, args.source, args.baseline_json)
    techniques = load_techniques(args.config)
    print(f"Techniques mapped: {len(techniques)}")
    if ok:
        print("All coverage.py techniques are covered.")
        return 0

    print("Coverage gaps found:")
    for err in errors:
        print(f"  - {err}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
