# prompt-templates

Delta spec for shared prompt templates. Adds `conversation_system_prompt.md` and `reformulation_prompt.md` for agentic conversation support.

## ADDED Requirements

### PT-4: Conversation system prompt template defines agent behavior

`shared/prompts/conversation_system_prompt.md` SHALL establish the agent's role for agentic conversation. The prompt SHALL instruct the LLM to:

1. Act as a knowledgeable reading companion for a specific book
2. Use the `search_book` tool when it needs to find specific passages, facts, or quotes from the book
3. Respond directly from conversation context when the answer is already available (no unnecessary retrieval)
4. Cite page numbers using the format "(p.42)" or "(pp.42-43)" when referencing retrieved passages
5. Respect the reader's current position -- never reveal or discuss content beyond the current page
6. Reformulate vague or context-dependent queries into self-contained search queries before invoking `search_book`
7. Acknowledge when it cannot find relevant information rather than fabricating answers

The prompt SHALL use `{book_title}` and `{current_page}` placeholders for runtime formatting.

#### Scenario: Prompt file exists

- **WHEN** the `shared/prompts/` directory is listed
- **THEN** `conversation_system_prompt.md` is present

#### Scenario: Prompt contains tool-use instructions

- **WHEN** `conversation_system_prompt.md` is read
- **THEN** it contains instructions about when and how to use the `search_book` tool

#### Scenario: Prompt contains citation format

- **WHEN** `conversation_system_prompt.md` is read
- **THEN** it specifies the page citation format "(p.42)" for single pages and "(pp.42-43)" for ranges

#### Scenario: Prompt contains spoiler prevention

- **WHEN** `conversation_system_prompt.md` is read
- **THEN** it instructs the LLM not to reveal content beyond the reader's current page

#### Scenario: Prompt contains placeholders

- **WHEN** `conversation_system_prompt.md` is read
- **THEN** it contains `{book_title}` and `{current_page}` placeholders

### PT-5: Reformulation prompt template for query rewriting

`shared/prompts/reformulation_prompt.md` SHALL provide instructions for producing a self-contained search query from conversation context. This prompt is used when the agent decides to search but the user's message contains anaphora, pronouns, or implicit references that would not work as a standalone search query.

The prompt SHALL instruct the LLM to:

1. Analyze the conversation context to understand what the user is referring to
2. Produce a single, self-contained search query that captures the user's intent without relying on conversation context
3. Resolve pronouns and references (e.g., "Tell me more about him" becomes "Tell me more about [character name]")
4. Keep the reformulated query concise and focused on retrievable content

#### Scenario: Prompt file exists

- **WHEN** the `shared/prompts/` directory is listed
- **THEN** `reformulation_prompt.md` is present

#### Scenario: Prompt contains anaphora resolution instructions

- **WHEN** `reformulation_prompt.md` is read
- **THEN** it contains instructions about resolving pronouns and references using conversation context

#### Scenario: Prompt contains self-contained query requirement

- **WHEN** `reformulation_prompt.md` is read
- **THEN** it instructs producing a query that works independently of conversation history
