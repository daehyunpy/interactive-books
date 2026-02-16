from pathlib import Path

import typer

app = typer.Typer()

VERSION = "0.1.0"
SCHEMA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "shared" / "schema"
DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "books.db"


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
) -> None:
    if version:
        typer.echo(f"interactive-books {VERSION}")
        raise typer.Exit()


@app.command()
def ingest(
    file_path: Path = typer.Argument(..., help="Path to the book file (PDF or TXT)"),
    title: str = typer.Option(
        "", "--title", "-t", help="Book title (defaults to filename)"
    ),
) -> None:
    """Parse, chunk, and ingest a book file."""
    from interactive_books.app.ingest import IngestBookUseCase
    from interactive_books.domain.errors import BookError
    from interactive_books.infra.chunkers.recursive import TextChunker
    from interactive_books.infra.parsers.pdf import BookParser as PdfBookParser
    from interactive_books.infra.parsers.txt import BookParser as TxtBookParser
    from interactive_books.infra.storage.book_repo import BookRepository
    from interactive_books.infra.storage.chunk_repo import ChunkRepository
    from interactive_books.infra.storage.database import Database

    if not title:
        title = file_path.stem

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = Database(DB_PATH)
    db.run_migrations(SCHEMA_DIR)

    chunk_repo = ChunkRepository(db)
    use_case = IngestBookUseCase(
        pdf_parser=PdfBookParser(),
        txt_parser=TxtBookParser(),
        chunker=TextChunker(),
        book_repo=BookRepository(db),
        chunk_repo=chunk_repo,
    )

    try:
        book = use_case.execute(file_path, title)
        chunk_count = len(chunk_repo.get_by_book(book.id))
        typer.echo(f"Book ID:     {book.id}")
        typer.echo(f"Title:       {book.title}")
        typer.echo(f"Status:      {book.status.value}")
        typer.echo(f"Chunks:      {chunk_count}")
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
) -> None:
    """Search a book's chunks using vector similarity."""
    import os

    from interactive_books.app.search import SearchBooksUseCase
    from interactive_books.domain.errors import BookError
    from interactive_books.infra.embeddings.openai import EmbeddingProvider
    from interactive_books.infra.storage.book_repo import BookRepository
    from interactive_books.infra.storage.chunk_repo import ChunkRepository
    from interactive_books.infra.storage.database import Database
    from interactive_books.infra.storage.embedding_repo import EmbeddingRepository

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        typer.echo("Error: OPENAI_API_KEY environment variable is not set", err=True)
        raise typer.Exit(code=1)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = Database(DB_PATH, enable_vec=True)
    db.run_migrations(SCHEMA_DIR)

    use_case = SearchBooksUseCase(
        embedding_provider=EmbeddingProvider(api_key=api_key),
        book_repo=BookRepository(db),
        chunk_repo=ChunkRepository(db),
        embedding_repo=EmbeddingRepository(db),
    )

    try:
        results = use_case.execute(book_id, query, top_k=top_k)
        if not results:
            typer.echo("No results found.")
            raise typer.Exit()
        for i, r in enumerate(results, 1):
            typer.echo(
                f"[{i}] pages {r.start_page}-{r.end_page}  (distance: {r.distance:.4f})"
            )
            preview = r.content[:200].replace("\n", " ")
            typer.echo(f"    {preview}")
            typer.echo()
    except BookError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)
    finally:
        db.close()


@app.command()
def embed(
    book_id: str = typer.Argument(..., help="ID of the book to embed"),
) -> None:
    """Generate embeddings for a book's chunks."""
    import os

    from interactive_books.app.embed import EmbedBookUseCase
    from interactive_books.domain.errors import BookError
    from interactive_books.infra.embeddings.openai import EmbeddingProvider
    from interactive_books.infra.storage.book_repo import BookRepository
    from interactive_books.infra.storage.chunk_repo import ChunkRepository
    from interactive_books.infra.storage.database import Database
    from interactive_books.infra.storage.embedding_repo import EmbeddingRepository

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        typer.echo("Error: OPENAI_API_KEY environment variable is not set", err=True)
        raise typer.Exit(code=1)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = Database(DB_PATH, enable_vec=True)
    db.run_migrations(SCHEMA_DIR)

    provider = EmbeddingProvider(api_key=api_key)
    use_case = EmbedBookUseCase(
        embedding_provider=provider,
        book_repo=BookRepository(db),
        chunk_repo=ChunkRepository(db),
        embedding_repo=EmbeddingRepository(db),
    )

    try:
        book = use_case.execute(book_id)
        typer.echo(f"Book ID:     {book.id}")
        typer.echo(f"Title:       {book.title}")
        typer.echo(f"Provider:    {book.embedding_provider}")
        typer.echo(f"Dimension:   {book.embedding_dimension}")
    except BookError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)
    finally:
        db.close()
