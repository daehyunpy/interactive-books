# prompt-templates

Shared prompt templates for cross-platform consistency. Located in `shared/prompts/`.

## Requirements

### PT-1: System prompt template defines assistant behavior

`shared/prompts/system_prompt.md` establishes the assistant's role: a knowledgeable reading companion that answers questions about a specific book using only the provided context passages, cites page numbers, and respects the reader's current position (no spoilers).

### PT-2: Query template assembles context with user question

`shared/prompts/query_template.md` defines how retrieved chunks and the user's question are assembled into the user message. Uses `{context}` and `{question}` placeholders for string formatting.

### PT-3: Citation instructions guide page references in answers

`shared/prompts/citation_instructions.md` instructs the LLM to cite specific page numbers when referencing information from the provided passages. Format: "(p.42)" for single pages or "(pp.42-43)" for ranges.
