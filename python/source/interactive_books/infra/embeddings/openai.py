from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.domain.protocols import (
    EmbeddingProvider as EmbeddingProviderPort,
)
from openai import OpenAI, OpenAIError

MODEL = "text-embedding-3-small"
DIMENSION = 1536


class EmbeddingProvider(EmbeddingProviderPort):
    def __init__(self, api_key: str) -> None:
        self._client = OpenAI(api_key=api_key)

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def dimension(self) -> int:
        return DIMENSION

    def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            response = self._client.embeddings.create(model=MODEL, input=texts)
        except OpenAIError as e:
            raise BookError(
                BookErrorCode.EMBEDDING_FAILED,
                f"OpenAI embedding failed: {e}",
            ) from e

        sorted_data = sorted(response.data, key=lambda d: d.index)
        return [d.embedding for d in sorted_data]
