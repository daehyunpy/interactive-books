BLOCK_TAGS = frozenset({
    "p", "div", "h1", "h2", "h3", "h4", "h5", "h6",
    "li", "blockquote", "tr", "br", "section", "article",
})


def extract_block_text(node: object) -> str:
    """Extract text from a selectolax node, inserting newlines at block tag boundaries."""
    parts: list[str] = []
    for child in node.iter():  # type: ignore[union-attr]
        if child.tag in BLOCK_TAGS and parts and parts[-1] != "\n":
            parts.append("\n")
        text = child.text(deep=False, strip=False) if hasattr(child, "text") else ""
        if text:
            parts.append(text)
    return "".join(parts).strip()
