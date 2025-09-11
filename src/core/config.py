from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "MenusApp"
ACTIVE_FILE = "active.txt"  # guarda el nombre del perfil activo


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
    (root / "profiles").mkdir(parents=True, exist_ok=True)
    return root


# ----------------- Perfiles -----------------
def profiles_root() -> Path:
    """Carpeta que contiene todos los perfiles."""
    return ensure_data_dir() / "profiles"


def list_profiles() -> list[str]:
    """Lista nombres de perfiles (carpetas inmediatas en profiles/)."""
    p = profiles_root()
    if not p.exists():
        return []
    return sorted([d.name for d in p.iterdir() if d.is_dir()])


def set_selected_profile(name: str) -> None:
    """Guarda el perfil activo en profiles/active.txt."""
    r = profiles_root()
    r.mkdir(parents=True, exist_ok=True)
    (r / ACTIVE_FILE).write_text(name, encoding="utf-8")


def get_selected_profile() -> str | None:
    """Lee el perfil activo desde profiles/active.txt (si existe)."""
    f = profiles_root() / ACTIVE_FILE
    if not f.exists():
        return None
    name = f.read_text(encoding="utf-8").strip()
    return name or None


def profile_root(name: str) -> Path:
    """Carpeta raíz para un perfil concreto."""
    return profiles_root() / name


def ensure_profile_root() -> Path:
    """Asegura que la carpeta del perfil activo existe. Si no hay perfil,
    crea uno por defecto 'default' y lo selecciona."""
    r = profiles_root()
    r.mkdir(parents=True, exist_ok=True)

    active = get_selected_profile()
    if not active:
        active = "default"
        set_selected_profile(active)

    root = profile_root(active)
    root.mkdir(parents=True, exist_ok=True)
    (root / "backups").mkdir(parents=True, exist_ok=True)
    return root


# --- Aliases retrocompatibilidad (si había código viejo) ---
def get_active_profile() -> str | None:
    """Alias retrocompatible de get_selected_profile()."""
    return get_selected_profile()
