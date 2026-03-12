"""Benchmark runner — orchestrates task×config execution."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from bench.config import AblationConfig, generate_claw_forge_yaml
from bench.models import TaskMeta, TaskResult


def run_single(
    task: TaskMeta,
    config: AblationConfig,
    base_yaml: Path,
    run_dir: Path,
    timeout_seconds: int = 300,
    model: str = "claude-sonnet-4-6",
    claw_forge_bin: str = "claw-forge",
    dry_run: bool = False,
) -> TaskResult:
    """Execute one (task, config) pair and return the result.

    Steps:
    1. Create isolated workdir: run_dir / task.task_id / config.id
    2. Copy task template files into workdir
    3. Generate config-specific claw-forge.yaml
    4. Invoke claw-forge run with subprocess
    5. Run pytest on the tests
    6. Return TaskResult
    """
    workdir = run_dir / task.task_id / f"config-{config.id}"
    workdir.mkdir(parents=True, exist_ok=True)

    # Step 1: Copy task template
    _copy_task_template(task, workdir)

    # Step 2: Generate config-specific yaml
    config_yaml = workdir / "claw-forge.yaml"
    generate_claw_forge_yaml(str(base_yaml), config, str(config_yaml))

    if dry_run:
        return TaskResult(
            task_id=task.task_id,
            config_id=config.id,
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

    # Step 3: Run claw-forge
    cf_exit, cf_stdout, cf_stderr, cf_duration = _run_claw_forge(
        workdir=workdir,
        config_yaml=config_yaml,
        model=model,
        timeout_seconds=timeout_seconds,
        claw_forge_bin=claw_forge_bin,
    )

    # Step 4: Run pytest
    pt_exit, pt_total, pt_passed, pt_failed = _run_pytest(workdir)

    error_msg = ""
    if cf_exit != 0:
        error_msg = f"claw-forge exit {cf_exit}: {cf_stderr[:500]}"
    elif pt_exit != 0 and pt_failed == 0 and pt_total == 0:
        error_msg = "pytest could not collect tests"

    return TaskResult(
        task_id=task.task_id,
        config_id=config.id,
        passed=(pt_exit == 0 and pt_failed == 0 and pt_total > 0),
        tests_total=pt_total,
        tests_passed=pt_passed,
        tests_failed=pt_failed,
        duration_seconds=cf_duration,
        exit_code=cf_exit,
        pytest_exit_code=pt_exit,
        error_message=error_msg,
        timestamp=datetime.now(timezone.utc).isoformat(),
        workdir=str(workdir),
    )


def run_all(
    tasks: list[TaskMeta],
    configs: list[AblationConfig],
    base_yaml: Path,
    run_dir: Path,
    results_file: Path,
    timeout_seconds: int = 300,
    model: str = "claude-sonnet-4-6",
    concurrency: int = 1,
    keep_all: bool = False,
    dry_run: bool = False,
) -> list[TaskResult]:
    """Run all tasks × all configs sequentially.

    Appends each TaskResult as JSONL to results_file as it completes.
    Returns the full list when done.
    """
    results: list[TaskResult] = []

    # Load existing results for resume support
    completed: set[tuple[str, str]] = set()
    if results_file.exists():
        for line in results_file.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    data = json.loads(line)
                    completed.add((data["task_id"], data["config_id"]))
                except (json.JSONDecodeError, KeyError):
                    pass

    results_file.parent.mkdir(parents=True, exist_ok=True)

    for task in tasks:
        for config in configs:
            if (task.task_id, config.id) in completed:
                continue

            result = run_single(
                task=task,
                config=config,
                base_yaml=base_yaml,
                run_dir=run_dir,
                timeout_seconds=timeout_seconds,
                model=model,
                dry_run=dry_run,
            )
            results.append(result)

            # Append to JSONL
            with open(results_file, "a") as f:
                f.write(result.to_jsonl() + "\n")

            # Cleanup passing workdirs unless --keep-all
            if not keep_all and result.passed and not dry_run:
                workdir = Path(result.workdir)
                if workdir.exists():
                    shutil.rmtree(workdir)

    return results


def _copy_task_template(task: TaskMeta, dest: Path) -> None:
    """Copy task template directory to dest, preserving structure."""
    src_dir = task.task_dir
    for item in src_dir.rglob("*"):
        if item.name == "_solution.py":
            continue  # Skip solution files
        rel = item.relative_to(src_dir)
        target = dest / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def _run_claw_forge(
    workdir: Path,
    config_yaml: Path,
    model: str,
    timeout_seconds: int,
    claw_forge_bin: str = "claw-forge",
) -> tuple[int, str, str, float]:
    """Invoke claw-forge run as a subprocess.

    Returns: (exit_code, stdout, stderr, duration_seconds)
    """
    cmd = [
        claw_forge_bin,
        "run",
        "--project",
        str(workdir),
        "--config",
        str(config_yaml),
        "--model",
        model,
        "--concurrency",
        "1",
    ]

    start = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=str(workdir),
        )
        duration = time.monotonic() - start
        return proc.returncode, proc.stdout, proc.stderr, duration
    except subprocess.TimeoutExpired:
        duration = time.monotonic() - start
        return -1, "", "timeout", duration
    except FileNotFoundError:
        duration = time.monotonic() - start
        return -2, "", f"claw-forge binary not found: {claw_forge_bin}", duration


def _run_pytest(workdir: Path, timeout_seconds: int = 60) -> tuple[int, int, int, int]:
    """Run pytest on workdir/tests/ and parse results.

    Returns: (exit_code, total, passed, failed)
    """
    test_dir = workdir / "tests"
    if not test_dir.exists():
        return 1, 0, 0, 0

    try:
        proc = subprocess.run(
            ["python", "-m", "pytest", str(test_dir), "-v", "--tb=short", "--no-header"],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=str(workdir),
            env={
                **__import__("os").environ,
                "PYTHONPATH": str(workdir / "src") + ":" + str(workdir),
            },
        )
    except subprocess.TimeoutExpired:
        return -1, 0, 0, 0

    # Parse pytest output for pass/fail counts
    output = proc.stdout + proc.stderr
    total = 0
    passed = 0
    failed = 0

    # Look for summary line like "5 passed, 2 failed" or "5 passed"
    summary_match = re.search(
        r"(\d+)\s+passed(?:.*?(\d+)\s+failed)?", output
    )
    if summary_match:
        passed = int(summary_match.group(1))
        failed = int(summary_match.group(2) or 0)
        total = passed + failed
    else:
        # Try to count from "PASSED" / "FAILED" lines
        passed = len(re.findall(r"PASSED", output))
        failed = len(re.findall(r"FAILED", output))
        total = passed + failed

    return proc.returncode, total, passed, failed
