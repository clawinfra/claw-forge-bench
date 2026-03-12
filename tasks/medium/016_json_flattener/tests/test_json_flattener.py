"""Tests for JSON flattener."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from json_flattener import flatten_json


def test_flat():
    assert flatten_json({"a": 1, "b": 2}) == {"a": 1, "b": 2}


def test_nested():
    data = {"a": {"b": {"c": 1}}}
    assert flatten_json(data) == {"a.b.c": 1}


def test_with_array():
    data = {"a": [1, 2, 3]}
    result = flatten_json(data)
    assert result == {"a.0": 1, "a.1": 2, "a.2": 3}


def test_nested_array_of_objects():
    data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
    result = flatten_json(data)
    assert result == {"users.0.name": "Alice", "users.1.name": "Bob"}


def test_mixed():
    data = {"a": 1, "b": {"c": 2, "d": [3, 4]}}
    result = flatten_json(data)
    assert result == {"a": 1, "b.c": 2, "b.d.0": 3, "b.d.1": 4}
