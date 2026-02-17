# chat-provider

ChatProvider protocol extensions to support tool-use in agentic conversation. Includes `chat_with_tools()` method, `PromptMessage` role extensions, `TokenUsage` value object, and new domain value objects. Located in `python/source/interactive_books/domain/protocols.py` and `python/source/interactive_books/domain/tool.py`.

## Requirements

### CP-1: PromptMessage domain model represents an LLM message

The domain layer defines a `PromptMessage` frozen dataclass in `domain/prompt_message.py` with fields: `role: str` and `content: str`. Valid roles are `"system"`, `"user"`, `"assistant"`, and `"tool_result"`.

This is separate from the `ChatMessage` entity in `domain/chat.py` which has `id`, `conversation_id`, `role: MessageRole`, `content`, and `created_at` for persisting chat history.

#### Scenario: PromptMessage with tool_result role

- **WHEN** a `PromptMessage` is created with `role="tool_result"`
- **THEN** the message is valid

#### Scenario: PromptMessage with existing roles

- **WHEN** a `PromptMessage` is created with `role="system"`, `"user"`, or `"assistant"`
- **THEN** the message is valid (backward compatible)

### CP-2: ChatProvider protocol defines LLM chat abstraction

The domain layer defines a `ChatProvider` protocol in `domain/protocols.py` with:

- A `model_name` property returning `str`
- A `chat(messages: list[PromptMessage]) -> str` method that sends messages to an LLM and returns the full response text
- A `chat_with_tools(messages: list[PromptMessage], tools: list[ToolDefinition]) -> ChatResponse` method that sends messages with tool definitions and returns a `ChatResponse`

The `chat()` method return type remains `str`. Token usage is only available via `chat_with_tools()` which returns `ChatResponse` including the `usage` field.

#### Scenario: Protocol has both methods

- **WHEN** a `ChatProvider` implementation is inspected
- **THEN** it implements both `chat()` and `chat_with_tools()`

#### Scenario: Backward compatibility

- **WHEN** existing code calls `chat_provider.chat(messages)`
- **THEN** it continues to work without modification

#### Scenario: chat() return type unchanged

- **WHEN** `chat_provider.chat(messages)` is called
- **THEN** it returns a `str` (unchanged)

#### Scenario: chat_with_tools() includes usage

- **WHEN** `chat_provider.chat_with_tools(messages, tools)` is called
- **THEN** it returns a `ChatResponse` with `text`, `tool_invocations`, and `usage` fields

### CP-3: ChatProvider.chat_with_tools() method

The `ChatProvider` protocol SHALL include a `chat_with_tools(messages: list[PromptMessage], tools: list[ToolDefinition]) -> ChatResponse` method. This method sends messages to the LLM along with tool definitions, and returns a `ChatResponse` that contains either a text response or a tool invocation request.

The `ChatResponse` dataclass includes:

- `text: str | None = None`
- `tool_invocations: list[ToolInvocation] = field(default_factory=list)`
- `usage: TokenUsage | None = None`

Providers that support token usage reporting SHALL populate the `usage` field from the API response metadata. Providers that do not support it SHALL return `None`.

#### Scenario: Provider returns text

- **WHEN** `chat_with_tools()` is called and the LLM responds with text
- **THEN** a `ChatResponse` with `text` populated is returned

#### Scenario: Provider returns tool invocation

- **WHEN** `chat_with_tools()` is called and the LLM requests a tool call
- **THEN** a `ChatResponse` with `tool_invocations` populated is returned, containing the tool name and parsed arguments

#### Scenario: API errors wrapped in LLMError

- **WHEN** `chat_with_tools()` encounters an API error
- **THEN** an `LLMError` with code `API_CALL_FAILED` is raised

#### Scenario: Empty tools list behaves like regular chat

- **WHEN** `chat_with_tools()` is called with `tools=[]`
- **THEN** the LLM responds as if no tools are available (text-only response)

#### Scenario: Anthropic adapter populates token usage

- **WHEN** `chat_with_tools()` is called on the Anthropic adapter and the API returns usage data
- **THEN** the returned `ChatResponse` has `usage` populated with `input_tokens` and `output_tokens`

#### Scenario: Provider without usage support

- **WHEN** `chat_with_tools()` is called on a provider that doesn't report token usage
- **THEN** the returned `ChatResponse` has `usage=None`

### CP-4: TokenUsage value object

The domain layer SHALL define a `TokenUsage` frozen dataclass in `domain/tool.py` with fields:

- `input_tokens: int`
- `output_tokens: int`

#### Scenario: TokenUsage creation

- **WHEN** a `TokenUsage` is created with `input_tokens=1234` and `output_tokens=567`
- **THEN** the object is frozen and has those field values
