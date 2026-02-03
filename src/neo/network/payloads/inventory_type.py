"""Neo N3 Inventory Type."""

from enum import IntEnum


class InventoryType(IntEnum):
    """Inventory types."""
    TX = 0x2b
    BLOCK = 0x2c
    EXTENSIBLE = 0x2e
