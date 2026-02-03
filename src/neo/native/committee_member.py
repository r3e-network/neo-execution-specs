"""Neo N3 Committee Member."""

from dataclasses import dataclass


@dataclass
class CommitteeMember:
    """Committee member."""
    public_key: bytes
    votes: int = 0
