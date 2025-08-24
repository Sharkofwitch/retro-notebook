import sys
from app.main import start_app


def run_headless_test(ticks: int = 3):
    """Headless smoke test: instantiate BitFactory, run a few ticks, save state and print path."""
    try:
        from PySide6.QtWidgets import QApplication
    except Exception as e:
        print('PySide6 not available for headless test:', e)
        return 2

    app = QApplication.instance() or QApplication([])
    try:
        from app.bit_factory import BitFactory, FACTORY_SAVE_PATH
    except Exception as e:
        print('Failed to import BitFactory:', e)
        return 3

    dlg = BitFactory()
    for _ in range(ticks):
        dlg.tick()
    try:
        dlg.save_game()
    except Exception as e:
        print('Save failed:', e)
        return 4
    print('Headless test completed. Save path:', os.path.abspath(FACTORY_SAVE_PATH))
    return 0


if __name__ == "__main__":
    if '--test' in sys.argv or '-t' in sys.argv:
        import os
        rc = run_headless_test()
        sys.exit(rc)
    start_app()