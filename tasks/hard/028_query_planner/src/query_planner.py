"""Simple query planner with JOIN ordering."""
from dataclasses import dataclass


@dataclass
class Table:
    name: str
    row_count: int
    selectivity: float = 1.0  # fraction of rows that match filter


@dataclass
class JoinPlan:
    order: list[str]
    estimated_cost: float


def plan_joins(tables: list[Table], joins: list[tuple[str, str]]) -> JoinPlan:
    """Plan JOIN order to minimize estimated cost.

    The cost model: for each join step, cost = left_rows * right_rows * selectivity.
    Optimal ordering puts most selective (smallest intermediate result) tables first.
    """
    # Bug: joins tables in the order they appear, ignoring selectivity
    order = [t.name for t in tables]
    cost = _estimate_cost(tables, order, joins)
    return JoinPlan(order=order, estimated_cost=cost)


def _estimate_cost(
    tables: list[Table],
    order: list[str],
    joins: list[tuple[str, str]],
) -> float:
    """Estimate the total cost of a join order."""
    table_map = {t.name: t for t in tables}
    if not order:
        return 0.0
    running_rows = table_map[order[0]].row_count * table_map[order[0]].selectivity
    total_cost = 0.0
    for name in order[1:]:
        t = table_map[name]
        right_rows = t.row_count * t.selectivity
        total_cost += running_rows * right_rows
        running_rows = running_rows * right_rows * 0.1  # join selectivity
    return total_cost


def optimize_order(tables: list[Table]) -> list[str]:
    """Find optimal join order by sorting by effective row count."""
    # Bug: sorts by raw row_count, ignoring selectivity
    sorted_tables = sorted(tables, key=lambda t: t.row_count)
    return [t.name for t in sorted_tables]
