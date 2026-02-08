## ADDED Requirements

### Requirement: Python source has DDD layer directories
The `python/source/interactive_books/` directory SHALL contain three subdirectories: `domain/`, `app/`, and `infra/`. Each SHALL contain an `__init__.py`.

#### Scenario: DDD layer directories exist
- **WHEN** a developer lists `python/source/interactive_books/`
- **THEN** directories `domain/`, `app/`, and `infra/` are present, each with `__init__.py`

### Requirement: Python tests mirror source structure
The `python/tests/` directory SHALL contain subdirectories `domain/`, `app/`, and `infra/` matching the source DDD layers. It SHALL contain a `conftest.py` at the top level.

#### Scenario: Test directories mirror source
- **WHEN** a developer lists `python/tests/`
- **THEN** directories `domain/`, `app/`, `infra/` are present along with `conftest.py`

### Requirement: Shared contracts directory exists
The `shared/` directory at the project root SHALL contain three subdirectories: `schema/`, `prompts/`, and `fixtures/`. Each SHALL contain a `.gitkeep` file.

#### Scenario: Shared directories exist in repo
- **WHEN** a developer clones the repo
- **THEN** `shared/schema/`, `shared/prompts/`, and `shared/fixtures/` directories are present

### Requirement: Swift placeholder directory exists
The `swift/` directory at the project root SHALL exist with a `.gitkeep` file. No Swift code or Xcode project SHALL be created.

#### Scenario: Swift directory is a placeholder
- **WHEN** a developer lists `swift/`
- **THEN** only `.gitkeep` is present
