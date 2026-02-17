## Why

Phase 8 (EPUB + DOCX) is complete — the Python CLI now supports four file formats. The next step in the build order (Phase 9) is text format parsers: HTML, Markdown, and URL. These are the remaining formats in the product requirements. HTML and Markdown are common document formats for technical content and web-sourced material. URL import lets users point at a web page and immediately start chatting about it. Without these parsers, users must manually convert web and Markdown content to text before ingesting.

## What Changes

- Add `FETCH_FAILED` error code to `BookErrorCode` in the domain layer
- Add `UrlParser` protocol to `domain/protocols.py` for URL-specific parsing (`parse_url(url: str) → list[PageContent]`)
- Implement HTML parser in `infra/parsers/html.py` using `selectolax` — strip tags, extract text, single logical page per document
- Implement Markdown parser in `infra/parsers/markdown.py` using `markdown-it-py` — render to plain text, split at H1 and H2 heading boundaries (same strategy as DOCX)
- Implement URL parser in `infra/parsers/url.py` using `httpx` + `selectolax` — fetch single page, check Content-Type, extract text, single logical page
- Add `markdown-it-py` dependency to `pyproject.toml`
- Extend `IngestBookUseCase` to accept `html_parser`, `md_parser`, and `url_parser`; extend `execute` signature to handle URL strings (`source: Path | str`); add `.html` and `.md` to `SUPPORTED_EXTENSIONS`
- Wire new parsers in `main.py` ingest command; update argument help text to include new formats
- Add shared test fixtures (`shared/fixtures/sample_book.html`, `sample_book.md`)
- Add unit tests for all three parsers and update ingest use case tests

## Capabilities

### New Capabilities
- `book-parsing` (HTML): Parse HTML files into a single logical page by stripping tags and extracting text via selectolax
- `book-parsing` (Markdown): Parse Markdown files into heading-based logical pages (H1 + H2 boundaries) using markdown-it-py
- `book-parsing` (URL): Fetch a single web page via httpx, check Content-Type, extract text via selectolax, produce a single logical page

### Modified Capabilities
- `book-ingestion`: Extend `IngestBookUseCase` to support `.html`, `.md`, and URL sources; accept `source: Path | str`; Content-Type detection for URLs

## Impact

- **Domain layer** (`domain/errors.py`): adds `FETCH_FAILED` to `BookErrorCode`
- **Domain layer** (`domain/protocols.py`): adds `UrlParser` protocol
- **Infrastructure layer**: new `infra/parsers/html.py`, `infra/parsers/markdown.py`, `infra/parsers/url.py`
- **Application layer** (`app/ingest.py`): extended parser injection, format routing, URL handling
- **CLI** (`main.py`): wire new parsers into `ingest` command, update help text
- **Dependencies** (`pyproject.toml`): adds `markdown-it-py`
- **Shared fixtures** (`shared/fixtures/`): adds sample HTML and Markdown files
- **Test suite**: new parser tests, updated ingest use case tests
