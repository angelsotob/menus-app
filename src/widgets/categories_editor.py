from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QListWidgetItem,
    QMessageBox,
)

from core.repository import Repo
from ui import load_ui

MEAL_KEYS = ["breakfast", "midmorning", "lunch", "snack", "dinner"]
MEAL_TITLES = {
    "breakfast": "Desayuno",
    "midmorning": "Media mañana",
    "lunch": "Comida",
    "snack": "Merienda",
    "dinner": "Cena",
}


class CategoriesEditor(QDialog):
    """
    Global category editor and food mapping.

    Left panel: editable list of global categories.
    Right panel: for each meal, list of suggested categories (use global ones).
    """

    # Issued when accepted. Param: True if there were changes that affected food (rename/delete).
    categories_changed = Signal(bool)

    def __init__(self, repo: Repo, parent=None) -> None:
        super().__init__(parent)
        self.ui = load_ui("categories_editor.ui")
        self.setLayout(self.ui.layout())
        self.setWindowTitle("Categorías")

        self.repo = repo
        self._cfg = self.repo.load_categories_config()
        self._foods_affected = False  # will be set to True if we rename/delete affecting food

        # --- UI init ---
        # Global
        self.ui.lstGlobalCats.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.ui.btnAddCat.clicked.connect(self._on_add_cat)
        self.ui.btnRenameCat.clicked.connect(self._on_rename_cat)
        self.ui.btnDeleteCat.clicked.connect(self._on_delete_cat)

        # By-meal
        self.ui.cmbMeal.clear()
        self.ui.cmbMeal.addItems([MEAL_TITLES[k] for k in MEAL_KEYS])
        self.ui.cmbMeal.currentIndexChanged.connect(self._reload_meal)
        self.ui.btnAddToMeal.clicked.connect(self._on_add_to_meal)
        self.ui.btnRemoveFromMeal.clicked.connect(self._on_remove_from_meal)
        self.ui.btnMoveUp.clicked.connect(lambda: self._move_in_meal(-1))
        self.ui.btnMoveDown.clicked.connect(lambda: self._move_in_meal(+1))

        # Save / Cancel
        self.ui.buttonBox.accepted.connect(self._accept)
        self.ui.buttonBox.rejected.connect(self.reject)

        # Load initial data
        self._reload_globals()
        self._reload_meal()
        self._reload_from_global_combo()

    # ---------- data helpers ----------
    def _globals(self) -> list[str]:
        return list(self._cfg.get("categories", []))

    def _by_meal(self) -> dict[str, list[str]]:
        return dict(self._cfg.get("by_meal", {}))

    def _set_globals(self, cats: list[str]) -> None:
        self._cfg["categories"] = cats

    def _set_by_meal(self, mapping: dict[str, list[str]]) -> None:
        self._cfg["by_meal"] = mapping

    def _current_meal_key(self) -> str:
        idx = self.ui.cmbMeal.currentIndex()
        return MEAL_KEYS[idx] if 0 <= idx < len(MEAL_KEYS) else MEAL_KEYS[0]

    # ---------- reloads UI ----------
    def _reload_globals(self) -> None:
        self.ui.lstGlobalCats.clear()
        for c in self._globals():
            self.ui.lstGlobalCats.addItem(c)
        self._sync_missing_in_meals()

    def _reload_meal(self) -> None:
        key = self._current_meal_key()
        self.ui.lblMeal.setText(f"Sugerencias para: {MEAL_TITLES.get(key, key)}")
        self.ui.lstMealCats.clear()
        mapping = self._by_meal()
        for c in mapping.get(key, []):
            self.ui.lstMealCats.addItem(c)

    def _reload_from_global_combo(self) -> None:
        self.ui.cmbFromGlobal.clear()
        self.ui.cmbFromGlobal.addItems(self._globals())

    def _sync_missing_in_meals(self) -> None:
        globals_set = set(self._globals())
        mapping = self._by_meal()
        changed = False
        for k in MEAL_KEYS:
            if k not in mapping:
                mapping[k] = []
                changed = True
            else:
                before = len(mapping[k])
                mapping[k] = [c for c in mapping[k] if c in globals_set]
                changed = changed or (len(mapping[k]) != before)
        if changed:
            self._set_by_meal(mapping)
            self._reload_meal()

    # ---------- actions: global ----------
    def _on_add_cat(self) -> None:
        name = self.ui.txtNewCat.text().strip()
        if not name:
            return
        cats = self._globals()
        if name in cats:
            QMessageBox.information(self, "Aviso", "Esa categoría ya existe.")
            return
        cats.append(name)
        self._set_globals(cats)
        self.ui.txtNewCat.clear()
        self._reload_globals()
        self._reload_meal()
        self._reload_from_global_combo()

    def _on_rename_cat(self) -> None:
        item = self.ui.lstGlobalCats.currentItem()
        if not item:
            return
        old = item.text()
        new = self.ui.txtNewCat.text().strip()
        if not new:
            return
        cats = self._globals()
        if old not in cats:
            return
        if new in cats and new != old:
            QMessageBox.information(self, "Aviso", "Ya existe otra categoría con ese nombre.")
            return

        # rename in globals
        cats = [new if c == old else c for c in cats]
        self._set_globals(cats)

        # rename in by_meal
        mapping = self._by_meal()
        for k in MEAL_KEYS:
            mapping[k] = [new if c == old else c for c in mapping.get(k, [])]
        self._set_by_meal(mapping)

        # rename in existing foods
        changed = self.repo.rename_category_in_foods(old, new)
        if changed:
            self._foods_affected = True
            QMessageBox.information(
                self,
                "Alimentos actualizados",
                f"Reasignados {changed} alimento(s) de '{old}' a '{new}'.",
            )

        self.ui.txtNewCat.clear()
        self._reload_globals()
        self._reload_meal()
        self._reload_from_global_combo()

    def _on_delete_cat(self) -> None:
        item = self.ui.lstGlobalCats.currentItem()
        if not item:
            return
        name = item.text()
        cats = self._globals()
        if name not in cats:
            return
        if (
            QMessageBox.question(self, "Confirmar", f"¿Eliminar la categoría '{name}'?")
            != QMessageBox.Yes
        ):
            return

        # delete from globals
        cats = [c for c in cats if c != name]
        self._set_globals(cats)

        # delete from by_meal
        mapping = self._by_meal()
        for k in MEAL_KEYS:
            mapping[k] = [c for c in mapping.get(k, []) if c != name]
        self._set_by_meal(mapping)

        # remap foods from deleted category to 'Others' if exist
        moved = self.repo.remap_deleted_category(name, fallback="Others")
        if moved:
            self._foods_affected = True
            QMessageBox.information(
                self,
                "Alimentos actualizados",
                f"Movidos {moved} alimento(s) de '{name}' a 'otros'.",
            )

        self._reload_globals()
        self._reload_meal()
        self._reload_from_global_combo()

    # ---------- actions: by meal ----------
    def _on_add_to_meal(self) -> None:
        key = self._current_meal_key()
        mapping = self._by_meal()
        globals_set = set(self._globals())
        src = self.ui.cmbFromGlobal.currentText().strip()
        if not src or src not in globals_set:
            return
        arr = mapping.get(key, [])
        if src in arr:
            return
        arr.append(src)
        mapping[key] = arr
        self._set_by_meal(mapping)
        self._reload_meal()

    def _on_remove_from_meal(self) -> None:
        key = self._current_meal_key()
        mapping = self._by_meal()
        item = self.ui.lstMealCats.currentItem()
        if not item:
            return
        target = item.text()
        mapping[key] = [c for c in mapping.get(key, []) if c != target]
        self._set_by_meal(mapping)
        self._reload_meal()

    def _move_in_meal(self, delta: int) -> None:
        key = self._current_meal_key()
        mapping = self._by_meal()
        lst = self.ui.lstMealCats
        row = lst.currentRow()
        if row < 0:
            return
        new_row = row + delta
        if not (0 <= new_row < lst.count()):
            return
        item: QListWidgetItem = lst.takeItem(row)
        lst.insertItem(new_row, item)
        lst.setCurrentRow(new_row)
        mapping[key] = [lst.item(i).text() for i in range(lst.count())]
        self._set_by_meal(mapping)

    # ---------- accept ----------
    def _accept(self) -> None:
        self._sync_missing_in_meals()
        self.repo.save_categories_config(self._cfg)
        # Notify the outside world that it may be necessary to refresh views
        self.categories_changed.emit(self._foods_affected)
        self.accept()

    # ---------- overrides ----------
    def showEvent(self, e: Any) -> None:  # type: ignore[override]
        super().showEvent(e)
        # Reload from the repo in case the JSON was edited by hand before opening
        try:
            self._cfg = self.repo.load_categories_config()
        except Exception:
            pass
        self._reload_globals()
        self._reload_meal()
        self._reload_from_global_combo()
