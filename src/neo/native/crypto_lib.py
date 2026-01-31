"""CryptoLib native contract."""

from __future__ import annotations
from neo.native.native_contract import NativeContract
from neo.types import UInt160


class CryptoLib(NativeContract):
    """Cryptographic functions."""
    
    id: int = -3
    name: str = "CryptoLib"
    
    @property
    def hash(self) -> UInt160:
        return UInt160(bytes.fromhex("726cb6e0cd8628a1350a611384688911ab75f51b")[::-1])
