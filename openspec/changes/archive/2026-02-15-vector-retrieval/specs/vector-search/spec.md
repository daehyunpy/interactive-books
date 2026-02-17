## ADDED Requirements

### Requirement: SearchResult value object represents a search hit

The domain layer SHALL define a `SearchResult` frozen dataclass in `domain/search_result.py` with fields: `chunk_id: str`, `content: str`, `start_page: int`, `end_page: int`, `distance: float`. The `distance` represents L2 distance (lower = more similar).

#### Scenario: Valid SearchResult creation
- **WHEN** `SearchResult(chunk_id="c1", content="text", start_page=1, end_page=2, distance=0.5)` is created
- **THEN** the object is created successfully with the given values

#### Scenario: SearchResult is immutable
- **WHEN** a `SearchResult` instance is created
- **THEN** its fields cannot be reassigned (frozen dataclass)

### Requirement: EmbeddingRepository search method performs KNN vector search

The `EmbeddingRepository` protocol SHALL include a `search(provider_name: str, dimension: int, book_id: str, query_vector: list[float], top_k: int) → list[tuple[str, float]]` method. It returns `(chunk_id, distance)` pairs ordered by ascending distance.

#### Scenario: Search returns nearest chunks
- **WHEN** `search(provider_name, dimension, book_id, query_vector, top_k=5)` is called
- **THEN** up to 5 `(chunk_id, distance)` pairs are returned, ordered by ascending distance

#### Scenario: Search with no embeddings
- **WHEN** `search` is called for a book with no embeddings
- **THEN** an empty list is returned

#### Scenario: Search respects book_id partition
- **WHEN** `search` is called with a specific book_id
- **THEN** only vectors belonging to that book are searched

### Requirement: sqlite-vec adapter implements KNN search

The `EmbeddingRepository` adapter in `infra/storage/embedding_repo.py` SHALL implement `search` using sqlite-vec's `MATCH` clause with `book_id` partition key filtering: `WHERE vector MATCH ? AND k = ? AND book_id = ?`.

#### Scenario: KNN query uses partition key
- **WHEN** `search` is called for a specific book
- **THEN** the sqlite-vec query includes `book_id = ?` for efficient partition-scoped search

#### Scenario: Results include chunk_id from auxiliary column
- **WHEN** search results are returned
- **THEN** each result includes the `chunk_id` auxiliary column value and the L2 distance
