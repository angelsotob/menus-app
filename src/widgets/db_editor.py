from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QSortFilterProxyModel, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView,
    QMenu,
    QMessageBox,
    QWidget,
)

from core.models import Food
from core.repository import Repo
from ui import load_ui
from widgets.food_table_model import FoodTableModel


class DbEditor(QWidget):
    def __init__(
        self,
        repo: Repo,
        parent=None,
        notify: Callable[[str, int], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.ui = load_ui("db_editor.ui")  # QWidget
        self.setLayout(self.ui.layout())

        self.repo = repo
        self.notify = notify or (lambda _m, _ms: None)

        # ---------- tabla + modelo ----------
        self.model = FoodTableModel(self.repo.list_foods())

        # Proxy para que la ordenación de cabeceras funcione de verdad
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)

        self.ui.tblFoods.setModel(self.proxy)
        self.ui.tblFoods.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.ui.tblFoods.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.ui.tblFoods.setSortingEnabled(True)
        self.ui.tblFoods.sortByColumn(0, Qt.AscendingOrder)

        # Estética/UX
        hdr = self.ui.tblFoods.horizontalHeader()
        hdr.setStretchLastSection(True)
        hdr.setDefaultSectionSize(180)
        self.ui.tblFoods.setAlternatingRowColors(True)
        self.ui.tblFoods.verticalHeader().setVisible(False)
        self.ui.tblFoods.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ui.tblFoods.resizeColumnsToContents()

        # ---------- filtros ----------
        self.ui.cmbCategory.addItems(FoodTableModel.categories())
        self.ui.txtSearch.textChanged.connect(self._apply_filters)
        self.ui.cmbCategory.currentTextChanged.connect(self._apply_filters)
        self.ui.chkShowInactive.stateChanged.connect(self._apply_filters)

        # ---------- botones ----------
        self.ui.btnAdd.clicked.connect(self.on_add)
        self.ui.btnEdit.clicked.connect(self.on_edit)
        self.ui.btnToggleActive.clicked.connect(self.on_toggle_active)
        self.ui.btnDelete.clicked.connect(self.on_delete)

        # ---------- menú contextual ----------
        self.ui.tblFoods.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.tblFoods.customContextMenuRequested.connect(self._open_context_menu)

        # ---------- atajos ----------
        self._install_shortcuts()

        self._apply_filters()

    # ---- atajos ----
    def _install_shortcuts(self) -> None:
        # Ctrl+N -> Añadir
        act_new = QAction(self)
        act_new.setShortcut(QKeySequence("Ctrl+N"))
        act_new.triggered.connect(self.on_add)
        self.addAction(act_new)

        # Enter/Return -> Editar
        act_edit = QAction(self)
        act_edit.setShortcut(QKeySequence(Qt.Key_Return))
        act_edit.triggered.connect(self.on_edit)
        self.addAction(act_edit)

        act_edit2 = QAction(self)
        act_edit2.setShortcut(QKeySequence(Qt.Key_Enter))
        act_edit2.triggered.connect(self.on_edit)
        self.addAction(act_edit2)

        # Supr -> Borrar
        act_del = QAction(self)
        act_del.setShortcut(QKeySequence(Qt.Key_Delete))
        act_del.triggered.connect(self.on_delete)
        self.addAction(act_del)

    # ---- menú contextual ----
    def _open_context_menu(self, pos) -> None:
        index = self.ui.tblFoods.indexAt(pos)
        if not index.isValid():
            return
        row = self._current_source_row()
        if row is None:
            return
        current = self.model.current_food(row)

        menu = QMenu(self)
        act_edit = menu.addAction("Editar")
        act_toggle = menu.addAction("Activar" if not current.activo else "Desactivar")
        act_delete = menu.addAction("Borrar")

        action = menu.exec(self.ui.tblFoods.viewport().mapToGlobal(pos))
        if action is None:
            return
        if action == act_edit:
            self.on_edit()
        elif action == act_toggle:
            self.on_toggle_active()
        elif action == act_delete:
            self.on_delete()

    # ---- acciones ----
    def on_add(self) -> None:
        food = self._open_food_dialog()
        if not food:
            return
        foods = self.repo.list_foods()
        foods.append(food)
        self.repo.save_foods(foods)
        self.model.set_rows(foods)
        self._apply_filters()
        self.notify("Alimento añadido", 2500)

    def on_edit(self) -> None:
        row = self._current_source_row()
        if row is None:
            return
        current = self.model.current_food(row)
        edited = self._open_food_dialog(current)
        if not edited:
            return
        foods = self.repo.list_foods()
        for i, f in enumerate(foods):
            if f.id == current.id:
                foods[i] = edited
                break
        self.repo.save_foods(foods)
        self.model.set_rows(foods)
        self._apply_filters()
        self.notify("Alimento actualizado", 2500)

    def on_toggle_active(self) -> None:
        row = self._current_source_row()
        if row is None:
            return
        current = self.model.current_food(row)

        next_state = "activar" if not current.activo else "desactivar"
        answer = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Quieres {next_state} '{current.nombre}'?",
        )
        if answer != QMessageBox.Yes:
            return

        foods = self.repo.list_foods()
        for i, f in enumerate(foods):
            if f.id == current.id:
                foods[i].activo = not f.activo
                break
        self.repo.save_foods(foods)
        self.model.set_rows(foods)
        self._apply_filters()
        self.notify("Estado cambiado", 2500)

    def on_delete(self) -> None:
        row = self._current_source_row()
        if row is None:
            return
        current = self.model.current_food(row)
        answer = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Borrar definitivamente '{current.nombre}'?",
        )
        if answer != QMessageBox.Yes:
            return
        foods = [f for f in self.repo.list_foods() if f.id != current.id]
        self.repo.save_foods(foods)
        self.model.set_rows(foods)
        self._apply_filters()
        self.notify("Alimento borrado", 2500)

    # ---- util ----
    def _apply_filters(self) -> None:
        text = self.ui.txtSearch.text()
        cat = self.ui.cmbCategory.currentText()
        show_inactive = self.ui.chkShowInactive.isChecked()
        self.model.apply_filters(text, cat, show_inactive)
        # Mantén la ordenación activa tras resetear el modelo
        self.ui.tblFoods.sortByColumn(
            self.ui.tblFoods.horizontalHeader().sortIndicatorSection(),
            self.ui.tblFoods.horizontalHeader().sortIndicatorOrder(),
        )

    def _current_source_row(self) -> int | None:
        """Fila en el **modelo fuente** (no en el proxy)."""
        sel = self.ui.tblFoods.selectionModel().selectedRows()
        if not sel:
            return None
        proxy_row = sel[0].row()
        src_index = self.proxy.mapToSource(self.proxy.index(proxy_row, 0))
        return src_index.row()

    def _open_food_dialog(self, current: Food | None = None) -> Food | None:
        from widgets.food_dialog import FoodDialog

        dlg = FoodDialog(self.repo, current, self)
        if dlg.exec():
            return dlg.result_food
        return None
