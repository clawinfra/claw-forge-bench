"""LRU Cache implementation."""
from collections import OrderedDict


class LRUCache:
    """Least Recently Used cache with fixed capacity."""

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache: OrderedDict = OrderedDict()

    def get(self, key: str) -> object | None:
        """Get value by key. Returns None if not found."""
        if key not in self.cache:
            return None
        # Bug: doesn't move to end (update access order)
        return self.cache[key]

    def put(self, key: str, value: object) -> None:
        """Put key-value pair. Evicts LRU item if at capacity."""
        if key in self.cache:
            self.cache[key] = value
            # Bug: doesn't move to end
            return
        if len(self.cache) >= self.capacity:
            self.cache.popitem(last=False)
        self.cache[key] = value

    def size(self) -> int:
        """Return current cache size."""
        return len(self.cache)
