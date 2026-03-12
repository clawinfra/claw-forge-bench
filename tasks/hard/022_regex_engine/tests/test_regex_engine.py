"""Tests for regex engine."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from regex_engine import match


def test_literal():
    assert match("abc", "abc") is True
    assert match("abc", "abd") is False


def test_dot():
    assert match("a.c", "abc") is True
    assert match("a.c", "aXc") is True


def test_star():
    assert match("a*", "") is True
    assert match("a*", "aaa") is True


def test_star_backtrack():
    """The star must backtrack to allow subsequent patterns to match."""
    assert match("a*a", "aa") is True
    assert match(".*b", "aab") is True


def test_plus():
    assert match("a+", "a") is True
    assert match("a+", "") is False


def test_question():
    assert match("a?b", "b") is True
    assert match("a?b", "ab") is True
    assert match("a?b", "aab") is False


def test_complex():
    assert match("a.*b", "axyzb") is True
    assert match("a.*b", "a") is False
