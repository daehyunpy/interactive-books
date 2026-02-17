## Context

Phases 1–7 delivered the full Python CLI pipeline: PDF/TXT ingestion, embedding, vector search, and agentic chat. The `BookParser` protocol in `domain/protocols.py` defines `parse(file_path: Path) → list[PageContent]`. Two implementations exist: `infra/parsers/pdf.py` (PyMuPDF, one `PageContent` per physical page) and `infra/parsers/txt.py` (character-count estimated pages). The `IngestBookUseCase` in `app/ingest.py` takes named parser parameters (`pdf_parser`, `txt_parser`), selects by file extension, and orchestrates parse → chunk → persist. The `TextChunker` is format-agnostic — it accepts `list[PageContent]` and produces `list[ChunkData]`, so it requires no changes.

Phase 8 adds EPUB and DOCX parsers as Batch 1 of the multi-format expansion. Both formats produce `list[PageContent]` using format-appropriate "page" definitions (chapters for EPUB, heading sections for DOCX). The existing chunker and downstream pipeline work unchanged.

## Goals / Non-Goals

**Goals:**
- Parse DRM-free EPUB files into per-chapter logical pages using stdlib `zipfile` + `selectolax`
- Parse DOCX files into heading-based logical pages (H1 + H2 boundaries) using `python-docx`
- Detect DRM-protected EPUBs and reject with `BookError(DRM_PROTECTED)`
- Extract text from DOCX paragraphs and tables; ignore images and embedded objects
- Integrate both parsers into the ingestion pipeline with `.epub` and `.docx` support
- Add sample fixtures and comprehensive unit tests

**Non-Goals:**
- HTML, Markdown, or URL parsers — that is Phase 9 (Batch 2)
- Formal `PageMappingStrategy` protocol extraction — page mapping logic stays internal to each parser (consistent with existing PDF/TXT parsers); the protocol can be introduced when Batch 2 needs shared strategies
- EPUB metadata extraction (title, author from OPF) for `Book` entity — noted in product requirements but `Book` has no `format` or `author` fields; deferred to when the domain model evolves
- OCR for scanned pages in DOCX
- Nested resource resolution (images, linked files)
- EPUB DRM removal or support

## Decisions

### 1. EPUB page mapping: one page per chapter (spine order)

**Decision:** Each EPUB chapter (content document listed in the OPF spine) maps to one `PageContent`. Page numbers are 1-indexed in spine order.

**Rationale:** The technical design specifies "one page per chapter" for EPUB. This is the simplest approach and matches how readers think about ebook structure. Spine order preserves reading order as defined by the publisher. Long chapters may produce large `PageContent` objects, but the downstream chunker handles splitting.

**Alternatives considered:**
- Split long chapters into sub-pages: adds complexity, no clear benefit since the chunker already handles large text
- One page per XHTML file: some EPUBs have multiple files per chapter or vice versa; spine order is more reliable

### 2. EPUB parsing: stdlib zipfile + selectolax

**Decision:** Use Python's `zipfile` module to read the EPUB (which is a ZIP archive), parse the `META-INF/container.xml` to find the OPF file, parse the OPF to get spine order and content document paths, then use `selectolax` to strip XHTML tags from each content document.

**Rationale:** The technical design specifies this approach. EPUB is just a ZIP of XHTML files — no dedicated EPUB library needed. `selectolax` (Lexbor-based) is fast and already planned for the HTML parser in Phase 9, so adding it now shares a dependency. The alternative `ebooklib` library is heavier and less maintained.

### 3. EPUB DRM detection

**Decision:** Check for the presence of `META-INF/encryption.xml` in the EPUB ZIP. If present and non-trivial (contains `EncryptedData` elements), raise `BookError(BookErrorCode.DRM_PROTECTED)`.

**Rationale:** Product requirements mandate DRM-free only with clear rejection. `encryption.xml` is the standard indicator of DRM in EPUB files. This is a simple heuristic that catches the common cases (Adobe DRM, Apple FairPlay) without needing to decrypt anything.

### 4. DOCX page mapping: H1 + H2 heading boundaries

**Decision:** Split DOCX content into logical pages at H1 (`Heading 1`) and H2 (`Heading 2`) paragraph styles. Content before the first heading is page 1. Each subsequent heading starts a new page. If no headings exist, the entire document is one page.

**Rationale:** The technical design and product requirements both specify "H1 + H2 headings define page boundaries." This produces meaningful semantic sections for retrieval. Documents without headings degrade gracefully to a single page.

### 5. DOCX parsing: python-docx

**Decision:** Use `python-docx` to extract paragraph text and table cell text. Identify headings via paragraph style names (`Heading 1`, `Heading 2`). Ignore images, embedded objects, and complex formatting.

**Rationale:** The technical design specifies `python-docx`. It has a clean API for paragraph iteration and table extraction. Product requirements explicitly state images are ignored and table/formula content is text-only.

### 6. Parser selection via dict mapping (replaces if/else)

**Decision:** Replace the current if/else parser selection in `IngestBookUseCase.execute` with a `dict[str, BookParser]` mapping (`{".pdf": self._pdf_parser, ".txt": self._txt_parser, ".epub": self._epub_parser, ".docx": self._docx_parser}`).

**Rationale:** With four parsers, an if/else chain is unwieldy. A dict lookup is cleaner and scales to Phase 9 additions. The dict is built in `__init__` from the named parser parameters.

### 7. DRM_PROTECTED error code added to BookErrorCode

**Decision:** Add `DRM_PROTECTED = "drm_protected"` to `BookErrorCode` in `domain/errors.py`.

**Rationale:** Product requirements require a clear error message for DRM-protected files. A dedicated error code enables the CLI (and future app) to handle this case distinctly from generic parse failures.

## Risks / Trade-offs

**[Risk] EPUB DRM detection heuristic may false-positive on font obfuscation** → Mitigation: check for `EncryptedData` elements targeting content documents, not just the presence of `encryption.xml`. Font obfuscation typically only encrypts font files.

**[Risk] DOCX files without standard heading styles won't split into pages** → Mitigation: acceptable — degrades gracefully to a single page. Product requirements don't require custom style mapping.

**[Risk] selectolax may strip too aggressively (e.g., lose paragraph breaks)** → Mitigation: extract text node by node, joining with newlines between block elements, rather than using a single `.text()` call.

**[Trade-off] No EPUB metadata extraction** → `Book` entity has no `author` field. Extracting OPF metadata (title, author, etc.) would require domain model changes. Deferred until the domain model is extended for richer book metadata.

**[Trade-off] Page mapping logic inside parsers, not a formal protocol** → Keeps consistency with existing PDF/TXT parsers. The `PageMappingStrategy` protocol can be introduced when Batch 2 creates shared strategies (DOCX and Markdown share heading-based mapping).
