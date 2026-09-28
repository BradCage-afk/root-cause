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
    $dst = Join-Path $here $d
    # an older version of this script nested folders (web\web); remove that copy
    $nested = Join-Path $dst $d
    if (Test-Path $nested) { Remove-Item $nested -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $dst | Out-Null
    # copy the folder's contents, not the folder: Copy-Item into an existing folder would nest it
    Copy-Item (Join-Path (Join-Path $src $d) "*") $dst -Recurse -Force
}
Get-ChildItem $src -File | Copy-Item -Destination $here -Force
Remove-Item $zip -Force
Remove-Item $tmp -Recurse -Force
Write-Host ""
Write-Host "Updated. Your setup, models and data were kept. Start Root Cause with run.bat"
