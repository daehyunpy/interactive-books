## 1. Shared Retry Utility

- [x] 1.1 Create `infra/retry.py` with `retry_with_backoff(fn, *, retryable_errors, max_retries, base_delay, max_delay, on_retry)` — exponential backoff with jitter, capped at `max_delay`
- [x] 1.2 Tests for `retry_with_backoff`: succeeds first try, retries and succeeds, retries exhausted re-raises, non-retryable error raises immediately, `on_retry` callback invoked, `max_retries=0` disables retry, delay capped at `max_delay`

## 2. OpenAI Adapter Integration

- [x] 2.1 Add retry constructor parameters (`max_retries`, `base_delay`, `max_delay`, `on_retry`) to `EmbeddingProvider` in `infra/embeddings/openai.py` (EP-5)
- [x] 2.2 Refactor `embed()` to use `retry_with_backoff` with `retryable_errors=(openai.RateLimitError,)` — non-rate-limit `OpenAIError` still raises `BookError` immediately (EP-3 modified)
- [x] 2.3 Tests for OpenAI adapter retry: rate-limit retries and succeeds, retries exhausted raises `BookError`, non-rate-limit error raises immediately, default constructor retry defaults

## 3. CLI Verbose Output

- [x] 3.1 Wire `on_retry` callback in `main.py` `embed` command when `--verbose` is set — print `[verbose] Rate limited, retrying in {delay:.1f}s (attempt {n}/{max})`
