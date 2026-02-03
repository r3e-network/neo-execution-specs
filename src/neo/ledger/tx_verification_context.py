"""Neo N3 Transaction Verification Context."""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class TransactionVerificationContext:
    """Context for tx verification."""
    sender_fee: Dict[bytes, int] = field(default_factory=dict)
