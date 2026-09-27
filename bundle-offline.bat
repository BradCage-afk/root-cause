@echo off
REM Run this at home WITH internet. Copies every Python package into .\wheels so setup.bat works with no Wi-Fi.
cd /d %~dp0
py -3 -m pip download -r requirements.txt -d wheels
echo Wheels saved. Ollama models live in %USERPROFILE%\.ollama\models - copy that folder to your USB stick too.
