"""Flatten nested JSON/dict structures."""


def flatten_json(data: dict, prefix: str = "", sep: str = ".") -> dict:
    """Flatten a nested dict into a flat dict with dotted keys."""
    result = {}
    for key, value in data.items():
        new_key = f"{prefix}{sep}{key}" if prefix else key
        if isinstance(value, dict):
            result.update(flatten_json(value, new_key, sep))
        # Bug: doesn't handle lists/arrays — just stores them as-is
        else:
            result[new_key] = value
    return result
