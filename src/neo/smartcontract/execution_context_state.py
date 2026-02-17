"""Neo N3 Execution Context State."""

from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class ExecutionContextState:
    """State for execution context."""
    script_hash: bytes = field(default_factory=lambda: bytes(20))
    call_flags: int = 0x0F
    contract: object | None = None
