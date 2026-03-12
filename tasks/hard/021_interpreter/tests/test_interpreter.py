"""Tests for interpreter."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from interpreter import Interpreter, tokenize


def test_simple_arithmetic():
    interp = Interpreter()
    assert interp.evaluate("2 + 3") == 5.0


def test_negative_number():
    interp = Interpreter()
    assert interp.evaluate("-5") == -5.0


def test_negative_in_expression():
    interp = Interpreter()
    assert interp.evaluate("3 + -2") == 1.0


def test_variable_assignment():
    interp = Interpreter()
    interp.evaluate("x = 10")
    assert interp.evaluate("x") == 10.0


def test_negative_assignment():
    interp = Interpreter()
    interp.evaluate("x = -3")
    assert interp.evaluate("x") == -3.0


def test_precedence():
    interp = Interpreter()
    assert interp.evaluate("2 + 3 * 4") == 14.0


def test_tokenize_negative():
    tokens = tokenize("-5")
    assert len(tokens) == 1
    assert tokens[0].value == -5.0
