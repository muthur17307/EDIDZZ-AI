# EditMind AI - Dedicated Backend Server (PowerShell)
$Host.UI.RawUI.WindowTitle = "EditMind AI - Dedicated Backend Server (Port 8000)"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "          EditMind AI -- Dedicated Backend Server" -ForegroundColor Cyan
Write-Host "   FastAPI + AI Video Pipeline + Local Qwen 2.5 + SQLite" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

$VenvPython = Join-Path $ScriptDir ".venv\Scripts\python.exe"

if (Test-Path $VenvPython) {
    Write-Host "[*] Launching with virtual environment (.venv)..." -ForegroundColor Green
    & $VenvPython "$ScriptDir\run_backend.py"
} else {
    Write-Host "[*] Virtual environment not found, launching with system python..." -ForegroundColor Yellow
    python "$ScriptDir\run_backend.py"
}

