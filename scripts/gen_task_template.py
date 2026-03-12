"""Helper to scaffold a new benchmark task."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    """Scaffold a new task directory."""
    parser = argparse.ArgumentParser(description="Generate a benchmark task template")
    parser.add_argument("task_id", help="Task ID (e.g. 001_fizzbuzz)")
    parser.add_argument("difficulty", choices=["easy", "medium", "hard"])
    parser.add_argument("--name", help="Module name (default: derived from task_id)")
    args = parser.parse_args()

    name = args.name or args.task_id.split("_", 1)[1] if "_" in args.task_id else args.task_id
    task_dir = PROJECT_ROOT / "tasks" / args.difficulty / args.task_id

    if task_dir.exists():
        print(f"Task already exists: {task_dir}")
        return 1

    (task_dir / "src").mkdir(parents=True)
    (task_dir / "tests").mkdir(parents=True)

    # Source template
    src_content = f'"""Broken implementation of {name}."""\n\n\n'
    src_content += f"def {name}():\n    # TODO: implement\n    pass\n"
    (task_dir / "src" / f"{name}.py").write_text(src_content)

    # Test template
    (task_dir / "tests" / f"test_{name}.py").write_text(
        f'"""Tests for {name}."""\nimport sys\nfrom pathlib import Path\n\n'
        f'sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))\n\n'
        f'from {name} import {name}\n\n\n'
        f'def test_{name}_basic():\n    assert {name}() is not None\n\n\n'
        f'def test_{name}_case2():\n    pass\n\n\n'
        f'def test_{name}_case3():\n    pass\n'
    )

    # App spec
    (task_dir / "app_spec.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<project_specification mode="greenfield">\n'
        f'  <project_name>bench-{args.task_id}</project_name>\n'
        f'  <overview>Fix the {name} implementation to pass all tests.</overview>\n'
        f"  <technology_stack>\n"
        f"    <language>Python 3.11+</language>\n"
        f"    <testing>pytest</testing>\n"
        f"  </technology_stack>\n"
        f"  <features>\n"
        f'    <feature id="fix-impl" priority="P0">\n'
        f"      <title>Fix implementation</title>\n"
        f"      <description>\n"
        f"        Fix the implementation in src/{name}.py so that all tests\n"
        f"        in tests/test_{name}.py pass.\n"
        f"      </description>\n"
        f"      <acceptance_criteria>\n"
        f"        <criterion>All tests in tests/test_{name}.py pass</criterion>\n"
        f"      </acceptance_criteria>\n"
        f"    </feature>\n"
        f"  </features>\n"
        f"</project_specification>\n"
    )

    # CLAUDE.md
    (task_dir / "CLAUDE.md").write_text(
        f"# Task: Fix {name}\n\n"
        f"The file `src/{name}.py` has a bug. Your job is to fix it so that all tests pass.\n\n"
        f"## Instructions\n"
        f"1. Read `tests/test_{name}.py` to understand expected behavior\n"
        f"2. Read `src/{name}.py` to find the bug\n"
        f"3. Fix the bug — make minimal changes\n"
        f"4. Run `pytest tests/` to verify all tests pass\n\n"
        f"## Constraints\n"
        f"- Do NOT modify test files\n"
        f"- Make the minimal change needed to fix the bug\n"
        f"- Do NOT add new dependencies\n"
    )

    print(f"Created task template: {task_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
