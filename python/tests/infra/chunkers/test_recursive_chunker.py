import pytest
from interactive_books.domain.page_content import PageContent
from interactive_books.infra.chunkers.recursive import RecursiveChunker


class TestRecursiveChunkerSingleChunk:
    def test_short_text_produces_single_chunk(self) -> None:
        pages = [PageContent(page_number=1, text="Hello world. This is a short text.")]
        chunker = RecursiveChunker(max_tokens=500, overlap_tokens=100)
        chunks = chunker.chunk(pages)
        assert len(chunks) == 1
        assert chunks[0].chunk_index == 0
        assert chunks[0].start_page == 1
        assert chunks[0].end_page == 1

    def test_single_chunk_contains_all_text(self) -> None:
        pages = [PageContent(page_number=1, text="Hello world.")]
        chunker = RecursiveChunker(max_tokens=500, overlap_tokens=100)
        chunks = chunker.chunk(pages)
        assert "Hello world." in chunks[0].content


class TestRecursiveChunkerParagraphSplits:
    def test_splits_at_paragraph_boundaries(self) -> None:
        para1 = "Word " * 15
        para2 = "Other " * 15
        text = para1.strip() + "\n\n" + para2.strip()
        pages = [PageContent(page_number=1, text=text)]
        chunker = RecursiveChunker(max_tokens=20, overlap_tokens=0)
        chunks = chunker.chunk(pages)
        assert len(chunks) >= 2

    def test_each_chunk_respects_max_tokens(self) -> None:
        text = "\n\n".join(["Word " * 10 for _ in range(5)])
        pages = [PageContent(page_number=1, text=text)]
        chunker = RecursiveChunker(max_tokens=15, overlap_tokens=0)
        chunks = chunker.chunk(pages)
        for chunk in chunks:
            word_count = len(chunk.content.split())
            assert word_count <= 15 + 5  # allow small buffer for boundary splits


class TestRecursiveChunkerPageSpanning:
    def test_chunk_spans_multiple_pages(self) -> None:
        pages = [
            PageContent(page_number=1, text="Word " * 400),
            PageContent(page_number=2, text="Word " * 400),
        ]
        chunker = RecursiveChunker(max_tokens=500, overlap_tokens=100)
        chunks = chunker.chunk(pages)
        has_spanning = any(c.start_page != c.end_page for c in chunks)
        assert has_spanning or len(chunks) >= 2

    def test_page_numbers_are_correct(self) -> None:
        pages = [
            PageContent(page_number=1, text="First page content."),
            PageContent(page_number=2, text="Second page content."),
        ]
        chunker = RecursiveChunker(max_tokens=500, overlap_tokens=0)
        chunks = chunker.chunk(pages)
        assert chunks[0].start_page == 1
        if len(chunks) == 1:
            assert chunks[0].end_page == 2


class TestRecursiveChunkerSequentialIndices:
    def test_chunk_indices_are_sequential(self) -> None:
        text = "\n\n".join(["Paragraph " * 20 for _ in range(5)])
        pages = [PageContent(page_number=1, text=text)]
        chunker = RecursiveChunker(max_tokens=30, overlap_tokens=0)
        chunks = chunker.chunk(pages)
        assert len(chunks) >= 2
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i


class TestRecursiveChunkerOverlap:
    def test_overlap_between_consecutive_chunks(self) -> None:
        text = " ".join([f"word{i}" for i in range(100)])
        pages = [PageContent(page_number=1, text=text)]
        chunker = RecursiveChunker(max_tokens=30, overlap_tokens=10)
        chunks = chunker.chunk(pages)
        assert len(chunks) >= 2
        chunk0_words = chunks[0].content.split()
        chunk1_words = chunks[1].content.split()
        overlap_words = chunk0_words[-10:]
        chunk1_start = chunk1_words[:10]
        common = set(overlap_words) & set(chunk1_start)
        assert len(common) > 0

    def test_first_chunk_has_no_leading_overlap(self) -> None:
        text = " ".join([f"word{i}" for i in range(100)])
        pages = [PageContent(page_number=1, text=text)]
        chunker = RecursiveChunker(max_tokens=30, overlap_tokens=10)
        chunks = chunker.chunk(pages)
        assert chunks[0].content.startswith("word0")


class TestRecursiveChunkerEmptyPages:
    def test_empty_pages_are_skipped(self) -> None:
        pages = [
            PageContent(page_number=1, text="Real content here."),
            PageContent(page_number=2, text=""),
            PageContent(page_number=3, text="More content here."),
        ]
        chunker = RecursiveChunker(max_tokens=500, overlap_tokens=0)
        chunks = chunker.chunk(pages)
        for chunk in chunks:
            if chunk.start_page == 2 and chunk.end_page == 2:
                pytest.fail("Empty page 2 should not be the sole page in a chunk")

    def test_all_pages_empty_returns_empty_list(self) -> None:
        pages = [
            PageContent(page_number=1, text=""),
            PageContent(page_number=2, text=""),
        ]
        chunker = RecursiveChunker(max_tokens=500, overlap_tokens=0)
        chunks = chunker.chunk(pages)
        assert chunks == []
