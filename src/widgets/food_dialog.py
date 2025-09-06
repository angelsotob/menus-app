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

        # categorías
        self.ui.cmbCategory.addItems(
            [
                "proteina",
                "verdura",
                "fruta",
                "cereal_harina",
                "legumbre",
                "pescado",
                "marisco",
                "huevo",
                "lacteo",
                "frutos_secos",
                "grasa",
                "otros",
            ]
        )
        # alérgenos
        for a in self.repo.list_allergens():
            self.ui.lstAllergens.addItem(a)

        if current:
            self.ui.txtName.setText(current.nombre)
            idx = self.ui.cmbCategory.findText(current.categoria)
            self.ui.cmbCategory.setCurrentIndex(max(0, idx))
            self.ui.txtTags.setText(", ".join(current.etiquetas))
            self.ui.txtNotes.setPlainText(current.notas or "")
            self.ui.chkActive.setChecked(current.activo)
            # selección de alérgenos
            for i in range(self.ui.lstAllergens.count()):
                item = self.ui.lstAllergens.item(i)
                item.setSelected(item.text() in set(current.alergenos))
            self._id = current.id
        else:
            self._id = f"food_{uuid.uuid4().hex[:8]}"

        self.ui.buttonBox.accepted.connect(self._accept)
        self.ui.buttonBox.rejected.connect(self.reject)

    def _accept(self) -> None:
        nombre = self.ui.txtName.text().strip()
        if not nombre:
            self.ui.txtName.setFocus()
            return
        categoria = self.ui.cmbCategory.currentText()
        etiquetas = [t.strip() for t in self.ui.txtTags.text().split(",") if t.strip()]
        notas = self.ui.txtNotes.toPlainText().strip() or None
        sel_allergens = [i.text() for i in self.ui.lstAllergens.selectedItems()]
        activo = self.ui.chkActive.isChecked()

        self.result_food = Food(
            id=self._id,
            nombre=nombre,
            categoria=categoria,  # type: ignore[arg-type]
            alergenos=sel_allergens,
            etiquetas=etiquetas,
            notas=notas,
            activo=activo,
        )
        self.accept()
