# setup_windows.ps1
# Automates VPropTrader setup on Windows 11

Write-Host "🚀 Starting VPropTrader Setup for Windows..." -ForegroundColor Cyan

# 1. Check Prerequisites
Write-Host "`n[1/5] Checking Prerequisites..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python 3\.") {
        Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
        
        # Check for bleeding edge versions
        if ($pythonVersion -match "Python 3\.1[3-9]") {
            Write-Host "⚠️ WARNING: You are using a very new version of Python ($pythonVersion)." -ForegroundColor Yellow
            Write-Host "   Some libraries (numpy, pandas) may not have pre-built binaries yet." -ForegroundColor Yellow
            Write-Host "   If installation hangs, please install Python 3.11 or 3.12." -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ Python 3 not found! Please install Python 3.10+ and add to PATH." -ForegroundColor Red
        exit 1
    }

    $nodeVersion = node --version 2>&1
    if ($nodeVersion -match "v") {
        Write-Host "✅ Node.js found: $nodeVersion" -ForegroundColor Green
    } else {
        Write-Host "❌ Node.js not found! Please install Node.js LTS." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error checking prerequisites." -ForegroundColor Red
    exit 1
}

# 2. Setup Python Backend (Sidecar)
Write-Host "`n[2/5] Setting up Python Backend (Sidecar)..." -ForegroundColor Yellow
$SidecarPath = Join-Path $PSScriptRoot "sidecar"

if (-not (Test-Path $SidecarPath)) {
    Write-Host "❌ 'sidecar' directory not found!" -ForegroundColor Red
    exit 1
}

Push-Location $SidecarPath

# Create venv if not exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
} else {
    Write-Host "Virtual environment already exists."
}

# Activate venv and install requirements
Write-Host "Installing Python dependencies..."
.\venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt --prefer-binary

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install Python dependencies." -ForegroundColor Red
    Pop-Location
    exit 1
}

Write-Host "✅ Backend setup complete." -ForegroundColor Green
Pop-Location

# 3. Setup Electron Frontend
Write-Host "`n[3/5] Setting up Electron Frontend..." -ForegroundColor Yellow
$ElectronPath = Join-Path $PSScriptRoot "electron-app"

if (-not (Test-Path $ElectronPath)) {
    Write-Host "❌ 'electron-app' directory not found!" -ForegroundColor Red
    exit 1
}

Push-Location $ElectronPath
Write-Host "Installing Node dependencies..."
npm install

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install Node dependencies." -ForegroundColor Red
    Pop-Location
    exit 1
}

Write-Host "✅ Frontend setup complete." -ForegroundColor Green
Pop-Location

# 4. Create .env file
Write-Host "`n[4/5] Configuring Environment..." -ForegroundColor Yellow
$EnvPath = Join-Path $SidecarPath ".env"

if (-not (Test-Path $EnvPath)) {
    Write-Host "Creating .env file..."
    Set-Content -Path $EnvPath -Value "FRED_API_KEY=your_fred_api_key_here"
    Write-Host "⚠️ Created .env file. Please update it with your FRED API Key." -ForegroundColor Magenta
} else {
    Write-Host "✅ .env file already exists." -ForegroundColor Green
}

# 5. Final Instructions
Write-Host "`n[5/5] Setup Complete!" -ForegroundColor Green
Write-Host "`n🎉 VPropTrader is ready to launch!" -ForegroundColor Cyan
Write-Host "To start the system, run:"
Write-Host "  .\start_system.ps1" -ForegroundColor White
