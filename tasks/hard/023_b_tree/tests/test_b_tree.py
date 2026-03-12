"""Tests for B-tree."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from b_tree import BTree


def test_insert_and_search():
    bt = BTree(order=3)
    bt.insert(10)
    bt.insert(20)
    assert bt.search(10) is True
    assert bt.search(20) is True
    assert bt.search(30) is False


def test_insert_causes_split():
    bt = BTree(order=3)
    for val in [10, 20, 30]:
        bt.insert(val)
    assert bt.search(10) is True
    assert bt.search(20) is True
    assert bt.search(30) is True


def test_in_order():
    bt = BTree(order=3)
    values = [30, 10, 20, 40, 50]
    for v in values:
        bt.insert(v)
    assert bt.in_order() == sorted(values)


def test_many_inserts():
    bt = BTree(order=3)
    values = [5, 3, 8, 1, 4, 7, 9, 2, 6]
    for v in values:
        bt.insert(v)
    assert bt.in_order() == sorted(values)
    for v in values:
        assert bt.search(v) is True


def test_no_duplicates_in_order():
    """After splits, no key should appear twice."""
    bt = BTree(order=3)
    for v in range(1, 11):
        bt.insert(v)
    result = bt.in_order()
    assert result == list(range(1, 11))
    assert len(result) == len(set(result))
