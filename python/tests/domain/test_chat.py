from datetime import datetime, timezone

from interactive_books.domain.chat import ChatMessage, MessageRole


class TestMessageRole:
    def test_all_roles_exist(self) -> None:
        expected = {"user", "assistant", "tool_result"}
        actual = {role.value for role in MessageRole}
        assert actual == expected

    def test_string_values_are_lowercase(self) -> None:
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.TOOL_RESULT.value == "tool_result"


class TestChatMessage:
    def test_create_user_message(self) -> None:
        now = datetime.now(timezone.utc)
        msg = ChatMessage(
            id="m1",
            conversation_id="conv1",
            role=MessageRole.USER,
            content="What is chapter 3 about?",
            created_at=now,
        )
        assert msg.id == "m1"
        assert msg.conversation_id == "conv1"
        assert msg.role == MessageRole.USER
        assert msg.content == "What is chapter 3 about?"
        assert msg.created_at == now

    def test_create_assistant_message(self) -> None:
        msg = ChatMessage(
            id="m2",
            conversation_id="conv1",
            role=MessageRole.ASSISTANT,
            content="Chapter 3 covers...",
        )
        assert msg.role == MessageRole.ASSISTANT

    def test_create_tool_result_message(self) -> None:
        msg = ChatMessage(
            id="m3",
            conversation_id="conv1",
            role=MessageRole.TOOL_RESULT,
            content="[Pages 10-12]: Relevant passage text.",
        )
        assert msg.role == MessageRole.TOOL_RESULT
        assert msg.conversation_id == "conv1"
