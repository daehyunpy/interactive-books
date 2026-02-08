## ADDED Requirements

### Requirement: CI runs on push and pull request
The `.github/workflows/ci.yml` SHALL trigger on push to `main` and `develop`, and on pull requests to `main` and `develop`.

#### Scenario: Push to develop triggers CI
- **WHEN** a developer pushes to `develop`
- **THEN** the CI pipeline runs

#### Scenario: PR to main triggers CI
- **WHEN** a developer opens a PR targeting `main`
- **THEN** the CI pipeline runs

### Requirement: CI installs dependencies with uv
The CI pipeline SHALL use `astral-sh/setup-uv` to install uv, then run `uv sync` from the `python/` directory.

#### Scenario: Dependencies are cached
- **WHEN** CI runs for the second time with no dependency changes
- **THEN** uv uses the cached dependencies (faster run)

### Requirement: CI runs ruff lint
The CI pipeline SHALL run `uv run ruff check .` from `python/`.

#### Scenario: Lint failure blocks merge
- **WHEN** code has a ruff violation
- **THEN** the CI job fails

### Requirement: CI runs pyright type check
The CI pipeline SHALL run `uv run pyright` from `python/`.

#### Scenario: Type error blocks merge
- **WHEN** code has a type error
- **THEN** the CI job fails

### Requirement: CI runs pytest
The CI pipeline SHALL run `uv run pytest -x` from `python/`.

#### Scenario: Test failure blocks merge
- **WHEN** a test fails
- **THEN** the CI job fails

### Requirement: CI uses Python 3.13
The CI pipeline SHALL use Python 3.13 as the runtime version.

#### Scenario: Correct Python version
- **WHEN** CI runs
- **THEN** Python 3.13 is used for all steps
