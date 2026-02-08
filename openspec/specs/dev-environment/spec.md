## ADDED Requirements

### Requirement: .env.example documents all environment variables
The `python/.env.example` SHALL list all environment variables with placeholder values: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `OLLAMA_BASE_URL`.

#### Scenario: Developer knows which variables to set
- **WHEN** a developer reads `python/.env.example`
- **THEN** they see all required and optional variables with descriptions

### Requirement: .envrc.example shows direnv setup
The `python/.envrc.example` SHALL contain the direnv configuration for loading `.env` (e.g., `dotenv`).

#### Scenario: Developer can set up direnv
- **WHEN** a developer copies `.envrc.example` to `.envrc` and runs `direnv allow`
- **THEN** environment variables from `.env` are loaded into their shell

### Requirement: .envrc and .env are gitignored
The `.gitignore` SHALL include `.envrc` and `.env` patterns so that actual environment files are never committed.

#### Scenario: Secrets are not committed
- **WHEN** a developer creates `.env` with API keys
- **THEN** `git status` does not show `.env` as an untracked file

### Requirement: pydantic-settings validates environment at runtime
The project SHALL include a settings module using pydantic-settings that validates environment variables at import time. Missing required variables SHALL raise a clear error.

#### Scenario: Missing API key produces actionable error
- **WHEN** a developer runs the CLI without `ANTHROPIC_API_KEY` set
- **THEN** a validation error names the missing variable

#### Scenario: Optional variables have defaults
- **WHEN** `OPENAI_API_KEY` is not set
- **THEN** the settings object loads successfully with `None` for optional fields

### Requirement: .gitignore covers Python, Swift, and environment files
The root `.gitignore` SHALL include patterns for: Python bytecode (`__pycache__/`, `*.pyc`), virtual environments (`.venv/`), environment files (`.env`, `.envrc`), macOS (`.DS_Store`), Xcode (`*.xcodeproj/xcuserdata/`, `build/`), and uv (`.uv/`).

#### Scenario: Common artifacts are ignored
- **WHEN** a developer runs `uv sync` and Python creates `__pycache__/`
- **THEN** `git status` does not show `__pycache__/` as untracked
