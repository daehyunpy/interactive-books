## Why

Phase 2 (DB Schema) is complete — the domain model, SQLite storage, and repository protocols are in place. The next step in the build order is book ingestion: the ability to take a PDF or TXT file, extract its text with page boundaries, split it into chunks, and persist the resulting `Book` + `Chunk` entities. Without ingestion, there is no content in the system to embed, retrieve, or chat about. This unblocks Phases 4–7.

## What Changes

- Add `BookParser` protocol to the domain layer — abstraction for extracting text and page boundaries from a file
- Add `TextChunker` protocol to the domain layer — abstraction for splitting extracted text into chunks with page mapping
- Implement `PyMuPdfParser` infrastructure adapter for PDF files using PyMuPDF
- Implement `PlainTextParser` infrastructure adapter for TXT files with estimated page boundaries
- Implement `RecursiveChunker` infrastructure adapter — splits by paragraph → sentence → token limit (~500 tokens, ~100 token overlap)
- Add `IngestBookUseCase` in the application layer — orchestrates parsing, chunking, and persistence with `Book` status transitions (PENDING → INGESTING → READY/FAILED)
- Add shared test fixtures (`shared/fixtures/sample_book.pdf`, `sample_book.txt`, `expected_chunks.json`)
- Wire `ingest` CLI command via Typer

## Capabilities

### New Capabilities
- `book-parsing`: Extract text and page boundaries from PDF and TXT files via a pluggable `BookParser` protocol
- `text-chunking`: Split extracted text into overlapping chunks with page mapping via a pluggable `TextChunker` protocol
- `book-ingestion`: Application-layer use case that orchestrates parsing → chunking → persistence with status transitions

### Modified Capabilities

_(none — no existing spec-level requirements are changing)_

## Impact

- **Domain layer** (`domain/protocols.py`): adds `BookParser` and `TextChunker` protocols
- **Infrastructure layer**: new `infra/parsers/` and `infra/chunkers/` packages
- **Application layer**: new `app/ingest.py` use case
- **CLI** (`main.py`): new `ingest <file>` command
- **Dependencies** (`pyproject.toml`): adds `pymupdf` for PDF parsing
- **Shared fixtures** (`shared/fixtures/`): adds sample test files
- **Test suite**: new tests mirroring the source structure (`tests/domain/`, `tests/infra/`, `tests/app/`)
