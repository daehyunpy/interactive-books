from interactive_books.domain.book import Book
from interactive_books.domain.section_summary import KeyStatement, SectionSummary
from interactive_books.infra.storage.book_repo import BookRepository
from interactive_books.infra.storage.database import Database
from interactive_books.infra.storage.summary_repo import SummaryRepository


def _make_book(db: Database, book_id: str = "b1") -> None:
    repo = BookRepository(db)
    repo.save(Book(id=book_id, title="Test Book"))


class TestSummaryRepositorySaveAndLoad:
    def test_save_and_get_by_book(self, db: Database) -> None:
        _make_book(db)
        repo = SummaryRepository(db)
        summaries = [
            SectionSummary(
                id="s1",
                book_id="b1",
                title="Chapter 1",
                start_page=1,
                end_page=5,
                summary="Introduces the setting.",
                key_statements=[
                    KeyStatement(statement="The town was quiet.", page=2),
                ],
                section_index=0,
            ),
            SectionSummary(
                id="s2",
                book_id="b1",
                title="Chapter 2",
                start_page=6,
                end_page=10,
                summary="The conflict begins.",
                key_statements=[
                    KeyStatement(statement="War broke out.", page=7),
                    KeyStatement(statement="The hero fled.", page=9),
                ],
                section_index=1,
            ),
        ]
        repo.save_all("b1", summaries)

        loaded = repo.get_by_book("b1")
        assert len(loaded) == 2
        assert loaded[0].id == "s1"
        assert loaded[0].title == "Chapter 1"
        assert loaded[0].start_page == 1
        assert loaded[0].end_page == 5
        assert loaded[0].summary == "Introduces the setting."
        assert len(loaded[0].key_statements) == 1
        assert loaded[0].key_statements[0].statement == "The town was quiet."
        assert loaded[0].key_statements[0].page == 2

        assert loaded[1].id == "s2"
        assert len(loaded[1].key_statements) == 2

    def test_get_by_book_returns_empty_when_none(self, db: Database) -> None:
        _make_book(db)
        repo = SummaryRepository(db)
        assert repo.get_by_book("b1") == []

    def test_get_by_book_ordered_by_section_index(self, db: Database) -> None:
        _make_book(db)
        repo = SummaryRepository(db)
        summaries = [
            SectionSummary(
                id="s2",
                book_id="b1",
                title="Second",
                start_page=5,
                end_page=10,
                summary="Second section.",
                key_statements=[],
                section_index=1,
            ),
            SectionSummary(
                id="s1",
                book_id="b1",
                title="First",
                start_page=1,
                end_page=4,
                summary="First section.",
                key_statements=[],
                section_index=0,
            ),
        ]
        repo.save_all("b1", summaries)

        loaded = repo.get_by_book("b1")
        assert loaded[0].section_index == 0
        assert loaded[1].section_index == 1

    def test_save_all_replaces_existing(self, db: Database) -> None:
        _make_book(db)
        repo = SummaryRepository(db)
        repo.save_all(
            "b1",
            [
                SectionSummary(
                    id="s1",
                    book_id="b1",
                    title="Old",
                    start_page=1,
                    end_page=1,
                    summary="Old summary.",
                    key_statements=[],
                    section_index=0,
                ),
            ],
        )

        repo.save_all(
            "b1",
            [
                SectionSummary(
                    id="s2",
                    book_id="b1",
                    title="New",
                    start_page=1,
                    end_page=5,
                    summary="New summary.",
                    key_statements=[],
                    section_index=0,
                ),
            ],
        )

        loaded = repo.get_by_book("b1")
        assert len(loaded) == 1
        assert loaded[0].id == "s2"
        assert loaded[0].title == "New"

    def test_empty_key_statements_round_trips(self, db: Database) -> None:
        _make_book(db)
        repo = SummaryRepository(db)
        repo.save_all(
            "b1",
            [
                SectionSummary(
                    id="s1",
                    book_id="b1",
                    title="No Keys",
                    start_page=1,
                    end_page=1,
                    summary="A section with no key statements.",
                    key_statements=[],
                    section_index=0,
                ),
            ],
        )
        loaded = repo.get_by_book("b1")
        assert loaded[0].key_statements == []


class TestSummaryRepositoryDelete:
    def test_delete_by_book(self, db: Database) -> None:
        _make_book(db)
        repo = SummaryRepository(db)
        repo.save_all(
            "b1",
            [
                SectionSummary(
                    id="s1",
                    book_id="b1",
                    title="Chapter 1",
                    start_page=1,
                    end_page=5,
                    summary="Summary.",
                    key_statements=[],
                    section_index=0,
                ),
            ],
        )
        repo.delete_by_book("b1")
        assert repo.get_by_book("b1") == []

    def test_delete_by_book_does_not_affect_other_books(self, db: Database) -> None:
        _make_book(db, "b1")
        _make_book(db, "b2")
        repo = SummaryRepository(db)
        repo.save_all(
            "b1",
            [
                SectionSummary(
                    id="s1",
                    book_id="b1",
                    title="Book 1",
                    start_page=1,
                    end_page=1,
                    summary="Summary.",
                    key_statements=[],
                    section_index=0,
                ),
            ],
        )
        repo.save_all(
            "b2",
            [
                SectionSummary(
                    id="s2",
                    book_id="b2",
                    title="Book 2",
                    start_page=1,
                    end_page=1,
                    summary="Summary.",
                    key_statements=[],
                    section_index=0,
                ),
            ],
        )

        repo.delete_by_book("b1")
        assert repo.get_by_book("b1") == []
        assert len(repo.get_by_book("b2")) == 1


class TestSummaryRepositoryCascade:
    def test_deleting_book_cascades_to_summaries(self, db: Database) -> None:
        _make_book(db)
        summary_repo = SummaryRepository(db)
        summary_repo.save_all(
            "b1",
            [
                SectionSummary(
                    id="s1",
                    book_id="b1",
                    title="Chapter 1",
                    start_page=1,
                    end_page=5,
                    summary="Summary.",
                    key_statements=[
                        KeyStatement(statement="Important.", page=3),
                    ],
                    section_index=0,
                ),
            ],
        )

        book_repo = BookRepository(db)
        book_repo.delete("b1")

        assert summary_repo.get_by_book("b1") == []
