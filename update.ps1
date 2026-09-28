# Updates Root Cause to the latest version on GitHub.
# Keeps your .venv, downloaded models, database and vault - only the code is replaced.
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$zip  = Join-Path $env:TEMP "root-cause-update.zip"
$tmp  = Join-Path $env:TEMP "root-cause-update"
Write-Host "Downloading the latest Root Cause..."
Invoke-WebRequest "https://github.com/BradCage-afk/root-cause/archive/refs/heads/main.zip" -OutFile $zip
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
Expand-Archive $zip -DestinationPath $tmp -Force
$src = Join-Path $tmp "root-cause-main"
foreach ($d in "rootcause", "web", "scripts", "demo", "docs", "tests") {
    Copy-Item (Join-Path $src $d) $here -Recurse -Force
}
Get-ChildItem $src -File | Copy-Item -Destination $here -Force
Remove-Item $zip -Force
Remove-Item $tmp -Recurse -Force
Write-Host ""
Write-Host "Updated. Your setup, models and data were kept. Start Root Cause with run.bat"
