"""Discover and validate benchmark tasks from the tasks/ directory."""
from __future__ import annotations

import ast
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from bench.models import Difficulty, TaskMeta


def discover_tasks(tasks_dir: Path) -> list[TaskMeta]:
    """Walk tasks/{easy,medium,hard}/ and return sorted TaskMeta list.

    Validates each task has: src/*.py, tests/test_*.py, app_spec.xml.
    Raises ValueError if any task is malformed.
    """
    tasks: list[TaskMeta] = []
    for difficulty in Difficulty:
        tier_dir = tasks_dir / difficulty.value
        if not tier_dir.is_dir():
            continue
        for task_dir in sorted(tier_dir.iterdir()):
            if not task_dir.is_dir():
                continue
            # Find source file
            src_dir = task_dir / "src"
            if not src_dir.is_dir():
                raise ValueError(f"Task {task_dir.name}: missing src/ directory")
            src_files = list(src_dir.glob("*.py"))
            if not src_files:
                raise ValueError(f"Task {task_dir.name}: no .py files in src/")
            source_file = src_files[0]

            # Find test file
            test_dir = task_dir / "tests"
            if not test_dir.is_dir():
                raise ValueError(f"Task {task_dir.name}: missing tests/ directory")
            test_files = list(test_dir.glob("test_*.py"))
            if not test_files:
                raise ValueError(f"Task {task_dir.name}: no test_*.py files in tests/")
            test_file = test_files[0]

            # Check app_spec.xml
            spec = task_dir / "app_spec.xml"
            if not spec.exists():
                raise ValueError(f"Task {task_dir.name}: missing app_spec.xml")

            # Extract description from app_spec.xml
            tree = ET.parse(spec)
            root = tree.getroot()
            overview = root.findtext("overview") or ""

            test_count = count_test_cases(test_file)

            tasks.append(
                TaskMeta(
                    task_id=task_dir.name,
                    difficulty=difficulty,
                    description=overview.strip(),
                    source_file=str(source_file.relative_to(task_dir)),
                    test_file=str(test_file.relative_to(task_dir)),
                    task_dir=task_dir,
                    expected_test_count=test_count,
                )
            )
    return tasks


def validate_task(task: TaskMeta) -> list[str]:
    """Return a list of validation errors (empty = valid).

    Checks:
    - Source file exists and is valid Python (compiles)
    - Test file exists and is valid Python
    - app_spec.xml is well-formed XML with exactly 1 <feature>
    - Test file has at least 3 test cases
    """
    errors: list[str] = []
    src_path = task.task_dir / task.source_file
    test_path = task.task_dir / task.test_file
    spec_path = task.task_dir / "app_spec.xml"

    # Check source file compiles
    if not src_path.exists():
        errors.append(f"Source file not found: {src_path}")
    else:
        try:
            ast.parse(src_path.read_text())
        except SyntaxError as e:
            errors.append(f"Source file syntax error at line {e.lineno}: {e.msg}")

    # Check test file compiles
    if not test_path.exists():
        errors.append(f"Test file not found: {test_path}")
    else:
        try:
            ast.parse(test_path.read_text())
        except SyntaxError as e:
            errors.append(f"Test file syntax error at line {e.lineno}: {e.msg}")

    # Check app_spec.xml
    if not spec_path.exists():
        errors.append(f"app_spec.xml not found: {spec_path}")
    else:
        try:
            tree = ET.parse(spec_path)
            root = tree.getroot()
            features = root.findall(".//feature")
            if len(features) != 1:
                errors.append(
                    f"app_spec.xml has {len(features)} features, expected 1"
                )
        except ET.ParseError as e:
            errors.append(f"app_spec.xml parse error: {e}")

    # Check test count
    if task.expected_test_count < 3:
        errors.append(
            f"Test file has {task.expected_test_count} test cases, minimum is 3"
        )

    return errors


def count_test_cases(test_file: Path) -> int:
    """Parse a pytest file and return the number of test_* functions/methods."""
    content = test_file.read_text()
    # Match both standalone functions and class methods
    pattern = r"^\s*(?:async\s+)?def\s+(test_\w+)"
    matches = re.findall(pattern, content, re.MULTILINE)
    return len(matches)
