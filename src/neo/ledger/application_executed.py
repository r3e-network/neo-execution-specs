"""Neo N3 Application Executed."""

from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class ApplicationExecuted:
    """Execution result event."""
    tx_hash: bytes
    trigger: int
    state: int
    gas_consumed: int
    stack: List = field(default_factory=list)
    notifications: List = field(default_factory=list)
