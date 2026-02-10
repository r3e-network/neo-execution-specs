"""Treasury native contract (ID -11, introduced in HF_Faun)."""

from __future__ import annotations
from typing import Any

from neo.native.native_contract import NativeContract, CallFlags, StorageItem


# Storage prefixes
PREFIX_BALANCE = 20


class TreasuryContract(NativeContract):
    """Manages the network treasury balance.

    Introduced in Hardfork_Faun. Provides a minimal interface for
    distributing GAS from the treasury pool and querying its balance.
    """

    def __init__(self) -> None:
        super().__init__()

    @property
    def name(self) -> str:
        return "Treasury"

    def _register_methods(self) -> None:
        """Register treasury methods."""
        super()._register_methods()
        self._register_method(
            "distribute",
            self.distribute,
            cpu_fee=1 << 15,
            call_flags=CallFlags.STATES,
        )
        self._register_method(
            "getBalance",
            self.get_balance,
            cpu_fee=1 << 15,
            call_flags=CallFlags.READ_STATES,
        )

    def get_balance(self, snapshot: Any) -> int:
        """Get current treasury balance.

        Args:
            snapshot: Storage snapshot.

        Returns:
            Balance in datoshi.
        """
        key = self._create_storage_key(PREFIX_BALANCE)
        item = snapshot.get(key)
        return int(item) if item else 0

    def distribute(self, engine: Any, amount: int) -> bool:
        """Distribute GAS from the treasury.

        Committee-only operation. Decreases the treasury balance by
        *amount* datoshi.

        Args:
            engine: Application engine.
            amount: Amount in datoshi to distribute (must be > 0).

        Returns:
            True on success.

        Raises:
            ValueError: If amount is non-positive or exceeds balance.
            PermissionError: If caller lacks committee authority.
        """
        if amount <= 0:
            raise ValueError(f"Amount must be positive, got {amount}")
        if not engine.check_committee():
            raise PermissionError("Committee signature required")

        key = self._create_storage_key(PREFIX_BALANCE)
        item = engine.snapshot.get_and_change(key, lambda: StorageItem())
        current = int(item) if item.value else 0

        if amount > current:
            raise ValueError(
                f"Insufficient treasury balance: {current}, requested {amount}"
            )

        item.set(current - amount)
        return True

    def initialize(self, engine: Any) -> None:
        """Initialize treasury on genesis with zero balance."""
        key = self._create_storage_key(PREFIX_BALANCE)
        item = StorageItem()
        item.set(0)
        engine.snapshot.add(key, item)
