from unittest.mock import patch

import pytest
from interactive_books.infra.retry import retry_with_backoff


class _TransientError(Exception):
    pass


class _PermanentError(Exception):
    pass


class TestRetryWithBackoff:
    def test_succeeds_on_first_attempt(self) -> None:
        result = retry_with_backoff(
            lambda: "ok",
            retryable_errors=(_TransientError,),
        )
        assert result == "ok"

    @patch("interactive_books.infra.retry.time.sleep")
    def test_retries_on_retryable_error_and_succeeds(self, mock_sleep) -> None:
        calls = 0

        def fn():
            nonlocal calls
            calls += 1
            if calls < 3:
                raise _TransientError("transient")
            return "recovered"

        result = retry_with_backoff(
            fn,
            retryable_errors=(_TransientError,),
            base_delay=1.0,
        )
        assert result == "recovered"
        assert calls == 3
        assert mock_sleep.call_count == 2

    @patch("interactive_books.infra.retry.time.sleep")
    def test_retries_exhausted_re_raises(self, mock_sleep) -> None:
        def fn():
            raise _TransientError("always fails")

        with pytest.raises(_TransientError, match="always fails"):
            retry_with_backoff(
                fn,
                retryable_errors=(_TransientError,),
                max_retries=3,
                base_delay=0.0,
            )
        assert mock_sleep.call_count == 3

    def test_non_retryable_error_raises_immediately(self) -> None:
        calls = 0

        def fn():
            nonlocal calls
            calls += 1
            raise _PermanentError("permanent")

        with pytest.raises(_PermanentError, match="permanent"):
            retry_with_backoff(
                fn,
                retryable_errors=(_TransientError,),
                max_retries=5,
            )
        assert calls == 1

    @patch("interactive_books.infra.retry.time.sleep")
    def test_on_retry_callback_invoked(self, mock_sleep) -> None:
        retries_seen: list[tuple[int, float]] = []

        def on_retry(attempt: int, delay: float) -> None:
            retries_seen.append((attempt, delay))

        calls = 0

        def fn():
            nonlocal calls
            calls += 1
            if calls < 3:
                raise _TransientError("transient")
            return "ok"

        retry_with_backoff(
            fn,
            retryable_errors=(_TransientError,),
            base_delay=1.0,
            on_retry=on_retry,
        )
        assert len(retries_seen) == 2
        assert retries_seen[0][0] == 1
        assert retries_seen[1][0] == 2
        assert all(delay > 0 for _, delay in retries_seen)

    def test_max_retries_zero_disables_retry(self) -> None:
        calls = 0

        def fn():
            nonlocal calls
            calls += 1
            raise _TransientError("no retry")

        with pytest.raises(_TransientError, match="no retry"):
            retry_with_backoff(
                fn,
                retryable_errors=(_TransientError,),
                max_retries=0,
            )
        assert calls == 1

    @patch("interactive_books.infra.retry.time.sleep")
    def test_delay_capped_at_max_delay(self, mock_sleep) -> None:
        calls = 0

        def fn():
            nonlocal calls
            calls += 1
            if calls <= 5:
                raise _TransientError("transient")
            return "ok"

        retry_with_backoff(
            fn,
            retryable_errors=(_TransientError,),
            max_retries=6,
            base_delay=10.0,
            max_delay=5.0,
        )
        for call in mock_sleep.call_args_list:
            delay = call[0][0]
            assert delay <= 5.0
