# claw-forge Ablation Benchmark Suite

Self-contained benchmark for ablation-testing [claw-forge](https://github.com/clawinfra/claw-forge)'s three middleware features across 30 Python coding tasks.

## Results (2026-03-13 · `claude-opus-4-6`)

| Config | Edit Mode | Loop Detect | Verify on Exit | Pass Rate | Δ vs A |
|--------|-----------|:-----------:|:--------------:|----------:|-------:|
| A (baseline) | str_replace | ✗ | ✗ | 96.7% (29/30) | — |
| B | hashline | ✗ | ✗ | 96.7% (29/30) | +0.0pp |
| C | str_replace | ✓ | ✗ | 96.7% (29/30) | +0.0pp |
| D | str_replace | ✗ | ✓ | 96.7% (29/30) | +0.0pp |
| **E (full stack)** | **hashline** | **✓** | **✓** | **100% (30/30)** | **+3.3pp** |

**Key finding:** Each middleware layer individually shows no uplift over baseline. But combining all three produces a +3.3pp interaction effect — Config E achieves **100%** on this suite. The full stack is greater than the sum of its parts.

→ [Full results in claw-forge docs](https://github.com/clawinfra/claw-forge/blob/main/docs/benchmarks/results.md)

## Recommended production stack

```bash
claw-forge run --edit-mode hashline --loop-detect-threshold 5 --verify-on-exit
```

## Quick Start

```bash
# Install dependencies
uv sync

# Validate all 30 tasks (pre-flight check)
uv run python scripts/validate_tasks.py --red-green

# Dry run (plan without executing)
uv run python scripts/run_bench_direct.py --configs A,B,C,D,E --dry-run

# Full benchmark (direct Claude SDK runner — recommended)
uv run python scripts/run_bench_direct.py \
    --configs A,B,C,D,E \
    --concurrency 5

# Results are appended to docs/benchmarks/results.md in claw-forge repo
```

## Ablation Configurations

| Config | Edit Mode | Loop Detect | Verify on Exit | Description |
|--------|-----------|:-----------:|:--------------:|-------------|
| A | str_replace | ✗ | ✗ | Baseline — no middleware |
| B | hashline | ✗ | ✗ | Hashline edit mode only |
| C | str_replace | ✓ (threshold=5) | ✗ | Loop detection only |
| D | str_replace | ✗ | ✓ | Verify-on-exit only |
| E | hashline | ✓ (threshold=5) | ✓ | **Full stack (recommended)** |

## Task Suite

30 Python coding tasks across 3 difficulty tiers:

- **Easy (001–010):** Single-function bugs, 1–3 lines to fix
  - fizzbuzz, palindrome, fibonacci, reverse_words, count_vowels, celsius_to_fahrenheit, flatten_list, is_anagram, binary_search, remove_duplicates
- **Medium (011–020):** Class/module bugs, 5–15 lines to fix
  - lru_cache, linked_list, stack_calculator, csv_parser, rate_limiter, json_flattener, trie, matrix_multiply, event_emitter, text_wrapper
- **Hard (021–030):** Multi-file/algorithm bugs, 20–40 lines to fix
  - interpreter, regex_engine, b_tree, graph_serializer, coroutine_scheduler, diff_algorithm, type_checker, query_planner, bytecode_compiler, protocol_parser

Each task has:
- `src/<name>.py` — broken/incomplete implementation
- `tests/test_<name>.py` — pytest suite (fails on broken, passes on fixed)
- `_solution.py` — reference solution (not shown to agent)
- `CLAUDE.md` — task spec given to agent

## Architecture

```
scripts/run_bench_direct.py   ← recommended: direct Claude SDK runner
scripts/run_bench.py          ← legacy: claw-forge CLI subprocess runner
scripts/validate_tasks.py     ← red-green contract validation
bench/                        ← core modules (runner, scorer, report, models, config)
tasks/easy|medium|hard/       ← 30 task directories
configs/                      ← 5 ablation config YAMLs (A–E)
runs/results.jsonl            ← append-only crash-safe result log (resume support)
```

## Resume Support

Results are appended to `runs/results.jsonl` after each task completes. If a run is interrupted, re-running the same command skips already-completed `(task_id, config_id)` pairs automatically.

## CI

[![CI](https://github.com/clawinfra/claw-forge-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/clawinfra/claw-forge-bench/actions)

- 36 unit tests for benchmark infrastructure
- Red-green contract validated for all 30 tasks on every push
- Dry-run smoke test
