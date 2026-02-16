## ADDED Requirements

### Requirement: IngestBookUseCase orchestrates the ingestion pipeline
The application layer SHALL provide an `IngestBookUseCase` class in `app/ingest.py` that accepts `BookParser`, `TextChunker`, `BookRepository`, and `ChunkRepository` via constructor injection. It SHALL expose an `execute(file_path: Path, title: str) → Book` method.

#### Scenario: Successful ingestion of a PDF
- **WHEN** `execute` is called with a valid PDF file path and title
- **THEN** a `Book` is created with status `READY`, chunks are persisted via `ChunkRepository`, and the `Book` is returned

#### Scenario: Successful ingestion of a TXT file
- **WHEN** `execute` is called with a valid TXT file path and title
- **THEN** a `Book` is created with status `READY`, chunks are persisted, and the `Book` is returned

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

### Requirement: File format determines parser selection
The use case SHALL select the appropriate `BookParser` based on file extension: `.pdf` uses the PDF parser, `.txt` uses the plain text parser. Unsupported extensions SHALL raise `BookError` with code `UNSUPPORTED_FORMAT` before creating a `Book`.

#### Scenario: PDF file selects PDF parser
- **WHEN** a file with `.pdf` extension is provided
- **THEN** the PDF parser is used for extraction

#### Scenario: TXT file selects text parser
- **WHEN** a file with `.txt` extension is provided
- **THEN** the plain text parser is used for extraction

#### Scenario: Unsupported format rejected before Book creation
- **WHEN** a file with `.epub` extension is provided
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
The CLI SHALL provide an `ingest` command that accepts a file path and optional title (defaulting to the filename without extension). It SHALL print the book ID, title, status, and chunk count on success.

#### Scenario: Ingest a PDF via CLI
- **WHEN** `cli ingest path/to/book.pdf` is executed
- **THEN** the book is ingested and a summary is printed showing book ID, title, status READY, and chunk count

#### Scenario: Ingest with custom title
- **WHEN** `cli ingest path/to/book.pdf --title "My Book"` is executed
- **THEN** the book is created with title "My Book"

#### Scenario: Ingest failure shows error
- **WHEN** `cli ingest path/to/invalid.xyz` is executed
- **THEN** an error message is displayed indicating the format is unsupported
