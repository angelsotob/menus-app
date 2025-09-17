from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from core.config import ensure_data_dir
from main_window import MainWindow
from theme import apply_dark


def main(argv: list[str]) -> int:
    ensure_data_dir()
    app = QApplication(argv)

    # HiDPI para que el logo se vea nítido en pantallas retina
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Icono global y ruta del logo para el splash
    logo_path = Path(__file__).resolve().parent / "Logo" / "Logo.png"
    if logo_path.exists():
        app.setWindowIcon(QIcon(str(logo_path)))
    apply_dark(app)

    splash = None
    if logo_path.exists():
        pix = QPixmap(str(logo_path))
        # Si el PNG es muy grande, puedes escalarlo (comenta si no quieres escalar):
        # pix = pix.scaled(420, 420, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        splash = QSplashScreen(pix)
        splash.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        splash.show()
        app.processEvents()  # asegura que el splash se pinte antes de seguir

    # Lanzar la ventana principal tras 3 segundos (3000 ms)
    def start_main():
        # guardar referencia en la app para evitar GC
        app._main_window = MainWindow()  # type: ignore[attr-defined]
        app._main_window.show()
        if splash is not None:
            # termina el splash “vinculándolo” a la ventana principal
            splash.finish(app._main_window.ui if hasattr(app._main_window, "ui") else None)

    QTimer.singleShot(3000, start_main)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
