from interactive_books.domain.prompt_message import PromptMessage
from interactive_books.domain.protocols import ChatProvider

JUDGE_PROMPT = (
    "You are evaluating whether a response matches expected behavior.\n\n"
    "## Actual response\n{actual}\n\n"
    "## Expected behavior\n{expected}\n\n"
    "Does the actual response match the expected behavior? "
    "Answer YES or NO, then explain briefly."
)


def judge_response(
    chat_provider: ChatProvider,
    actual: str,
    expected: str,
) -> bool:
    """Use an LLM to judge whether *actual* matches *expected* behavior.

    Returns ``True`` when the judge's first word is YES.
    """
    prompt = JUDGE_PROMPT.format(actual=actual, expected=expected)
    messages = [PromptMessage(role="user", content=prompt)]
    verdict = chat_provider.chat(messages)
    first_word = verdict.strip().split()[0].upper().rstrip(".,!:")
    return first_word == "YES"
