"""Text wrapper that breaks lines at word boundaries."""


def wrap_text(text: str, width: int) -> str:
    """Wrap text to the specified width, breaking at word boundaries."""
    # Bug: breaks at exact character position, not at word boundaries
    lines = []
    while len(text) > width:
        lines.append(text[:width])
        text = text[width:]
    if text:
        lines.append(text)
    return "\n".join(lines)
