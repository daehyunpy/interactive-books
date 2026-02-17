import os

import pytest
from interactive_books.domain.prompt_message import PromptMessage
from interactive_books.infra.llm.anthropic import ChatProvider

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set",
    ),
]


class TestAnthropicChatIntegration:
    def test_chat_returns_response(self) -> None:
        provider = ChatProvider(api_key=os.environ["ANTHROPIC_API_KEY"])
        result = provider.chat(
            [PromptMessage(role="user", content="Reply with exactly: hello")]
        )
        assert len(result) > 0
