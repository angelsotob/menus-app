# src/core/repository.py
from __future__ import annotations

import json
import os
import shutil
import tempfile
from collections.abc import Iterable
from pathlib import Path

from core.config import ensure_data_dir
from core.models import DayMenu, Food, WeekMenu


class Repo:
    """
    Repositorio de datos con **persistencia y modelo interno en español (ES)**.

    - Al LEER JSON del perfil (foods/categories/rules): se cargan tal cual (ES).
    - Al ESCRIBIR: se guardan tal cual (ES).
    - APIs devuelven/aceptan categorías en ES.
    """

    def __init__(self, root: Path | None = None):
        self.root = root or ensure_data_dir()
        (self.root / "backups").mkdir(parents=True, exist_ok=True)

    # ---------- utilities ----------
    def _file(self, name: str) -> Path:
        return self.root / name

    def _read_json(self, name: str) -> dict:
        p = self._file(name)
        if not p.exists():
            return {"version": 1}
        return json.loads(p.read_text(encoding="utf-8"))

    def _atomic_write(self, path: Path, data: dict) -> None:
        if path.exists():
            (self.root / "backups").mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, self.root / "backups" / f"{path.stem}.bak.json")

        fd, tmp_name = tempfile.mkstemp(
            prefix=f"{path.stem}_",
            suffix=".tmp",
            dir=str(self.root),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            Path(tmp_name).replace(path)
        finally:
            try:
                os.close(fd)
            except OSError:
                pass
            try:
                ptmp = Path(tmp_name)
                if ptmp.exists():
                    ptmp.unlink(missing_ok=True)
            except Exception:
                pass

    # ---------- foods (ES <-> ES) ----------
    def list_foods(self) -> list[Food]:
        data = self._read_json("foods.json")
        foods_raw = data.get("foods", [])
        out: list[Food] = []
        for i in foods_raw:
            out.append(Food.model_validate(i))
        return out

    def save_foods(self, foods: Iterable[Food | dict]) -> None:
        # Permite Food o dict (para tests/semillas rápidas)
        foods_es: list[dict] = []
        for f in foods:
            obj = f if isinstance(f, Food) else Food.model_validate(f)
            foods_es.append(
                {
                    "id": obj.id,
                    "name": obj.name,
                    "category": obj.category,  # ES
                    "allergens": obj.allergens,
                    "labels": obj.labels,
                    "notes": obj.notes,
                    "active": obj.active,
                }
            )
        data = {"version": 1, "foods": foods_es}
        self._atomic_write(self._file("foods.json"), data)

    # ---------- allergens ----------
    def list_allergens(self) -> list[str]:
        data = self._read_json("allergens.json")
        return list(data.get("allergens", []))

    def save_allergens(self, allergens: list[str]) -> None:
        self._atomic_write(self._file("allergens.json"), {"version": 1, "allergens": allergens})

    # ---------- rules ----------
    def load_rules(self) -> dict:
        return self._read_json("rules.json")

    def save_rules(self, rules: dict) -> None:
        self._atomic_write(self._file("rules.json"), rules)

    # ---------- menus (sin traducciones; solo IDs) ----------
    def save_day_menu(self, menu: DayMenu, name: str) -> None:
        d = {"date": str(menu.date), "meals": menu.meals.model_dump()}
        self._atomic_write(self._file(f"{name}.day.menu.json"), d)

    def save_week_menu(self, menu: WeekMenu, name: str) -> None:
        d = {
            "week_start": str(menu.week_start),
            "days": {k: v.model_dump() for k, v in menu.days.items()},
        }
        self._atomic_write(self._file(f"{name}.week.menu.json"), d)

    # ---------- categories (ES) ----------
    def _ensure_categories_file(self) -> Path:
        p = self._file("categories.json")
        if not p.exists():
            default_es = {
                "version": 1,
                "categories": [
                    "Cereales",
                    "Fruta",
                    "Lácteos",
                    "Legumbres",
                    "Marisco",
                    "Otros",
                    "Pescado",
                    "Proteína",
                    "Vegetales",
                ],
                "by_meal": {
                    "breakfast": ["Cereales", "Fruta", "Lácteos", "Otros"],
                    "midmorning": ["Fruta", "Otros", "Proteína"],
                    "lunch": ["Cereales", "Legumbres", "Otros", "Proteína", "Vegetales"],
                    "snack": ["Fruta", "Lácteos", "Otros"],
                    "dinner": ["Otros", "Pescado", "Proteína", "Vegetales"],
                },
            }
            self._atomic_write(p, default_es)
        return p

    def load_categories_config(self) -> dict:
        p = self._ensure_categories_file()
        return json.loads(p.read_text(encoding="utf-8"))

    def save_categories_config(self, cfg: dict) -> None:
        self._atomic_write(self._ensure_categories_file(), cfg)

    # --------- APIs de conveniencia (interno ES) ----------
    def list_categories(self) -> list[str]:
        cfg_es = self.load_categories_config()
        cats = list(cfg_es.get("categories", []))
        if not cats:
            return sorted({f.category for f in self.list_foods()})
        # dedup preservando orden
        seen: set[str] = set()
        out: list[str] = []
        for c in cats:
            if c not in seen:
                seen.add(c)
                out.append(c)
        return out

    def default_cats_for(self, meal_key: str) -> list[str]:
        cfg_es = self.load_categories_config()
        by_es = cfg_es.get("by_meal", {})
        arr = by_es.get(meal_key, [])
        if not arr:
            all_es = self.list_categories()
            return ["Otros"] if "Otros" in all_es else all_es
        return list(arr)

    # ---------- categories sincronización <-> foods ----------
    def rename_category_in_foods(self, old: str, new: str) -> int:
        foods = self.list_foods()
        count = 0
        for f in foods:
            if f.category == old:
                f.category = new  # type: ignore[assignment]
                count += 1
        if count:
            self.save_foods(foods)
        return count

    def remap_deleted_category(self, deleted: str, fallback: str = "Otros") -> int:
        foods = self.list_foods()
        count = 0
        for f in foods:
            if f.category == deleted:
                f.category = fallback  # type: ignore[assignment]
                count += 1
        if count:
            self.save_foods(foods)
        return count
