# Python Tool Testing — Coverage.py

White Box metric validation using **coverage.py** only, aligned with *Testable Strategy & Metrics Reference v3.0*.

Covers the metric groups shown in the strategy mapping:

- Cyclomatic Complexity (Decision Coverage)
- Statement Coverage
- Branch Coverage
- Path Coverage
- Coverage Delta

## Recommended Target Repository

| Field | Value |
|-------|-------|
| **Repository** | [nedbat/coveragepy](https://github.com/nedbat/coveragepy) |
| **Tool** | coverage.py (Primary) |
| **Secondary tools** | pytest-cov, mccabe, AST path proxy |

**Why coveragepy?** It is the official coverage.py codebase with a comprehensive pytest suite. Running `coverage run --branch` on its own tests produces statement, branch, path-proxy, and delta metrics directly from coverage.py JSON output.

## Quick Start

```powershell
python -m pip install -r requirements.txt
python -m pytest tests/ -q
```

### Full pipeline (analyze coveragepy)

```powershell
.\run_coveragepy_analysis.ps1
```

### Manual run

```powershell
git clone https://github.com/nedbat/coveragepy.git work/coveragepy
cd work/coveragepy
pip install -e .
python -m coverage run --branch -m pytest tests/ -q
python -m coverage json -o coverage.json
cd ../..
python coverage_py_metrics.py `
  --coverage-json work/coveragepy/coverage.json `
  --source work/coveragepy/coverage `
  --repo-url https://github.com/nedbat/coveragepy `
  --output-json reports/coveragepy_metrics.json
```

### Coverage Delta (optional baseline)

```powershell
python coverage_py_metrics.py `
  --coverage-json work/coveragepy/coverage.json `
  --baseline-json work/coveragepy/coverage_baseline.json
```

### Validate all techniques are covered

```powershell
python validate_technique_coverage.py `
  --coverage-json work/coveragepy/coverage.json `
  --baseline-json work/coveragepy/coverage_baseline.json `
  --source work/coveragepy/coverage
```

See `config/technique_coverage.json` for the full mapping of all 29 Excel techniques to metric fields.

See `config/target_repo.json` for machine-readable mapping and formulas.
See `config/execution_trigger.json` for exact commands and expected output.

## Execution (trigger data)

| Input | Value |
|-------|-------|
| **Subject repo** | `https://github.com/nedbat/coveragepy` |
| **Source root (AST proxy)** | `work/coveragepy/coverage` |
| **coverage.py JSON** | `work/coveragepy/coverage.json` (after `coverage run --branch`) |
| **One-shot script** | `.\run_coveragepy_analysis.ps1` |

Expected metrics after running against coveragepy (`tests/test_coverage.py`, 72 tests):

| Metric | Expected value |
|--------|----------------|
| Statement Coverage % | 55.02% |
| Branch Coverage % | 19.57% |
| Path Coverage % (proxy) | 37.29% |
| Decision Coverage | 19.57% |
| Dead code lines | 302 |
| Path execution proxy | 460 |
| AST decision points | 1057 |
| AST loop nodes | 257 |
| Statements / covered / missing | 744 / 442 / 302 |
| Branches / covered / missing | 92 / 18 / 74 |

```
python-tool-testing-coverage-py/
├── coverage_py_metrics.py         # Metric extractor from coverage JSON
├── validate_technique_coverage.py # Verifies all 29 techniques are covered
├── config/
│   ├── target_repo.json           # Strategy/metric/tool mapping
│   ├── technique_coverage.json    # Excel technique → metric field map
│   └── execution_trigger.json     # Exact commands + expected output
├── run_coveragepy_analysis.ps1    # End-to-end coveragepy pipeline
├── requirements.txt
└── tests/
```

## References

- [coverage.py](https://github.com/nedbat/coveragepy)
- [coverage.py docs](https://coverage.readthedocs.io/)
