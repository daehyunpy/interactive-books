## 1. Domain Value Objects

- [x] 1.1 Add `PageContent` frozen dataclass to `domain/` (page_number >= 1, text: str) with validation tests
- [x] 1.2 Add `ChunkData` frozen dataclass to `domain/` (content non-empty, start_page >= 1, end_page >= start_page, chunk_index >= 0) with validation tests

## 2. Domain Protocols

- [x] 2.1 Add `BookParser` protocol to `domain/protocols.py` with `parse(file_path: Path) → list[PageContent]`
- [x] 2.2 Add `TextChunker` protocol to `domain/protocols.py` with `chunk(pages: list[PageContent]) → list[ChunkData]`

## 3. PDF Parser Adapter

- [x] 3.1 Add `pymupdf` dependency to `pyproject.toml`
- [x] 3.2 Implement `PyMuPdfParser` in `infra/parsers/pdf.py` — extract per-page text, handle empty/unparseable pages, raise BookError on file-not-found and invalid PDF
- [x] 3.3 Write tests for `PyMuPdfParser` (multi-page PDF, empty page, file not found, invalid PDF) using a small test fixture PDF

## 4. Plain Text Parser Adapter

- [x] 4.1 Implement `PlainTextParser` in `infra/parsers/txt.py` — divide text by `chars_per_page` (default 3000), raise BookError on empty/missing file
- [x] 4.2 Write tests for `PlainTextParser` (short file, multi-page file, empty file, file not found)

## 5. Recursive Chunker Adapter

- [x] 5.1 Implement `RecursiveChunker` in `infra/chunkers/recursive.py` — split by paragraph → newline → sentence → word, configurable `max_tokens`/`overlap_tokens`, assign page ranges and sequential chunk_index
- [x] 5.2 Write tests for `RecursiveChunker` (single chunk, paragraph splits, page-spanning chunks, overlap verification, empty pages skipped, all pages empty)

## 6. Ingest Use Case

- [x] 6.1 Implement `IngestBookUseCase` in `app/ingest.py` — accept parsers + repos via constructor, select parser by extension, orchestrate parse → chunk → persist with Book status transitions (PENDING → INGESTING → READY/FAILED)
- [x] 6.2 Write tests for `IngestBookUseCase` (successful PDF ingest, successful TXT ingest, unsupported format rejected before Book creation, parse failure sets FAILED status, chunk failure sets FAILED status, chunks linked to book with unique IDs)

## 7. Shared Test Fixtures

- [x] 7.1 Add `shared/fixtures/sample_book.pdf` (small multi-page PDF for integration testing)
- [x] 7.2 Add `shared/fixtures/sample_book.txt` (plain text file for integration testing)

## 8. CLI Command

- [x] 8.1 Wire `ingest` command in `main.py` via Typer — accept file path and optional `--title`, print book ID/title/status/chunk count on success, print error on failure

## 9. Verification

- [x] 9.1 Run full test suite (`uv run pytest -x`), lint (`uv run ruff check .`), and type check (`uv run pyright`) — all passing
