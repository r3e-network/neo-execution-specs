"""Neo N3 Execution Context State."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ExecutionContextState:
    """State for execution context."""
    script_hash: bytes = field(default_factory=lambda: bytes(20))
    call_flags: int = 0x0F
    contract: Optional[object] = None
