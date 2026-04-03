@echo off
chcp 65001 >nul
title HaltScanner Pro

echo =============================================
echo   HaltScanner Pro - Start
echo =============================================
echo.

cd /d "%~dp0"

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found! Install from python.org
    pause
    exit /b 1
)

:: Check venv
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo Virtual environment activated
) else (
    echo No venv found - using system Python
)

:: Install deps if needed
pip show anthropic >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt -q
)

echo.
echo Starting HaltScanner Pro...
echo Press Ctrl+C to stop
echo.

python main.py

pause
