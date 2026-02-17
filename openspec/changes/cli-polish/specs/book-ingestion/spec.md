# book-ingestion

Delta spec for auto-embedding in the ingestion pipeline. `IngestBookUseCase` accepts an optional `EmbedBookUseCase` to embed chunks immediately after ingestion.

## MODIFIED Requirements

### Requirement: IngestBookUseCase orchestrates the ingestion pipeline (MODIFIED)

The application layer SHALL provide an `IngestBookUseCase` class in `app/ingest.py` that accepts `BookParser` (pdf and txt), `TextChunker`, `BookRepository`, and `ChunkRepository` via constructor injection. It SHALL also accept an optional `embed_use_case: EmbedBookUseCase | None = None` parameter.

It SHALL expose an `execute(file_path: Path, title: str) -> tuple[Book, Exception | None]` method that:

1. Validates file extension (`.pdf` or `.txt`); raises `BookError(UNSUPPORTED_FORMAT)` otherwise
2. Creates a `Book` entity, transitions to INGESTING, saves
3. Parses the file with the appropriate parser
4. Chunks the parsed pages
5. Persists chunks via `ChunkRepository.save_chunks()`
6. Transitions to READY, saves
7. If `embed_use_case` is not None, calls `embed_use_case.execute(book.id)` — if this raises, the exception is caught and returned as the second tuple element (the book stays READY, not FAILED)
8. Returns `(book, None)` on full success or `(book, exception)` if embed failed

**Changes from original:**

- Added optional `embed_use_case` parameter for auto-embedding after chunking
- Return type changed from `Book` to `tuple[Book, Exception | None]` — second element is `None` on success (including when no embed was attempted), or the caught exception if embed failed
- Auto-embed failure does not fail the ingest — the book remains in READY status
- The caller (CLI) decides whether to construct and pass `EmbedBookUseCase`

#### Scenario: Successful ingestion with auto-embed

- **WHEN** `execute` is called with `embed_use_case` provided and embedding succeeds
- **THEN** `(book, None)` is returned; book has `embedding_provider` and `embedding_dimension` set

#### Scenario: Successful ingestion without auto-embed

- **WHEN** `execute` is called with `embed_use_case=None`
- **THEN** `(book, None)` is returned; book is parsed and chunked but not embedded (same as current behavior, just wrapped in tuple)

#### Scenario: Ingestion succeeds but auto-embed fails

- **WHEN** `execute` is called with `embed_use_case` provided and embedding raises an error
- **THEN** `(book, exception)` is returned; book is in READY status, second element is the caught exception

#### Scenario: Parse failure still transitions to FAILED

- **WHEN** parsing raises a `BookError`
- **THEN** the book is saved with status FAILED and the error is re-raised (unchanged behavior)
