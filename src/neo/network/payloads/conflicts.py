"""Neo N3 Conflicts Attribute."""

from dataclasses import dataclass


@dataclass
class ConflictsAttribute:
    """Conflicts tx attribute."""
    hash: bytes
