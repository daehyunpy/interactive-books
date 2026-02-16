## ADDED Requirements

### Requirement: System prompt template defines assistant behavior

A shared prompt template SHALL exist at `shared/prompts/system_prompt.md` that establishes the assistant's role: a knowledgeable reading companion that answers questions about a specific book using only the provided context passages, cites page numbers, and respects the reader's current position (no spoilers).

#### Scenario: System prompt file exists
- **WHEN** the application loads prompt templates
- **THEN** `shared/prompts/system_prompt.md` is readable and contains the system prompt text

#### Scenario: System prompt constrains to provided context
- **WHEN** the system prompt is used
- **THEN** it instructs the LLM to answer only from the provided passages, not from general knowledge

### Requirement: Query template assembles context with user question

A shared prompt template SHALL exist at `shared/prompts/query_template.md` that defines how retrieved chunks and the user's question are assembled into the user message. It SHALL use `{context}` and `{question}` placeholders.

#### Scenario: Template uses placeholders
- **WHEN** the query template is loaded
- **THEN** it contains `{context}` and `{question}` placeholders for string formatting

#### Scenario: Context includes page references
- **WHEN** context is assembled from SearchResult objects
- **THEN** each passage is labeled with its page range (e.g., "[Pages 42-43]")

### Requirement: Citation instructions guide page references in answers

A shared prompt template SHALL exist at `shared/prompts/citation_instructions.md` that instructs the LLM to cite specific page numbers when referencing information from the provided passages. Format: "(p.42)" or "(pp.42-43)".

#### Scenario: Citation instructions file exists
- **WHEN** the application loads prompt templates
- **THEN** `shared/prompts/citation_instructions.md` is readable and contains citation formatting rules

#### Scenario: Citation format specified
- **WHEN** the LLM follows citation instructions
- **THEN** page references use the format "(p.N)" for single pages or "(pp.N-M)" for ranges
