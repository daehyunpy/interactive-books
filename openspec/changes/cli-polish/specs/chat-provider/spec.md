# chat-provider

Delta spec for adding token usage to `ChatResponse` and populating it from the Anthropic adapter.

## ADDED Requirements

### Requirement: TokenUsage value object

The domain layer SHALL define a `TokenUsage` frozen dataclass in `domain/tool.py` with fields:
- `input_tokens: int`
- `output_tokens: int`

#### Scenario: TokenUsage creation

- **WHEN** a `TokenUsage` is created with `input_tokens=1234` and `output_tokens=567`
- **THEN** the object is frozen and has those field values

## MODIFIED Requirements

### CP-3: ChatProvider.chat_with_tools() method (MODIFIED)

The `ChatProvider.chat_with_tools()` method SHALL return a `ChatResponse` that includes an optional `usage: TokenUsage | None` field. Providers that support token usage reporting SHALL populate this field from the API response metadata. Providers that do not support it SHALL return `None`.

The `ChatResponse` dataclass gains a new field:
- `usage: TokenUsage | None = None`

**Changes from original:**
- `ChatResponse` now includes `usage` field for token count reporting
- Existing code that doesn't inspect `usage` is unaffected (field defaults to `None`)

#### Scenario: Anthropic adapter populates token usage

- **WHEN** `chat_with_tools()` is called on the Anthropic adapter and the API returns usage data
- **THEN** the returned `ChatResponse` has `usage` populated with `input_tokens` and `output_tokens`

#### Scenario: Provider without usage support

- **WHEN** `chat_with_tools()` is called on a provider that doesn't report token usage
- **THEN** the returned `ChatResponse` has `usage=None`

#### Scenario: Backward compatibility

- **WHEN** existing code accesses `ChatResponse.text` or `ChatResponse.tool_invocations`
- **THEN** behavior is unchanged; the new `usage` field defaults to `None`

### CP-2: ChatProvider protocol defines LLM chat abstraction (MODIFIED)

The `ChatProvider` protocol's `chat()` method SHALL also return token usage. The return type changes from `str` to `ChatResponse` to provide consistent access to token usage across both `chat()` and `chat_with_tools()`.

Wait — changing `chat()` return type from `str` to `ChatResponse` is a breaking change affecting all callers. This is too invasive for a polish phase.

**Revised:** The `chat()` method return type remains `str`. Token usage is only available via `chat_with_tools()`. The `ChatWithBookUseCase` already uses `chat_with_tools()` exclusively via the retrieval strategy, so it has access to `ChatResponse.usage`.

No changes to `CP-2`.

**Changes from original:**
- No change to `chat()` method signature
- Token usage available only through `chat_with_tools()` return value

#### Scenario: chat() return type unchanged

- **WHEN** `chat_provider.chat(messages)` is called
- **THEN** it returns a `str` (unchanged)

#### Scenario: chat_with_tools() includes usage

- **WHEN** `chat_provider.chat_with_tools(messages, tools)` is called
- **THEN** it returns a `ChatResponse` with `text`, `tool_invocations`, and `usage` fields
