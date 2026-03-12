"""Report writer — renders BenchmarkSummary as Markdown and appends to results.md."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from bench.models import BenchmarkSummary, Difficulty

RESULTS_MARKER = "<!-- RESULTS_MARKER: new sections inserted above this line -->"


def render_markdown(summary: BenchmarkSummary) -> str:
    """Render a BenchmarkSummary as a Markdown section."""
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines: list[str] = []

    lines.append(f"## Ablation Bench Results — {date_str}")
    lines.append("")
    lines.append(f"Model: `{summary.model}`")
    lines.append("")

    # Table header
    lines.append(
        "| Config | Label | Pass Rate | Δ vs A | Easy | Medium | Hard | Errors |"
    )
    lines.append(
        "|--------|-------|----------:|-------:|-----:|-------:|-----:|-------:|"
    )

    for cs in summary.configs:
        delta = "—" if cs.config_id == "A" else f"+{cs.delta_vs_baseline:.0%}"
        if cs.delta_vs_baseline < 0 and cs.config_id != "A":
            delta = f"{cs.delta_vs_baseline:.0%}"

        easy_rate = cs.pass_rate_by_difficulty.get(Difficulty.EASY, 0.0)
        medium_rate = cs.pass_rate_by_difficulty.get(Difficulty.MEDIUM, 0.0)
        hard_rate = cs.pass_rate_by_difficulty.get(Difficulty.HARD, 0.0)

        lines.append(
            f"| {cs.config_id} | {cs.label} "
            f"| {cs.pass_rate:.0%} | {delta} "
            f"| {easy_rate:.0%} | {medium_rate:.0%} | {hard_rate:.0%} "
            f"| {cs.total_errors} |"
        )

    lines.append("")
    lines.append(
        f"**Hashline impact (B vs A):** "
        f"+{summary.hashline_impact:.0%}"
    )
    lines.append(
        f"**Full-stack impact (E vs A):** "
        f"+{summary.full_stack_impact:.0%}"
    )
    best_cs = next(
        (c for c in summary.configs if c.config_id == summary.best_single_change),
        None,
    )
    if best_cs:
        lines.append(
            f"**Best single change:** Config {best_cs.config_id} "
            f"({best_cs.label}, +{best_cs.delta_vs_baseline:.0%})"
        )

    lines.append("")
    lines.append("### Notes")
    lines.append("")
    lines.append(
        f"- Tasks: {summary.task_count} "
        f"(10 easy, 10 medium, 10 hard)"
    )
    lines.append("- Timeout: 300s per task")
    lines.append("- Repetitions: 1 per config (add --reps for statistical significance)")
    lines.append(f"- Run ID: `{summary.run_id}`")
    lines.append("")

    return "\n".join(lines)


def append_to_results(
    summary: BenchmarkSummary,
    results_md_path: Path,
) -> None:
    """Insert rendered Markdown above the RESULTS_MARKER in results.md.

    If the marker line is not found, appends at the end of the file.
    If results.md doesn't exist, creates it with the marker.
    """
    md = render_markdown(summary)

    if not results_md_path.exists():
        results_md_path.parent.mkdir(parents=True, exist_ok=True)
        results_md_path.write_text(
            f"# Ablation Benchmark Results\n\n{md}\n---\n\n{RESULTS_MARKER}\n"
        )
        return

    content = results_md_path.read_text()
    if RESULTS_MARKER in content:
        content = content.replace(
            RESULTS_MARKER,
            f"{md}\n---\n\n{RESULTS_MARKER}",
        )
    else:
        content += f"\n\n{md}\n---\n\n{RESULTS_MARKER}\n"

    results_md_path.write_text(content)


def write_jsonl_backup(
    summary: BenchmarkSummary,
    output_path: Path,
) -> None:
    """Write raw results as JSONL alongside the Markdown for reproducibility."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        for result in summary.raw_results:
            f.write(result.to_jsonl() + "\n")
