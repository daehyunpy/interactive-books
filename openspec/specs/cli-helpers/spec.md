# cli-helpers

Shared CLI helper functions and global flags. Located in `python/source/interactive_books/main.py`.

## Requirements

### CH-1: Shared DB setup helper

The CLI module SHALL provide a `_open_db(enable_vec: bool = False) → Database` helper function that creates the data directory, constructs a `Database`, and runs migrations. All commands SHALL use this helper instead of duplicating DB setup.

#### Scenario: DB helper creates and migrates

- **WHEN** `_open_db()` is called
- **THEN** `DB_PATH.parent` is created, a `Database` is constructed, and migrations are applied

#### Scenario: DB helper with vec extension

- **WHEN** `_open_db(enable_vec=True)` is called
- **THEN** the database is opened with sqlite-vec extension enabled

### CH-2: Shared API-key validation helper

The CLI module SHALL provide a `_require_env(name: str) → str` helper function that reads an environment variable and exits with a consistent error message if the variable is not set or empty.

#### Scenario: Env var present

- **WHEN** `_require_env("OPENAI_API_KEY")` is called and the variable is set
- **THEN** the value is returned

#### Scenario: Env var missing

- **WHEN** `_require_env("OPENAI_API_KEY")` is called and the variable is not set
- **THEN** an error message "Error: OPENAI_API_KEY environment variable is not set" is printed to stderr and the process exits with code 1

### CH-3: Global --verbose flag

The CLI SHALL support a `--verbose` global flag that enables detailed output across all commands. When verbose is enabled, commands SHALL print additional operational details such as model names, chunk counts, and timing information.

#### Scenario: Verbose flag off by default

- **WHEN** a command is run without `--verbose`
- **THEN** only standard output is printed

#### Scenario: Verbose flag enabled

- **WHEN** a command is run with `--verbose`
- **THEN** additional debug information is printed
