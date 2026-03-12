"""Tests for diff algorithm."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from diff_algorithm import diff, apply_diff, edit_distance


def test_identical():
    old = ["a", "b", "c"]
    ops = diff(old, old)
    assert all(op == "=" for op, _ in ops)


def test_insertion():
    old = ["a", "c"]
    new = ["a", "b", "c"]
    ops = diff(old, new)
    result = apply_diff(old, ops)
    assert result == new


def test_deletion():
    old = ["a", "b", "c"]
    new = ["a", "c"]
    ops = diff(old, new)
    result = apply_diff(old, ops)
    assert result == new


def test_minimal_diff():
    """Diff should produce minimal edits, not greedy ones."""
    old = ["a", "b", "c", "d"]
    new = ["a", "x", "c", "d"]
    ops = diff(old, new)
    # Optimal: keep a, delete b, insert x, keep c, keep d = 2 edits
    edits = sum(1 for op, _ in ops if op != "=")
    assert edits == 2


def test_edit_distance():
    old = ["a", "b", "c"]
    new = ["a", "x", "c"]
    assert edit_distance(old, new) == 2  # -b, +x


def test_complete_replacement():
    old = ["a", "b"]
    new = ["c", "d"]
    ops = diff(old, new)
    result = apply_diff(old, ops)
    assert result == new
