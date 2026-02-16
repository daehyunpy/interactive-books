# domain-errors

Typed domain exceptions matching the cross-platform error taxonomy. Located in `python/source/interactive_books/domain/errors.py`.

## Requirements

### DE-1: BookError

`BookError` exception class with enumerated cases: `not_found`, `parse_failed`, `unsupported_format`, `already_exists`, `invalid_state` (for invalid status transitions). Each case has a descriptive message. Uses an inner enum `BookErrorCode` for case identification.

### DE-2: LLMError

`LLMError` exception class with enumerated cases: `api_key_missing`, `api_call_failed`, `rate_limited`, `timeout`. Each case has a descriptive message. Uses an inner enum `LLMErrorCode`.

### DE-3: StorageError

`StorageError` exception class with enumerated cases: `db_corrupted`, `migration_failed`, `write_failed`, `not_found`. Each case has a descriptive message. Uses an inner enum `StorageErrorCode`.

### DE-4: Error case names match taxonomy

Error case names match the "Error Taxonomy" table in `docs/technical_design.md` → "Cross-Platform Contracts". Python uses `snake_case` enum values.

### DE-5: Errors are typed exceptions

All error classes inherit from a common `DomainError` base class (which inherits from `Exception`). They are never bare `Exception` or `RuntimeError`.

### DE-6: Error messages are descriptive

Each error carries a human-readable `message` attribute and the specific `code` enum value. `str(error)` returns the message.
