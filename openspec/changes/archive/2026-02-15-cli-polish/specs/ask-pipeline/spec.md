## MODIFIED Requirements

### AP-3: CLI ask command wires the Q&A pipeline

The CLI provides an `ask` command accepting a book ID and question string. Supports `--top-k` option (default 5). Validates both `OPENAI_API_KEY` (for embeddings/search) and `ANTHROPIC_API_KEY` (for chat) using the shared `_require_env` helper. Prints the answer to stdout. Catches `BookError` and `LLMError` with error messages to stderr. Uses `_open_db` helper for database setup. When `--verbose` is enabled, prints the chat model name, number of context chunks retrieved, and the search duration to stderr before the answer.
