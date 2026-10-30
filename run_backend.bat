@echo off
title EditMind AI - Dedicated Backend Server (FastAPI Port 8000)
cd /d "%~dp0"

echo ======================================================================
echo           EditMind AI -- Dedicated Backend Server
echo    FastAPI + AI Video Pipeline + Local Qwen 2.5 + SQLite
echo ======================================================================
echo.

if exist "%~dp0.venv\Scripts\python.exe" (
    echo [*] Using virtual environment .venv ...
    "%~dp0.venv\Scripts\python.exe" "%~dp0run_backend.py"
) else (
    echo [*] Using system Python ...
    python "%~dp0run_backend.py"
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Backend exited with error code %ERRORLEVEL%.
    pause
)
