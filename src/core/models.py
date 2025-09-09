from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, field_validator


class Food(BaseModel):
    id: str
    nombre: str
    # Nota: antes era Literal[...] (estático). Ahora es str para permitir categorías dinámicas.
    categoria: str
    alergenos: list[str] = Field(default_factory=list)
    etiquetas: list[str] = Field(default_factory=list)
    notas: str | None = None
    activo: bool = True

    @field_validator("nombre", "categoria")
    @classmethod
    def _strip_text(cls, v: str) -> str:
        return v.strip()

    @field_validator("alergenos", "etiquetas")
    @classmethod
    def _normalize_list(cls, v: list[str]) -> list[str]:
        return [s.strip() for s in v if s and s.strip()]


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
    def _monday_required(cls, d: date) -> date:
        # 0 = Monday
        if d.weekday() != 0:
            raise ValueError("semana_inicio debe ser lunes")
        return d

    @field_validator("dias")
    @classmethod
    def _keys_required(cls, d: dict[str, DayMeals]) -> dict[str, DayMeals]:
        expected = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
        missing = [k for k in expected if k not in d]
        if missing:
            raise ValueError(f"faltan días: {', '.join(missing)}")
        return d
