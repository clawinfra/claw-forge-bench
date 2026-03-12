"""Data models for benchmark results."""
from __future__ import annotations

import enum
import json
from dataclasses import asdict, dataclass, field
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
    edit_mode: str  # "str_replace" | "hashline"
    loop_detect_threshold: int  # 0 = disabled, 5 = default
    verify_on_exit: bool

    def to_cli_flags(self) -> list[str]:
        """Return CLI flags list for claw-forge run."""
        flags = [
            "--edit-mode",
            self.edit_mode,
            "--loop-detect-threshold",
            str(self.loop_detect_threshold),
        ]
        if self.verify_on_exit:
            flags.append("--verify-on-exit")
        else:
            flags.append("--no-verify-on-exit")
        return flags

    def to_yaml_overrides(self) -> dict[str, object]:
        """Return dict to merge into base claw-forge.yaml."""
        return {
            "agent": {
                "edit_mode": self.edit_mode,
                "loop_detect_threshold": self.loop_detect_threshold,
                "verify_on_exit": self.verify_on_exit,
            }
        }


@dataclass
class TaskMeta:
    """Metadata for a single benchmark task."""

    task_id: str  # e.g. "001_fizzbuzz"
    difficulty: Difficulty
    description: str
    source_file: str  # relative path within task dir
    test_file: str  # relative path within task dir
    task_dir: Path  # absolute path to task template
    expected_test_count: int  # number of test cases in test file


@dataclass
class TaskResult:
    """Result of running one (task, config) pair."""

    task_id: str
    config_id: ConfigID
    passed: bool  # all tests passed
    tests_total: int
    tests_passed: int
    tests_failed: int
    duration_seconds: float
    exit_code: int  # claw-forge exit code
    pytest_exit_code: int  # pytest exit code
    error_message: str = ""  # if claw-forge or pytest errored
    timestamp: str = ""  # ISO 8601
    workdir: str = ""  # path to run directory

    def to_jsonl(self) -> str:
        """Serialize to a single JSON line."""
        return json.dumps(asdict(self), default=str)

    @classmethod
    def from_jsonl(cls, line: str) -> TaskResult:
        """Deserialize from a single JSON line."""
        data = json.loads(line)
        data["config_id"] = ConfigID(data["config_id"])
        return cls(**data)


@dataclass
class ConfigSummary:
    """Aggregated results for one ablation config."""

    config_id: ConfigID
    label: str
    total_tasks: int
    tasks_passed: int
    pass_rate: float  # 0.0 – 1.0
    pass_rate_by_difficulty: dict[Difficulty, float] = field(default_factory=dict)
    avg_duration_seconds: float = 0.0
    total_errors: int = 0
    delta_vs_baseline: float = 0.0  # pass_rate - baseline pass_rate


@dataclass
class BenchmarkSummary:
    """Complete benchmark results across all configs."""

    run_id: str  # UUID
    timestamp: str  # ISO 8601
    model: str  # model used for the run
    task_count: int
    configs: list[ConfigSummary] = field(default_factory=list)
    raw_results: list[TaskResult] = field(default_factory=list)
    best_config: ConfigID = ConfigID.A
    best_single_change: ConfigID = ConfigID.A  # biggest delta vs baseline
    hashline_impact: float = 0.0  # B.pass_rate - A.pass_rate
    full_stack_impact: float = 0.0  # E.pass_rate - A.pass_rate
