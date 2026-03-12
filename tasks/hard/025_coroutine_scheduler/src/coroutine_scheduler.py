"""Simple coroutine scheduler."""
from collections import deque


class Scheduler:
    """Round-robin coroutine scheduler."""

    def __init__(self):
        self.ready: deque = deque()
        self.results: dict[str, object] = {}

    def spawn(self, name: str, coroutine):
        """Add a coroutine to the scheduler."""
        self.ready.append((name, coroutine, None))

    def run(self) -> dict[str, object]:
        """Run all coroutines until completion."""
        while self.ready:
            name, coro, send_val = self.ready.popleft()
            try:
                # Bug: always uses next() instead of send(), ignoring yielded values
                # This means coroutines that use `val = yield expr` never get the value back
                value = next(coro)
                self.ready.append((name, coro, None))
            except StopIteration as e:
                self.results[name] = e.value
        return self.results


def task_counter(n: int):
    """A coroutine that counts up to n, yielding each value."""
    total = 0
    for i in range(1, n + 1):
        total += i
        yield total
    return total


def task_accumulator(values: list):
    """A coroutine that accumulates values, yielding partial sums."""
    total = 0
    for v in values:
        total += v
        yield total
    return total


def task_echo_chain(n: int):
    """A coroutine that yields a value and expects to receive it back via send().
    
    Each step: yield current → receive back → add to total.
    If send() works: total = sum of all sent-back values = sum(1..n) 
    If only next() is used: received is always None, total = 0
    """
    total = 0
    for i in range(1, n + 1):
        received = yield i  # expects to get i back via send()
        if received is not None:
            total += received
    return total
