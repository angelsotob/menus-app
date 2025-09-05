from __future__ import annotations

import sys
from pathlib import Path

from core.config import ensure_data_dir
from core.repository import Repo

DEFAULTS_DIR = Path(__file__).parent / "data_defaults"


def copy_if_missing(src: Path, dst: Path) -> None:
    if not dst.exists():
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def bootstrap() -> Path:
    data_root = ensure_data_dir()
    # copiar semillas si faltan
    copy_if_missing(DEFAULTS_DIR / "alimentos.json", data_root / "alimentos.json")
    copy_if_missing(DEFAULTS_DIR / "alergenos.json", data_root / "alergenos.json")
    copy_if_missing(DEFAULTS_DIR / "reglas.json", data_root / "reglas.json")
    return data_root


def main(argv: list[str]) -> int:
    data_root = bootstrap()
    repo = Repo(data_root)
    foods = repo.list_foods()
    allergens = repo.list_allergens()
    print(f"[MenusApp] Data dir: {data_root}")
    print(f"[MenusApp] Foods: {len(foods)} | Allergens: {len(allergens)}")
    print("[MenusApp] Fase 0 OK. Ya puedes empezar la Fase 1 (GUI del editor de BD).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
