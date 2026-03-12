"""Tests for stack calculator."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from stack_calculator import calculate


def test_addition():
    assert calculate("2 + 3") == 5.0


def test_multiplication():
    assert calculate("2 * 3") == 6.0


def test_precedence():
    """Multiplication should be evaluated before addition."""
    assert calculate("2 + 3 * 4") == 14.0


def test_precedence_complex():
    assert calculate("1 + 2 * 3 + 4") == 11.0


def test_division():
    assert calculate("10 / 2") == 5.0


def test_mixed():
    assert calculate("2 * 3 + 4 * 5") == 26.0
