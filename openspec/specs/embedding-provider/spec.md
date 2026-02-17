# embedding-provider

Embedding generation contract and OpenAI adapter. Defines the `EmbeddingProvider` protocol and `EmbeddingVector` value object in the domain layer, with an OpenAI implementation in the infrastructure layer.

## Requirements

### EP-1: EmbeddingProvider protocol defines embedding generation contract

The domain layer SHALL define an `EmbeddingProvider` protocol in `domain/protocols.py` with a method `embed(texts: list[str]) → list[list[float]]` that takes a batch of text strings and returns one vector per input. The protocol SHALL also expose `provider_name: str` and `dimension: int` as properties.

#### Scenario: Protocol is defined in domain layer

- **WHEN** a developer imports from `domain/protocols.py`
- **THEN** `EmbeddingProvider` is available as a Protocol class with `embed`, `provider_name`, and `dimension`

### EP-2: EmbeddingVector value object represents a chunk's vector

The domain layer SHALL define an `EmbeddingVector` frozen dataclass with `chunk_id: str` and `vector: list[float]`. `vector` MUST be non-empty. Defined in `domain/embedding_vector.py`.

#### Scenario: Valid EmbeddingVector creation

- **WHEN** `EmbeddingVector(chunk_id="abc", vector=[0.1, 0.2, 0.3])` is created
- **THEN** the object is created successfully with the given values

#### Scenario: Empty vector rejected

- **WHEN** `EmbeddingVector(chunk_id="abc", vector=[])` is created
- **THEN** a `BookError` with code `EMBEDDING_FAILED` is raised

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

### EP-4: Provider exposes metadata

The OpenAI adapter SHALL return `"openai"` for `provider_name` and `1536` for `dimension`.

#### Scenario: Provider name

- **WHEN** `provider_name` is accessed
- **THEN** the value `"openai"` is returned

#### Scenario: Dimension

- **WHEN** `dimension` is accessed
- **THEN** the value `1536` is returned

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
