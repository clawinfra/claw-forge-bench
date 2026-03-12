"""Direct Claude Agent SDK benchmark runner.

Bypasses claw-forge CLI entirely — calls the Claude Agent SDK query()
function directly with claw-forge middleware hooks per ablation config.

Usage:
    uv run python scripts/run_bench_direct.py --configs A,B,C,D,E --concurrency 5
    uv run python scripts/run_bench_direct.py --configs A --tasks 001_fizzbuzz --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# claw-forge hooks available from the PBR workspace
sys.path.insert(0, "/tmp/claw-forge-hashline-pbr")

from claude_agent_sdk import ClaudeAgentOptions, query
from claw_forge.agent.hooks import get_default_hooks

from bench.config import get_config
from bench.models import ConfigID, Difficulty, TaskMeta, TaskResult
from bench.task_registry import discover_tasks

# ── Constants ──────────────────────────────────────────────────────────────────

DEFAULT_MODEL = "claude-opus-4-6"
DEFAULT_TIMEOUT = 180  # seconds per (task, config) run
DEFAULT_CONCURRENCY = 3
RESULTS_FILE = PROJECT_ROOT / "runs" / "results.jsonl"
RUN_DIR = Path("/tmp/claw-forge-bench-runs-direct")

# ── Hook builders per config ──────────────────────────────────────────────────


def build_hooks(config_id: str) -> dict | None:
    """Return SDK hooks dict for the given config, or None for baseline."""
    if config_id == "A":
        # Baseline: no middleware hooks at all
        return None
    elif config_id == "B":
        return get_default_hooks(edit_mode="hashline")
    elif config_id == "C":
        return get_default_hooks(loop_detect_threshold=5)
    elif config_id == "D":
        return get_default_hooks(verify_on_exit=True)
    elif config_id == "E":
        return get_default_hooks(
            edit_mode="hashline",
            loop_detect_threshold=5,
            verify_on_exit=True,
        )
    else:
        raise ValueError(f"Unknown config: {config_id}")


def build_system_prompt(config_id: str, claude_md: str) -> str | None:
    """Return system prompt with hashline fragment if needed."""
    config = get_config(ConfigID(config_id))
    parts: list[str] = []

    if config.edit_mode == "hashline":
        try:
            from claw_forge.hashline import build_system_prompt_fragment

            parts.append(build_system_prompt_fragment())
        except ImportError:
            pass

    # CLAUDE.md is the task prompt — injected as user prompt, not system prompt
    # Only return hashline system prompt if needed
    return "\n\n".join(parts) if parts else None


# ── Copy task template ────────────────────────────────────────────────────────


def copy_task_template(task: TaskMeta, dest: Path) -> None:
    """Copy task src/ and tests/ to isolated workdir."""
    src_dir = task.task_dir
    for item in src_dir.rglob("*"):
        if item.name == "_solution.py":
            continue
        if item.name == "app_spec.xml":
            continue
        rel = item.relative_to(src_dir)
        target = dest / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


# ── Run pytest ────────────────────────────────────────────────────────────────


def run_pytest(workdir: Path, timeout_seconds: int = 60) -> tuple[int, int, int, int]:
    """Run pytest on workdir/tests/ and parse results.

    Returns: (exit_code, total, passed, failed)
    """
    test_dir = workdir / "tests"
    if not test_dir.exists():
        return 1, 0, 0, 0

    env = {**os.environ, "PYTHONPATH": f"{workdir / 'src'}:{workdir}"}
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_dir), "-v", "--tb=short", "--no-header"],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=str(workdir),
            env=env,
        )
    except subprocess.TimeoutExpired:
        return -1, 0, 0, 0

    output = proc.stdout + proc.stderr
    total = passed = failed = 0

    summary_match = re.search(r"(\d+)\s+passed(?:.*?(\d+)\s+failed)?", output)
    if summary_match:
        passed = int(summary_match.group(1))
        failed = int(summary_match.group(2) or 0)
        total = passed + failed
    else:
        passed = len(re.findall(r"PASSED", output))
        failed = len(re.findall(r"FAILED", output))
        total = passed + failed

    return proc.returncode, total, passed, failed


# ── Run single task ──────────────────────────────────────────────────────────


async def run_single(
    task: TaskMeta,
    config_id: str,
    run_dir: Path,
    model: str,
    timeout_seconds: int,
    dry_run: bool = False,
) -> TaskResult:
    """Execute one (task, config) pair via Claude Agent SDK."""
    workdir = run_dir / task.task_id / f"config-{config_id}"
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True, exist_ok=True)

    # Copy task template
    copy_task_template(task, workdir)

    if dry_run:
        return TaskResult(
            task_id=task.task_id,
            config_id=ConfigID(config_id),
            passed=False,
            tests_total=task.expected_test_count,
            tests_passed=0,
            tests_failed=0,
            duration_seconds=0.0,
            exit_code=-1,
            pytest_exit_code=-1,
            error_message="dry_run",
            timestamp=datetime.now(timezone.utc).isoformat(),
            workdir=str(workdir),
        )

    # Read CLAUDE.md as the task prompt
    claude_md_path = task.task_dir / "CLAUDE.md"
    if claude_md_path.exists():
        prompt = claude_md_path.read_text()
    else:
        prompt = (
            f"Fix the bug in src/{task.source_file} so all tests in tests/ pass. "
            "Make minimal changes. Do NOT modify test files."
        )

    # Build hooks and system prompt
    hooks = build_hooks(config_id)
    system_prompt = build_system_prompt(config_id, prompt)

    # Build env with OAuth token
    env: dict[str, str] = {}
    oauth_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", "")
    if oauth_token:
        env["CLAUDE_CODE_OAUTH_TOKEN"] = oauth_token

    # Build SDK options
    options = ClaudeAgentOptions(
        model=model,
        max_turns=30,
        permission_mode="bypassPermissions",
        cwd=str(workdir),
        system_prompt=system_prompt,
        env=env,
        hooks=hooks,
    )

    # Run agent with timeout
    start = time.monotonic()
    exit_code = 0
    error_message = ""

    try:
        async with asyncio.timeout(timeout_seconds):
            async for message in query(prompt=prompt, options=options):
                # Just consume messages — the agent edits files in workdir
                msg_type = message.__class__.__name__
                if msg_type == "ResultMessage":
                    pass  # Agent completed
    except TimeoutError:
        exit_code = -1
        error_message = f"agent timeout after {timeout_seconds}s"
    except Exception as exc:
        exit_code = -2
        error_message = f"agent error: {exc!s}"[:500]

    duration = time.monotonic() - start

    # Run pytest
    pt_exit, pt_total, pt_passed, pt_failed = run_pytest(workdir)

    if not error_message and pt_exit != 0 and pt_failed == 0 and pt_total == 0:
        error_message = "pytest could not collect tests"

    return TaskResult(
        task_id=task.task_id,
        config_id=ConfigID(config_id),
        passed=(pt_exit == 0 and pt_failed == 0 and pt_total > 0),
        tests_total=pt_total,
        tests_passed=pt_passed,
        tests_failed=pt_failed,
        duration_seconds=round(duration, 2),
        exit_code=exit_code,
        pytest_exit_code=pt_exit,
        error_message=error_message,
        timestamp=datetime.now(timezone.utc).isoformat(),
        workdir=str(workdir),
    )


# ── Load completed pairs ─────────────────────────────────────────────────────


def load_completed(results_file: Path) -> set[tuple[str, str]]:
    """Load (task_id, config_id) pairs from existing results JSONL."""
    completed: set[tuple[str, str]] = set()
    if not results_file.exists():
        return completed
    for line in results_file.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            completed.add((data["task_id"], data["config_id"]))
        except (json.JSONDecodeError, KeyError):
            pass
    return completed


# ── Main runner ──────────────────────────────────────────────────────────────


async def run_all(
    tasks: list[TaskMeta],
    config_ids: list[str],
    run_dir: Path,
    results_file: Path,
    model: str,
    timeout_seconds: int,
    concurrency: int,
    dry_run: bool = False,
) -> list[TaskResult]:
    """Run all (task, config) pairs with concurrency control."""
    completed = load_completed(results_file)
    results_file.parent.mkdir(parents=True, exist_ok=True)

    # Build work items
    work: list[tuple[TaskMeta, str]] = []
    for task in tasks:
        for cid in config_ids:
            if (task.task_id, cid) in completed:
                continue
            work.append((task, cid))

    if not work:
        print("No new (task, config) pairs to run — all completed.")
        return []

    print(f"Running {len(work)} pairs (skipping {len(completed)} already completed)")

    semaphore = asyncio.Semaphore(concurrency)
    results: list[TaskResult] = []
    lock = asyncio.Lock()

    async def run_with_sem(task: TaskMeta, cid: str) -> TaskResult | None:
        async with semaphore:
            tag = f"[{task.task_id}/{cid}]"
            print(f"{tag} starting...", flush=True)
            try:
                result = await run_single(
                    task=task,
                    config_id=cid,
                    run_dir=run_dir,
                    model=model,
                    timeout_seconds=timeout_seconds,
                    dry_run=dry_run,
                )
            except Exception as exc:
                print(f"{tag} CRASH: {exc!s}", flush=True)
                result = TaskResult(
                    task_id=task.task_id,
                    config_id=ConfigID(cid),
                    passed=False,
                    tests_total=0,
                    tests_passed=0,
                    tests_failed=0,
                    duration_seconds=0.0,
                    exit_code=-3,
                    pytest_exit_code=-1,
                    error_message=f"runner crash: {exc!s}"[:500],
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    workdir="",
                )
            status = "PASS" if result.passed else "FAIL"
            print(
                f"{tag} {status} ({result.tests_passed}/{result.tests_total} "
                f"tests, {result.duration_seconds:.1f}s)",
                flush=True,
            )
            # Append to JSONL atomically
            async with lock:
                with open(results_file, "a") as f:
                    f.write(result.to_jsonl() + "\n")
                results.append(result)
            return result

    # Launch all tasks concurrently (semaphore limits parallelism)
    tasks_coros = [run_with_sem(task, cid) for task, cid in work]
    await asyncio.gather(*tasks_coros, return_exceptions=True)

    return results


# ── CLI ──────────────────────────────────────────────────────────────────────


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Direct Claude Agent SDK benchmark runner (bypasses claw-forge CLI)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Model to use (default: {DEFAULT_MODEL})",
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
        default=DEFAULT_TIMEOUT,
        help=f"Seconds per (task, config) run (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help=f"Max parallel runs (default: {DEFAULT_CONCURRENCY})",
    )
    parser.add_argument(
        "--run-dir",
        default=str(RUN_DIR),
        help=f"Root for isolated workdirs (default: {RUN_DIR})",
    )
    parser.add_argument(
        "--results-file",
        default=str(RESULTS_FILE),
        help=f"Results JSONL file (default: {RESULTS_FILE})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List tasks and configs without executing",
    )
    return parser.parse_args(argv)


def main() -> int:
    """Entry point."""
    args = parse_args()

    # Parse config IDs
    config_ids = [c.strip().upper() for c in args.configs.split(",")]
    for cid in config_ids:
        if cid not in ("A", "B", "C", "D", "E"):
            print(f"ERROR: Invalid config ID: {cid}", file=sys.stderr)
            return 1

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
        task_ids = {tid.strip() for tid in args.tasks.split(",")}
        tasks = [t for t in all_tasks if t.task_id in task_ids]

    if not tasks:
        print("ERROR: No tasks matched the filter.", file=sys.stderr)
        return 1

    # Dry-run info
    if args.dry_run:
        configs_display = [get_config(ConfigID(c)) for c in config_ids]
        completed = load_completed(Path(args.results_file))
        total_pairs = len(tasks) * len(config_ids)
        skip_count = sum(1 for t in tasks for c in config_ids if (t.task_id, c) in completed)

        print("=== Direct Claude Agent SDK Benchmark (DRY RUN) ===")
        print(f"Model: {args.model}")
        print(f"Configs: {', '.join(config_ids)}")
        print(f"Tasks: {len(tasks)}")
        remaining = total_pairs - skip_count
        print(f"Total pairs: {total_pairs} ({skip_count} completed, {remaining} remaining)")
        print(f"Timeout: {args.timeout}s | Concurrency: {args.concurrency}")
        print()
        print("Tasks:")
        for t in tasks:
            print(f"  [{t.difficulty.value:6s}] {t.task_id}: {t.description}")
        print()
        print("Configs:")
        for c in configs_display:
            print(f"  {c.id}: {c.label}")
            print(
                f"       edit_mode={c.edit_mode}, loop_detect={c.loop_detect_threshold}, "
                f"verify={c.verify_on_exit}"
            )
        return 0

    # Check OAuth token
    if not os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        print("ERROR: CLAUDE_CODE_OAUTH_TOKEN not set in environment.", file=sys.stderr)
        return 1

    print("=== Direct Claude Agent SDK Benchmark ===")
    print(f"Model: {args.model}")
    print(f"Configs: {', '.join(config_ids)}")
    print(f"Tasks: {len(tasks)}")
    print(f"Timeout: {args.timeout}s | Concurrency: {args.concurrency}")
    print()

    results = asyncio.run(
        run_all(
            tasks=tasks,
            config_ids=config_ids,
            run_dir=Path(args.run_dir),
            results_file=Path(args.results_file),
            model=args.model,
            timeout_seconds=args.timeout,
            concurrency=args.concurrency,
        )
    )

    if not results:
        return 0

    # Summary
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"\n=== Summary: {passed}/{total} passed ({passed / total:.0%}) ===")
    for r in results:
        status = "✅" if r.passed else "❌"
        dur = f"{r.duration_seconds:.1f}s"
        tests = f"{r.tests_passed}/{r.tests_total}"
        print(f"  {status} {r.task_id}/{r.config_id} — {tests} tests, {dur}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
