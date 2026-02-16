from interactive_books.domain.book import Book
from interactive_books.domain.chunk import Chunk
from interactive_books.infra.storage.book_repo import BookRepository
from interactive_books.infra.storage.chunk_repo import ChunkRepository
from interactive_books.infra.storage.database import Database


def _make_book(db: Database, book_id: str = "b1") -> None:
    repo = BookRepository(db)
    repo.save(Book(id=book_id, title="Test Book"))


class TestChunkRepository:
    def test_save_and_get_by_book(self, db: Database) -> None:
        _make_book(db)
        repo = ChunkRepository(db)
        chunks = [
            Chunk(id="c1", book_id="b1", content="First", start_page=1, end_page=1, chunk_index=0),
            Chunk(id="c2", book_id="b1", content="Second", start_page=2, end_page=3, chunk_index=1),
        ]
        repo.save_chunks("b1", chunks)

        loaded = repo.get_by_book("b1")
        assert len(loaded) == 2
        assert loaded[0].id == "c1"
        assert loaded[1].id == "c2"

    def test_get_by_book_ordered_by_chunk_index(self, db: Database) -> None:
        _make_book(db)
        repo = ChunkRepository(db)
        # Insert in reverse order
        chunks = [
            Chunk(id="c2", book_id="b1", content="Second", start_page=2, end_page=2, chunk_index=1),
            Chunk(id="c1", book_id="b1", content="First", start_page=1, end_page=1, chunk_index=0),
        ]
        repo.save_chunks("b1", chunks)

        loaded = repo.get_by_book("b1")
        assert loaded[0].chunk_index == 0
        assert loaded[1].chunk_index == 1

    def test_get_by_book_empty(self, db: Database) -> None:
        _make_book(db)
        repo = ChunkRepository(db)
        assert repo.get_by_book("b1") == []

    def test_get_up_to_page(self, db: Database) -> None:
        _make_book(db)
        repo = ChunkRepository(db)
        chunks = [
            Chunk(id="c1", book_id="b1", content="Page 1", start_page=1, end_page=1, chunk_index=0),
            Chunk(id="c2", book_id="b1", content="Page 2", start_page=2, end_page=3, chunk_index=1),
            Chunk(id="c3", book_id="b1", content="Page 5", start_page=5, end_page=7, chunk_index=2),
        ]
        repo.save_chunks("b1", chunks)

        result = repo.get_up_to_page("b1", 3)
        assert len(result) == 2
        assert {c.id for c in result} == {"c1", "c2"}

    def test_get_up_to_page_returns_all_when_page_is_high(self, db: Database) -> None:
        _make_book(db)
        repo = ChunkRepository(db)
        chunks = [
            Chunk(id="c1", book_id="b1", content="A", start_page=1, end_page=1, chunk_index=0),
            Chunk(id="c2", book_id="b1", content="B", start_page=2, end_page=2, chunk_index=1),
        ]
        repo.save_chunks("b1", chunks)

        result = repo.get_up_to_page("b1", 100)
        assert len(result) == 2

    def test_get_up_to_page_ordered_by_chunk_index(self, db: Database) -> None:
        _make_book(db)
        repo = ChunkRepository(db)
        chunks = [
            Chunk(id="c2", book_id="b1", content="B", start_page=2, end_page=2, chunk_index=1),
            Chunk(id="c1", book_id="b1", content="A", start_page=1, end_page=1, chunk_index=0),
        ]
        repo.save_chunks("b1", chunks)

        result = repo.get_up_to_page("b1", 5)
        assert result[0].chunk_index == 0
        assert result[1].chunk_index == 1

    def test_delete_by_book(self, db: Database) -> None:
        _make_book(db)
        repo = ChunkRepository(db)
        chunks = [
            Chunk(id="c1", book_id="b1", content="A", start_page=1, end_page=1, chunk_index=0),
        ]
        repo.save_chunks("b1", chunks)
        repo.delete_by_book("b1")
        assert repo.get_by_book("b1") == []

    def test_chunks_scoped_to_book(self, db: Database) -> None:
        _make_book(db, "b1")
        _make_book(db, "b2")
        repo = ChunkRepository(db)
        repo.save_chunks("b1", [
            Chunk(id="c1", book_id="b1", content="Book 1", start_page=1, end_page=1, chunk_index=0),
        ])
        repo.save_chunks("b2", [
            Chunk(id="c2", book_id="b2", content="Book 2", start_page=1, end_page=1, chunk_index=0),
        ])

        b1_chunks = repo.get_by_book("b1")
        assert len(b1_chunks) == 1
        assert b1_chunks[0].id == "c1"
