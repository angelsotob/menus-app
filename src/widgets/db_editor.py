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

        # model + proxy
        self.model = FoodTableModel(self.repo.list_foods())
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)

        self.ui.tblFoods.setModel(self.proxy)
        self.ui.tblFoods.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.ui.tblFoods.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.ui.tblFoods.setSortingEnabled(True)
        self.ui.tblFoods.sortByColumn(0, Qt.AscendingOrder)

        hdr = self.ui.tblFoods.horizontalHeader()
        hdr.setStretchLastSection(True)
        hdr.setDefaultSectionSize(180)
        self.ui.tblFoods.setAlternatingRowColors(True)
        self.ui.tblFoods.verticalHeader().setVisible(False)
        self.ui.tblFoods.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ui.tblFoods.resizeColumnsToContents()

        # filters
        for disp, val in [
            ("(Todas)", "(All)"),
            ("Proteína", "Protein"),
            ("Verduras", "Vegetables"),
            ("Fruta", "Fruit"),
            ("Cereales", "Cereals"),
            ("Legumbres", "Legumes"),
            ("Pescado", "Fish"),
            ("Marisco", "Seafood"),
            ("Huevos", "Eggs"),
            ("Lácteos", "Milk"),
            ("Frutos secos", "Nuts"),
            ("Grasas", "Fats"),
            ("Otros", "Others"),
        ]:
            self.ui.cmbCategory.addItem(disp, val)

        self.ui.txtSearch.textChanged.connect(self._apply_filters)
        self.ui.cmbCategory.currentTextChanged.connect(self._apply_filters)
        self.ui.chkShowInactive.stateChanged.connect(self._apply_filters)

        # buttons
        self.ui.btnAdd.clicked.connect(self.on_add)
        self.ui.btnEdit.clicked.connect(self.on_edit)
        self.ui.btnToggleActive.clicked.connect(self.on_toggle_active)
        self.ui.btnDelete.clicked.connect(self.on_delete)

        # context menu
        self.ui.tblFoods.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.tblFoods.customContextMenuRequested.connect(self._open_context_menu)

        # shortcuts
        self._install_shortcuts()

        self._apply_filters()

    # ---- Refresh API for profile changes ----
    def refresh_from_repo(self, repo: Repo | None = None, keep_selection: bool = False) -> None:
        if repo is not None:
            self.repo = repo
        prev_id = None
        if keep_selection:
            row = self._current_source_row()
            if row is not None:
                prev = self.model.current_food(row)
                prev_id = prev.id

        self.model.set_rows(self.repo.list_foods())
        self._apply_filters()

        if prev_id:
            # try to re-select by id
            for r, f in enumerate(self.model._rows):
                if f.id == prev_id:
                    src_idx = self.model.index(r, 0)
                    proxy_idx = self.proxy.mapFromSource(src_idx)
                    if proxy_idx.isValid():
                        self.ui.tblFoods.selectRow(proxy_idx.row())
                    break

    # ---- shortcuts, context menu, actions ----
    def _install_shortcuts(self) -> None:
        act_new = QAction(self)
        act_new.setShortcut(QKeySequence("Ctrl+N"))
        act_new.triggered.connect(self.on_add)
        self.addAction(act_new)
        act_edit = QAction(self)
        act_edit.setShortcut(QKeySequence(Qt.Key_Return))
        act_edit.triggered.connect(self.on_edit)
        self.addAction(act_edit)
        act_edit2 = QAction(self)
        act_edit2.setShortcut(QKeySequence(Qt.Key_Enter))
        act_edit2.triggered.connect(self.on_edit)
        self.addAction(act_edit2)
        act_del = QAction(self)
        act_del.setShortcut(QKeySequence(Qt.Key_Delete))
        act_del.triggered.connect(self.on_delete)
        self.addAction(act_del)

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
        act_toggle = menu.addAction("Activar" if not current.active else "Desactivar")
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
        answer = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Quieres {'activar' if not current.active else 'desactivar'} '{current.name}'?",
        )
        if answer != QMessageBox.Yes:
            return
        foods = self.repo.list_foods()
        for i, f in enumerate(foods):
            if f.id == current.id:
                foods[i].active = not f.active
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
            self, "Confirmar", f"¿Borrar definitivamente '{current.name}'?"
        )
        if answer != QMessageBox.Yes:
            return
        foods = [f for f in self.repo.list_foods() if f.id != current.id]
        self.repo.save_foods(foods)
        self.model.set_rows(foods)
        self._apply_filters()
        self.notify("Alimento borrado", 2500)

    def _apply_filters(self) -> None:
        text = self.ui.txtSearch.text()
        cat = self.ui.cmbCategory.currentData()
        show_inactive = self.ui.chkShowInactive.isChecked()
        self.model.apply_filters(text, cat, show_inactive)
        self.ui.tblFoods.sortByColumn(
            self.ui.tblFoods.horizontalHeader().sortIndicatorSection(),
            self.ui.tblFoods.horizontalHeader().sortIndicatorOrder(),
        )

    def _current_source_row(self) -> int | None:
        sel = self.ui.tblFoods.selectionModel().selectedRows()
        if not sel:
            return None
        proxy_row = sel[0].row()
        src_index = self.proxy.mapToSource(self.proxy.index(proxy_row, 0))
        return src_index.row()

    def _open_food_dialog(self, current: Food | None = None) -> Food | None:
        from widgets.food_dialog import FoodDialog

        dlg = FoodDialog(self.repo, current, self)
        return dlg.result_food if dlg.exec() else None
