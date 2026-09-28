@echo off
REM Starts Root Cause and shares it with devices on the same Wi-Fi / hotspot / LAN (no internet needed).
REM Anyone on that network can open it and press its buttons - share only on a network you trust.
cd /d %~dp0
set RC_HOST=0.0.0.0
echo.
echo If Windows Firewall asks about Python, tick "Private networks" and click Allow.
echo.
.venv\Scripts\python -m rootcause.app
pause
