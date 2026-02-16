## ADDED Requirements

### Requirement: Anthropic adapter implements ChatProvider

The infrastructure layer SHALL provide a `ChatProvider` adapter in `infra/llm/anthropic.py` that uses the Anthropic Python SDK's `messages.create()` API. Default model: `claude-sonnet-4-5-20250514`.

#### Scenario: Successful chat call
- **WHEN** `chat(messages)` is called with valid messages including a system message
- **THEN** the Anthropic API is called with the system prompt as the `system` parameter and remaining messages as the `messages` parameter, and the response text is returned

#### Scenario: System message extraction
- **WHEN** messages include a `ChatMessage(role="system", ...)` entry
- **THEN** the adapter extracts it and passes it via the `system` parameter, not in the messages array

#### Scenario: API error handling
- **WHEN** the Anthropic API raises an error
- **THEN** an `LLMError` with code `API_CALL_FAILED` is raised with a descriptive message

#### Scenario: Model name property
- **WHEN** `model_name` is accessed
- **THEN** the configured model name string is returned
