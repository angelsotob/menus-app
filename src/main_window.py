from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from core.config import APP_DISPLAY_NAME, ensure_profile_root, get_selected_profile
from core.repository import Repo
from ui import apply_window_defaults, load_ui, set_window_title_suffix


class MainWindow:
    """Wrapper sobre el QMainWindow cargado desde .ui."""

    def __init__(self) -> None:
        self.ui: QMainWindow = load_ui("main_window.ui")  # es un QMainWindow
        apply_window_defaults(self.ui)  # tamaño por defecto + prefijo de título

        # --- NUEVO: icono de la ventana principal ---
        # src/main_window.py -> subir a raíz del repo y buscar Logo/Logo.png
        logo_path = Path(__file__).resolve().parents[1] / "Logo" / "Logo.png"
        if logo_path.exists():
            pm = QPixmap(str(logo_path))
            # asegurar que el pixmap base tenga un mínimo de 256 px
            if pm.width() < 256:
                pm = pm.scaled(256, 256, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon = QIcon(pm)
            self.ui.setWindowIcon(icon)

        self.repo = Repo(ensure_profile_root())
        set_window_title_suffix(self.ui, self._title_with_profile())

        # Barra de estado garantizada
        if self.ui.statusBar() is None:
            self.ui.setStatusBar(QStatusBar(self.ui))

        # Acciones de menú
        act_exit = self.ui.findChild(QAction, "actionExit")
        act_db = self.ui.findChild(QAction, "actionOpenDbEditor")
        act_allergens = self.ui.findChild(QAction, "actionAllergensEditor")
        act_prefs = self.ui.findChild(QAction, "actionPreferences")
        act_about = self.ui.findChild(QAction, "actionAbout")
        act_day = self.ui.findChild(QAction, "actionOpenDayEditor")
        act_week = self.ui.findChild(QAction, "actionOpenWeekPlanner")
        act_cats = self.ui.findChild(QAction, "actionCategoriesEditor")
        act_rules = self.ui.findChild(QAction, "actionRulesEditor")

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
        if act_day:
            act_day.triggered.connect(self.open_day_editor)
        if act_week:
            act_week.triggered.connect(self.open_week_planner)
        if act_cats:
            act_cats.triggered.connect(self.open_categories_editor)
        if act_rules:
            act_rules.triggered.connect(self.open_rules_editor)

        # Stacked central
        self.stack: QStackedWidget | None = self.ui.findChild(QStackedWidget, "stack")

        # Abre DB Editor por defecto
        self.open_db_editor()

    # ---------- helpers ----------
    def _push_central_widget(self, w: QWidget) -> None:
        if self.stack is not None:
            idx = self.stack.addWidget(w)
            self.stack.setCurrentIndex(idx)
        else:
            self.ui.setCentralWidget(w)

    def _status(self, msg: str, ms: int = 2500) -> None:
        sb = self.ui.statusBar()
        if sb is not None:
            sb.showMessage(msg, ms)

    def _title_with_profile(self) -> str:
        prof = get_selected_profile() or "-"
        return f"Perfil: {prof}"

    def _switch_profile(self) -> None:
        """Reinicializa Repo al perfil activo y refresca vistas."""
        self.repo = Repo(ensure_profile_root())
        set_window_title_suffix(self.ui, self._title_with_profile())

        cw = self.ui.centralWidget() if self.stack is None else self.stack.currentWidget()
        if cw is None:
            return

        # DbEditor
        try:
            from widgets.db_editor import DbEditor

            if isinstance(cw, DbEditor):
                cw.refresh_from_repo(self.repo, keep_selection=False)
                return
        except Exception:
            pass

        # DayEditor
        try:
            from widgets.day_editor import DayEditor

            if isinstance(cw, DayEditor):
                cw.set_repo(self.repo)
                return
        except Exception:
            pass

        # WeekPlanner
        try:
            from widgets.week_planner import WeekPlanner

            if isinstance(cw, WeekPlanner):
                cw.set_repo(self.repo)
                return
        except Exception:
            pass

    # ---------- slots ----------
    def open_db_editor(self) -> None:
        from widgets.db_editor import DbEditor

        w = DbEditor(self.repo, parent=self.ui, notify=self._status)
        self._push_central_widget(w)

    def open_allergens_editor(self) -> None:
        from widgets.allergens_editor import AllergensEditor

        dlg = AllergensEditor(self.repo, self.ui)
        dlg.exec()

    def open_preferences(self) -> None:
        from widgets.preferences import PreferencesDialog

        dlg = PreferencesDialog(self.repo, self.ui)
        dlg.profile_changed.connect(lambda *_: self._switch_profile())
        if dlg.exec():
            self._switch_profile()

    def show_about(self) -> None:
        """Diálogo 'Acerca de' con logo, versión, autor, descripción, enlace y licencia."""
        # ⚠️ Ideal: mover a core/config.py
        VERSION = "0.6.0 (en desarrollo)"
        AUTHOR = "Ángel Soto"
        WEBSITE = "https://example.com/manual"
        DESCRIPTION = (
            "NutriPlan es una aplicación sencilla para planificar menús diarios y semanales, "
            "gestionar alimentos, categorías y validar reglas nutricionales."
        )
        LICENSE_HINT = (
            "Este software se distribuye bajo los términos especificados "
            "en el archivo <i>LICENSE</i>. Revísalo antes de redistribuir."
        )

        dlg = QDialog(self.ui)
        dlg.setWindowTitle(f"Acerca de {APP_DISPLAY_NAME}")

        # Logo
        logo_path = Path(__file__).resolve().parents[1] / "Logo" / "Logo.png"
        logo_lbl = QLabel()
        logo_lbl.setAlignment(Qt.AlignCenter)
        if logo_path.exists():
            pm = QPixmap(str(logo_path))
            pm = pm.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pm)
            dlg.setWindowIcon(QIcon(pm))

        # Texto rico con enlaces
        txt = QLabel(dlg)
        txt.setTextFormat(Qt.RichText)
        txt.setOpenExternalLinks(True)
        txt.setWordWrap(True)
        txt.setText(
            f"<h2 style='margin:0'>{APP_DISPLAY_NAME}</h2>"
            f"<p><b>Versión:</b> {VERSION}</p>"
            f"<p><b>Autor:</b> {AUTHOR}</p>"
            f"<p>{DESCRIPTION}</p>"
            f"<p><a href='{WEBSITE}'>Manual de usuario</a></p>"
            f"<p style='color:#888; font-size:10pt'><i>{LICENSE_HINT}</i></p>"
        )

        # Layout
        main_layout = QVBoxLayout(dlg)
        top = QHBoxLayout()
        top.addWidget(logo_lbl, 0)
        top.addWidget(txt, 1)
        main_layout.addLayout(top)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok, parent=dlg)
        buttons.accepted.connect(dlg.accept)
        main_layout.addWidget(buttons)

        dlg.resize(560, 300)
        dlg.exec()

    def show(self) -> None:
        self.ui.show()

    def open_day_editor(self) -> None:
        from widgets.day_editor import DayEditor

        w = DayEditor(self.repo, parent=self.ui)
        self._push_central_widget(w)

    def open_week_planner(self) -> None:
        from widgets.week_planner import WeekPlanner

        w = WeekPlanner(self.repo, parent=self.ui)
        self._push_central_widget(w)

    def open_categories_editor(self) -> None:
        from widgets.categories_editor import CategoriesEditor

        dlg = CategoriesEditor(self.repo, self.ui)
        if dlg.exec():
            self._status("Categorías actualizadas", 2500)

    def open_rules_editor(self) -> None:
        from widgets.rules_editor import RulesEditor

        dlg = RulesEditor(self.repo, self.ui)
        dlg.exec()
