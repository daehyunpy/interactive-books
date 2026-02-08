## 1. Root Configuration

- [x] 1.1 Create root `.gitignore` covering Python (`__pycache__/`, `*.pyc`, `.venv/`), Swift (`*.xcodeproj/xcuserdata/`, `build/`), environment (`.env`, `.envrc`), macOS (`.DS_Store`), and uv (`.uv/`)
- [x] 1.2 Create `.github/workflows/ci.yml` — triggers on push to `main`/`develop` and PRs to `main`/`develop`, uses Python 3.13, `astral-sh/setup-uv`, runs `uv sync`, `ruff check .`, `pyright`, `pytest -x` from `python/`

## 2. Shared and Swift Placeholders

- [x] 2.1 Create `shared/schema/`, `shared/prompts/`, `shared/fixtures/` each with `.gitkeep`
- [x] 2.2 Create `swift/` with `.gitkeep` (placeholder only, no Swift code)

## 3. Python Package Structure

- [x] 3.1 Create `python/pyproject.toml` — package name `interactive-books`, Python `>=3.13`, runtime deps (typer, pydantic-settings, httpx), dev group (pytest, ruff, pyright), `[project.scripts]` entry `cli = "interactive_books.main:app"`, src layout with `source/` as source dir
- [x] 3.2 Create `python/source/interactive_books/main.py` — `typer.Typer()` app with optional `--version` flag
- [x] 3.3 Create DDD layer directories: `python/source/interactive_books/domain/`, `app/`, `infra/` each with `__init__.py`

## 4. Test Structure

- [x] 4.1 Create `python/tests/conftest.py` (minimal)
- [x] 4.2 Create test layer directories: `python/tests/domain/`, `app/`, `infra/` each with `__init__.py`

## 5. Developer Environment

- [x] 5.1 Create `python/.env.example` listing `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `OLLAMA_BASE_URL` with placeholder values and descriptions
- [x] 5.2 Create `python/.envrc.example` with direnv config (`dotenv`)
- [x] 5.3 Create settings module `python/source/interactive_books/infra/settings.py` using pydantic-settings — `ANTHROPIC_API_KEY` required, `OPENAI_API_KEY` and `OLLAMA_BASE_URL` optional with `None` defaults

## 6. Verification

- [x] 6.1 Run `uv sync` from `python/` — confirm dependencies install
- [x] 6.2 Run `uv run cli --help` — confirm typer app starts
- [x] 6.3 Run `uv run ruff check .` from `python/` — confirm no lint errors
- [x] 6.4 Run `uv run pyright` from `python/` — confirm no type errors
- [x] 6.5 Run `uv run pytest -x` from `python/` — confirm tests pass (smoke test added)
