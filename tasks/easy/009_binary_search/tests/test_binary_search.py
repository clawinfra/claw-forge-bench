"""Tests for binary_search."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from binary_search import binary_search


def test_found():
    assert binary_search([1, 3, 5, 7, 9], 5) == 2


def test_not_found():
    assert binary_search([1, 3, 5, 7, 9], 4) == -1


def test_first_element():
    assert binary_search([1, 3, 5, 7, 9], 1) == 0


def test_last_element():
    assert binary_search([1, 3, 5, 7, 9], 9) == 4


def test_empty():
    assert binary_search([], 5) == -1


def test_single_element():
    assert binary_search([5], 5) == 0
    assert binary_search([5], 3) == -1
