# start_system.ps1
# Launches VPropTrader (Backend + Frontend) on Windows 11

Write-Host "🚀 Launching VPropTrader..." -ForegroundColor Cyan

$SidecarPath = Join-Path $PSScriptRoot "sidecar"
$ElectronPath = Join-Path $PSScriptRoot "electron-app"

# 1. Start Backend (Sidecar)
Write-Host "`n[1/2] Starting Backend (Sidecar)..." -ForegroundColor Yellow
if (-not (Test-Path $SidecarPath)) {
    Write-Host "❌ 'sidecar' directory not found!" -ForegroundColor Red
    exit 1
}

$VenvActivate = Join-Path $SidecarPath "venv\Scripts\activate.ps1"
if (-not (Test-Path $VenvActivate)) {
    Write-Host "❌ Virtual environment not found! Please run setup_windows.ps1 first." -ForegroundColor Red
    exit 1
}

# Start Uvicorn in a new process
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& {cd '$SidecarPath'; . '$VenvActivate'; uvicorn app.main:app --reload --host 127.0.0.1 --port 8001}"
Write-Host "✅ Backend started in a new window." -ForegroundColor Green

# 2. Start Frontend (Electron)
Write-Host "`n[2/2] Starting Frontend (Electron)..." -ForegroundColor Yellow
if (-not (Test-Path $ElectronPath)) {
    Write-Host "❌ 'electron-app' directory not found!" -ForegroundColor Red
    exit 1
}

Push-Location $ElectronPath
# Start Electron (this will block until closed, or we can use Start-Process)
# Using Start-Process to keep the main window free or just run it directly.
# Let's run it directly so we see logs here.
npm start
Pop-Location

Write-Host "`n👋 VPropTrader Session Ended." -ForegroundColor Cyan
