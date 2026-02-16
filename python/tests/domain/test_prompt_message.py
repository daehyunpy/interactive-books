import pytest
from interactive_books.domain.prompt_message import PromptMessage


class TestPromptMessage:
    def test_creation(self) -> None:
        msg = PromptMessage(role="user", content="What is this about?")

        assert msg.role == "user"
        assert msg.content == "What is this about?"

    def test_system_role(self) -> None:
        msg = PromptMessage(role="system", content="You are helpful.")

        assert msg.role == "system"

    def test_is_frozen(self) -> None:
        msg = PromptMessage(role="user", content="hello")

        with pytest.raises(AttributeError):
            msg.content = "changed"  # type: ignore[misc]
