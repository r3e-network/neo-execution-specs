"""Neo N3 Contract State."""

from dataclasses import dataclass, field
from typing import Optional, Dict


@dataclass
class ContractState:
    """Deployed contract state."""
    id: int = 0
    update_counter: int = 0
    hash: bytes = field(default_factory=lambda: bytes(20))
    nef: bytes = b""
    manifest: Dict = field(default_factory=dict)
