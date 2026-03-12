# PLAN: claw-forge Ablation Benchmark Suite

**Project:** `~/projects/claw-forge-bench`  
**Purpose:** Self-contained local benchmark for ablation-testing claw-forge's three middleware features (hashline, loop-detect, verify-on-exit) across 5 configurations.  
**Results target:** `/tmp/claw-forge-hashline-pbr/docs/benchmarks/results.md`  
**Git identity:** Alex Chen <alex.chen31337@gmail.com>  

---

## 1. Architecture Overview + Data Flow

### Core Idea

30 Python coding tasks (broken/incomplete files + test suites) are fed to `claw-forge run` under 5 different ablation configurations. A scorer measures test pass rate per config. Results are written as a Markdown table.

Each task is a **self-contained mini-project** structured as a valid claw-forge target:
- A Python source file with a deliberate bug or missing implementation
- A pytest test file that passes when (and only when) the source is correctly fixed
- A minimal `app_spec.xml` with a single feature pointing at the file

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        bench.py (runner)                             │
│                                                                      │
│  for task in 30_tasks:                                              │
│    for config in [A, B, C, D, E]:                                   │
│      1. Copy task template → isolated workdir                       │
│      2. Write claw-forge.yaml with config-specific flags            │
│      3. Invoke: claw-forge run --project <workdir> [flags]          │
│      4. Run: pytest <workdir>/tests/ → capture exit code            │
│      5. Record: (task_id, config_id, pass/fail, duration, cost)     │
│                                                                      │
│  Pass results to scorer                                             │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        score.py (scorer)                             │
│                                                                      │
│  Input:  results.jsonl (one JSON line per task×config run)          │
│  Output: BenchmarkSummary with per-config pass rates + deltas       │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     report.py (results writer)                       │
│                                                                      │
│  Reads BenchmarkSummary                                             │
│  Renders Markdown table                                             │
│  Appends ABOVE the RESULTS_MARKER line in:                          │
│    /tmp/claw-forge-hashline-pbr/docs/benchmarks/results.md          │
└──────────────────────────────────────────────────────────────────────┘
```

### Isolation Model

Each (task, config) run gets its own temporary directory:
```
/tmp/claw-forge-bench-runs/
  task-001-easy-fizzbuzz/
    config-A/          ← pristine copy of task, claw-forge runs here
    config-B/
    ...
```

After `claw-forge run` completes (or times out), the scorer runs `pytest` against the workdir's test suite. The workdir is kept on failure for debugging but cleaned up on success (configurable via `--keep-all`).

---

## 2. File Structure with Exact Function Signatures

```
~/projects/claw-forge-bench/
├── PLAN.md                          # This file
├── README.md                        # Usage instructions
├── pyproject.toml                   # uv project definition
├── configs/
│   ├── base.yaml                    # Shared claw-forge.yaml template
│   ├── config_a.yaml                # A: baseline str_replace only
│   ├── config_b.yaml                # B: hashline only
│   ├── config_c.yaml                # C: str_replace + loop-detect
│   ├── config_d.yaml                # D: str_replace + verify-on-exit
│   └── config_e.yaml                # E: hashline + loop-detect + verify-on-exit
├── tasks/
│   ├── easy/
│   │   ├── 001_fizzbuzz/
│   │   │   ├── src/fizzbuzz.py      # Broken implementation
│   │   │   ├── tests/test_fizzbuzz.py  # Passing = correct fix
│   │   │   ├── app_spec.xml         # Single-feature spec
│   │   │   └── CLAUDE.md            # Task-specific agent instructions
│   │   ├── 002_palindrome/
│   │   │   └── ...
│   │   └── ... (10 tasks total)
│   ├── medium/
│   │   ├── 011_lru_cache/
│   │   │   └── ...
│   │   └── ... (10 tasks total)
│   └── hard/
│       ├── 021_interpreter/
│       │   └── ...
│       └── ... (10 tasks total)
├── bench/
│   ├── __init__.py
│   ├── runner.py                    # Orchestrates task×config execution
│   ├── score.py                     # Computes pass rates and statistics
│   ├── report.py                    # Writes Markdown results table
│   ├── config.py                    # Ablation config definitions
│   ├── models.py                    # Data models (TaskResult, BenchmarkSummary)
│   └── task_registry.py             # Discovers and validates tasks
├── scripts/
│   ├── run_bench.py                 # CLI entry point
│   ├── validate_tasks.py            # Pre-flight: verify all tasks are solvable
│   └── gen_task_template.py         # Helper to scaffold a new task
└── tests/
    ├── test_score.py                # Unit tests for scorer
    ├── test_report.py               # Unit tests for report writer
    ├── test_config.py               # Unit tests for config generation
    └── test_task_registry.py        # Unit tests for task discovery
```

### Module: `bench/models.py`

```python
"""Data models for benchmark results."""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


class Difficulty(enum.StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ConfigID(enum.StrEnum):
    A = "A"  # baseline: str_replace, no loop-detect, no verify-on-exit
    B = "B"  # hashline, no loop-detect, no verify-on-exit
    C = "C"  # str_replace + loop-detect (threshold=5)
    D = "D"  # str_replace + verify-on-exit
    E = "E"  # hashline + loop-detect + verify-on-exit


@dataclass
class AblationConfig:
    """Maps a ConfigID to concrete claw-forge CLI flags."""
    id: ConfigID
    label: str
    edit_mode: str                   # "str_replace" | "hashline"
    loop_detect_threshold: int       # 0 = disabled, 5 = default
    verify_on_exit: bool

    def to_cli_flags(self) -> list[str]:
        """Return CLI flags list for claw-forge run."""
        ...

    def to_yaml_overrides(self) -> dict[str, object]:
        """Return dict to merge into base claw-forge.yaml."""
        ...


@dataclass
class TaskMeta:
    """Metadata for a single benchmark task."""
    task_id: str                     # e.g. "001_fizzbuzz"
    difficulty: Difficulty
    description: str
    source_file: str                 # relative path within task dir
    test_file: str                   # relative path within task dir
    task_dir: Path                   # absolute path to task template
    expected_test_count: int         # number of test cases in test file


@dataclass
class TaskResult:
    """Result of running one (task, config) pair."""
    task_id: str
    config_id: ConfigID
    passed: bool                     # all tests passed
    tests_total: int
    tests_passed: int
    tests_failed: int
    duration_seconds: float
    exit_code: int                   # claw-forge exit code
    pytest_exit_code: int            # pytest exit code
    error_message: str = ""          # if claw-forge or pytest errored
    timestamp: str = ""              # ISO 8601
    workdir: str = ""                # path to run directory

    def to_jsonl(self) -> str:
        """Serialize to a single JSON line."""
        ...

    @classmethod
    def from_jsonl(cls, line: str) -> TaskResult:
        """Deserialize from a single JSON line."""
        ...


@dataclass
class ConfigSummary:
    """Aggregated results for one ablation config."""
    config_id: ConfigID
    label: str
    total_tasks: int
    tasks_passed: int
    pass_rate: float                 # 0.0 – 1.0
    pass_rate_by_difficulty: dict[Difficulty, float]
    avg_duration_seconds: float
    total_errors: int
    delta_vs_baseline: float         # pass_rate - baseline pass_rate


@dataclass
class BenchmarkSummary:
    """Complete benchmark results across all configs."""
    run_id: str                      # UUID
    timestamp: str                   # ISO 8601
    model: str                       # model used for the run
    task_count: int
    configs: list[ConfigSummary]
    raw_results: list[TaskResult]
    best_config: ConfigID
    best_single_change: ConfigID     # biggest delta vs baseline
    hashline_impact: float           # B.pass_rate - A.pass_rate
    full_stack_impact: float         # E.pass_rate - A.pass_rate
```

### Module: `bench/config.py`

```python
"""Ablation configuration definitions."""
from __future__ import annotations

from bench.models import AblationConfig, ConfigID


# ── The 5 Ablation Configs ──────────────────────────────────────────────

CONFIGS: dict[ConfigID, AblationConfig] = {
    ConfigID.A: AblationConfig(
        id=ConfigID.A,
        label="baseline (str_replace only)",
        edit_mode="str_replace",
        loop_detect_threshold=0,      # disabled
        verify_on_exit=False,
    ),
    ConfigID.B: AblationConfig(
        id=ConfigID.B,
        label="hashline",
        edit_mode="hashline",
        loop_detect_threshold=0,      # disabled
        verify_on_exit=False,
    ),
    ConfigID.C: AblationConfig(
        id=ConfigID.C,
        label="str_replace + loop-detect",
        edit_mode="str_replace",
        loop_detect_threshold=5,      # default threshold
        verify_on_exit=False,
    ),
    ConfigID.D: AblationConfig(
        id=ConfigID.D,
        label="str_replace + verify-on-exit",
        edit_mode="str_replace",
        loop_detect_threshold=0,      # disabled
        verify_on_exit=True,
    ),
    ConfigID.E: AblationConfig(
        id=ConfigID.E,
        label="hashline + loop-detect + verify-on-exit",
        edit_mode="hashline",
        loop_detect_threshold=5,
        verify_on_exit=True,
    ),
}


def get_config(config_id: ConfigID) -> AblationConfig:
    """Return the AblationConfig for the given ID."""
    ...


def all_configs() -> list[AblationConfig]:
    """Return all 5 configs in order A→E."""
    ...


def generate_claw_forge_yaml(
    base_yaml_path: str,
    config: AblationConfig,
    output_path: str,
) -> None:
    """Merge ablation overrides into base.yaml and write to output_path.

    The base.yaml contains shared provider pool config.
    The config overrides agent.edit_mode, agent.loop_detect_threshold,
    and agent.verify_on_exit.
    """
    ...
```

### Module: `bench/task_registry.py`

```python
"""Discover and validate benchmark tasks from the tasks/ directory."""
from __future__ import annotations

from pathlib import Path

from bench.models import Difficulty, TaskMeta


def discover_tasks(tasks_dir: Path) -> list[TaskMeta]:
    """Walk tasks/{easy,medium,hard}/ and return sorted TaskMeta list.

    Validates each task has: src/*.py, tests/test_*.py, app_spec.xml.
    Raises ValueError if any task is malformed.
    """
    ...


def validate_task(task: TaskMeta) -> list[str]:
    """Return a list of validation errors (empty = valid).

    Checks:
    - Source file exists and is valid Python (compiles)
    - Test file exists and is valid Python
    - app_spec.xml is well-formed XML with exactly 1 <feature>
    - Test file imports from the correct source module
    - At least 3 test cases per task
    """
    ...


def count_test_cases(test_file: Path) -> int:
    """Parse a pytest file and return the number of test_* functions/methods."""
    ...
```

### Module: `bench/runner.py`

```python
"""Benchmark runner — orchestrates task×config execution."""
from __future__ import annotations

import subprocess
from pathlib import Path

from bench.config import AblationConfig
from bench.models import TaskMeta, TaskResult


def run_single(
    task: TaskMeta,
    config: AblationConfig,
    base_yaml: Path,
    run_dir: Path,
    timeout_seconds: int = 300,
    model: str = "claude-sonnet-4-6",
    claw_forge_bin: str = "claw-forge",
) -> TaskResult:
    """Execute one (task, config) pair and return the result.

    Steps:
    1. Create isolated workdir: run_dir / task.task_id / config.id
    2. Copy task template files into workdir
    3. Generate config-specific claw-forge.yaml
    4. Write app_spec.xml into workdir
    5. Invoke: claw-forge run --project <workdir> --config <yaml> [flags]
       with subprocess, capturing stdout/stderr, enforcing timeout
    6. After claw-forge exits (or times out), run pytest on the tests
    7. Parse pytest output for pass/fail counts
    8. Return TaskResult
    """
    ...


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
) -> list[TaskResult]:
    """Run all tasks × all configs sequentially (or with limited concurrency).

    Appends each TaskResult as JSONL to results_file as it completes.
    Returns the full list when done.

    Args:
        tasks: List of tasks to run.
        configs: List of ablation configs.
        base_yaml: Path to base claw-forge.yaml template.
        run_dir: Root directory for isolated run workdirs.
        results_file: Path to output JSONL file (append mode).
        timeout_seconds: Max seconds per (task, config) run.
        model: Model to pass to claw-forge run --model.
        concurrency: Max parallel runs (default 1 = sequential).
        keep_all: If True, keep all workdirs. If False, clean passing runs.
    """
    ...


def _copy_task_template(task: TaskMeta, dest: Path) -> None:
    """Copy task template directory to dest, preserving structure."""
    ...


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
    ...


def _run_pytest(workdir: Path, timeout_seconds: int = 60) -> tuple[int, int, int, int]:
    """Run pytest on workdir/tests/ and parse results.

    Returns: (exit_code, total, passed, failed)
    """
    ...
```

### Module: `bench/score.py`

```python
"""Scoring engine — aggregates TaskResults into BenchmarkSummary."""
from __future__ import annotations

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
    ...


def compute_summary(
    results: list[TaskResult],
    model: str,
    run_id: str,
) -> BenchmarkSummary:
    """Compute full BenchmarkSummary from raw TaskResults.

    Groups by config_id, computes pass rates (overall + per-difficulty),
    computes deltas vs config A (baseline), identifies best config.
    """
    ...


def compute_config_summary(
    config_id: ConfigID,
    label: str,
    results: list[TaskResult],
    baseline_pass_rate: float,
) -> ConfigSummary:
    """Compute summary for a single config from its TaskResults."""
    ...


def pass_rate_by_difficulty(
    results: list[TaskResult],
    difficulty_map: dict[str, Difficulty],
) -> dict[Difficulty, float]:
    """Compute pass rate broken down by difficulty tier."""
    ...
```

### Module: `bench/report.py`

```python
"""Report writer — renders BenchmarkSummary as Markdown and appends to results.md."""
from __future__ import annotations

from pathlib import Path

from bench.models import BenchmarkSummary


RESULTS_MARKER = "<!-- RESULTS_MARKER: new sections inserted above this line -->"


def render_markdown(summary: BenchmarkSummary) -> str:
    """Render a BenchmarkSummary as a Markdown section.

    Format matches the existing template in results.md:
    - H2 header with date
    - Model name
    - Results table (Config | Score | Pass Rate | Δ vs A | Runs | Errors)
    - Impact summary lines
    - Notes section
    """
    ...


def append_to_results(
    summary: BenchmarkSummary,
    results_md_path: Path,
) -> None:
    """Insert rendered Markdown above the RESULTS_MARKER in results.md.

    If the marker line is not found, appends at the end of the file.
    If results.md doesn't exist, creates it with the marker.
    """
    ...


def write_jsonl_backup(
    summary: BenchmarkSummary,
    output_path: Path,
) -> None:
    """Write raw results as JSONL alongside the Markdown for reproducibility."""
    ...
```

### Script: `scripts/run_bench.py`

```python
"""CLI entry point for the benchmark suite."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    """Entry point.

    Usage:
        uv run python scripts/run_bench.py \\
            --model claude-sonnet-4-6 \\
            --configs A,B,C,D,E \\
            --tasks all \\
            --timeout 300 \\
            --concurrency 1 \\
            --results-md /tmp/claw-forge-hashline-pbr/docs/benchmarks/results.md \\
            --keep-all
    """
    ...


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments.

    Args:
        --model         Model for claw-forge run (default: claude-sonnet-4-6)
        --configs       Comma-separated config IDs: A,B,C,D,E (default: all)
        --tasks         Task filter: "all", "easy", "medium", "hard",
                        or comma-separated task IDs (default: all)
        --timeout       Seconds per (task, config) run (default: 300)
        --concurrency   Max parallel runs (default: 1)
        --results-md    Path to results.md to append to
                        (default: /tmp/claw-forge-hashline-pbr/docs/benchmarks/results.md)
        --run-dir       Root for isolated workdirs (default: /tmp/claw-forge-bench-runs)
        --keep-all      Keep all workdirs (default: clean passing runs)
        --dry-run       List tasks and configs without executing
    """
    ...
```

---

## 3. Interface Definitions (API, CLI, Config)

### CLI Interface

The benchmark has one CLI entry point:

```bash
uv run python scripts/run_bench.py [OPTIONS]
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--model` | str | `claude-sonnet-4-6` | Model passed to `claw-forge run --model` |
| `--configs` | str | `A,B,C,D,E` | Comma-separated config IDs to test |
| `--tasks` | str | `all` | Filter: `all`, `easy`, `medium`, `hard`, or task IDs |
| `--timeout` | int | `300` | Seconds per (task, config) run |
| `--concurrency` | int | `1` | Max parallel runs |
| `--results-md` | str | `/tmp/claw-forge-hashline-pbr/docs/benchmarks/results.md` | Where to append results |
| `--run-dir` | str | `/tmp/claw-forge-bench-runs` | Root for isolated workdirs |
| `--keep-all` | flag | `False` | Don't clean workdirs after passing runs |
| `--dry-run` | flag | `False` | Print plan without executing |

### Validation CLI

```bash
uv run python scripts/validate_tasks.py [--tasks-dir tasks/]
```

Runs pre-flight checks on all 30 tasks:
1. Python files compile without syntax errors
2. Test files contain ≥ 3 test cases each
3. `app_spec.xml` is valid XML with exactly 1 feature
4. Tests **fail** against the broken source (confirming the bug exists)
5. A reference solution comment in each source file describes the fix

### Config YAML Format

Each ablation config overlays the base `claw-forge.yaml`:

**`configs/base.yaml`** — shared provider pool, no feature-specific flags:
```yaml
pool:
  strategy: priority
  max_retries: 2

providers:
  claude-oauth:
    type: anthropic_oauth
    priority: 1

agent:
  default_model: claude-sonnet-4-6
  max_tokens: 8192
  temperature: 0.0
  max_concurrent_agents: 1

state:
  database_url: "sqlite+aiosqlite:///claw_forge.db"
```

**`configs/config_a.yaml`** — baseline:
```yaml
agent:
  edit_mode: str_replace
  loop_detect_threshold: 0
  verify_on_exit: false
```

**`configs/config_b.yaml`** — hashline only:
```yaml
agent:
  edit_mode: hashline
  loop_detect_threshold: 0
  verify_on_exit: false
```

**`configs/config_c.yaml`** — str_replace + loop-detect:
```yaml
agent:
  edit_mode: str_replace
  loop_detect_threshold: 5
  verify_on_exit: false
```

**`configs/config_d.yaml`** — str_replace + verify-on-exit:
```yaml
agent:
  edit_mode: str_replace
  loop_detect_threshold: 0
  verify_on_exit: true
```

**`configs/config_e.yaml`** — full stack:
```yaml
agent:
  edit_mode: hashline
  loop_detect_threshold: 5
  verify_on_exit: true
```

### claw-forge Invocation

The runner builds the full command per (task, config):

```bash
cd <workdir> && claw-forge run \
    --project . \
    --config claw-forge.yaml \
    --model <model> \
    --concurrency 1 \
    --edit-mode <edit_mode> \
    --loop-detect-threshold <threshold> \
    --verify-on-exit | --no-verify-on-exit
```

**Note:** The `--edit-mode`, `--loop-detect-threshold`, and `--verify-on-exit` flags are from the hashline-pbr branch at `/tmp/claw-forge-hashline-pbr`. The runner must invoke the dev version:

```bash
cd /tmp/claw-forge-hashline-pbr && uv run claw-forge run \
    --project <workdir> \
    --config <workdir>/claw-forge.yaml \
    [flags]
```

---

## 4. Data Models and Schemas

### JSONL Result Format

Each (task, config) run produces one line in `results.jsonl`:

```json
{
  "task_id": "001_fizzbuzz",
  "config_id": "A",
  "passed": false,
  "tests_total": 5,
  "tests_passed": 3,
  "tests_failed": 2,
  "duration_seconds": 47.3,
  "exit_code": 0,
  "pytest_exit_code": 1,
  "error_message": "",
  "timestamp": "2026-03-12T23:30:00+11:00",
  "workdir": "/tmp/claw-forge-bench-runs/001_fizzbuzz/config-A"
}
```

### Markdown Output Format

Matches the existing template in `/tmp/claw-forge-hashline-pbr/docs/benchmarks/results.md`:

```markdown
## Ablation Bench Results — 2026-03-12

Model: `claude-sonnet-4-6`

| Config | Label | Pass Rate | Δ vs A | Easy | Medium | Hard | Errors |
|--------|-------|----------:|-------:|-----:|-------:|-----:|-------:|
| A | baseline (str_replace) | 60% | — | 90% | 60% | 30% | 0 |
| B | hashline | 73% | +13% | 100% | 70% | 50% | 0 |
| C | str_replace+loop-detect | 67% | +7% | 90% | 70% | 40% | 0 |
| D | str_replace+verify-on-exit | 70% | +10% | 100% | 60% | 50% | 0 |
| E | hashline+loop-detect+verify | 83% | +23% | 100% | 80% | 70% | 0 |

**Hashline impact (B vs A):** +13%  
**Full-stack impact (E vs A):** +23%  
**Best single change:** Config B (hashline, +13%)

### Notes

- Tasks: 30 (10 easy, 10 medium, 10 hard)
- Timeout: 300s per task
- Repetitions: 1 per config (add --reps for statistical significance)
```

### Task Spec XML Format

Each task has a minimal `app_spec.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project_specification mode="greenfield">
  <project_name>bench-001-fizzbuzz</project_name>
  <overview>Fix the fizzbuzz implementation to pass all tests.</overview>
  <technology_stack>
    <language>Python 3.11+</language>
    <testing>pytest</testing>
  </technology_stack>
  <features>
    <feature id="fix-impl" priority="P0">
      <title>Fix implementation</title>
      <description>
        Fix the implementation in src/fizzbuzz.py so that all tests
        in tests/test_fizzbuzz.py pass. Read the test file to understand
        the expected behavior.
      </description>
      <acceptance_criteria>
        <criterion>All tests in tests/test_fizzbuzz.py pass</criterion>
      </acceptance_criteria>
    </feature>
  </features>
</project_specification>
```

---

## 5. Error Handling Strategy

### Layer 1: Task Validation Errors (pre-flight)

`validate_tasks.py` catches these before any benchmark runs:

| Error | Handling |
|-------|----------|
| Missing source/test file | `ValueError` with task_id + expected path |
| Source doesn't compile | Report `SyntaxError` with line number |
| Test file has < 3 test cases | Warning (soft fail); reported but benchmark continues |
| `app_spec.xml` malformed | `ValueError` with parse error |
| Tests pass against broken source | **Critical** — task is incorrectly specified; skip with error |

### Layer 2: claw-forge Runtime Errors

| Error | Handling |
|-------|----------|
| `claw-forge run` timeout | Kill subprocess, record `TaskResult(passed=False, error_message="timeout")` |
| `claw-forge run` crash (non-zero exit) | Record exit code + stderr in `TaskResult.error_message` |
| Provider auth failure | Detected via stderr pattern matching; recorded as error, run continues |
| Lock file conflict | Each (task, config) gets its own workdir — no conflicts possible |
| Missing `claw-forge` binary | Fatal error at startup, not per-task |

### Layer 3: pytest Execution Errors

| Error | Handling |
|-------|----------|
| pytest not found | Fatal at startup (require `uv pip install pytest`) |
| pytest timeout | Kill subprocess, record as failed with `error_message="pytest_timeout"` |
| pytest import error | Record as failed; indicates claw-forge didn't write valid Python |
| All tests pass | `passed=True` |
| Some tests fail | `passed=False`, capture exact pass/fail counts |

### Layer 4: Report Writing Errors

| Error | Handling |
|-------|----------|
| `results.md` not found | Create it fresh with the RESULTS_MARKER |
| RESULTS_MARKER missing | Append at end of file with warning |
| Permission denied | Fatal with clear message about path |
| Git identity not configured | Set via `GIT_AUTHOR_NAME` / `GIT_AUTHOR_EMAIL` env vars |

### Recovery: Resumable Runs

The JSONL results file is append-only. If a run is interrupted:
1. Re-running with the same `--run-dir` detects existing JSONL entries
2. Completed (task, config) pairs are skipped
3. Only missing pairs are executed
4. This makes long benchmark runs crash-safe

---

## 6. Test Plan

### How We Know the 30 Benchmark Tasks Are Correctly Specified

Every task must satisfy the **Red-Green Contract**: tests FAIL on the broken source, tests PASS on the correct source.

#### Validation Script (`scripts/validate_tasks.py`)

For each of the 30 tasks:

1. **Syntax check:** Both `src/*.py` and `tests/test_*.py` compile without errors
2. **Red check (broken):** Run `pytest tests/` against the broken source → must FAIL (exit code ≠ 0)
3. **Green check (solution):** Each task includes a `_solution.py` file (gitignored, used only for validation). Apply it, run `pytest` → must PASS (exit code = 0). Revert after.
4. **Test count:** Each test file has ≥ 3 `test_*` functions
5. **Isolation:** Tests must not import from outside the task directory
6. **Determinism:** Run tests 3 times → same result each time (no flaky tests)

The validation script runs as a CI-like pre-flight check:

```bash
uv run python scripts/validate_tasks.py --tasks-dir tasks/
# Exit 0: all 30 tasks pass Red-Green Contract
# Exit 1: prints failing tasks with specific errors
```

#### Task Design Principles

**Easy tasks (001–010):** Single function with a clear bug. Fix is ≤5 lines.
- Off-by-one errors, wrong operators, missing edge cases
- Agent needs: read test, understand expected behavior, fix 1–2 lines

**Medium tasks (011–020):** Class or module with multiple interacting parts. Fix requires understanding data flow.
- Wrong algorithm, missing method, incorrect state management
- Agent needs: understand architecture, fix across 2–3 functions, ~10–30 lines

**Hard tasks (021–030):** Multi-file or complex algorithm. Fix requires deep reasoning.
- Parser bugs, interpreter issues, concurrent data structure errors
- Agent needs: trace execution paths, fix across files, ~30–80 lines

### Unit Tests for Benchmark Infrastructure

```bash
uv run pytest tests/ -v
```

| Test file | What it verifies |
|-----------|-----------------|
| `tests/test_score.py` | Pass rate computation, delta calculation, difficulty breakdown |
| `tests/test_report.py` | Markdown rendering matches expected format, RESULTS_MARKER insertion |
| `tests/test_config.py` | All 5 configs generate correct YAML/CLI flags |
| `tests/test_task_registry.py` | Task discovery, validation rules, counting |

---

## 7. Constraints and Assumptions

### Hard Constraints

1. **No Docker** — All execution is bare-metal Linux (subprocess only)
2. **No external services** — No databases, no cloud APIs beyond the LLM provider
3. **claw-forge from dev branch** — Must use `/tmp/claw-forge-hashline-pbr` (has `--edit-mode`, `--loop-detect-threshold`, `--verify-on-exit` flags). The installed `claw-forge` binary does NOT have these flags.
4. **Python only** — All 30 tasks are Python (pytest test runner)
5. **Sequential by default** — Default concurrency=1 to avoid provider rate limits
6. **Single feature per task** — Each task has exactly one feature in its `app_spec.xml`
7. **No network-dependent tasks** — Tasks must not require internet access (no API calls, no pip installs at test time)
8. **Timeout: 300s per task** — Prevents runaway agent loops
9. **Git identity** — All commits use `Alex Chen <alex.chen31337@gmail.com>`

### Assumptions

1. **claw-forge at `/tmp/claw-forge-hashline-pbr` is functional** — The hashline-pbr branch builds and runs correctly with `uv run claw-forge run`
2. **Claude OAuth is configured** — `~/.claude/.credentials.json` exists and is valid (or another provider is configured in base.yaml)
3. **uv is installed** — All Python execution uses `uv run`
4. **pytest is available** — `uv pip install pytest` has been run
5. **Tasks are deterministic** — Same broken code + same tests = same validation result every time
6. **Single model per benchmark run** — All 5 configs use the same model (the ablation variable is the middleware, not the model)

### Cost Estimation

With `claude-sonnet-4-6` at ~$3/MTok input + $15/MTok output:
- ~30 tasks × 5 configs = 150 runs
- Estimated ~2,000–5,000 tokens per run (small tasks)
- **Estimated total cost: $5–$20 per full benchmark run**
- Easy tasks: ~$0.02–$0.05 each
- Hard tasks: ~$0.10–$0.30 each (more reasoning tokens)

### Future Extensions (Out of Scope for v1)

- Statistical significance via `--reps N` (run each pair N times, compute mean ± std)
- Model comparison (run same tasks with different `--model` values)
- Automatic PR with results (git commit + push to hashline-pbr branch)
- Parallel execution across multiple provider keys
- Task difficulty auto-classification based on agent performance

---

## Appendix A: The 30 Benchmark Tasks

### Easy (001–010)

| ID | Name | Bug Type | Lines to Fix |
|----|------|----------|:------------:|
| 001 | fizzbuzz | Wrong modulo order (checks 3 before 15) | 2 |
| 002 | palindrome | Off-by-one in string slice | 1 |
| 003 | fibonacci | Base case returns wrong value | 1 |
| 004 | reverse_words | Splits on wrong delimiter | 1 |
| 005 | count_vowels | Missing vowel in set ('u' omitted) | 1 |
| 006 | celsius_to_fahrenheit | Wrong formula (adds instead of multiplies) | 1 |
| 007 | flatten_list | Doesn't handle nested lists recursively | 3 |
| 008 | is_anagram | Case-sensitive comparison (should be insensitive) | 2 |
| 009 | binary_search | Wrong midpoint calculation (off by one) | 1 |
| 010 | remove_duplicates | Doesn't preserve order | 3 |

### Medium (011–020)

| ID | Name | Bug Type | Lines to Fix |
|----|------|----------|:------------:|
| 011 | lru_cache | Eviction doesn't update access order | 8 |
| 012 | linked_list | Delete method doesn't handle tail node | 10 |
| 013 | stack_calculator | Missing operator precedence handling | 15 |
| 014 | csv_parser | Doesn't handle quoted fields with commas | 12 |
| 015 | rate_limiter | Sliding window doesn't slide (fixed window) | 10 |
| 016 | json_flattener | Doesn't handle arrays in nested objects | 15 |
| 017 | trie | Search returns True for prefixes (not just full words) | 8 |
| 018 | matrix_multiply | Transpose indices swapped | 5 |
| 019 | event_emitter | Listener removal during emit causes skip | 10 |
| 020 | text_wrapper | Breaks words mid-character instead of at spaces | 12 |

### Hard (021–030)

| ID | Name | Bug Type | Lines to Fix |
|----|------|----------|:------------:|
| 021 | interpreter | Tokenizer doesn't handle negative numbers | 25 |
| 022 | regex_engine | Greedy `*` doesn't backtrack | 30 |
| 023 | b_tree | Split doesn't promote median correctly | 35 |
| 024 | graph_serializer | Cycle detection fails on self-referencing nodes | 20 |
| 025 | coroutine_scheduler | Doesn't resume after yield with value | 30 |
| 026 | diff_algorithm | Myers diff produces non-minimal edits | 40 |
| 027 | type_checker | Doesn't unify generic type parameters | 35 |
| 028 | query_planner | JOIN order ignores selectivity estimates | 30 |
| 029 | bytecode_compiler | Local variable slots collide across scopes | 25 |
| 030 | protocol_parser | Fragmented messages reassembled out of order | 30 |

---

## Appendix B: Task Template Structure

Each task directory follows this exact structure:

```
tasks/<difficulty>/<NNN_name>/
├── src/
│   └── <name>.py          # Broken implementation (this is what the agent fixes)
├── tests/
│   └── test_<name>.py     # pytest tests (≥3 test functions, passes when source is correct)
├── _solution.py            # Reference solution (gitignored, for validation only)
├── app_spec.xml            # Single-feature claw-forge spec
└── CLAUDE.md               # Task-specific instructions for the agent
```

**CLAUDE.md template:**
```markdown
# Task: Fix <name>

The file `src/<name>.py` has a bug. Your job is to fix it so that all tests pass.

## Instructions
1. Read `tests/test_<name>.py` to understand expected behavior
2. Read `src/<name>.py` to find the bug
3. Fix the bug — make minimal changes
4. Run `pytest tests/` to verify all tests pass

## Constraints
- Do NOT modify test files
- Make the minimal change needed to fix the bug
- Do NOT add new dependencies
```

---

## Appendix C: Invocation Examples

### Full benchmark run
```bash
cd ~/projects/claw-forge-bench
uv run python scripts/run_bench.py \
    --model claude-sonnet-4-6 \
    --configs A,B,C,D,E \
    --timeout 300 \
    --results-md /tmp/claw-forge-hashline-pbr/docs/benchmarks/results.md
```

### Quick smoke test (easy tasks, 2 configs)
```bash
uv run python scripts/run_bench.py \
    --model claude-sonnet-4-6 \
    --configs A,E \
    --tasks easy \
    --timeout 120
```

### Dry run (plan without executing)
```bash
uv run python scripts/run_bench.py --dry-run
```

### Validate all tasks (pre-flight)
```bash
uv run python scripts/validate_tasks.py
```

### Single task, single config (debugging)
```bash
uv run python scripts/run_bench.py \
    --configs B \
    --tasks 001_fizzbuzz \
    --keep-all
```
