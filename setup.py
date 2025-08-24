from setuptools import setup

APP = ['run.py']
OPTIONS = {
    # argv_emulation relies on legacy Carbon APIs on some macOS versions/architectures.
    # Disable it to avoid loading /System/Library/Carbon.framework/Carbon which may be absent.
    'argv_emulation': False,
    'packages': ['app'],
    # force-include some runtime packages that py2app sometimes misses
    'includes': [
    'PySide6', 'PySide6.QtWidgets', 'PySide6.QtGui', 'PySide6.QtCore',
    'pkg_resources', 'jaraco.text', 'markdown2'
    ],
    # bundle assets and notebooks into Resources
    'resources': ['assets', 'notebooks'],
    # Icon file to use for the built .app.
    'iconfile': 'assets/icon.icns',
}

setup(
    app=APP,
    name='RetroNotebook',
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
