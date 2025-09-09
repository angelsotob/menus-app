from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from core.export_qt import export_widget_to_image, export_widget_to_pdf
from core.models import DayMeals, DayMenu, Food
from core.repository import Repo
from ui import load_ui
from widgets.print_views import DayPrintView

# Roles de usuario para guardar datos en QListWidgetItem (evitar colisiones con roles Qt)
ROLE_CAT = Qt.UserRole + 1
ROLE_FID = Qt.UserRole + 2


@dataclass
class MealItem:
    categoria: str
    food_id: str

    def as_label(self, foods_by_id: dict[str, Food]) -> str:
        f = foods_by_id.get(self.food_id)
        return f.nombre if f else "(desconocido)"


class PickFoodDialog(QDialog):
    def __init__(
        self,
        repo: Repo,
        meal_key: str,
        parent=None,
        current: MealItem | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Seleccionar alimento")
        self.repo = repo
        self.meal_key = meal_key
        self.result_item: MealItem | None = None

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.cmbCat = QComboBox()
        self.cmbFood = QComboBox()
        # Categorías sugeridas desde categorias.json
        self.cmbCat.addItems(self.repo.default_cats_for(meal_key))
        form.addRow(QLabel("Categoría:"), self.cmbCat)
        form.addRow(QLabel("Alimento:"), self.cmbFood)
        layout.addLayout(form)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(bb)
        bb.accepted.connect(self._accept)
        bb.rejected.connect(self.reject)

        self.cmbCat.currentTextChanged.connect(self._reload_foods)
        self._reload_foods(self.cmbCat.currentText())

        if current:
            idx = self.cmbCat.findText(current.categoria)
            if idx >= 0:
                self.cmbCat.setCurrentIndex(idx)
            foods = self._foods_for_category(current.categoria)
            if foods:
                try:
                    target = next(i for i, f in enumerate(foods) if f.id == current.food_id)
                    self.cmbFood.setCurrentIndex(target)
                except StopIteration:
                    pass

    def _foods_for_category(self, cat: str) -> list[Food]:
        return [f for f in self.repo.list_foods() if f.categoria == cat and f.activo]

    def _reload_foods(self, cat: str) -> None:
        self.cmbFood.clear()
        foods = self._foods_for_category(cat)
        for f in foods:
            self.cmbFood.addItem(f.nombre, f.id)

    def _accept(self) -> None:
        cat = self.cmbCat.currentText()
        food_id = self.cmbFood.currentData()
        if not food_id:
            return
        self.result_item = MealItem(cat, food_id)
        self.accept()


class DayEditor(QWidget):
    def __init__(self, repo: Repo, parent=None) -> None:
        super().__init__(parent)
        self.ui = load_ui("day_editor.ui")
        self.setLayout(self.ui.layout())

        self.repo = repo
        self._refresh_foods_map()

        # Conexión de botones
        self.ui.btnAddDes.clicked.connect(lambda: self._add_to(self.ui.lstDesayuno, "desayuno"))
        self.ui.btnEditDes.clicked.connect(lambda: self._edit_in(self.ui.lstDesayuno, "desayuno"))
        self.ui.btnDelDes.clicked.connect(lambda: self._del_in(self.ui.lstDesayuno))

        self.ui.btnAddMed.clicked.connect(lambda: self._add_to(self.ui.lstMedia, "media_manana"))
        self.ui.btnEditMed.clicked.connect(lambda: self._edit_in(self.ui.lstMedia, "media_manana"))
        self.ui.btnDelMed.clicked.connect(lambda: self._del_in(self.ui.lstMedia))

        self.ui.btnAddCom.clicked.connect(lambda: self._add_to(self.ui.lstComida, "comida"))
        self.ui.btnEditCom.clicked.connect(lambda: self._edit_in(self.ui.lstComida, "comida"))
        self.ui.btnDelCom.clicked.connect(lambda: self._del_in(self.ui.lstComida))

        self.ui.btnAddMer.clicked.connect(lambda: self._add_to(self.ui.lstMerienda, "merienda"))
        self.ui.btnEditMer.clicked.connect(lambda: self._edit_in(self.ui.lstMerienda, "merienda"))
        self.ui.btnDelMer.clicked.connect(lambda: self._del_in(self.ui.lstMerienda))

        self.ui.btnAddCen.clicked.connect(lambda: self._add_to(self.ui.lstCena, "cena"))
        self.ui.btnEditCen.clicked.connect(lambda: self._edit_in(self.ui.lstCena, "cena"))
        self.ui.btnDelCen.clicked.connect(lambda: self._del_in(self.ui.lstCena))

        self.ui.btnSave.clicked.connect(self._save_day)
        self.ui.btnLoad.clicked.connect(self._load_day)
        self.ui.btnExportPdf.clicked.connect(lambda: self._export("pdf"))
        self.ui.btnExportImg.clicked.connect(lambda: self._export("img"))

        # Etiqueta inicial (por si hay datos previos)
        self._relabel_all()

    # ------ helpers de relabel ------
    def _refresh_foods_map(self) -> None:
        self._foods_by_id = {f.id: f for f in self.repo.list_foods()}

    def _relabel_list(self, lst: QListWidget) -> None:
        for i in range(lst.count()):
            it = lst.item(i)
            cat = it.data(ROLE_CAT)
            fid = it.data(ROLE_FID)
            it.setText(MealItem(cat, fid).as_label(self._foods_by_id))

    def _relabel_all(self) -> None:
        self._refresh_foods_map()
        self._relabel_list(self.ui.lstDesayuno)
        self._relabel_list(self.ui.lstMedia)
        self._relabel_list(self.ui.lstComida)
        self._relabel_list(self.ui.lstMerienda)
        self._relabel_list(self.ui.lstCena)

    # ------ Qt events ------
    def showEvent(self, e) -> None:  # type: ignore[override]
        super().showEvent(e)
        self._relabel_all()

    # ----- helpers de items -----
    def _items_of(self, lst: QListWidget) -> list[MealItem]:
        out: list[MealItem] = []
        for i in range(lst.count()):
            item = lst.item(i)
            cat = item.data(ROLE_CAT)
            fid = item.data(ROLE_FID)
            out.append(MealItem(cat, fid))
        return out

    def _set_items(self, lst: QListWidget, items: list[MealItem]) -> None:
        lst.clear()
        for it in items:
            li = QListWidgetItem(it.as_label(self._foods_by_id))
            li.setData(ROLE_CAT, it.categoria)
            li.setData(ROLE_FID, it.food_id)
            lst.addItem(li)

    def _pick(self, meal_key: str, current: MealItem | None = None) -> MealItem | None:
        dlg = PickFoodDialog(self.repo, meal_key, self, current)
        if dlg.exec():
            return dlg.result_item
        return None

    def _add_to(self, lst: QListWidget, meal_key: str) -> None:
        item = self._pick(meal_key)
        if item:
            it = QListWidgetItem(item.as_label(self._foods_by_id))
            it.setData(ROLE_CAT, item.categoria)
            it.setData(ROLE_FID, item.food_id)
            lst.addItem(it)
            self._relabel_all()

    def _edit_in(self, lst: QListWidget, meal_key: str) -> None:
        it = lst.currentItem()
        if not it:
            return
        current = MealItem(it.data(ROLE_CAT), it.data(ROLE_FID))
        res = self._pick(meal_key, current)
        if res:
            it.setData(ROLE_CAT, res.categoria)
            it.setData(ROLE_FID, res.food_id)
            it.setText(res.as_label(self._foods_by_id))
            self._relabel_all()

    def _del_in(self, lst: QListWidget) -> None:
        it = lst.currentItem()
        if it:
            lst.takeItem(lst.row(it))
            self._relabel_all()

    # ----- persistencia -----
    def to_day_meals(self) -> DayMeals:
        return DayMeals(
            desayuno=[i.food_id for i in self._items_of(self.ui.lstDesayuno)],
            media_manana=[i.food_id for i in self._items_of(self.ui.lstMedia)],
            comida=[i.food_id for i in self._items_of(self.ui.lstComida)],
            merienda=[i.food_id for i in self._items_of(self.ui.lstMerienda)],
            cena=[i.food_id for i in self._items_of(self.ui.lstCena)],
        )

    def _save_day(self) -> None:
        today_code = date.today().strftime("%Y%m%d")
        templates = Path.cwd() / "templates"
        templates.mkdir(parents=True, exist_ok=True)
        default_path = templates / f"menu_dia_{today_code}.json"

        fn, _ = QFileDialog.getSaveFileName(self, "Guardar día", str(default_path), "JSON (*.json)")
        if not fn:
            return

        path = Path(fn)
        if path.suffix.lower() != ".json":
            path = path.with_suffix(".json")

        dm = self.to_day_meals()
        menu = DayMenu(fecha=date.today(), comidas=dm)

        data = menu.model_dump(mode="json")
        text = json.dumps(data, indent=2, ensure_ascii=False)
        path.write_text(text, encoding="utf-8")

        try:
            self.repo.save_day_menu(menu, path.stem)
        except Exception:
            pass

        QMessageBox.information(self, "Guardado", f"Menú diario guardado en:\n{path}")

    def _load_day(self) -> None:
        templates = Path.cwd() / "templates"
        templates.mkdir(parents=True, exist_ok=True)

        fn, _ = QFileDialog.getOpenFileName(self, "Cargar día", str(templates), "JSON (*.json)")
        if not fn:
            return

        data = json.loads(Path(fn).read_text(encoding="utf-8"))
        comidas = data.get("comidas", {})

        def to_items(ids: Iterable[str]) -> list[MealItem]:
            return [
                MealItem(
                    self._foods_by_id[i].categoria if i in self._foods_by_id else "otros",
                    i,
                )
                for i in ids
            ]

        self._set_items(self.ui.lstDesayuno, to_items(comidas.get("desayuno", [])))
        self._set_items(self.ui.lstMedia, to_items(comidas.get("media_manana", [])))
        self._set_items(self.ui.lstComida, to_items(comidas.get("comida", [])))
        self._set_items(self.ui.lstMerienda, to_items(comidas.get("merienda", [])))
        self._set_items(self.ui.lstCena, to_items(comidas.get("cena", [])))
        QMessageBox.information(self, "Cargado", f"Menú diario cargado desde:\n{fn}")
        self._relabel_all()

    # ----- export -----
    def _export(self, kind: str) -> None:
        day = self.to_day_meals()
        print_view = DayPrintView(self._foods_by_id, day, parent=None)
        print_view.resize(1000, 600)

        today_code = date.today().strftime("%Y%m%d")
        outputs = Path.cwd() / "outputs"
        outputs.mkdir(parents=True, exist_ok=True)

        if kind == "pdf":
            default_path = outputs / f"menu_dia_{today_code}.pdf"
            fn, _ = QFileDialog.getSaveFileName(
                self, "Exportar PDF", str(default_path), "PDF (*.pdf)"
            )
            if not fn:
                return
            export_widget_to_pdf(print_view, fn)
            QMessageBox.information(self, "Exportado", f"Exportado a PDF:\n{fn}")
        else:
            default_path = outputs / f"menu_dia_{today_code}.png"
            fn, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar Imagen",
                str(default_path),
                "PNG (*.png);;JPEG (*.jpg)",
            )
            if not fn:
                return
            fmt = "PNG" if fn.lower().endswith(".png") else "JPG"
            export_widget_to_image(print_view, fn, fmt=fmt, scale=2.0)
            QMessageBox.information(self, "Exportado", f"Exportado a imagen:\n{fn}")
