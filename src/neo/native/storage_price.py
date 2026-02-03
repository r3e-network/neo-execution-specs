"""Neo N3 Storage Price."""

from dataclasses import dataclass


@dataclass
class StoragePrice:
    """Storage pricing."""
    price_per_byte: int = 100000
