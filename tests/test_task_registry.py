"""Unit tests for task discovery and validation."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from bench.models import Difficulty
from bench.task_registry import count_test_cases, discover_tasks, validate_task

TASKS_DIR = PROJECT_ROOT / "tasks"


def test_discover_all_30_tasks():
    """Should find exactly 30 tasks."""
    tasks = discover_tasks(TASKS_DIR)
    assert len(tasks) == 30


def test_10_easy_tasks():
    """Should find exactly 10 easy tasks."""
    tasks = discover_tasks(TASKS_DIR)
    easy = [t for t in tasks if t.difficulty == Difficulty.EASY]
    assert len(easy) == 10


def test_10_medium_tasks():
    """Should find exactly 10 medium tasks."""
    tasks = discover_tasks(TASKS_DIR)
    medium = [t for t in tasks if t.difficulty == Difficulty.MEDIUM]
    assert len(medium) == 10


def test_10_hard_tasks():
    """Should find exactly 10 hard tasks."""
    tasks = discover_tasks(TASKS_DIR)
    hard = [t for t in tasks if t.difficulty == Difficulty.HARD]
    assert len(hard) == 10


def test_task_ids_are_unique():
    """All task IDs should be unique."""
    tasks = discover_tasks(TASKS_DIR)
    ids = [t.task_id for t in tasks]
    assert len(ids) == len(set(ids))


def test_all_tasks_have_source_files():
    """Every task should have a source file."""
    tasks = discover_tasks(TASKS_DIR)
    for t in tasks:
        src = t.task_dir / t.source_file
        assert src.exists(), f"Missing source file: {src}"


def test_all_tasks_have_test_files():
    """Every task should have a test file."""
    tasks = discover_tasks(TASKS_DIR)
    for t in tasks:
        test = t.task_dir / t.test_file
        assert test.exists(), f"Missing test file: {test}"


def test_all_tasks_have_app_spec():
    """Every task should have an app_spec.xml."""
    tasks = discover_tasks(TASKS_DIR)
    for t in tasks:
        spec = t.task_dir / "app_spec.xml"
        assert spec.exists(), f"Missing app_spec.xml: {spec}"


def test_all_tasks_have_claude_md():
    """Every task should have a CLAUDE.md."""
    tasks = discover_tasks(TASKS_DIR)
    for t in tasks:
        claude = t.task_dir / "CLAUDE.md"
        assert claude.exists(), f"Missing CLAUDE.md: {claude}"


def test_all_tasks_validate():
    """All tasks should pass validation."""
    tasks = discover_tasks(TASKS_DIR)
    for t in tasks:
        errors = validate_task(t)
        assert not errors, f"Task {t.task_id} validation errors: {errors}"


def test_minimum_test_count():
    """Each task should have at least 3 test cases."""
    tasks = discover_tasks(TASKS_DIR)
    for t in tasks:
        assert t.expected_test_count >= 3, (
            f"Task {t.task_id} has only {t.expected_test_count} tests"
        )


def test_count_test_cases():
    """count_test_cases should correctly count test functions."""
    tasks = discover_tasks(TASKS_DIR)
    fizzbuzz = next(t for t in tasks if t.task_id == "001_fizzbuzz")
    count = count_test_cases(fizzbuzz.task_dir / fizzbuzz.test_file)
    assert count >= 3
