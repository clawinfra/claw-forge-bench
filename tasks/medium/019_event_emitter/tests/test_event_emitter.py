"""Tests for event emitter."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from event_emitter import EventEmitter


def test_basic_emit():
    ee = EventEmitter()
    results = []
    ee.on("test", lambda x: results.append(x))
    ee.emit("test", 42)
    assert results == [42]


def test_multiple_listeners():
    ee = EventEmitter()
    results = []
    ee.on("test", lambda: results.append(1))
    ee.on("test", lambda: results.append(2))
    ee.emit("test")
    assert results == [1, 2]


def test_once():
    ee = EventEmitter()
    results = []
    ee.once("test", lambda: results.append(1))
    ee.emit("test")
    ee.emit("test")
    assert results == [1]  # only called once


def test_multiple_once_listeners():
    """Multiple once() listeners should all fire."""
    ee = EventEmitter()
    results = []
    ee.once("test", lambda: results.append(1))
    ee.once("test", lambda: results.append(2))
    ee.emit("test")
    assert sorted(results) == [1, 2]


def test_off():
    ee = EventEmitter()
    results = []
    cb = lambda: results.append(1)
    ee.on("test", cb)
    ee.off("test", cb)
    ee.emit("test")
    assert results == []


def test_listener_count():
    ee = EventEmitter()
    assert ee.listener_count("test") == 0
    ee.on("test", lambda: None)
    assert ee.listener_count("test") == 1
