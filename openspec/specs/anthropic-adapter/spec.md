# anthropic-adapter

Anthropic SDK implementation of the ChatProvider protocol. Located in `python/source/interactive_books/infra/llm/anthropic.py`.

## Requirements

### AA-1: Anthropic adapter implements ChatProvider

The infrastructure layer provides a `ChatProvider` adapter in `infra/llm/anthropic.py` that uses the Anthropic Python SDK's `messages.create()` API. Default model: `claude-sonnet-4-5-20250514`.

- System messages (`PromptMessage(role="system", ...)`) are extracted from the message list and passed via the `system` parameter, not in the messages array
- API errors are wrapped in `LLMError` with code `API_CALL_FAILED`
- The `model_name` property returns the configured model name string
