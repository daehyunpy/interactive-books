from pathlib import Path

import pytest
from interactive_books.app.ingest import IngestBookUseCase
from interactive_books.domain.book import Book, BookStatus
from interactive_books.domain.chunk import Chunk
from interactive_books.domain.chunk_data import ChunkData
from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.domain.page_content import PageContent
from interactive_books.domain.protocols import BookParser, TextChunker, UrlParser


class FakeEmbedBookUseCase:
    def __init__(self, *, error: Exception | None = None) -> None:
        self._error = error
        self.last_book_id: str | None = None

    def execute(self, book_id: str) -> Book:
        self.last_book_id = book_id
        if self._error is not None:
            raise self._error
        return Book(id=book_id, title="embedded")


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

    def count_by_book(self, book_id: str) -> int:
        return len(self.chunks.get(book_id, []))

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


class FakeUrlParser:
    def __init__(self, pages: list[PageContent] | None = None) -> None:
        self._pages = pages or [
            PageContent(page_number=1, text="URL page content."),
        ]
        self.last_url: str | None = None

    def parse_url(self, url: str) -> list[PageContent]:
        self.last_url = url
        return self._pages


class FailingUrlParser:
    def parse_url(self, url: str) -> list[PageContent]:
        raise BookError(BookErrorCode.FETCH_FAILED, "Fetch failed")


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
    epub_parser: BookParser | None = None,
    docx_parser: BookParser | None = None,
    html_parser: BookParser | None = None,
    md_parser: BookParser | None = None,
    url_parser: UrlParser | None = None,
    chunker: TextChunker | None = None,
    book_repo: FakeBookRepository | None = None,
    chunk_repo: FakeChunkRepository | None = None,
    embed_use_case: FakeEmbedBookUseCase | None = None,
) -> tuple[IngestBookUseCase, FakeBookRepository, FakeChunkRepository]:
    br = book_repo or FakeBookRepository()
    cr = chunk_repo or FakeChunkRepository()
    return (
        IngestBookUseCase(
            pdf_parser=pdf_parser or FakeParser(),
            txt_parser=txt_parser or FakeParser(),
            epub_parser=epub_parser or FakeParser(),
            docx_parser=docx_parser or FakeParser(),
            html_parser=html_parser or FakeParser(),
            md_parser=md_parser or FakeParser(),
            url_parser=url_parser or FakeUrlParser(),  # type: ignore[arg-type]
            chunker=chunker or FakeChunker(),
            book_repo=br,
            chunk_repo=cr,
            embed_use_case=embed_use_case,  # type: ignore[arg-type]
        ),
        br,
        cr,
    )


class TestIngestSuccess:
    def test_successful_pdf_ingest_returns_ready_book(self, tmp_path: Path) -> None:
        use_case, _, _ = make_use_case()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        book, embed_error = use_case.execute(pdf_path, "Test Book")
        assert book.status == BookStatus.READY
        assert book.title == "Test Book"
        assert embed_error is None

    def test_successful_txt_ingest_returns_ready_book(self, tmp_path: Path) -> None:
        use_case, _, _ = make_use_case()
        txt_path = tmp_path / "test.txt"
        txt_path.touch()
        book, _ = use_case.execute(txt_path, "Text Book")
        assert book.status == BookStatus.READY

    def test_book_is_persisted(self, tmp_path: Path) -> None:
        use_case, book_repo, _ = make_use_case()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()
        book, _ = use_case.execute(pdf_path, "Test Book")
        assert book_repo.get(book.id) is not None
        assert book_repo.get(book.id).status == BookStatus.READY  # type: ignore[union-attr]


class TestIngestEpubSuccess:
    def test_successful_epub_ingest_returns_ready_book(
        self, tmp_path: Path
    ) -> None:
        use_case, _, _ = make_use_case()
        epub_path = tmp_path / "test.epub"
        epub_path.touch()
        book, embed_error = use_case.execute(epub_path, "EPUB Book")
        assert book.status == BookStatus.READY
        assert embed_error is None

    def test_epub_format_no_longer_rejected_as_unsupported(
        self, tmp_path: Path
    ) -> None:
        use_case, book_repo, _ = make_use_case()
        epub_path = tmp_path / "test.epub"
        epub_path.touch()
        book, _ = use_case.execute(epub_path, "EPUB Book")
        assert book_repo.get(book.id) is not None


class TestIngestDocxSuccess:
    def test_successful_docx_ingest_returns_ready_book(
        self, tmp_path: Path
    ) -> None:
        use_case, _, _ = make_use_case()
        docx_path = tmp_path / "test.docx"
        docx_path.touch()
        book, embed_error = use_case.execute(docx_path, "DOCX Book")
        assert book.status == BookStatus.READY
        assert embed_error is None

    def test_docx_format_no_longer_rejected_as_unsupported(
        self, tmp_path: Path
    ) -> None:
        use_case, book_repo, _ = make_use_case()
        docx_path = tmp_path / "test.docx"
        docx_path.touch()
        book, _ = use_case.execute(docx_path, "DOCX Book")
        assert book_repo.get(book.id) is not None


class DrmProtectedParser:
    def parse(self, file_path: Path) -> list[PageContent]:
        raise BookError(BookErrorCode.DRM_PROTECTED, "EPUB is DRM-protected")


class TestIngestDrmProtectedEpub:
    def test_drm_protected_epub_raises_drm_error(self, tmp_path: Path) -> None:
        use_case, _, _ = make_use_case(epub_parser=DrmProtectedParser())
        epub_path = tmp_path / "test.epub"
        epub_path.touch()
        with pytest.raises(BookError) as exc_info:
            use_case.execute(epub_path, "DRM Book")
        assert exc_info.value.code == BookErrorCode.DRM_PROTECTED


class TestIngestUnsupportedFormat:
    def test_unsupported_format_raises_before_book_creation(
        self, tmp_path: Path
    ) -> None:
        use_case, book_repo, _ = make_use_case()
        path = tmp_path / "test.xyz"
        path.touch()
        with pytest.raises(BookError) as exc_info:
            use_case.execute(path, "Unknown Book")
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
        book, _ = use_case.execute(pdf_path, "Test Book")
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
        book, _ = use_case.execute(pdf_path, "Test Book")
        saved_chunks = chunk_repo.get_by_book(book.id)
        ids = [c.id for c in saved_chunks]
        assert len(ids) == len(set(ids))


# ── Tests: Auto-Embed ───────────────────────────────────────────


class TestAutoEmbed:
    def test_auto_embed_success_returns_no_error(self, tmp_path: Path) -> None:
        embed = FakeEmbedBookUseCase()
        use_case, _, _ = make_use_case(embed_use_case=embed)
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        book, embed_error = use_case.execute(pdf_path, "Test Book")

        assert book.status == BookStatus.READY
        assert embed_error is None
        assert embed.last_book_id == book.id

    def test_auto_embed_failure_returns_exception_with_ready_book(
        self, tmp_path: Path
    ) -> None:
        failure = RuntimeError("Embedding API down")
        embed = FakeEmbedBookUseCase(error=failure)
        use_case, _, _ = make_use_case(embed_use_case=embed)
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        book, embed_error = use_case.execute(pdf_path, "Test Book")

        assert book.status == BookStatus.READY
        assert embed_error is failure

    def test_no_embed_use_case_returns_no_error(self, tmp_path: Path) -> None:
        use_case, _, _ = make_use_case()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        book, embed_error = use_case.execute(pdf_path, "Test Book")

        assert book.status == BookStatus.READY
        assert embed_error is None


# ── Tests: HTML/MD/URL Ingest ──────────────────────────────────


class TestIngestHtmlSuccess:
    def test_successful_html_ingest_returns_ready_book(
        self, tmp_path: Path
    ) -> None:
        use_case, _, _ = make_use_case()
        html_path = tmp_path / "test.html"
        html_path.touch()
        book, embed_error = use_case.execute(html_path, "HTML Book")
        assert book.status == BookStatus.READY
        assert embed_error is None


class TestIngestMarkdownSuccess:
    def test_successful_md_ingest_returns_ready_book(
        self, tmp_path: Path
    ) -> None:
        use_case, _, _ = make_use_case()
        md_path = tmp_path / "test.md"
        md_path.touch()
        book, embed_error = use_case.execute(md_path, "Markdown Book")
        assert book.status == BookStatus.READY
        assert embed_error is None


class TestIngestUrlSuccess:
    def test_successful_url_ingest_returns_ready_book(self) -> None:
        use_case, _, _ = make_use_case()
        book, embed_error = use_case.execute(
            "https://example.com/page", "URL Book"
        )
        assert book.status == BookStatus.READY
        assert embed_error is None

    def test_url_source_uses_url_parser(self) -> None:
        url_parser = FakeUrlParser()
        use_case, _, _ = make_use_case(url_parser=url_parser)  # type: ignore[arg-type]
        use_case.execute("https://example.com/article", "URL Book")
        assert url_parser.last_url == "https://example.com/article"

    def test_url_fetch_failure_propagates_error(self) -> None:
        use_case, book_repo, _ = make_use_case(
            url_parser=FailingUrlParser(),  # type: ignore[arg-type]
        )
        with pytest.raises(BookError) as exc_info:
            use_case.execute("https://example.com/bad", "Bad URL")
        assert exc_info.value.code == BookErrorCode.FETCH_FAILED
        books = book_repo.get_all()
        assert len(books) == 1
        assert books[0].status == BookStatus.FAILED


class TestIngestUnsupportedFormatStillRejected:
    def test_unsupported_extension_still_rejected(self, tmp_path: Path) -> None:
        use_case, book_repo, _ = make_use_case()
        path = tmp_path / "test.xyz"
        path.touch()
        with pytest.raises(BookError) as exc_info:
            use_case.execute(path, "Unknown Book")
        assert exc_info.value.code == BookErrorCode.UNSUPPORTED_FORMAT
