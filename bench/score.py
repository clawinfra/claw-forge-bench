"""Scoring engine — aggregates TaskResults into BenchmarkSummary."""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from bench.models import (
    BenchmarkSummary,
    ConfigID,
    ConfigSummary,
    Difficulty,
    TaskResult,
)


def load_results(results_file: Path) -> list[TaskResult]:
    """Load TaskResults from a JSONL file."""
    results: list[TaskResult] = []
    with open(results_file) as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(TaskResult.from_jsonl(line))
    return results


def compute_summary(
    results: list[TaskResult],
    model: str,
    run_id: str = "",
    difficulty_map: dict[str, Difficulty] | None = None,
) -> BenchmarkSummary:
    """Compute full BenchmarkSummary from raw TaskResults.

    Groups by config_id, computes pass rates (overall + per-difficulty),
    computes deltas vs config A (baseline), identifies best config.
    """
    if not run_id:
        run_id = str(uuid.uuid4())

    # Build difficulty map from task_id prefix if not provided
    if difficulty_map is None:
        difficulty_map = _infer_difficulty_map(results)

    # Group by config
    by_config: dict[ConfigID, list[TaskResult]] = defaultdict(list)
    for r in results:
        by_config[r.config_id].append(r)

    # Get unique task count
    task_ids = {r.task_id for r in results}
    task_count = len(task_ids)

    # Compute baseline pass rate
    baseline_results = by_config.get(ConfigID.A, [])
    baseline_rate = (
        sum(1 for r in baseline_results if r.passed) / len(baseline_results)
        if baseline_results
        else 0.0
    )

    # Config labels
    from bench.config import CONFIGS

    config_summaries: list[ConfigSummary] = []
    for cid in ConfigID:
        config_results = by_config.get(cid, [])
        if not config_results:
            continue
        label = CONFIGS[cid].label
        summary = compute_config_summary(
            config_id=cid,
            label=label,
            results=config_results,
            baseline_pass_rate=baseline_rate,
            difficulty_map=difficulty_map,
        )
        config_summaries.append(summary)

    # Identify best config
    best = max(config_summaries, key=lambda s: s.pass_rate) if config_summaries else None
    best_config = best.config_id if best else ConfigID.A

    # Best single change (biggest positive delta, excluding A itself)
    non_baseline = [s for s in config_summaries if s.config_id != ConfigID.A]
    best_change = (
        max(non_baseline, key=lambda s: s.delta_vs_baseline) if non_baseline else None
    )
    best_single_change = best_change.config_id if best_change else ConfigID.A

    # Hashline impact (B vs A)
    b_summary = next((s for s in config_summaries if s.config_id == ConfigID.B), None)
    hashline_impact = b_summary.pass_rate - baseline_rate if b_summary else 0.0

    # Full stack impact (E vs A)
    e_summary = next((s for s in config_summaries if s.config_id == ConfigID.E), None)
    full_stack_impact = e_summary.pass_rate - baseline_rate if e_summary else 0.0

    return BenchmarkSummary(
        run_id=run_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        model=model,
        task_count=task_count,
        configs=config_summaries,
        raw_results=results,
        best_config=best_config,
        best_single_change=best_single_change,
        hashline_impact=hashline_impact,
        full_stack_impact=full_stack_impact,
    )


def compute_config_summary(
    config_id: ConfigID,
    label: str,
    results: list[TaskResult],
    baseline_pass_rate: float,
    difficulty_map: dict[str, Difficulty] | None = None,
) -> ConfigSummary:
    """Compute summary for a single config from its TaskResults."""
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    rate = passed / total if total > 0 else 0.0
    avg_dur = sum(r.duration_seconds for r in results) / total if total > 0 else 0.0
    errors = sum(1 for r in results if r.error_message and "dry_run" not in r.error_message)

    diff_rates: dict[Difficulty, float] = {}
    if difficulty_map:
        diff_rates = pass_rate_by_difficulty(results, difficulty_map)

    return ConfigSummary(
        config_id=config_id,
        label=label,
        total_tasks=total,
        tasks_passed=passed,
        pass_rate=rate,
        pass_rate_by_difficulty=diff_rates,
        avg_duration_seconds=avg_dur,
        total_errors=errors,
        delta_vs_baseline=rate - baseline_pass_rate,
    )


def pass_rate_by_difficulty(
    results: list[TaskResult],
    difficulty_map: dict[str, Difficulty],
) -> dict[Difficulty, float]:
    """Compute pass rate broken down by difficulty tier."""
    by_diff: dict[Difficulty, list[TaskResult]] = defaultdict(list)
    for r in results:
        diff = difficulty_map.get(r.task_id)
        if diff:
            by_diff[diff].append(r)

    rates: dict[Difficulty, float] = {}
    for diff in Difficulty:
        diff_results = by_diff.get(diff, [])
        if diff_results:
            rates[diff] = sum(1 for r in diff_results if r.passed) / len(diff_results)
        else:
            rates[diff] = 0.0
    return rates


def _infer_difficulty_map(results: list[TaskResult]) -> dict[str, Difficulty]:
    """Infer difficulty from task_id numbering: 001-010=easy, 011-020=medium, 021-030=hard."""
    dmap: dict[str, Difficulty] = {}
    for r in results:
        # Extract leading number
        parts = r.task_id.split("_", 1)
        try:
            num = int(parts[0])
        except ValueError:
            continue
        if num <= 10:
            dmap[r.task_id] = Difficulty.EASY
        elif num <= 20:
            dmap[r.task_id] = Difficulty.MEDIUM
        else:
            dmap[r.task_id] = Difficulty.HARD
    return dmap
