# EditMind AI - Split Runner (PowerShell)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "          EditMind AI -- Separate Processes Launcher" -ForegroundColor Cyan
Write-Host "   Window 1: FastAPI Backend (Port 8000)" -ForegroundColor Cyan
Write-Host "   Window 2: React 19 Frontend Dev Server (Port 5173)" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[*] Launching Backend in dedicated window..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-File", "`"$ScriptDir\run_backend.ps1`""

Start-Sleep -Seconds 2

Write-Host "[*] Launching Frontend in dedicated window..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-File", "`"$ScriptDir\run_frontend.ps1`""

Write-Host ""
Write-Host "[OK] Both services launched in separate windows!" -ForegroundColor Green
Write-Host "     - Backend API  : http://127.0.0.1:8000 (Docs: http://127.0.0.1:8000/docs)"
Write-Host "     - Frontend App : http://localhost:5173"

