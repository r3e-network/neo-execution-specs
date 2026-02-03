"""Neo N3 Execution result."""

from dataclasses import dataclass
from typing import List, Any


@dataclass
class ExecutionResult:
    """Contract execution result."""
    state: int = 0
    gas_consumed: int = 0
    stack: List[Any] = None
