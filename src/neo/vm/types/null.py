"""Null stack item."""

from __future__ import annotations
from neo.vm.types.stack_item import StackItem, StackItemType


class Null(StackItem):
    """Null value singleton."""
    
    _instance: Null | None = None
    
    def __new__(cls) -> Null:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def type(self) -> StackItemType:
        return StackItemType.ANY
    
    @property
    def is_null(self) -> bool:
        return True

    def get_boolean(self) -> bool:
        return False


NULL = Null()
