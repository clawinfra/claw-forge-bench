"""Tests for query planner."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from query_planner import Table, plan_joins, optimize_order


def test_single_table():
    tables = [Table("users", 1000)]
    plan = plan_joins(tables, [])
    assert plan.order == ["users"]


def test_selectivity_ordering():
    """Table with high selectivity (fewer matching rows) should come first."""
    tables = [
        Table("orders", 10000, selectivity=1.0),    # 10000 effective rows
        Table("users", 1000, selectivity=0.01),      # 10 effective rows
    ]
    order = optimize_order(tables)
    assert order[0] == "users"  # users has fewer effective rows


def test_plan_uses_selectivity():
    tables = [
        Table("big", 100000, selectivity=0.001),   # 100 effective
        Table("medium", 1000, selectivity=1.0),     # 1000 effective
        Table("small", 10, selectivity=1.0),        # 10 effective
    ]
    plan = plan_joins(tables, [("big", "medium"), ("medium", "small")])
    # Optimal order: small (10), big (100), medium (1000)
    assert plan.order[0] == "small"


def test_equal_selectivity():
    tables = [
        Table("a", 100, selectivity=1.0),
        Table("b", 50, selectivity=1.0),
    ]
    order = optimize_order(tables)
    assert order[0] == "b"  # fewer rows


def test_cost_decreases_with_optimization():
    tables = [
        Table("big", 10000, selectivity=1.0),
        Table("small", 10, selectivity=0.1),
    ]
    plan = plan_joins(tables, [("big", "small")])
    # With optimization, small (effective 1) should be first
    assert plan.order[0] == "small"
