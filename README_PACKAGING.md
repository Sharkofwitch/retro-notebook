Py2app packaging instructions for RetroNotebook

Prerequisites
- macOS (build on the same architecture you target: Apple Silicon vs Intel)
- Xcode command line tools (for codesign/notarize if needed)
- A venv with project deps installed (including PySide6 and py2app)

Quick steps

1. Create and activate a venv
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt py2app
```

2. Run py2app
```bash
python setup.py py2app
```

3. The built app will be in `dist/RetroNotebook.app`.

Notes & troubleshooting
- If the app fails to start, run the binary from Terminal to see missing modules or libs:
```
/path/to/dist/RetroNotebook.app/Contents/MacOS/RetroNotebook
```
- Qt (PySide6) may require bundling plugin folders (platforms, imageformats). If you see errors about engine or platform plugins, locate your PySide6 plugin folder with:
```bash
python - <<PY
import PySide6, pathlib
print((pathlib.Path(PySide6.__file__).parent / 'plugins').as_posix())
PY
```
Then copy or include that folder into the app's `Contents/Resources/`.

Code signing & notarization
- To distribute outside your machine, codesign and notarize the .app. See Apple's docs for 'codesign' and 'notarytool'.

If you want, I can generate a PyInstaller spec instead (often easier for Qt apps) or create a more advanced `setup.py` that detects and copies PySide6 plugins automatically.
