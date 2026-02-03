"""Neo N3 Capabilities."""

from dataclasses import dataclass
from enum import IntEnum


class NodeCapabilityType(IntEnum):
    """Node capability types."""
    TCP_SERVER = 0x01
    WS_SERVER = 0x02
    FULL_NODE = 0x10
