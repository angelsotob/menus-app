# 🥗 NutriPlan

**Rule-based desktop menu planning application built with Python and Qt (PySide6).**

NutriPlan is a modular desktop application designed to plan daily and weekly menus, manage food databases and validate nutritional constraints through a configurable rules engine.

It focuses on maintainability, clean architecture and production-ready structure.

---

## 🚀 Features

### 🗂 Food Database Management
- CRUD editor for foods
- Categories and allergens management
- Active / inactive filtering
- Search and category filters

### 📅 Menu Planning
- Daily planner
- Weekly planner
- Save / Load menus
- Profile-based configuration

### 📜 Recipes
- Create and manage recipes
- Recipes expand into ingredients during validation
- Integrated with menu planning system

### ⚖️ Rule-Based Validation Engine
- Daily and weekly rules
- Category count rules
- Item count rules
- Allergen restrictions
- No-repeat consecutive item rule
- Natural-language validation messages

### 📤 Export
- Export menus to PDF (A4 auto-scaled)
- Export to PNG/JPEG images
- Atomic file writes with automatic backups

---

## 🧠 Architecture Overview

The project follows a layered structure:

```
src/
 ├── core/          # Domain logic (models, repository, rules engine)
 ├── widgets/       # Qt UI controllers
 ├── ui/            # Qt Designer .ui files
 ├── theme.py       # UI styling
 └── main_window.py # Application entry UI wrapper
```

### Core Principles

- Separation of concerns (UI / domain / persistence)
- Pydantic-based domain models
- Atomic JSON persistence with backup system
- Profile isolation
- Extensible rules engine
- Versioned releases with structured CHANGELOG

---

## 🏗 Technical Stack

- Python 3.12+
- PySide6 (Qt for Python)
- Pydantic (data validation)
- JSON-based persistence layer
- Pytest (unit testing)

---

## 📦 Installation

Clone the repository:

```bash
git clone https://github.com/<your-user>/menus-app.git
cd menus-app
```

Create virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python app.py
```

---

## 👤 Profiles

NutriPlan supports isolated user profiles.

Each profile maintains:
- Foods database
- Recipes
- Rules
- Menus
- Backups

The active profile is stored internally and can be switched from Preferences.

---

## 📂 Data Storage

Data is stored in a local directory resolved in this order:

1. `MENUSAPP_DATA_DIR` environment variable
2. `./MenusApp` (if exists)
3. `~/MenusApp`

All writes are atomic and previous versions are automatically backed up.

---

## 🧪 Testing

Run tests with:

```bash
pytest
```

The test suite covers:
- Repository layer
- Rules engine logic
- Configuration handling

---

## 🛠 Roadmap

- Improved UX refinements
- Packaging for standalone distribution
- Enhanced reporting
- Additional validation rule types
- Documentation expansion

---

## 📄 License

See `LICENSE.md` for details.

---

## 👨‍💻 Author

Ángel Soto  
Embedded Systems Engineer  

This project reflects a modular and maintainable approach to software architecture, applied to a real-world desktop application.
