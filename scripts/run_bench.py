"""CLI entry point for the benchmark suite."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from bench.config import get_config
from bench.models import ConfigID, Difficulty
from bench.report import append_to_results, write_jsonl_backup
from bench.runner import run_all
from bench.score import compute_summary, load_results
from bench.task_registry import discover_tasks


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="claw-forge ablation benchmark suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-6",
        help="Model for claw-forge run (default: claude-sonnet-4-6)",
    )
    parser.add_argument(
        "--configs",
        default="A,B,C,D,E",
        help="Comma-separated config IDs: A,B,C,D,E (default: all)",
    )
    parser.add_argument(
        "--tasks",
        default="all",
        help='Task filter: "all", "easy", "medium", "hard", or comma-separated task IDs',
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Seconds per (task, config) run (default: 300)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="Max parallel runs (default: 1)",
    )
    parser.add_argument(
        "--results-md",
        default="/tmp/claw-forge-hashline-pbr/docs/benchmarks/results.md",
        help="Path to results.md to append to",
    )
    parser.add_argument(
        "--run-dir",
        default="/tmp/claw-forge-bench-runs",
        help="Root for isolated workdirs (default: /tmp/claw-forge-bench-runs)",
    )
    parser.add_argument(
        "--keep-all",
        action="store_true",
        help="Keep all workdirs (default: clean passing runs)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List tasks and configs without executing",
    )
    parser.add_argument(
        "--config",
        dest="config_alias",
        help="Shorthand: single config ID (e.g. --config A)",
    )
    return parser.parse_args(argv)


def main() -> int:
    """Entry point."""
    args = parse_args()

    # Resolve config alias
    if args.config_alias:
        args.configs = args.config_alias

    # Parse config IDs
    config_ids = [ConfigID(c.strip().upper()) for c in args.configs.split(",")]
    configs = [get_config(cid) for cid in config_ids]

    # Discover tasks
    tasks_dir = PROJECT_ROOT / "tasks"
    all_tasks = discover_tasks(tasks_dir)

    # Filter tasks
    task_filter = args.tasks.lower()
    if task_filter == "all":
        tasks = all_tasks
    elif task_filter in ("easy", "medium", "hard"):
        difficulty = Difficulty(task_filter)
        tasks = [t for t in all_tasks if t.difficulty == difficulty]
    else:
        # Comma-separated task IDs
        task_ids = {tid.strip() for tid in args.tasks.split(",")}
        tasks = [t for t in all_tasks if t.task_id in task_ids]

    if not tasks:
        print("ERROR: No tasks matched the filter.", file=sys.stderr)
        return 1

    # Dry run: just print the plan
    if args.dry_run:
        print("=== claw-forge Ablation Benchmark (DRY RUN) ===")
        print(f"Model: {args.model}")
        print(f"Configs: {', '.join(str(c.id) for c in configs)}")
        print(f"Tasks: {len(tasks)} ({task_filter})")
        print(f"Timeout: {args.timeout}s per run")
        print(f"Total runs: {len(tasks) * len(configs)}")
        print()
        print("Tasks:")
        for t in tasks:
            print(f"  [{t.difficulty.value:6s}] {t.task_id}: {t.description}")
        print()
        print("Configs:")
        for c in configs:
            print(f"  {c.id}: {c.label}")
            print(f"       edit_mode={c.edit_mode}, loop_detect={c.loop_detect_threshold}, "
                  f"verify={c.verify_on_exit}")
        return 0

    # Run benchmark
    run_dir = Path(args.run_dir)
    results_file = run_dir / "results.jsonl"

    print("=== claw-forge Ablation Benchmark ===")
    print(f"Model: {args.model}")
    print(f"Configs: {', '.join(str(c.id) for c in configs)}")
    print(f"Tasks: {len(tasks)}")
    print(f"Total runs: {len(tasks) * len(configs)}")
    print()

    results = run_all(
        tasks=tasks,
        configs=configs,
        base_yaml=PROJECT_ROOT / "configs" / "base.yaml",
        run_dir=run_dir,
        results_file=results_file,
        timeout_seconds=args.timeout,
        model=args.model,
        concurrency=args.concurrency,
        keep_all=args.keep_all,
    )

    if not results:
        print("No new results (all tasks already completed?)")
        # Load existing results
        if results_file.exists():
            results = load_results(results_file)
        else:
            return 0

    # Build difficulty map
    difficulty_map = {t.task_id: t.difficulty for t in all_tasks}

    # Compute summary
    summary = compute_summary(
        results=results,
        model=args.model,
        difficulty_map=difficulty_map,
    )

    # Write results
    results_md = Path(args.results_md)
    append_to_results(summary, results_md)
    print(f"\nResults appended to: {results_md}")

    # Write JSONL backup
    backup = run_dir / f"results-{summary.run_id}.jsonl"
    write_jsonl_backup(summary, backup)
    print(f"JSONL backup: {backup}")

    # Print summary
    print("\n=== Summary ===")
    for cs in summary.configs:
        delta = f"+{cs.delta_vs_baseline:.0%}" if cs.config_id != "A" else "baseline"
        print(f"  {cs.config_id}: {cs.pass_rate:.0%} ({delta}) — {cs.label}")
    print(f"\nBest config: {summary.best_config}")
    print(f"Hashline impact: +{summary.hashline_impact:.0%}")
    print(f"Full-stack impact: +{summary.full_stack_impact:.0%}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
