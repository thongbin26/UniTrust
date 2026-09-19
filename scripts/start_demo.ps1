param(
    [ValidateRange(1, 3600)][int]$BackendTimeout = 180,
    [ValidateRange(1, 3600)][int]$FrontendTimeout = 60
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    Write-Host "[FAIL] Missing .venv\Scripts\python.exe. Prepare the project environment first." -ForegroundColor Red
    exit 1
}

# One foreground supervisor owns both services and handles Ctrl+C cleanup.
# No extra terminal windows, shell-built process commands, or broad process kills.
Push-Location -LiteralPath $ProjectRoot
try {
    & $Python -B -u scripts/start_demo.py --backend-timeout $BackendTimeout --frontend-timeout $FrontendTimeout
    $ExitCode = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $ExitCode
