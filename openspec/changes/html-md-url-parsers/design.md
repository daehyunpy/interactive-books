## Context

Phases 1–8 delivered the full Python CLI pipeline: PDF/TXT/EPUB/DOCX ingestion, embedding, vector search, and agentic chat. The `BookParser` protocol in `domain/protocols.py` defines `parse(file_path: Path) → list[PageContent]`. Four implementations exist: `infra/parsers/pdf.py`, `infra/parsers/txt.py`, `infra/parsers/epub.py`, and `infra/parsers/docx.py`. The `IngestBookUseCase` in `app/ingest.py` takes named parser parameters and selects by file extension via a `dict[str, BookParser]` mapping. The `TextChunker` is format-agnostic and requires no changes.

Phase 9 adds HTML, Markdown, and URL parsers as Batch 2 of the multi-format expansion. HTML and Markdown are local file parsers that produce `list[PageContent]` via the existing `BookParser` protocol. The URL parser is fundamentally different — it involves network I/O and Content-Type detection — so it gets a dedicated `UrlParser` protocol rather than being forced through the file-path interface. The downstream pipeline (chunker, embeddings, retrieval) works unchanged.

## Goals / Non-Goals

**Goals:**
- Parse HTML files into a single logical page by stripping tags and extracting text using `selectolax` (already a dependency from Phase 8)
- Parse Markdown files into heading-based logical pages (H1 + H2 boundaries) using `markdown-it-py`
- Fetch a URL via `httpx`, validate Content-Type, extract text via `selectolax`, produce a single logical page
- Add `FETCH_FAILED` error code for URL-specific failures (network, auth, non-text content)
- Add `UrlParser` protocol to domain for URL-specific parsing
- Integrate all three into the ingestion pipeline with `.html`, `.md`, and URL support
- Extend `IngestBookUseCase.execute` signature to `source: Path | str` (Path for files, str for URLs)
- Add sample fixtures and comprehensive unit tests

**Non-Goals:**
- JavaScript-rendered content — static HTML only (v1 limitation per product requirements)
- URL crawling, depth limits, or multi-page assembly — single page fetch only
- Nested resource resolution (linked images, stylesheets, includes) — deferred to v2
- OCR for images in HTML or Markdown files
- MIME type sniffing beyond Content-Type header
- Formal `PageMappingStrategy` protocol extraction — page mapping logic stays internal to each parser, consistent with existing parsers

## Decisions

### 1. HTML page mapping: single page (entire document)

**Decision:** The entire HTML document maps to one `PageContent` with `page_number=1`.

**Rationale:** The technical design specifies "single logical page (entire document)" for HTML. Single-file HTML documents have no inherent page structure. The downstream chunker handles splitting large text into appropriately sized chunks.

**Alternatives considered:**
- Split by heading tags (H1/H2): adds complexity, inconsistent with how most HTML documents are structured (many use divs/sections rather than semantic headings)
- Split by character count: TXT parser already does this; no value in duplicating for HTML

### 2. HTML parsing: selectolax (already a dependency)

**Decision:** Use `selectolax` to strip HTML tags and extract text from the body element, using the same block-tag-aware text extraction approach as the EPUB parser.

**Rationale:** `selectolax` is already a project dependency (added in Phase 8 for EPUB parsing). It's fast (Lexbor-based) and the text extraction logic from `infra/parsers/epub.py` can be reused. No new dependency needed.

### 3. Markdown page mapping: H1 + H2 heading boundaries (same as DOCX)

**Decision:** Split Markdown content into logical pages at H1 (`#`) and H2 (`##`) headings. Content before the first heading is page 1. Each subsequent heading starts a new page. If no headings exist, the entire document is one page.

**Rationale:** The technical design specifies "H1 + H2 headings define page boundaries (same strategy as DOCX)" for Markdown. This produces meaningful semantic sections for retrieval and is consistent with the DOCX parser behavior.

### 4. Markdown parsing: markdown-it-py for AST, custom plain-text renderer

**Decision:** Use `markdown-it-py` to parse Markdown into an AST (token stream). Walk the tokens to: (a) detect H1/H2 headings for page splitting, and (b) extract plain text content by collecting text tokens and stripping formatting.

**Rationale:** The technical design specifies `markdown-it-py`. It's CommonMark-compliant and produces a token stream that can be walked to detect headings while simultaneously extracting text. This is cleaner than regex-based heading detection and handles edge cases (headings in code blocks, ATX vs setext styles).

**Alternatives considered:**
- Regex-based heading detection + raw text: fragile, fails on headings inside code fences
- Convert to HTML then strip tags: roundabout; loses heading boundary information during HTML conversion

### 5. URL parser: separate `UrlParser` protocol (not `BookParser`)

**Decision:** Create a `UrlParser` protocol in `domain/protocols.py` with `parse_url(url: str) → list[PageContent]`. The URL parser implementation in `infra/parsers/url.py` uses `httpx` to fetch and `selectolax` to extract text. It does not implement `BookParser`.

**Rationale:** The `BookParser` protocol is `parse(file_path: Path)` — URLs are not file paths. Forcing URLs through a Path-based interface would require saving to temp files and losing Content-Type information. A separate protocol is cleaner: it represents the genuine difference between "parse a local file" and "fetch and parse a remote resource." The `IngestBookUseCase` handles both cases via distinct code paths.

**Alternatives considered:**
- Force URL through `BookParser` by saving to temp file: loses Content-Type info, adds temp file management, couples network I/O with file parsing
- Expand `BookParser` to accept `Path | str`: breaks the clean interface for all existing parsers

### 6. URL Content-Type validation: accept text/html and text/plain only

**Decision:** After fetching the URL response, check the `Content-Type` header. Accept `text/html` (extract via selectolax) and `text/plain` (use raw text). Reject all other content types with `BookError(FETCH_FAILED)`.

**Rationale:** Product requirements state: "URL returns non-text: Reject with message explaining only text content is supported." Accepting only text/html and text/plain covers the vast majority of web pages and plain text URLs. PDFs, images, and other binary content types are rejected clearly.

### 7. URL error handling: FETCH_FAILED error code

**Decision:** Add `FETCH_FAILED = "fetch_failed"` to `BookErrorCode`. The URL parser raises this for: network errors (connection, timeout), non-2xx HTTP responses, unsupported Content-Type, and empty content.

**Rationale:** The error taxonomy in the technical design lists `fetch_failed` as a `BookError` case. URL-specific failures are distinct from parse failures (which indicate malformed local files). A dedicated error code enables the CLI and future app to surface URL-specific messages.

### 8. IngestBookUseCase: extend execute signature to `source: Path | str`

**Decision:** Change `execute(file_path: Path, title: str)` to `execute(source: Path | str, title: str)`. When `source` is a `str` starting with `http://` or `https://`, route to the `url_parser`. Otherwise, convert to `Path` and use the existing file-extension-based routing.

**Rationale:** The CLI command is `ingest <file|url>`. The use case must handle both. A union type is the simplest way to express this without creating a separate use case. The URL code path is small (delegate to `url_parser`) and shares the rest of the pipeline (chunking, persisting, embedding).

### 9. Shared text extraction: extract `_extract_block_text` to shared module

**Decision:** Move the `_extract_block_text` helper (currently in `infra/parsers/epub.py`) to a shared `infra/parsers/_html_text.py` module. Both the EPUB parser and the new HTML parser import from there. The URL parser also reuses it for HTML content.

**Rationale:** The EPUB parser and HTML parser both need the same selectolax-based block-tag-aware text extraction. Duplicating the logic violates DRY. A shared private module (prefixed with `_`) keeps the helper internal to the parsers package while avoiding duplication.

## Risks / Trade-offs

**[Risk] URL fetch may be slow or timeout** → Mitigation: use httpx with a reasonable timeout (30 seconds). On failure, raise `FETCH_FAILED` with a clear message. No retries (per product requirements: "Don't retry").

**[Risk] Content-Type header may be missing or incorrect** → Mitigation: if Content-Type is missing, attempt to parse as HTML (most common case). If Content-Type indicates a type we don't support, reject clearly.

**[Risk] HTML documents may be very large (multi-MB)** → Accepted: the downstream chunker handles splitting large text. Selectolax is fast enough for large documents. If this becomes an issue, a size limit can be added later.

**[Risk] Markdown files with non-standard heading syntax** → Mitigation: `markdown-it-py` is CommonMark-compliant and handles standard ATX (`#`) and setext (underline) headings. Non-standard syntax degrades gracefully to a single page.

**[Trade-off] No JavaScript rendering for HTML** → Accepted: product requirements explicitly state "HTML with JavaScript-rendered content: not supported in v1 (static HTML only)."

**[Trade-off] URL fetches only one page, no crawling** → Accepted: product requirements explicitly state "fetches one page; no crawling or link-following in v1."

**[Trade-off] Shared text extraction creates coupling between EPUB and HTML parsers** → Minimal risk: the shared module is a small, stable utility with no business logic. Both parsers need identical behavior. If they diverge in future, the module can be forked.
