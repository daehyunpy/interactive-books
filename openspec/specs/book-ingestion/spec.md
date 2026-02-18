# book-ingestion

Book ingestion pipeline: parsing, chunking, persistence, and optional auto-embedding. Located in `python/source/interactive_books/app/ingest.py`.

## Requirements

### Requirement: IngestBookUseCase orchestrates the ingestion pipeline

The application layer SHALL provide an `IngestBookUseCase` class in `app/ingest.py` that accepts `BookParser` instances (pdf, txt, epub, docx, html, md), a `UrlParser` instance, `TextChunker`, `BookRepository`, and `ChunkRepository` via constructor injection. It SHALL also accept an optional `embed_use_case: EmbedBookUseCase | None = None` parameter. Parser selection for file-based sources SHALL use a `dict[str, BookParser]` mapping keyed by file extension. The `url_parser` SHALL be stored separately for URL source handling.

It SHALL expose an `execute(source: Path | str, title: str) -> tuple[Book, Exception | None]` method that:

1. Validates source: if `source` is a `str` starting with `http://` or `https://`, accepts as URL; otherwise validates file extension (`.pdf`, `.txt`, `.epub`, `.docx`, `.html`, or `.md`); raises `BookError(UNSUPPORTED_FORMAT)` for unsupported extensions
2. Creates a `Book` entity, transitions to INGESTING, saves
3. Parses the source: URL sources delegate to `url_parser.parse_url(source)`; file sources use the extension-based parser mapping
4. Chunks the parsed pages
5. Persists chunks via `ChunkRepository.save_chunks()`
6. Transitions to READY, saves
7. If `embed_use_case` is not None, calls `embed_use_case.execute(book.id)` — if this raises, the exception is caught and returned as the second tuple element (the book stays READY, not FAILED)
8. Returns `(book, None)` on full success or `(book, exception)` if embed failed

#### Scenario: Successful ingestion of a PDF

- **WHEN** `execute` is called with a valid PDF file path and title
- **THEN** a `Book` is created with status `READY`, chunks are persisted via `ChunkRepository`, and `(book, None)` is returned

#### Scenario: Successful ingestion of a TXT file

- **WHEN** `execute` is called with a valid TXT file path and title
- **THEN** a `Book` is created with status `READY`, chunks are persisted, and `(book, None)` is returned

#### Scenario: Successful ingestion of an HTML file

- **WHEN** `execute` is called with a valid HTML file path and title
- **THEN** a `Book` is created with status `READY`, chunks are persisted, and `(book, None)` is returned

#### Scenario: Successful ingestion of a Markdown file

- **WHEN** `execute` is called with a valid Markdown file path and title
- **THEN** a `Book` is created with status `READY`, chunks are persisted, and `(book, None)` is returned

#### Scenario: Successful ingestion of a URL

- **WHEN** `execute` is called with a URL string starting with `https://` and a title
- **THEN** the URL parser's `parse_url` method is called and `(book, None)` is returned

#### Scenario: URL fetch failure during ingestion

- **WHEN** the URL parser raises `BookError(FETCH_FAILED)`
- **THEN** the book is saved with status FAILED and the error is re-raised

#### Scenario: Successful ingestion with auto-embed

- **WHEN** `execute` is called with `embed_use_case` provided and embedding succeeds
- **THEN** `(book, None)` is returned; book has `embedding_provider` and `embedding_dimension` set

#### Scenario: Successful ingestion without auto-embed

- **WHEN** `execute` is called with `embed_use_case=None`
- **THEN** `(book, None)` is returned; book is parsed and chunked but not embedded

#### Scenario: Ingestion succeeds but auto-embed fails

- **WHEN** `execute` is called with `embed_use_case` provided and embedding raises an error
- **THEN** `(book, exception)` is returned; book is in READY status, second element is the caught exception

### Requirement: Book status transitions follow the state machine during ingestion

The use case SHALL transition the `Book` through status states: PENDING → INGESTING → READY on success, or PENDING → INGESTING → FAILED on error.

#### Scenario: Status transitions on success

- **WHEN** ingestion completes successfully
- **THEN** the `Book` saved to the repository has status `READY`

#### Scenario: Status transitions on parse failure

- **WHEN** the parser raises a `BookError`
- **THEN** the `Book` is saved with status `FAILED` and the error is re-raised

#### Scenario: Status transitions on chunk failure

- **WHEN** the chunker raises an error after parsing succeeds
- **THEN** the `Book` is saved with status `FAILED` and the error is re-raised

#### Scenario: Parse failure still transitions to FAILED (auto-embed present)

- **WHEN** parsing raises a `BookError` and `embed_use_case` is provided
- **THEN** the book is saved with status FAILED and the error is re-raised (auto-embed is not attempted)

### Requirement: File format determines parser selection

The use case SHALL select the appropriate `BookParser` based on file extension using a `dict[str, BookParser]` mapping: `.pdf` uses the PDF parser, `.txt` uses the plain text parser, `.epub` uses the EPUB parser, `.docx` uses the DOCX parser, `.html` uses the HTML parser, `.md` uses the Markdown parser. Unsupported extensions SHALL raise `BookError` with code `UNSUPPORTED_FORMAT` before creating a `Book`.

#### Scenario: PDF file selects PDF parser

- **WHEN** a file with `.pdf` extension is provided
- **THEN** the PDF parser is used for extraction

#### Scenario: TXT file selects text parser

- **WHEN** a file with `.txt` extension is provided
- **THEN** the plain text parser is used for extraction

#### Scenario: EPUB file selects EPUB parser

- **WHEN** a file with `.epub` extension is provided
- **THEN** the EPUB parser is used for extraction

#### Scenario: DOCX file selects DOCX parser

- **WHEN** a file with `.docx` extension is provided
- **THEN** the DOCX parser is used for extraction

#### Scenario: HTML file selects HTML parser

- **WHEN** a file with `.html` extension is provided
- **THEN** the HTML parser is used for extraction

#### Scenario: Markdown file selects Markdown parser

- **WHEN** a file with `.md` extension is provided
- **THEN** the Markdown parser is used for extraction

#### Scenario: DRM-protected EPUB rejected during ingestion

- **WHEN** a DRM-protected EPUB file is provided for ingestion
- **THEN** `BookError(DRM_PROTECTED)` is raised by the EPUB parser during ingestion

#### Scenario: Unsupported format rejected before Book creation

- **WHEN** a file with `.xyz` extension is provided
- **THEN** `BookError(UNSUPPORTED_FORMAT)` is raised and no `Book` is created in the repository

### Requirement: Chunks are persisted with correct book association

The use case SHALL convert `ChunkData` objects from the chunker into `Chunk` domain entities with generated IDs and the `Book`'s ID, then save them via `ChunkRepository.save_chunks`.

#### Scenario: Chunks linked to book

- **WHEN** ingestion produces 5 chunks
- **THEN** `ChunkRepository.save_chunks` is called with the book's ID and 5 `Chunk` entities

#### Scenario: Chunk IDs are unique

- **WHEN** chunks are created during ingestion
- **THEN** each `Chunk` has a unique `id`

### Requirement: CLI ingest command wires the pipeline

The CLI SHALL provide an `ingest` command that accepts a file path or URL and optional `--title` (defaulting to filename stem for files, last path segment for URLs). It SHALL construct `IngestBookUseCase` with parsers (including HTML, Markdown, and URL parsers), chunker, and repositories. It SHALL detect URLs by prefix (`http://` or `https://`). If `OPENAI_API_KEY` is available in the environment, it SHALL also construct `EmbedBookUseCase` and pass it as `embed_use_case` to `IngestBookUseCase` for auto-embedding.

After successful execution, the command SHALL print:

- Book ID, title, status, and chunk count
- If auto-embed succeeded: embedding provider and dimension
- If auto-embed was skipped (no API key): `Tip: Set OPENAI_API_KEY to auto-embed, or run 'embed <book-id>' manually.`
- If auto-embed failed: `Warning: Embedding failed: <reason>` and `Tip: Run 'embed' command separately to retry.`

#### Scenario: Ingest a PDF via CLI

- **WHEN** `cli ingest path/to/book.pdf` is executed
- **THEN** the book is ingested and a summary is printed showing book ID, title, status READY, and chunk count

#### Scenario: Ingest with custom title

- **WHEN** `cli ingest path/to/book.pdf --title "My Book"` is executed
- **THEN** the book is created with title "My Book"

#### Scenario: Ingest with auto-embed

- **WHEN** `cli ingest book.pdf` is executed with `OPENAI_API_KEY` set
- **THEN** the book is parsed, chunked, and embedded; output shows status, chunk count, and embedding info

#### Scenario: Ingest without API key

- **WHEN** `cli ingest book.pdf` is executed without `OPENAI_API_KEY`
- **THEN** the book is parsed and chunked but not embedded; output shows a tip about running `embed`

#### Scenario: Ingest with embed failure

- **WHEN** `cli ingest book.pdf` is executed and embedding fails (e.g., API error)
- **THEN** the book is still ingested (status READY); a warning is printed with the error reason

#### Scenario: Ingest failure shows error

- **WHEN** `cli ingest path/to/invalid.xyz` is executed
- **THEN** an error message is displayed indicating the format is unsupported
