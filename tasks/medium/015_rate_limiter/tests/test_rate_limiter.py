"""Tests for rate limiter."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rate_limiter import RateLimiter


def test_basic_allow():
    rl = RateLimiter(3, 10.0)
    assert rl.allow(1.0) is True
    assert rl.allow(2.0) is True
    assert rl.allow(3.0) is True
    assert rl.allow(4.0) is False  # limit reached


def test_window_expiry():
    rl = RateLimiter(2, 5.0)
    assert rl.allow(1.0) is True
    assert rl.allow(2.0) is True
    assert rl.allow(3.0) is False
    # After window expires for first request
    assert rl.allow(7.0) is True  # t=1 expired


def test_sliding_window():
    """Sliding window should expire individual requests, not all at once."""
    rl = RateLimiter(2, 5.0)
    assert rl.allow(1.0) is True
    assert rl.allow(3.0) is True
    assert rl.allow(5.0) is False  # both still in window
    # At t=7, only t=1 has expired; t=3 is still in window
    assert rl.allow(7.0) is True
    assert rl.allow(7.5) is False  # t=3 and t=7 in window


def test_remaining():
    rl = RateLimiter(3, 10.0)
    assert rl.remaining(0.0) == 3
    rl.allow(1.0)
    assert rl.remaining(2.0) == 2
