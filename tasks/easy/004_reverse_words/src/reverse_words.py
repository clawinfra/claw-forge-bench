"""Reverse words in a string."""


def reverse_words(s: str) -> str:
    """Reverse the order of words in a string."""
    # Bug: splits on comma instead of whitespace
    words = s.split(",")
    return " ".join(reversed(words))
