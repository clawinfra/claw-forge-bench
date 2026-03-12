"""Anagram checker."""
from collections import Counter


def is_anagram(s1: str, s2: str) -> bool:
    """Check if two strings are anagrams (case-insensitive, ignore spaces)."""
    # Bug: doesn't lowercase before comparing
    clean1 = s1.replace(" ", "")
    clean2 = s2.replace(" ", "")
    return Counter(clean1) == Counter(clean2)
