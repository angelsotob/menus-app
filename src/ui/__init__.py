from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QWidget

from core.config import APP_DISPLAY_NAME, DEFAULT_WINDOW_SIZE

UI_DIR = Path(__file__).parent


def load_ui(name: str):
    path = UI_DIR / name
    loader = QUiLoader()
    f = QFile(str(path))
    if not f.exists():
        raise FileNotFoundError(f"UI not found: {path}")
    if not f.open(QFile.ReadOnly):
        raise RuntimeError(f"Cannot open UI: {path}")
    try:
        w = loader.load(f)
        if w is None:
            raise RuntimeError(f"Cannot load UI: {name}")
        return w
    finally:
        f.close()


def apply_window_defaults(w: QWidget, *, override_title: str | None = None) -> None:
    """Aplica tamaño mínimo por defecto y prefija el título con el nombre de la app."""
    try:
        # Asegurar tamaño mínimo por defecto
        def_w, def_h = DEFAULT_WINDOW_SIZE
        cur_w, cur_h = int(w.width() or 0), int(w.height() or 0)
        if cur_w < def_w or cur_h < def_h:
            w.resize(max(cur_w, def_w), max(cur_h, def_h))

        # Título actual o forzado
        current = override_title if override_title is not None else (w.windowTitle() or "")
        if current:
            # Evitar doble prefijo si ya viene con el nombre
            if not current.startswith(APP_DISPLAY_NAME + " — "):
                w.setWindowTitle(f"{APP_DISPLAY_NAME} — {current}")
        else:
            w.setWindowTitle(APP_DISPLAY_NAME)
    except Exception:
        # No romper la UI por un fallo estético
        pass


def set_window_title_suffix(w: QWidget, suffix: str) -> None:
    """Establece el título como 'APP_DISPLAY_NAME — {suffix}'."""
    try:
        if suffix:
            w.setWindowTitle(f"{APP_DISPLAY_NAME} — {suffix}")
        else:
            w.setWindowTitle(APP_DISPLAY_NAME)
    except Exception:
        pass
