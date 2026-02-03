"""Neo N3 Interop descriptor."""

from dataclasses import dataclass
from typing import Callable


@dataclass
class InteropDescriptor:
    """Syscall descriptor."""
    name: str
    hash: int
    handler: Callable
    price: int = 0
