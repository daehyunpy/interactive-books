# chat-provider

Delta spec for ChatProvider protocol extensions to support tool-use in agentic conversation. Adds `chat_with_tools()` method, extends `PromptMessage` valid roles, and references new domain value objects.

## ADDED Requirements

### CP-3: ChatProvider.chat_with_tools() method

The `ChatProvider` protocol SHALL include a `chat_with_tools(messages: list[PromptMessage], tools: list[ToolDefinition]) -> ChatResponse` method. This method sends messages to the LLM along with tool definitions, and returns a `ChatResponse` that contains either a text response or a tool invocation request.

The method SHALL handle the LLM's native tool-use API format and translate it into domain value objects (`ChatResponse`, `ToolInvocation`).

#### Scenario: Provider returns text

- **WHEN** `chat_with_tools()` is called and the LLM responds with text
- **THEN** a `ChatResponse` with `text` populated is returned

#### Scenario: Provider returns tool invocation

- **WHEN** `chat_with_tools()` is called and the LLM requests a tool call
- **THEN** a `ChatResponse` with `tool_invocation` populated is returned, containing the tool name and parsed arguments

#### Scenario: API errors wrapped in LLMError

- **WHEN** `chat_with_tools()` encounters an API error
- **THEN** an `LLMError` with code `API_CALL_FAILED` is raised

#### Scenario: Empty tools list behaves like regular chat

- **WHEN** `chat_with_tools()` is called with `tools=[]`
- **THEN** the LLM responds as if no tools are available (text-only response)

## MODIFIED Requirements

### CP-1: PromptMessage domain model represents an LLM message (MODIFIED)

The domain layer defines a `PromptMessage` frozen dataclass in `domain/prompt_message.py` with fields: `role: str` and `content: str`. Valid roles are `"system"`, `"user"`, `"assistant"`, and `"tool_result"`.

**Changes from original:**
- `"tool_result"` added as a valid role value to support passing tool execution results back to the LLM in the message list

This is separate from the `ChatMessage` entity in `domain/chat.py` which has `id`, `conversation_id`, `role: MessageRole`, `content`, and `created_at` for persisting chat history.

#### Scenario: PromptMessage with tool_result role

- **WHEN** a `PromptMessage` is created with `role="tool_result"`
- **THEN** the message is valid

#### Scenario: PromptMessage with existing roles

- **WHEN** a `PromptMessage` is created with `role="system"`, `"user"`, or `"assistant"`
- **THEN** the message is valid (backward compatible)

### CP-2: ChatProvider protocol defines LLM chat abstraction (MODIFIED)

The domain layer defines a `ChatProvider` protocol in `domain/protocols.py` with:

- A `model_name` property returning `str`
- A `chat(messages: list[PromptMessage]) -> str` method that sends messages to an LLM and returns the full response text
- A `chat_with_tools(messages: list[PromptMessage], tools: list[ToolDefinition]) -> ChatResponse` method that sends messages with tool definitions and returns a `ChatResponse`

**Changes from original:**
- `chat_with_tools()` method added to the protocol
- Protocol now references `ToolDefinition` and `ChatResponse` from `domain/tool_use.py`
- Existing `chat()` method is preserved for backward compatibility

#### Scenario: Protocol has both methods

- **WHEN** a `ChatProvider` implementation is inspected
- **THEN** it implements both `chat()` and `chat_with_tools()`

#### Scenario: Backward compatibility

- **WHEN** existing code calls `chat_provider.chat(messages)`
- **THEN** it continues to work without modification
