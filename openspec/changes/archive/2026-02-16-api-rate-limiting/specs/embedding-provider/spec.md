## MODIFIED Requirements

### EP-3: OpenAI embedding adapter implements EmbeddingProvider

The system SHALL provide an `EmbeddingProvider` adapter in `infra/embeddings/openai.py` that uses the OpenAI Python SDK to generate embeddings via the `text-embedding-3-small` model (1536 dimensions). The adapter SHALL use the shared `retry_with_backoff` utility to retry on rate-limit errors (HTTP 429), up to a configurable maximum number of retries (default: 6).

#### Scenario: Embed a single text

- **WHEN** `embed(["Hello world"])` is called
- **THEN** a list containing one vector of 1536 floats is returned

#### Scenario: Embed a batch of texts

- **WHEN** `embed(["text one", "text two", "text three"])` is called
- **THEN** a list of 3 vectors is returned, each with 1536 floats

#### Scenario: API key not configured

- **WHEN** the OpenAI API key is missing or invalid
- **THEN** a `BookError` with code `EMBEDDING_FAILED` is raised with a descriptive message

#### Scenario: Rate limit error triggers retry

- **WHEN** the OpenAI API returns HTTP 429 (rate limit exceeded)
- **THEN** the adapter retries via `retry_with_backoff` with `retryable_errors=(openai.RateLimitError,)`

#### Scenario: Rate limit error resolves on retry

- **WHEN** the OpenAI API returns HTTP 429 on the first attempt but succeeds on a subsequent attempt
- **THEN** the embedding result is returned as if the first attempt had succeeded

#### Scenario: Rate limit retries exhausted

- **WHEN** the OpenAI API returns HTTP 429 on every attempt up to max_retries
- **THEN** a `BookError` with code `EMBEDDING_FAILED` is raised wrapping the last rate-limit error

#### Scenario: Non-rate-limit API error does not retry

- **WHEN** the OpenAI API returns a non-429 error (network, auth, server error)
- **THEN** a `BookError` with code `EMBEDDING_FAILED` is raised immediately without retrying

#### Scenario: Retry callback is invoked

- **WHEN** a rate-limit retry occurs and an `on_retry` callback is configured
- **THEN** the callback is called with the attempt number and delay before sleeping

## ADDED Requirements

### EP-5: OpenAI adapter accepts retry configuration

The OpenAI `EmbeddingProvider` constructor SHALL accept optional parameters `max_retries: int` (default 6), `base_delay: float` (default 1.0), `max_delay: float` (default 60.0), and `on_retry: Callable[[int, float], None] | None` (default None). These parameters are forwarded to `retry_with_backoff` when calling the OpenAI API.

#### Scenario: Default retry configuration

- **WHEN** `EmbeddingProvider(api_key="key")` is constructed with no retry parameters
- **THEN** the provider uses max_retries=6, base_delay=1.0, max_delay=60.0, on_retry=None

#### Scenario: Custom retry configuration

- **WHEN** `EmbeddingProvider(api_key="key", max_retries=3, base_delay=0.5)` is constructed
- **THEN** the provider uses the specified values for retry behavior

#### Scenario: Disable retries

- **WHEN** `EmbeddingProvider(api_key="key", max_retries=0)` is constructed and a rate-limit error occurs
- **THEN** the error is raised immediately without retrying
