from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "MenusApp"


def get_data_dir() -> Path:
    """Orden de resolución:
    1) MENUSAPP_DATA_DIR (env)
    2) ./MenusApp (si existe en el cwd)
    3) ~/MenusApp
    """
    env = os.getenv("MENUSAPP_DATA_DIR")
    if env:
        return Path(env).expanduser().resolve()
    cwd_candidate = Path.cwd() / APP_NAME
    if cwd_candidate.exists():
        return cwd_candidate.resolve()
    return (Path.home() / APP_NAME).resolve()


def ensure_data_dir() -> Path:
    root = get_data_dir()
    (root / "backups").mkdir(parents=True, exist_ok=True)
    return root
