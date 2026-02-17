import pytest
from interactive_books.domain.embedding_vector import EmbeddingVector
from interactive_books.infra.storage.database import Database
from interactive_books.infra.storage.embedding_repo import EmbeddingRepository

PROVIDER = "openai"
DIMENSION = 1536


@pytest.fixture
def db() -> Database:
    return Database(":memory:", enable_vec=True)


@pytest.fixture
def repo(db: Database) -> EmbeddingRepository:
    return EmbeddingRepository(db)


class TestEnsureTable:
    def test_creates_virtual_table(
        self, repo: EmbeddingRepository, db: Database
    ) -> None:
        repo.ensure_table(PROVIDER, DIMENSION)

        cursor = db.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (f"embeddings_{PROVIDER}_{DIMENSION}",),
        )
        assert cursor.fetchone() is not None

    def test_idempotent(self, repo: EmbeddingRepository) -> None:
        repo.ensure_table(PROVIDER, DIMENSION)
        repo.ensure_table(PROVIDER, DIMENSION)  # should not raise


class TestSaveEmbeddings:
    def test_save_and_count(self, repo: EmbeddingRepository, db: Database) -> None:
        repo.ensure_table(PROVIDER, DIMENSION)

        embeddings = [
            EmbeddingVector(chunk_id="chunk-1", vector=[0.1] * DIMENSION),
            EmbeddingVector(chunk_id="chunk-2", vector=[0.2] * DIMENSION),
        ]
        repo.save_embeddings(PROVIDER, DIMENSION, "book-1", embeddings)

        cursor = db.connection.execute(
            f"SELECT count(*) FROM embeddings_{PROVIDER}_{DIMENSION}"
        )
        assert cursor.fetchone()[0] == 2


class TestDeleteByBook:
    def test_deletes_only_target_book(
        self, repo: EmbeddingRepository, db: Database
    ) -> None:
        repo.ensure_table(PROVIDER, DIMENSION)

        book1_embeddings = [
            EmbeddingVector(chunk_id="b1-c1", vector=[0.1] * DIMENSION),
        ]
        book2_embeddings = [
            EmbeddingVector(chunk_id="b2-c1", vector=[0.2] * DIMENSION),
        ]
        repo.save_embeddings(PROVIDER, DIMENSION, "book-1", book1_embeddings)
        repo.save_embeddings(PROVIDER, DIMENSION, "book-2", book2_embeddings)

        repo.delete_by_book(PROVIDER, DIMENSION, "book-1")

        cursor = db.connection.execute(
            f"SELECT count(*) FROM embeddings_{PROVIDER}_{DIMENSION}"
        )
        assert cursor.fetchone()[0] == 1


SEARCH_DIM = 3


class TestSearch:
    def _seed_vectors(self, repo: EmbeddingRepository, book_id: str) -> None:
        """Seed 3 vectors in 3D space with known distances from [1,0,0]."""
        repo.ensure_table(PROVIDER, SEARCH_DIM)
        embeddings = [
            EmbeddingVector(chunk_id="close", vector=[0.9, 0.0, 0.0]),
            EmbeddingVector(chunk_id="mid", vector=[0.5, 0.5, 0.0]),
            EmbeddingVector(chunk_id="far", vector=[0.0, 1.0, 0.0]),
        ]
        repo.save_embeddings(PROVIDER, SEARCH_DIM, book_id, embeddings)

    def test_returns_nearest_chunks_ordered_by_distance(
        self, repo: EmbeddingRepository
    ) -> None:
        self._seed_vectors(repo, "book-1")

        results = repo.search(PROVIDER, SEARCH_DIM, "book-1", [1.0, 0.0, 0.0], top_k=3)

        assert len(results) == 3
        chunk_ids = [r[0] for r in results]
        assert chunk_ids == ["close", "mid", "far"]
        # distances should be ascending
        distances = [r[1] for r in results]
        assert distances[0] < distances[1] < distances[2]

    def test_respects_top_k(self, repo: EmbeddingRepository) -> None:
        self._seed_vectors(repo, "book-1")

        results = repo.search(PROVIDER, SEARCH_DIM, "book-1", [1.0, 0.0, 0.0], top_k=2)

        assert len(results) == 2
        assert results[0][0] == "close"
        assert results[1][0] == "mid"

    def test_returns_empty_for_no_embeddings(self, repo: EmbeddingRepository) -> None:
        repo.ensure_table(PROVIDER, SEARCH_DIM)

        results = repo.search(PROVIDER, SEARCH_DIM, "book-1", [1.0, 0.0, 0.0], top_k=5)

        assert results == []

    def test_respects_book_id_partition(self, repo: EmbeddingRepository) -> None:
        self._seed_vectors(repo, "book-1")
        # Add a very close vector for book-2
        repo.save_embeddings(
            PROVIDER,
            SEARCH_DIM,
            "book-2",
            [EmbeddingVector(chunk_id="b2-close", vector=[0.99, 0.0, 0.0])],
        )

        results = repo.search(PROVIDER, SEARCH_DIM, "book-1", [1.0, 0.0, 0.0], top_k=5)

        chunk_ids = [r[0] for r in results]
        assert "b2-close" not in chunk_ids
        assert len(results) == 3  # only book-1's vectors


class TestHasEmbeddings:
    def test_returns_true_when_embeddings_exist(
        self, repo: EmbeddingRepository
    ) -> None:
        repo.ensure_table(PROVIDER, DIMENSION)
        embeddings = [EmbeddingVector(chunk_id="c1", vector=[0.1] * DIMENSION)]
        repo.save_embeddings(PROVIDER, DIMENSION, "book-1", embeddings)

        assert repo.has_embeddings("book-1", PROVIDER, DIMENSION) is True

    def test_returns_false_when_no_embeddings(self, repo: EmbeddingRepository) -> None:
        repo.ensure_table(PROVIDER, DIMENSION)

        assert repo.has_embeddings("book-1", PROVIDER, DIMENSION) is False

    def test_returns_false_after_deletion(self, repo: EmbeddingRepository) -> None:
        repo.ensure_table(PROVIDER, DIMENSION)
        embeddings = [EmbeddingVector(chunk_id="c1", vector=[0.1] * DIMENSION)]
        repo.save_embeddings(PROVIDER, DIMENSION, "book-1", embeddings)
        repo.delete_by_book(PROVIDER, DIMENSION, "book-1")

        assert repo.has_embeddings("book-1", PROVIDER, DIMENSION) is False
