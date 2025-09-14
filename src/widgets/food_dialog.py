from __future__ import annotations

import uuid

from PySide6.QtWidgets import QDialog

from core.models import Food
from core.repository import Repo
from ui import load_ui


class FoodDialog(QDialog):
    def __init__(self, repo: Repo, current: Food | None, parent=None) -> None:
        super().__init__(parent)
        self.ui = load_ui("food_dialog.ui")
        self.setLayout(self.ui.layout())

        self.repo = repo
        self.result_food: Food | None = None

        # --- Categorías dinámicas (ES) ---
        cats = self.repo.list_categories()
        # dedup preservando orden
        seen: set[str] = set()
        cats = [c for c in cats if not (c in seen or seen.add(c))]

        self.ui.cmbCategory.clear()
        for c in cats:
            self.ui.cmbCategory.addItem(c, c)  # mostramos ES y guardamos ES

        # --- Alérgenos ---
        self.ui.lstAllergens.clear()
        for a in self.repo.list_allergens():
            self.ui.lstAllergens.addItem(a)

        # --- Editar: precargar ---
        if current:
            self.ui.txtName.setText(current.name)
            idx = -1
            for i in range(self.ui.cmbCategory.count()):
                if self.ui.cmbCategory.itemData(i) == current.category:
                    idx = i
                    break
            self.ui.cmbCategory.setCurrentIndex(max(0, idx))
            self.ui.txtTags.setText(", ".join(current.labels))
            self.ui.txtNotes.setPlainText(current.notes or "")
            self.ui.chkActive.setChecked(current.active)
            cur_all = set(current.allergens)
            for i in range(self.ui.lstAllergens.count()):
                item = self.ui.lstAllergens.item(i)
                item.setSelected(item.text() in cur_all)
            self._id = current.id
        else:
            self._id = f"food_{uuid.uuid4().hex[:8]}"

        self.ui.buttonBox.accepted.connect(self._accept)
        self.ui.buttonBox.rejected.connect(self.reject)

    def _accept(self) -> None:
        name = self.ui.txtName.text().strip()
        if not name:
            self.ui.txtName.setFocus()
            return

        category = (self.ui.cmbCategory.currentData() or self.ui.cmbCategory.currentText()).strip()
        labels = [t.strip() for t in self.ui.txtTags.text().split(",") if t.strip()]
        notes = self.ui.txtNotes.toPlainText().strip() or None
        sel_allergens = [i.text() for i in self.ui.lstAllergens.selectedItems()]
        active = self.ui.chkActive.isChecked()

        self.result_food = Food(
            id=self._id,
            name=name,
            category=category,  # ES
            allergens=sel_allergens,
            labels=labels,
            notes=notes,
            active=active,
        )
        self.accept()
