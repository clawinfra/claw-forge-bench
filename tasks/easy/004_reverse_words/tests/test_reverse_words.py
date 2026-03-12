"""Tests for reverse_words."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from reverse_words import reverse_words


def test_basic():
    assert reverse_words("hello world") == "world hello"


def test_multiple_words():
    assert reverse_words("the quick brown fox") == "fox brown quick the"


def test_single_word():
    assert reverse_words("hello") == "hello"


def test_extra_spaces():
    assert reverse_words("  hello   world  ") == "world hello"
