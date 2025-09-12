from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QMessageBox, QStackedWidget, QStatusBar, QWidget

from core.config import ensure_profile_root, get_selected_profile
from core.repository import Repo
from ui import load_ui


class MainWindow:
    """Wrapper over the QMainWindow loaded from .ui."""

    def __init__(self) -> None:
        self.ui: QMainWindow = load_ui("main_window.ui")  # is a QMainWindow
        self.repo = Repo(ensure_profile_root())
        self.ui.setWindowTitle(self._title_with_profile())

        # Ensures status bar
        if self.ui.statusBar() is None:
            self.ui.setStatusBar(QStatusBar(self.ui))

        # Menu actions
        act_exit = self.ui.findChild(QAction, "actionExit")
        act_db = self.ui.findChild(QAction, "actionOpenDbEditor")
        act_allergens = self.ui.findChild(QAction, "actionAllergensEditor")
        act_prefs = self.ui.findChild(QAction, "actionPreferences")
        act_about = self.ui.findChild(QAction, "actionAbout")
        act_day = self.ui.findChild(QAction, "actionOpenDayEditor")
        act_week = self.ui.findChild(QAction, "actionOpenWeekPlanner")
        act_cats = self.ui.findChild(QAction, "actionCategoriesEditor")

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

        # Stacked central
        self.stack: QStackedWidget | None = self.ui.findChild(QStackedWidget, "stack")

        # Opens DB Editor by default
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
        return f"MenusApp — Perfil: {prof}"

    def _switch_profile(self) -> None:
        """Reinitialize the Repo to the active profile and refresh open views."""
        self.repo = Repo(ensure_profile_root())
        self.ui.setWindowTitle(self._title_with_profile())

        # Refresh the active widget if it supports set_repo/refresh.
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
        # On-the-go reload when a profile is changed/created.
        dlg.profile_changed.connect(lambda *_: self._switch_profile())
        if dlg.exec():
            # In case the change was applied when pressing OK.
            self._switch_profile()

    def show_about(self) -> None:
        QMessageBox.information(self.ui, "Acerca de", "MenusApp — Preferencias y Perfiles")

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
