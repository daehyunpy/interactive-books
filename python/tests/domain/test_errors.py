from interactive_books.domain.errors import (
    BookError,
    BookErrorCode,
    DomainError,
    LLMError,
    LLMErrorCode,
    StorageError,
    StorageErrorCode,
)


class TestDomainErrorBase:
    def test_domain_error_is_exception(self) -> None:
        assert issubclass(DomainError, Exception)

    def test_book_error_is_domain_error(self) -> None:
        assert issubclass(BookError, DomainError)

    def test_llm_error_is_domain_error(self) -> None:
        assert issubclass(LLMError, DomainError)

    def test_storage_error_is_domain_error(self) -> None:
        assert issubclass(StorageError, DomainError)


class TestBookError:
    def test_all_codes_exist(self) -> None:
        expected = {
            "not_found",
            "parse_failed",
            "unsupported_format",
            "already_exists",
            "invalid_state",
            "embedding_failed",
        }
        actual = {code.value for code in BookErrorCode}
        assert actual == expected

    def test_error_has_code_and_message(self) -> None:
        error = BookError(BookErrorCode.NOT_FOUND, "Book xyz not found")
        assert error.code == BookErrorCode.NOT_FOUND
        assert error.message == "Book xyz not found"

    def test_str_returns_message(self) -> None:
        error = BookError(BookErrorCode.INVALID_STATE, "Cannot transition")
        assert str(error) == "Cannot transition"

    def test_error_is_raisable(self) -> None:
        try:
            raise BookError(BookErrorCode.PARSE_FAILED, "Bad PDF")
        except BookError as e:
            assert e.code == BookErrorCode.PARSE_FAILED


class TestLLMError:
    def test_all_codes_exist(self) -> None:
        expected = {"api_key_missing", "api_call_failed", "rate_limited", "timeout"}
        actual = {code.value for code in LLMErrorCode}
        assert actual == expected

    def test_error_has_code_and_message(self) -> None:
        error = LLMError(LLMErrorCode.API_KEY_MISSING, "No API key")
        assert error.code == LLMErrorCode.API_KEY_MISSING
        assert error.message == "No API key"

    def test_str_returns_message(self) -> None:
        error = LLMError(LLMErrorCode.TIMEOUT, "Request timed out")
        assert str(error) == "Request timed out"


class TestStorageError:
    def test_all_codes_exist(self) -> None:
        expected = {"db_corrupted", "migration_failed", "write_failed", "not_found"}
        actual = {code.value for code in StorageErrorCode}
        assert actual == expected

    def test_error_has_code_and_message(self) -> None:
        error = StorageError(StorageErrorCode.MIGRATION_FAILED, "Bad migration")
        assert error.code == StorageErrorCode.MIGRATION_FAILED
        assert error.message == "Bad migration"

    def test_str_returns_message(self) -> None:
        error = StorageError(StorageErrorCode.DB_CORRUPTED, "Database corrupt")
        assert str(error) == "Database corrupt"
