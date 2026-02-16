# embedding-storage

Vector storage contract and sqlite-vec adapter. Defines the `EmbeddingRepository` protocol in the domain layer, with a sqlite-vec implementation using per-provider virtual tables.

## Requirements

### ES-1: EmbeddingRepository protocol defines vector storage contract

The domain layer SHALL define an `EmbeddingRepository` protocol in `domain/protocols.py` with methods:

- `ensure_table(provider_name: str, dimension: int) → None` — create a per-provider vector table if it does not exist
- `save_embeddings(provider_name: str, dimension: int, book_id: str, embeddings: list[EmbeddingVector]) → None` — store vectors
- `delete_by_book(provider_name: str, dimension: int, book_id: str) → None` — delete all vectors for a book
- `has_embeddings(book_id: str, provider_name: str, dimension: int) → bool` — check if a book has stored vectors
- `search(provider_name: str, dimension: int, book_id: str, query_vector: list[float], top_k: int) → list[tuple[str, float]]` — KNN vector search returning (chunk_id, distance) pairs

#### Scenario: Protocol is defined in domain layer

- **WHEN** a developer imports from `domain/protocols.py`
- **THEN** `EmbeddingRepository` is available as a Protocol class with `ensure_table`, `save_embeddings`, `delete_by_book`, and `has_embeddings` methods

### ES-2: sqlite-vec storage adapter implements EmbeddingRepository

The system SHALL provide an `EmbeddingRepository` adapter in `infra/storage/embedding_repo.py` that uses sqlite-vec virtual tables for vector storage. Tables are per-provider, named `embeddings_{provider}_{dimension}` (e.g., `embeddings_openai_1536`).

#### Scenario: Ensure per-provider vector table

- **WHEN** `ensure_table(provider_name="openai", dimension=1536)` is called
- **THEN** a sqlite-vec virtual table named `embeddings_openai_1536` is created if it does not already exist, with `book_id`, `chunk_id`, and a vector column of 1536 dimensions

#### Scenario: Ensure table is idempotent

- **WHEN** `ensure_table` is called for a provider/dimension that already has a table
- **THEN** no error is raised and the existing table is unchanged

#### Scenario: Save embeddings for a book

- **WHEN** `save_embeddings(provider_name, dimension, book_id, embeddings)` is called with a list of `EmbeddingVector` objects
- **THEN** all vectors are inserted into the per-provider virtual table

#### Scenario: Delete embeddings for a book

- **WHEN** `delete_by_book(provider_name, dimension, book_id)` is called
- **THEN** all rows with that `book_id` are removed from the per-provider table

#### Scenario: Check embeddings exist — has embeddings

- **WHEN** `has_embeddings(book_id, provider_name, dimension)` is called for a book with stored vectors
- **THEN** `True` is returned

#### Scenario: Check embeddings exist — no embeddings

- **WHEN** `has_embeddings(book_id, provider_name, dimension)` is called for a book without stored vectors
- **THEN** `False` is returned

### ES-3: Per-provider table naming convention

The virtual table name SHALL follow the pattern `embeddings_{provider_name}_{dimension}` (e.g., `embeddings_openai_1536`). All books using the same provider and dimension share one table, filtered by `book_id`.

#### Scenario: Table name for OpenAI provider

- **WHEN** a provider with name `"openai"` and dimension `1536` is used
- **THEN** the table name is `embeddings_openai_1536`
