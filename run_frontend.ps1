# EditMind AI - Dedicated Frontend Dev Server (PowerShell)
$Host.UI.RawUI.WindowTitle = "EditMind AI - Dedicated Frontend Dev Server (Port 5173)"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "          EditMind AI -- Dedicated Frontend Dev Server" -ForegroundColor Cyan
Write-Host "   React 19 + Vite HMR + TailwindCSS (Port 5173)" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

$FrontendDir = Join-Path $ScriptDir "EditAI\frontend"

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Node.js is not found in PATH!" -ForegroundColor Red
    Write-Host "Please install Node.js from https://nodejs.org/"
    pause
    exit 1
}

Set-Location $FrontendDir

if (-not (Test-Path "node_modules")) {
    Write-Host "[*] Installing frontend dependencies (npm install)..." -ForegroundColor Yellow
    npm install
}

Write-Host "[*] Starting Vite Dev Server on http://localhost:5173 ..." -ForegroundColor Green
npm run dev

