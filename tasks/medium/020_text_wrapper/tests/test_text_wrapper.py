"""Tests for text wrapper."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from text_wrapper import wrap_text


def test_no_wrap():
    assert wrap_text("hello", 10) == "hello"


def test_basic_wrap():
    result = wrap_text("hello world foo", 11)
    assert result == "hello world\nfoo"


def test_word_boundary():
    """Should not break in the middle of a word."""
    result = wrap_text("the quick brown fox", 10)
    lines = result.split("\n")
    for line in lines:
        # No line should start or end with a partial word fragment
        for word in line.split():
            assert word in ["the", "quick", "brown", "fox"]


def test_exact_width():
    assert wrap_text("hello world", 11) == "hello world"


def test_long_text():
    text = "the quick brown fox jumps over the lazy dog"
    result = wrap_text(text, 15)
    lines = result.split("\n")
    for line in lines:
        assert len(line) <= 15
