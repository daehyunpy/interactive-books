from anthropic import Anthropic, APIError
from interactive_books.domain.errors import LLMError, LLMErrorCode
from interactive_books.domain.prompt_message import PromptMessage
from interactive_books.domain.protocols import ChatProvider as ChatProviderPort

MODEL = "claude-sonnet-4-5-20250929"
MAX_TOKENS = 4096


class ChatProvider(ChatProviderPort):
    def __init__(self, api_key: str) -> None:
        self._client = Anthropic(api_key=api_key)
        self._model = MODEL

    @property
    def model_name(self) -> str:
        return self._model

    def chat(self, messages: list[PromptMessage]) -> str:
        system_messages = [m.content for m in messages if m.role == "system"]
        api_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role != "system"
        ]

        try:
            kwargs: dict = {
                "model": self._model,
                "max_tokens": MAX_TOKENS,
                "messages": api_messages,
            }
            if system_messages:
                kwargs["system"] = system_messages[0]

            response = self._client.messages.create(**kwargs)
        except APIError as e:
            raise LLMError(
                LLMErrorCode.API_CALL_FAILED,
                f"Anthropic API error: {e}",
            ) from e

        return response.content[0].text
