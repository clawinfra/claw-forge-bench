"""Tests for graph serializer."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from graph_serializer import Node, serialize_graph, deserialize_graph


def test_simple_graph():
    a = Node("a", 1)
    b = Node("b", 2)
    a.add_edge(b)
    result = json.loads(serialize_graph(a))
    assert result["id"] == "a"
    assert len(result["edges"]) == 1


def test_self_reference():
    """A node that points to itself should not cause infinite recursion."""
    a = Node("a", 1)
    a.add_edge(a)
    result = json.loads(serialize_graph(a))
    assert result["id"] == "a"
    # Should have a back-reference, not infinite nesting
    assert any(e.get("ref") == "a" for e in result["edges"])


def test_cycle():
    a = Node("a")
    b = Node("b")
    a.add_edge(b)
    b.add_edge(a)
    result = json.loads(serialize_graph(a))
    assert result["id"] == "a"


def test_roundtrip():
    a = Node("a", 1)
    b = Node("b", 2)
    c = Node("c", 3)
    a.add_edge(b)
    b.add_edge(c)
    json_str = serialize_graph(a)
    root = deserialize_graph(json_str)
    assert root.id == "a"
    assert root.value == 1
    assert len(root.edges) == 1
    assert root.edges[0].id == "b"
