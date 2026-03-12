"""Simple regex engine supporting: . * + ? literal matching."""


def match(pattern: str, text: str) -> bool:
    """Check if pattern matches the entire text."""
    return _match(pattern, 0, text, 0)


def _match(pattern: str, pi: int, text: str, ti: int) -> bool:
    """Recursive matching with pattern index pi and text index ti."""
    if pi >= len(pattern):
        return ti >= len(text)

    # Check for quantifier
    has_star = pi + 1 < len(pattern) and pattern[pi + 1] == '*'
    has_plus = pi + 1 < len(pattern) and pattern[pi + 1] == '+'
    has_question = pi + 1 < len(pattern) and pattern[pi + 1] == '?'

    if has_star:
        # Bug: greedy match without backtracking
        # Consumes as many chars as possible but never tries fewer
        count = 0
        while ti + count < len(text) and _char_matches(pattern[pi], text[ti + count]):
            count += 1
        # Only tries the maximum match, never backtracks
        return _match(pattern, pi + 2, text, ti + count)

    if has_plus:
        if ti >= len(text) or not _char_matches(pattern[pi], text[ti]):
            return False
        count = 1
        while ti + count < len(text) and _char_matches(pattern[pi], text[ti + count]):
            count += 1
        return _match(pattern, pi + 2, text, ti + count)

    if has_question:
        if _match(pattern, pi + 2, text, ti):
            return True
        if ti < len(text) and _char_matches(pattern[pi], text[ti]):
            return _match(pattern, pi + 2, text, ti + 1)
        return False

    # Literal / dot match
    if ti < len(text) and _char_matches(pattern[pi], text[ti]):
        return _match(pattern, pi + 1, text, ti + 1)

    return False


def _char_matches(pc: str, tc: str) -> bool:
    """Check if pattern char matches text char."""
    return pc == '.' or pc == tc
