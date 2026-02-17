## 1. Domain Error Code

- [ ] 1.1 Add `DRM_PROTECTED = "drm_protected"` to `BookErrorCode` in `domain/errors.py`
- [ ] 1.2 Write test for `BookError` with `DRM_PROTECTED` code (construction, message propagation)

## 2. Dependencies

- [ ] 2.1 Add `selectolax` to `pyproject.toml` dependencies
- [ ] 2.2 Add `python-docx` to `pyproject.toml` dependencies
- [ ] 2.3 Run `uv sync` to install new dependencies

## 3. EPUB Parser

- [ ] 3.1 Implement `BookParser` in `infra/parsers/epub.py` — read EPUB ZIP, parse `META-INF/container.xml` for OPF path, parse OPF for spine-ordered content document paths, use `selectolax` to strip XHTML tags from each content document, return one `PageContent` per chapter (1-indexed by spine order)
- [ ] 3.2 Add DRM detection in EPUB parser — check for presence of `META-INF/encryption.xml`; if it exists (regardless of contents), raise `BookError(BookErrorCode.DRM_PROTECTED)`
- [ ] 3.3 Handle EPUB error cases — file not found raises `BookError(PARSE_FAILED)`, invalid/corrupted ZIP raises `BookError(PARSE_FAILED)`, EPUB with no content documents raises `BookError(PARSE_FAILED)`
- [ ] 3.4 Write tests for EPUB parser using programmatically generated EPUBs in conftest: multi-chapter EPUB, single-chapter EPUB, chapter with only whitespace (included with empty text), file not found, invalid ZIP, DRM-protected EPUB rejection (encryption.xml present), EPUB with no chapters

## 4. DOCX Parser

- [ ] 4.1 Implement `BookParser` in `infra/parsers/docx.py` — use `python-docx` to iterate paragraphs and tables, split at `Heading 1` and `Heading 2` styles, content before first heading is page 1, each heading starts a new page, extract table cell text row by row, return `list[PageContent]` with 1-indexed page numbers
- [ ] 4.2 Handle DOCX with no headings — entire document content is one `PageContent` with `page_number=1`
- [ ] 4.3 Handle DOCX error cases — file not found raises `BookError(PARSE_FAILED)`, invalid/corrupted DOCX raises `BookError(PARSE_FAILED)`, empty DOCX (no text content) raises `BookError(PARSE_FAILED)`
- [ ] 4.4 Write tests for DOCX parser using programmatically generated DOCX in conftest: multi-section DOCX with H1 and H2 headings, DOCX with no headings (single page), DOCX with tables, DOCX with mixed content (paragraphs + tables + headings), empty DOCX, file not found, invalid DOCX file

## 5. Ingestion Pipeline Integration

- [ ] 5.1 Extend `IngestBookUseCase.__init__` to accept `epub_parser: BookParser` and `docx_parser: BookParser` parameters
- [ ] 5.2 Add `.epub` and `.docx` to `SUPPORTED_EXTENSIONS` in `app/ingest.py`
- [ ] 5.3 Replace if/else parser selection with `dict[str, BookParser]` mapping in `IngestBookUseCase`
- [ ] 5.4 Update existing ingest use case tests: add EPUB and DOCX success paths, add DRM-protected EPUB rejection test, verify `.epub` and `.docx` are no longer rejected as unsupported

## 6. CLI Wiring

- [ ] 6.1 Wire `EpubBookParser` and `DocxBookParser` imports in `main.py` ingest command (lazy imports, aliased)
- [ ] 6.2 Pass new parsers to `IngestBookUseCase` constructor in `main.py`
- [ ] 6.3 Update CLI help text to mention EPUB and DOCX support

## 7. Shared Test Fixtures

- [ ] 7.1 Create `shared/fixtures/sample_book.epub` — a small static multi-chapter EPUB checked into the repo for integration testing
- [ ] 7.2 Create `shared/fixtures/sample_book.docx` — a small static multi-section DOCX with headings checked into the repo for integration testing

## 8. Spec Updates

- [ ] 8.1 Update `openspec/specs/book-parsing/spec.md` — add EPUB parser requirements (spine-order chapters, DRM rejection, error handling) and DOCX parser requirements (H1+H2 page mapping, table text extraction, error handling)
- [ ] 8.2 Update `openspec/specs/book-ingestion/spec.md` — extend supported formats to include `.epub` and `.docx`, update parser selection description, add DRM-related scenario

## 9. Verification

- [ ] 9.1 Run full test suite (`uv run pytest -x`), lint (`uv run ruff check .`), and type check (`uv run pyright`) — all passing
