# ask-pipeline

Book Q&A use case and CLI command. Located in `python/source/interactive_books/app/ask.py` and `python/source/interactive_books/main.py`.

## Requirements

### AP-1: AskBookUseCase orchestrates question answering

`AskBookUseCase` in `app/ask.py` accepts `ChatProvider`, `SearchBooksUseCase`, and `prompts_dir: Path` via constructor injection. Exposes `execute(book_id: str, question: str, top_k: int = 5) → str` that:

1. Calls `SearchBooksUseCase.execute()` to get relevant chunks
2. Loads prompt templates from `prompts_dir`
3. Builds message list: system prompt (with citation instructions) + user query (with context)
4. Calls `ChatProvider.chat()` and returns the answer string

Edge cases: book not found and no embeddings propagate as `BookError`; no search results still calls the LLM with a "no relevant passages" message; LLM failures propagate as `LLMError`.

### AP-2: Prompt assembly uses shared templates

The use case loads templates from `prompts_dir` and assembles:
1. System message: `system_prompt.md` + `citation_instructions.md`
2. User message: `query_template.md` with `{context}` (passages labeled with `[Pages X-Y]`, joined by double newlines) and `{question}`

### AP-3: CLI ask command wires the Q&A pipeline

The CLI provides an `ask` command accepting a book ID and question string. Supports `--top-k` option (default 5). Validates both `OPENAI_API_KEY` (for embeddings/search) and `ANTHROPIC_API_KEY` (for chat). Prints the answer to stdout. Catches `BookError` and `LLMError` with error messages to stderr.
