from interactive_books.domain.chat import ChatMessage, MessageRole
from interactive_books.infra.context.full_history import ConversationContextStrategy


def _make_message(i: int) -> ChatMessage:
    return ChatMessage(
        id=f"m{i}",
        conversation_id="c1",
        role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
        content=f"Message {i}",
    )


class TestFullHistoryStrategy:
    def test_returns_all_when_under_cap(self) -> None:
        strategy = ConversationContextStrategy(max_messages=10)
        history = [_make_message(i) for i in range(5)]

        result = strategy.build_context(history)

        assert len(result) == 5
        assert [m.id for m in result] == ["m0", "m1", "m2", "m3", "m4"]

    def test_caps_at_max_messages(self) -> None:
        strategy = ConversationContextStrategy(max_messages=3)
        history = [_make_message(i) for i in range(10)]

        result = strategy.build_context(history)

        assert len(result) == 3
        assert [m.id for m in result] == ["m7", "m8", "m9"]

    def test_empty_history(self) -> None:
        strategy = ConversationContextStrategy(max_messages=10)
        result = strategy.build_context([])
        assert result == []

    def test_exact_cap_size(self) -> None:
        strategy = ConversationContextStrategy(max_messages=5)
        history = [_make_message(i) for i in range(5)]

        result = strategy.build_context(history)

        assert len(result) == 5

    def test_default_max_messages(self) -> None:
        strategy = ConversationContextStrategy()
        history = [_make_message(i) for i in range(25)]

        result = strategy.build_context(history)

        assert len(result) == 20

    def test_returns_copy_not_original(self) -> None:
        strategy = ConversationContextStrategy(max_messages=10)
        history = [_make_message(0)]

        result = strategy.build_context(history)
        result.append(_make_message(1))

        assert len(history) == 1
