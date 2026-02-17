## Why

Phases 1–7 are complete — the Python CLI can ingest PDF and TXT files, generate embeddings, run vector search, and have multi-turn agentic conversations. The next step in the build order (Phase 8) is structured format parsers. EPUB and DOCX are the two most common ebook and document formats users will have. Without these parsers, the app only supports raw PDF and TXT, severely limiting the library of books users can upload. This unblocks the product requirement for multi-format support.

## What Changes

- Add `DRM_PROTECTED` error code to `BookErrorCode` in the domain layer
- Implement EPUB parser in `infra/parsers/epub.py` using stdlib `zipfile` + `selectolax` — parse OPF manifest for spine order, extract XHTML chapter content, one logical page per chapter, detect and reject DRM-protected EPUBs
- Implement DOCX parser in `infra/parsers/docx.py` using `python-docx` — extract paragraph and table text, split into logical pages at H1 and H2 heading boundaries, ignore images and embedded objects
- Add `selectolax` and `python-docx` dependencies to `pyproject.toml`
- Extend `IngestBookUseCase` to accept `epub_parser` and `docx_parser`, add `.epub` and `.docx` to `SUPPORTED_EXTENSIONS`, replace if/else parser selection with a dict mapping
- Wire new parsers in `main.py` ingest command
- Add shared test fixtures (`shared/fixtures/sample_book.epub`, `sample_book.docx`)
- Add unit tests for both parsers and update ingest use case tests

## Capabilities

### New Capabilities
- `book-parsing` (EPUB): Parse EPUB files into per-chapter logical pages via OPF spine order, strip XHTML tags, detect and reject DRM
- `book-parsing` (DOCX): Parse DOCX files into logical pages split at H1/H2 heading boundaries, extract paragraph and table text

### Modified Capabilities
- `book-ingestion`: Extend `IngestBookUseCase` to support `.epub` and `.docx` format selection and parser injection

## Impact

- **Domain layer** (`domain/errors.py`): adds `DRM_PROTECTED` to `BookErrorCode`
- **Infrastructure layer**: new `infra/parsers/epub.py` and `infra/parsers/docx.py`
- **Application layer** (`app/ingest.py`): extended parser injection and format routing
- **CLI** (`main.py`): wire new parsers into `ingest` command
- **Dependencies** (`pyproject.toml`): adds `selectolax` and `python-docx`
- **Shared fixtures** (`shared/fixtures/`): adds sample EPUB and DOCX files
- **Test suite**: new parser tests, updated ingest use case tests
