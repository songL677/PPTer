$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")

$PythonBin = "python"
if (Test-Path ".\.venv\Scripts\python.exe") {
  $PythonBin = ".\.venv\Scripts\python.exe"
}

& $PythonBin -m pip install -r requirements.txt -r requirements-build.txt

& $PythonBin -m PyInstaller `
  --noconfirm `
  --windowed `
  --name "PPTer" `
  --collect-all streamlit `
  --collect-all altair `
  --collect-all pydeck `
  --collect-all pandas `
  --collect-all pyarrow `
  --collect-all pymupdf `
  --add-data "app.py;." `
  --add-data "ai;ai" `
  --add-data "parsers;parsers" `
  --add-data "services;services" `
  --add-data "storage;storage" `
  --add-data "exports;exports" `
  desktop_app.py

Write-Host "打包完成：dist/PPTer/PPTer.exe"
