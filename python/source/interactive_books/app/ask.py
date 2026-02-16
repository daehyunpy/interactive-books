from pathlib import Path

from interactive_books.app.search import SearchBooksUseCase
from interactive_books.domain.prompt_message import PromptMessage
from interactive_books.domain.protocols import ChatProvider
from interactive_books.domain.search_result import SearchResult

NO_CONTEXT_MESSAGE = "No relevant passages found in the book for this question."


class AskBookUseCase:
    def __init__(
        self,
        *,
        chat_provider: ChatProvider,
        search_use_case: SearchBooksUseCase,
        prompts_dir: Path,
    ) -> None:
        self._chat = chat_provider
        self._search = search_use_case
        self._prompts_dir = prompts_dir

    def execute(self, book_id: str, question: str, top_k: int = 5) -> str:
        results = self._search.execute(book_id, question, top_k=top_k)

        system_prompt = self._load_template("system_prompt.md")
        citation_instructions = self._load_template("citation_instructions.md")
        query_template = self._load_template("query_template.md")

        system_text = f"{system_prompt}\n\n{citation_instructions}"
        context = self._format_context(results)
        user_text = query_template.format(context=context, question=question)

        messages = [
            PromptMessage(role="system", content=system_text),
            PromptMessage(role="user", content=user_text),
        ]

        return self._chat.chat(messages)

    def _load_template(self, filename: str) -> str:
        return (self._prompts_dir / filename).read_text().strip()

    def _format_context(self, results: list[SearchResult]) -> str:
        if not results:
            return NO_CONTEXT_MESSAGE

        passages = [
            f"[Pages {r.start_page}-{r.end_page}]:\n{r.content}" for r in results
        ]
        return "\n\n".join(passages)
