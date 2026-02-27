You are summarizing a section of a book. The section spans pages {{start_page}} to {{end_page}}.

Analyze the content below and produce a JSON object with exactly these fields:

- **title**: A short heading for this section (max 10 words). Identify the main topic or chapter heading from the content.
- **summary**: A 2-3 sentence summary of the section's key content.
- **key_statements**: An array of 1-3 important statements from this section. Each entry has:
  - **statement**: The key claim, event, or idea (one sentence).
  - **page**: The page number where this statement appears or is most relevant (integer between {{start_page}} and {{end_page}}).

Respond with ONLY valid JSON. No markdown formatting, no code fences, no extra text.

Example response format:
{"title": "The Industrial Revolution", "summary": "This section covers the origins of industrialization in 18th century England. It examines how technological innovations transformed manufacturing and labor.", "key_statements": [{"statement": "The spinning jenny reduced the cost of textile production by 80%.", "page": 12}, {"statement": "Factory workers migrated from rural areas in unprecedented numbers.", "page": 14}]}

Section content:
{{content}}