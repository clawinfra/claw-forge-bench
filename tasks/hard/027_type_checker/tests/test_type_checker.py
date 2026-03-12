"""Tests for type checker."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from type_checker import Type, TypeChecker


def test_concrete_match():
    tc = TypeChecker()
    assert tc.check(Type("int"), Type("int")) is True
    assert tc.check(Type("int"), Type("str")) is False


def test_generic_binding():
    """Type variable T should be bound on first encounter."""
    tc = TypeChecker()
    assert tc.check(Type("T"), Type("int")) is True
    # T is now bound to int
    assert tc.check(Type("T"), Type("int")) is True
    assert tc.check(Type("T"), Type("str")) is False


def test_generic_in_params():
    tc = TypeChecker()
    # List[T] vs List[int] should bind T=int
    expected = Type("List", [Type("T")])
    actual = Type("List", [Type("int")])
    assert tc.check(expected, actual) is True
    # Now T is int, so List[T] vs List[str] should fail
    assert tc.check(
        Type("List", [Type("T")]),
        Type("List", [Type("str")]),
    ) is False


def test_nested_generics():
    tc = TypeChecker()
    expected = Type("Map", [Type("T"), Type("T2")])
    actual = Type("Map", [Type("str"), Type("int")])
    assert tc.check(expected, actual) is True


def test_param_count_mismatch():
    tc = TypeChecker()
    assert tc.check(
        Type("List", [Type("int")]),
        Type("List", []),
    ) is False
