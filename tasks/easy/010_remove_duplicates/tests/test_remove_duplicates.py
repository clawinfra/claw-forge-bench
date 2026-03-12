"""Tests for remove_duplicates."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from remove_duplicates import remove_duplicates


def test_basic():
    assert remove_duplicates([1, 2, 3, 2, 1]) == [1, 2, 3]


def test_preserves_order():
    assert remove_duplicates([3, 1, 2, 1, 3]) == [3, 1, 2]


def test_no_duplicates():
    assert remove_duplicates([1, 2, 3]) == [1, 2, 3]


def test_all_same():
    assert remove_duplicates([1, 1, 1]) == [1]


def test_empty():
    assert remove_duplicates([]) == []


def test_strings():
    result = remove_duplicates(["b", "a", "b", "c", "a"])
    assert result == ["b", "a", "c"]
