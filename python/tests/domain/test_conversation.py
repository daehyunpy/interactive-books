from datetime import datetime, timezone

import pytest
from interactive_books.domain.conversation import Conversation
from interactive_books.domain.errors import BookError, BookErrorCode


class TestConversationCreation:
    def test_create_with_all_fields(self) -> None:
        now = datetime.now(timezone.utc)
        conv = Conversation(
            id="c1", book_id="b1", title="About chapter 3", created_at=now
        )
        assert conv.id == "c1"
        assert conv.book_id == "b1"
        assert conv.title == "About chapter 3"
        assert conv.created_at == now

    def test_create_with_defaults(self) -> None:
        conv = Conversation(id="c1", book_id="b1", title="My conversation")
        assert conv.created_at is not None

    def test_empty_title_raises(self) -> None:
        with pytest.raises(BookError) as exc_info:
            Conversation(id="c1", book_id="b1", title="")
        assert exc_info.value.code == BookErrorCode.INVALID_STATE

    def test_whitespace_only_title_raises(self) -> None:
        with pytest.raises(BookError) as exc_info:
            Conversation(id="c1", book_id="b1", title="   ")
        assert exc_info.value.code == BookErrorCode.INVALID_STATE


class TestConversationRename:
    def test_rename_updates_title(self) -> None:
        conv = Conversation(id="c1", book_id="b1", title="Old title")
        conv.rename("New title")
        assert conv.title == "New title"

    def test_rename_to_empty_raises(self) -> None:
        conv = Conversation(id="c1", book_id="b1", title="Valid")
        with pytest.raises(BookError) as exc_info:
            conv.rename("")
        assert exc_info.value.code == BookErrorCode.INVALID_STATE

    def test_rename_to_whitespace_raises(self) -> None:
        conv = Conversation(id="c1", book_id="b1", title="Valid")
        with pytest.raises(BookError) as exc_info:
            conv.rename("   ")
        assert exc_info.value.code == BookErrorCode.INVALID_STATE
