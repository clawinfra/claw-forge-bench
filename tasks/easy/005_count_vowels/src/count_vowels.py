"""Count vowels in a string."""


def count_vowels(s: str) -> int:
    """Count the number of vowels in a string."""
    # Bug: missing 'u' and 'U'
    vowels = set("aeiAEI")
    return sum(1 for c in s if c in vowels)
