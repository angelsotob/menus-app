from __future__ import annotations

from pathlib import Path

from core.models import Food
from core.repository import Repo


def test_repo_roundtrip(tmp_path: Path) -> None:
    repo = Repo(tmp_path)
    foods = [
        Food(
            id="f1",
            name="Pollo",
            category="Protein",
            allergens=[],
            labels=[],
            active=True,
        ),
        Food(
            id="f2",
            name="Manzana",
            category="Fruit",
            allergens=[],
            labels=[],
            active=True,
        ),
    ]
    repo.save_foods(foods)
    loaded = repo.list_foods()
    assert len(loaded) == 2
    assert loaded[0].name == "Pollo"


def test_allergens_empty_ok(tmp_path: Path) -> None:
    repo = Repo(tmp_path)
    repo.save_allergens([])
    assert repo.list_allergens() == []
