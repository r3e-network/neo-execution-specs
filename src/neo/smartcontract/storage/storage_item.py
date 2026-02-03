"""Neo N3 Storage Item."""

from dataclasses import dataclass


@dataclass
class StorageItem:
    """Storage item value."""
    value: bytes = b""
    is_constant: bool = False
