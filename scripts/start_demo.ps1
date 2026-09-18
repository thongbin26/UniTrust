$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = (Resolve-Path "$ScriptDir\..").Path

Write-Host "--- UniTrust V2 Demo Startup ---" -ForegroundColor Cyan
Write-Host "Project Root: $ProjectRoot"

# 1. Verify .venv exists
$VenvPath = "$ProjectRoot\.venv"
if (-Not (Test-Path $VenvPath)) {
    Write-Host "❌ ERROR: .venv not found in $ProjectRoot. Please setup the virtual environment." -ForegroundColor Red
    exit 1
}

# 2. Set PYTHONPATH
$env:PYTHONPATH = $ProjectRoot
Write-Host "PYTHONPATH set to $ProjectRoot"

# 3. Invoke Preflight
Write-Host "Running Preflight Checks..." -ForegroundColor Cyan
& "$VenvPath\Scripts\python.exe" "$ProjectRoot\scripts\preflight_demo.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ERROR: Preflight checks FAILED. Aborting startup." -ForegroundColor Red
    exit 1
}

# 4. Start FastAPI
Write-Host "Starting FastAPI backend on 127.0.0.1:8000..." -ForegroundColor Cyan
$BackendProcess = Start-Process -FilePath "$VenvPath\Scripts\python.exe" -ArgumentList "-m uvicorn main:app --host 127.0.0.1 --port 8000" -PassThru -NoNewWindow
Write-Host "Backend Process ID: $($BackendProcess.Id)" -ForegroundColor Cyan
if ($BackendProcess.HasExited) {
    Write-Host "❌ ERROR: Backend failed to start. Port 8000 might be in use." -ForegroundColor Red
    exit 1
}

# 5. Poll /health
$HealthUrl = "http://127.0.0.1:8000/health"
$MaxAttempts = 30
$Attempt = 0
$BackendReady = $false

Write-Host "Waiting for backend to be ready..."
while ($Attempt -lt $MaxAttempts) {
    try {
        $Response = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -ErrorAction Stop
        if ($Response.StatusCode -eq 200) {
            $BackendReady = $true
            break
        }
    } catch {
        # ignore error and wait
    }
    Start-Sleep -Seconds 1
    $Attempt++
    Write-Host -NoNewline "."
}
Write-Host ""

if (-Not $BackendReady) {
    Write-Host "❌ ERROR: Backend failed to become healthy within $($MaxAttempts) seconds." -ForegroundColor Red
    Stop-Process -Id $BackendProcess.Id -Force
    exit 1
}
Write-Host "✅ Backend is healthy!" -ForegroundColor Green

# 6. Start Streamlit
Write-Host "Starting Streamlit frontend on 127.0.0.1:8501..." -ForegroundColor Cyan
$FrontendProcess = Start-Process -FilePath "$VenvPath\Scripts\streamlit.exe" -ArgumentList "run $ProjectRoot\frontend\Home.py --server.port 8501 --server.address 127.0.0.1" -PassThru -NoNewWindow
Write-Host "Frontend Process ID: $($FrontendProcess.Id)" -ForegroundColor Cyan
if ($FrontendProcess.HasExited) {
    Write-Host "❌ ERROR: Frontend failed to start. Port 8501 might be in use." -ForegroundColor Red
    Stop-Process -Id $BackendProcess.Id -Force
    exit 1
}

Write-Host "===============================================" -ForegroundColor Green
Write-Host "🚀 UniTrust V2 Demo is now running!" -ForegroundColor Green
Write-Host "Backend API: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Frontend UI: http://127.0.0.1:8501" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the servers. If processes linger, you may need to close this terminal." -ForegroundColor Yellow

try {
    # Keep script alive to hold processes
    Wait-Process -Id $BackendProcess.Id, $FrontendProcess.Id
} finally {
    Write-Host "Stopping processes..." -ForegroundColor Cyan
    if (-Not $BackendProcess.HasExited) { Stop-Process -Id $BackendProcess.Id -Force }
    if (-Not $FrontendProcess.HasExited) { Stop-Process -Id $FrontendProcess.Id -Force }
    Write-Host "Stopped cleanly." -ForegroundColor Green
}
