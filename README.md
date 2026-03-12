# claw-forge Ablation Benchmark Suite

Self-contained benchmark for ablation-testing claw-forge's three middleware features:
- **hashline** — line-addressable editing
- **loop-detect** — agent loop detection and circuit breaking
- **verify-on-exit** — post-edit verification pass

## Quick Start

```bash
# Install dependencies
uv sync

# Validate all 30 tasks (pre-flight check)
uv run python scripts/validate_tasks.py

# Dry run (plan without executing)
uv run python scripts/run_bench.py --dry-run

# Full benchmark
uv run python scripts/run_bench.py \
    --model claude-sonnet-4-6 \
    --configs A,B,C,D,E \
    --timeout 300
```

## Ablation Configurations

| Config | Edit Mode | Loop Detect | Verify on Exit |
|--------|-----------|:-----------:|:--------------:|
| A (baseline) | str_replace | ✗ | ✗ |
| B | hashline | ✗ | ✗ |
| C | str_replace | ✓ (threshold=5) | ✗ |
| D | str_replace | ✗ | ✓ |
| E (full stack) | hashline | ✓ (threshold=5) | ✓ |

## Task Tiers

- **Easy (001–010):** Single-function bugs, 1–3 lines to fix
- **Medium (011–020):** Class/module bugs, 5–15 lines to fix
- **Hard (021–030):** Multi-file/algorithm bugs, 20–40 lines to fix

## Results

Results are appended to `/tmp/claw-forge-hashline-pbr/docs/benchmarks/results.md`.
