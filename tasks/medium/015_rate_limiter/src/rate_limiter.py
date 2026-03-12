"""Sliding window rate limiter."""
import time


class RateLimiter:
    """Rate limiter with a sliding window."""

    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: list[float] = []

    def allow(self, timestamp: float | None = None) -> bool:
        """Check if a request is allowed at the given timestamp."""
        now = timestamp if timestamp is not None else time.time()
        # Bug: clears ALL requests when window expires instead of sliding
        if self.requests and now - self.requests[0] > self.window_seconds:
            self.requests.clear()
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False

    def remaining(self, timestamp: float | None = None) -> int:
        """Return remaining allowed requests in current window."""
        now = timestamp if timestamp is not None else time.time()
        if self.requests and now - self.requests[0] > self.window_seconds:
            self.requests.clear()
        return max(0, self.max_requests - len(self.requests))
