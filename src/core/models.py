from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, field_validator


class Food(BaseModel):
    id: str
    name: str
    # Note: it used to be Literal[...] (static). Now it is str to allow dynamic categories.
    category: str
    allergens: list[str] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    notes: str | None = None
    active: bool = True

    @field_validator("name", "category")
    @classmethod
    def _strip_text(cls, v: str) -> str:
        return v.strip()

    @field_validator("allergens", "labels")
    @classmethod
    def _normalize_list(cls, v: list[str]) -> list[str]:
        return [s.strip() for s in v if s and s.strip()]


class DayMeals(BaseModel):
    breakfast: list[str] = Field(default_factory=list)
    midmorning: list[str] = Field(default_factory=list)
    lunch: list[str] = Field(default_factory=list)
    snack: list[str] = Field(default_factory=list)
    dinner: list[str] = Field(default_factory=list)


class DayMenu(BaseModel):
    date: date
    meals: DayMeals


class WeekMenu(BaseModel):
    week_start: date  # monday
    # keys: "monday","tuesday","wednesday","thursday","friday","saturday","sunday"
    days: dict[str, DayMeals]

    @field_validator("week_start")
    @classmethod
    def _monday_required(cls, d: date) -> date:
        # 0 is Monday
        if d.weekday() != 0:
            raise ValueError("week_start must be monday")
        return d

    @field_validator("days")
    @classmethod
    def _keys_required(cls, d: dict[str, DayMeals]) -> dict[str, DayMeals]:
        expected = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        missing = [k for k in expected if k not in d]
        if missing:
            raise ValueError(f"days missing: {', '.join(missing)}")
        return d
