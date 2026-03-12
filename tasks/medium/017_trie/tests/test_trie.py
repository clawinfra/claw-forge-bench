"""Tests for trie."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from trie import Trie


def test_insert_and_search():
    t = Trie()
    t.insert("apple")
    assert t.search("apple") is True


def test_search_not_found():
    t = Trie()
    t.insert("apple")
    assert t.search("app") is False  # prefix, not full word


def test_starts_with():
    t = Trie()
    t.insert("apple")
    assert t.starts_with("app") is True
    assert t.starts_with("b") is False


def test_multiple_words():
    t = Trie()
    t.insert("apple")
    t.insert("app")
    assert t.search("app") is True
    assert t.search("apple") is True


def test_empty_search():
    t = Trie()
    assert t.search("anything") is False
