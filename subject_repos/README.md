# Subject Repositories

Vendored subject codebases used for coverage.py metric validation.

| Directory | Upstream | Purpose |
|-----------|----------|---------|
| `pytest-cov/` | [pytest-dev/pytest-cov](https://github.com/pytest-dev/pytest-cov) | pytest-cov plugin codebase; matches Excel trigger `pytest-cov --cov-branch` |

Run analysis:

```powershell
.\run_coveragepy_analysis.ps1 -Target pytest-cov
```
