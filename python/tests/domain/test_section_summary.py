from dataclasses import FrozenInstanceError

import pytest
from interactive_books.domain.errors import BookError, BookErrorCode
from interactive_books.domain.section_summary import KeyStatement, SectionSummary


class TestKeyStatement:
    def test_create_valid(self) -> None:
        ks = KeyStatement(statement="The author argues for X", page=5)
        assert ks.statement == "The author argues for X"
        assert ks.page == 5

    def test_empty_statement_raises(self) -> None:
        with pytest.raises(BookError) as exc_info:
            KeyStatement(statement="  ", page=1)
        assert exc_info.value.code == BookErrorCode.INVALID_STATE

    def test_page_below_one_raises(self) -> None:
        with pytest.raises(BookError) as exc_info:
            KeyStatement(statement="Something", page=0)
        assert exc_info.value.code == BookErrorCode.INVALID_STATE

    def test_is_frozen(self) -> None:
        ks = KeyStatement(statement="Test", page=1)
        with pytest.raises(FrozenInstanceError):
            ks.page = 2  # type: ignore[misc]


class TestSectionSummary:
    def test_create_valid(self) -> None:
        ks = KeyStatement(statement="Key point", page=3)
        ss = SectionSummary(
            id="ss-1",
            book_id="b1",
            title="Introduction",
            start_page=1,
            end_page=5,
            summary="This section introduces the topic.",
            key_statements=[ks],
            section_index=0,
        )
        assert ss.title == "Introduction"
        assert ss.start_page == 1
        assert ss.end_page == 5
        assert len(ss.key_statements) == 1

    def test_empty_title_raises(self) -> None:
        with pytest.raises(BookError) as exc_info:
            SectionSummary(
                id="ss-1",
                book_id="b1",
                title="",
                start_page=1,
                end_page=1,
                summary="Summary text",
                key_statements=[],
                section_index=0,
            )
        assert exc_info.value.code == BookErrorCode.INVALID_STATE

    def test_empty_summary_raises(self) -> None:
        with pytest.raises(BookError) as exc_info:
            SectionSummary(
                id="ss-1",
                book_id="b1",
                title="Title",
                start_page=1,
                end_page=1,
                summary="   ",
                key_statements=[],
                section_index=0,
            )
        assert exc_info.value.code == BookErrorCode.INVALID_STATE

    def test_start_page_below_one_raises(self) -> None:
        with pytest.raises(BookError) as exc_info:
            SectionSummary(
                id="ss-1",
                book_id="b1",
                title="Title",
                start_page=0,
                end_page=1,
                summary="Summary",
                key_statements=[],
                section_index=0,
            )
        assert exc_info.value.code == BookErrorCode.INVALID_STATE

    def test_end_page_below_start_page_raises(self) -> None:
        with pytest.raises(BookError) as exc_info:
            SectionSummary(
                id="ss-1",
                book_id="b1",
                title="Title",
                start_page=5,
                end_page=3,
                summary="Summary",
                key_statements=[],
                section_index=0,
            )
        assert exc_info.value.code == BookErrorCode.INVALID_STATE

    def test_is_frozen(self) -> None:
        ss = SectionSummary(
            id="ss-1",
            book_id="b1",
            title="Title",
            start_page=1,
            end_page=1,
            summary="Summary",
            key_statements=[],
            section_index=0,
        )
        with pytest.raises(FrozenInstanceError):
            ss.title = "New"  # type: ignore[misc]
