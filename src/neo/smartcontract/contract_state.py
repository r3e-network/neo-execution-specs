"""Neo N3 Contract State."""

from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class ContractState:
    """Deployed contract state."""
    id: int = 0
    update_counter: int = 0
    hash: bytes = field(default_factory=lambda: bytes(20))
    nef: bytes = b""
    manifest: dict = field(default_factory=dict)
