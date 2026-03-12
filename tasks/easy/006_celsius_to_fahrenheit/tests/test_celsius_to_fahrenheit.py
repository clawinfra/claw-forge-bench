"""Tests for celsius_to_fahrenheit."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from celsius_to_fahrenheit import celsius_to_fahrenheit


def test_freezing():
    assert celsius_to_fahrenheit(0) == 32.0


def test_boiling():
    assert celsius_to_fahrenheit(100) == 212.0


def test_body_temp():
    assert abs(celsius_to_fahrenheit(37) - 98.6) < 0.1


def test_negative():
    assert celsius_to_fahrenheit(-40) == -40.0
