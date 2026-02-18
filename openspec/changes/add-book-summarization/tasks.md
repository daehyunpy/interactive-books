## 1. Domain Layer — Value Objects

- [ ] 1.1 Create `SectionSummary` and `KeyStatement` frozen dataclasses in `domain/section_summary.py`
  - `KeyStatement(statement: str, page: int)` — page >= 1
  - `SectionSummary(id: str, book_id: str, title: str, start_page: int, end_page: int, summary: str, key_statements: list[KeyStatement], section_index: int, created_at: datetime)`
  - Validation: non-empty title, non-empty summary, start_page >= 1, end_page >= start_page
- [ ] 1.2 Add unit tests for `SectionSummary` and `KeyStatement` validation
- [ ] 1.3 Add `SummaryRepository` protocol to `domain/protocols.py`
  - `save_all(book_id: str, summaries: list[SectionSummary]) -> None`
  - `get_by_book(book_id: str) -> list[SectionSummary]`
  - `delete_by_book(book_id: str) -> None`

## 2. Infrastructure — Database Migration

- [ ] 2.1 Create `shared/schema/003_add_section_summaries.sql`
  - `section_summaries` table with FK to `books`, CASCADE delete
  - Index on `book_id`

## 3. Infrastructure — Summary Repository

- [ ] 3.1 Create `infra/storage/summary_repo.py` implementing `SummaryRepository`
  - Serialize `key_statements` as JSON on save, deserialize on load
- [ ] 3.2 Add integration tests for `SummaryRepository` (save, load, delete, cascade)

## 4. Shared Prompts — Summarization Template

- [ ] 4.1 Create `shared/prompts/summarization_prompt.md` with structured instructions for the LLM
  - Input: section content with page range
  - Output: title, 2-3 sentence summary, 1-3 key statements with page numbers
  - Instruct the LLM to return JSON for reliable parsing

## 5. Application Layer — SummarizeBookUseCase

- [ ] 5.1 Create `app/summarize.py` with `SummarizeBookUseCase`
  - Constructor: `chat_provider`, `book_repo`, `chunk_repo`, `summary_repo`, `prompts_dir`, `on_progress` callback
  - `execute(book_id: str, regenerate: bool = False) -> list[SectionSummary]`
  - If cached summaries exist and `regenerate` is False, return them
  - Otherwise: group chunks, summarize via LLM, persist, return
- [ ] 5.2 Implement section grouping: group chunks by contiguous page ranges (overlapping/adjacent pages form one section)
- [ ] 5.3 Implement per-section LLM summarization with the prompt template
  - Cap content at `MAX_SECTION_TOKENS = 6000` per section
  - Cap total sections at `MAX_SECTIONS = 30`
  - Parse LLM JSON response into `SectionSummary` objects
- [ ] 5.4 Add unit tests for section grouping logic (various page range patterns)
- [ ] 5.5 Add unit tests for the use case with mocked ChatProvider and SummaryRepository

## 6. CLI — `summarize` Command

- [ ] 6.1 Add `summarize <book_id>` command to `main.py`
  - Requires `ANTHROPIC_API_KEY`
  - Displays each section: title, page range, summary, key statements with pages
  - `--regenerate` flag to force re-generation
- [ ] 6.2 Add CLI test for the `summarize` command

## 7. CLI — Chat Integration

- [ ] 7.1 Modify `chat` command to display summary on new conversations (no existing messages)
- [ ] 7.2 Add `--no-summary` flag to `chat` command to skip automatic summary display

## 8. Verification

- [ ] 8.1 Run full test suite (`uv run pytest -x`) — all tests pass
- [ ] 8.2 Run lint and type checks (`uv run ruff check .` and `uv run pyright`) — clean
