# Shared pytest fixtures
from collections.abc import Generator
from pathlib import Path

import pytest

from interactive_books.infra.storage.database import Database

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "shared" / "schema"


@pytest.fixture
def db() -> Generator[Database]:
    database = Database(":memory:")
    database.run_migrations(SCHEMA_DIR)
    yield database
    database.close()
