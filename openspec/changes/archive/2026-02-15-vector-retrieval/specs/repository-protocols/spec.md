## MODIFIED Requirements

### RP-4: Domain types only

All protocol method signatures use domain types (Book, Chunk, SearchResult, EmbeddingVector, etc.), not raw dicts, tuples, or database-specific types. The `EmbeddingRepository.search` method returns `list[tuple[str, float]]` as a lightweight return type for chunk_id + distance pairs.
