## Context

The project has complete documentation but no code. The directory layout is defined in `docs/technical_design.md` → "Directory Layout". Coding standards (DDD, TDD, Clean Code) are in `AGENTS.md`. The Python CLI is built first (Phases 1–7), then the Swift app (Phase 8).

This design covers Phase 1 only: creating the monorepo skeleton so subsequent phases have a place to write code.

## Goals / Non-Goals

**Goals:**
- Establish the `python/`, `swift/`, `shared/` monorepo structure
- Configure uv + pyproject.toml so `uv sync` and `uv run pytest` work from day one
- Set up direnv + pydantic-settings for environment variable management
- Create a CI pipeline that runs lint, type check, and tests on every push/PR
- Ensure the DDD layer directories exist with correct structure

**Non-Goals:**
- No application logic, domain models, or business rules (Phase 2+)
- No database schema or migrations (Phase 2)
- No actual CLI commands (Phase 3+)
- No Swift code or Xcode project (Phase 8)
- No prompt templates or test fixtures content (later phases)

## Decisions

### 1. Python `source/` layout over flat layout

Use `python/source/interactive_books/` (src layout) rather than `python/interactive_books/`.

**Why:** Prevents accidentally importing the package from the project root without installing it. uv and pip handle src layouts natively. The project uses `source/` instead of the conventional `src/` per team preference.

**Alternative:** Flat layout (`python/interactive_books/`). Simpler, but allows broken imports to silently succeed during development.

### 2. Single `pyproject.toml` with dependency groups

All dependencies in one `pyproject.toml` using dependency groups:
- Default: runtime deps (typer, pydantic-settings, httpx)
- `[dependency-groups]` dev: development deps (pytest, ruff, pyright)

**Why:** uv supports dependency groups natively. Keeps one file, avoids separate requirements files. Dev deps don't ship with the package.

**Alternative:** Separate `requirements-dev.txt`. More files to maintain, no clear benefit with uv.

### 3. `.envrc` and `.env` are both gitignored

Neither `.envrc` nor `.env` are committed. Instead:
- `.envrc.example` shows the direnv setup (committed)
- `.env.example` documents required variables (committed)
- Developer copies both, fills in values, runs `direnv allow`
- pydantic-settings validates at runtime

**Why:** `.envrc` is personal config — some developers may customize it. Keeping it gitignored avoids `direnv allow` prompts on every pull and keeps all environment files consistently gitignored.

### 4. CI runs from `python/` working directory

GitHub Actions `ci.yml` sets `working-directory: python/` for all steps. Tests, lint, and type check all run relative to `python/`.

**Why:** The monorepo has multiple codebases. CI must scope to the right directory. Later, a Swift CI job will run from `swift/`.

### 5. `shared/` directories created with `.gitkeep`

Empty directories (`shared/schema/`, `shared/prompts/`, `shared/fixtures/`) use `.gitkeep` files since git doesn't track empty directories.

**Why:** The directories need to exist in the repo so the cross-platform contract structure is visible from Phase 1. Content arrives in later phases.

### 6. `swift/` is a placeholder only

Create `swift/.gitkeep` — no Xcode project, no Swift files. The Swift app is Phase 8.

**Why:** Establishing the top-level structure now avoids reorganization later. But creating an Xcode project now would be premature and would need rebuilding when Phase 8 starts.

## Risks / Trade-offs

- **pyproject.toml dependencies may need version updates by Phase 2+** → Pin minimum versions only (`>=`), not exact versions. uv lockfile handles reproducibility.
- **CI may be slow if uv cache isn't warm** → Use `astral-sh/setup-uv` action with GitHub Actions cache.
- **`.envrc` requires direnv to be installed** → Documented as prerequisite in AGENTS.md. Fallback: `eval "$(direnv export zsh)"` or manual `source .env`.
