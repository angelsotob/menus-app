from __future__ import annotations

import json

from PySide6.QtWidgets import QDialog, QMessageBox

from core.i18n import OP_SYMBOL2LONGWORD_ES, OP_WORD2SYMBOL_ES
from core.repository import Repo
from ui import apply_window_defaults, load_ui

RENDER_OP_ES = {
    ">=": "al menos",
    ">": "más de",
    "==": "exactamente",
    "<=": "como máximo",
    "<": "menos de",
    "!=": "distinto de",
}


class RulesEditor(QDialog):
    """
    Editor de reglas con:
      - Constructor guiado
      - Vista legible (diarias/semanales)
      - Visor/Editor JSON alternable (Ver/Ocultar JSON)
    """

    def __init__(self, repo: Repo, parent=None) -> None:
        super().__init__(parent)
        self.ui = load_ui("rules_editor.ui")
        self.setLayout(self.ui.layout())
        apply_window_defaults(self)
        self.repo = repo

        # UI init
        self._init_scope()
        self._init_type()
        self._init_ops()
        self._init_categories()
        self._init_foods()

        # --- NUEVO: filtrar alimentos al cambiar categoría ---
        self.ui.cmbCategory.currentIndexChanged.connect(self._reload_foods_by_selected_category)
        self._reload_foods_by_selected_category()  # inicial

        # Mostrar vista legible por defecto; ocultar JSON
        self.ui.txtJson.setVisible(False)
        self.ui.btnToggleJson.setText("Ver JSON")

        # Cargar texto JSON desde archivo y refrescar vista
        self._reload_text()
        self._refresh_rules_view()

        # Connections
        self.ui.btnLoadDefaults.clicked.connect(self._load_defaults)
        self.ui.btnReloadFromFile.clicked.connect(self._reload_text)
        self.ui.btnReloadFromFile.clicked.connect(self._refresh_rules_view)
        self.ui.btnAddRule.clicked.connect(self._add_rule)
        self.ui.btnToggleJson.clicked.connect(self._toggle_json)
        self.ui.buttonBox.accepted.connect(self._save)
        self.ui.buttonBox.rejected.connect(self.reject)

        # Reactividad básica (si quieres ocultar/mostrar campos por tipo)
        self.ui.cmbType.currentTextChanged.connect(self._toggle_fields_by_type)
        self._toggle_fields_by_type()

    # ---------- inits ----------
    def _init_scope(self) -> None:
        self.ui.cmbScope.clear()
        self.ui.cmbScope.addItem("Diario", "daily")
        self.ui.cmbScope.addItem("Semanal", "weekly")

    def _init_type(self) -> None:
        self.ui.cmbType.clear()
        self.ui.cmbType.addItem("Cantidad de categoría", "category_count")
        self.ui.cmbType.addItem("Cantidad de alimento", "item_count")
        self.ui.cmbType.addItem("Prohibir alérgeno (diario)", "forbid_allergen")
        self.ui.cmbType.addItem(
            "No repetir alimento en días consecutivos (semanal)",
            "do_not_repeat_consecutive_item",
        )

    def _init_ops(self) -> None:
        self.ui.cmbOp.clear()
        # Mostrar en texto; mapear a símbolo al guardar
        for sym, long_word in OP_SYMBOL2LONGWORD_ES.items():
            self.ui.cmbOp.addItem(long_word, sym)

    def _init_categories(self) -> None:
        cfg = self.repo.load_categories_config()
        cats_es = list(cfg.get("categories", []))
        self.ui.cmbCategory.clear()
        self.ui.cmbCategory.addItem("(vacío)", "")
        for c in cats_es:
            self.ui.cmbCategory.addItem(c, c)

    def _init_foods(self) -> None:
        # Inicialización mínima; el llenado real lo hace _reload_foods_by_selected_category()
        self.ui.cmbFood.clear()
        self.ui.cmbFood.addItem("Todos", "Todos")

    # ---------- helpers ----------
    def _rules_from_editor(self) -> dict:
        try:
            data = json.loads(self.ui.txtJson.toPlainText() or "{}")
            if not isinstance(data, dict):
                raise ValueError("El JSON raíz debe ser un objeto")
        except Exception:
            data = {}
        data.setdefault("version", 1)
        data.setdefault("daily", [])
        data.setdefault("weekly", [])
        return data

    def _set_rules_text(self, data: dict) -> None:
        self.ui.txtJson.setPlainText(json.dumps(data, ensure_ascii=False, indent=2))

    def _toggle_fields_by_type(self) -> None:
        # Mantén todos visibles (sencillo). Si quieres, aquí puedes ocultar por tipo.
        return

    # ---------- NUEVO: filtrado de alimentos por categoría seleccionada ----------
    def _selected_category(self) -> str | None:
        cat = self.ui.cmbCategory.currentData()
        return cat if isinstance(cat, str) and cat.strip() else None

    def _reload_foods_by_selected_category(self) -> None:
        cat = self._selected_category()
        foods = self.repo.list_foods()
        if cat:
            foods = [f for f in foods if f.category == cat]

        self.ui.cmbFood.blockSignals(True)
        try:
            self.ui.cmbFood.clear()
            self.ui.cmbFood.addItem("Todos", "Todos")
            for f in foods:
                self.ui.cmbFood.addItem(f.name, f.name)
        finally:
            self.ui.cmbFood.blockSignals(False)

    # ---------- pretty render ----------
    def _op_text(self, op: str | None) -> str:
        if not op:
            return ""
        return RENDER_OP_ES.get(op, op)

    def _rule_to_text(self, scope: str, r: dict) -> str:
        s_scope = "diariamente" if scope == "daily" else "semanalmente"
        rtype = (r.get("type") or "").strip()

        if rtype == "category_count":
            cat = (r.get("category") or "").strip()
            cat_lc = cat.lower() if cat else ""
            op = self._op_text(r.get("op"))
            qty = str(r.get("quantity", ""))
            return f"Debería haber {s_scope} {op} {qty} {cat_lc} en el menú."

        if rtype == "item_count":
            cat = (r.get("category") or "").strip()
            cat_part = f" de {cat.lower()}" if cat else ""
            fname = (r.get("food_name") or "Todos").strip()
            op = self._op_text(r.get("op"))
            qty = str(r.get("quantity", ""))
            if fname.lower() == "todos":
                return f"Debería haber {s_scope} {op} {qty} elementos{cat_part}."
            return f"Debería haber {s_scope} {op} {qty} {fname}{cat_part} en el menú."

        if rtype == "forbid_allergen":
            aller = (r.get("allergen") or "").strip()
            suf = "en el día" if scope == "daily" else "en la semana"
            return f"No debe aparecer el alérgeno {aller} {suf}."

        if rtype == "do_not_repeat_consecutive_item":
            name = (r.get("name") or "").strip()
            return f"No repetir {name} en días consecutivos (semanal)."

        return f"Regla {rtype}"

    def _refresh_rules_view(self) -> None:
        data = self._rules_from_editor()

        self.ui.lstDailyRules.clear()
        for r in data.get("daily", []):
            self.ui.lstDailyRules.addItem(self._rule_to_text("daily", r))

        self.ui.lstWeeklyRules.clear()
        for r in data.get("weekly", []):
            self.ui.lstWeeklyRules.addItem(self._rule_to_text("weekly", r))

    # ---------- load/save ----------
    def _reload_text(self) -> None:
        rules = self.repo.load_rules()
        self._set_rules_text(rules)

    def _load_defaults(self) -> None:
        defaults = {
            "version": 1,
            "daily": [
                {
                    "type": "category_count",
                    "category": "Vegetales",
                    "op": "mayor o igual que",
                    "quantity": 2,
                },
                {
                    "type": "category_count",
                    "category": "Fruta",
                    "op": "mayor o igual que",
                    "quantity": 1,
                },
                {
                    "type": "category_count",
                    "category": "Proteína",
                    "op": "mayor o igual que",
                    "quantity": 1,
                },
                {
                    "type": "category_count",
                    "category": "Cereales",
                    "op": "menor o igual que",
                    "quantity": 2,
                },
                {
                    "type": "category_count",
                    "category": "Lácteos",
                    "op": "menor o igual que",
                    "quantity": 1,
                },
                {"type": "forbid_allergen", "allergen": "Gluten"},
            ],
            "weekly": [
                {
                    "type": "category_count",
                    "category": "Pescado",
                    "op": "mayor o igual que",
                    "quantity": 2,
                },
                {
                    "type": "category_count",
                    "category": "Legumbres",
                    "op": "mayor o igual que",
                    "quantity": 3,
                },
                {
                    "type": "category_count",
                    "category": "Fruta",
                    "op": "mayor o igual que",
                    "quantity": 7,
                },
                {
                    "type": "category_count",
                    "category": "Vegetales",
                    "op": "mayor o igual que",
                    "quantity": 10,
                },
                {
                    "type": "category_count",
                    "category": "Proteína",
                    "op": "menor o igual que",
                    "quantity": 14,
                },
            ],
        }
        self._set_rules_text(defaults)
        self._refresh_rules_view()

    def _save(self) -> None:
        try:
            # Antes de guardar, normalizamos operadores texto -> símbolo
            data = json.loads(self.ui.txtJson.toPlainText() or "{}")
            for scope in ("daily", "weekly"):
                lst = data.get(scope, [])
                if isinstance(lst, list):
                    for r in lst:
                        op = r.get("op")
                        if isinstance(op, str) and op.strip() in OP_WORD2SYMBOL_ES:
                            r["op"] = OP_WORD2SYMBOL_ES[op.strip()]
            self.repo.save_rules(data)
            QMessageBox.information(self, "Guardado", "Reglas guardadas.")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo guardar: {e}")

    # ---------- add rule ----------
    def _add_rule(self) -> None:
        scope = self.ui.cmbScope.currentData()  # "daily" | "weekly"
        rtype = self.ui.cmbType.currentData()
        rules = self._rules_from_editor()

        if rtype == "category_count":
            category = self.ui.cmbCategory.currentData() or ""
            op_text = self.ui.cmbOp.currentText().strip()
            qty = int(self.ui.spnQty.value())
            rule = {
                "type": "category_count",
                "category": category,
                "op": op_text,  # se normaliza al guardar
                "quantity": qty,
            }
            rules[scope].append(rule)

        elif rtype == "item_count":
            category = self.ui.cmbCategory.currentData() or ""
            food_name = self.ui.cmbFood.currentData() or "Todos"
            op_text = self.ui.cmbOp.currentText().strip()
            qty = int(self.ui.spnQty.value())
            rule = {
                "type": "item_count",
                "category": category or None,
                "food_name": food_name,
                "op": op_text,  # se normaliza al guardar
                "quantity": qty,
            }
            rules[scope].append(rule)

        elif rtype == "forbid_allergen":
            rule = {"type": "forbid_allergen", "allergen": "Gluten"}
            rules[scope].append(rule)

        elif rtype == "do_not_repeat_consecutive_item":
            food_name = self.ui.cmbFood.currentData() or ""
            if not food_name or food_name == "Todos":
                QMessageBox.information(
                    self, "Aviso", "Selecciona un alimento concreto para esta regla."
                )
                return
            rule = {"type": "do_not_repeat_consecutive_item", "name": food_name}
            if scope != "weekly":
                msg = (
                    "“No repetir en días consecutivos” se evalúa a nivel semanal; "
                    "se añadirá en Semanal."
                )
                QMessageBox.information(self, "Aviso", msg)
                rules["weekly"].append(rule)
            else:
                rules[scope].append(rule)

        else:
            QMessageBox.information(self, "Aviso", "Tipo de regla no soportado.")
            return

        self._set_rules_text(rules)
        self._refresh_rules_view()
        QMessageBox.information(self, "OK", "Regla añadida al JSON (no olvides Guardar).")

    # ---------- toggle ----------
    def _toggle_json(self) -> None:
        vis = self.ui.txtJson.isVisible()
        self.ui.txtJson.setVisible(not vis)
        self.ui.btnToggleJson.setText("Ocultar JSON" if not vis else "Ver JSON")
        if vis is True:
            self._refresh_rules_view()
