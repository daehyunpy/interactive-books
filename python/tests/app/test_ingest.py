from pathlib import Path

import pytest
from interactive_books.app.ingest import IngestBookUseCase
from interactive_books.domain.book import Book, BookStatus
from interactive_books.domain.chunk import Chunk
from interactive_books.domain.chunk_data import ChunkData
from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.domain.page_content import PageContent
from interactive_books.domain.protocols import BookParser, TextChunker


class FakeBookRepository:
    def __init__(self) -> None:
        self.books: dict[str, Book] = {}

    def save(self, book: Book) -> None:
        self.books[book.id] = book

    def get(self, book_id: str) -> Book | None:
        return self.books.get(book_id)

    def get_all(self) -> list[Book]:
        return list(self.books.values())

    def delete(self, book_id: str) -> None:
        self.books.pop(book_id, None)


class FakeChunkRepository:
    def __init__(self) -> None:
        self.chunks: dict[str, list[Chunk]] = {}

    def save_chunks(self, book_id: str, chunks: list[Chunk]) -> None:
        self.chunks[book_id] = chunks

    def get_by_book(self, book_id: str) -> list[Chunk]:
        return self.chunks.get(book_id, [])

    def get_up_to_page(self, book_id: str, page: int) -> list[Chunk]:
        return [c for c in self.get_by_book(book_id) if c.start_page <= page]

    def delete_by_book(self, book_id: str) -> None:
        self.chunks.pop(book_id, None)


class FakeParser:
    def __init__(self, pages: list[PageContent] | None = None) -> None:
        self._pages = pages or [
            PageContent(page_number=1, text="Page one content."),
            PageContent(page_number=2, text="Page two content."),
        ]

    def parse(self, file_path: Path) -> list[PageContent]:
        return self._pages


class FailingParser:
    def parse(self, file_path: Path) -> list[PageContent]:
        raise BookError(BookErrorCode.PARSE_FAILED, "Parse failed")


class FakeChunker:
    def __init__(self, chunks: list[ChunkData] | None = None) -> None:
        self._chunks = chunks or [
            ChunkData(
                content="Page one content.", start_page=1, end_page=1, chunk_index=0
            ),
            ChunkData(
                content="Page two content.", start_page=2, end_page=2, chunk_index=1
            ),
        ]

    def chunk(self, pages: list[PageContent]) -> list[ChunkData]:
        return self._chunks


class FailingChunker:
    def chunk(self, pages: list[PageContent]) -> list[ChunkData]:
        raise BookError(BookErrorCode.PARSE_FAILED, "Chunking failed")


def make_use_case(
    *,
    pdf_parser: BookParser | None = None,
    txt_parser: BookParser | None = None,
    chunker: TextChunker | None = None,
    book_repo: FakeBookRepository | None = None,
    chunk_repo: FakeChunkRepository | None = None,
) -> tuple[IngestBookUseCase, FakeBookRepository, FakeChunkRepository]:
    br = book_repo or FakeBookRepository()
    cr = chunk_repo or FakeChunkRepository()
    return (
        IngestBookUseCase(
            pdf_parser=pdf_parser or FakeParser(),
            txt_parser=txt_parser or FakeParser(),
            chunker=chunker or FakeChunker(),
            book_repo=br,
            chunk_repo=cr,
        ),
        br,
        cr,
    )


class TestIngestSuccess:
    def test_successful_pdf_ingest_returns_ready_book(self, tmp_path: Path) -> None:
        use_case, _, _ = make_use_case()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        book = use_case.execute(pdf_path, "Test Book")
        assert book.status == BookStatus.READY
        assert book.title == "Test Book"

    def test_successful_txt_ingest_returns_ready_book(self, tmp_path: Path) -> None:
        use_case, _, _ = make_use_case()
        txt_path = tmp_path / "test.txt"
        txt_path.touch()
        book = use_case.execute(txt_path, "Text Book")
        assert book.status == BookStatus.READY

    def test_book_is_persisted(self, tmp_path: Path) -> None:
        use_case, book_repo, _ = make_use_case()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        book = use_case.execute(pdf_path, "Test Book")
        assert book_repo.get(book.id) is not None
        assert book_repo.get(book.id).status == BookStatus.READY  # type: ignore[union-attr]


class TestIngestUnsupportedFormat:
    def test_unsupported_format_raises_before_book_creation(
        self, tmp_path: Path
    ) -> None:
        use_case, book_repo, _ = make_use_case()
        path = tmp_path / "test.epub"
        path.touch()
        with pytest.raises(BookError) as exc_info:
            use_case.execute(path, "EPUB Book")
        assert exc_info.value.code == BookErrorCode.UNSUPPORTED_FORMAT
        assert len(book_repo.books) == 0


class TestIngestFailures:
    def test_parse_failure_sets_failed_status(self, tmp_path: Path) -> None:
        use_case, book_repo, _ = make_use_case(pdf_parser=FailingParser())
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        with pytest.raises(BookError):
            use_case.execute(pdf_path, "Bad Book")
        books = book_repo.get_all()
        assert len(books) == 1
        assert books[0].status == BookStatus.FAILED

    def test_chunk_failure_sets_failed_status(self, tmp_path: Path) -> None:
        use_case, book_repo, _ = make_use_case(chunker=FailingChunker())
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        with pytest.raises(BookError):
            use_case.execute(pdf_path, "Bad Book")
        books = book_repo.get_all()
        assert len(books) == 1
        assert books[0].status == BookStatus.FAILED


class TestIngestChunkAssociation:
    def test_chunks_linked_to_book(self, tmp_path: Path) -> None:
        chunks = [
            ChunkData(content="Chunk one.", start_page=1, end_page=1, chunk_index=0),
            ChunkData(content="Chunk two.", start_page=1, end_page=2, chunk_index=1),
            ChunkData(content="Chunk three.", start_page=2, end_page=2, chunk_index=2),
            ChunkData(content="Chunk four.", start_page=2, end_page=3, chunk_index=3),
            ChunkData(content="Chunk five.", start_page=3, end_page=3, chunk_index=4),
        ]
        use_case, _, chunk_repo = make_use_case(chunker=FakeChunker(chunks))
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        book = use_case.execute(pdf_path, "Test Book")
        saved_chunks = chunk_repo.get_by_book(book.id)
        assert len(saved_chunks) == 5
        for chunk in saved_chunks:
            assert chunk.book_id == book.id

    def test_chunk_ids_are_unique(self, tmp_path: Path) -> None:
        chunks = [
            ChunkData(content="Chunk one.", start_page=1, end_page=1, chunk_index=0),
            ChunkData(content="Chunk two.", start_page=2, end_page=2, chunk_index=1),
        ]
        use_case, _, chunk_repo = make_use_case(chunker=FakeChunker(chunks))
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        book = use_case.execute(pdf_path, "Test Book")
        saved_chunks = chunk_repo.get_by_book(book.id)
        ids = [c.id for c in saved_chunks]
        assert len(ids) == len(set(ids))
