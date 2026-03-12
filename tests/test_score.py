"""Unit tests for the scoring engine."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from bench.models import ConfigID, Difficulty, TaskResult
from bench.score import compute_config_summary, compute_summary, pass_rate_by_difficulty


def _make_result(task_id: str, config_id: ConfigID, passed: bool) -> TaskResult:
    return TaskResult(
        task_id=task_id,
        config_id=config_id,
        passed=passed,
        tests_total=5,
        tests_passed=5 if passed else 2,
        tests_failed=0 if passed else 3,
        duration_seconds=10.0,
        exit_code=0,
        pytest_exit_code=0 if passed else 1,
    )


def test_compute_config_summary_all_pass():
    results = [
        _make_result("001_fizzbuzz", ConfigID.A, True),
        _make_result("002_palindrome", ConfigID.A, True),
    ]
    summary = compute_config_summary(ConfigID.A, "baseline", results, 0.0)
    assert summary.pass_rate == 1.0
    assert summary.tasks_passed == 2
    assert summary.total_tasks == 2


def test_compute_config_summary_mixed():
    results = [
        _make_result("001_fizzbuzz", ConfigID.A, True),
        _make_result("002_palindrome", ConfigID.A, False),
    ]
    summary = compute_config_summary(ConfigID.A, "baseline", results, 0.0)
    assert summary.pass_rate == 0.5
    assert summary.tasks_passed == 1


def test_delta_vs_baseline():
    results = [
        _make_result("001_fizzbuzz", ConfigID.B, True),
        _make_result("002_palindrome", ConfigID.B, True),
    ]
    summary = compute_config_summary(ConfigID.B, "hashline", results, 0.5)
    assert abs(summary.delta_vs_baseline - 0.5) < 0.01


def test_pass_rate_by_difficulty():
    difficulty_map = {
        "001_fizzbuzz": Difficulty.EASY,
        "002_palindrome": Difficulty.EASY,
        "011_lru_cache": Difficulty.MEDIUM,
    }
    results = [
        _make_result("001_fizzbuzz", ConfigID.A, True),
        _make_result("002_palindrome", ConfigID.A, False),
        _make_result("011_lru_cache", ConfigID.A, True),
    ]
    rates = pass_rate_by_difficulty(results, difficulty_map)
    assert rates[Difficulty.EASY] == 0.5
    assert rates[Difficulty.MEDIUM] == 1.0


def test_compute_summary():
    results = [
        _make_result("001_fizzbuzz", ConfigID.A, True),
        _make_result("002_palindrome", ConfigID.A, False),
        _make_result("001_fizzbuzz", ConfigID.B, True),
        _make_result("002_palindrome", ConfigID.B, True),
    ]
    summary = compute_summary(results, model="test-model", run_id="test-run")
    assert summary.task_count == 2
    assert len(summary.configs) == 2
    assert summary.model == "test-model"
    # B should be better than A
    a_summary = next(c for c in summary.configs if c.config_id == ConfigID.A)
    b_summary = next(c for c in summary.configs if c.config_id == ConfigID.B)
    assert b_summary.pass_rate > a_summary.pass_rate


def test_best_config():
    results = [
        _make_result("001_fizzbuzz", ConfigID.A, False),
        _make_result("001_fizzbuzz", ConfigID.B, True),
        _make_result("001_fizzbuzz", ConfigID.E, True),
    ]
    summary = compute_summary(results, model="test")
    assert summary.best_config in (ConfigID.B, ConfigID.E)


def test_hashline_impact():
    results = [
        _make_result("001_fizzbuzz", ConfigID.A, False),
        _make_result("001_fizzbuzz", ConfigID.B, True),
    ]
    summary = compute_summary(results, model="test")
    assert summary.hashline_impact == 1.0  # 100% - 0% = 100%
