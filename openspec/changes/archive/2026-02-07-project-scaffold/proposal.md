## Why

The project has complete documentation (requirements, technical design, coding standards) but zero code. Before any feature work can begin, the monorepo structure, package configuration, environment setup, and CI pipeline must exist. This is Phase 1 of the 8-phase build order.

## What Changes

- Create `python/` directory with DDD layer structure (`domain/`, `app/`, `infra/`)
- Create `python/source/interactive_books/` package with `__init__.py` and `main.py` entry point
- Create `python/tests/` directory mirroring source structure
- Create `python/pyproject.toml` with all dependencies (typer, pydantic-settings, httpx, pytest, ruff, pyright)
- Create `python/.envrc.example` and `python/.env.example` (both committed; `.envrc` and `.env` gitignored)
- Create `shared/` directory with subdirectories for schema, prompts, and fixtures
- Create `swift/` placeholder directory for Phase 8
- Create `.github/workflows/ci.yml` with Python lint, type check, and test jobs
- Create root `.gitignore` covering Python, Swift, and environment files

## Capabilities

### New Capabilities

- `python-package`: Python CLI package structure — pyproject.toml, source layout, entry point, dependency management with uv
- `ddd-layers`: DDD directory skeleton for both Python and Swift — domain, app, infra layers with correct dependency direction
- `dev-environment`: Developer environment setup — direnv, .env.example, environment variable loading via pydantic-settings
- `ci-pipeline`: GitHub Actions CI — lint (ruff), type check (pyright), test (pytest) on push and PR

### Modified Capabilities

None — this is the first change, no existing specs.

## Impact

- **New directories**: `python/`, `swift/`, `shared/`, `.github/`
- **New config files**: `pyproject.toml`, `.envrc`, `.env.example`, `.gitignore`, `ci.yml`
- **Dependencies**: uv must be available to install Python packages
- **No application logic** — this change creates structure only, no functional code
