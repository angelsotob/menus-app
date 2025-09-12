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

## [5.0.0] - 2025-09-12
### Added
- Full translation of the application to English (UI texts, models, configuration files).
- Consistent use of internal category keys (English) with localized display names.
- Updated file naming conventions (`foods.json`, `categories.json`, etc.) for clarity.

### Changed
- All code, comments, and documentation migrated from Spanish to English.
- Category handling refactored to avoid duplication between internal keys and display values.
- Improved consistency in profile-aware menu saving/export.

### Fixed
- Resolved duplication issue where categories appeared in both Spanish and English in the food dialog.
- Fixed atomic write function for JSON files on Unix systems.

---

## [0.4.2] - 2025-09-11
### Added
- Profile system with live switching (Preferences): select/create profile; data directory is profile-scoped.
- Day/Week save & export filenames include active profile tag (`menu_day_{profile}_{YYYYMMDD}`, `menu_week_{profile}_{YYYYMMDD}`).
- Default save locations: `/templates/` for JSON, `/outputs/` for PDF/PNG (auto-created).

### Changed
- DB Editor: real header sorting via `QSortFilterProxyModel`.
- Status bar notifications after CRUD actions.

### Fixed
- Category editor now persists `categories.json` and propagates renames to existing foods; removes orphan categories from per-meal suggestions.

---

## [0.4.1] - 2025-09-10
### Added
- Categories editor (global + per-meal) with persistence in `categories.json`.
- Integration with FoodDialog/DbEditor and planners (Day/Week) reading mappings from repo.

### Changed
- Automatic remapping of foods when renaming/deleting categories.
- Default export routes to `/outputs/` and templates to `/templates/`.

### Fixed
- Real sorting in the table (proxy model).

---

## [0.4.0] - 2025-09-09
### Added
- **Week planner**:
  - Tabs M–S with one `DayEditor` per day.
  - Save/Load week in **`/templates/`** as JSON (`menu_week_YYYYMMDD.json`, using Monday as reference).
  - Export **PDF/Image** to **`/outputs/`** (`menu_week_YYYYMMDD.*`).
  - Weekly print view with **fixed column width** and **word-wrap**.
- Designer warnings silenced in `week_planner.ui` using `QTabWidget::North` and `Qt::Horizontal`.

### Changed
- Daily and weekly export: default filenames with **date** (`YYYYMMDD`).

### Fixed
- Ensure creation of default folders (`/templates/`, `/outputs/`) if they don’t exist.

---

## [0.3.0] - 2025-09-08
### Added
- **Day planner**:
  - 5 meals: Breakfast, Midmorning, Lunch, Snack, and Dinner.
  - Food selection by **suggested categories**.
  - Save/Load day in JSON (initially in chosen path).
  - Export day to **PDF/Image**.
  - Daily print view with **fixed column width** and **word-wrap**.
- Default filenames with date (`menu_day_YYYYMMDD.*`).

### Fixed
- Correct item labeling (show **name** instead of **ID**).
- JSON serialization compatible (dates → ISO).

---

## [0.2.0] - 2025-09-06
### Added
- **Database Editor** (GUI):
  - Table with filters (text, category, show inactive), sorting, and context menu.
  - Create/Edit/Delete, activate/deactivate (soft delete).
  - **Allergens editor** (editable list).
  - **Preferences dialog** (theme, data folder — basic).
- Themes: **dark by default**, optional light theme.

### Changed
- UI structure with `QUiLoader` and dynamic loading from `/src/ui`.

---

## [0.1.0] - 2025-09-05
### Added
- **Phase 0 (bootstrap)**:
  - Base models (`Food`, `DayMeals`, `DayMenu`, `WeekMenu`).
  - JSON repository (`Repo`) with atomic read/write.
  - Default seeds (`foods.json`, `allergens.json`, `rules.json`).
  - Startup and initial verification script.

---

## License
This project is licensed under **CC BY-NC 4.0**.

[Unreleased]: https://github.com/owner/repo/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/owner/repo/compare/v0.4.2...v0.5.0
[0.4.2]: https://github.com/owner/repo/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/OWNER/REPO/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/angelsotob/menus-app/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/angelsotob/menus-app/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/angelsotob/menus-app/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/angelsotob/menus-app/releases/tag/v0.1.0