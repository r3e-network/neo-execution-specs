"""Neo N3 Notification - Contract event notifications."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class NotifyEventArgs:
    """Notification event arguments."""
    script_hash: bytes
    event_name: str
    state: list[Any]
