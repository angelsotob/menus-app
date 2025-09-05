from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Categoria = Literal[
    "proteina",
    "verdura",
    "fruta",
    "cereal_harina",
    "legumbre",
    "pescado",
    "marisco",
    "huevo",
    "lacteo",
    "frutos_secos",
    "grasa",
    "otros",
]


class Food(BaseModel):
    id: str
    nombre: str
    categoria: Categoria
    alergenos: list[str] = Field(default_factory=list)
    etiquetas: list[str] = Field(default_factory=list)
    notas: str | None = None
    activo: bool = True


class DayMeals(BaseModel):
    desayuno: list[str] = Field(default_factory=list)
    media_manana: list[str] = Field(default_factory=list)
    comida: list[str] = Field(default_factory=list)
    merienda: list[str] = Field(default_factory=list)
    cena: list[str] = Field(default_factory=list)


class DayMenu(BaseModel):
    fecha: date
    comidas: DayMeals


class WeekMenu(BaseModel):
    semana_inicio: date  # lunes
    # keys: "lunes","martes","miercoles","jueves","viernes","sabado","domingo"
    dias: dict[str, DayMeals]

    @field_validator("semana_inicio")
    @classmethod
    def _monday_required(cls, v: date) -> date:
        if v.weekday() != 0:  # 0=lunes
            raise ValueError("semana_inicio debe ser lunes")
        return v

    @field_validator("dias")
    @classmethod
    def _keys_required(cls, d: dict[str, DayMeals]) -> dict[str, DayMeals]:
        expected = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
        missing = [k for k in expected if k not in d]
        if missing:
            raise ValueError(f"faltan días en la semana: {missing}")
        return d
