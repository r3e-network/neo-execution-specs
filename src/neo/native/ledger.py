"""Ledger contract."""

from __future__ import annotations
from neo.native.native_contract import NativeContract
from neo.types import UInt160


class LedgerContract(NativeContract):
    """Blockchain ledger access."""
    
    id: int = -4
    name: str = "LedgerContract"
    
    @property
    def hash(self) -> UInt160:
        return UInt160(bytes.fromhex("da65b600f7124ce6c79950c1772a36403104f2be")[::-1])
