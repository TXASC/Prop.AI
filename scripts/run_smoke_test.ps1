# One-click runner for OddsAdapter smoke test
$repoRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $repoRoot
$smokeTest = Join-Path $repoRoot 'scripts\smoke_test_odds_adapter.py'
if (Test-Path .venv) {
    $pythonExe = ".\.venv\Scripts\python.exe"
    Write-Host "Using venv: $pythonExe"
    & $pythonExe $smokeTest
} else {
    $pythonExe = "python"
    Write-Host "Using system python: $pythonExe"
    & $pythonExe $smokeTest
}
