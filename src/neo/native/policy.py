"""Policy contract."""

from __future__ import annotations
from neo.native.native_contract import NativeContract
from neo.types import UInt160


class PolicyContract(NativeContract):
    """Network policy settings."""
    
    id: int = -7
    name: str = "PolicyContract"
    
    # Default values
    max_transactions_per_block: int = 512
    fee_per_byte: int = 1000
    
    @property
    def hash(self) -> UInt160:
        return UInt160(bytes.fromhex("cc5e4edd9f5f8dba8bb65734541df7a1c081c67b")[::-1])
