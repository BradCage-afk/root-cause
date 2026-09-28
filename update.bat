@echo off
REM Updates Root Cause from GitHub, keeping your setup, models and data. Needs internet.
cd /d %~dp0
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0update.ps1"
pause
