"""Neo N3 Storage Context.

Reference: Neo.SmartContract.StorageContext
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.types import UInt160


@dataclass
class StorageContext:
    """Storage context for contract storage access.
    
    Attributes:
        script_hash: The contract's script hash.
        is_read_only: Whether this context is read-only.
    """
    script_hash: "UInt160"
    is_read_only: bool = False
    
    def as_read_only(self) -> "StorageContext":
        """Create a read-only copy of this context."""
        return StorageContext(
            script_hash=self.script_hash,
            is_read_only=True
        )
