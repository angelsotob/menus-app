from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from core.models import Food


class FoodTableModel(QAbstractTableModel):
    COLS = ["Nombre", "Categoría", "Alergenos", "Etiquetas", "Activo"]

    def __init__(self, rows: list[Food] | None = None) -> None:
        super().__init__()
        self._rows: list[Food] = rows or []
        self._filtered_idx: list[int] = list(range(len(self._rows)))
        self._text = ""
        self._category: str | None = None
        self._show_inactive = True

    # ---- base ----
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # type: ignore[override]
        return 0 if parent.isValid() else len(self._filtered_idx)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # type: ignore[override]
        return 0 if parent.isValid() else len(self.COLS)

    def headerData(self, section: int, orientation, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.COLS[section]
        return section + 1

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid():
            return None
        if role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        food = self._rows[self._filtered_idx[index.row()]]
        col = index.column()
        if col == 0:
            return food.name
        if col == 1:
            return food.category
        if col == 2:
            return ", ".join(food.allergens)
        if col == 3:
            return ", ".join(food.labels)
        if col == 4:
            return "Sí" if food.active else "No"
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:  # type: ignore[override]
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    # ---- public API ----
    def set_rows(self, rows: list[Food]) -> None:
        self._rows = rows
        self._refilter()

    def current_food(self, row: int) -> Food:
        return self._rows[self._filtered_idx[row]]

    def apply_filters(
        self,
        text: str = "",
        category: str | None = None,
        show_inactive: bool = True,
    ) -> None:
        self._text = text.strip().lower()
        self._category = category
        self._show_inactive = show_inactive
        self._refilter()

    def _refilter(self) -> None:
        self.beginResetModel()
        idx: list[int] = []
        for i, f in enumerate(self._rows):
            if not self._show_inactive and not f.active:
                continue
            if self._category and self._category != "(All)" and f.category != self._category:
                continue
            if self._text:
                parts = [
                    f.name,
                    f.category,
                    " ".join(f.allergens),
                    " ".join(f.labels),
                ]
                haystack = " ".join(parts).lower()
                if self._text not in haystack:
                    continue
            idx.append(i)
        self._filtered_idx = idx
        self.endResetModel()

    @staticmethod
    def categories() -> list[str]:
        return [
            "(All)",
            "Protein",
            "Vegetables",
            "Fruit",
            "Cereals",
            "Legumes",
            "Fish",
            "Seafood",
            "Eggs",
            "Milk",
            "Nuts",
            "Fats",
            "Others",
        ]
