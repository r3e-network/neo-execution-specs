"""Neo N3 Candidate State."""

from dataclasses import dataclass


@dataclass
class CandidateState:
    """Validator candidate."""
    registered: bool = True
    votes: int = 0
