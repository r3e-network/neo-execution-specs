"""Comprehensive tests for FungibleToken mint/burn/transfer lifecycle.

Covers:
- AccountState serialization round-trip
- mint(): happy path, zero amount, negative amount, total supply update
- burn(): happy path, insufficient balance, full balance deletion
- transfer(): happy path, insufficient funds, self-transfer, zero amount,
  witness check, full balance deletion, notification emission
"""

from __future__ import annotations

import pytest
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from neo.types import UInt160
from neo.native.native_contract import NativeContract, StorageItem, StorageKey
from neo.native.fungible_token import (
    FungibleToken,
    AccountState,
    PREFIX_TOTAL_SUPPLY,
    PREFIX_ACCOUNT,
)


# ---------------------------------------------------------------------------
# Mock infrastructure
# ---------------------------------------------------------------------------

class MockSnapshot:
    """In-memory snapshot supporting get, get_and_change, put, delete."""

    def __init__(self) -> None:
        self._store: Dict[tuple, Any] = {}

    def _key(self, k) -> tuple:
        if isinstance(k, StorageKey):
            return (k.id, k.key)
        return k

    def get(self, key) -> Optional[Any]:
        return self._store.get(self._key(key))

    def get_and_change(self, key, factory: Callable = None) -> Optional[Any]:
        tk = self._key(key)
        if tk not in self._store:
            if factory is None:
                return None
            self._store[tk] = factory()
        return self._store[tk]

    def put(self, key, value) -> None:
        self._store[self._key(key)] = value

    def delete(self, key) -> None:
        self._store.pop(self._key(key), None)


class MockEngine:
    """Minimal engine mock for FungibleToken tests."""

    def __init__(self, snapshot: MockSnapshot) -> None:
        self.snapshot = snapshot
        self.calling_script_hash: Optional[UInt160] = None
        self.notifications: List[Tuple] = []
        self.contract_calls: List[Tuple] = []
        self._witness_ok: bool = True
        self._contracts: set = set()

    def check_witness(self, account: UInt160) -> bool:
        return self._witness_ok

    def send_notification(self, script_hash, event, args) -> None:
        self.notifications.append((script_hash, event, args))

    def is_contract(self, account: UInt160) -> bool:
        return account in self._contracts

    def call_contract(self, hash_, method, args) -> None:
        self.contract_calls.append((hash_, method, args))


class ConcreteToken(FungibleToken):
    """Minimal concrete FungibleToken for testing."""

    @property
    def name(self) -> str:
        return "TestToken"

    @property
    def symbol(self) -> str:
        return "TEST"

    @property
    def decimals(self) -> int:
        return 8


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ALICE = UInt160(b"\x01" * 20)
BOB = UInt160(b"\x02" * 20)


def _fresh_token() -> ConcreteToken:
    """Create a fresh token, clearing the global registry."""
    NativeContract._contracts.clear()
    NativeContract._contracts_by_id.clear()
    NativeContract._contracts_by_name.clear()
    NativeContract._id_counter = 0
    return ConcreteToken()


def _setup():
    """Return (token, snapshot, engine) ready for use."""
    token = _fresh_token()
    snap = MockSnapshot()
    engine = MockEngine(snap)
    return token, snap, engine


# ---------------------------------------------------------------------------
# AccountState tests
# ---------------------------------------------------------------------------

class TestAccountState:
    """AccountState serialization round-trip."""

    def test_default_balance_is_zero(self):
        state = AccountState()
        assert state.balance == 0

    def test_roundtrip_positive(self):
        state = AccountState(balance=1_000_000)
        restored = AccountState.from_bytes(state.to_bytes())
        assert restored.balance == 1_000_000

    def test_roundtrip_zero(self):
        state = AccountState(balance=0)
        restored = AccountState.from_bytes(state.to_bytes())
        assert restored.balance == 0

    def test_from_empty_bytes(self):
        state = AccountState.from_bytes(b"")
        assert state.balance == 0


# ---------------------------------------------------------------------------
# Mint tests
# ---------------------------------------------------------------------------

class TestMint:
    """FungibleToken.mint() lifecycle."""

    def test_mint_increases_balance(self):
        token, snap, engine = _setup()
        token.mint(engine, ALICE, 500)
        assert token.balance_of(snap, ALICE) == 500

    def test_mint_increases_total_supply(self):
        token, snap, engine = _setup()
        token.mint(engine, ALICE, 500)
        assert token.total_supply(snap) == 500

    def test_mint_cumulative(self):
        token, snap, engine = _setup()
        token.mint(engine, ALICE, 300)
        token.mint(engine, ALICE, 200)
        assert token.balance_of(snap, ALICE) == 500
        assert token.total_supply(snap) == 500

    def test_mint_zero_is_noop(self):
        token, snap, engine = _setup()
        token.mint(engine, ALICE, 0)
        assert token.balance_of(snap, ALICE) == 0
        assert len(engine.notifications) == 0

    def test_mint_negative_raises(self):
        token, _snap, engine = _setup()
        with pytest.raises(ValueError, match="negative"):
            token.mint(engine, ALICE, -1)

    def test_mint_emits_transfer_notification(self):
        token, _snap, engine = _setup()
        token.mint(engine, ALICE, 100)
        assert len(engine.notifications) == 1
        _, event, args = engine.notifications[0]
        assert event == "Transfer"
        assert args[0] is None  # from = None (mint)
        assert args[1] == ALICE
        assert args[2] == 100


# ---------------------------------------------------------------------------
# Burn tests
# ---------------------------------------------------------------------------

class TestBurn:
    """FungibleToken.burn() lifecycle."""

    def test_burn_decreases_balance(self):
        token, snap, engine = _setup()
        token.mint(engine, ALICE, 500)
        token.burn(engine, ALICE, 200)
        assert token.balance_of(snap, ALICE) == 300

    def test_burn_decreases_total_supply(self):
        token, snap, engine = _setup()
        token.mint(engine, ALICE, 500)
        token.burn(engine, ALICE, 200)
        assert token.total_supply(snap) == 300

    def test_burn_full_balance_deletes_account(self):
        token, snap, engine = _setup()
        token.mint(engine, ALICE, 500)
        token.burn(engine, ALICE, 500)
        assert token.balance_of(snap, ALICE) == 0

    def test_burn_insufficient_balance_raises(self):
        token, snap, engine = _setup()
        token.mint(engine, ALICE, 100)
        with pytest.raises(ValueError, match="Insufficient"):
            token.burn(engine, ALICE, 200)

    def test_burn_no_account_raises(self):
        token, _snap, engine = _setup()
        with pytest.raises(ValueError, match="Insufficient"):
            token.burn(engine, ALICE, 1)

    def test_burn_zero_is_noop(self):
        token, snap, engine = _setup()
        token.mint(engine, ALICE, 100)
        notif_before = len(engine.notifications)
        token.burn(engine, ALICE, 0)
        assert token.balance_of(snap, ALICE) == 100
        assert len(engine.notifications) == notif_before

    def test_burn_negative_raises(self):
        token, _snap, engine = _setup()
        with pytest.raises(ValueError, match="negative"):
            token.burn(engine, ALICE, -1)


# ---------------------------------------------------------------------------
# Transfer tests
# ---------------------------------------------------------------------------

class TestTransfer:
    """FungibleToken.transfer() lifecycle."""

    def test_transfer_happy_path(self):
        token, snap, engine = _setup()
        token.mint(engine, ALICE, 1000)
        engine.calling_script_hash = ALICE
        result = token.transfer(engine, ALICE, BOB, 300)
        assert result is True
        assert token.balance_of(snap, ALICE) == 700
        assert token.balance_of(snap, BOB) == 300

    def test_transfer_insufficient_funds(self):
        token, snap, engine = _setup()
        token.mint(engine, ALICE, 100)
        engine.calling_script_hash = ALICE
        result = token.transfer(engine, ALICE, BOB, 200)
        assert result is False
        assert token.balance_of(snap, ALICE) == 100

    def test_transfer_no_account_returns_false(self):
        token, _snap, engine = _setup()
        engine.calling_script_hash = ALICE
        result = token.transfer(engine, ALICE, BOB, 100)
        assert result is False

    def test_transfer_self_preserves_balance(self):
        token, snap, engine = _setup()
        token.mint(engine, ALICE, 500)
        engine.calling_script_hash = ALICE
        result = token.transfer(engine, ALICE, ALICE, 200)
        assert result is True
        assert token.balance_of(snap, ALICE) == 500

    def test_transfer_full_balance_deletes_sender(self):
        token, snap, engine = _setup()
        token.mint(engine, ALICE, 500)
        engine.calling_script_hash = ALICE
        result = token.transfer(engine, ALICE, BOB, 500)
        assert result is True
        assert token.balance_of(snap, ALICE) == 0
        assert token.balance_of(snap, BOB) == 500

    def test_transfer_witness_failure(self):
        token, snap, engine = _setup()
        token.mint(engine, ALICE, 500)
        engine._witness_ok = False
        result = token.transfer(engine, ALICE, BOB, 100)
        assert result is False
        assert token.balance_of(snap, ALICE) == 500

    def test_transfer_zero_amount(self):
        token, snap, engine = _setup()
        token.mint(engine, ALICE, 500)
        engine.calling_script_hash = ALICE
        result = token.transfer(engine, ALICE, BOB, 0)
        assert result is True
        assert token.balance_of(snap, ALICE) == 500

    def test_transfer_negative_raises(self):
        token, _snap, engine = _setup()
        engine.calling_script_hash = ALICE
        with pytest.raises(ValueError, match="negative"):
            token.transfer(engine, ALICE, BOB, -1)

    def test_transfer_emits_notification(self):
        token, _snap, engine = _setup()
        token.mint(engine, ALICE, 1000)
        engine.notifications.clear()
        engine.calling_script_hash = ALICE
        token.transfer(engine, ALICE, BOB, 100)
        assert len(engine.notifications) == 1
        _, event, args = engine.notifications[0]
        assert event == "Transfer"
        assert args[0] == ALICE
        assert args[1] == BOB
        assert args[2] == 100

    def test_transfer_calling_script_bypasses_witness(self):
        """When from_account == calling_script_hash, witness check is skipped."""
        token, snap, engine = _setup()
        token.mint(engine, ALICE, 500)
        engine.calling_script_hash = ALICE
        engine._witness_ok = False  # would fail if checked
        result = token.transfer(engine, ALICE, BOB, 100)
        assert result is True
        assert token.balance_of(snap, ALICE) == 400
