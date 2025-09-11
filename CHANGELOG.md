# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- (placeholder) …

### Changed
- (placeholder) …

### Fixed
- (placeholder) …

---

## [0.4.2] - 2025-09-11
### Added
- Profile system with live switching (Preferences): select/create profile; data directory is profile-scoped.
- Day/Week save & export filenames include active profile tag (`menu_dia_{profile}_{YYYYMMDD}`, `menu_semana_{profile}_{YYYYMMDD}`).
- Default save locations: `/templates/` for JSON, `/outputs/` for PDF/PNG (auto-created).

### Changed
- DB Editor: real header sorting via `QSortFilterProxyModel`.
- Status bar notifications after CRUD actions.

### Fixed
- Category editor now persists `categorias.json` and propagates renames to existing foods; removes orphan categories from per-meal suggestions.

---

## [0.4.1] - 2025-09-10
### Added
- Categories editor (global + per-meal) con persistencia en `categorias.json`.
- Integración con FoodDialog/DbEditor y planners (Day/Week) leyendo mapeos desde repo.

### Changed
- Remapeo automático de alimentos al renombrar/borrar categorías.
- Export routes por defecto a `/outputs/` y plantillas a `/templates/`.

### Fixed
- Ordenación real en la tabla (proxy model).

---

## [0.4.0] - 2025-09-09
### Added
- **Week planner (Planificador semanal)**:
  - Pestañas L–D con un `DayEditor` por día.
  - Guardar/Cargar semana en **`/templates/`** como JSON (`menu_semana_YYYYMMDD.json`, usando el lunes como referencia).
  - Exportar **PDF/Imagen** a **`/outputs/`** (`menu_semana_YYYYMMDD.*`).
  - Vista de impresión semanal con **ancho de columna fijo** y **word-wrap**.
- Silenciados avisos de Designer en `week_planner.ui` usando `QTabWidget::North` y `Qt::Horizontal`.

### Changed
- Export diario y semanal: nombres por defecto con **fecha** (`YYYYMMDD`).

### Fixed
- Asegurar creación de carpetas por defecto (`/templates/`, `/outputs/`) si no existen.

---

## [0.3.0] - 2025-09-08
### Added
- **Day planner (Planificador diario)**:
  - 5 comidas: Desayuno, Media mañana, Comida, Merienda y Cena.
  - Selección de alimentos por **categorías sugeridas**.
  - Guardar/Cargar día en JSON (inicialmente en ruta elegida).
  - Exportar día a **PDF/Imagen**.
  - Vista de impresión diaria con **ancho fijo** de columna y **word-wrap**.
- Nombres por defecto con fecha (`menu_dia_YYYYMMDD.*`).

### Fixed
- Etiquetado correcto de items (mostrar **nombre** y no el **ID**).
- Serialización JSON compatible (fechas → ISO).

---

## [0.2.0] - 2025-09-06
### Added
- **Editor de Base de Datos** (GUI):
  - Tabla con filtros (texto, categoría, mostrar inactivos), ordenación y menú contextual.
  - Altas/ediciones/bajas, activar/desactivar (soft delete).
  - Editor de **alérgenos** (lista editable).
  - Diálogo de **preferencias** (tema, carpeta datos — básico).
- Temas: **oscuro por defecto**, opción de claro.

### Changed
- Estructura de UI con `QUiLoader` y carga dinámica desde `/src/ui`.

---

## [0.1.0] - 2025-09-05
### Added
- **Fase 0 (bootstrap)**:
  - Modelos base (`Food`, `DayMeals`, `DayMenu`, `WeekMenu`).
  - Repositorio JSON (`Repo`) con lectura/escritura atómica.
  - Semillas por defecto (`alimentos.json`, `alergenos.json`, `reglas.json`).
  - Script de arranque y verificación inicial.

---

## License
This project is licensed under **CC BY-NC 4.0**.

[Unreleased]: https://github.com/owner/repo/compare/v0.4.2...HEAD
[0.4.2]: https://github.com/owner/repo/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/OWNER/REPO/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/angelsotob/menus-app/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/angelsotob/menus-app/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/angelsotob/menus-app/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/angelsotob/menus-app/releases/tag/v0.1.0