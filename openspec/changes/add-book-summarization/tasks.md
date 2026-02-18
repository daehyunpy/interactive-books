## 1. Domain Layer — Value Objects

- [ ] 1.1 Create `SectionSummary` and `KeyStatement` frozen dataclasses in `domain/section_summary.py`
  - `KeyStatement(statement: str, page: int)` — page >= 1
  - `SectionSummary(title: str, start_page: int, end_page: int, summary: str, key_statements: list[KeyStatement])`
  - Validation: non-empty title, non-empty summary, start_page >= 1, end_page >= start_page
- [ ] 1.2 Add unit tests for `SectionSummary` and `KeyStatement` validation

## 2. Shared Prompts — Summarization Template

- [ ] 2.1 Create `shared/prompts/summarization_prompt.md` with structured instructions for the LLM
  - Input: section content with page range
  - Output: title, 2-3 sentence summary, 1-3 key statements with page numbers
  - Instruct the LLM to return JSON for reliable parsing

## 3. Application Layer — SummarizeBookUseCase

- [ ] 3.1 Create `app/summarize.py` with `SummarizeBookUseCase`
  - Constructor: `chat_provider`, `book_repo`, `chunk_repo`, `prompts_dir`, `on_progress` callback
  - `execute(book_id: str) -> list[SectionSummary]`
- [ ] 3.2 Implement section grouping: group chunks by contiguous page ranges (overlapping/adjacent pages form one section)
- [ ] 3.3 Implement per-section LLM summarization with the prompt template
  - Cap content at `MAX_SECTION_TOKENS = 6000` per section
  - Cap total sections at `MAX_SECTIONS = 30`
  - Parse LLM JSON response into `SectionSummary` objects
- [ ] 3.4 Add unit tests for section grouping logic (various page range patterns)
- [ ] 3.5 Add unit tests for the use case with mocked ChatProvider

## 4. CLI — `summarize` Command

- [ ] 4.1 Add `summarize <book_id>` command to `main.py`
  - Requires `ANTHROPIC_API_KEY`
  - Displays each section: title, page range, summary, key statements with pages
- [ ] 4.2 Add CLI test for the `summarize` command

## 5. CLI — Chat Integration

- [ ] 5.1 Modify `chat` command to run summarization on new conversations (no existing messages)
- [ ] 5.2 Add `--no-summary` flag to `chat` command to skip automatic summarization
- [ ] 5.3 Display summary output before the chat REPL prompt

## 6. Verification

- [ ] 6.1 Run full test suite (`uv run pytest -x`) — all tests pass
- [ ] 6.2 Run lint and type checks (`uv run ruff check .` and `uv run pyright`) — clean
