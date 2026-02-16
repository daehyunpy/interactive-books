from anthropic import Anthropic, APIError
from interactive_books.domain.errors import LLMError, LLMErrorCode
from interactive_books.domain.prompt_message import PromptMessage
from interactive_books.domain.protocols import ChatProvider as ChatProviderPort

MODEL = "claude-sonnet-4-5-20250514"
MAX_TOKENS = 4096


class ChatProvider(ChatProviderPort):
    def __init__(self, api_key: str) -> None:
        self._client = Anthropic(api_key=api_key)
        self._model = MODEL

    @property
    def model_name(self) -> str:
        return self._model

    def chat(self, messages: list[PromptMessage]) -> str:
        system_text = None
        api_messages: list[dict[str, str]] = []

        for msg in messages:
            if msg.role == "system":
                system_text = msg.content
            else:
                api_messages.append({"role": msg.role, "content": msg.content})

        try:
            kwargs: dict = {
                "model": self._model,
                "max_tokens": MAX_TOKENS,
                "messages": api_messages,
            }
            if system_text is not None:
                kwargs["system"] = system_text

            response = self._client.messages.create(**kwargs)
        except APIError as e:
            raise LLMError(
                LLMErrorCode.API_CALL_FAILED,
                f"Anthropic API error: {e}",
            ) from e

        return response.content[0].text
