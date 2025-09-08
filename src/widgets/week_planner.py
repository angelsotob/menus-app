from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMessageBox, QVBoxLayout, QWidget

from core.export_qt import export_widget_to_image, export_widget_to_pdf
from core.models import WeekMenu
from core.repository import Repo
from ui import load_ui
from widgets.day_editor import DayEditor, MealItem
from widgets.print_views import WeekPrintView

DAY_KEYS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
TAB_LAYOUT_NAMES = [
    "layoutLunes",
    "layoutMartes",
    "layoutMiercoles",
    "layoutJueves",
    "layoutViernes",
    "layoutSabado",
    "layoutDomingo",
]


def monday_of(d: date) -> date:
    # Monday as start of week: 0 = Monday
    return d - timedelta(days=d.weekday())


class WeekPlanner(QWidget):
    def __init__(self, repo: Repo, parent=None) -> None:
        super().__init__(parent)
        self.ui = load_ui("week_planner.ui")
        self.setLayout(self.ui.layout())  # adopt layout from .ui
        self.repo = repo

        # Prepara un DayEditor por pestaña
        self._editors: dict[str, DayEditor] = {}
        for key, layout_name in zip(DAY_KEYS, TAB_LAYOUT_NAMES):
            lay: QVBoxLayout = getattr(self.ui, layout_name)
            ed = DayEditor(self.repo, parent=self.ui)
            lay.addWidget(ed)
            self._editors[key] = ed

        # Botones
        self.ui.btnSave.clicked.connect(self._save_week)
        self.ui.btnLoad.clicked.connect(self._load_week)
        self.ui.btnExportPdf.clicked.connect(lambda: self._export("pdf"))
        self.ui.btnExportImg.clicked.connect(lambda: self._export("img"))

        # foods map para export
        self._foods_by_id = {f.id: f for f in self.repo.list_foods()}

    # ---------- helpers ----------
    def to_week_menu(self) -> WeekMenu:
        """Convierte los 7 DayEditor a un WeekMenu."""
        dias = {}
        for key in DAY_KEYS:
            ed = self._editors[key]
            dias[key] = ed.to_day_meals()
        start = monday_of(date.today())
        return WeekMenu(semana_inicio=start, dias=dias)

    def _set_day_from_ids(self, key: str, ids_by_meal: dict[str, list[str]]) -> None:
        """Setea un día concreto en su DayEditor a partir de ids por comida."""
        ed = self._editors[key]

        def to_items(ids: list[str]) -> list[MealItem]:
            items: list[MealItem] = []
            foods_by_id = self._foods_by_id
            for fid in ids:
                if fid in foods_by_id:
                    items.append(MealItem(foods_by_id[fid].categoria, fid))
                else:
                    items.append(MealItem("otros", fid))
            return items

        ed._set_items(ed.ui.lstDesayuno, to_items(ids_by_meal.get("desayuno", [])))
        ed._set_items(ed.ui.lstMedia, to_items(ids_by_meal.get("media_manana", [])))
        ed._set_items(ed.ui.lstComida, to_items(ids_by_meal.get("comida", [])))
        ed._set_items(ed.ui.lstMerienda, to_items(ids_by_meal.get("merienda", [])))
        ed._set_items(ed.ui.lstCena, to_items(ids_by_meal.get("cena", [])))
        ed._relabel_all()

    # ---------- persistencia ----------
    def _save_week(self) -> None:
        start = monday_of(date.today())
        code = start.strftime("%Y%m%d")

        templates = Path.cwd() / "templates"
        templates.mkdir(parents=True, exist_ok=True)
        default_path = templates / f"menu_semana_{code}.json"

        fn, _ = QFileDialog.getSaveFileName(
            self, "Guardar semana", str(default_path), "JSON (*.json)"
        )
        if not fn:
            return
        path = Path(fn)
        if path.suffix.lower() != ".json":
            path = path.with_suffix(".json")

        wm = self.to_week_menu()
        data = wm.model_dump(mode="json")
        text = json.dumps(data, indent=2, ensure_ascii=False)
        path.write_text(text, encoding="utf-8")

        try:
            self.repo.save_rules({"last_saved_week": str(path)})
        except Exception:
            pass

        QMessageBox.information(self, "Guardado", f"Semana guardada en:\n{path}")

    def _load_week(self) -> None:
        templates = Path.cwd() / "templates"
        templates.mkdir(parents=True, exist_ok=True)

        fn, _ = QFileDialog.getOpenFileName(
            self, "Cargar semana", str(templates), "JSON (*.json)"
        )
        if not fn:
            return
        data = json.loads(Path(fn).read_text(encoding="utf-8"))
        dias = data.get("dias", {})

        for key in DAY_KEYS:
            ids_by_meal = {}
            d = dias.get(key, {})
            if isinstance(d, dict):
                ids_by_meal = {
                    "desayuno": d.get("desayuno", []),
                    "media_manana": d.get("media_manana", []),
                    "comida": d.get("comida", []),
                    "merienda": d.get("merienda", []),
                    "cena": d.get("cena", []),
                }
            self._set_day_from_ids(key, ids_by_meal)

        QMessageBox.information(self, "Cargado", f"Semana cargada desde:\n{fn}")

    # ---------- export ----------
    def _export(self, kind: str) -> None:
        wm = self.to_week_menu()
        print_view = WeekPrintView(self._foods_by_id, wm, parent=None)
        print_view.resize(1400, 900)

        start = wm.semana_inicio
        code = start.strftime("%Y%m%d")

        outputs = Path.cwd() / "outputs"
        outputs.mkdir(parents=True, exist_ok=True)

        if kind == "pdf":
            default_path = outputs / f"menu_semana_{code}.pdf"
            fn, _ = QFileDialog.getSaveFileName(
                self, "Exportar PDF (semana)", str(default_path), "PDF (*.pdf)"
            )
            if not fn:
                return
            export_widget_to_pdf(print_view, fn)
            QMessageBox.information(self, "Exportado", f"Semana exportada a PDF:\n{fn}")
        else:
            default_path = outputs / f"menu_semana_{code}.png"
            fn, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar Imagen (semana)",
                str(default_path),
                "PNG (*.png);;JPEG (*.jpg)",
            )
            if not fn:
                return
            fmt = "PNG" if fn.lower().endswith(".png") else "JPG"
            export_widget_to_image(print_view, fn, fmt=fmt, scale=2.0)
            QMessageBox.information(self, "Exportado", f"Semana exportada a imagen:\n{fn}")
