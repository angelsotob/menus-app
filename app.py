from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from core.config import ensure_data_dir
from main_window import MainWindow
from theme import apply_dark


def main(argv: list[str]) -> int:
    ensure_data_dir()
    app = QApplication(argv)
    apply_dark(app)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
