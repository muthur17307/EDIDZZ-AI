@echo off
title EditMind AI - Dedicated Frontend Dev Server (Vite Port 5173)
cd /d "%~dp0"

echo ======================================================================
echo           EditMind AI -- Dedicated Frontend Dev Server
echo    React 19 + Vite HMR + TailwindCSS (Port 5173)
echo ======================================================================
echo.

where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is not found in PATH!
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

cd "EditAI\frontend"

if not exist "node_modules\" (
    echo [*] Installing frontend dependencies (npm install)...
    call npm install
)

echo [*] Starting Vite Dev Server on http://localhost:5173 ...
call npm run dev

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Frontend exited with error code %ERRORLEVEL%.
    pause
)

