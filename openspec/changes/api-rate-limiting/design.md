## Context

The OpenAI API enforces token-per-minute (TPM) rate limits. When embedding large books, `EmbedBookUseCase` sends batches of 100 chunks in rapid succession. A typical book with 500+ chunks can exceed the TPM limit within seconds, triggering HTTP 429 errors.

Currently, the OpenAI adapter in `infra/embeddings/openai.py` catches all `OpenAIError` exceptions and wraps them as `BookError(EMBEDDING_FAILED)`. This means rate-limit errors are treated identically to permanent failures — no retry, immediate abort.

The Anthropic chat API has the same rate-limit behavior (HTTP 429), and future providers will too. The retry logic should be reusable.

## Goals / Non-Goals

**Goals:**

- Provide a shared retry utility reusable by any infrastructure adapter
- Retry rate-limited OpenAI embedding calls with exponential backoff and jitter
- Keep retry logic entirely in the infrastructure layer — no protocol or domain changes
- Provide visibility into retry behavior via verbose CLI output
- Eventually give up after a reasonable number of attempts

**Non-Goals:**

- Pre-emptive throttling or token counting before API calls
- Wiring retry into the Anthropic adapter in this change (future use — the utility is ready)
- Retry for non-rate-limit errors (network errors, auth errors, server errors)

## Decisions

### 1. Manual retry implementation (no tenacity dependency)

**Decision:** Implement exponential backoff with jitter manually rather than adding a `tenacity` dependency.

**Rationale:** The retry logic is ~15 lines of code. Adding a third-party dependency for this is overkill. The project has minimal dependencies and we should keep it that way. The manual implementation is also easier to test with deterministic sleep mocking.

**Alternatives considered:**

- `tenacity` library: well-tested, but adds a dependency for a trivial amount of code
- `backoff` library: same issue

### 2. Shared retry utility in `infra/retry.py`

**Decision:** Extract retry logic into a standalone function `retry_with_backoff(fn, retryable_errors, ...)` in `infra/retry.py`. Each adapter calls this function, passing its own error types.

**Rationale:** The retry algorithm (exponential backoff + jitter) is identical regardless of which API is being called. Only the retryable error type differs: `openai.RateLimitError` for OpenAI, `anthropic.RateLimitError` for Anthropic. A shared function avoids copy-paste and ensures consistent behavior. It earns its existence with 2 known consumers (OpenAI embeddings now, Anthropic chat in the near future).

**Alternatives considered:**

- Retry inside each adapter: simpler initially, but duplicates the same ~15 lines per adapter. The second adapter would trigger a refactor anyway.
- Decorator pattern: clean syntax but harder to test, hides control flow, and callback wiring becomes awkward.

### 3. Retry only on rate-limit errors, not all API errors

**Decision:** The retry utility accepts a `retryable_errors` tuple. The OpenAI adapter passes `(openai.RateLimitError,)`. All other errors propagate immediately.

**Rationale:** Rate-limit errors are transient and guaranteed to resolve with time. Auth errors, invalid request errors, and server errors are not helped by retrying. Retrying them wastes time and masks real problems. The `retryable_errors` parameter makes this explicit per-adapter.

### 4. Exponential backoff with jitter

**Decision:** Use exponential backoff with randomized jitter: `delay = min(base_delay * (2 ^ attempt) * (1 + random(0, jitter_factor)), max_delay)`. Default: base 1s, max 60s, jitter factor 0.5, max retries 6.

**Rationale:** OpenAI's own documentation recommends exponential backoff with jitter. The jitter prevents thundering herd when multiple processes retry simultaneously. 6 retries with exponential backoff covers ~2 minutes of wait time, which aligns with the 1-minute TPM window rolling over.

### 5. Retry function signature

**Decision:** `retry_with_backoff(fn, *, retryable_errors, max_retries=6, base_delay=1.0, max_delay=60.0, on_retry=None)` where `fn` is a zero-argument callable, `retryable_errors` is a tuple of exception types, and `on_retry` is an optional `Callable[[int, float], None]` invoked with `(attempt, delay)` before each sleep.

**Rationale:** Zero-argument callable keeps the interface simple — callers wrap their specific API call in a lambda or closure. Required `retryable_errors` forces each caller to be explicit about what's retryable. Optional `on_retry` decouples from logging/CLI frameworks.

### 6. OpenAI adapter delegates to retry utility

**Decision:** The OpenAI `EmbeddingProvider` constructor accepts `max_retries`, `base_delay`, `max_delay`, and `on_retry` parameters. The `embed()` method wraps `self._client.embeddings.create()` in a closure and passes it to `retry_with_backoff`.

**Rationale:** Callers of the adapter (CLI, use cases) can configure retry behavior without knowing the retry implementation. Tests can use `max_retries=0` for fast failure and `base_delay=0` for no-wait tests.

## Risks / Trade-offs

**[Risk] Retries extend total embedding time significantly** → Mitigation: Max delay is capped at 60s. With 6 retries at exponential backoff, worst case is ~2 minutes of waiting. This is acceptable for a batch operation that takes minutes anyway.

**[Risk] Partial batch success not resumable** → Mitigation: This is an existing limitation from the embed pipeline design. If retry exhausts all attempts on batch 3/5, batches 1-2 are stored but cleaned up on failure (EPL-4). Incremental embedding is a future enhancement, not in scope here.

**[Trade-off] No pre-emptive throttling** → We could count tokens before each batch and sleep proactively. This adds complexity (need a tokenizer) for marginal benefit. Reactive retry is simpler and handles the actual API response, which is the ground truth for rate limits.

**[Trade-off] Shared utility vs inline** → Adds one file (`infra/retry.py`) and a level of indirection. Worth it for consistency across adapters and testability of the retry algorithm in isolation.

## Open Questions

_None — the approach is straightforward and well-supported by OpenAI's own documentation._
