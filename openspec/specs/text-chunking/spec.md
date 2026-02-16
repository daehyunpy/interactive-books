## ADDED Requirements

### Requirement: TextChunker protocol defines chunking contract
The domain layer SHALL define a `TextChunker` protocol with a method `chunk(pages: list[PageContent]) → list[ChunkData]`. The protocol SHALL be defined in `domain/protocols.py`.

#### Scenario: Protocol is defined in domain layer
- **WHEN** a developer imports from `domain/protocols.py`
- **THEN** `TextChunker` is available as a Protocol class with a `chunk` method

### Requirement: ChunkData value object represents a chunk with page mapping
The domain layer SHALL define a `ChunkData` frozen dataclass with `content: str`, `start_page: int`, `end_page: int`, and `chunk_index: int`. `start_page` MUST be >= 1. `end_page` MUST be >= `start_page`. `chunk_index` MUST be >= 0. `content` MUST be non-empty.

#### Scenario: Valid ChunkData creation
- **WHEN** `ChunkData(content="Some text", start_page=1, end_page=1, chunk_index=0)` is created
- **THEN** the object is created successfully

#### Scenario: Empty content rejected
- **WHEN** `ChunkData(content="", start_page=1, end_page=1, chunk_index=0)` is created
- **THEN** a `BookError` with code `PARSE_FAILED` is raised

#### Scenario: Invalid page range rejected
- **WHEN** `ChunkData(content="text", start_page=3, end_page=1, chunk_index=0)` is created
- **THEN** a `BookError` with code `PARSE_FAILED` is raised

### Requirement: Recursive chunker splits text by natural boundaries
The `RecursiveChunker` adapter SHALL implement `TextChunker`. It SHALL split text using a hierarchy of separators: paragraph (`\n\n`) first, then newline (`\n`), then sentence boundary, then word boundary. It SHALL accept configurable `max_tokens` (default: 500) and `overlap_tokens` (default: 100) parameters.

#### Scenario: Short text stays as single chunk
- **WHEN** pages with total text under `max_tokens` words are chunked
- **THEN** a single `ChunkData` is returned with `chunk_index=0`

#### Scenario: Text is split at paragraph boundaries
- **WHEN** pages contain text with multiple paragraphs totaling over `max_tokens` words
- **THEN** chunks are split at paragraph boundaries (`\n\n`) and each chunk is at most `max_tokens` words

#### Scenario: Chunks have correct page mapping
- **WHEN** page 1 has 400 words and page 2 has 400 words and `max_tokens=500`
- **THEN** at least one chunk has `start_page=1, end_page=2` (spanning both pages)

#### Scenario: Chunks have sequential indices
- **WHEN** text is split into N chunks
- **THEN** `chunk_index` values are 0, 1, 2, ..., N-1

### Requirement: Chunks overlap for context continuity
The `RecursiveChunker` SHALL include `overlap_tokens` words from the end of the previous chunk at the beginning of the next chunk.

#### Scenario: Overlap between consecutive chunks
- **WHEN** text is split into multiple chunks with `overlap_tokens=100`
- **THEN** the last ~100 words of chunk N appear at the beginning of chunk N+1

#### Scenario: First chunk has no leading overlap
- **WHEN** the first chunk is created
- **THEN** it starts from the beginning of the text with no prepended overlap

### Requirement: Empty pages are skipped during chunking
The chunker SHALL skip pages with empty text and not include them in chunk content or page mapping.

#### Scenario: Page with empty text is skipped
- **WHEN** pages include a `PageContent` with empty `text`
- **THEN** that page's content is excluded from chunks and its `page_number` does not appear in any chunk's page range

#### Scenario: All pages empty
- **WHEN** all pages have empty text
- **THEN** an empty list of `ChunkData` is returned
