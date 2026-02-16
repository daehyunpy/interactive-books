## MODIFIED Requirements

### ES-1: EmbeddingRepository protocol defines vector storage contract

The domain layer SHALL define an `EmbeddingRepository` protocol in `domain/protocols.py` with methods:

- `ensure_table(provider_name: str, dimension: int) → None` — create a per-provider vector table if it does not exist
- `save_embeddings(provider_name: str, dimension: int, book_id: str, embeddings: list[EmbeddingVector]) → None` — store vectors
- `delete_by_book(provider_name: str, dimension: int, book_id: str) → None` — delete all vectors for a book
- `has_embeddings(book_id: str, provider_name: str, dimension: int) → bool` — check if a book has stored vectors
- `search(provider_name: str, dimension: int, book_id: str, query_vector: list[float], top_k: int) → list[tuple[str, float]]` — KNN vector search returning (chunk_id, distance) pairs
