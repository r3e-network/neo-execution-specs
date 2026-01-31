"""Oracle contract."""

from __future__ import annotations
from neo.native.native_contract import NativeContract
from neo.types import UInt160


class OracleContract(NativeContract):
    """Oracle service for external data."""
    
    id: int = -9
    name: str = "OracleContract"
    
    @property
    def hash(self) -> UInt160:
        return UInt160(bytes.fromhex("fe924b7cfe89ddd271abaf7210a80a7e11178758")[::-1])
