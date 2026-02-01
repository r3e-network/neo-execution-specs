"""Notary native contract for multisignature transaction assistance.

Reference: Neo.SmartContract.Native.Notary
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional

from neo.types import UInt160
from neo.native.native_contract import NativeContract, CallFlags, StorageKey, StorageItem


# Storage prefixes
PREFIX_DEPOSIT = 1
PREFIX_MAX_NOT_VALID_BEFORE_DELTA = 10

# Default values
DEFAULT_MAX_NOT_VALID_BEFORE_DELTA = 140
DEFAULT_DEPOSIT_DELTA_TILL = 5760


@dataclass
class Deposit:
    """Notary deposit data."""
    amount: int = 0
    till: int = 0
    
    def serialize(self) -> bytes:
        """Serialize deposit to bytes."""
        result = bytearray()
        # Amount as variable-length integer
        amount_bytes = self.amount.to_bytes(8, 'little')
        result.extend(amount_bytes)
        # Till as 4-byte integer
        result.extend(self.till.to_bytes(4, 'little'))
        return bytes(result)
    
    @classmethod
    def deserialize(cls, data: bytes) -> Deposit:
        """Deserialize deposit from bytes."""
        amount = int.from_bytes(data[:8], 'little')
        till = int.from_bytes(data[8:12], 'little')
        return cls(amount=amount, till=till)


class Notary(NativeContract):
    """Notary native contract for multisignature transaction assistance.
    
    Provides functionality for:
    - GAS deposits for notary services
    - Signature verification for notary nodes
    - Managing NotValidBefore delta settings
    """
    
    def __init__(self) -> None:
        self._storage: Dict[bytes, StorageItem] = {}
        super().__init__()
    
    @property
    def name(self) -> str:
        return "Notary"
    
    def _register_methods(self) -> None:
        """Register Notary contract methods."""
        super()._register_methods()
        
        self._register_method("verify", self.verify,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("balanceOf", self.balance_of,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("expirationOf", self.expiration_of,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("lockDepositUntil", self.lock_deposit_until,
                            cpu_fee=1 << 15, call_flags=CallFlags.STATES)
        self._register_method("withdraw", self.withdraw,
                            cpu_fee=1 << 15, call_flags=CallFlags.ALL)
        self._register_method("getMaxNotValidBeforeDelta", 
                            self.get_max_not_valid_before_delta,
                            cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES)
        self._register_method("setMaxNotValidBeforeDelta",
                            self.set_max_not_valid_before_delta,
                            cpu_fee=1 << 15, call_flags=CallFlags.STATES)
        self._register_method("onNEP17Payment", self.on_nep17_payment,
                            cpu_fee=1 << 15, call_flags=CallFlags.STATES)
