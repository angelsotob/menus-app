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

MEAL_KEYS = ["desayuno", "media_manana", "comida", "merienda", "cena"]
MEAL_TITLES = {
    "desayuno": "Desayuno",
    "media_manana": "Media mañana",
    "comida": "Comida",
    "merienda": "Merienda",
    "cena": "Cena",
}


class CategoriesEditor(QDialog):
    """
    Editor de categorías globales y mapeo por comida.

    Panel izquierdo: lista editable de categorías globales.
    Panel derecho: para cada comida, lista de categorías sugeridas (usa las globales).
    """

    # Se emite al aceptar. Param: True si hubo cambios que afectaron a alimentos (rename/delete).
    categories_changed = Signal(bool)

    def __init__(self, repo: Repo, parent=None) -> None:
        super().__init__(parent)
        self.ui = load_ui("categories_editor.ui")
        self.setLayout(self.ui.layout())
        self.setWindowTitle("Categorías")

        self.repo = repo
        self._cfg = self.repo.load_categories_config()
        self._foods_affected = (
            False  # se pondrá a True si renombramos/eliminamos afectando alimentos
        )

        # --- UI init ---
        # Lado global
        self.ui.lstGlobalCats.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.ui.btnAddCat.clicked.connect(self._on_add_cat)
        self.ui.btnRenameCat.clicked.connect(self._on_rename_cat)
        self.ui.btnDeleteCat.clicked.connect(self._on_delete_cat)

        # Lado por-comida
        self.ui.cmbMeal.clear()
        self.ui.cmbMeal.addItems([MEAL_TITLES[k] for k in MEAL_KEYS])
        self.ui.cmbMeal.currentIndexChanged.connect(self._reload_meal)
        self.ui.btnAddToMeal.clicked.connect(self._on_add_to_meal)
        self.ui.btnRemoveFromMeal.clicked.connect(self._on_remove_from_meal)
        self.ui.btnMoveUp.clicked.connect(lambda: self._move_in_meal(-1))
        self.ui.btnMoveDown.clicked.connect(lambda: self._move_in_meal(+1))

        # Guardar / Cancelar
        self.ui.buttonBox.accepted.connect(self._accept)
        self.ui.buttonBox.rejected.connect(self.reject)

        # Cargar datos iniciales
        self._reload_globals()
        self._reload_meal()
        self._reload_from_global_combo()

    # ---------- helpers de datos ----------
    def _globals(self) -> list[str]:
        return list(self._cfg.get("categorias", []))

    def _por_comida(self) -> dict[str, list[str]]:
        return dict(self._cfg.get("por_comida", {}))

    def _set_globals(self, cats: list[str]) -> None:
        self._cfg["categorias"] = cats

    def _set_por_comida(self, mapping: dict[str, list[str]]) -> None:
        self._cfg["por_comida"] = mapping

    def _current_meal_key(self) -> str:
        idx = self.ui.cmbMeal.currentIndex()
        return MEAL_KEYS[idx] if 0 <= idx < len(MEAL_KEYS) else MEAL_KEYS[0]

    # ---------- recargas UI ----------
    def _reload_globals(self) -> None:
        self.ui.lstGlobalCats.clear()
        for c in self._globals():
            self.ui.lstGlobalCats.addItem(c)
        self._sync_missing_in_meals()

    def _reload_meal(self) -> None:
        key = self._current_meal_key()
        self.ui.lblMeal.setText(f"Sugerencias para: {MEAL_TITLES.get(key, key)}")
        self.ui.lstMealCats.clear()
        mapping = self._por_comida()
        for c in mapping.get(key, []):
            self.ui.lstMealCats.addItem(c)

    def _reload_from_global_combo(self) -> None:
        self.ui.cmbFromGlobal.clear()
        self.ui.cmbFromGlobal.addItems(self._globals())

    def _sync_missing_in_meals(self) -> None:
        globals_set = set(self._globals())
        mapping = self._por_comida()
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
            self._set_por_comida(mapping)
            self._reload_meal()

    # ---------- acciones: globales ----------
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

        # renombrar en globales
        cats = [new if c == old else c for c in cats]
        self._set_globals(cats)

        # renombrar en por_comida
        mapping = self._por_comida()
        for k in MEAL_KEYS:
            mapping[k] = [new if c == old else c for c in mapping.get(k, [])]
        self._set_por_comida(mapping)

        # renombrar en alimentos existentes
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

        # eliminar de globales
        cats = [c for c in cats if c != name]
        self._set_globals(cats)

        # eliminar de por_comida
        mapping = self._por_comida()
        for k in MEAL_KEYS:
            mapping[k] = [c for c in mapping.get(k, []) if c != name]
        self._set_por_comida(mapping)

        # remap alimentos de la categoría borrada a 'otros' si existe
        moved = self.repo.remap_deleted_category(name, fallback="otros")
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

    # ---------- acciones: por comida ----------
    def _on_add_to_meal(self) -> None:
        key = self._current_meal_key()
        mapping = self._por_comida()
        globals_set = set(self._globals())
        src = self.ui.cmbFromGlobal.currentText().strip()
        if not src or src not in globals_set:
            return
        arr = mapping.get(key, [])
        if src in arr:
            return
        arr.append(src)
        mapping[key] = arr
        self._set_por_comida(mapping)
        self._reload_meal()

    def _on_remove_from_meal(self) -> None:
        key = self._current_meal_key()
        mapping = self._por_comida()
        item = self.ui.lstMealCats.currentItem()
        if not item:
            return
        target = item.text()
        mapping[key] = [c for c in mapping.get(key, []) if c != target]
        self._set_por_comida(mapping)
        self._reload_meal()

    def _move_in_meal(self, delta: int) -> None:
        key = self._current_meal_key()
        mapping = self._por_comida()
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
        self._set_por_comida(mapping)

    # ---------- aceptar ----------
    def _accept(self) -> None:
        self._sync_missing_in_meals()
        self.repo.save_categories_config(self._cfg)
        # Notificar al mundo exterior que puede que haga falta refrescar vistas
        self.categories_changed.emit(self._foods_affected)
        self.accept()

    # ---------- overrides ----------
    def showEvent(self, e: Any) -> None:  # type: ignore[override]
        super().showEvent(e)
        # Recargar del repo por si el JSON fue editado a mano antes de abrir
        try:
            self._cfg = self.repo.load_categories_config()
        except Exception:
            pass
        self._reload_globals()
        self._reload_meal()
        self._reload_from_global_combo()
