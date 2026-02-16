from unittest.mock import MagicMock, patch

import pytest
from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.infra.embeddings.openai import EmbeddingProvider
from openai import APIConnectionError, AuthenticationError


class TestEmbeddingProviderMetadata:
    def test_provider_name_is_openai(self) -> None:
        provider = EmbeddingProvider(api_key="test-key")
        assert provider.provider_name == "openai"

    def test_dimension_is_1536(self) -> None:
        provider = EmbeddingProvider(api_key="test-key")
        assert provider.dimension == 1536


class TestEmbedBatch:
    def test_embed_single_text(self) -> None:
        mock_embedding = MagicMock()
        mock_embedding.embedding = [0.1] * 1536
        mock_embedding.index = 0

        mock_response = MagicMock()
        mock_response.data = [mock_embedding]

        provider = EmbeddingProvider(api_key="test-key")
        with patch.object(
            provider._client.embeddings, "create", return_value=mock_response
        ):
            result = provider.embed(["Hello world"])

        assert len(result) == 1
        assert len(result[0]) == 1536

    def test_embed_multiple_texts(self) -> None:
        mock_embeddings = []
        for i in range(3):
            mock_emb = MagicMock()
            mock_emb.embedding = [0.1 * (i + 1)] * 1536
            mock_emb.index = i
            mock_embeddings.append(mock_emb)

        mock_response = MagicMock()
        mock_response.data = mock_embeddings

        provider = EmbeddingProvider(api_key="test-key")
        with patch.object(
            provider._client.embeddings, "create", return_value=mock_response
        ):
            result = provider.embed(["text one", "text two", "text three"])

        assert len(result) == 3
        for vec in result:
            assert len(vec) == 1536

    def test_results_ordered_by_index(self) -> None:
        mock_embeddings = []
        for i in [2, 0, 1]:
            mock_emb = MagicMock()
            mock_emb.embedding = [float(i)] * 4
            mock_emb.index = i
            mock_embeddings.append(mock_emb)

        mock_response = MagicMock()
        mock_response.data = mock_embeddings

        provider = EmbeddingProvider(api_key="test-key")
        with patch.object(
            provider._client.embeddings, "create", return_value=mock_response
        ):
            result = provider.embed(["a", "b", "c"])

        assert result[0][0] == 0.0
        assert result[1][0] == 1.0
        assert result[2][0] == 2.0


class TestEmbedErrors:
    def test_api_key_missing_raises_embedding_failed(self) -> None:
        provider = EmbeddingProvider(api_key="bad-key")

        mock_response = MagicMock()
        mock_response.status_code = 401
        error = AuthenticationError(
            message="Incorrect API key",
            response=mock_response,
            body=None,
        )

        with patch.object(provider._client.embeddings, "create", side_effect=error):
            with pytest.raises(BookError) as exc_info:
                provider.embed(["Hello"])
            assert exc_info.value.code == BookErrorCode.EMBEDDING_FAILED

    def test_api_connection_error_raises_embedding_failed(self) -> None:
        provider = EmbeddingProvider(api_key="test-key")

        error = APIConnectionError(request=MagicMock())

        with patch.object(provider._client.embeddings, "create", side_effect=error):
            with pytest.raises(BookError) as exc_info:
                provider.embed(["Hello"])
            assert exc_info.value.code == BookErrorCode.EMBEDDING_FAILED
