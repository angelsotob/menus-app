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
        (self.root / "backups").mkdir(parents=True, exist_ok=True)

    # ---------- utilidades ----------
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

    # ---------- reglas ----------
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

    # ---------- categorías ----------
    def _ensure_categories_file(self) -> Path:
        p = self._file("categorias.json")
        if not p.exists():
            default = {
                "version": 1,
                "categorias": [
                    "proteina",
                    "pescado",
                    "marisco",
                    "verdura",
                    "fruta",
                    "legumbre",
                    "cereal_harina",
                    "lacteo",
                    "otros",
                ],
                "por_comida": {
                    "desayuno": ["cereal_harina", "lacteo", "fruta", "otros"],
                    "media_manana": ["fruta", "proteina", "otros"],
                    "comida": ["proteina", "verdura", "cereal_harina", "legumbre", "otros"],
                    "merienda": ["fruta", "lacteo", "otros"],
                    "cena": ["pescado", "proteina", "verdura", "otros"],
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
        cats = list(cfg.get("categorias", []))
        if not cats:
            cats = sorted({f.categoria for f in self.list_foods()})
        return cats

    def default_cats_for(self, meal_key: str) -> list[str]:
        cfg = self.load_categories_config()
        por = cfg.get("por_comida", {})
        cats = por.get(meal_key, [])
        if not cats:
            cats = ["otros"] if "otros" in self.list_categories() else self.list_categories()
        return cats

    # ---------- sincronización categorías <-> alimentos ----------
    def rename_category_in_foods(self, old: str, new: str) -> int:
        foods = self.list_foods()
        count = 0
        for f in foods:
            if f.categoria == old:
                f.categoria = new  # type: ignore[assignment]
                count += 1
        if count:
            self.save_foods(foods)
        return count

    def remap_deleted_category(self, deleted: str, fallback: str = "otros") -> int:
        """
        Cuando borras una categoría, mueve los alimentos con esa categoría a
        'fallback' (si existe). Si no existe, no remapea (devuelve 0).
        """
        cats = set(self.list_categories())
        if fallback not in cats:
            return 0
        foods = self.list_foods()
        count = 0
        for f in foods:
            if f.categoria == deleted:
                f.categoria = fallback  # type: ignore[assignment]
                count += 1
        if count:
            self.save_foods(foods)
        return count
