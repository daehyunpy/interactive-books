# cli-commands

CLI command definitions, wiring, and registration. Covers `ingest`, `embed`, `search`, `chat`, `books`, `show`, `delete`, and `set-page` commands. Located in `python/source/interactive_books/main.py`.

## Requirements

### CC-1: CLI app structure and global options

The CLI SHALL be a Typer application with `--version` / `-v` and `--verbose` global options. The `--verbose` flag sets a module-level `_verbose` boolean used by all commands.

### CC-2: CLI books command lists all books

The CLI SHALL provide a `books` command that displays a table of all books with ID, title, status, chunk count, embedding provider, and current page.

### CC-3: CLI show command displays book details

The CLI SHALL provide a `show <book-id>` command that displays detailed information about a single book.

### CC-4: DeleteBookUseCase removes a book and all associated data

The application layer SHALL provide a `DeleteBookUseCase` class in `app/delete_book.py` that accepts `BookRepository` and `EmbeddingRepository` via constructor injection. It SHALL expose an `execute(book_id: str) -> Book` method that:

1. Fetches the book via `book_repo.get(book_id)` -- raises `BookError(NOT_FOUND)` if missing
2. If `book.embedding_provider` and `book.embedding_dimension` are both non-None, calls `embedding_repo.delete_by_book(provider, dimension, book_id)` to clean up vec0 virtual table rows
3. Calls `book_repo.delete(book_id)` -- chunks, conversations, and messages cascade automatically via SQL foreign keys
4. Returns the deleted book

#### Scenario: Book deletion cascades to conversations and messages

- **WHEN** `execute` is called for a book that has conversations with messages
- **THEN** the book, its chunks, its conversations, and all messages in those conversations are deleted

#### Scenario: Unchanged behavior for books without conversations

- **WHEN** `execute` is called for a book that has no conversations
- **THEN** the behavior is identical to the original (chunks and embeddings cleaned up)

### CC-5: CLI ingest command wires the pipeline

The CLI `ingest` command SHALL accept a file path and optional `--title` (defaulting to filename stem). It SHALL construct `IngestBookUseCase` with parsers, chunker, and repositories. If `OPENAI_API_KEY` is available in the environment, it SHALL also construct `EmbedBookUseCase` and pass it as `embed_use_case` to `IngestBookUseCase` for auto-embedding.

After successful execution, the command SHALL print:

- Book ID, title, status, and chunk count
- If auto-embed succeeded: embedding provider and dimension
- If auto-embed was skipped (no API key): `Tip: Set OPENAI_API_KEY to auto-embed, or run 'embed <book-id>' manually.`
- If auto-embed failed: `Warning: Embedding failed: <reason>` and `Tip: Run 'embed' command separately to retry.`

`OPENAI_API_KEY` is NOT required — ingest still works without it (parse + chunk only).

#### Scenario: Ingest with auto-embed

- **WHEN** `cli ingest book.pdf` is executed with `OPENAI_API_KEY` set
- **THEN** the book is parsed, chunked, and embedded; output shows status, chunk count, and embedding info

#### Scenario: Ingest without API key

- **WHEN** `cli ingest book.pdf` is executed without `OPENAI_API_KEY`
- **THEN** the book is parsed and chunked but not embedded; output shows a tip about running `embed`

#### Scenario: Ingest with embed failure

- **WHEN** `cli ingest book.pdf` is executed and embedding fails (e.g., API error)
- **THEN** the book is still ingested (status READY); a warning is printed with the error reason

### CC-6: CLI embed command output includes chunk count

The CLI `embed` command output SHALL include the number of chunks embedded in its summary, in addition to the existing book ID, title, provider, and dimension fields.

#### Scenario: Embed output shows chunk count

- **WHEN** `cli embed <book-id>` completes successfully
- **THEN** the output includes a line showing the number of chunks embedded (e.g., `Chunks:      47`)

### CC-7: CLI search command queries vector store

The CLI SHALL provide a `search <book-id> <query>` command with optional `--top-k` parameter.

### CC-8: CLI set-page command updates reading position

The CLI SHALL provide a `set-page <book-id> <page>` command that updates the current reading position for a book.

### CC-9: CLI chat command replaces ask command

The CLI SHALL provide a `chat <book-id>` command that starts an interactive conversation about a book. This command replaces the removed `ask` command. The full specification for the chat command is defined in the `chat-cli` spec (CCLI-1 through CCLI-6).

The `chat` command SHALL:

- Accept a required `book-id` argument
- Support `--verbose` flag for tool result visibility
- Use `_require_env` to validate `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`
- Use `_open_db` helper for database setup
- Wire together `ChatWithBookUseCase`, `ConversationRepository`, `ChatMessageRepository`, and all required dependencies

The conversation selection SHALL re-prompt on invalid input instead of silently creating a new conversation. When the user enters an invalid selection (non-numeric, out of range), the CLI SHALL print an invalid choice message and re-prompt. After 3 invalid attempts (`MAX_SELECTION_RETRIES`), a new conversation is created as fallback.

#### Scenario: Chat command registered

- **WHEN** `cli --help` is executed
- **THEN** the `chat` command appears in the help output with a description

#### Scenario: Chat replaces ask in CLI

- **WHEN** `cli --help` is executed
- **THEN** there is a `chat` command but no `ask` command

#### Scenario: Re-prompt on invalid selection

- **WHEN** the user enters an invalid conversation selection (e.g., "abc" or "99")
- **THEN** an invalid choice message is printed and the prompt is shown again

#### Scenario: Fallback after max retries

- **WHEN** the user enters 3 consecutive invalid selections
- **THEN** a new conversation is created automatically
