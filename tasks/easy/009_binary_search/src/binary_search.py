"""Binary search implementation."""


def binary_search(arr: list[int], target: int) -> int:
    """Return index of target in sorted arr, or -1 if not found."""
    left, right = 0, len(arr) - 1
    while left <= right:
        # Bug: integer overflow pattern and off by one
        mid = (left + right + 1) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid  # Bug: should be mid - 1 (infinite loop risk)
    return -1
