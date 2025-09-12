from __future__ import annotations

from PySide6.QtWidgets import QDialog, QInputDialog

from core.repository import Repo
from ui import load_ui


class AllergensEditor(QDialog):
    def __init__(self, repo: Repo, parent=None) -> None:
        super().__init__(parent)
        self.ui = load_ui("allergens_editor.ui")
        self.setLayout(self.ui.layout())
        self.repo = repo

        self._reload()

        self.ui.btnAdd.clicked.connect(self.on_add)
        self.ui.btnRename.clicked.connect(self.on_rename)
        self.ui.btnRemove.clicked.connect(self.on_remove)
        self.ui.buttonBox.accepted.connect(self._save_and_close)
        self.ui.buttonBox.rejected.connect(self.reject)

    def _reload(self) -> None:
        self.ui.lstAllergens.clear()
        for a in self.repo.list_allergens():
            self.ui.lstAllergens.addItem(a)

    def on_add(self) -> None:
        text, ok = QInputDialog.getText(self, "New allergen", "Name:")
        if ok and text.strip():
            self.ui.lstAllergens.addItem(text.strip())

    def on_rename(self) -> None:
        cur = self.ui.lstAllergens.currentItem()
        if not cur:
            return
        text, ok = QInputDialog.getText(self, "Rename", "New name:", text=cur.text())
        if ok and text.strip():
            cur.setText(text.strip())

    def on_remove(self) -> None:
        cur = self.ui.lstAllergens.currentItem()
        if cur:
            self.ui.lstAllergens.takeItem(self.ui.lstAllergens.row(cur))

    def _save_and_close(self) -> None:
        items = [self.ui.lstAllergens.item(i).text() for i in range(self.ui.lstAllergens.count())]
        self.repo.save_allergens(items)
        self.accept()
