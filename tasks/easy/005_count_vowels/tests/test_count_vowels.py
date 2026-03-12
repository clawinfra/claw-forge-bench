"""Tests for count_vowels."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from count_vowels import count_vowels


def test_basic():
    assert count_vowels("hello") == 2


def test_all_vowels():
    assert count_vowels("aeiou") == 5


def test_uppercase():
    assert count_vowels("AEIOU") == 5


def test_no_vowels():
    assert count_vowels("bcdfg") == 0


def test_with_u():
    assert count_vowels("ubuntu") == 3
