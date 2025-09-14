from __future__ import annotations

from datetime import date

from core.models import DayMeals, WeekMenu
from core.repository import Repo
from core.rules_engine import RulesEngine


def test_rules_engine_basic(tmp_path):
    repo = Repo(tmp_path)
    # semillas mínimas
    repo.save_foods([])
    repo.save_rules(
        {
            "daily": [
                {"type": "category_count", "category": "Vegetales", "op": ">=", "quantity": 1}
            ],
            "weekly": [],
        }
    )
    eng = RulesEngine(repo)
    dm = DayMeals(breakfast=[], midmorning=[], lunch=[], snack=[], dinner=[])
    v = eng.validate_day(dm)
    assert v, "Debe fallar por no tener Vegetales"

    # ahora añadimos una comida vegetal ficticia
    repo.save_foods(
        [
            {
                "id": "f1",
                "name": "Brócoli",
                "category": "Vegetales",
                "allergens": [],
                "labels": [],
                "active": True,
            }
        ]
    )
    eng = RulesEngine(repo)
    dm2 = DayMeals(breakfast=["f1"], midmorning=[], lunch=[], snack=[], dinner=[])
    v2 = eng.validate_day(dm2)
    assert not v2, f"No debería haber violaciones: {v2}"

    wm = WeekMenu(
        week_start=date(2024, 9, 9),
        days={
            k: dm2
            for k in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        },
    )
    vw = eng.validate_week(wm)
    assert not vw
