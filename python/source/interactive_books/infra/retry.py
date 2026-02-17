import random
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

JITTER_FACTOR = 0.5


def retry_with_backoff(
    fn: Callable[[], T],
    *,
    retryable_errors: tuple[type[BaseException], ...],
    max_retries: int = 6,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    on_retry: Callable[[int, float], None] | None = None,
) -> T:
    """Retry a callable on transient errors with exponential backoff and jitter."""
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except retryable_errors:
            if attempt >= max_retries:
                raise
            delay = min(
                base_delay * (2**attempt) * (1 + random.random() * JITTER_FACTOR),
                max_delay,
            )
            if on_retry is not None:
                on_retry(attempt + 1, delay)
            time.sleep(delay)
    raise RuntimeError("unreachable")
