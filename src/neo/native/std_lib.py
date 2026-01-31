"""StdLib native contract."""

from __future__ import annotations
from neo.native.native_contract import NativeContract
from neo.types import UInt160


class StdLib(NativeContract):
    """Standard library functions."""
    
    id: int = -2
    name: str = "StdLib"
    
    @property
    def hash(self) -> UInt160:
        return UInt160(bytes.fromhex("acce6fd80d44e1796aa0c2c625e9e4e0ce39efc0")[::-1])
