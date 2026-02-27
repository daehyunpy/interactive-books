import json
from pathlib import Path

import pytest
from interactive_books.app.summarize import (
    Section,
    SummarizeBookUseCase,
    group_chunks_into_sections,
)
from interactive_books.domain.book import Book
from interactive_books.domain.chunk import Chunk
from interactive_books.domain.errors import BookError, BookErrorCode, LLMError
from interactive_books.domain.prompt_message import PromptMessage
from interactive_books.domain.section_summary import SectionSummary
from interactive_books.domain.tool import ChatResponse, ToolDefinition

from tests.fakes import FakeBookRepository, FakeChunkRepository, FakeSummaryRepository


def _chunk(
    chunk_id: str,
    start_page: int,
    end_page: int,
    content: str = "Content.",
    chunk_index: int = 0,
) -> Chunk:
    return Chunk(
        id=chunk_id,
        book_id="b1",
        content=content,
        start_page=start_page,
        end_page=end_page,
        chunk_index=chunk_index,
    )


# --- Section grouping tests ---


class TestGroupChunksIntoSections:
    def test_empty_chunks_returns_empty(self) -> None:
        assert group_chunks_into_sections([]) == []

    def test_single_chunk_becomes_single_section(self) -> None:
        chunks = [_chunk("c1", 1, 3, "Hello")]
        sections = group_chunks_into_sections(chunks)
        assert len(sections) == 1
        assert sections[0].start_page == 1
        assert sections[0].end_page == 3
        assert sections[0].content == "Hello"

    def test_contiguous_chunks_merge_into_one_section(self) -> None:
        chunks = [
            _chunk("c1", 1, 2, "Part A", chunk_index=0),
            _chunk("c2", 2, 3, "Part B", chunk_index=1),
            _chunk("c3", 3, 4, "Part C", chunk_index=2),
        ]
        sections = group_chunks_into_sections(chunks)
        assert len(sections) == 1
        assert sections[0].start_page == 1
        assert sections[0].end_page == 4
        assert "Part A" in sections[0].content
        assert "Part C" in sections[0].content

    def test_adjacent_chunks_merge(self) -> None:
        chunks = [
            _chunk("c1", 1, 2, "Part A", chunk_index=0),
            _chunk("c2", 3, 4, "Part B", chunk_index=1),
        ]
        sections = group_chunks_into_sections(chunks)
        assert len(sections) == 1
        assert sections[0].start_page == 1
        assert sections[0].end_page == 4

    def test_gap_creates_new_section(self) -> None:
        chunks = [
            _chunk("c1", 1, 3, "Section A", chunk_index=0),
            _chunk("c2", 5, 7, "Section B", chunk_index=1),
        ]
        sections = group_chunks_into_sections(chunks)
        assert len(sections) == 2
        assert sections[0].start_page == 1
        assert sections[0].end_page == 3
        assert sections[1].start_page == 5
        assert sections[1].end_page == 7

    def test_overlapping_chunks_merge(self) -> None:
        chunks = [
            _chunk("c1", 1, 5, "Part A", chunk_index=0),
            _chunk("c2", 3, 8, "Part B", chunk_index=1),
        ]
        sections = group_chunks_into_sections(chunks)
        assert len(sections) == 1
        assert sections[0].start_page == 1
        assert sections[0].end_page == 8

    def test_multiple_sections_with_gaps(self) -> None:
        chunks = [
            _chunk("c1", 1, 2, "A", chunk_index=0),
            _chunk("c2", 2, 3, "B", chunk_index=1),
            _chunk("c3", 10, 12, "C", chunk_index=2),
            _chunk("c4", 12, 15, "D", chunk_index=3),
            _chunk("c5", 20, 22, "E", chunk_index=4),
        ]
        sections = group_chunks_into_sections(chunks)
        assert len(sections) == 3
        assert sections[0] == Section(start_page=1, end_page=3, content="A\n\nB")
        assert sections[1] == Section(start_page=10, end_page=15, content="C\n\nD")
        assert sections[2] == Section(start_page=20, end_page=22, content="E")


# --- Fake ChatProvider for use case tests ---


class FakeChatProvider:
    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.call_count = 0

    @property
    def model_name(self) -> str:
        return "fake"

    def chat(self, messages: list[PromptMessage]) -> str:
        self.call_count += 1
        return self._responses.pop(0)

    def chat_with_tools(
        self, messages: list[PromptMessage], tools: list[ToolDefinition]
    ) -> ChatResponse:
        raise NotImplementedError


def _valid_json_response(
    title: str = "Chapter 1",
    summary: str = "A summary of the section.",
    key_statements: list[dict[str, object]] | None = None,
) -> str:
    return json.dumps(
        {
            "title": title,
            "summary": summary,
            "key_statements": key_statements
            or [{"statement": "Key point.", "page": 1}],
        }
    )


@pytest.fixture
def prompts_dir(tmp_path: Path) -> Path:
    prompt_file = tmp_path / "summarization_prompt.md"
    prompt_file.write_text(
        "Summarize pages {{start_page}} to {{end_page}}.\n\n{{content}}"
    )
    return tmp_path


# --- SummarizeBookUseCase tests ---


class TestSummarizeBookUseCase:
    def test_book_not_found_raises(self, prompts_dir: Path) -> None:
        use_case = SummarizeBookUseCase(
            chat_provider=FakeChatProvider([]),
            book_repo=FakeBookRepository(),
            chunk_repo=FakeChunkRepository(),
            summary_repo=FakeSummaryRepository(),
            prompts_dir=prompts_dir,
        )
        with pytest.raises(BookError) as exc_info:
            use_case.execute("nonexistent")
        assert exc_info.value.code == BookErrorCode.NOT_FOUND

    def test_book_with_no_chunks_raises(self, prompts_dir: Path) -> None:
        book_repo = FakeBookRepository()
        book_repo.save(Book(id="b1", title="Empty Book"))
        use_case = SummarizeBookUseCase(
            chat_provider=FakeChatProvider([]),
            book_repo=book_repo,
            chunk_repo=FakeChunkRepository(),
            summary_repo=FakeSummaryRepository(),
            prompts_dir=prompts_dir,
        )
        with pytest.raises(BookError) as exc_info:
            use_case.execute("b1")
        assert exc_info.value.code == BookErrorCode.INVALID_STATE

    def test_returns_cached_summaries_when_not_regenerating(
        self, prompts_dir: Path
    ) -> None:
        book_repo = FakeBookRepository()
        book_repo.save(Book(id="b1", title="Cached Book"))
        summary_repo = FakeSummaryRepository()
        cached = [
            SectionSummary(
                id="s1",
                book_id="b1",
                title="Cached",
                start_page=1,
                end_page=5,
                summary="Cached summary.",
                key_statements=[],
                section_index=0,
            )
        ]
        summary_repo.summaries["b1"] = cached
        provider = FakeChatProvider([])

        use_case = SummarizeBookUseCase(
            chat_provider=provider,
            book_repo=book_repo,
            chunk_repo=FakeChunkRepository(),
            summary_repo=summary_repo,
            prompts_dir=prompts_dir,
        )
        result = use_case.execute("b1")

        assert result == cached
        assert provider.call_count == 0

    def test_regenerate_ignores_cache(self, prompts_dir: Path) -> None:
        book_repo = FakeBookRepository()
        book_repo.save(Book(id="b1", title="Book"))
        chunk_repo = FakeChunkRepository()
        chunk_repo.save_chunks("b1", [_chunk("c1", 1, 3, "Content.")])
        summary_repo = FakeSummaryRepository()
        summary_repo.summaries["b1"] = [
            SectionSummary(
                id="old",
                book_id="b1",
                title="Old",
                start_page=1,
                end_page=3,
                summary="Old summary.",
                key_statements=[],
                section_index=0,
            )
        ]

        use_case = SummarizeBookUseCase(
            chat_provider=FakeChatProvider([_valid_json_response(title="New")]),
            book_repo=book_repo,
            chunk_repo=chunk_repo,
            summary_repo=summary_repo,
            prompts_dir=prompts_dir,
        )
        result = use_case.execute("b1", regenerate=True)

        assert len(result) == 1
        assert result[0].title == "New"

    def test_summarizes_single_section(self, prompts_dir: Path) -> None:
        book_repo = FakeBookRepository()
        book_repo.save(Book(id="b1", title="Book"))
        chunk_repo = FakeChunkRepository()
        chunk_repo.save_chunks(
            "b1",
            [
                _chunk("c1", 1, 3, "First part.", chunk_index=0),
                _chunk("c2", 3, 5, "Second part.", chunk_index=1),
            ],
        )
        summary_repo = FakeSummaryRepository()

        response = _valid_json_response(
            title="Introduction",
            summary="The book begins with the setting.",
            key_statements=[{"statement": "The town was quiet.", "page": 2}],
        )

        use_case = SummarizeBookUseCase(
            chat_provider=FakeChatProvider([response]),
            book_repo=book_repo,
            chunk_repo=chunk_repo,
            summary_repo=summary_repo,
            prompts_dir=prompts_dir,
        )
        result = use_case.execute("b1")

        assert len(result) == 1
        assert result[0].title == "Introduction"
        assert result[0].start_page == 1
        assert result[0].end_page == 5
        assert result[0].summary == "The book begins with the setting."
        assert len(result[0].key_statements) == 1
        assert result[0].key_statements[0].statement == "The town was quiet."
        assert result[0].key_statements[0].page == 2
        assert result[0].section_index == 0
        assert "b1" in summary_repo.summaries

    def test_summarizes_multiple_sections(self, prompts_dir: Path) -> None:
        book_repo = FakeBookRepository()
        book_repo.save(Book(id="b1", title="Book"))
        chunk_repo = FakeChunkRepository()
        chunk_repo.save_chunks(
            "b1",
            [
                _chunk("c1", 1, 3, "Part A.", chunk_index=0),
                _chunk("c2", 10, 12, "Part B.", chunk_index=1),
            ],
        )

        use_case = SummarizeBookUseCase(
            chat_provider=FakeChatProvider([
                _valid_json_response(title="Section A"),
                _valid_json_response(title="Section B"),
            ]),
            book_repo=book_repo,
            chunk_repo=chunk_repo,
            summary_repo=FakeSummaryRepository(),
            prompts_dir=prompts_dir,
        )
        result = use_case.execute("b1")

        assert len(result) == 2
        assert result[0].title == "Section A"
        assert result[1].title == "Section B"
        assert result[0].section_index == 0
        assert result[1].section_index == 1

    def test_retries_on_invalid_json(self, prompts_dir: Path) -> None:
        book_repo = FakeBookRepository()
        book_repo.save(Book(id="b1", title="Book"))
        chunk_repo = FakeChunkRepository()
        chunk_repo.save_chunks("b1", [_chunk("c1", 1, 3)])

        use_case = SummarizeBookUseCase(
            chat_provider=FakeChatProvider([
                "Not valid JSON at all",
                _valid_json_response(title="Recovered"),
            ]),
            book_repo=book_repo,
            chunk_repo=chunk_repo,
            summary_repo=FakeSummaryRepository(),
            prompts_dir=prompts_dir,
        )
        result = use_case.execute("b1")

        assert len(result) == 1
        assert result[0].title == "Recovered"

    def test_raises_after_retry_fails(self, prompts_dir: Path) -> None:
        book_repo = FakeBookRepository()
        book_repo.save(Book(id="b1", title="Book"))
        chunk_repo = FakeChunkRepository()
        chunk_repo.save_chunks("b1", [_chunk("c1", 1, 3)])

        use_case = SummarizeBookUseCase(
            chat_provider=FakeChatProvider([
                "Not JSON",
                "Still not JSON",
            ]),
            book_repo=book_repo,
            chunk_repo=chunk_repo,
            summary_repo=FakeSummaryRepository(),
            prompts_dir=prompts_dir,
        )
        with pytest.raises(LLMError):
            use_case.execute("b1")

    def test_progress_callback_is_called(self, prompts_dir: Path) -> None:
        book_repo = FakeBookRepository()
        book_repo.save(Book(id="b1", title="Book"))
        chunk_repo = FakeChunkRepository()
        chunk_repo.save_chunks(
            "b1",
            [
                _chunk("c1", 1, 3, chunk_index=0),
                _chunk("c2", 10, 12, chunk_index=1),
            ],
        )
        progress_calls: list[tuple[int, int]] = []

        use_case = SummarizeBookUseCase(
            chat_provider=FakeChatProvider([
                _valid_json_response(),
                _valid_json_response(),
            ]),
            book_repo=book_repo,
            chunk_repo=chunk_repo,
            summary_repo=FakeSummaryRepository(),
            prompts_dir=prompts_dir,
            on_progress=lambda current, total: progress_calls.append((current, total)),
        )
        use_case.execute("b1")

        assert progress_calls == [(1, 2), (2, 2)]

    def test_clamps_key_statement_page_to_section_range(
        self, prompts_dir: Path
    ) -> None:
        book_repo = FakeBookRepository()
        book_repo.save(Book(id="b1", title="Book"))
        chunk_repo = FakeChunkRepository()
        chunk_repo.save_chunks("b1", [_chunk("c1", 5, 10)])

        response = _valid_json_response(
            key_statements=[{"statement": "Out of range.", "page": 99}],
        )
        use_case = SummarizeBookUseCase(
            chat_provider=FakeChatProvider([response]),
            book_repo=book_repo,
            chunk_repo=chunk_repo,
            summary_repo=FakeSummaryRepository(),
            prompts_dir=prompts_dir,
        )
        result = use_case.execute("b1")

        assert result[0].key_statements[0].page == 10

    def test_handles_code_fenced_json_response(self, prompts_dir: Path) -> None:
        book_repo = FakeBookRepository()
        book_repo.save(Book(id="b1", title="Book"))
        chunk_repo = FakeChunkRepository()
        chunk_repo.save_chunks("b1", [_chunk("c1", 1, 3)])

        fenced_response = (
            "```json\n" + _valid_json_response(title="Fenced") + "\n```"
        )
        use_case = SummarizeBookUseCase(
            chat_provider=FakeChatProvider([fenced_response]),
            book_repo=book_repo,
            chunk_repo=chunk_repo,
            summary_repo=FakeSummaryRepository(),
            prompts_dir=prompts_dir,
        )
        result = use_case.execute("b1")

        assert result[0].title == "Fenced"
