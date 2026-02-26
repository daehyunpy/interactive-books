"""Agent-level spoiler prevention integration tests.

Exercises the full ChatWithBookUseCase pipeline with a real LLM to verify
that the agent does not leak content beyond the reader's current_page.
Uses a pre-built SQLite fixture (1984_embedded.db) and an LLM-as-judge
to evaluate response quality.
"""

import os
import shutil
import uuid
from collections.abc import Generator
from pathlib import Path

import pytest

from interactive_books.app.chat import ChatWithBookUseCase
from interactive_books.app.search import SearchBooksUseCase
from interactive_books.domain.conversation import Conversation
from interactive_books.infra.context.full_history import (
    ConversationContextStrategy,
)
from interactive_books.infra.embeddings.openai import EmbeddingProvider
from interactive_books.infra.llm.anthropic import ChatProvider
from interactive_books.infra.retrieval.tool_use import RetrievalStrategy
from interactive_books.infra.storage.book_repo import (
    BookRepository,
)
from interactive_books.infra.storage.chat_message_repo import (
    ChatMessageRepository,
)
from interactive_books.infra.storage.chunk_repo import (
    ChunkRepository,
)
from interactive_books.infra.storage.conversation_repo import (
    ConversationRepository,
)
from interactive_books.infra.storage.database import Database
from interactive_books.infra.storage.embedding_repo import (
    EmbeddingRepository,
)
from tests.helpers.llm_judge import judge_response

FIXTURE_DB = (
    Path(__file__).resolve().parents[3] / "shared" / "fixtures" / "1984_embedded.db"
)
PROMPTS_DIR = Path(__file__).resolve().parents[3] / "shared" / "prompts"

# Reader has finished through chapter 3 (~page 30).
# Chunks with start_page > 30 are filtered from search results.
CURRENT_PAGE = 30

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
def _fixture_db(tmp_path: Path) -> Generator[Database]:
    """Copy the pre-built fixture DB to tmp_path and open it."""
    db_copy = tmp_path / "1984_embedded.db"
    shutil.copy2(FIXTURE_DB, db_copy)
    db = Database(db_copy, enable_vec=True)
    yield db  # type: ignore[misc]
    db.close()


@pytest.fixture
def _book_at_page(_fixture_db: Database) -> str:
    """Set current_page on the fixture book and return its ID."""
    book_repo = BookRepository(_fixture_db)
    books = book_repo.get_all()
    assert len(books) == 1, "Fixture DB should contain exactly one book"
    book = books[0]
    book.set_current_page(CURRENT_PAGE)
    book_repo.save(book)
    return book.id


@pytest.fixture
def _conversation(_fixture_db: Database, _book_at_page: str) -> str:
    """Create a fresh conversation for the fixture book; return its ID."""
    conv = Conversation(
        id=str(uuid.uuid4()),
        book_id=_book_at_page,
        title="Spoiler test",
    )
    ConversationRepository(_fixture_db).save(conv)
    return conv.id


@pytest.fixture
def _chat_use_case(_fixture_db: Database) -> ChatWithBookUseCase:
    """Wire the full ChatWithBookUseCase with real providers and repos."""
    chat_provider = ChatProvider(api_key=os.environ["ANTHROPIC_API_KEY"])
    embedding_provider = EmbeddingProvider(api_key=os.environ["OPENAI_API_KEY"])

    book_repo = BookRepository(_fixture_db)
    chunk_repo = ChunkRepository(_fixture_db)
    embedding_repo = EmbeddingRepository(_fixture_db)
    conversation_repo = ConversationRepository(_fixture_db)
    message_repo = ChatMessageRepository(_fixture_db)

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
def _judge_provider() -> ChatProvider:
    """Separate ChatProvider instance for the LLM judge."""
    return ChatProvider(api_key=os.environ["ANTHROPIC_API_KEY"])


class TestSpoilerPreventionViaSearch:
    """Agent uses search_book and answers from early content only."""

    def test_agent_answers_from_early_content_without_spoilers(
        self,
        _conversation: str,
        _chat_use_case: ChatWithBookUseCase,
        _judge_provider: ChatProvider,
    ) -> None:
        response = _chat_use_case.execute(
            _conversation,
            "What is the setting of the story?",
        )

        assert judge_response(
            _judge_provider,
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
        _conversation: str,
        _chat_use_case: ChatWithBookUseCase,
        _judge_provider: ChatProvider,
    ) -> None:
        response = _chat_use_case.execute(
            _conversation,
            "How does the book end?",
        )

        assert judge_response(
            _judge_provider,
            actual=response,
            expected=(
                "The response should refuse to discuss the ending or say "
                "it cannot reveal content beyond the reader's current position. "
                "It must NOT mention Winston's arrest, Room 101, "
                "the betrayal of Julia, 'He loved Big Brother', "
                "or any Part Three events. A response that says something like "
                "'I can only discuss content up to your current reading position' "
                "or 'I don't have information about the ending in the pages "
                "you've read so far' is acceptable."
            ),
        ), f"Agent leaked spoilers about the ending:\n{response}"
