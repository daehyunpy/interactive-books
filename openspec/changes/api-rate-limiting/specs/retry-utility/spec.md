## ADDED Requirements

### Requirement: Shared retry utility with exponential backoff

The infrastructure layer SHALL provide a `retry_with_backoff` function in `infra/retry.py` that retries a callable on specified transient errors using exponential backoff with jitter. The function SHALL accept `fn` (zero-argument callable), `retryable_errors` (tuple of exception types), `max_retries` (default 6), `base_delay` (default 1.0), `max_delay` (default 60.0), and `on_retry` (optional callback, default None).

#### Scenario: Succeeds on first attempt
- **WHEN** `retry_with_backoff(fn, retryable_errors=(SomeError,))` is called and `fn` succeeds
- **THEN** the result of `fn` is returned without any retry

#### Scenario: Retries on retryable error and succeeds
- **WHEN** `fn` raises a retryable error on the first attempt but succeeds on the second
- **THEN** the result of the second attempt is returned

#### Scenario: Retries exhausted
- **WHEN** `fn` raises a retryable error on every attempt up to `max_retries`
- **THEN** the last retryable error is re-raised

#### Scenario: Non-retryable error raises immediately
- **WHEN** `fn` raises an error not in `retryable_errors`
- **THEN** the error is raised immediately without retrying

#### Scenario: Delay uses exponential backoff with jitter
- **WHEN** a retry occurs
- **THEN** the delay is computed as `min(base_delay * (2 ^ attempt) * (1 + random(0, 0.5)), max_delay)`

#### Scenario: Delay is capped at max_delay
- **WHEN** the computed delay exceeds `max_delay`
- **THEN** the actual delay used is `max_delay`

#### Scenario: on_retry callback is invoked before sleeping
- **WHEN** a retry occurs and `on_retry` is provided
- **THEN** `on_retry(attempt, delay)` is called before sleeping

#### Scenario: max_retries=0 disables retry
- **WHEN** `retry_with_backoff(fn, retryable_errors=(SomeError,), max_retries=0)` is called and `fn` raises a retryable error
- **THEN** the error is raised immediately without retrying
