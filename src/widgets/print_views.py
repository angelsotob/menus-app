from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.models import DayMeals, Food, WeekMenu


class DayPrintView(QWidget):
    """Tabla limpia para exportar un día (columna de elementos con ancho fijo y wrap)."""

    HEADERS = ["Comida", "Elementos"]

    def __init__(self, foods_by_id: dict[str, Food], day: DayMeals, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        title = QLabel("Menú diario")
        title.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        layout.addWidget(title)

        tbl = QTableWidget(5, 2, self)
        tbl.setHorizontalHeaderLabels(self.HEADERS)

        # Configurar ancho fijo y wrap
        tbl.setWordWrap(True)
        hdr: QHeaderView = tbl.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Fixed)
        # Columna 0 más estrecha para etiqueta de comida; columna 1 fija para texto con salto
        tbl.setColumnWidth(0, 140)
        tbl.setColumnWidth(1, 600)

        rows = [
            ("Desayuno", day.desayuno),
            ("Media mañana", day.media_manana),
            ("Comida", day.comida),
            ("Merienda", day.merienda),
            ("Cena", day.cena),
        ]
        for r, (label, ids) in enumerate(rows):
            item0 = QTableWidgetItem(label)
            item0.setFlags(item0.flags() & ~Qt.ItemIsEditable)
            tbl.setItem(r, 0, item0)

            names = [foods_by_id[i].nombre for i in ids if i in foods_by_id]
            item1 = QTableWidgetItem(", ".join(names))
            item1.setFlags(item1.flags() & ~Qt.ItemIsEditable)
            item1.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
            tbl.setItem(r, 1, item1)

        tbl.resizeRowsToContents()
        layout.addWidget(tbl)
        self.setLayout(layout)


class WeekPrintView(QWidget):
    """Grid limpio para exportar una semana con ancho de columna fijo y wrap."""

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

        # Configurar ancho fijo y wrap uniforme por día
        tbl.setWordWrap(True)
        hdr_h: QHeaderView = tbl.horizontalHeader()
        hdr_h.setSectionResizeMode(QHeaderView.Fixed)
        # Ancho fijo por día (ajusta si quieres más/menos texto por columna)
        fixed_day_width = 170
        for c in range(len(self.DAYS)):
            tbl.setColumnWidth(c, fixed_day_width)

        # Altura de filas según contenido
        hdr_v: QHeaderView = tbl.verticalHeader()
        hdr_v.setSectionResizeMode(QHeaderView.ResizeToContents)

        dias = week.dias
        keys = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]

        for c, day_key in enumerate(keys):
            d = dias.get(day_key)
            if not d:
                continue
            rows = [d.desayuno, d.media_manana, d.comida, d.merienda, d.cena]
            for r, ids in enumerate(rows):
                names = [foods_by_id[i].nombre for i in ids if i in foods_by_id]
                item = QTableWidgetItem(", ".join(names))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
                tbl.setItem(r, c, item)

        tbl.resizeRowsToContents()
        layout.addWidget(tbl)
        self.setLayout(layout)
