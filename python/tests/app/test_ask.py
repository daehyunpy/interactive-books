from pathlib import Path

import pytest
from interactive_books.app.ask import AskBookUseCase
from interactive_books.domain.errors import (
    BookError,
    BookErrorCode,
    LLMError,
    LLMErrorCode,
)
from interactive_books.domain.prompt_message import PromptMessage
from interactive_books.domain.search_result import SearchResult


class FakeSearchBooksUseCase:
    def __init__(self) -> None:
        self._results: list[SearchResult] = []
        self._error: BookError | None = None
        self.last_book_id: str | None = None
        self.last_top_k: int | None = None

    def set_results(self, results: list[SearchResult]) -> None:
        self._results = results

    def set_error(self, error: BookError) -> None:
        self._error = error

    def execute(self, book_id: str, query: str, top_k: int = 5) -> list[SearchResult]:
        self.last_book_id = book_id
        self.last_top_k = top_k
        if self._error:
            raise self._error
        return self._results


class FakeChatProvider:
    def __init__(self, response: str = "The answer.") -> None:
        self._response = response
        self._error: LLMError | None = None
        self.last_messages: list[PromptMessage] | None = None

    def set_error(self, error: LLMError) -> None:
        self._error = error

    @property
    def model_name(self) -> str:
        return "fake-model"

    def chat(self, messages: list[PromptMessage]) -> str:
        self.last_messages = messages
        if self._error:
            raise self._error
        return self._response


@pytest.fixture
def prompts_dir(tmp_path: Path) -> Path:
    (tmp_path / "system_prompt.md").write_text("You are a reading companion.")
    (tmp_path / "citation_instructions.md").write_text("Cite pages as (p.N).")
    (tmp_path / "query_template.md").write_text(
        "Passages:\n\n{context}\n\nQuestion: {question}"
    )
    return tmp_path


def _sample_results() -> list[SearchResult]:
    return [
        SearchResult(
            chunk_id="c1",
            content="Early content here.",
            start_page=1,
            end_page=10,
            distance=0.1,
        ),
        SearchResult(
            chunk_id="c2",
            content="Mid content here.",
            start_page=40,
            end_page=50,
            distance=0.5,
        ),
    ]


def _make_use_case(
    *,
    chat: FakeChatProvider | None = None,
    search: FakeSearchBooksUseCase | None = None,
    prompts_dir: Path,
) -> tuple[AskBookUseCase, FakeChatProvider, FakeSearchBooksUseCase]:
    cp = chat or FakeChatProvider()
    su = search or FakeSearchBooksUseCase()
    return (
        AskBookUseCase(chat_provider=cp, search_use_case=su, prompts_dir=prompts_dir),  # type: ignore[arg-type]
        cp,
        su,
    )


class TestAskSuccess:
    def test_returns_llm_answer(self, prompts_dir: Path) -> None:
        search = FakeSearchBooksUseCase()
        search.set_results(_sample_results())
        use_case, chat, _ = _make_use_case(search=search, prompts_dir=prompts_dir)

        result = use_case.execute("book-1", "What happens?")

        assert result == "The answer."

    def test_passes_top_k_to_search(self, prompts_dir: Path) -> None:
        search = FakeSearchBooksUseCase()
        search.set_results(_sample_results())
        use_case, _, _ = _make_use_case(search=search, prompts_dir=prompts_dir)

        use_case.execute("book-1", "query", top_k=10)

        assert search.last_top_k == 10

    def test_assembles_system_message_with_citations(self, prompts_dir: Path) -> None:
        search = FakeSearchBooksUseCase()
        search.set_results(_sample_results())
        use_case, chat, _ = _make_use_case(search=search, prompts_dir=prompts_dir)

        use_case.execute("book-1", "What happens?")

        assert chat.last_messages is not None
        system_msg = chat.last_messages[0]
        assert system_msg.role == "system"
        assert "reading companion" in system_msg.content
        assert "Cite pages" in system_msg.content

    def test_assembles_user_message_with_context(self, prompts_dir: Path) -> None:
        search = FakeSearchBooksUseCase()
        search.set_results(_sample_results())
        use_case, chat, _ = _make_use_case(search=search, prompts_dir=prompts_dir)

        use_case.execute("book-1", "What happens?")

        assert chat.last_messages is not None
        user_msg = chat.last_messages[1]
        assert user_msg.role == "user"
        assert "[Pages 1-10]" in user_msg.content
        assert "Early content here." in user_msg.content
        assert "[Pages 40-50]" in user_msg.content
        assert "Question: What happens?" in user_msg.content


class TestAskContextFormatting:
    def test_labels_passages_with_page_ranges(self, prompts_dir: Path) -> None:
        search = FakeSearchBooksUseCase()
        search.set_results(
            [
                SearchResult(
                    chunk_id="c1",
                    content="Text A.",
                    start_page=5,
                    end_page=5,
                    distance=0.1,
                ),
                SearchResult(
                    chunk_id="c2",
                    content="Text B.",
                    start_page=20,
                    end_page=25,
                    distance=0.3,
                ),
            ]
        )
        use_case, chat, _ = _make_use_case(search=search, prompts_dir=prompts_dir)

        use_case.execute("book-1", "question")

        assert chat.last_messages is not None
        user_msg = chat.last_messages[1]
        assert "[Pages 5-5]:\nText A." in user_msg.content
        assert "[Pages 20-25]:\nText B." in user_msg.content


class TestAskBookNotFound:
    def test_propagates_not_found(self, prompts_dir: Path) -> None:
        search = FakeSearchBooksUseCase()
        search.set_error(BookError(BookErrorCode.NOT_FOUND, "Book not found"))
        use_case, _, _ = _make_use_case(search=search, prompts_dir=prompts_dir)

        with pytest.raises(BookError) as exc_info:
            use_case.execute("nonexistent", "query")
        assert exc_info.value.code == BookErrorCode.NOT_FOUND


class TestAskNoEmbeddings:
    def test_propagates_invalid_state(self, prompts_dir: Path) -> None:
        search = FakeSearchBooksUseCase()
        search.set_error(BookError(BookErrorCode.INVALID_STATE, "No embeddings"))
        use_case, _, _ = _make_use_case(search=search, prompts_dir=prompts_dir)

        with pytest.raises(BookError) as exc_info:
            use_case.execute("book-1", "query")
        assert exc_info.value.code == BookErrorCode.INVALID_STATE


class TestAskNoResults:
    def test_still_calls_llm_with_no_context(self, prompts_dir: Path) -> None:
        search = FakeSearchBooksUseCase()
        search.set_results([])
        use_case, chat, _ = _make_use_case(search=search, prompts_dir=prompts_dir)

        result = use_case.execute("book-1", "query")

        assert result == "The answer."
        assert chat.last_messages is not None
        user_msg = chat.last_messages[1]
        assert "No relevant passages found" in user_msg.content


class TestAskLLMFailure:
    def test_propagates_llm_error(self, prompts_dir: Path) -> None:
        search = FakeSearchBooksUseCase()
        search.set_results(_sample_results())
        chat = FakeChatProvider()
        chat.set_error(LLMError(LLMErrorCode.API_CALL_FAILED, "API down"))
        use_case, _, _ = _make_use_case(
            chat=chat, search=search, prompts_dir=prompts_dir
        )

        with pytest.raises(LLMError) as exc_info:
            use_case.execute("book-1", "query")
        assert exc_info.value.code == LLMErrorCode.API_CALL_FAILED
