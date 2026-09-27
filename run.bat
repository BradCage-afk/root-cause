@echo off
REM Starts Root Cause at http://127.0.0.1:8000 (Ollama must be running - it starts with Windows after install)
cd /d %~dp0
start "" http://127.0.0.1:8000
.venv\Scripts\python -m rootcause.app
