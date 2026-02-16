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

The system SHALL provide an `EmbeddingProvider` adapter in `infra/embeddings/openai.py` that uses the OpenAI Python SDK to generate embeddings via the `text-embedding-3-small` model (1536 dimensions).

#### Scenario: Embed a single text
- **WHEN** `embed(["Hello world"])` is called
- **THEN** a list containing one vector of 1536 floats is returned

#### Scenario: Embed a batch of texts
- **WHEN** `embed(["text one", "text two", "text three"])` is called
- **THEN** a list of 3 vectors is returned, each with 1536 floats

#### Scenario: API key not configured
- **WHEN** the OpenAI API key is missing or invalid
- **THEN** a `BookError` with code `EMBEDDING_FAILED` is raised with a descriptive message

#### Scenario: API call fails
- **WHEN** the OpenAI API returns an error (network, rate limit, server error)
- **THEN** a `BookError` with code `EMBEDDING_FAILED` is raised wrapping the original error

### EP-4: Provider exposes metadata

The OpenAI adapter SHALL return `"openai"` for `provider_name` and `1536` for `dimension`.

#### Scenario: Provider name
- **WHEN** `provider_name` is accessed
- **THEN** the value `"openai"` is returned

#### Scenario: Dimension
- **WHEN** `dimension` is accessed
- **THEN** the value `1536` is returned
