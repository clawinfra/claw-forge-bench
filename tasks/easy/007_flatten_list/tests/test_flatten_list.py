"""Tests for flatten_list."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from flatten_list import flatten


def test_flat():
    assert flatten([1, 2, 3]) == [1, 2, 3]


def test_one_level():
    assert flatten([1, [2, 3], 4]) == [1, 2, 3, 4]


def test_deep_nesting():
    assert flatten([1, [2, [3, [4]]]]) == [1, 2, 3, 4]


def test_empty():
    assert flatten([]) == []
    assert flatten([[], []]) == []


def test_mixed_types():
    assert flatten([1, "a", [2, "b", [3]]]) == [1, "a", 2, "b", 3]
