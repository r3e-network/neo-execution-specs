"""Neo N3 Execution result."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExecutionResult:
    """Contract execution result."""

    state: int = 0
    gas_consumed: int = 0
    stack: list[Any] = field(default_factory=list)
