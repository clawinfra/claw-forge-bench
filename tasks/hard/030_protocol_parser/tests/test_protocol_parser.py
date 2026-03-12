"""Tests for protocol parser."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from protocol_parser import ProtocolParser, Fragment, Message, parse_frame


def test_single_fragment():
    parser = ProtocolParser()
    frag = Fragment(message_id=1, sequence=0, total=1, data=b"hello")
    msg = parser.feed(frag)
    assert msg is not None
    assert msg.data == b"hello"


def test_ordered_fragments():
    parser = ProtocolParser()
    f1 = Fragment(message_id=1, sequence=0, total=2, data=b"hel")
    f2 = Fragment(message_id=1, sequence=1, total=2, data=b"lo")
    assert parser.feed(f1) is None
    msg = parser.feed(f2)
    assert msg is not None
    assert msg.data == b"hello"


def test_out_of_order_fragments():
    """Fragments arriving out of order should still reassemble correctly."""
    parser = ProtocolParser()
    f1 = Fragment(message_id=1, sequence=2, total=3, data=b"ld")
    f2 = Fragment(message_id=1, sequence=0, total=3, data=b"wor")
    f3 = Fragment(message_id=1, sequence=1, total=3, data=b"--")
    parser.feed(f1)
    parser.feed(f2)
    msg = parser.feed(f3)
    assert msg is not None
    assert msg.data == b"wor--ld"


def test_multiple_messages():
    parser = ProtocolParser()
    parser.feed(Fragment(message_id=1, sequence=0, total=1, data=b"msg1"))
    parser.feed(Fragment(message_id=2, sequence=0, total=1, data=b"msg2"))
    completed = parser.get_completed()
    assert len(completed) == 2


def test_pending_count():
    parser = ProtocolParser()
    parser.feed(Fragment(message_id=1, sequence=0, total=2, data=b"a"))
    assert parser.pending_count() == 1
    parser.feed(Fragment(message_id=1, sequence=1, total=2, data=b"b"))
    assert parser.pending_count() == 0


def test_parse_frame():
    raw = (1).to_bytes(4, "big") + (0).to_bytes(2, "big") + (1).to_bytes(2, "big") + b"data"
    frag = parse_frame(raw)
    assert frag.message_id == 1
    assert frag.sequence == 0
    assert frag.data == b"data"
