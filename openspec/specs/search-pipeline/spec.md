# search-pipeline

Search orchestration use case with page filtering and CLI integration. Connects embedding, vector search, and chunk retrieval into a complete search pipeline.

## Requirements

### SPL-1: SearchBooksUseCase orchestrates vector search with page filtering

The application layer SHALL provide a `SearchBooksUseCase` class in `app/search.py` that accepts `EmbeddingProvider`, `BookRepository`, `ChunkRepository`, and `EmbeddingRepository` via constructor injection. It SHALL expose an `execute(book_id: str, query: str, top_k: int = 5) → list[SearchResult]` method.

#### Scenario: Successful search returns ranked results

- **WHEN** `execute` is called with a valid book ID and query
- **THEN** the query is embedded, KNN search is performed, and results are returned as `SearchResult` objects ordered by ascending distance

#### Scenario: Book not found

- **WHEN** `execute` is called with a non-existent book ID
- **THEN** a `BookError` with code `NOT_FOUND` is raised

#### Scenario: Book has no embeddings

- **WHEN** `execute` is called for a book without embeddings
- **THEN** a `BookError` with code `INVALID_STATE` is raised with a message indicating no embeddings exist

#### Scenario: Search returns at most top_k results

- **WHEN** `execute` is called with `top_k=3`
- **THEN** at most 3 `SearchResult` objects are returned

### SPL-2: Page filtering scopes results to reader's current position

When `book.current_page > 0`, the use case SHALL filter results to only include chunks where `start_page <= current_page`. When `current_page == 0` (no position set), all chunks are eligible.

#### Scenario: Page filtering active

- **WHEN** a book has `current_page = 50` and search returns chunks from pages 1-100
- **THEN** only chunks with `start_page <= 50` are included in results

#### Scenario: Page filtering inactive

- **WHEN** a book has `current_page = 0`
- **THEN** all chunks are eligible regardless of page number

#### Scenario: Over-fetch compensates for page filtering

- **WHEN** page filtering is active
- **THEN** the use case requests `top_k * 3` from the vector search to ensure enough results survive filtering

### SPL-3: CLI search command wires the retrieval pipeline

The CLI SHALL provide a `search` command that accepts a book ID and query string. It SHALL print each result's page range, distance score, and a content preview. Validates `OPENAI_API_KEY` using the shared `_require_env` helper. Uses `_open_db` helper for database setup. When `--verbose` is enabled, prints the embedding provider name, dimension, number of results, and search duration.

#### Scenario: Search via CLI

- **WHEN** `cli search <book-id> <query>` is executed
- **THEN** the search results are printed showing page range, distance, and content preview for each result

#### Scenario: Search with custom top-k

- **WHEN** `cli search <book-id> <query> --top-k 10` is executed
- **THEN** up to 10 results are returned

#### Scenario: Search with no results

- **WHEN** the search returns zero results
- **THEN** a message is printed indicating no results were found

#### Scenario: Search with invalid book ID

- **WHEN** `cli search <invalid-id> <query>` is executed
- **THEN** an error message is displayed indicating the book was not found
