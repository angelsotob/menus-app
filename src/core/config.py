from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "MenusApp"
ACTIVE_FILE = "active.txt"  # Saves active profile name


def get_data_dir() -> Path:
    """Resolution order:
    1) MENUSAPP_DATA_DIR (env)
    2) ./MenusApp (if exists in cwd)
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


# ----------------- Profiles -----------------
def profiles_root() -> Path:
    """Directory that includes all profiles."""
    return ensure_data_dir() / "profiles"


def list_profiles() -> list[str]:
    """List profiles names (immediate folders in profiles/)."""
    p = profiles_root()
    if not p.exists():
        return []
    return sorted([d.name for d in p.iterdir() if d.is_dir()])


def set_selected_profile(name: str) -> None:
    """Saves active profile in profiles/active.txt."""
    r = profiles_root()
    r.mkdir(parents=True, exist_ok=True)
    (r / ACTIVE_FILE).write_text(name, encoding="utf-8")


def get_selected_profile() -> str | None:
    """Reads active profile from profiles/active.txt (if exists)."""
    f = profiles_root() / ACTIVE_FILE
    if not f.exists():
        return None
    name = f.read_text(encoding="utf-8").strip()
    return name or None


def profile_root(name: str) -> Path:
    """Root directory of specific profile."""
    return profiles_root() / name


def ensure_profile_root() -> Path:
    """Ensures that the folder of the active profile exists. If there is no profile,
    creates a default 'default' and selects it."""
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


# --- Aliases backward compatibility (if there was old code) ---
def get_active_profile() -> str | None:
    """Aliases backward compatibility de get_selected_profile()."""
    return get_selected_profile()
