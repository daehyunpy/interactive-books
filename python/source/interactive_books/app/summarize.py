import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from interactive_books.domain.chunk import Chunk
from interactive_books.domain.errors import BookError, BookErrorCode, LLMError, LLMErrorCode
from interactive_books.domain.prompt_message import PromptMessage
from interactive_books.domain.protocols import (
    BookRepository,
    ChatProvider,
    ChunkRepository,
    SummaryRepository,
)
from interactive_books.domain.section_summary import KeyStatement, SectionSummary

MAX_SECTION_TOKENS = 6000
MAX_SECTIONS = 30
APPROX_CHARS_PER_TOKEN = 4


@dataclass(frozen=True)
class Section:
    start_page: int
    end_page: int
    content: str


class SummarizeBookUseCase:
    def __init__(
        self,
        *,
        chat_provider: ChatProvider,
        book_repo: BookRepository,
        chunk_repo: ChunkRepository,
        summary_repo: SummaryRepository,
        prompts_dir: Path,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> None:
        self._chat = chat_provider
        self._book_repo = book_repo
        self._chunk_repo = chunk_repo
        self._summary_repo = summary_repo
        self._prompts_dir = prompts_dir
        self._on_progress = on_progress

    def execute(
        self, book_id: str, *, regenerate: bool = False
    ) -> list[SectionSummary]:
        book = self._book_repo.get(book_id)
        if book is None:
            raise BookError(BookErrorCode.NOT_FOUND, f"Book '{book_id}' not found")

        if not regenerate:
            cached = self._summary_repo.get_by_book(book_id)
            if cached:
                return cached

        chunks = self._chunk_repo.get_by_book(book_id)
        if not chunks:
            raise BookError(
                BookErrorCode.INVALID_STATE,
                f"Book '{book_id}' has no chunks to summarize",
            )

        sections = group_chunks_into_sections(chunks)
        sections = sections[:MAX_SECTIONS]

        template = self._load_template("summarization_prompt.md")
        summaries: list[SectionSummary] = []

        for i, section in enumerate(sections):
            if self._on_progress:
                self._on_progress(i + 1, len(sections))

            content = _truncate_to_token_budget(section.content)
            prompt = template.replace("{{start_page}}", str(section.start_page))
            prompt = prompt.replace("{{end_page}}", str(section.end_page))
            prompt = prompt.replace("{{content}}", content)

            parsed = self._summarize_section(prompt)

            key_statements = [
                KeyStatement(
                    statement=ks["statement"],
                    page=_clamp_page(ks.get("page", section.start_page), section.start_page, section.end_page),
                )
                for ks in parsed.get("key_statements", [])[:3]
            ]

            summaries.append(
                SectionSummary(
                    id=str(uuid.uuid4()),
                    book_id=book_id,
                    title=parsed.get("title", f"Section {i + 1}"),
                    start_page=section.start_page,
                    end_page=section.end_page,
                    summary=parsed.get("summary", "No summary available."),
                    key_statements=key_statements,
                    section_index=i,
                )
            )

        self._summary_repo.save_all(book_id, summaries)
        return summaries

    def _summarize_section(self, prompt: str) -> dict:  # type: ignore[type-arg]
        messages = [PromptMessage(role="user", content=prompt)]
        response = self._chat.chat(messages)
        try:
            return _parse_json_response(response)
        except ValueError:
            pass

        retry_prompt = (
            f"Your previous response was not valid JSON:\n{response}\n\n"
            "Please respond with ONLY valid JSON matching the requested format."
        )
        retry_messages = [
            PromptMessage(role="user", content=prompt),
            PromptMessage(role="assistant", content=response),
            PromptMessage(role="user", content=retry_prompt),
        ]
        retry_response = self._chat.chat(retry_messages)
        try:
            return _parse_json_response(retry_response)
        except ValueError as e:
            raise LLMError(
                LLMErrorCode.API_CALL_FAILED,
                f"Failed to parse LLM response as JSON after retry: {e}",
            ) from e

    def _load_template(self, filename: str) -> str:
        return (self._prompts_dir / filename).read_text().strip()


def group_chunks_into_sections(chunks: list[Chunk]) -> list[Section]:
    if not chunks:
        return []

    sections: list[Section] = []
    current_start = chunks[0].start_page
    current_end = chunks[0].end_page
    current_parts: list[str] = [chunks[0].content]

    for chunk in chunks[1:]:
        if chunk.start_page <= current_end + 1:
            current_end = max(current_end, chunk.end_page)
            current_parts.append(chunk.content)
        else:
            sections.append(
                Section(
                    start_page=current_start,
                    end_page=current_end,
                    content="\n\n".join(current_parts),
                )
            )
            current_start = chunk.start_page
            current_end = chunk.end_page
            current_parts = [chunk.content]

    sections.append(
        Section(
            start_page=current_start,
            end_page=current_end,
            content="\n\n".join(current_parts),
        )
    )

    return sections


def _truncate_to_token_budget(content: str) -> str:
    max_chars = MAX_SECTION_TOKENS * APPROX_CHARS_PER_TOKEN
    if len(content) <= max_chars:
        return content
    return content[:max_chars] + "\n\n[Content truncated due to length.]"


def _parse_json_response(response: str) -> dict:  # type: ignore[type-arg]
    text = response.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError(f"Expected JSON object, got {type(parsed).__name__}")
    return parsed


def _clamp_page(page: object, start_page: int, end_page: int) -> int:
    if not isinstance(page, int):
        return start_page
    return max(start_page, min(page, end_page))
