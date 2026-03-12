"""Pre-flight: verify all tasks are correctly specified."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from bench.task_registry import discover_tasks, validate_task


def main() -> int:
    """Validate all benchmark tasks."""
    parser = argparse.ArgumentParser(description="Validate benchmark tasks")
    parser.add_argument(
        "--tasks-dir",
        default=str(PROJECT_ROOT / "tasks"),
        help="Path to tasks directory",
    )
    parser.add_argument(
        "--red-green",
        action="store_true",
        help="Also run red-green contract tests (broken=fail, solution=pass)",
    )
    args = parser.parse_args()

    tasks_dir = Path(args.tasks_dir)
    tasks = discover_tasks(tasks_dir)

    print(f"Found {len(tasks)} tasks")
    errors_total = 0

    for task in tasks:
        errs = validate_task(task)
        if errs:
            print(f"  ✗ {task.task_id}:")
            for e in errs:
                print(f"    - {e}")
            errors_total += len(errs)
        else:
            status = f"✓ {task.task_id} ({task.expected_test_count} tests)"
            print(f"  {status}")

        # Red-green contract
        if args.red_green:
            red_ok = _check_red(task)
            green_ok = _check_green(task)
            if not red_ok:
                print("    ✗ RED FAILED: tests pass on broken source!")
                errors_total += 1
            if not green_ok:
                print("    ✗ GREEN FAILED: tests fail on solution!")
                errors_total += 1

    if errors_total > 0:
        print(f"\n{errors_total} error(s) found.")
        return 1

    print(f"\nAll {len(tasks)} tasks valid.")
    return 0


def _check_red(task) -> bool:
    """Run tests against broken source — should FAIL."""
    test_dir = task.task_dir / "tests"
    src_dir = task.task_dir / "src"
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_dir), "-q", "--tb=no"],
            capture_output=True,
            text=True,
            timeout=30,
            env={
                **__import__("os").environ,
                "PYTHONPATH": str(src_dir) + ":" + str(task.task_dir),
            },
        )
        return proc.returncode != 0  # Should fail
    except subprocess.TimeoutExpired:
        return True  # Timeout = broken enough


def _check_green(task) -> bool:
    """Run tests against solution — should PASS."""
    solution = task.task_dir / "_solution.py"
    if not solution.exists():
        return True  # Skip if no solution

    # Temporarily swap source with solution
    src_path = task.task_dir / task.source_file
    backup = src_path.read_text()
    try:
        src_path.write_text(solution.read_text())
        test_dir = task.task_dir / "tests"
        src_dir = task.task_dir / "src"
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_dir), "-q", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=30,
            env={
                **__import__("os").environ,
                "PYTHONPATH": str(src_dir) + ":" + str(task.task_dir),
            },
        )
        return proc.returncode == 0
    finally:
        src_path.write_text(backup)


if __name__ == "__main__":
    sys.exit(main())
