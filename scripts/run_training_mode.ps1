# One-click runner for hands-off training mode
$repoRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $repoRoot

$VENV = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
if (-Not (Test-Path $VENV)) {
    Write-Error ".venv Python not found at $VENV. Please create and install dependencies in .venv."
    exit 1
}
Write-Host "Using venv: $VENV"

& $VENV jobs\training_runner.py --mode train --reason "manual_one_click"
& $VENV jobs\weekly_digest.py

Write-Host "--- Output paths ---"
Write-Host "Digest: output\weekly_digest.md"
Write-Host "Log: logs\training_runner.log"
Write-Host "--- Last 10 lines of log ---"
Get-Content logs\training_runner.log -Tail 10
