"""Neo N3 Transaction Verification Context."""

from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class TransactionVerificationContext:
    """Context for tx verification."""
    sender_fee: dict[bytes, int] = field(default_factory=dict)
