from dataclasses import FrozenInstanceError

import pytest
from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.domain.page_content import PageContent


class TestPageContentCreation:
    def test_create_valid_page_content(self) -> None:
        page = PageContent(page_number=1, text="Hello world")
        assert page.page_number == 1
        assert page.text == "Hello world"

    def test_page_number_zero_raises(self) -> None:
        with pytest.raises(BookError) as exc_info:
            PageContent(page_number=0, text="Hello")
        assert exc_info.value.code == BookErrorCode.PARSE_FAILED

    def test_page_number_negative_raises(self) -> None:
        with pytest.raises(BookError) as exc_info:
            PageContent(page_number=-1, text="Hello")
        assert exc_info.value.code == BookErrorCode.PARSE_FAILED

    def test_empty_text_is_allowed(self) -> None:
        page = PageContent(page_number=1, text="")
        assert page.text == ""


class TestPageContentImmutability:
    def test_page_content_is_frozen(self) -> None:
        page = PageContent(page_number=1, text="Hello")
        with pytest.raises(FrozenInstanceError):
            page.text = "modified"  # type: ignore[misc]
