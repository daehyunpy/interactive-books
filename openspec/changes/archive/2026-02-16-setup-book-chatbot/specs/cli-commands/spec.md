# cli-commands

Delta spec for CLI command changes. Removes the `ask` command and adds the `chat` command with conversation selection. Other commands (`books`, `show`, `delete`, `set-page`) are unchanged.

## ADDED Requirements

### CC-9: CLI chat command replaces ask command

The CLI SHALL provide a `chat <book-id>` command that starts an interactive conversation about a book. This command replaces the removed `ask` command. The full specification for the chat command is defined in the `chat-cli` spec (CCLI-1 through CCLI-6).

The `chat` command SHALL:
- Accept a required `book-id` argument
- Support `--verbose` / `-v` flag for tool result visibility
- Use `_require_env` to validate `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`
- Use `_open_db` helper for database setup
- Wire together `ChatWithBookUseCase`, `ConversationRepository`, `ChatMessageRepository`, and all required dependencies

#### Scenario: Chat command registered

- **WHEN** `cli --help` is executed
- **THEN** the `chat` command appears in the help output with a description

#### Scenario: Chat command wiring

- **WHEN** `cli chat <book-id>` is executed
- **THEN** all dependencies are constructed and injected: `ChatProvider`, `SearchBooksUseCase`, `ChatMessageRepository`, `ConversationRepository`, `BookRepository`, `RetrievalStrategy`, `ConversationContextStrategy`

#### Scenario: Chat replaces ask in CLI

- **WHEN** `cli --help` is executed
- **THEN** there is a `chat` command but no `ask` command

## MODIFIED Requirements

### CC-4: DeleteBookUseCase removes a book and all associated data (MODIFIED)

The application layer SHALL provide a `DeleteBookUseCase` class in `app/delete_book.py` that accepts `BookRepository` and `EmbeddingRepository` via constructor injection. It SHALL expose an `execute(book_id: str) -> Book` method that:

1. Fetches the book via `book_repo.get(book_id)` -- raises `BookError(NOT_FOUND)` if missing
2. If `book.embedding_provider` and `book.embedding_dimension` are both non-None, calls `embedding_repo.delete_by_book(provider, dimension, book_id)` to clean up vec0 virtual table rows
3. Calls `book_repo.delete(book_id)` -- chunks, conversations, and messages cascade automatically via SQL foreign keys
4. Returns the deleted book

**Changes from original:**
- Cascade delete now also covers `conversations` and `chat_messages` (via `conversations`) in addition to `chunks`
- No code change required in `DeleteBookUseCase` itself -- the cascade is handled by SQL foreign key constraints added in the `sql-schema` delta

#### Scenario: Book deletion cascades to conversations and messages

- **WHEN** `execute` is called for a book that has conversations with messages
- **THEN** the book, its chunks, its conversations, and all messages in those conversations are deleted

#### Scenario: Unchanged behavior for books without conversations

- **WHEN** `execute` is called for a book that has no conversations
- **THEN** the behavior is identical to the original (chunks and embeddings cleaned up)

## REMOVED Requirements

### AP-3 / CC (ask command): CLI ask command

**Reason:** The `ask` command is removed from the CLI. It is replaced by the `chat` command which provides a superset of functionality (interactive REPL, conversation persistence, tool-use, verbose mode).

**Migration:** Remove the `ask` command definition and its callback from `main.py`. Remove the `AskBookUseCase` import and wiring. Users migrate to `cli chat <book-id>` for book Q&A. The `app/ask.py` module is deleted.
