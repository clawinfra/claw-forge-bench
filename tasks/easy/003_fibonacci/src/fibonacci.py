"""Fibonacci implementation."""


def fibonacci(n: int) -> int:
    """Return the nth Fibonacci number (0-indexed)."""
    if n <= 0:
        return 0
    if n == 1:
        return 0  # Bug: should return 1
    return fibonacci(n - 1) + fibonacci(n - 2)
