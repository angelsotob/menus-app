from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from core.models import DayMeals, Food, WeekMenu


class DayPrintView(QWidget):
    """Tabla limpia para exportar un día."""

    HEADERS = ["Comida", "Elementos"]

    def __init__(self, foods_by_id: dict[str, Food], day: DayMeals, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        title = QLabel("Menú diario")
        title.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        layout.addWidget(title)

        tbl = QTableWidget(5, 2, self)
        tbl.setHorizontalHeaderLabels(self.HEADERS)
        rows = [
            ("Desayuno", day.desayuno),
            ("Media mañana", day.media_manana),
            ("Comida", day.comida),
            ("Merienda", day.merienda),
            ("Cena", day.cena),
        ]
        for r, (label, ids) in enumerate(rows):
            tbl.setItem(r, 0, QTableWidgetItem(label))
            names = [foods_by_id[i].nombre for i in ids if i in foods_by_id]
            tbl.setItem(r, 1, QTableWidgetItem(", ".join(names)))
        tbl.resizeColumnsToContents()
        tbl.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(tbl)
        self.setLayout(layout)


class WeekPrintView(QWidget):
    """Grid limpio para exportar una semana."""

    MEALS = ["Desayuno", "Media mañana", "Comida", "Merienda", "Cena"]
    DAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    def __init__(self, foods_by_id: dict[str, Food], week: WeekMenu, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        title = QLabel("Menú semanal")
        title.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        layout.addWidget(title)

        tbl = QTableWidget(len(self.MEALS), len(self.DAYS), self)
        tbl.setHorizontalHeaderLabels(self.DAYS)
        tbl.setVerticalHeaderLabels(self.MEALS)

        dias = week.dias
        for c, day_key in enumerate(
            ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
        ):
            d = dias.get(day_key)
            if not d:
                continue
            rows = [d.desayuno, d.media_manana, d.comida, d.merienda, d.cena]
            for r, ids in enumerate(rows):
                names = [foods_by_id[i].nombre for i in ids if i in foods_by_id]
                tbl.setItem(r, c, QTableWidgetItem(", ".join(names)))
        tbl.resizeColumnsToContents()
        tbl.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(tbl)
        self.setLayout(layout)
