import os
from pathlib import Path
from typing import TYPE_CHECKING

import typer

if TYPE_CHECKING:
    from interactive_books.app.conversations import ManageConversationsUseCase
    from interactive_books.domain.conversation import Conversation

app = typer.Typer()

VERSION = "0.1.0"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_DIR = PROJECT_ROOT / "shared" / "schema"
PROMPTS_DIR = PROJECT_ROOT / "shared" / "prompts"
DB_PATH = PROJECT_ROOT / "data" / "books.db"
CONTENT_PREVIEW_LENGTH = 200

_verbose: bool = False


def _open_db(enable_vec: bool = False):  # type: ignore[no-untyped-def]
    from interactive_books.infra.storage.database import Database

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = Database(DB_PATH, enable_vec=enable_vec)
    db.run_migrations(SCHEMA_DIR)
    return db


def _require_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        typer.echo(f"Error: {name} environment variable is not set", err=True)
        raise typer.Exit(code=1)
    return value


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output"),
) -> None:
    global _verbose  # noqa: PLW0603
    _verbose = verbose
    if version:
        typer.echo(f"interactive-books {VERSION}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command()
def ingest(
    file_path: Path = typer.Argument(..., help="Path to the book file (PDF or TXT)"),
    title: str = typer.Option(
        "", "--title", "-t", help="Book title (defaults to filename)"
    ),
) -> None:
    """Parse, chunk, and ingest a book file."""
    from interactive_books.app.embed import EmbedBookUseCase
    from interactive_books.app.ingest import IngestBookUseCase
    from interactive_books.domain.errors import BookError
    from interactive_books.infra.chunkers.recursive import TextChunker
    from interactive_books.infra.parsers.pdf import BookParser as PdfBookParser
    from interactive_books.infra.parsers.txt import BookParser as TxtBookParser
    from interactive_books.infra.storage.book_repo import BookRepository
    from interactive_books.infra.storage.chunk_repo import ChunkRepository

    if not title:
        title = file_path.stem

    openai_key = os.environ.get("OPENAI_API_KEY", "")
    has_embed = bool(openai_key)
    db = _open_db(enable_vec=has_embed)
    book_repo = BookRepository(db)
    chunk_repo = ChunkRepository(db)

    embed_use_case: EmbedBookUseCase | None = None
    if has_embed:
        from interactive_books.infra.embeddings.openai import EmbeddingProvider
        from interactive_books.infra.storage.embedding_repo import EmbeddingRepository

        def _log_embed_progress(
            batch_num: int, total_batches: int, batch_size: int
        ) -> None:
            typer.echo(
                f"[verbose] Embedding batch {batch_num}/{total_batches} ({batch_size} chunks)"
            )

        embed_use_case = EmbedBookUseCase(
            embedding_provider=EmbeddingProvider(api_key=openai_key),
            book_repo=book_repo,
            chunk_repo=chunk_repo,
            embedding_repo=EmbeddingRepository(db),
            on_progress=_log_embed_progress if _verbose else None,
        )

    use_case = IngestBookUseCase(
        pdf_parser=PdfBookParser(),
        txt_parser=TxtBookParser(),
        chunker=TextChunker(),
        book_repo=book_repo,
        chunk_repo=chunk_repo,
        embed_use_case=embed_use_case,
    )

    try:
        book, embed_error = use_case.execute(file_path, title)
        chunk_count = chunk_repo.count_by_book(book.id)
        typer.echo(f"Book ID:     {book.id}")
        typer.echo(f"Title:       {book.title}")
        typer.echo(f"Status:      {book.status.value}")
        typer.echo(f"Chunks:      {chunk_count}")
        if _verbose:
            typer.echo(f"[verbose] Ingested {chunk_count} chunks")
        if embed_error is not None:
            typer.echo(
                f"Warning: Embedding failed: {embed_error}",
                err=True,
            )
            typer.echo("Tip: Run 'embed' command separately to retry.", err=True)
        elif has_embed:
            typer.echo(f"Embedded:    {book.embedding_provider}")
        else:
            typer.echo(
                "Tip: Set OPENAI_API_KEY to auto-embed, or run 'embed <book-id>' manually."
            )
    except BookError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)
    finally:
        db.close()


@app.command()
def search(
    book_id: str = typer.Argument(..., help="ID of the book to search"),
    query: str = typer.Argument(..., help="Search query text"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of results to return"),
    page: int | None = typer.Option(
        None, "--page", "-p", help="Temporary page limit (overrides set-page)"
    ),
    all_pages: bool = typer.Option(
        False, "--all-pages", help="Search all pages, ignoring set-page"
    ),
) -> None:
    """Search a book's chunks using vector similarity."""
    if page is not None and all_pages:
        typer.echo("Error: --page and --all-pages are mutually exclusive.", err=True)
        raise typer.Exit(code=1)

    page_override = 0 if all_pages else page

    import time

    from interactive_books.app.search import SearchBooksUseCase
    from interactive_books.domain.errors import BookError
    from interactive_books.infra.embeddings.openai import EmbeddingProvider
    from interactive_books.infra.storage.book_repo import BookRepository
    from interactive_books.infra.storage.chunk_repo import ChunkRepository
    from interactive_books.infra.storage.embedding_repo import EmbeddingRepository

    api_key = _require_env("OPENAI_API_KEY")
    db = _open_db(enable_vec=True)

    provider = EmbeddingProvider(api_key=api_key)
    use_case = SearchBooksUseCase(
        embedding_provider=provider,
        book_repo=BookRepository(db),
        chunk_repo=ChunkRepository(db),
        embedding_repo=EmbeddingRepository(db),
    )

    try:
        if _verbose:
            typer.echo(
                f"[verbose] Provider: {provider.provider_name}, Dimension: {provider.dimension}"
            )
        t0 = time.monotonic()
        results = use_case.execute(book_id, query, top_k=top_k, page_override=page_override)
        elapsed = time.monotonic() - t0
        if _verbose:
            typer.echo(
                f"[verbose] Search completed in {elapsed:.2f}s, {len(results)} results"
            )
        if not results:
            typer.echo("No results found.")
            raise typer.Exit()
        for i, result in enumerate(results, 1):
            typer.echo(
                f"[{i}] pages {result.start_page}-{result.end_page}  (distance: {result.distance:.4f})"
            )
            preview = result.content[:CONTENT_PREVIEW_LENGTH].replace("\n", " ")
            typer.echo(f"    {preview}")
            typer.echo()
    except BookError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)
    finally:
        db.close()


@app.command()
def chat(
    book_id: str = typer.Argument(..., help="ID of the book to chat about"),
) -> None:
    """Start a conversation about a book."""

    from interactive_books.app.chat import ChatWithBookUseCase
    from interactive_books.app.conversations import ManageConversationsUseCase
    from interactive_books.app.search import SearchBooksUseCase
    from interactive_books.domain.chat_event import (
        ChatEvent,
        TokenUsageEvent,
        ToolInvocationEvent,
        ToolResultEvent,
    )
    from interactive_books.domain.errors import BookError, LLMError
    from interactive_books.infra.context.full_history import ConversationContextStrategy
    from interactive_books.infra.embeddings.openai import EmbeddingProvider
    from interactive_books.infra.llm.anthropic import ChatProvider
    from interactive_books.infra.retrieval.tool_use import RetrievalStrategy
    from interactive_books.infra.storage.book_repo import BookRepository
    from interactive_books.infra.storage.chat_message_repo import ChatMessageRepository
    from interactive_books.infra.storage.chunk_repo import ChunkRepository
    from interactive_books.infra.storage.conversation_repo import ConversationRepository
    from interactive_books.infra.storage.embedding_repo import EmbeddingRepository

    openai_key = _require_env("OPENAI_API_KEY")
    anthropic_key = _require_env("ANTHROPIC_API_KEY")
    db = _open_db(enable_vec=True)

    try:
        book_repo = BookRepository(db)
        book = book_repo.get(book_id)
        if book is None:
            typer.echo(f"Error: Book not found: {book_id}", err=True)
            raise typer.Exit(code=1)

        conversation_repo = ConversationRepository(db)
        message_repo = ChatMessageRepository(db)
        manage = ManageConversationsUseCase(
            conversation_repo=conversation_repo,
            book_repo=book_repo,
        )

        conversation = _select_or_create_conversation(manage, book_id)
        typer.echo(f"Conversation: {conversation.title} ({conversation.id[:8]}...)")
        typer.echo("Type your message (or 'quit' to exit).\n")

        chat_provider = ChatProvider(api_key=anthropic_key)

        def _on_event(event: ChatEvent) -> None:
            if isinstance(event, ToolInvocationEvent):
                typer.echo(f"[verbose] Tool call: {event.tool_name}({event.arguments})")
            elif isinstance(event, ToolResultEvent):
                page_ranges = ", ".join(
                    f"pages {r.start_page}-{r.end_page}" for r in event.results
                )
                typer.echo(
                    f"[verbose]   → {event.result_count} results ({page_ranges})"
                )
            elif isinstance(event, TokenUsageEvent):
                typer.echo(
                    f"[verbose] Tokens: {event.input_tokens:,} in / {event.output_tokens:,} out"
                )

        chat_use_case = ChatWithBookUseCase(
            chat_provider=chat_provider,
            retrieval_strategy=RetrievalStrategy(),
            context_strategy=ConversationContextStrategy(),
            search_use_case=SearchBooksUseCase(
                embedding_provider=EmbeddingProvider(api_key=openai_key),
                book_repo=book_repo,
                chunk_repo=ChunkRepository(db),
                embedding_repo=EmbeddingRepository(db),
            ),
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            prompts_dir=PROMPTS_DIR,
            on_event=_on_event if _verbose else None,
        )

        if _verbose:
            typer.echo(f"[verbose] Chat model: {chat_provider.model_name}")

        while True:
            try:
                user_input = typer.prompt("You")
            except (KeyboardInterrupt, EOFError):
                typer.echo("\nGoodbye!")
                break

            if user_input.strip().lower() in ("quit", "exit"):
                typer.echo("Goodbye!")
                break

            if not user_input.strip():
                continue

            try:
                answer = chat_use_case.execute(conversation.id, user_input)
                typer.echo(f"\nAssistant: {answer}\n")
            except (BookError, LLMError) as e:
                typer.echo(f"Error: {e.message}", err=True)
    finally:
        db.close()


MAX_SELECTION_RETRIES = 3


def _select_or_create_conversation(
    manage: "ManageConversationsUseCase",  # noqa: F821
    book_id: str,
) -> "Conversation":  # noqa: F821
    """Let the user pick an existing conversation or create a new one."""

    existing = manage.list_by_book(book_id)
    if existing:
        typer.echo("Existing conversations:")
        for i, conv in enumerate(existing, 1):
            typer.echo(f"  [{i}] {conv.title} ({conv.id[:8]}...)")
        typer.echo("  [N] New conversation")

        for attempt in range(MAX_SELECTION_RETRIES):
            choice = typer.prompt("Select", default="N")
            if choice.upper() == "N":
                break
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(existing):
                    return existing[idx]
            except ValueError:
                pass
            remaining = MAX_SELECTION_RETRIES - attempt - 1
            if remaining > 0:
                typer.echo(
                    f"Invalid choice. Please enter 1-{len(existing)} or N. "
                    f"({remaining} {'attempt' if remaining == 1 else 'attempts'} left)"
                )
            else:
                typer.echo("Invalid choice, creating new conversation.")

    return manage.create(book_id)


@app.command()
def embed(
    book_id: str = typer.Argument(..., help="ID of the book to embed"),
) -> None:
    """Generate embeddings for a book's chunks."""
    from interactive_books.app.embed import EmbedBookUseCase
    from interactive_books.domain.errors import BookError
    from interactive_books.infra.embeddings.openai import EmbeddingProvider
    from interactive_books.infra.storage.book_repo import BookRepository
    from interactive_books.infra.storage.chunk_repo import ChunkRepository
    from interactive_books.infra.storage.embedding_repo import EmbeddingRepository

    api_key = _require_env("OPENAI_API_KEY")
    db = _open_db(enable_vec=True)

    def _log_retry(attempt: int, delay: float) -> None:
        typer.echo(
            f"[verbose] Rate limited, retrying in {delay:.1f}s (attempt {attempt})"
        )

    provider = EmbeddingProvider(
        api_key=api_key,
        on_retry=_log_retry if _verbose else None,
    )
    chunk_repo = ChunkRepository(db)

    def _log_progress(batch_num: int, total_batches: int, batch_size: int) -> None:
        typer.echo(
            f"[verbose] Embedding batch {batch_num}/{total_batches} ({batch_size} chunks)"
        )

    use_case = EmbedBookUseCase(
        embedding_provider=provider,
        book_repo=BookRepository(db),
        chunk_repo=chunk_repo,
        embedding_repo=EmbeddingRepository(db),
        on_progress=_log_progress if _verbose else None,
    )

    try:
        chunk_count = chunk_repo.count_by_book(book_id)
        if _verbose:
            typer.echo(f"[verbose] Embedding {chunk_count} chunks")
            typer.echo(
                f"[verbose] Provider: {provider.provider_name}, Dimension: {provider.dimension}"
            )
        book = use_case.execute(book_id)
        typer.echo(f"Book ID:     {book.id}")
        typer.echo(f"Title:       {book.title}")
        typer.echo(f"Chunks:      {chunk_count}")
        typer.echo(f"Provider:    {book.embedding_provider}")
        typer.echo(f"Dimension:   {book.embedding_dimension}")
    except BookError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)
    finally:
        db.close()


@app.command()
def books() -> None:
    """List all books."""
    from interactive_books.app.list_books import ListBooksUseCase
    from interactive_books.infra.storage.book_repo import BookRepository
    from interactive_books.infra.storage.chunk_repo import ChunkRepository

    db = _open_db()
    use_case = ListBooksUseCase(
        book_repo=BookRepository(db),
        chunk_repo=ChunkRepository(db),
    )

    try:
        summaries = use_case.execute()
        if not summaries:
            typer.echo("No books found.")
            return
        header = f"{'ID':<38} {'Title':<30} {'Status':<10} {'Chunks':>6} {'Provider':<12} {'Page':>4}"
        typer.echo(header)
        typer.echo("-" * len(header))
        for s in summaries:
            provider = s.embedding_provider or "-"
            typer.echo(
                f"{s.id:<38} {s.title:<30} {s.status.value:<10} {s.chunk_count:>6} {provider:<12} {s.current_page:>4}"
            )
    finally:
        db.close()


@app.command()
def show(
    book_id: str = typer.Argument(..., help="ID of the book to show"),
) -> None:
    """Show detailed information about a book."""
    from interactive_books.domain.errors import BookError, BookErrorCode
    from interactive_books.infra.storage.book_repo import BookRepository
    from interactive_books.infra.storage.chunk_repo import ChunkRepository

    db = _open_db()

    try:
        book_repo = BookRepository(db)
        chunk_repo = ChunkRepository(db)
        book = book_repo.get(book_id)
        if book is None:
            raise BookError(BookErrorCode.NOT_FOUND, f"Book not found: {book_id}")
        chunk_count = chunk_repo.count_by_book(book_id)
        typer.echo(f"ID:          {book.id}")
        typer.echo(f"Title:       {book.title}")
        typer.echo(f"Status:      {book.status.value}")
        typer.echo(f"Chunks:      {chunk_count}")
        typer.echo(f"Provider:    {book.embedding_provider or '-'}")
        typer.echo(f"Dimension:   {book.embedding_dimension or '-'}")
        typer.echo(f"Page:        {book.current_page}")
        typer.echo(f"Created:     {book.created_at.isoformat()}")
        typer.echo(f"Updated:     {book.updated_at.isoformat()}")
    except BookError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)
    finally:
        db.close()


@app.command()
def delete(
    book_id: str = typer.Argument(..., help="ID of the book to delete"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """Delete a book and all associated data."""
    from interactive_books.app.delete_book import DeleteBookUseCase
    from interactive_books.domain.errors import BookError
    from interactive_books.infra.storage.book_repo import BookRepository
    from interactive_books.infra.storage.embedding_repo import EmbeddingRepository

    db = _open_db(enable_vec=True)

    try:
        book_repo = BookRepository(db)
        book = book_repo.get(book_id)
        if book is None:
            typer.echo(f"Error: Book not found: {book_id}", err=True)
            raise typer.Exit(code=1)

        if not yes:
            typer.confirm(f"Delete '{book.title}' and all associated data?", abort=True)

        use_case = DeleteBookUseCase(
            book_repo=book_repo,
            embedding_repo=EmbeddingRepository(db),
        )
        deleted = use_case.execute(book_id)
        typer.echo(f"Deleted: {deleted.title} ({deleted.id})")
    except BookError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)
    finally:
        db.close()


@app.command(name="set-page")
def set_page(
    book_id: str = typer.Argument(..., help="ID of the book"),
    page: int = typer.Argument(..., help="Page number (0 to reset)"),
) -> None:
    """Set the current reading position for a book."""
    from interactive_books.domain.errors import BookError, BookErrorCode
    from interactive_books.infra.storage.book_repo import BookRepository

    db = _open_db()

    try:
        book_repo = BookRepository(db)
        book = book_repo.get(book_id)
        if book is None:
            raise BookError(BookErrorCode.NOT_FOUND, f"Book not found: {book_id}")
        book.set_current_page(page)
        book_repo.save(book)
        if page == 0:
            typer.echo(f"Reset reading position for '{book.title}'.")
        else:
            typer.echo(f"Set reading position to page {page} for '{book.title}'.")
    except BookError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)
    finally:
        db.close()
