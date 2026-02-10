"""Comprehensive tests for Notary deposit/withdraw lifecycle.

Covers:
- Deposit serialization round-trip
- on_nep17_payment: deposit creation, amount accumulation, till extension
- balance_of / expiration_of lookups
- lock_deposit_until: extend, reject shrink, missing deposit
- withdraw: expired deposit, non-expired rejection, witness check
- get/set max_not_valid_before_delta with committee check
- initialize on genesis
"""

from __future__ import annotations

import pytest
from dataclasses import dataclass
from typing import Any, Dict, Optional

from neo.types import UInt160
from neo.native.notary import (
    Notary,
    Deposit,
    DEFAULT_MAX_NOT_VALID_BEFORE_DELTA,
    DEFAULT_DEPOSIT_DELTA_TILL,
    PREFIX_DEPOSIT,
    PREFIX_MAX_NOT_VALID_BEFORE_DELTA,
)
from neo.native.native_contract import NativeContract, StorageItem, StorageKey


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

    def contains(self, key) -> bool:
        return self._to_tuple(key) in self._store

    def put(self, key, value) -> None:
        self._store[self._to_tuple(key)] = value

    def delete(self, key) -> None:
        tk = self._to_tuple(key)
        self._store.pop(tk, None)


@dataclass
class _MockBlock:
    index: int = 0


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

    def check_committee(self) -> bool:
        return self._is_committee

    def check_witness(self, account: UInt160) -> bool:
        return account in self._witness_accounts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ACCOUNT_A = UInt160(b'\x01' * 20)
ACCOUNT_B = UInt160(b'\x02' * 20)


def _fresh_notary() -> Notary:
    """Create a fresh Notary, clearing global registry."""
    NativeContract._contracts.clear()
    NativeContract._contracts_by_id.clear()
    NativeContract._contracts_by_name.clear()
    NativeContract._id_counter = 0
    return Notary()


def _initialized_notary(block_index: int = 0):
    """Return (notary, snapshot, engine) with storage initialized."""
    n = _fresh_notary()
    snap = MockSnapshot()
    snap.persisting_block = _MockBlock(index=block_index)
    engine = MockEngine(snap, witness_accounts={ACCOUNT_A, ACCOUNT_B})
    n.initialize(engine)
    return n, snap, engine


# ===========================================================================
# Tests: Deposit serialization
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

    def test_serialize_length(self):
        d = Deposit(amount=1, till=1)
        data = d.serialize()
        # 8 bytes amount + 4 bytes till = 12
        assert len(data) == 12


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
        n, snap, engine = _initialized_notary()
        n.on_nep17_payment(engine, ACCOUNT_A, 10_000_000, [None, 100])
        n.on_nep17_payment(engine, ACCOUNT_A, 10_000_000, [None, 200])

        assert n.expiration_of(snap, ACCOUNT_A) == 200

    def test_till_not_reduced_on_deposit(self):
        n, snap, engine = _initialized_notary()
        n.on_nep17_payment(engine, ACCOUNT_A, 10_000_000, [None, 200])
        n.on_nep17_payment(engine, ACCOUNT_A, 10_000_000, [None, 100])

        # till should stay at 200 (higher value wins)
        assert n.expiration_of(snap, ACCOUNT_A) == 200

    def test_deposit_to_different_account(self):
        n, snap, engine = _initialized_notary()
        n.on_nep17_payment(engine, ACCOUNT_A, 10_000_000, [ACCOUNT_B, 300])

        assert n.balance_of(snap, ACCOUNT_B) == 10_000_000
        assert n.balance_of(snap, ACCOUNT_A) == 0

    def test_zero_amount_raises(self):
        n, snap, engine = _initialized_notary()
        with pytest.raises(ValueError, match="positive"):
            n.on_nep17_payment(engine, ACCOUNT_A, 0, [None, 100])

    def test_negative_amount_raises(self):
        n, snap, engine = _initialized_notary()
        with pytest.raises(ValueError, match="positive"):
            n.on_nep17_payment(engine, ACCOUNT_A, -1, [None, 100])


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

    def test_no_deposit_returns_false(self):
        n, snap, engine = _initialized_notary()
        result = n.lock_deposit_until(engine, ACCOUNT_A, 100)
        assert result is False

    def test_witness_required(self):
        n, snap, engine = _initialized_notary()
        n.on_nep17_payment(engine, ACCOUNT_A, 10_000_000, [None, 100])
        # Create engine without witness for ACCOUNT_A
        engine_no_witness = MockEngine(snap, witness_accounts=set())
        with pytest.raises(PermissionError):
            n.lock_deposit_until(engine_no_witness, ACCOUNT_A, 200)


# ===========================================================================
# Tests: withdraw
# ===========================================================================

class TestWithdraw:
    """withdraw with expiration check."""

    def test_withdraw_expired_deposit(self):
        n, snap, engine = _initialized_notary(block_index=200)
        n.on_nep17_payment(engine, ACCOUNT_A, 50_000_000, [None, 100])

        # Block index 200 > till 100, so withdrawal should succeed
        result = n.withdraw(engine, ACCOUNT_A, ACCOUNT_B)
        assert result is True
        # Deposit should be removed
        assert n.balance_of(snap, ACCOUNT_A) == 0

    def test_withdraw_non_expired_rejected(self):
        n, snap, engine = _initialized_notary(block_index=50)
        n.on_nep17_payment(engine, ACCOUNT_A, 50_000_000, [None, 100])

        # Block index 50 < till 100, so withdrawal should fail
        result = n.withdraw(engine, ACCOUNT_A, ACCOUNT_B)
        assert result is False
        # Deposit should remain
        assert n.balance_of(snap, ACCOUNT_A) == 50_000_000

    def test_withdraw_no_deposit_returns_false(self):
        n, snap, engine = _initialized_notary(block_index=200)
        result = n.withdraw(engine, ACCOUNT_A, ACCOUNT_B)
        assert result is False

    def test_withdraw_to_self(self):
        n, snap, engine = _initialized_notary(block_index=200)
        n.on_nep17_payment(engine, ACCOUNT_A, 10_000_000, [None, 100])
        result = n.withdraw(engine, ACCOUNT_A, None)
        assert result is True
        assert n.balance_of(snap, ACCOUNT_A) == 0

    def test_withdraw_witness_required(self):
        n, snap, engine = _initialized_notary(block_index=200)
        n.on_nep17_payment(engine, ACCOUNT_A, 10_000_000, [None, 100])
        engine_no_witness = MockEngine(snap, witness_accounts=set())
        engine_no_witness.snapshot.persisting_block = _MockBlock(index=200)
        with pytest.raises(PermissionError):
            n.withdraw(engine_no_witness, ACCOUNT_A, ACCOUNT_B)


# ===========================================================================
# Tests: max_not_valid_before_delta
# ===========================================================================

class TestMaxNotValidBeforeDelta:
    """get/set max_not_valid_before_delta with committee check."""

    def test_get_default_delta(self):
        n, snap, engine = _initialized_notary()
        delta = n.get_max_not_valid_before_delta(snap)
        assert delta == DEFAULT_MAX_NOT_VALID_BEFORE_DELTA

    def test_set_delta(self):
        n, snap, engine = _initialized_notary()
        n.set_max_not_valid_before_delta(engine, 200)
        assert n.get_max_not_valid_before_delta(snap) == 200

    def test_set_delta_zero_raises(self):
        n, snap, engine = _initialized_notary()
        with pytest.raises(ValueError, match="positive"):
            n.set_max_not_valid_before_delta(engine, 0)

    def test_set_delta_committee_only(self):
        n, snap, engine = _initialized_notary()
        engine_no_committee = MockEngine(snap, is_committee=False)
        with pytest.raises(PermissionError, match="Committee"):
            n.set_max_not_valid_before_delta(engine_no_committee, 200)
