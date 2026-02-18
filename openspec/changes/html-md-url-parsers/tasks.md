## 9.1 — Domain: add FETCH_FAILED error code

- [x] Add `FETCH_FAILED = "fetch_failed"` to `BookErrorCode` in `domain/errors.py`
- [x] Verify pyright passes with the new error code

## 9.2 — Domain: add UrlParser protocol

- [x] Add `UrlParser` protocol to `domain/protocols.py` with method `parse_url(url: str) → list[PageContent]`
- [x] Verify pyright passes

## 9.3 — Shared: extract HTML text extraction to shared module

- [x] Create `infra/parsers/_html_text.py` with `BLOCK_TAGS` constant and `extract_block_text(node) → str` function (moved from `epub.py`)
- [x] Update `infra/parsers/epub.py` to import `BLOCK_TAGS` and `extract_block_text` from `_html_text.py` instead of defining them locally
- [x] Verify existing EPUB tests still pass after the refactor
- [x] Verify pyright passes

## 9.4 — Infrastructure: HTML parser

- [x] Write tests in `tests/infra/parsers/test_html_parser.py`:
  - `test_parse_returns_single_page` — HTML file produces one PageContent with page_number=1
  - `test_parse_extracts_body_text` — tags stripped, text content preserved
  - `test_parse_preserves_block_structure` — block tags produce newlines between text
  - `test_parse_empty_body_raises_book_error` — empty body raises PARSE_FAILED
  - `test_file_not_found_raises_book_error` — nonexistent path raises PARSE_FAILED
  - `test_parse_no_body_raises_book_error` — selectolax normalizes missing body to empty body
- [x] Add HTML fixtures to `tests/infra/parsers/conftest.py`:
  - `html_with_content` — well-formed HTML with paragraphs and headings
  - `html_empty_body` — HTML with an empty body
  - `html_no_body` — HTML fragment with no body tag
  - `invalid_html` — malformed/non-HTML content with .html extension
- [x] Implement `BookParser` class in `infra/parsers/html.py`:
  - Import `extract_block_text` from `_html_text.py`
  - File-not-found guard → `BookError(PARSE_FAILED)`
  - Read file as UTF-8
  - Parse with `selectolax.parser.HTMLParser`
  - Extract body text via `extract_block_text`
  - Raise `BookError(PARSE_FAILED)` if body text is empty after stripping
  - Return `[PageContent(page_number=1, text=extracted_text)]`
- [x] Verify all HTML parser tests pass
- [x] Verify pyright passes

## 9.5 — Infrastructure: Markdown parser

- [x] Write tests in `tests/infra/parsers/test_markdown_parser.py`:
  - `test_parse_splits_at_h1_headings` — H1 headings create page boundaries
  - `test_parse_splits_at_h2_headings` — H2 headings create page boundaries
  - `test_parse_mixed_h1_h2_splits_correctly` — both H1 and H2 split content
  - `test_parse_assigns_sequential_page_numbers` — pages numbered 1, 2, 3...
  - `test_content_before_first_heading_is_page_one` — intro text before any heading
  - `test_heading_text_included_in_section` — heading text included in its page
  - `test_no_headings_returns_single_page` — no headings → entire doc is one page
  - `test_parse_strips_formatting` — bold, italic, links, code stripped to plain text
  - `test_headings_in_code_blocks_ignored` — fenced code block headings don't split
  - `test_empty_file_raises_book_error` — empty file raises PARSE_FAILED
  - `test_file_not_found_raises_book_error` — nonexistent path raises PARSE_FAILED
- [x] Add Markdown fixtures to `tests/infra/parsers/conftest.py`:
  - `md_with_headings` — Markdown with H1, H2, content, and formatting
  - `md_no_headings` — Markdown with only paragraphs
  - `md_with_code_block` — Markdown with headings inside a fenced code block
  - `md_empty` — empty Markdown file
- [x] Implement `BookParser` class in `infra/parsers/markdown.py`:
  - File-not-found guard → `BookError(PARSE_FAILED)`
  - Read file as UTF-8
  - Parse with `markdown_it.MarkdownIt()` to get token stream
  - Walk tokens: detect `heading_open` with `tag` in `{"h1", "h2"}` for page boundaries
  - Collect text from `inline` tokens (strip formatting by walking inline children)
  - Split into sections at heading boundaries, content before first heading is page 1
  - If no headings, entire document is one page
  - Raise `BookError(PARSE_FAILED)` if all text is empty
  - Return `list[PageContent]` with sequential page numbers
- [x] Verify all Markdown parser tests pass
- [ ] Verify pyright passes

## 9.6 — Infrastructure: URL parser

- [x] Write tests in `tests/infra/parsers/test_url_parser.py`:
  - `test_parse_url_returns_single_page` — HTML URL produces one PageContent with page_number=1
  - `test_parse_url_extracts_text` — HTML content has tags stripped
  - `test_parse_url_plain_text_content` — text/plain URL returns raw text
  - `test_parse_url_network_error_raises_fetch_failed` — connection error → FETCH_FAILED
  - `test_parse_url_non_2xx_raises_fetch_failed` — 404/500 → FETCH_FAILED
  - `test_parse_url_unsupported_content_type_raises_fetch_failed` — application/pdf → FETCH_FAILED
  - `test_parse_url_empty_content_raises_fetch_failed` — empty response → FETCH_FAILED
  - `test_parse_url_markdown_content_type_splits_by_heading` — text/markdown URL produces heading-based pages
  - `test_parse_url_missing_content_type_treated_as_html` — no Content-Type header → try as HTML
- [x] Implement `UrlParser` class in `infra/parsers/url.py`:
  - Implements `UrlParser` protocol from domain
  - `parse_url(url: str) → list[PageContent]`
  - Fetch with `httpx.get(url, timeout=30, follow_redirects=True)`
  - Map `httpx` exceptions to `BookError(FETCH_FAILED)`
  - Check response status code — non-2xx → `BookError(FETCH_FAILED)`
  - Check Content-Type header:
    - `text/html` → parse body with selectolax via `extract_block_text`
    - `text/plain` → use response text directly
    - `text/markdown` → parse with markdown-it-py for heading-based pages (reuse Markdown parser logic)
    - Missing → attempt as HTML
    - Other → `BookError(FETCH_FAILED, "Unsupported content type: ...")`
  - Raise `BookError(FETCH_FAILED)` if extracted text is empty
  - Return `[PageContent(page_number=1, text=extracted_text)]`
- [x] Verify all URL parser tests pass (using httpx mock transport or monkeypatch)
- [ ] Verify pyright passes

## 9.7 — Application: extend IngestBookUseCase for HTML, MD, and URL

- [x] Write tests in `tests/app/test_ingest.py`:
  - `test_successful_html_ingest_returns_ready_book`
  - `test_successful_md_ingest_returns_ready_book`
  - `test_successful_url_ingest_returns_ready_book` — URL string source
  - `test_url_source_uses_url_parser` — verify URL source routes to url_parser
  - `test_unsupported_extension_still_rejected` — e.g., `.xyz` → UNSUPPORTED_FORMAT
  - `test_url_fetch_failure_propagates_error` — FETCH_FAILED propagates
- [x] Update `SUPPORTED_EXTENSIONS` to include `.html` and `.md`
- [x] Add `html_parser: BookParser`, `md_parser: BookParser`, and `url_parser: UrlParser` parameters to `IngestBookUseCase.__init__`
- [x] Add `.html` and `.md` entries to the `self._parsers` dict
- [x] Store `self._url_parser` from constructor
- [x] Change `execute` signature from `file_path: Path` to `source: Path | str`
- [x] Add URL detection at the start of `execute`: if `source` is `str` and starts with `http://` or `https://`, delegate to `self._url_parser.parse_url(source)`; otherwise convert to `Path` and use existing file-extension logic
- [x] Verify all ingest tests pass (existing + new)
- [x] Verify pyright passes

## 9.8 — CLI: wire new parsers and update ingest command

- [x] Update `main.py` ingest command:
  - Add lazy imports for `HtmlBookParser`, `MarkdownBookParser`, `UrlParser`
  - Pass `html_parser`, `md_parser`, `url_parser` to `IngestBookUseCase`
  - Change `file_path` argument to accept `str` (to handle URLs); detect URL vs file path
  - Update argument help text to mention HTML, Markdown, and URL support
- [x] Updated integration test `_make_ingest_use_case` for new parameters
- [x] Updated `test_all_codes_exist` to include `fetch_failed`

## 9.9 — Dependencies and fixtures

- [x] Add `markdown-it-py` to `dependencies` in `pyproject.toml`
- [x] Run `uv sync` to install new dependency
- [x] Create `shared/fixtures/sample_book.html` — a small HTML file with paragraphs and headings
- [x] Create `shared/fixtures/sample_book.md` — a small Markdown file with H1, H2, paragraphs, and formatting

## 9.10 — Delta specs: update book-parsing and book-ingestion specs

- [x] Create delta spec `openspec/changes/html-md-url-parsers/specs/book-parsing/delta.md`:
  - Requirement: HTML parser extracts text as single page
  - Requirement: Markdown parser extracts text with heading-based page boundaries
  - Requirement: URL parser fetches and extracts text as single page
  - Scenarios for each format including error cases
- [x] Create delta spec `openspec/changes/html-md-url-parsers/specs/book-ingestion/delta.md`:
  - Update `IngestBookUseCase` spec for `.html`, `.md`, URL source support
  - Scenario: HTML file selects HTML parser
  - Scenario: Markdown file selects Markdown parser
  - Scenario: URL source uses URL parser
  - Scenario: URL fetch failure during ingestion

## 9.11 — Final verification

- [x] Run full test suite: `uv run pytest -x` — 365 passed
- [x] Run linter: `uv run ruff check .` — All checks passed
- [x] Run type checker: `uv run pyright` — 0 errors
- [x] Verify no dead code or unused imports
