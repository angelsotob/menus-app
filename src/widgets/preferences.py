from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QFileDialog, QInputDialog, QMessageBox

from core.config import (
    ensure_data_dir,
    ensure_profile_root,
    get_selected_profile,
    list_profiles,
    profile_root,
    set_selected_profile,
)
from ui import load_ui


class PreferencesDialog(QDialog):
    # Señal para notificar cambio de perfil: envía (perfil:str, ruta:Path)
    profile_changed = Signal(str, Path)

    def __init__(self, repo, parent=None) -> None:
        super().__init__(parent)
        self.ui = load_ui("preferences.ui")
        self.setLayout(self.ui.layout())
        self.repo = repo

        # Datos generales
        self.ui.txtDataDir.setText(str(ensure_data_dir()))
        self.ui.cmbTheme.addItems(["Oscuro (por defecto)", "Claro"])
        self.ui.cmbTheme.setCurrentIndex(0)

        # Perfiles
        self._reload_profiles_ui()

        # Conexiones
        self.ui.btnBrowseDataDir.clicked.connect(self._browse)
        self.ui.btnNewProfile.clicked.connect(self._new_profile)
        self.ui.buttonBox.accepted.connect(self._accept)
        self.ui.buttonBox.rejected.connect(self.reject)

    # -------- Perfiles UI --------
    def _reload_profiles_ui(self) -> None:
        self.ui.cmbProfile.clear()
        names = list_profiles()
        if not names:
            # Garantiza uno por defecto
            ensure_profile_root()
            names = list_profiles()
        self.ui.cmbProfile.addItems(names)
        # Marca activo
        active = get_selected_profile()
        if active:
            idx = self.ui.cmbProfile.findText(active)
            if idx >= 0:
                self.ui.cmbProfile.setCurrentIndex(idx)
        self.ui.lblProfile.setText(f"Perfil activo: {get_selected_profile() or '-'}")

    def _new_profile(self) -> None:
        name, ok = QInputDialog.getText(self, "Nuevo perfil", "Nombre del perfil:")
        if not ok or not name.strip():
            return
        name = name.strip()
        if name in list_profiles():
            QMessageBox.information(self, "Aviso", "Ese perfil ya existe.")
            return

        # Crear carpeta y sembrar archivos mínimos si quieres (opcional)
        root = profile_root(name)
        root.mkdir(parents=True, exist_ok=True)
        (root / "backups").mkdir(parents=True, exist_ok=True)

        # Copia semillas si te interesa (alimentos/alergenos vacíos, por ejemplo)
        # Aquí lo dejamos vacío para que cada perfil arranque limpio.

        # Selecciona nuevo perfil
        set_selected_profile(name)
        self._reload_profiles_ui()
        # Emite señal ya (cambio on the go)
        self.profile_changed.emit(name, root)

    def _accept(self) -> None:
        # Si se cambió el seleccionado, aplicamos y emitimos
        current = self.ui.cmbProfile.currentText().strip()
        if current and current != (get_selected_profile() or ""):
            set_selected_profile(current)
            root = ensure_profile_root()
            self.profile_changed.emit(current, root)

        self.accept()

    # -------- Data dir browse --------
    def _browse(self) -> None:
        new = QFileDialog.getExistingDirectory(
            self,
            "Selecciona carpeta de datos",
            self.ui.txtDataDir.text(),
        )
        if new:
            self.ui.txtDataDir.setText(new)
            # Nota: cambiar físicamente la ruta global implicaría migrar perfiles;
            # lo dejamos como vista informativa.
