"""Neo N3 Notification - Contract event notifications."""

from dataclasses import dataclass
from typing import Any, List


@dataclass
class NotifyEventArgs:
    """Notification event arguments."""
    script_hash: bytes
    event_name: str
    state: List[Any]
