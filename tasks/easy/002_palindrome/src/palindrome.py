"""Palindrome checker."""


def is_palindrome(s: str) -> bool:
    """Check if string is a palindrome (case-insensitive, alphanumeric only)."""
    cleaned = "".join(c.lower() for c in s if c.isalnum())
    # Bug: compares to wrong slice (excludes last char)
    return cleaned == cleaned[-2::-1]
