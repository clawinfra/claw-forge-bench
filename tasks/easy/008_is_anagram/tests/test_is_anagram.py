"""Tests for is_anagram."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from is_anagram import is_anagram


def test_basic_anagram():
    assert is_anagram("listen", "silent") is True


def test_not_anagram():
    assert is_anagram("hello", "world") is False


def test_case_insensitive():
    assert is_anagram("Listen", "Silent") is True
    assert is_anagram("Dormitory", "dirty room") is True


def test_with_spaces():
    assert is_anagram("a gentleman", "elegant man") is True
