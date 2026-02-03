"""Neo N3 Transaction Router."""

from typing import Callable, Optional


class TransactionRouter:
    """Route transactions."""
    
    def __init__(self):
        self._handlers = []
    
    def register(self, handler: Callable) -> None:
        """Register handler."""
        self._handlers.append(handler)
