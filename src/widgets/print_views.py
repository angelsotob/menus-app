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
    """Clean table to export a day (fixed-width items column with wrapping)."""

    HEADERS = ["Meal", "Elements"]

    def __init__(self, foods_by_id: dict[str, Food], day: DayMeals, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        title = QLabel("Menú diario")
        title.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        layout.addWidget(title)

        tbl = QTableWidget(5, 2, self)
        tbl.setHorizontalHeaderLabels(self.HEADERS)

        # Configure fixed column width and wrap
        tbl.setWordWrap(True)
        hdr: QHeaderView = tbl.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Fixed)
        # Column 0 narrower for the meal label; column 1 fixed for wrapped text.
        tbl.setColumnWidth(0, 140)
        tbl.setColumnWidth(1, 600)

        rows = [
            ("Desayuno", day.breakfast),
            ("Media mañana", day.midmorning),
            ("Comida", day.lunch),
            ("Merienda", day.snack),
            ("Cena", day.dinner),
        ]
        for r, (label, ids) in enumerate(rows):
            item0 = QTableWidgetItem(label)
            item0.setFlags(item0.flags() & ~Qt.ItemIsEditable)
            tbl.setItem(r, 0, item0)

            names = [foods_by_id[i].name for i in ids if i in foods_by_id]
            item1 = QTableWidgetItem(", ".join(names))
            item1.setFlags(item1.flags() & ~Qt.ItemIsEditable)
            item1.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
            tbl.setItem(r, 1, item1)

        tbl.resizeRowsToContents()
        layout.addWidget(tbl)
        self.setLayout(layout)


class WeekPrintView(QWidget):
    """ "Clean grid to export a week with fixed column width and wrapping."""

    MEALS = ["Breakfast", "Midmorning", "Lunch", "Snack", "Dinner"]
    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    def __init__(self, foods_by_id: dict[str, Food], week: WeekMenu, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        title = QLabel("Menú semanal")
        title.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        layout.addWidget(title)

        tbl = QTableWidget(len(self.MEALS), len(self.DAYS), self)
        tbl.setHorizontalHeaderLabels(self.DAYS)
        tbl.setVerticalHeaderLabels(self.MEALS)

        # Set fixed width and uniform wrapping per day.
        tbl.setWordWrap(True)
        hdr_h: QHeaderView = tbl.horizontalHeader()
        hdr_h.setSectionResizeMode(QHeaderView.Fixed)
        # Fixed width per day (adjust if you want more/less text per column).
        fixed_day_width = 170
        for c in range(len(self.DAYS)):
            tbl.setColumnWidth(c, fixed_day_width)

        # Set row height based on content.
        hdr_v: QHeaderView = tbl.verticalHeader()
        hdr_v.setSectionResizeMode(QHeaderView.ResizeToContents)

        dias = week.days
        keys = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

        for c, day_key in enumerate(keys):
            d = dias.get(day_key)
            if not d:
                continue
            rows = [d.breakfast, d.midmorning, d.lunch, d.snack, d.dinner]
            for r, ids in enumerate(rows):
                names = [foods_by_id[i].name for i in ids if i in foods_by_id]
                item = QTableWidgetItem(", ".join(names))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
                tbl.setItem(r, c, item)

        tbl.resizeRowsToContents()
        layout.addWidget(tbl)
        self.setLayout(layout)
