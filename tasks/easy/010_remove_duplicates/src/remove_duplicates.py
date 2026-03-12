"""Remove duplicates from a list."""


def remove_duplicates(lst: list) -> list:
    """Remove duplicates while preserving order."""
    # Bug: set() doesn't preserve order
    return list(set(lst))
