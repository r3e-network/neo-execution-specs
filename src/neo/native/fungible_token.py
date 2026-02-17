"""FungibleToken base class for NEP-17 tokens."""

from __future__ import annotations
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any

from neo.types import UInt160
from neo.native.native_contract import NativeContract, CallFlags, StorageItem

# Storage prefixes
PREFIX_TOTAL_SUPPLY = 11
PREFIX_ACCOUNT = 20

@dataclass
class AccountState:
    """Base account state for fungible tokens."""

    balance: int = 0

    def to_bytes(self) -> bytes:
        """Serialize to bytes."""
        return self.balance.to_bytes(32, "little", signed=True)

    @classmethod
    def from_bytes(cls, data: bytes) -> "AccountState":
        """Deserialize from bytes."""
        state = cls()
        if data:
            state.balance = int.from_bytes(data[:32], "little", signed=True)
        return state

class FungibleToken(NativeContract):
    """Base class for NEP-17 compatible native tokens."""

    def __init__(self) -> None:
        super().__init__()
        self._factor = 10**self.decimals

    @property
    @abstractmethod
    def symbol(self) -> str:
        """Token symbol."""
        ...

    @property
    @abstractmethod
    def decimals(self) -> int:
        """Number of decimal places."""
        ...

    @property
    def factor(self) -> int:
        """Factor for converting display value to internal value."""
        return self._factor

    def _native_supported_standards(self, context: Any) -> list[str]:
        return ["NEP-17"]

    def _register_methods(self) -> None:
        """Register NEP-17 methods."""
        super()._register_methods()
        self._register_method("symbol", self._get_symbol, cpu_fee=0, call_flags=CallFlags.NONE)
        self._register_method("decimals", self._get_decimals, cpu_fee=0, call_flags=CallFlags.NONE)
        self._register_method(
            "totalSupply", self.total_supply, cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES
        )
        self._register_method(
            "balanceOf", self.balance_of, cpu_fee=1 << 15, call_flags=CallFlags.READ_STATES
        )
        self._register_method(
            "transfer",
            self.transfer,
            cpu_fee=1 << 17,
            storage_fee=50,
            call_flags=CallFlags.STATES | CallFlags.ALLOW_CALL | CallFlags.ALLOW_NOTIFY,
            manifest_parameter_names=["from", "to", "amount", "data"],
        )

    def _register_events(self) -> None:
        """Register NEP-17 standard events."""
        super()._register_events()
        self._register_event(
            "Transfer",
            [("from", "Hash160"), ("to", "Hash160"), ("amount", "Integer")],
            order=0,
        )

    def _get_symbol(self) -> str:
        return self.symbol

    def _get_decimals(self) -> int:
        return self.decimals

    @property
    def initial_supply(self) -> int:
        """Get the initial supply of the token (before any transfers)."""
        return 0

    def total_supply(self, snapshot: Any = None) -> int:
        """Get the total supply of the token."""
        if snapshot is None:
            return self.initial_supply
        key = self._create_storage_key(PREFIX_TOTAL_SUPPLY)
        item = snapshot.get(key)
        if item is None:
            return self.initial_supply
        return int(item)

    def balance_of(self, snapshot: Any, account: UInt160) -> int:
        """Get the balance of an account."""
        key = self._create_storage_key(PREFIX_ACCOUNT, account.data)
        item = snapshot.get(key)
        if item is None:
            return 0
        state = self._get_account_state(item)
        return state.balance

    def _get_account_state(self, item: StorageItem) -> AccountState:
        """Get account state from storage item. Override for custom state."""
        return AccountState.from_bytes(item.value)

    def _create_account_state(self) -> AccountState:
        """Create a new account state. Override for custom state."""
        return AccountState()

    def mint(
        self, engine: Any, account: UInt160, amount: int, call_on_payment: bool = True
    ) -> None:
        """Mint tokens to an account."""
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        if amount == 0:
            return

        # Update account balance
        key = self._create_storage_key(PREFIX_ACCOUNT, account.data)
        item = engine.snapshot.get_and_change(
            key, lambda: StorageItem(self._create_account_state().to_bytes())
        )
        state = self._get_account_state(item)
        self._on_balance_changing(engine, account, state, amount)
        state.balance += amount
        item.value = state.to_bytes()

        # Update total supply
        supply_key = self._create_storage_key(PREFIX_TOTAL_SUPPLY)
        supply_item = engine.snapshot.get_and_change(supply_key, lambda: StorageItem())
        supply_item.add(amount)

        # Post transfer
        self._post_transfer(engine, None, account, amount, None, call_on_payment)

    def burn(self, engine: Any, account: UInt160, amount: int) -> None:
        """Burn tokens from an account."""
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        if amount == 0:
            return

        key = self._create_storage_key(PREFIX_ACCOUNT, account.data)
        item = engine.snapshot.get_and_change(key)
        if item is None:
            raise ValueError("Insufficient balance")

        state = self._get_account_state(item)
        if state.balance < amount:
            raise ValueError("Insufficient balance")

        self._on_balance_changing(engine, account, state, -amount)

        if state.balance == amount:
            engine.snapshot.delete(key)
        else:
            state.balance -= amount
            item.value = state.to_bytes()

        # Update total supply
        supply_key = self._create_storage_key(PREFIX_TOTAL_SUPPLY)
        supply_item = engine.snapshot.get_and_change(supply_key)
        supply_item.add(-amount)

        # Post transfer
        self._post_transfer(engine, account, None, amount, None, False)

    def transfer(
        self, engine: Any, from_account: UInt160, to_account: UInt160, amount: int, data: Any = None
    ) -> bool:
        """Transfer tokens between accounts."""
        if amount < 0:
            raise ValueError("Amount cannot be negative")

        # Check witness
        if from_account != engine.calling_script_hash:
            if not engine.check_witness(from_account):
                return False

        key_from = self._create_storage_key(PREFIX_ACCOUNT, from_account.data)
        storage_from = engine.snapshot.get_and_change(key_from)

        if amount == 0:
            if storage_from is not None:
                state_from = self._get_account_state(storage_from)
                self._on_balance_changing(engine, from_account, state_from, 0)
        else:
            if storage_from is None:
                return False

            state_from = self._get_account_state(storage_from)
            if state_from.balance < amount:
                return False

            if from_account == to_account:
                self._on_balance_changing(engine, from_account, state_from, 0)
            else:
                self._on_balance_changing(engine, from_account, state_from, -amount)

                if state_from.balance == amount:
                    engine.snapshot.delete(key_from)
                else:
                    state_from.balance -= amount
                    storage_from.value = state_from.to_bytes()

                key_to = self._create_storage_key(PREFIX_ACCOUNT, to_account.data)
                storage_to = engine.snapshot.get_and_change(
                    key_to, lambda: StorageItem(self._create_account_state().to_bytes())
                )
                state_to = self._get_account_state(storage_to)
                self._on_balance_changing(engine, to_account, state_to, amount)
                state_to.balance += amount
                storage_to.value = state_to.to_bytes()

        self._post_transfer(engine, from_account, to_account, amount, data, True)
        return True

    def _on_balance_changing(
        self, engine: Any, account: UInt160, state: AccountState, amount: int
    ) -> None:
        """Called when balance is changing. Override for custom behavior."""
        pass

    def _post_transfer(
        self,
        engine: Any,
        from_account: UInt160 | None,
        to_account: UInt160 | None,
        amount: int,
        data: Any,
        call_on_payment: bool,
    ) -> None:
        """Called after a transfer. Sends notification and calls onNEP17Payment."""
        # Send Transfer notification
        engine.send_notification(self.hash, "Transfer", [from_account, to_account, amount])

        # Call onNEP17Payment if needed
        if call_on_payment and to_account is not None:
            if engine.is_contract(to_account):
                engine.call_contract(to_account, "onNEP17Payment", [from_account, amount, data])
