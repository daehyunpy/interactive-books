from enum import Enum


class DomainError(Exception):
    def __init__(self, code: Enum, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class BookErrorCode(Enum):
    NOT_FOUND = "not_found"
    PARSE_FAILED = "parse_failed"
    UNSUPPORTED_FORMAT = "unsupported_format"
    ALREADY_EXISTS = "already_exists"
    INVALID_STATE = "invalid_state"
    EMBEDDING_FAILED = "embedding_failed"


class BookError(DomainError):
    def __init__(self, code: BookErrorCode, message: str) -> None:
        super().__init__(code, message)


class LLMErrorCode(Enum):
    API_KEY_MISSING = "api_key_missing"
    API_CALL_FAILED = "api_call_failed"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    UNSUPPORTED_FEATURE = "unsupported_feature"


class LLMError(DomainError):
    def __init__(self, code: LLMErrorCode, message: str) -> None:
        super().__init__(code, message)


class StorageErrorCode(Enum):
    DB_CORRUPTED = "db_corrupted"
    MIGRATION_FAILED = "migration_failed"
    WRITE_FAILED = "write_failed"
    NOT_FOUND = "not_found"


class StorageError(DomainError):
    def __init__(self, code: StorageErrorCode, message: str) -> None:
        super().__init__(code, message)
