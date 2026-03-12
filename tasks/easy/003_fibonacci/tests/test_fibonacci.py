"""Tests for fibonacci."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fibonacci import fibonacci


def test_base_cases():
    assert fibonacci(0) == 0
    assert fibonacci(1) == 1


def test_small_values():
    assert fibonacci(2) == 1
    assert fibonacci(3) == 2
    assert fibonacci(4) == 3
    assert fibonacci(5) == 5


def test_larger_values():
    assert fibonacci(10) == 55
    assert fibonacci(15) == 610


def test_negative():
    assert fibonacci(-1) == 0
