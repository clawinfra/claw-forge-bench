"""Tests for CSV parser."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from csv_parser import parse_csv, parse_row


def test_simple_row():
    assert parse_row("a,b,c") == ["a", "b", "c"]


def test_quoted_field():
    assert parse_row('a,"b,c",d') == ["a", "b,c", "d"]


def test_multiline():
    text = "a,b\nc,d"
    assert parse_csv(text) == [["a", "b"], ["c", "d"]]


def test_quoted_csv():
    text = 'name,city\n"Smith, John","New York, NY"'
    rows = parse_csv(text)
    assert rows[1] == ["Smith, John", "New York, NY"]


def test_empty_fields():
    assert parse_row("a,,c") == ["a", "", "c"]
