"""Neo N3 High Priority Attribute."""

from dataclasses import dataclass


@dataclass
class HighPriorityAttribute:
    """High priority tx attribute."""
    type: int = 0x01
