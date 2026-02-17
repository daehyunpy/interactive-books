# chat-provider

LLM message and chat protocol definitions in the domain layer.

## Requirements

### CP-1: PromptMessage domain model represents an LLM message

The domain layer defines a `PromptMessage` frozen dataclass in `domain/prompt_message.py` with fields: `role: str` and `content: str`. Valid roles are `"system"`, `"user"`, and `"assistant"`.

This is separate from the `ChatMessage` entity in `domain/chat.py` which has `id`, `book_id`, `role: MessageRole`, `content`, and `created_at` for persisting chat history.

### CP-2: ChatProvider protocol defines LLM chat abstraction

The domain layer defines a `ChatProvider` protocol in `domain/protocols.py` with:
- A `model_name` property returning `str`
- A `chat(messages: list[PromptMessage]) → str` method that sends messages to an LLM and returns the full response text
