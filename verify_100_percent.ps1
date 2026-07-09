param(
    [string]$MetricsJson = "$PSScriptRoot\coveragepy_metrics.json",
    [string]$DashboardJson = "$PSScriptRoot\dashboard_metrics.json"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $MetricsJson)) {
    Write-Error "Missing metrics file: $MetricsJson. Run .\run_coveragepy_analysis.ps1 first."
}

python "$PSScriptRoot\scripts\verify_100_percent.py" `
    --metrics-json $MetricsJson `
    --dashboard-json $DashboardJson

if ($LASTEXITCODE -ne 0) {
    Write-Error "100% verification FAILED. Do not submit to testing team until fixed."
}

Write-Host ""
Write-Host "SUCCESS: All metrics are 100/100 PASS" -ForegroundColor Green
Write-Host "Submit these ROOT files to the testing platform:"
Write-Host "  coverage input  : coverage.json"
Write-Host "  dashboard scores: platform_metrics.json"
Write-Host "  full metrics    : coveragepy_metrics.json"
