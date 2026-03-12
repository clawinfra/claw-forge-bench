"""Tests for LRU Cache."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from lru_cache import LRUCache


def test_basic_put_get():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") == 1
    assert cache.get("b") == 2


def test_eviction():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)  # evicts "a"
    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert cache.get("c") == 3


def test_access_order_updates():
    """Getting a key should make it most recently used."""
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.get("a")  # "a" is now most recent
    cache.put("c", 3)  # should evict "b", not "a"
    assert cache.get("a") == 1
    assert cache.get("b") is None
    assert cache.get("c") == 3


def test_update_existing():
    """Updating a key should make it most recently used."""
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("a", 10)  # update "a", now most recent
    cache.put("c", 3)  # should evict "b"
    assert cache.get("a") == 10
    assert cache.get("b") is None


def test_miss():
    cache = LRUCache(2)
    assert cache.get("missing") is None


def test_size():
    cache = LRUCache(3)
    assert cache.size() == 0
    cache.put("a", 1)
    assert cache.size() == 1
    cache.put("b", 2)
    cache.put("c", 3)
    assert cache.size() == 3
    cache.put("d", 4)
    assert cache.size() == 3
