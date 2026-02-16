## MODIFIED Requirements

### DE-1: BookError

`BookError` exception class with enumerated cases: `not_found`, `parse_failed`, `unsupported_format`, `already_exists`, `invalid_state` (for invalid status transitions), `embedding_failed` (for embedding generation or storage failures). Each case has a descriptive message. Uses an inner enum `BookErrorCode` for case identification.
