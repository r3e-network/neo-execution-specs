"""Neo N3 Log event."""

from dataclasses import dataclass


@dataclass
class LogEventArgs:
    """Log event."""
    script_hash: bytes
    message: str
