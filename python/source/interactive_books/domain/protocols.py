from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from interactive_books.domain.book import Book
from interactive_books.domain.chat import ChatMessage
from interactive_books.domain.chat_event import ChatEvent
from interactive_books.domain.chunk import Chunk
from interactive_books.domain.chunk_data import ChunkData
from interactive_books.domain.conversation import Conversation
from interactive_books.domain.embedding_vector import EmbeddingVector
from interactive_books.domain.page_content import PageContent
from interactive_books.domain.prompt_message import PromptMessage
from interactive_books.domain.search_result import SearchResult
from interactive_books.domain.tool import ChatResponse, ToolDefinition


class BookRepository(Protocol):
    def save(self, book: Book) -> None: ...
    def get(self, book_id: str) -> Book | None: ...
    def get_all(self) -> list[Book]: ...
    def delete(self, book_id: str) -> None: ...


class ChunkRepository(Protocol):
    def save_chunks(self, book_id: str, chunks: list[Chunk]) -> None: ...
    def get_by_book(self, book_id: str) -> list[Chunk]: ...
    def get_up_to_page(self, book_id: str, page: int) -> list[Chunk]: ...
    def count_by_book(self, book_id: str) -> int: ...
    def delete_by_book(self, book_id: str) -> None: ...


class BookParser(Protocol):
    def parse(self, file_path: Path) -> list[PageContent]: ...


class UrlParser(Protocol):
    def parse_url(self, url: str) -> list[PageContent]: ...


class TextChunker(Protocol):
    def chunk(self, pages: list[PageContent]) -> list[ChunkData]: ...


class ChatProvider(Protocol):
    @property
    def model_name(self) -> str: ...
    def chat(self, messages: list[PromptMessage]) -> str: ...
    def chat_with_tools(
        self,
        messages: list[PromptMessage],
        tools: list[ToolDefinition],
    ) -> ChatResponse: ...


class EmbeddingProvider(Protocol):
    @property
    def provider_name(self) -> str: ...
    @property
    def dimension(self) -> int: ...
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class EmbeddingRepository(Protocol):
    def ensure_table(self, provider_name: str, dimension: int) -> None: ...
    def save_embeddings(
        self,
        provider_name: str,
        dimension: int,
        book_id: str,
        embeddings: list[EmbeddingVector],
    ) -> None: ...
    def delete_by_book(
        self, provider_name: str, dimension: int, book_id: str
    ) -> None: ...
    def has_embeddings(
        self, book_id: str, provider_name: str, dimension: int
    ) -> bool: ...
    def search(
        self,
        provider_name: str,
        dimension: int,
        book_id: str,
        query_vector: list[float],
        top_k: int,
    ) -> list[tuple[str, float]]: ...


class ConversationRepository(Protocol):
    def save(self, conversation: Conversation) -> None: ...
    def get(self, conversation_id: str) -> Conversation | None: ...
    def get_by_book(self, book_id: str) -> list[Conversation]: ...
    def delete(self, conversation_id: str) -> None: ...


class ChatMessageRepository(Protocol):
    def save(self, message: ChatMessage) -> None: ...
    def get_by_conversation(self, conversation_id: str) -> list[ChatMessage]: ...
    def delete_by_conversation(self, conversation_id: str) -> None: ...


class RetrievalStrategy(Protocol):
    def execute(
        self,
        chat_provider: "ChatProvider",
        messages: list[PromptMessage],
        tools: list[ToolDefinition],
        search_fn: Callable[[str], list[SearchResult]],
        on_event: Callable[[ChatEvent], None] | None = None,
    ) -> tuple[str, list[ChatMessage]]: ...


class ConversationContextStrategy(Protocol):
    def build_context(
        self,
        history: list[ChatMessage],
    ) -> list[ChatMessage]: ...
