"""Contract Management native contract."""

from __future__ import annotations
from neo.native.native_contract import NativeContract
from neo.types import UInt160


class ContractManagement(NativeContract):
    """Manages contract deployment and updates."""
    
    id: int = -1
    name: str = "ContractManagement"
    
    @property
    def hash(self) -> UInt160:
        return UInt160(bytes.fromhex("fffdc93764dbaddd97c48f252a53ea4643faa3fd")[::-1])
