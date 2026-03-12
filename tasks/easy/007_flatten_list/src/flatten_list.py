"""Flatten nested lists."""


def flatten(lst: list) -> list:
    """Flatten a nested list into a single list."""
    result = []
    for item in lst:
        if isinstance(item, list):
            # Bug: only flattens one level, doesn't recurse
            result.extend(item)
        else:
            result.append(item)
    return result
