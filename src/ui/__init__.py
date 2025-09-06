from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader

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
