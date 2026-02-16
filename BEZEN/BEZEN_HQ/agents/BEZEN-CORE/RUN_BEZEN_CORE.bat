@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist .venv (
  py -m venv .venv
)

call .venv\Scripts\activate.bat
py -m pip install --upgrade pip
py -m pip install -r requirements.txt

py main.py
pause
