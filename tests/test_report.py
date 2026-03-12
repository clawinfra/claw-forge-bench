"""Unit tests for report writer."""
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from bench.models import BenchmarkSummary, ConfigID, ConfigSummary, Difficulty
from bench.report import RESULTS_MARKER, append_to_results, render_markdown


def _make_summary() -> BenchmarkSummary:
    """Create a test BenchmarkSummary."""
    return BenchmarkSummary(
        run_id="test-run-001",
        timestamp="2026-03-12T12:00:00Z",
        model="claude-sonnet-4-6",
        task_count=30,
        configs=[
            ConfigSummary(
                config_id=ConfigID.A,
                label="baseline",
                total_tasks=30,
                tasks_passed=18,
                pass_rate=0.6,
                pass_rate_by_difficulty={
                    Difficulty.EASY: 0.9,
                    Difficulty.MEDIUM: 0.6,
                    Difficulty.HARD: 0.3,
                },
                avg_duration_seconds=45.0,
                total_errors=0,
                delta_vs_baseline=0.0,
            ),
            ConfigSummary(
                config_id=ConfigID.E,
                label="full stack",
                total_tasks=30,
                tasks_passed=25,
                pass_rate=0.83,
                pass_rate_by_difficulty={
                    Difficulty.EASY: 1.0,
                    Difficulty.MEDIUM: 0.8,
                    Difficulty.HARD: 0.7,
                },
                avg_duration_seconds=50.0,
                total_errors=0,
                delta_vs_baseline=0.23,
            ),
        ],
        raw_results=[],
        best_config=ConfigID.E,
        best_single_change=ConfigID.E,
        hashline_impact=0.13,
        full_stack_impact=0.23,
    )


def test_render_markdown_contains_header():
    md = render_markdown(_make_summary())
    assert "## Ablation Bench Results" in md


def test_render_markdown_contains_model():
    md = render_markdown(_make_summary())
    assert "claude-sonnet-4-6" in md


def test_render_markdown_contains_table():
    md = render_markdown(_make_summary())
    assert "| Config |" in md
    assert "| A |" in md
    assert "| E |" in md


def test_render_markdown_contains_impact():
    md = render_markdown(_make_summary())
    assert "Hashline impact" in md
    assert "Full-stack impact" in md


def test_append_to_results_creates_file():
    """Should create results.md if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results_path = Path(tmpdir) / "results.md"
        append_to_results(_make_summary(), results_path)
        assert results_path.exists()
        content = results_path.read_text()
        assert RESULTS_MARKER in content
        assert "Ablation Bench Results" in content


def test_append_to_results_inserts_above_marker():
    """Should insert results above the RESULTS_MARKER."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results_path = Path(tmpdir) / "results.md"
        results_path.write_text(f"# Header\n\n{RESULTS_MARKER}\n\n# Footer\n")
        append_to_results(_make_summary(), results_path)
        content = results_path.read_text()
        # Results should be above the marker
        marker_pos = content.index(RESULTS_MARKER)
        results_pos = content.index("Ablation Bench Results")
        assert results_pos < marker_pos
        # Footer should still be there
        assert "# Footer" in content


def test_append_to_results_preserves_existing():
    """Multiple appends should keep all results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results_path = Path(tmpdir) / "results.md"
        results_path.write_text(f"# Header\n\n{RESULTS_MARKER}\n")
        append_to_results(_make_summary(), results_path)
        results_path.read_text()  # first append happened
        append_to_results(_make_summary(), results_path)
        second_content = results_path.read_text()
        # Should have two result sections
        assert second_content.count("Ablation Bench Results") == 2
