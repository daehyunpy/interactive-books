## Why

The OpenAI embedding API enforces per-minute token limits (TPM). When embedding large books, the `EmbedBookUseCase` sends batches in rapid succession with no delay, exhausting the token budget and triggering HTTP 429 errors. The error is currently wrapped as a `BookError(EMBEDDING_FAILED)` with no retry — the entire embed operation fails and any partial progress is lost.

This will also affect the Anthropic chat API when used heavily, and any future providers with rate limits.

## What Changes

- Add a shared retry utility (`infra/retry.py`) with exponential backoff and jitter, reusable by any adapter
- Use it in the OpenAI embedding adapter for 429 (rate limit) errors
- Keep retries transparent to the domain and application layers — this is purely an infrastructure concern
- Surface retry activity in verbose CLI output so users know the system is waiting, not stuck

## Capabilities

### New Capabilities

- `retry-utility`: Shared infrastructure utility for retrying callables on transient errors with exponential backoff and jitter

### Modified Capabilities

- `embedding-provider`: The OpenAI adapter SHALL use the retry utility to retry on rate-limit errors, instead of immediately raising `BookError`

## Impact

- `infra/retry.py` — new shared retry utility (reusable across adapters)
- `infra/embeddings/openai.py` — use retry utility around the API call
- `main.py` — surface retry attempts in verbose output via `on_retry` callback
- No domain or protocol changes required — the `EmbeddingProvider.embed` contract is unchanged
- No new dependencies — manual implementation (~15 lines)
