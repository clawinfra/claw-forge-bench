"""Simple diff algorithm (longest common subsequence based)."""


def diff(old: list[str], new: list[str]) -> list[tuple[str, str]]:
    """Compute diff between old and new sequences.

    Returns list of (op, line) tuples:
    - ("=", line) — unchanged
    - ("-", line) — removed from old
    - ("+", line) — added in new
    """
    # Bug: uses a greedy approach that doesn't find optimal LCS
    result = []
    i, j = 0, 0
    while i < len(old) and j < len(new):
        if old[i] == new[j]:
            result.append(("=", old[i]))
            i += 1
            j += 1
        else:
            # Bug: always deletes from old first, never considers
            # that inserting from new might produce a shorter diff
            result.append(("-", old[i]))
            i += 1
    while i < len(old):
        result.append(("-", old[i]))
        i += 1
    while j < len(new):
        result.append(("+", new[j]))
        j += 1
    return result


def apply_diff(old: list[str], operations: list[tuple[str, str]]) -> list[str]:
    """Apply diff operations to reconstruct the new sequence."""
    result = []
    for op, line in operations:
        if op == "=" or op == "+":
            result.append(line)
    return result


def edit_distance(old: list[str], new: list[str]) -> int:
    """Compute the minimum edit distance (insertions + deletions)."""
    ops = diff(old, new)
    return sum(1 for op, _ in ops if op != "=")
