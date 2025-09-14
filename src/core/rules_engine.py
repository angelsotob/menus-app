from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.i18n import (
    OP_SYMBOL2LONGWORD_ES,
    OP_SYMBOL2WORD_ES,
    OP_WORD2SYMBOL_ES,
    RULE_TITLE_ES,
)
from core.models import DayMeals, DayMenu, WeekMenu
from core.repository import Repo


@dataclass
class Violation:
    scope: str  # "daily" | "weekly"
    rule_type: str  # "category_count" | "item_count" | "forbid_allergen" | ...
    payload: dict[str, Any]


def _map_op_to_symbol(op: str) -> str:
    """Acepta símbolo (>=, >, …) o texto en ES (“al menos”, “mayor que”, …) y devuelve símbolo."""
    if not isinstance(op, str):
        return ">="
    raw = op.strip()
    return OP_WORD2SYMBOL_ES.get(raw, raw)  # si ya es símbolo, lo deja igual


class RulesEngine:
    def __init__(self, repo: Repo) -> None:
        self.repo = repo

    # ---- helpers ----
    def _foods_by_id(self) -> dict[str, Any]:
        return {f.id: f for f in self.repo.list_foods()}

    def _count_category_in_day(self, meals: DayMeals, category_es: str) -> int:
        """Cuenta cuántos alimentos del día pertenecen a la categoría dada (ES)."""
        foods_by_id = self._foods_by_id()
        total = 0
        for ids in [meals.breakfast, meals.midmorning, meals.lunch, meals.snack, meals.dinner]:
            for fid in ids:
                f = foods_by_id.get(fid)
                if f and f.category == category_es:
                    total += 1
        return total

    def _count_item_in_day(
        self, meals: DayMeals, *, category_es: str | None, food_name: str | None
    ) -> int:
        """
        Cuenta apariciones de un alimento por nombre (case-insensitive).
        Si 'food_name' es "Todos" o "*", cuenta cualquiera.
        Si se da 'category_es', restringe a esa categoría (ES).
        """
        foods_by_id = self._foods_by_id()
        target_all = False
        if food_name:
            low = food_name.strip().lower()
            target_all = (low == "todos") or (low == "*")
        total = 0
        for ids in [meals.breakfast, meals.midmorning, meals.lunch, meals.snack, meals.dinner]:
            for fid in ids:
                f = foods_by_id.get(fid)
                if not f:
                    continue
                if category_es and f.category != category_es:
                    continue
                if target_all:
                    total += 1
                else:
                    if food_name and f.name.strip().lower() == food_name.strip().lower():
                        total += 1
        return total

    # ---- validators ----
    def validate_day(self, day: DayMenu, rules: dict | None = None) -> list[Violation]:
        if rules is None:
            rules = self.repo.load_rules()
        violations: list[Violation] = []

        for r in rules.get("daily", []):
            rtype = r.get("type")

            if rtype == "category_count":
                cat_es = r.get("category", "")
                op = _map_op_to_symbol(r.get("op", ">="))
                qty = int(r.get("quantity", 0))
                found = self._count_category_in_day(day.meals, cat_es)
                ok = _apply_op(found, op, qty)
                if not ok:
                    violations.append(
                        Violation(
                            scope="daily",
                            rule_type="category_count",
                            payload={
                                "category_es": cat_es,
                                "op": op,
                                "op_word_es": OP_SYMBOL2WORD_ES.get(op, op),
                                "op_long_es": OP_SYMBOL2LONGWORD_ES.get(op, op),
                                "quantity": qty,
                                "found": found,
                                "userland": r.get("userland"),
                                "title_es": RULE_TITLE_ES["category_count"],
                            },
                        )
                    )

            elif rtype == "item_count":
                cat_es = (r.get("category") or "").strip() or None
                food_name = (r.get("food_name") or "").strip() or None
                op = _map_op_to_symbol(r.get("op", ">="))
                qty = int(r.get("quantity", 0))
                found = self._count_item_in_day(day.meals, category_es=cat_es, food_name=food_name)
                ok = _apply_op(found, op, qty)
                if not ok:
                    violations.append(
                        Violation(
                            scope="daily",
                            rule_type="item_count",
                            payload={
                                "category_es": cat_es or "",
                                "food_name": food_name or "Todos",
                                "op": op,
                                "op_word_es": OP_SYMBOL2WORD_ES.get(op, op),
                                "op_long_es": OP_SYMBOL2LONGWORD_ES.get(op, op),
                                "quantity": qty,
                                "found": found,
                                "userland": r.get("userland"),
                                "title_es": RULE_TITLE_ES["item_count"],
                            },
                        )
                    )

            elif rtype == "forbid_allergen":
                # (Pendiente: comprobar alérgenos reales por alimento)
                pass

            else:
                pass

        return violations

    def validate_week(self, week: WeekMenu, rules: dict | None = None) -> list[Violation]:
        if rules is None:
            rules = self.repo.load_rules()
        violations: list[Violation] = []

        for r in rules.get("weekly", []):
            rtype = r.get("type")

            if rtype == "category_count":
                cat_es = r.get("category", "")
                op = _map_op_to_symbol(r.get("op", ">="))
                qty = int(r.get("quantity", 0))
                total_found = 0
                for d in week.days.values():
                    total_found += self._count_category_in_day(d, cat_es)
                ok = _apply_op(total_found, op, qty)
                if not ok:
                    violations.append(
                        Violation(
                            scope="weekly",
                            rule_type="category_count",
                            payload={
                                "category_es": cat_es,
                                "op": op,
                                "op_word_es": OP_SYMBOL2WORD_ES.get(op, op),
                                "op_long_es": OP_SYMBOL2LONGWORD_ES.get(op, op),
                                "quantity": qty,
                                "found": total_found,
                                "userland": r.get("userland"),
                                "title_es": RULE_TITLE_ES["category_count"],
                            },
                        )
                    )

            elif rtype == "item_count":
                cat_es = (r.get("category") or "").strip() or None
                food_name = (r.get("food_name") or "").strip() or None
                op = _map_op_to_symbol(r.get("op", ">="))
                qty = int(r.get("quantity", 0))
                total_found = 0
                for d in week.days.values():
                    total_found += self._count_item_in_day(
                        d, category_es=cat_es, food_name=food_name
                    )
                ok = _apply_op(total_found, op, qty)
                if not ok:
                    violations.append(
                        Violation(
                            scope="weekly",
                            rule_type="item_count",
                            payload={
                                "category_es": cat_es or "",
                                "food_name": food_name or "Todos",
                                "op": op,
                                "op_word_es": OP_SYMBOL2WORD_ES.get(op, op),
                                "op_long_es": OP_SYMBOL2LONGWORD_ES.get(op, op),
                                "quantity": qty,
                                "found": total_found,
                                "userland": r.get("userland"),
                                "title_es": RULE_TITLE_ES["item_count"],
                            },
                        )
                    )

            elif rtype == "do_not_repeat_consecutive_item":
                target = (r.get("name") or "").strip().lower()
                if not target:
                    continue
                order = [
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                    "sunday",
                ]
                foods_by_id = self._foods_by_id()

                def day_has_target(d: DayMeals) -> bool:
                    for ids in [d.breakfast, d.midmorning, d.lunch, d.snack, d.dinner]:
                        for fid in ids:
                            f = foods_by_id.get(fid)
                            if f and f.name.strip().lower() == target:
                                return True
                    return False

                prev_key = None
                prev_yes = False
                for k in order:
                    d = week.days.get(k)
                    if not d:
                        prev_key = k
                        prev_yes = False
                        continue
                    cur_yes = day_has_target(d)
                    if prev_yes and cur_yes:
                        violations.append(
                            Violation(
                                scope="weekly",
                                rule_type="do_not_repeat_consecutive_item",
                                payload={
                                    "name": r.get("name"),
                                    "prev_day": k if prev_key is None else prev_key,
                                    "day": k,
                                    "userland": r.get("userland"),
                                    "title_es": RULE_TITLE_ES["do_not_repeat_consecutive_item"],
                                },
                            )
                        )
                    prev_yes = cur_yes
                    prev_key = k

            else:
                pass

        return violations


def format_violations(violations: list[Violation], userland_fallback: bool = True) -> str:
    out: list[str] = []
    for v in violations:
        p = v.payload
        userland = (p.get("userland") or "").strip()
        if userland:
            line = userland.format(
                category=p.get("category_es", ""),
                op=p.get("op", ""),
                op_word=p.get("op_word_es", ""),
                quantity=p.get("quantity", ""),
                found=p.get("found", ""),
                allergen=p.get("allergen", ""),
                name=p.get("name", ""),
                scope=v.scope,
                rule=v.rule_type,
                title=p.get("title_es", ""),
                food_name=p.get("food_name", ""),
            )
            out.append(f"• {line}")
            continue

        if v.rule_type == "category_count":
            line = (
                f"• {v.scope.capitalize()}: {p.get('title_es')} — "
                f"“{p.get('category_es')}” {p.get('op_word_es')} {p.get('quantity')} "
                f"(encontrado: {p.get('found')})."
            )
            out.append(line)
        elif v.rule_type == "item_count":
            cat_part = f" en “{p.get('category_es')}”" if p.get("category_es") else ""
            line = (
                f"• {v.scope.capitalize()}: {p.get('title_es')} — "
                f"“{p.get('food_name')}”{cat_part} {p.get('op_word_es')} {p.get('quantity')} "
                f"(encontrado: {p.get('found')})."
            )
            out.append(line)
        elif v.rule_type == "do_not_repeat_consecutive_item":
            line = (
                f"• {v.scope.capitalize()}: {p.get('title_es')} — "
                f"No repetir “{p.get('name')}” en días consecutivos — "
                f"detectado entre {p.get('prev_day')} y {p.get('day')}."
            )
            out.append(line)
        else:
            out.append(f"• {v.scope.capitalize()}: {v.rule_type}")
    return "\n".join(out)


def _apply_op(found: int, op: str, qty: int) -> bool:
    if op == ">=":
        return found >= qty
    if op == ">":
        return found > qty
    if op == "==":
        return found == qty
    if op == "<=":
        return found <= qty
    if op == "<":
        return found < qty
    if op == "!=":
        return found != qty
    return True
