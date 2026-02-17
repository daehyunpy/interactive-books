## MODIFIED Requirements

### SPL-3: CLI search command wires the retrieval pipeline

The CLI provides a `search` command that accepts a book ID and query string. It prints each result's page range, distance score, and a content preview. Supports `--top-k` option (default 5). Validates `OPENAI_API_KEY` using the shared `_require_env` helper. Uses `_open_db` helper for database setup. When `--verbose` is enabled, prints the embedding provider name, dimension, number of results, and search duration to stderr before the results.
