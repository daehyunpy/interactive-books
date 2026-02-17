from unittest.mock import MagicMock, patch

import pytest
from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.infra.embeddings.openai import EmbeddingProvider
from openai import APIConnectionError, AuthenticationError, RateLimitError


def _mock_embedding(index: int, vector: list[float]) -> MagicMock:
    emb = MagicMock()
    emb.index = index
    emb.embedding = vector
    return emb


def _mock_response(embeddings: list[MagicMock]) -> MagicMock:
    response = MagicMock()
    response.data = embeddings
    return response


class TestEmbeddingProviderMetadata:
    def test_provider_name_is_openai(self) -> None:
        provider = EmbeddingProvider(api_key="test-key")
        assert provider.provider_name == "openai"

    def test_dimension_is_1536(self) -> None:
        provider = EmbeddingProvider(api_key="test-key")
        assert provider.dimension == 1536


class TestEmbedBatch:
    def test_embed_single_text(self) -> None:
        response = _mock_response([_mock_embedding(0, [0.1] * 1536)])

        provider = EmbeddingProvider(api_key="test-key")
        with patch.object(provider._client.embeddings, "create", return_value=response):
            result = provider.embed(["Hello world"])

        assert len(result) == 1
        assert len(result[0]) == 1536

    def test_embed_multiple_texts(self) -> None:
        response = _mock_response(
            [_mock_embedding(i, [0.1 * (i + 1)] * 1536) for i in range(3)]
        )

        provider = EmbeddingProvider(api_key="test-key")
        with patch.object(provider._client.embeddings, "create", return_value=response):
            result = provider.embed(["text one", "text two", "text three"])

        assert len(result) == 3
        for vec in result:
            assert len(vec) == 1536

    def test_results_ordered_by_index(self) -> None:
        response = _mock_response(
            [_mock_embedding(i, [float(i)] * 4) for i in [2, 0, 1]]
        )

        provider = EmbeddingProvider(api_key="test-key")
        with patch.object(provider._client.embeddings, "create", return_value=response):
            result = provider.embed(["a", "b", "c"])

        assert result[0][0] == 0.0
        assert result[1][0] == 1.0
        assert result[2][0] == 2.0


class TestEmbedErrors:
    def test_authentication_error_raises_embedding_failed(self) -> None:
        provider = EmbeddingProvider(api_key="bad-key")

        mock_http_response = MagicMock()
        mock_http_response.status_code = 401
        error = AuthenticationError(
            message="Incorrect API key",
            response=mock_http_response,
            body=None,
        )

        with patch.object(provider._client.embeddings, "create", side_effect=error):
            with pytest.raises(BookError) as exc_info:
                provider.embed(["Hello"])
            assert exc_info.value.code == BookErrorCode.EMBEDDING_FAILED

    def test_connection_error_raises_embedding_failed(self) -> None:
        provider = EmbeddingProvider(api_key="test-key")

        error = APIConnectionError(request=MagicMock())

        with patch.object(provider._client.embeddings, "create", side_effect=error):
            with pytest.raises(BookError) as exc_info:
                provider.embed(["Hello"])
            assert exc_info.value.code == BookErrorCode.EMBEDDING_FAILED


def _rate_limit_error() -> RateLimitError:
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.headers = {}
    return RateLimitError(
        message="Rate limit exceeded",
        response=mock_response,
        body=None,
    )


class TestEmbedRetry:
    @patch("interactive_books.infra.retry.time.sleep")
    def test_rate_limit_retries_and_succeeds(self, mock_sleep) -> None:
        success_response = _mock_response([_mock_embedding(0, [0.1] * 1536)])
        calls = 0

        def side_effect(**kwargs):
            nonlocal calls
            calls += 1
            if calls < 3:
                raise _rate_limit_error()
            return success_response

        provider = EmbeddingProvider(api_key="test-key", base_delay=1.0)
        with patch.object(
            provider._client.embeddings, "create", side_effect=side_effect
        ):
            result = provider.embed(["Hello"])

        assert len(result) == 1
        assert calls == 3
        assert mock_sleep.call_count == 2

    @patch("interactive_books.infra.retry.time.sleep")
    def test_rate_limit_retries_exhausted_raises_book_error(self, mock_sleep) -> None:
        provider = EmbeddingProvider(api_key="test-key", max_retries=2, base_delay=0.0)
        with patch.object(
            provider._client.embeddings,
            "create",
            side_effect=_rate_limit_error(),
        ):
            with pytest.raises(BookError) as exc_info:
                provider.embed(["Hello"])
            assert exc_info.value.code == BookErrorCode.EMBEDDING_FAILED
            assert "Rate limit" in exc_info.value.message

    def test_non_rate_limit_error_raises_immediately(self) -> None:
        provider = EmbeddingProvider(api_key="test-key", max_retries=5)
        error = APIConnectionError(request=MagicMock())

        with patch.object(provider._client.embeddings, "create", side_effect=error):
            with pytest.raises(BookError) as exc_info:
                provider.embed(["Hello"])
            assert exc_info.value.code == BookErrorCode.EMBEDDING_FAILED

    def test_default_retry_configuration(self) -> None:
        provider = EmbeddingProvider(api_key="test-key")
        assert provider._max_retries == 6
        assert provider._base_delay == 1.0
        assert provider._max_delay == 60.0
        assert provider._on_retry is None
