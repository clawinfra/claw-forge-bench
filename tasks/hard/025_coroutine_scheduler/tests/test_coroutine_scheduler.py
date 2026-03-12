"""Tests for coroutine scheduler."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from coroutine_scheduler import Scheduler, task_counter, task_accumulator, task_echo_chain


def test_single_task():
    s = Scheduler()
    s.spawn("counter", task_counter(3))
    results = s.run()
    assert results["counter"] == 6  # 1+2+3


def test_multiple_tasks():
    s = Scheduler()
    s.spawn("c1", task_counter(2))
    s.spawn("c2", task_counter(3))
    results = s.run()
    assert results["c1"] == 3  # 1+2
    assert results["c2"] == 6  # 1+2+3


def test_accumulator():
    s = Scheduler()
    s.spawn("acc", task_accumulator([10, 20, 30]))
    results = s.run()
    assert results["acc"] == 60


def test_echo_chain_with_send():
    """task_echo_chain needs send() to work — yields i, expects i back, sums them.
    With correct send(): total = 1+2+3 = 6
    With broken next()-only: total = 0 (received is always None)
    """
    s = Scheduler()
    s.spawn("echo", task_echo_chain(3))
    results = s.run()
    assert results["echo"] == 6  # 1+2+3


def test_interleaving():
    """Multiple tasks should be interleaved (round-robin)."""
    s = Scheduler()
    s.spawn("a", task_counter(2))
    s.spawn("b", task_counter(2))
    results = s.run()
    assert results["a"] == 3
    assert results["b"] == 3
