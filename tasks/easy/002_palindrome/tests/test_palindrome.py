"""Tests for palindrome."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from palindrome import is_palindrome


def test_simple_palindrome():
    assert is_palindrome("racecar") is True
    assert is_palindrome("madam") is True


def test_not_palindrome():
    assert is_palindrome("hello") is False
    assert is_palindrome("python") is False


def test_case_insensitive():
    assert is_palindrome("RaceCar") is True
    assert is_palindrome("Madam") is True


def test_with_spaces_and_punctuation():
    assert is_palindrome("A man, a plan, a canal: Panama") is True
    assert is_palindrome("race a car") is False


def test_empty_and_single():
    assert is_palindrome("") is True
    assert is_palindrome("a") is True
