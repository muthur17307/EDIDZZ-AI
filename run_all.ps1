# PowerShell Master Setup & Full-Stack Launcher for EditMind AI
$Host.UI.RawUI.WindowTitle = "EditMind AI — Full Stack Launcher"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "       EditMind AI — Automated Setup & Full-Stack Launcher" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RootDir

# 1. Verify Python
try {
    $pyVer = & python --version 2>&1
    Write-Host "[OK] Detected: $pyVer" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python was not found in PATH! Please install Python 3.10+." -ForegroundColor Red
    Pause
    Exit 1
}

# 2. Setup Virtual Environment
$VenvPy = Join-Path $RootDir ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPy)) {
    Write-Host "[1/4] Creating virtual environment (.venv)..." -ForegroundColor Magenta
    & python -m venv .venv
    Write-Host "[OK] Virtual environment created." -ForegroundColor Green
} else {
    Write-Host "[1/4] Existing virtual environment detected." -ForegroundColor DarkGray
}

# 3. Activate Virtual Environment
$ActivateScript = Join-Path $RootDir ".venv\Scripts\Activate.ps1"
if (Test-Path $ActivateScript) {
    & $ActivateScript
}

# 4. Install Dependencies
Write-Host "[2/4] Verifying Python backend & pipeline dependencies..." -ForegroundColor Magenta
& $VenvPy -m pip install --upgrade pip --quiet
& $VenvPy -m pip install -r requirements.txt

# 5. Check Frontend Requirements
Write-Host "[3/4] Verifying frontend UI requirements..." -ForegroundColor Magenta
$DistHtml = Join-Path $RootDir "EditAI\frontend\dist\index.html"
if (-not (Test-Path $DistHtml)) {
    Write-Host "      Frontend dist missing. Checking for Node / npm..." -ForegroundColor Yellow
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        Push-Location (Join-Path $RootDir "EditAI\frontend")
        npm install
        npm run build
        Pop-Location
        Write-Host "[OK] Frontend build complete." -ForegroundColor Green
    } else {
        Write-Host "[WARN] Node.js is not on PATH and dist/ is not pre-built." -ForegroundColor Yellow
    }
} else {
    Write-Host "[OK] Pre-compiled frontend bundle verified." -ForegroundColor Green
}

# 6. Run Application
Write-Host "[4/4] Starting backend server and connecting pipeline..." -ForegroundColor Cyan
& $VenvPy run_all.py

