from unittest.mock import patch

import typer.testing
from interactive_books.domain.section_summary import KeyStatement, SectionSummary
from interactive_books.main import app

runner = typer.testing.CliRunner()


def _sample_summaries() -> list[SectionSummary]:
    return [
        SectionSummary(
            id="s1",
            book_id="book-1",
            title="Introduction",
            start_page=1,
            end_page=5,
            summary="The book begins with the setting.",
            key_statements=[
                KeyStatement(statement="The town was quiet.", page=2),
            ],
            section_index=0,
        ),
        SectionSummary(
            id="s2",
            book_id="book-1",
            title="The Conflict",
            start_page=6,
            end_page=12,
            summary="The main conflict is introduced.",
            key_statements=[],
            section_index=1,
        ),
    ]


class TestSummarizeCommand:
    def test_displays_summaries(self) -> None:
        summaries = _sample_summaries()

        with (
            patch("interactive_books.main._open_db"),
            patch("interactive_books.main._require_env", return_value="fake-key"),
            patch(
                "interactive_books.infra.llm.anthropic.ChatProvider"
            ),
            patch(
                "interactive_books.app.summarize.SummarizeBookUseCase"
            ) as mock_use_case_cls,
        ):
            mock_use_case_cls.return_value.execute.return_value = summaries

            result = runner.invoke(app, ["summarize", "book-1"])

        assert result.exit_code == 0
        assert "2 section(s) summarized" in result.output
        assert "Introduction" in result.output
        assert "pp.1-5" in result.output
        assert "The town was quiet." in result.output
        assert "The Conflict" in result.output

    def test_regenerate_flag_passed_to_use_case(self) -> None:
        with (
            patch("interactive_books.main._open_db"),
            patch("interactive_books.main._require_env", return_value="fake-key"),
            patch(
                "interactive_books.infra.llm.anthropic.ChatProvider"
            ),
            patch(
                "interactive_books.app.summarize.SummarizeBookUseCase"
            ) as mock_use_case_cls,
        ):
            mock_use_case_cls.return_value.execute.return_value = []

            runner.invoke(app, ["summarize", "book-1", "--regenerate"])

            mock_use_case_cls.return_value.execute.assert_called_once_with(
                "book-1", regenerate=True
            )

    def test_error_displays_message(self) -> None:
        from interactive_books.domain.errors import BookError, BookErrorCode

        with (
            patch("interactive_books.main._open_db"),
            patch("interactive_books.main._require_env", return_value="fake-key"),
            patch(
                "interactive_books.infra.llm.anthropic.ChatProvider"
            ),
            patch(
                "interactive_books.app.summarize.SummarizeBookUseCase"
            ) as mock_use_case_cls,
        ):
            mock_use_case_cls.return_value.execute.side_effect = BookError(
                BookErrorCode.NOT_FOUND, "Book 'x' not found"
            )

            result = runner.invoke(app, ["summarize", "x"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()
