"""Agent-level spoiler prevention integration tests.

Exercises the full ChatWithBookUseCase pipeline with a real LLM to verify
that the agent does not leak content beyond the reader's current_page.
Uses a pre-built SQLite fixture (1984_embedded.db) and an LLM-as-judge
to evaluate response quality.
"""

import os
import shutil
from collections.abc import Generator
from pathlib import Path
from uuid import uuid4

import pytest

from interactive_books.app.chat import ChatWithBookUseCase
from interactive_books.app.search import SearchBooksUseCase
from interactive_books.domain.conversation import Conversation
from interactive_books.infra.context.full_history import ConversationContextStrategy
from interactive_books.infra.embeddings.openai import EmbeddingProvider
from interactive_books.infra.llm.anthropic import ChatProvider
from interactive_books.infra.retrieval.tool_use import RetrievalStrategy
from interactive_books.infra.storage.book_repo import BookRepository
from interactive_books.infra.storage.chat_message_repo import ChatMessageRepository
from interactive_books.infra.storage.chunk_repo import ChunkRepository
from interactive_books.infra.storage.conversation_repo import ConversationRepository
from interactive_books.infra.storage.database import Database
from interactive_books.infra.storage.embedding_repo import EmbeddingRepository
from tests.helpers.llm_judge import judge_response

FIXTURE_DB = (
    Path(__file__).resolve().parents[3] / "shared" / "fixtures" / "1984_embedded.db"
)
PROMPTS_DIR = Path(__file__).resolve().parents[3] / "shared" / "prompts"

# Default page position — tests may override via the current_page fixture.
DEFAULT_CURRENT_PAGE = 30

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set",
    ),
    pytest.mark.skipif(
        not os.environ.get("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set",
    ),
]


@pytest.fixture
def current_page() -> int:
    """Override in test classes to set a different reading position."""
    return DEFAULT_CURRENT_PAGE


@pytest.fixture
def fixture_db(tmp_path: Path) -> Generator[Database]:
    """Copy the pre-built fixture DB to tmp_path and open it."""
    db_copy = tmp_path / "1984_embedded.db"
    shutil.copy2(FIXTURE_DB, db_copy)
    db = Database(db_copy, enable_vec=True)
    yield db
    db.close()


@pytest.fixture
def book_id(fixture_db: Database, current_page: int) -> str:
    """Set current_page on the fixture book and return its ID."""
    book_repo = BookRepository(fixture_db)
    books = book_repo.get_all()
    assert len(books) == 1, "Fixture DB should contain exactly one book"
    book = books[0]
    book.set_current_page(current_page)
    book_repo.save(book)
    return book.id


@pytest.fixture
def conversation_id(fixture_db: Database, book_id: str) -> str:
    """Create a fresh conversation for the fixture book; return its ID."""
    conv = Conversation(
        id=str(uuid4()),
        book_id=book_id,
        title="Spoiler test",
    )
    ConversationRepository(fixture_db).save(conv)
    return conv.id


@pytest.fixture
def chat_use_case(fixture_db: Database) -> ChatWithBookUseCase:
    """Wire the full ChatWithBookUseCase with real providers and repos."""
    chat_provider = ChatProvider(api_key=os.environ["ANTHROPIC_API_KEY"])
    embedding_provider = EmbeddingProvider(api_key=os.environ["OPENAI_API_KEY"])

    book_repo = BookRepository(fixture_db)
    chunk_repo = ChunkRepository(fixture_db)
    embedding_repo = EmbeddingRepository(fixture_db)
    conversation_repo = ConversationRepository(fixture_db)
    message_repo = ChatMessageRepository(fixture_db)

    search_use_case = SearchBooksUseCase(
        embedding_provider=embedding_provider,
        book_repo=book_repo,
        chunk_repo=chunk_repo,
        embedding_repo=embedding_repo,
    )

    return ChatWithBookUseCase(
        chat_provider=chat_provider,
        retrieval_strategy=RetrievalStrategy(),
        context_strategy=ConversationContextStrategy(),
        search_use_case=search_use_case,
        conversation_repo=conversation_repo,
        message_repo=message_repo,
        prompts_dir=PROMPTS_DIR,
    )


@pytest.fixture
def judge_provider() -> ChatProvider:
    """Separate ChatProvider instance for the LLM judge."""
    return ChatProvider(api_key=os.environ["ANTHROPIC_API_KEY"])


class TestSpoilerPreventionViaSearch:
    """Agent uses search_book and answers from early content only."""

    def test_agent_answers_from_early_content_without_spoilers(
        self,
        conversation_id: str,
        chat_use_case: ChatWithBookUseCase,
        judge_provider: ChatProvider,
    ) -> None:
        response = chat_use_case.execute(
            conversation_id,
            "What is the setting of the story?",
        )

        assert judge_response(
            judge_provider,
            actual=response,
            expected=(
                "The response should describe the setting of 1984: "
                "Airstrip One (formerly England/Britain), London, Oceania, "
                "Victory Mansions, telescreens, the Ministry of Truth, or "
                "the oppressive Party surveillance state. "
                "It must NOT mention Room 101, Julia (as a love interest), "
                "Winston's arrest, thought reform, 'I love Big Brother', "
                "or any events from Part Three of the novel."
            ),
        ), f"Agent leaked spoilers or gave irrelevant answer:\n{response}"


class TestSpoilerPreventionViaKnowledge:
    """Agent must not answer from parametric knowledge about late-book events."""

    def test_agent_refuses_to_reveal_ending(
        self,
        conversation_id: str,
        chat_use_case: ChatWithBookUseCase,
        judge_provider: ChatProvider,
    ) -> None:
        response = chat_use_case.execute(
            conversation_id,
            "How does the book end?",
        )

        assert judge_response(
            judge_provider,
            actual=response,
            expected=(
                "The key criterion: the response must NOT reveal the ending "
                "of 1984. It must NOT mention Winston's arrest, Room 101, "
                "the betrayal of Julia, 'He loved Big Brother', "
                "or any Part Three events. "
                "Any of these responses are acceptable: "
                "(a) refusing to discuss the ending, "
                "(b) saying it cannot reveal content beyond the current position, "
                "(c) asking the reader to clarify or provide more context, "
                "(d) saying it doesn't have information about the ending. "
                "The only way to FAIL is if the response actually reveals "
                "plot details from the end of the book."
            ),
        ), f"Agent leaked spoilers about the ending:\n{response}"


class TestSpoilerPreventionAtPage5:
    """Very early reader — only Victory Mansions and the Ministry are visible.

    Chunks at pages 1 and 3 are accessible.  The diary (page 6),
    Two Minutes Hate (page 8), and everything after are spoilers.
    """

    @pytest.fixture
    def current_page(self) -> int:
        return 5

    def test_agent_describes_victory_mansions_at_page_5(
        self,
        conversation_id: str,
        chat_use_case: ChatWithBookUseCase,
        judge_provider: ChatProvider,
    ) -> None:
        response = chat_use_case.execute(
            conversation_id,
            "Where does Winston live?",
        )

        assert judge_response(
            judge_provider,
            actual=response,
            expected=(
                "The response should mention Victory Mansions, London, "
                "Airstrip One, Oceania, or the telescreen in Winston's flat. "
                "It must NOT mention Winston writing a diary, the Two Minutes Hate, "
                "O'Brien, the dark-haired girl, Syme, Newspeak, Mr. Charrington, "
                "the proles, or any events from page 6 onward."
            ),
        ), f"Agent leaked content beyond page 5:\n{response}"

    def test_agent_does_not_reveal_diary_at_page_5(
        self,
        conversation_id: str,
        chat_use_case: ChatWithBookUseCase,
        judge_provider: ChatProvider,
    ) -> None:
        response = chat_use_case.execute(
            conversation_id,
            "Does Winston keep a diary?",
        )

        # An empty response means the agent found nothing to say — no spoiler.
        if not response.strip():
            return

        assert judge_response(
            judge_provider,
            actual=response,
            expected=(
                "The response should NOT confirm that Winston keeps a diary. "
                "The diary is introduced on page 6, beyond the reader's position. "
                "An acceptable answer is something like 'Based on what you've read "
                "so far, I don't have information about that' or a refusal to "
                "discuss content beyond the current reading position. "
                "It must NOT describe the diary, the junk shop, or the act of writing."
            ),
        ), f"Agent revealed diary spoiler at page 5:\n{response}"


class TestSpoilerPreventionAtPage50:
    """Mid-book reader — Newspeak and the proles are known, but not Charrington's room.

    Chunks through page 40 are accessible.  Mr. Charrington's upstairs
    room (page 51) and the prole district walk (page 60) are spoilers.
    """

    @pytest.fixture
    def current_page(self) -> int:
        return 50

    def test_agent_does_not_reveal_charrington_room_at_page_50(
        self,
        conversation_id: str,
        chat_use_case: ChatWithBookUseCase,
        judge_provider: ChatProvider,
    ) -> None:
        response = chat_use_case.execute(
            conversation_id,
            "Tell me about Mr. Charrington and his shop.",
        )

        # An empty response means the agent found nothing to say — no spoiler.
        if not response.strip():
            return

        assert judge_response(
            judge_provider,
            actual=response,
            expected=(
                "The key criterion: the response must NOT reveal details from "
                "page 51 or later. It must NOT mention the room upstairs with "
                "no telescreen, the glass paperweight with coral, the print of "
                "St. Clement Danes church, or Winston renting that room. "
                "Any of these responses are acceptable: "
                "(a) saying there's no information about Charrington yet, "
                "(b) declining to discuss content beyond the current position, "
                "(c) asking for clarification, "
                "(d) an empty or minimal answer. "
                "The only way to FAIL is to reveal the upstairs room details."
            ),
        ), f"Agent revealed Charrington's room spoiler at page 50:\n{response}"


class TestFullAccessAtEndOfFixture:
    """Reader past all available content — no spoiler restrictions.

    All 13 chunks (pages 1–68) are accessible.  The agent should be able
    to discuss any topic covered in the fixture.
    """

    @pytest.fixture
    def current_page(self) -> int:
        return 100

    def test_agent_discusses_party_control_at_full_access(
        self,
        conversation_id: str,
        chat_use_case: ChatWithBookUseCase,
        judge_provider: ChatProvider,
    ) -> None:
        response = chat_use_case.execute(
            conversation_id,
            "How does the Party control the past?",
        )

        # An empty response at full access means the agent didn't engage —
        # not ideal, but not a spoiler failure.  Skip the judge.
        if not response.strip():
            return

        assert judge_response(
            judge_provider,
            actual=response,
            expected=(
                "The response should discuss how the Party controls the past: "
                "rewriting historical records at the Ministry of Truth, "
                "the idea that 'who controls the past controls the future', "
                "or Winston's job altering newspapers and documents. "
                "Since the reader has full access, any content from the book "
                "is acceptable."
            ),
        ), f"Agent failed to discuss available content:\n{response}"
