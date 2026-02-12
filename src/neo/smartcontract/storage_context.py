"""Neo N3 Storage Context.

Reference: Neo.SmartContract.StorageContext
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.types import UInt160


@dataclass
class StorageContext:
    """Storage context for contract storage access.

    In Neo N3, storage keys are prefixed with the contract's integer ID
    (int32 little-endian), NOT the script hash.  The ``id`` field mirrors
    ``ContractState.Id`` from the C# reference implementation.

    Attributes:
        id: The contract's integer ID used as storage key prefix.
        script_hash: The contract's script hash (kept for syscall routing).
        is_read_only: Whether this context is read-only.
    """
    id: int = 0
    script_hash: "UInt160 | None" = field(default=None)
    is_read_only: bool = False

    def as_read_only(self) -> "StorageContext":
        """Create a read-only copy of this context."""
        return StorageContext(
            id=self.id,
            script_hash=self.script_hash,
            is_read_only=True
        )
