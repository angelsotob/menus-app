from __future__ import annotations

from PySide6.QtWidgets import QDialog, QFileDialog

from core.config import ensure_data_dir
from ui import load_ui


class PreferencesDialog(QDialog):
    def __init__(self, repo, parent=None) -> None:
        super().__init__(parent)
        self.ui = load_ui("preferences.ui")
        self.setLayout(self.ui.layout())
        self.repo = repo

        self.ui.txtDataDir.setText(str(ensure_data_dir()))
        self.ui.cmbTheme.addItems(["Oscuro (por defecto)", "Claro"])
        self.ui.cmbTheme.setCurrentIndex(0)

        self.ui.btnBrowseDataDir.clicked.connect(self._browse)
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)

    def _browse(self) -> None:
        new = QFileDialog.getExistingDirectory(
            self,
            "Selecciona carpeta de datos",
            self.ui.txtDataDir.text(),
        )
        if new:
            self.ui.txtDataDir.setText(new)
            # Nota: para cambiar la ruta real, habría que re-instanciar Repo
            # apuntando a esa ruta y copiar datos.
