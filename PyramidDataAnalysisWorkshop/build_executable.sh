#!/usr/bin/env bash
set -euo pipefail

# Build a single-file executable using PyInstaller. Run this from the project root.
# Usage: ./build_executable.sh

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# create venv if missing
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

# activate
source .venv/bin/activate

# install runtime and build deps
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# Build with PyInstaller. The code reads other .py files at runtime via exec_file_in_namespace,
# so include them as data and add hidden-imports for modules that are imported dynamically.
pyinstaller --onefile --name pyramid_analysis \
  --add-data "read_pyramid_data.py:." \
  --add-data "analyze_pyramid_data.py:." \
  --add-data "plot_pyramid_data_workshop.py:." \
  --add-data "config:config" \
  --hidden-import mplcursors \
  --hidden-import dateutil \
  --hidden-import dateutil.parser \
  --hidden-import alive_progress \
  --hidden-import matplotlib.backends.backend_pdf \
  main.py

echo "Build complete. Executable: dist/pyramid_analysis"

