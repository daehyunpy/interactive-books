## ADDED Requirements

### Requirement: Python package uses src layout
The Python CLI package SHALL be located at `python/source/interactive_books/` using the src layout convention with `source/` as the directory name.

#### Scenario: Package is importable after install
- **WHEN** a developer runs `uv sync` from `python/`
- **THEN** `import interactive_books` succeeds in Python

#### Scenario: Package is not importable without install
- **WHEN** a developer runs Python from the `python/` directory without installing
- **THEN** `import interactive_books` fails (src layout prevents accidental imports)

### Requirement: pyproject.toml defines all metadata and dependencies
The `python/pyproject.toml` SHALL define the package name (`interactive-books`), Python version (`>=3.13`), and all runtime dependencies (typer, pydantic-settings, httpx).

#### Scenario: Runtime dependencies are installable
- **WHEN** a developer runs `uv sync` from `python/`
- **THEN** typer, pydantic-settings, and httpx are installed

### Requirement: Development dependencies are in a dependency group
Development tools (pytest, ruff, pyright) SHALL be defined in a `[dependency-groups]` dev group, not as runtime dependencies.

#### Scenario: Dev dependencies are installable
- **WHEN** a developer runs `uv sync` from `python/`
- **THEN** pytest, ruff, and pyright are available

#### Scenario: Dev dependencies are not shipped with the package
- **WHEN** the package is built for distribution
- **THEN** pytest, ruff, and pyright are not included as requirements

### Requirement: CLI entry point is defined
The `pyproject.toml` SHALL define a `[project.scripts]` entry point named `cli` pointing to `interactive_books.main:app`.

#### Scenario: CLI is runnable
- **WHEN** a developer runs `uv run cli` from `python/`
- **THEN** the typer app starts without errors

### Requirement: Package uses namespace packages (no __init__.py)
The `python/source/interactive_books/` directory SHALL NOT contain empty `__init__.py` files. The package SHALL use implicit namespace packages (PEP 420). Hatchling handles package discovery via `[tool.hatch.build.targets.wheel]`.

#### Scenario: Package is discoverable without __init__.py
- **WHEN** a developer runs `uv sync` from `python/`
- **THEN** `import interactive_books.main` succeeds without `__init__.py`

### Requirement: Entry point main.py creates a typer app
The `python/source/interactive_books/main.py` SHALL create a `typer.Typer()` app instance. It MAY include a placeholder `--version` flag.

#### Scenario: main.py is importable
- **WHEN** a developer imports `interactive_books.main`
- **THEN** an `app` attribute of type `typer.Typer` exists
