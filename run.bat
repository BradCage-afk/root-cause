@echo off
REM Starts Root Cause. The browser opens by itself once the app is ready (first start ~1 minute).
cd /d %~dp0
.venv\Scripts\python -m rootcause.app
pause
