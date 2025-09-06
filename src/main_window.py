from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QMessageBox, QStackedWidget, QStatusBar, QWidget

from core.config import ensure_data_dir
from core.repository import Repo
from ui import load_ui


class MainWindow:
    """Wrapper sobre el QMainWindow cargado desde .ui."""

    def __init__(self) -> None:
        self.ui: QMainWindow = load_ui("main_window.ui")  # es un QMainWindow
        self.ui.setWindowTitle("MenusApp — Base de datos")
        self.repo = Repo(ensure_data_dir())

        # --- Asegura que hay status bar (pónlo justo después de cargar self.ui) ---
        if self.ui.statusBar() is None:
            self.ui.setStatusBar(QStatusBar(self.ui))
        # ----------------------------------------------------------------------------

        # Acciones de menú
        act_exit = self.ui.findChild(QAction, "actionExit")
        act_db = self.ui.findChild(QAction, "actionOpenDbEditor")
        act_allergens = self.ui.findChild(QAction, "actionAllergensEditor")
        act_prefs = self.ui.findChild(QAction, "actionPreferences")
        act_about = self.ui.findChild(QAction, "actionAbout")

        if act_exit:
            act_exit.triggered.connect(self.ui.close)
        if act_db:
            act_db.triggered.connect(self.open_db_editor)
        if act_allergens:
            act_allergens.triggered.connect(self.open_allergens_editor)
        if act_prefs:
            act_prefs.triggered.connect(self.open_preferences)
        if act_about:
            act_about.triggered.connect(self.show_about)

        # Stacked central
        self.stack: QStackedWidget | None = self.ui.findChild(QStackedWidget, "stack")

        # Abre por defecto el editor de BD
        self.open_db_editor()

    # ---------- helpers ----------
    def _push_central_widget(self, w: QWidget) -> None:
        if self.stack is not None:
            idx = self.stack.addWidget(w)
            self.stack.setCurrentIndex(idx)
        else:
            self.ui.setCentralWidget(w)

    def _status(self, msg: str, ms: int = 2500) -> None:
        # llamado por DbEditor para mostrar mensajes
        sb = self.ui.statusBar()
        if sb is not None:
            sb.showMessage(msg, ms)

    # ---------- slots ----------
    def open_db_editor(self) -> None:
        from widgets.db_editor import DbEditor  # import diferido

        w = DbEditor(self.repo, parent=self.ui, notify=self._status)
        self._push_central_widget(w)

    def open_allergens_editor(self) -> None:
        from widgets.allergens_editor import AllergensEditor

        dlg = AllergensEditor(self.repo, self.ui)
        dlg.exec()

    def open_preferences(self) -> None:
        from widgets.preferences import PreferencesDialog

        dlg = PreferencesDialog(self.repo, self.ui)
        dlg.exec()

    def show_about(self) -> None:
        QMessageBox.information(self.ui, "Acerca de", "MenusApp — Editor de Base de Datos")

    def show(self) -> None:
        self.ui.show()
