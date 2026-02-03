"""Neo N3 Diagnostic info."""

from dataclasses import dataclass


@dataclass
class Diagnostic:
    """Execution diagnostic."""
    gas_consumed: int = 0
    storage_changes: int = 0
