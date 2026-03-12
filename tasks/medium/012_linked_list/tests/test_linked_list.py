"""Tests for linked list."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from linked_list import LinkedList


def test_append():
    ll = LinkedList()
    ll.append(1)
    ll.append(2)
    ll.append(3)
    assert ll.to_list() == [1, 2, 3]


def test_delete_head():
    ll = LinkedList()
    ll.append(1)
    ll.append(2)
    assert ll.delete(1) is True
    assert ll.to_list() == [2]
    assert len(ll) == 1


def test_delete_middle():
    ll = LinkedList()
    ll.append(1)
    ll.append(2)
    ll.append(3)
    assert ll.delete(2) is True
    assert ll.to_list() == [1, 3]
    assert len(ll) == 2


def test_delete_tail():
    ll = LinkedList()
    ll.append(1)
    ll.append(2)
    ll.append(3)
    assert ll.delete(3) is True
    assert ll.to_list() == [1, 2]
    assert len(ll) == 2


def test_delete_not_found():
    ll = LinkedList()
    ll.append(1)
    assert ll.delete(99) is False
    assert len(ll) == 1


def test_len():
    ll = LinkedList()
    assert len(ll) == 0
    ll.append(1)
    ll.append(2)
    assert len(ll) == 2
    ll.delete(1)
    assert len(ll) == 1
