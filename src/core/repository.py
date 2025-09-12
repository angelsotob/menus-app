from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

from core.config import ensure_data_dir
from core.models import DayMenu, Food, WeekMenu


class Repo:
    def __init__(self, root: Path | None = None):
        self.root = root or ensure_data_dir()
        (self.root / "backups").mkdir(parents=True, exist_ok=True)

    # ---------- utility ----------
    def _file(self, name: str) -> Path:
        return self.root / name

    def _read_json(self, name: str) -> dict:
        p = self._file(name)
        if not p.exists():
            return {"version": 1}
        return json.loads(p.read_text(encoding="utf-8"))

    def _atomic_write(self, path: Path, data: dict) -> None:
        """
        Atomic JSON write:
        - Backup previous file (if any) into backups/
        - Write to a temp file in the same directory
        - Replace destination atomically
        """
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
            # ensure fd is closed if os.fdopen failed early
            try:
                os.close(fd)
            except OSError:
                pass
            # best-effort cleanup if temp still exists
            try:
                ptmp = Path(tmp_name)
                if ptmp.exists():
                    ptmp.unlink(missing_ok=True)
            except Exception:
                pass

    # ---------- foods ----------
    def list_foods(self) -> list[Food]:
        data = self._read_json("foods.json")
        return [Food.model_validate(i) for i in data.get("foods", [])]

    def save_foods(self, foods: list[Food]) -> None:
        data = {"version": 1, "foods": [f.model_dump() for f in foods]}
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

    # ---------- menus ----------
    def save_day_menu(self, menu: DayMenu, name: str) -> None:
        d = {"date": str(menu.date), "meals": menu.meals.model_dump()}
        self._atomic_write(self._file(f"{name}.day.menu.json"), d)

    def save_week_menu(self, menu: WeekMenu, name: str) -> None:
        d = {
            "week_start": str(menu.week_start),
            "days": {k: v.model_dump() for k, v in menu.days.items()},
        }
        self._atomic_write(self._file(f"{name}.week.menu.json"), d)

    # ---------- categories ----------
    def _ensure_categories_file(self) -> Path:
        p = self._file("categories.json")
        if not p.exists():
            default = {
                "version": 1,
                "categories": [
                    "Proteina",
                    "Pescado",
                    "Marisco",
                    "Vegetales",
                    "Fruta",
                    "Legumbres",
                    "Cereales",
                    "Lácteos",
                    "Otros",
                ],
                "by_meal": {
                    "breakfast": ["Cereales", "Lácteos", "Fruta", "Otros"],
                    "midmorning": ["Fruta", "Proteina", "Otros"],
                    "lunch": ["Proteina", "Vegetales", "Cereales", "Legumbres", "Otros"],
                    "snack": ["Fruta", "Lácteos", "Otros"],
                    "dinner": ["Pescado", "Proteina", "Vegetales", "Otros"],
                },
            }
            self._atomic_write(p, default)
        return p

    def load_categories_config(self) -> dict:
        p = self._ensure_categories_file()
        return json.loads(p.read_text(encoding="utf-8"))

    def save_categories_config(self, cfg: dict) -> None:
        self._atomic_write(self._ensure_categories_file(), cfg)

    def list_categories(self) -> list[str]:
        cfg = self.load_categories_config()
        cats = list(cfg.get("categories", []))
        if not cats:
            cats = sorted({f.category for f in self.list_foods()})
        # Dedup preservando orden
        seen: set[str] = set()
        out: list[str] = []
        for c in cats:
            if c not in seen:
                seen.add(c)
                out.append(c)
        return out

    def default_cats_for(self, meal_key: str) -> list[str]:
        cfg = self.load_categories_config()
        por = cfg.get("by_meal", {})
        cats = por.get(meal_key, [])
        if not cats:
            cats = ["Otros"] if "Otros" in self.list_categories() else self.list_categories()
        return cats

    # ---------- categories synchronization <-> foods ----------
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
        """
        When you delete a category, move foods with that category to `fallback` (if it exists).
        Returns how many were changed. If fallback doesn't exist, returns 0.
        """
        cats = set(self.list_categories())
        if fallback not in cats:
            return 0
        foods = self.list_foods()
        count = 0
        for f in foods:
            if f.category == deleted:
                f.category = fallback  # type: ignore[assignment]
                count += 1
        if count:
            self.save_foods(foods)
        return count
