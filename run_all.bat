@echo off
setlocal EnableDelayedExpansion
title EditMind AI — Autonomous Video Editing Pipeline

echo ======================================================================
echo        EditMind AI — Automated Setup & Full-Stack Launcher
echo ======================================================================

cd /d "%~dp0"

:: 1. Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ from python.org and check "Add python.exe to PATH".
    pause
    exit /b 1
)

:: 2. Create or verify virtual environment (.venv)
if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Creating virtual environment (.venv)...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create .venv!
        pause
        exit /b 1
    )
    echo       Virtual environment created successfully.
) else (
    echo [1/4] Existing virtual environment (.venv) detected.
)

:: 3. Activate virtual environment
call .venv\Scripts\activate.bat

:: 4. Install & verify backend requirements
echo [2/4] Installing / verifying Python backend & pipeline dependencies...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Root requirements install had issues. Trying EditAI requirements...
    pip install -r EditAI\backend\requirements.txt
)

:: 5. Verify Frontend Build (dist)
echo [3/4] Verifying frontend UI requirements...
if not exist "EditAI\frontend\dist\index.html" (
    echo       Frontend dist missing. Checking Node.js / npm...
    where npm >nul 2>&1
    if %errorlevel% equ 0 (
        echo       Building frontend with npm...
        cd EditAI\frontend
        call npm install
        call npm run build
        cd ..\..
    ) else (
        echo [WARNING] Node.js is not found on PATH and dist/ is missing.
    )
) else (
    echo       Pre-compiled frontend bundle verified.
)

:: 6. Launch Full Application via run_all.py
echo [4/4] Starting backend server and connecting pipeline...
python run_all.py

pause

