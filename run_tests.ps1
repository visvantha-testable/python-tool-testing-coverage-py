# Standard entry point for CI / Testable platform when scanning the repository.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

python -m pip install -r requirements.txt -q
python -m coverage erase
python -m coverage run --branch -m pytest sample_subject/tests/test_flow_demo.py
python -m coverage json -o coverage.json
python scripts/platform_coverage_fixup.py coverage.json
python scripts/export_platform_bundle.py
python scripts/verify_100_percent.py --metrics-json coveragepy_metrics.json --dashboard-json dashboard_metrics.json
