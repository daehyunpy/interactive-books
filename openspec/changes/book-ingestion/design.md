## Context

Phase 2 delivered the domain model (`Book`, `Chunk`, `ChatMessage`), error types, repository protocols (`BookRepository`, `ChunkRepository`), and SQLite storage adapters. The `Book` aggregate root already has status transitions (PENDING → INGESTING → READY/FAILED) and the `Chunk` value object validates page ranges.

Phase 3 fills the pipeline gap: getting content *into* the system. Without ingestion, the repositories are empty and Phases 4–7 have nothing to work with.

The technical design document specifies: PyMuPDF for PDF parsing, recursive chunking (paragraph → sentence → token limit), and an application-layer use case that orchestrates the flow.

## Goals / Non-Goals

**Goals:**
- Parse PDF files into per-page text with reliable page boundaries using PyMuPDF
- Parse TXT files into estimated pages by character count
- Split extracted text into overlapping chunks (~500 tokens, ~100 token overlap) preserving page mapping
- Orchestrate the full ingest pipeline (parse → chunk → persist) with proper `Book` status transitions
- Wire a `cli ingest <file>` command for prototyping and debugging
- Reject unsupported file formats with clear error messages
- Handle partial parse failures gracefully (skip unparseable pages, mark which are missing)

**Non-Goals:**
- Embedding generation — that is Phase 4
- EPUB support — that is P2 scope per product requirements
- OCR for scanned PDFs — explicitly a non-goal in v1
- Background/async ingestion — Phase 3 runs synchronously; async is a Phase 6–7 concern
- CLI polish (progress bars, --verbose output) — Phase 7 scope

## Decisions

### 1. BookParser returns a list of PageContent, not raw text

**Decision:** `BookParser.parse(file_path) → list[PageContent]` where `PageContent` is a value object with `page_number: int` and `text: str`.

**Rationale:** Returning structured per-page data preserves page boundaries for the chunker. If we returned a single concatenated string, page mapping would require a second pass. This also makes the parser testable in isolation — assert on page count and per-page content.

**Alternatives considered:**
- Single string with page markers: fragile, parser-specific marker format
- Dict of page_number → text: less type-safe than a dedicated value object

### 2. TextChunker takes page-aware input

**Decision:** `TextChunker.chunk(pages: list[PageContent]) → list[ChunkData]` where `ChunkData` is a value object with `content: str`, `start_page: int`, `end_page: int`, `chunk_index: int`.

**Rationale:** The chunker needs page boundaries to assign `start_page`/`end_page` to each chunk. Passing structured page data avoids re-parsing page boundaries inside the chunker.

**Alternatives considered:**
- Chunker receives raw text + separate page boundary map: more complex API surface, same result

### 3. Recursive chunking strategy

**Decision:** Split by paragraph (`\n\n`) first, then by newline (`\n`), then by sentence boundary, then by word boundary if a single sentence exceeds the token limit. Overlap by pulling tokens from the end of the previous chunk.

**Rationale:** This is the simplest chunking strategy that preserves semantic coherence. Paragraph boundaries are the strongest natural break points. The technical design specifies this approach and names it as the "first implementation" for the TextChunker abstraction.

**Alternatives considered:**
- Sentence-only splitting: loses paragraph-level coherence
- Semantic chunking (embedding-based): requires embeddings, which is Phase 4 — circular dependency

### 4. Token counting via simple word-based approximation

**Decision:** Use `len(text.split())` as a rough token proxy for chunking decisions. No tokenizer dependency.

**Rationale:** Chunking only needs approximate sizing. The exact token count matters for LLM context windows (Phase 6), not for chunk boundaries. Adding tiktoken or similar adds a dependency for marginal benefit at this stage.

**Alternatives considered:**
- tiktoken: accurate but adds a dependency and is model-specific
- Character count: less intuitive than word count for "~500 tokens"

### 5. TXT page estimation by character count

**Decision:** For TXT files without page structure, divide total characters by a configurable `chars_per_page` constant (default: 3000, roughly one printed page). Label citations as "estimated page" in metadata.

**Rationale:** Product requirements specify this approach. The constant is configurable so it can be tuned. 3000 chars ≈ 500 words ≈ one printed page.

### 6. Value objects live in the domain layer, protocols in protocols.py

**Decision:** `PageContent` and `ChunkData` are domain value objects (frozen dataclasses). `BookParser` and `TextChunker` are protocols in `domain/protocols.py`.

**Rationale:** These are domain concepts — page boundaries and chunk structure are part of the ubiquitous language. Infrastructure adapters implement the protocols; the domain layer defines the contracts. This follows the existing pattern where `Book`, `Chunk`, and `ChatMessage` are in domain/ and `BookRepository`/`ChunkRepository` protocols are in `protocols.py`.

### 7. IngestBookUseCase orchestrates the pipeline

**Decision:** A single use case class `IngestBookUseCase` in `app/ingest.py` accepts `BookParser`, `TextChunker`, `BookRepository`, and `ChunkRepository` via constructor injection.

**Rationale:** The application layer orchestrates: create Book → start_ingestion → parse → chunk → save_chunks → complete_ingestion (or fail_ingestion on error). This keeps domain logic in domain objects and wiring in the app layer.

### 8. File format detection by extension

**Decision:** Detect file format from the file extension (`.pdf`, `.txt`). Reject anything else with `BookError(UNSUPPORTED_FORMAT)`.

**Rationale:** Simple, reliable for v1 scope (PDF + TXT only). MIME-type detection is overkill when we support two formats. The use case selects the appropriate parser based on extension.

## Risks / Trade-offs

**[Risk] PyMuPDF may produce poor text for some PDFs** → Mitigation: skip unparseable pages, track which pages failed, and log warnings. The product requirements explicitly call for partial ingestion with user notification.

**[Risk] Word-based token approximation may produce inconsistent chunk sizes** → Mitigation: acceptable for Phase 3. Phase 4+ can refine with a real tokenizer if needed. Overlap ensures no content is lost between chunks.

**[Risk] TXT page estimation is imprecise** → Mitigation: product requirements accept this trade-off. Citations are labeled "estimated page" to set user expectations.

**[Trade-off] No streaming/async ingestion** → Large books block the CLI. Acceptable for Phase 3 (debug tool). Async ingestion is a Phase 7 concern.

**[Trade-off] No duplicate book detection** → If the user ingests the same file twice, two Book records are created. Acceptable for v1; dedup can be added later.
