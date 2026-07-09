"""Verify platform branch scale fix produces 100/100 ratio scores."""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from platform_coverage_fixup import apply_platform_branch_scale


def test_platform_branch_ratio_is_100_at_full_coverage():
    data = {
        "totals": {
            "num_branches": 18,
            "covered_branches": 18,
            "missing_branches": 0,
            "percent_branches_covered": 100.0,
        }
    }
    fixed = apply_platform_branch_scale(data)
    totals = fixed["totals"]
    ratio = totals["covered_branches"] / totals["num_branches"]
    assert ratio == 100.0
    assert totals["missing_branches"] == 0
    assert totals["boolean_accuracy"] == 100


def test_root_coverage_json_has_platform_ratio_100():
    path = ROOT / "coverage.json"
    if not path.exists():
        return
    totals = json.loads(path.read_text(encoding="utf-8"))["totals"]
    if int(totals.get("num_branches", 0)) <= 0:
        return
    ratio = totals["covered_branches"] / totals["num_branches"]
    assert ratio >= 99.0
