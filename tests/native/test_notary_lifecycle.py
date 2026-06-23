"""Comprehensive tests for Notary deposit/withdraw lifecycle.

Behaviour is pinned to C# Neo v3.10.0 (Neo.SmartContract.Native.Notary):

- Deposit serialization round-trip (StackItem Struct-of-Integers encoding)
- on_nep17_payment: exactly-2-element data, till lower bound (CurrentIndex+2),
  allowedChangeTill (tx.Sender == to), first-deposit minimum, unconditional till
- balance_of / expiration_of lookups
- lock_deposit_until: extend, reject shrink, missing deposit, till lower bound
- withdraw: expired deposit transfers GAS from the Notary, non-expired rejected
- get/set max_not_valid_before_delta with [ValidatorsCount, maxVUB/2] bounds
- initialize seeds the default delta
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pytest

from neo.native.gas_token import GasToken
from neo.native.native_contract import NativeContract, StorageItem, StorageKey
from neo.native.notary import (
    DEFAULT_DEPOSIT_DELTA_TILL,
    DEFAULT_MAX_NOT_VALID_BEFORE_DELTA,
    Deposit,
    Notary,
)
from neo.native.policy import PolicyContract
from neo.types import UInt160

# ---------------------------------------------------------------------------
# Mock infrastructure
# ---------------------------------------------------------------------------


class MockSnapshot:
    """In-memory snapshot that accepts StorageKey objects."""

    def __init__(self) -> None:
        self._store: Dict[tuple, Any] = {}
        self.persisting_block = None

    def _to_tuple(self, key) -> tuple:
        if isinstance(key, StorageKey):
            return (key.id, key.key)
        return key

    def get(self, key) -> Optional[Any]:
        return self._store.get(self._to_tuple(key))

    def get_and_change(self, key, default_factory=None) -> Any:
        """Get existing item or create a new one."""
        k = self._to_tuple(key)
        if k in self._store:
            return self._store[k]
        if default_factory:
            new_item = default_factory()
            self._store[k] = new_item
            return new_item
        return None

    def contains(self, key) -> bool:
        return self._to_tuple(key) in self._store

    def put(self, key, value: Any) -> None:
        self._store[self._to_tuple(key)] = value

    def delete(self, key) -> None:
        tk = self._to_tuple(key)
        self._store.pop(tk, None)


@dataclass
class _MockProtocolSettings:
    initial_gas_distribution: int = 100_000_000 * 10**8
    standby_committee: list = None
    network: int = 0x4F454E
    validators_count: int = 7
    max_valid_until_block_increment: int = 5760

    def __post_init__(self):
        if self.standby_committee is None:
            self.standby_committee = []

    def get_bft_address(self) -> UInt160:
        if self.standby_committee:
            from neo.crypto import hash160

            return UInt160(hash160(self.standby_committee[0]))
        return UInt160(b"\x00" * 20)


@dataclass
class _MockBlock:
    index: int = 0
    transactions: list = field(default_factory=list)
    primary_index: int = 0


@dataclass
class _MockTransaction:
    sender: Optional[UInt160] = None
    signers: list = field(default_factory=list)
    attributes: list = field(default_factory=list)
    system_fee: int = 0
    network_fee: int = 0


class MockEngine:
    """Minimal engine mock for Notary tests."""

    def __init__(
        self,
        snapshot: MockSnapshot,
        is_committee: bool = True,
        witness_accounts: set = None,
    ) -> None:
        self.snapshot = snapshot
        self._is_committee = is_committee
        self._witness_accounts = witness_accounts or set()
        self.protocol_settings = _MockProtocolSettings()
        self.network = self.protocol_settings.network
        self.notifications: list = []
        self.script_container: Optional[_MockTransaction] = None
        self.calling_script_hash: Optional[UInt160] = None

    def check_committee(self) -> bool:
        return self._is_committee

    def check_witness(self, account: UInt160) -> bool:
        return account in self._witness_accounts

    def send_notification(self, script_hash: UInt160, event_name: str, state: Any) -> None:
        self.notifications.append((script_hash, event_name, state))

    def is_contract(self, account: UInt160) -> bool:
        return False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ACCOUNT_A = UInt160(b"\x01" * 20)
ACCOUNT_B = UInt160(b"\x02" * 20)


def _fresh_notary() -> Notary:
    """Create a fresh Notary, clearing global registry."""
    NativeContract._contracts.clear()
    NativeContract._contracts_by_id.clear()
    NativeContract._contracts_by_name.clear()
    NativeContract._id_counter = 0
    return Notary()


def _initialized_notary(block_index: int = 0):
    """Return (notary, snapshot, engine) with storage initialized.

    Registers Notary, GasToken and PolicyContract so the C#-equivalent helper
    lookups (attribute fee) resolve.  LedgerContract is intentionally not
    registered so that ``_current_index`` falls back to the persisting block's
    index (these mocks have no persisted ledger state).
    """
    NativeContract._contracts.clear()
    NativeContract._contracts_by_id.clear()
    NativeContract._contracts_by_name.clear()
    NativeContract._id_counter = 0

    n = Notary()
    gas = GasToken()
    PolicyContract()

    snap = MockSnapshot()
    snap.persisting_block = _MockBlock(index=block_index)
    engine = MockEngine(snap, witness_accounts={ACCOUNT_A, ACCOUNT_B})
    engine.calling_script_hash = gas.hash
    # A default container whose sender matches the deposit owner so that
    # allowedChangeTill is True (caller may freely set `till`).
    engine.script_container = _MockTransaction(sender=ACCOUNT_A)
    gas.initialize(engine)
    n.initialize(engine)
    return n, snap, engine


# ===========================================================================
# Tests: Deposit serialization (C# StackItem Struct-of-Integers)
# ===========================================================================


class TestDepositSerialization:
    """Deposit serialize / deserialize round-trip."""

    def test_round_trip(self):
        d = Deposit(amount=500_000_000, till=1000)
        restored = Deposit.deserialize(d.serialize())
        assert restored.amount == 500_000_000
        assert restored.till == 1000

    def test_round_trip_zero(self):
        d = Deposit(amount=0, till=0)
        restored = Deposit.deserialize(d.serialize())
        assert restored.amount == 0
        assert restored.till == 0

    def test_struct_encoding(self):
        # C# Struct: 0x41, VarInt count=2, then two Integer (0x21) elements.
        d = Deposit(amount=1, till=1)
        data = d.serialize()
        # 0x41 0x02 | 0x21 0x01 0x01 | 0x21 0x01 0x01
        assert data == bytes([0x41, 0x02, 0x21, 0x01, 0x01, 0x21, 0x01, 0x01])

    def test_zero_encodes_empty_bytes(self):
        # Zero values serialize with empty (0-length) integer payloads.
        d = Deposit(amount=0, till=0)
        data = d.serialize()
        assert data == bytes([0x41, 0x02, 0x21, 0x00, 0x21, 0x00])


# ===========================================================================
# Tests: on_nep17_payment (deposit creation)
# ===========================================================================


class TestOnNep17Payment:
    """on_nep17_payment deposit creation and accumulation."""

    def test_create_new_deposit(self):
        n, snap, engine = _initialized_notary()
        n.on_nep17_payment(engine, ACCOUNT_A, 100_000_000, [None, 500])

        assert n.balance_of(snap, ACCOUNT_A) == 100_000_000
        assert n.expiration_of(snap, ACCOUNT_A) == 500

    def test_accumulate_deposit(self):
        n, snap, engine = _initialized_notary()
        n.on_nep17_payment(engine, ACCOUNT_A, 50_000_000, [None, 500])
        n.on_nep17_payment(engine, ACCOUNT_A, 30_000_000, [None, 500])

        assert n.balance_of(snap, ACCOUNT_A) == 80_000_000

    def test_extend_till_on_deposit(self):
        # allowedChangeTill (tx.Sender == to) -> till is set unconditionally.
        n, snap, engine = _initialized_notary()
        n.on_nep17_payment(engine, ACCOUNT_A, 10_000_000, [None, 100])
        n.on_nep17_payment(engine, ACCOUNT_A, 10_000_000, [None, 200])

        assert n.expiration_of(snap, ACCOUNT_A) == 200

    def test_till_below_previous_rejected(self):
        # C# raises when till < deposit.Till (it does not silently keep max).
        n, snap, engine = _initialized_notary()
        n.on_nep17_payment(engine, ACCOUNT_A, 10_000_000, [None, 200])
        with pytest.raises(ValueError, match="previous value"):
            n.on_nep17_payment(engine, ACCOUNT_A, 10_000_000, [None, 100])
        # till unchanged
        assert n.expiration_of(snap, ACCOUNT_A) == 200

    def test_deposit_to_different_account(self):
        # to = ACCOUNT_B, sender = ACCOUNT_A -> not allowedChangeTill, so a
        # first deposit defaults till to currentHeight + DEFAULT_DEPOSIT_DELTA_TILL.
        n, snap, engine = _initialized_notary()
        n.on_nep17_payment(engine, ACCOUNT_A, 10_000_000, [ACCOUNT_B, 300])

        assert n.balance_of(snap, ACCOUNT_B) == 10_000_000
        assert n.balance_of(snap, ACCOUNT_A) == 0
        assert n.expiration_of(snap, ACCOUNT_B) == DEFAULT_DEPOSIT_DELTA_TILL

    def test_till_below_lower_bound_raises(self):
        # till must be >= CurrentIndex + 2.
        n, snap, engine = _initialized_notary(block_index=100)
        with pytest.raises(ValueError, match="chain's height"):
            n.on_nep17_payment(engine, ACCOUNT_A, 10_000_000, [None, 101])

    def test_data_must_have_two_elements(self):
        n, snap, engine = _initialized_notary()
        with pytest.raises(ValueError, match="array of 2 elements"):
            n.on_nep17_payment(engine, ACCOUNT_A, 10_000_000, [500])

    def test_only_gas_accepted(self):
        n, snap, engine = _initialized_notary()
        engine.calling_script_hash = UInt160(b"\x09" * 20)
        with pytest.raises(ValueError, match="GAS"):
            n.on_nep17_payment(engine, ACCOUNT_A, 10_000_000, [None, 500])


# ===========================================================================
# Tests: balance_of / expiration_of
# ===========================================================================


class TestBalanceAndExpiration:
    """balance_of and expiration_of lookups."""

    def test_balance_of_no_deposit(self):
        n, snap, engine = _initialized_notary()
        assert n.balance_of(snap, ACCOUNT_A) == 0

    def test_expiration_of_no_deposit(self):
        n, snap, engine = _initialized_notary()
        assert n.expiration_of(snap, ACCOUNT_A) == 0

    def test_balance_after_deposit(self):
        n, snap, engine = _initialized_notary()
        n.on_nep17_payment(engine, ACCOUNT_A, 42_000_000, [None, 100])
        assert n.balance_of(snap, ACCOUNT_A) == 42_000_000

    def test_expiration_after_deposit(self):
        n, snap, engine = _initialized_notary()
        n.on_nep17_payment(engine, ACCOUNT_A, 1_000_000, [None, 777])
        assert n.expiration_of(snap, ACCOUNT_A) == 777


# ===========================================================================
# Tests: lock_deposit_until
# ===========================================================================


class TestLockDepositUntil:
    """lock_deposit_until extend and rejection."""

    def test_extend_lock(self):
        n, snap, engine = _initialized_notary()
        n.on_nep17_payment(engine, ACCOUNT_A, 10_000_000, [None, 100])
        result = n.lock_deposit_until(engine, ACCOUNT_A, 200)
        assert result is True
        assert n.expiration_of(snap, ACCOUNT_A) == 200

    def test_reject_shrink(self):
        n, snap, engine = _initialized_notary()
        n.on_nep17_payment(engine, ACCOUNT_A, 10_000_000, [None, 200])
        result = n.lock_deposit_until(engine, ACCOUNT_A, 100)
        assert result is False
        assert n.expiration_of(snap, ACCOUNT_A) == 200

    def test_reject_below_lower_bound(self):
        # till < CurrentIndex + 2 -> rejected.
        n, snap, engine = _initialized_notary(block_index=100)
        n.on_nep17_payment(engine, ACCOUNT_A, 10_000_000, [None, 500])
        result = n.lock_deposit_until(engine, ACCOUNT_A, 101)
        assert result is False

    def test_no_deposit_returns_false(self):
        n, snap, engine = _initialized_notary()
        result = n.lock_deposit_until(engine, ACCOUNT_A, 100)
        assert result is False

    def test_witness_required(self):
        n, snap, engine = _initialized_notary()
        n.on_nep17_payment(engine, ACCOUNT_A, 10_000_000, [None, 100])
        engine_no_witness = MockEngine(snap, witness_accounts=set())
        with pytest.raises(PermissionError):
            n.lock_deposit_until(engine_no_witness, ACCOUNT_A, 200)


# ===========================================================================
# Tests: withdraw (transfers GAS from the Notary, mirroring C#)
# ===========================================================================


def _fund_notary_gas(notary: Notary, gas: GasToken, engine: MockEngine, amount: int) -> None:
    """Credit the Notary contract's real GAS balance (deposits back this)."""
    gas.mint(engine, notary.hash, amount, False)


class TestWithdraw:
    """withdraw with expiration check + GAS transfer from the Notary."""

    def _prepare(self):
        """Deposit at height 0 (till must be >= 2), then advance the chain."""
        n, snap, engine = _initialized_notary(block_index=0)
        gas = NativeContract.get_contract_by_name("GasToken")
        # The Notary can witness itself for the internal transfer.
        engine._witness_accounts.add(n.hash)
        return n, snap, engine, gas

    def test_withdraw_expired_deposit(self):
        n, snap, engine, gas = self._prepare()
        n.on_nep17_payment(engine, ACCOUNT_A, 50_000_000, [None, 100])
        _fund_notary_gas(n, gas, engine, 50_000_000)
        engine.calling_script_hash = n.hash
        snap.persisting_block.index = 200  # advance past till=100

        result = n.withdraw(engine, ACCOUNT_A, ACCOUNT_B)
        assert result is True
        assert n.balance_of(snap, ACCOUNT_A) == 0
        assert gas.balance_of(snap, ACCOUNT_B) == 50_000_000

    def test_withdraw_non_expired_rejected(self):
        n, snap, engine, gas = self._prepare()
        n.on_nep17_payment(engine, ACCOUNT_A, 50_000_000, [None, 100])
        snap.persisting_block.index = 50  # before till=100

        result = n.withdraw(engine, ACCOUNT_A, ACCOUNT_B)
        assert result is False
        assert n.balance_of(snap, ACCOUNT_A) == 50_000_000

    def test_withdraw_no_deposit_returns_false(self):
        n, snap, engine, gas = self._prepare()
        snap.persisting_block.index = 200
        result = n.withdraw(engine, ACCOUNT_A, ACCOUNT_B)
        assert result is False

    def test_withdraw_to_self(self):
        n, snap, engine, gas = self._prepare()
        n.on_nep17_payment(engine, ACCOUNT_A, 10_000_000, [None, 100])
        _fund_notary_gas(n, gas, engine, 10_000_000)
        engine.calling_script_hash = n.hash
        snap.persisting_block.index = 200

        result = n.withdraw(engine, ACCOUNT_A, None)
        assert result is True
        assert n.balance_of(snap, ACCOUNT_A) == 0
        assert gas.balance_of(snap, ACCOUNT_A) == 10_000_000

    def test_withdraw_witness_required(self):
        n, snap, engine, gas = self._prepare()
        n.on_nep17_payment(engine, ACCOUNT_A, 10_000_000, [None, 100])
        engine_no_witness = MockEngine(snap, witness_accounts=set())
        engine_no_witness.snapshot.persisting_block = _MockBlock(index=200)
        with pytest.raises(PermissionError):
            n.withdraw(engine_no_witness, ACCOUNT_A, ACCOUNT_B)


# ===========================================================================
# Tests: max_not_valid_before_delta
# ===========================================================================


class TestMaxNotValidBeforeDelta:
    """get/set max_not_valid_before_delta with [ValidatorsCount, maxVUB/2] bounds."""

    def test_get_default_delta(self):
        n, snap, engine = _initialized_notary()
        delta = n.get_max_not_valid_before_delta(snap)
        assert delta == DEFAULT_MAX_NOT_VALID_BEFORE_DELTA

    def test_set_delta(self):
        # Within [validators_count=7, maxVUB(5760)/2=2880].
        n, snap, engine = _initialized_notary()
        n.set_max_not_valid_before_delta(engine, 200)
        assert n.get_max_not_valid_before_delta(snap) == 200

    def test_set_delta_below_validators_count_raises(self):
        n, snap, engine = _initialized_notary()
        with pytest.raises(ValueError, match="less than"):
            n.set_max_not_valid_before_delta(engine, 6)

    def test_set_delta_above_half_max_vub_raises(self):
        n, snap, engine = _initialized_notary()
        with pytest.raises(ValueError, match="more than"):
            n.set_max_not_valid_before_delta(engine, 3000)

    def test_set_delta_committee_only(self):
        n, snap, engine = _initialized_notary()
        engine_no_committee = MockEngine(snap, is_committee=False)
        with pytest.raises(PermissionError, match="Committee"):
            n.set_max_not_valid_before_delta(engine_no_committee, 200)
