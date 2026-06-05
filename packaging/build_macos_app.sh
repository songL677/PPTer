#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-python}"
if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
fi

"$PYTHON_BIN" -m pip install -r requirements.txt -r requirements-build.txt

export PYINSTALLER_CONFIG_DIR="${PYINSTALLER_CONFIG_DIR:-/private/tmp/ppter_pyinstaller_config}"

"$PYTHON_BIN" -m PyInstaller \
  --noconfirm \
  --windowed \
  --name "AI学习助手" \
  --collect-all streamlit \
  --collect-all altair \
  --collect-all pydeck \
  --collect-all pandas \
  --collect-all pyarrow \
  --collect-all pymupdf \
  --add-data "app.py:." \
  --add-data "ai:ai" \
  --add-data "parsers:parsers" \
  --add-data "services:services" \
  --add-data "storage:storage" \
  --add-data "exports:exports" \
  desktop_app.py

echo "打包完成：dist/AI学习助手.app"
