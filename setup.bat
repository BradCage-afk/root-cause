@echo off
REM Root Cause - one-time setup on Windows. Needs internet ONCE; afterwards everything runs offline.
setlocal
cd /d %~dp0
where py >nul 2>nul || (echo Python 3.11+ not found. Install from python.org and tick "Add python.exe to PATH". & exit /b 1)
echo [1/3] Creating virtual environment...
py -3 -m venv .venv || exit /b 1
.venv\Scripts\python -m pip install --upgrade pip >nul
echo [2/3] Installing Python packages...
if exist wheels (
  .venv\Scripts\pip install --no-index --find-links wheels -r requirements.txt || exit /b 1
) else (
  .venv\Scripts\pip install -r requirements.txt || exit /b 1
)
echo [3/3] Pulling local models (about 2.3 GB)...
where ollama >nul 2>nul || (echo Ollama not installed. Get it from https://ollama.com/download/windows then run setup.bat again. & exit /b 1)
ollama pull llama3.2:3b
ollama pull nomic-embed-text
echo.
echo Setup complete. Start Root Cause with run.bat
