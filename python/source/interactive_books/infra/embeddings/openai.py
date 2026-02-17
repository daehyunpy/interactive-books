from collections.abc import Callable

from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.domain.protocols import (
    EmbeddingProvider as EmbeddingProviderPort,
)
from interactive_books.infra.retry import retry_with_backoff
from openai import OpenAI, OpenAIError, RateLimitError

MODEL = "text-embedding-3-small"
DIMENSION = 1536


class EmbeddingProvider(EmbeddingProviderPort):
    def __init__(
        self,
        api_key: str,
        *,
        max_retries: int = 6,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        on_retry: Callable[[int, float], None] | None = None,
    ) -> None:
        self._client = OpenAI(api_key=api_key)
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._max_delay = max_delay
        self._on_retry = on_retry

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def dimension(self) -> int:
        return DIMENSION

    def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            response = retry_with_backoff(
                lambda: self._client.embeddings.create(model=MODEL, input=texts),
                retryable_errors=(RateLimitError,),
                max_retries=self._max_retries,
                base_delay=self._base_delay,
                max_delay=self._max_delay,
                on_retry=self._on_retry,
            )
        except OpenAIError as e:
            raise BookError(
                BookErrorCode.EMBEDDING_FAILED,
                f"OpenAI embedding failed: {e}",
            ) from e

        sorted_data = sorted(response.data, key=lambda d: d.index)
        return [d.embedding for d in sorted_data]
