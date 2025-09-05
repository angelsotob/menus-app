from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from core.config import ensure_data_dir
from core.models import DayMenu, Food, WeekMenu


class Repo:
    def __init__(self, root: Path | None = None):
        self.root = root or ensure_data_dir()

    # ---------- utilidades ----------
    def _file(self, name: str) -> Path:
        return self.root / name

    def _read_json(self, name: str) -> dict:
        p = self._file(name)
        if not p.exists():
            return {"version": 1}
        return json.loads(p.read_text(encoding="utf-8"))

    def _atomic_write(self, path: Path, data: dict) -> None:
        # backup si existe
        if path.exists():
            shutil.copy2(path, self.root / "backups" / f"{path.stem}.bak.json")
        # escritura atómica
        fd, tmp_name = tempfile.mkstemp(prefix=path.stem, suffix=".tmp", dir=str(self.root))
        tmp = Path(tmp_name)
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)

    # ---------- alimentos ----------
    def list_foods(self) -> list[Food]:
        data = self._read_json("alimentos.json")
        return [Food.model_validate(i) for i in data.get("alimentos", [])]

    def save_foods(self, foods: list[Food]) -> None:
        data = {"version": 1, "alimentos": [f.model_dump() for f in foods]}
        self._atomic_write(self._file("alimentos.json"), data)

    # ---------- alergenos ----------
    def list_allergens(self) -> list[str]:
        data = self._read_json("alergenos.json")
        return list(data.get("alergenos", []))

    def save_allergens(self, allergens: list[str]) -> None:
        self._atomic_write(self._file("alergenos.json"), {"version": 1, "alergenos": allergens})

    # ---------- reglas (solo persistencia) ----------
    def load_rules(self) -> dict:
        return self._read_json("reglas.json")

    def save_rules(self, rules: dict) -> None:
        self._atomic_write(self._file("reglas.json"), rules)

    # ---------- menús ----------
    def save_day_menu(self, menu: DayMenu, name: str) -> None:
        d = {"fecha": str(menu.fecha), "comidas": menu.comidas.model_dump()}
        self._atomic_write(self._file(f"{name}.day.menu.json"), d)

    def save_week_menu(self, menu: WeekMenu, name: str) -> None:
        d = {
            "semana_inicio": str(menu.semana_inicio),
            "dias": {k: v.model_dump() for k, v in menu.dias.items()},
        }
        self._atomic_write(self._file(f"{name}.week.menu.json"), d)
