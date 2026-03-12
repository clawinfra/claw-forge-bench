"""Protocol parser for framed messages with fragmentation support."""
from dataclasses import dataclass, field


@dataclass
class Fragment:
    message_id: int
    sequence: int
    total: int
    data: bytes


@dataclass
class Message:
    message_id: int
    data: bytes


class ProtocolParser:
    """Parse and reassemble fragmented protocol messages."""

    def __init__(self):
        self.buffer: dict[int, list[Fragment]] = {}
        self.completed: list[Message] = []

    def feed(self, fragment: Fragment) -> Message | None:
        """Feed a fragment. Returns completed Message if all fragments received."""
        msg_id = fragment.message_id

        if msg_id not in self.buffer:
            self.buffer[msg_id] = []

        self.buffer[msg_id].append(fragment)

        if len(self.buffer[msg_id]) == fragment.total:
            # Bug: assembles fragments in arrival order, not sequence order
            fragments = self.buffer.pop(msg_id)
            data = b"".join(f.data for f in fragments)
            msg = Message(message_id=msg_id, data=data)
            self.completed.append(msg)
            return msg

        return None

    def pending_count(self) -> int:
        """Return number of messages with pending fragments."""
        return len(self.buffer)

    def get_completed(self) -> list[Message]:
        """Return all completed messages."""
        return list(self.completed)


def parse_frame(raw: bytes) -> Fragment:
    """Parse a raw frame into a Fragment.

    Frame format: [msg_id:4][seq:2][total:2][data:*]
    """
    if len(raw) < 8:
        raise ValueError("Frame too short")
    msg_id = int.from_bytes(raw[0:4], "big")
    seq = int.from_bytes(raw[4:6], "big")
    total = int.from_bytes(raw[6:8], "big")
    data = raw[8:]
    return Fragment(message_id=msg_id, sequence=seq, total=total, data=data)
