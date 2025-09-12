from __future__ import annotations

import uuid

from PySide6.QtWidgets import QDialog

from core.models import Food
from core.repository import Repo
from ui import load_ui

# Mapea valor interno -> texto mostrado (ES)
CAT_I18N = {
    "Protein": "Proteína",
    "Fish": "Pescado",
    "Seafood": "Marisco",
    "Vegetables": "Verduras",
    "Fruit": "Fruta",
    "Fruits": "Fruta",  # por si viniera del JSON en plural
    "Legumes": "Legumbres",
    "Cereals": "Cereales",
    "Milk": "Lácteos",
    "Eggs": "Huevos",
    "Nuts": "Frutos secos",
    "Fats": "Grasas",
    "Others": "Otros",
    # Variantes en ES por si estuvieran en datos viejos:
    "Proteina": "Proteína",
    "Pescado": "Pescado",
    "Marisco": "Marisco",
    "Vegetales": "Verduras",
    "Fruta": "Fruta",
    "Legumbres": "Legumbres",
    "Cereales": "Cereales",
    "Lácteos": "Lácteos",
    "Otros": "Otros",
}

# Inversa para fallback: texto mostrado ES -> valor interno si es posible
I18N_REV = {v: k for k, v in CAT_I18N.items()}


class FoodDialog(QDialog):
    def __init__(self, repo: Repo, current: Food | None, parent=None) -> None:
        super().__init__(parent)
        self.ui = load_ui("food_dialog.ui")
        self.setLayout(self.ui.layout())

        self.repo = repo
        self.result_food: Food | None = None

        # --- Categorías dinámicas ---
        # 1) Trae del repo
        cats = self.repo.list_categories()

        # 2) Dedup preservando orden (por si el repo trajera duplicadas)
        seen: set[str] = set()
        cats = [c for c in cats if not (c in seen or seen.add(c))]

        # 3) Poblado del combo: mostramos ES, guardamos "internal" en userData
        self.ui.cmbCategory.clear()
        for internal in cats:
            display = CAT_I18N.get(internal, internal)  # fallback a lo que venga
            self.ui.cmbCategory.addItem(display, internal)

        # --- Alérgenos ---
        self.ui.lstAllergens.clear()
        for a in self.repo.list_allergens():
            self.ui.lstAllergens.addItem(a)

        # --- Si estamos editando, precargar valores ---
        if current:
            self.ui.txtName.setText(current.name)

            # Intento 1: buscar por userData == categoría interna actual
            idx = -1
            for i in range(self.ui.cmbCategory.count()):
                if self.ui.cmbCategory.itemData(i) == current.category:
                    idx = i
                    break

            # Intento 2 (fallback): si la categoría guardada es ES, mapear a interna y seleccionar
            if idx < 0:
                maybe_internal = I18N_REV.get(current.category)
                if maybe_internal is not None:
                    for i in range(self.ui.cmbCategory.count()):
                        if self.ui.cmbCategory.itemData(i) == maybe_internal:
                            idx = i
                            break

            self.ui.cmbCategory.setCurrentIndex(max(0, idx))

            self.ui.txtTags.setText(", ".join(current.labels))
            self.ui.txtNotes.setPlainText(current.notes or "")
            self.ui.chkActive.setChecked(current.active)

            # Selección de alérgenos
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

        # Siempre preferimos el userData (valor interno). Si no hay, intentamos
        # mapear el texto mostrado ES -> interno; y si no, usamos el texto tal cual.
        data = self.ui.cmbCategory.currentData()
        if data:
            category = str(data).strip()
        else:
            shown = self.ui.cmbCategory.currentText().strip()
            category = I18N_REV.get(shown, shown)

        labels = [t.strip() for t in self.ui.txtTags.text().split(",") if t.strip()]
        notes = self.ui.txtNotes.toPlainText().strip() or None
        sel_allergens = [i.text() for i in self.ui.lstAllergens.selectedItems()]
        active = self.ui.chkActive.isChecked()

        self.result_food = Food(
            id=self._id,
            name=name,
            category=category,  # string dinámica
            allergens=sel_allergens,
            labels=labels,
            notes=notes,
            active=active,
        )
        self.accept()
