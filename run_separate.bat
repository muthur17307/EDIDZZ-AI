@echo off
title EditMind AI - Split Runner (Frontend + Backend in Separate Windows)
cd /d "%~dp0"

echo ======================================================================
echo           EditMind AI -- Separate Processes Launcher
echo    Window 1: FastAPI Backend (Port 8000)
echo    Window 2: React 19 Frontend Dev Server (Port 5173)
echo ======================================================================
echo.

echo [*] Launching FastAPI Backend in dedicated window...
start "EditMind AI - Backend (Port 8000)" cmd /k ""%~dp0run_backend.bat""

timeout /t 2 /nobreak >nul

echo [*] Launching Vite Frontend Dev Server in dedicated window...
start "EditMind AI - Frontend (Port 5173)" cmd /k ""%~dp0run_frontend.bat""

echo.
echo [OK] Both services launched in separate windows!
echo      - Backend API  : http://127.0.0.1:8000 (Docs: http://127.0.0.1:8000/docs)
echo      - Frontend App : http://localhost:5173
echo.

