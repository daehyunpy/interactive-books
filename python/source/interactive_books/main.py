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
    from interactive_books.infra.chunkers.recursive import RecursiveChunker
    from interactive_books.infra.parsers.pdf import PyMuPdfParser
    from interactive_books.infra.parsers.txt import PlainTextParser
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
        pdf_parser=PyMuPdfParser(),
        txt_parser=PlainTextParser(),
        chunker=RecursiveChunker(),
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
