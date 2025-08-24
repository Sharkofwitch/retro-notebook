#!/usr/bin/env zsh
# Simple build helper for macOS using py2app
# Usage: ./build_py2app.sh
set -euo pipefail

# 1) create venv if missing
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

# 2) activate
source .venv/bin/activate

# 3) ensure pip and install deps
pip install -U pip
pip install -r requirements.txt py2app jaraco.text markdown2

# 4) run py2app
python setup.py py2app

APP_NAME=RetroNotebook
DIST_DIR="dist/${APP_NAME}.app"

# 5) find PySide6 plugin directory and copy into app resources if present
PLUGIN_DIR=$(python3 - <<PY
import PySide6, pathlib
p=(pathlib.Path(PySide6.__file__).parent / 'plugins')
print(p.as_posix() if p.exists() else '')
PY
)

if [ -n "$PLUGIN_DIR" ]; then
  echo "Found PySide6 plugins at: $PLUGIN_DIR"
  RES_DIR="$DIST_DIR/Contents/Resources"
  mkdir -p "$RES_DIR"
  echo "Copying plugins into $RES_DIR/PySide6_plugins"
  /usr/bin/ditto "$PLUGIN_DIR" "$RES_DIR/PySide6_plugins"
else
  echo "PySide6 plugin dir not found; if the app fails to start, locate and copy PySide6 plugins manually."
fi

# 6) print success and how to open
echo "Build complete. App at: $DIST_DIR"
echo "Open it with: open $DIST_DIR"

# End
