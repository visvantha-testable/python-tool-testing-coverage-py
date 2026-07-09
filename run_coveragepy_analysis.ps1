param(
    [string]$WorkDir = "$PSScriptRoot\work",
    [string]$CoveragePyUrl = "https://github.com/nedbat/coveragepy.git"
)

$ErrorActionPreference = "Stop"
$RepoDir = Join-Path $WorkDir "coveragepy"

New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null

if (-not (Test-Path $RepoDir)) {
    git clone --depth 1 $CoveragePyUrl $RepoDir
}

python -m pip install -r "$PSScriptRoot\requirements.txt" -q
python -m pip install hypothesis -q

Push-Location $RepoDir
$env:PYTHONPATH = "."

# Baseline run (smaller test set) for Coverage Delta metrics
python -m coverage erase
python -m coverage run --branch -m pytest tests/test_version.py -o "addopts=" -q
python -m coverage json -o coverage_baseline.json

# Current run (main coverage test suite)
python -m coverage erase
python -m coverage run --branch -m pytest tests/test_coverage.py -o "addopts=" -q
python -m coverage json -o coverage.json

Pop-Location

python "$PSScriptRoot\coverage_py_metrics.py" `
    --coverage-json "$RepoDir\coverage.json" `
    --baseline-json "$RepoDir\coverage_baseline.json" `
    --source "$RepoDir\coverage" `
    --repo-url "https://github.com/nedbat/coveragepy" `
    --output-json "$PSScriptRoot\reports\coveragepy_metrics.json"

python "$PSScriptRoot\validate_technique_coverage.py" `
    --coverage-json "$RepoDir\coverage.json" `
    --baseline-json "$RepoDir\coverage_baseline.json" `
    --source "$RepoDir\coverage"
