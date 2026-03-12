"""Tests for matrix multiplication."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from matrix_multiply import matrix_multiply


def test_identity():
    a = [[1, 0], [0, 1]]
    b = [[5, 6], [7, 8]]
    assert matrix_multiply(a, b) == [[5.0, 6.0], [7.0, 8.0]]


def test_basic():
    a = [[1, 2], [3, 4]]
    b = [[5, 6], [7, 8]]
    result = matrix_multiply(a, b)
    assert result == [[19.0, 22.0], [43.0, 50.0]]


def test_non_square():
    a = [[1, 2, 3]]
    b = [[4], [5], [6]]
    assert matrix_multiply(a, b) == [[32.0]]


def test_incompatible():
    a = [[1, 2]]
    b = [[3, 4]]
    try:
        matrix_multiply(a, b)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
