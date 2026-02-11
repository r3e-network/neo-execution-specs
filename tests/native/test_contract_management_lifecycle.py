"""Comprehensive tests for ContractManagement deploy/update/destroy lifecycle.

Covers:
- ContractState serialization round-trip
- deploy: happy path, empty NEF/manifest, duplicate deploy
- update: NEF only, manifest only, both, counter increment
- destroy: cleanup of contract + hash key + storage
- get_contract / get_contract_by_id lookups
- has_method with manifest ABI inspection
- set/get minimum deployment fee with committee check
- initialize on genesis
"""

from __future__ import annotations

import json
import pytest
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from neo.types import UInt160
from neo.native.contract_management import (
    ContractManagement,
    ContractState,
    DEFAULT_MINIMUM_DEPLOYMENT_FEE,
)
from neo.native.native_contract import NativeContract, StorageKey


# ---------------------------------------------------------------------------
# Mock infrastructure
# ---------------------------------------------------------------------------

class MockSnapshot:
    """In-memory snapshot that accepts StorageKey objects."""

    def __init__(self) -> None:
        self._store: Dict[tuple, Any] = {}
        self._notifications: List = []

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

    def add(self, key, value) -> None:
        tk = self._to_tuple(key)
        if tk in self._store:
            raise KeyError("Key already exists")
        self._store[tk] = value

    def delete(self, key) -> None:
        tk = self._to_tuple(key)
        self._store.pop(tk, None)

    def get_and_change(self, key, factory=None):
        tk = self._to_tuple(key)
        val = self._store.get(tk)
        if val is None and factory is not None:
            val = factory()
            self._store[tk] = val
        return val

    def delete_contract_storage(self, contract_id: int) -> None:
        """Remove all storage entries for a contract ID."""
        to_remove = [k for k in self._store if isinstance(k, tuple) and k[0] == contract_id]
        for k in to_remove:
            del self._store[k]


class MockEngine:
    """Minimal engine mock for ContractManagement tests."""

    def __init__(
        self,
        snapshot: MockSnapshot,
        sender: UInt160 = None,
        calling_hash: UInt160 = None,
        is_committee: bool = True,
        storage_price: int = 100000,
    ) -> None:
        self.snapshot = snapshot
        self.storage_price = storage_price
        self._sender = sender or UInt160(b'\x01' * 20)
        self._calling_hash = calling_hash
        self._is_committee = is_committee
        self.script_container = _MockTx(self._sender)
        self.notifications: List = []
        self.fees_added: List[int] = []

    @property
    def calling_script_hash(self) -> UInt160:
        return self._calling_hash

    def check_committee(self) -> bool:
        return self._is_committee

    def add_fee(self, fee: int) -> None:
        self.fees_added.append(fee)

    def send_notification(self, contract_hash, event_name, state) -> None:
        self.notifications.append((contract_hash, event_name, state))


@dataclass
class _MockTx:
    sender: UInt160


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_manifest(name: str = "TestContract", methods: list = None) -> bytes:
    """Build a minimal manifest JSON."""
    if methods is None:
        methods = [{"name": "main", "parameters": [], "returntype": "Void", "safe": False}]
    manifest = {
        "name": name,
        "abi": {"methods": methods, "events": []},
        "groups": [],
        "permissions": [],
        "trusts": [],
        "extra": None,
    }
    return json.dumps(manifest).encode("utf-8")


def _make_nef(size: int = 64) -> bytes:
    """Build a minimal NEF-like byte blob with a 4-byte checksum tail."""
    body = b'\x00' * (size - 4)
    checksum = (0x12345678).to_bytes(4, 'little')
    return body + checksum


def _fresh_cm() -> ContractManagement:
    """Create a fresh ContractManagement, clearing global registry first."""
    NativeContract._contracts.clear()
    NativeContract._contracts_by_id.clear()
    NativeContract._contracts_by_name.clear()
    NativeContract._id_counter = 0
    return ContractManagement()


# ===========================================================================
# Tests
# ===========================================================================

class TestContractStateSerialization:
    """ContractState to_bytes / from_bytes round-trip."""

    def test_round_trip_basic(self):
        h = UInt160(b'\xab' * 20)
        state = ContractState(id=7, update_counter=3, hash=h, nef=b'\xde\xad', manifest=b'\xbe\xef')
        restored = ContractState.from_bytes(state.to_bytes())

        assert restored.id == 7
        assert restored.update_counter == 3
        assert restored.hash == h
        assert restored.nef == b'\xde\xad'
        assert restored.manifest == b'\xbe\xef'

    def test_round_trip_empty_data(self):
        state = ContractState(id=0, update_counter=0, hash=UInt160.ZERO, nef=b'', manifest=b'')
        restored = ContractState.from_bytes(state.to_bytes())
        assert restored.id == 0
        assert restored.nef == b''
        assert restored.manifest == b''

    def test_from_bytes_empty(self):
        state = ContractState.from_bytes(b'')
        assert state.id == 0


class TestContractManagementDeploy:
    """deploy() happy path and error cases."""

    def test_deploy_happy_path(self):
        cm = _fresh_cm()
        snap = MockSnapshot()
        engine = MockEngine(snap)

        # Initialize to set up next-available-id
        cm.initialize(engine)

        nef = _make_nef()
        manifest = _make_manifest()
        contract = cm.deploy(engine, nef, manifest)

        assert contract.id == 1
        assert contract.update_counter == 0
        assert contract.nef == nef
        assert contract.manifest == manifest
        assert contract.hash is not None
        assert len(engine.fees_added) == 1
        assert engine.fees_added[0] > 0

    def test_deploy_sends_notification(self):
        cm = _fresh_cm()
        snap = MockSnapshot()
        engine = MockEngine(snap)
        cm.initialize(engine)

        cm.deploy(engine, _make_nef(), _make_manifest())
        assert len(engine.notifications) == 1
        assert engine.notifications[0][1] == "Deploy"

    def test_deploy_empty_nef_raises(self):
        cm = _fresh_cm()
        snap = MockSnapshot()
        engine = MockEngine(snap)
        cm.initialize(engine)

        with pytest.raises(ValueError, match="NEF file cannot be empty"):
            cm.deploy(engine, b'', _make_manifest())

    def test_deploy_empty_manifest_raises(self):
        cm = _fresh_cm()
        snap = MockSnapshot()
        engine = MockEngine(snap)
        cm.initialize(engine)

        with pytest.raises(ValueError, match="Manifest cannot be empty"):
            cm.deploy(engine, _make_nef(), b'')

    def test_deploy_duplicate_raises(self):
        cm = _fresh_cm()
        snap = MockSnapshot()
        engine = MockEngine(snap)
        cm.initialize(engine)

        nef = _make_nef()
        manifest = _make_manifest()
        cm.deploy(engine, nef, manifest)

        with pytest.raises(ValueError, match="Contract already exists"):
            cm.deploy(engine, nef, manifest)

    def test_deploy_fee_respects_minimum(self):
        cm = _fresh_cm()
        snap = MockSnapshot()
        engine = MockEngine(snap, storage_price=1)
        cm.initialize(engine)

        small_nef = _make_nef(size=8)
        small_manifest = _make_manifest()
        cm.deploy(engine, small_nef, small_manifest)

        # Fee should be at least DEFAULT_MINIMUM_DEPLOYMENT_FEE
        assert engine.fees_added[0] >= DEFAULT_MINIMUM_DEPLOYMENT_FEE


class TestContractManagementGetContract:
    """get_contract and get_contract_by_id lookups."""

    def test_get_contract_returns_deployed(self):
        cm = _fresh_cm()
        snap = MockSnapshot()
        engine = MockEngine(snap)
        cm.initialize(engine)

        nef = _make_nef()
        manifest = _make_manifest()
        deployed = cm.deploy(engine, nef, manifest)

        found = cm.get_contract(snap, deployed.hash)
        assert found is not None
        assert found.id == deployed.id
        assert found.hash == deployed.hash

    def test_get_contract_missing_returns_none(self):
        cm = _fresh_cm()
        snap = MockSnapshot()
        result = cm.get_contract(snap, UInt160(b'\xff' * 20))
        assert result is None

    def test_get_contract_by_id(self):
        cm = _fresh_cm()
        snap = MockSnapshot()
        engine = MockEngine(snap)
        cm.initialize(engine)

        deployed = cm.deploy(engine, _make_nef(), _make_manifest())
        found = cm.get_contract_by_id(snap, deployed.id)
        assert found is not None
        assert found.hash == deployed.hash

    def test_get_contract_by_id_missing(self):
        cm = _fresh_cm()
        snap = MockSnapshot()
        result = cm.get_contract_by_id(snap, 9999)
        assert result is None


class TestContractManagementHasMethod:
    """has_method with manifest ABI inspection."""

    def test_has_method_found(self):
        cm = _fresh_cm()
        snap = MockSnapshot()
        engine = MockEngine(snap)
        cm.initialize(engine)

        methods = [
            {"name": "transfer", "parameters": [{"name": "from"}, {"name": "to"}, {"name": "amount"}],
             "returntype": "Boolean", "safe": False},
        ]
        deployed = cm.deploy(engine, _make_nef(), _make_manifest(methods=methods))
        assert cm.has_method(snap, deployed.hash, "transfer", 3) is True

    def test_has_method_wrong_pcount(self):
        cm = _fresh_cm()
        snap = MockSnapshot()
        engine = MockEngine(snap)
        cm.initialize(engine)

        methods = [{"name": "transfer", "parameters": [{"name": "a"}], "returntype": "Void", "safe": False}]
        deployed = cm.deploy(engine, _make_nef(), _make_manifest(methods=methods))
        assert cm.has_method(snap, deployed.hash, "transfer", 3) is False

    def test_has_method_missing_contract(self):
        cm = _fresh_cm()
        snap = MockSnapshot()
        assert cm.has_method(snap, UInt160(b'\xff' * 20), "foo", 0) is False


class TestContractManagementUpdate:
    """update() lifecycle."""

    def _deploy_and_get_engine(self):
        cm = _fresh_cm()
        snap = MockSnapshot()
        engine = MockEngine(snap)
        cm.initialize(engine)
        nef = _make_nef()
        manifest = _make_manifest()
        deployed = cm.deploy(engine, nef, manifest)
        # Set calling_hash to the deployed contract
        engine._calling_hash = deployed.hash
        return cm, snap, engine, deployed

    def test_update_nef_only(self):
        cm, snap, engine, deployed = self._deploy_and_get_engine()
        new_nef = _make_nef(size=128)
        cm.update(engine, new_nef, None)

        updated = cm.get_contract(snap, deployed.hash)
        assert updated.nef == new_nef
        assert updated.update_counter == 1

    def test_update_manifest_only(self):
        cm, snap, engine, deployed = self._deploy_and_get_engine()
        new_manifest = _make_manifest(name="UpdatedContract")
        cm.update(engine, None, new_manifest)

        updated = cm.get_contract(snap, deployed.hash)
        assert updated.manifest == new_manifest
        assert updated.update_counter == 1

    def test_update_both(self):
        cm, snap, engine, deployed = self._deploy_and_get_engine()
        new_nef = _make_nef(size=128)
        new_manifest = _make_manifest(name="V2")
        cm.update(engine, new_nef, new_manifest)

        updated = cm.get_contract(snap, deployed.hash)
        assert updated.nef == new_nef
        assert updated.manifest == new_manifest
        assert updated.update_counter == 1

    def test_update_both_none_raises(self):
        cm, snap, engine, deployed = self._deploy_and_get_engine()
        with pytest.raises(ValueError, match="NEF and manifest cannot both be null"):
            cm.update(engine, None, None)

    def test_update_empty_nef_raises(self):
        cm, snap, engine, deployed = self._deploy_and_get_engine()
        with pytest.raises(ValueError, match="NEF file cannot be empty"):
            cm.update(engine, b'', None)

    def test_update_empty_manifest_raises(self):
        cm, snap, engine, deployed = self._deploy_and_get_engine()
        with pytest.raises(ValueError, match="Manifest cannot be empty"):
            cm.update(engine, None, b'')

    def test_update_increments_counter_twice(self):
        cm, snap, engine, deployed = self._deploy_and_get_engine()
        cm.update(engine, _make_nef(size=80), None)
        cm.update(engine, _make_nef(size=96), None)

        updated = cm.get_contract(snap, deployed.hash)
        assert updated.update_counter == 2

    def test_update_sends_notification(self):
        cm, snap, engine, deployed = self._deploy_and_get_engine()
        engine.notifications.clear()
        cm.update(engine, _make_nef(size=80), None)
        assert any(n[1] == "Update" for n in engine.notifications)


class TestContractManagementDestroy:
    """destroy() cleanup."""

    def test_destroy_removes_contract(self):
        cm = _fresh_cm()
        snap = MockSnapshot()
        engine = MockEngine(snap)
        cm.initialize(engine)

        deployed = cm.deploy(engine, _make_nef(), _make_manifest())
        engine._calling_hash = deployed.hash

        cm.destroy(engine)

        assert cm.get_contract(snap, deployed.hash) is None
        assert cm.get_contract_by_id(snap, deployed.id) is None

    def test_destroy_sends_notification(self):
        cm = _fresh_cm()
        snap = MockSnapshot()
        engine = MockEngine(snap)
        cm.initialize(engine)

        deployed = cm.deploy(engine, _make_nef(), _make_manifest())
        engine._calling_hash = deployed.hash
        engine.notifications.clear()

        cm.destroy(engine)
        assert any(n[1] == "Destroy" for n in engine.notifications)

    def test_destroy_nonexistent_is_noop(self):
        cm = _fresh_cm()
        snap = MockSnapshot()
        engine = MockEngine(snap)
        engine._calling_hash = UInt160(b'\xff' * 20)

        # Should not raise
        cm.destroy(engine)


class TestContractManagementFees:
    """Minimum deployment fee get/set."""

    def test_get_default_fee(self):
        cm = _fresh_cm()
        snap = MockSnapshot()
        fee = cm.get_minimum_deployment_fee(snap)
        assert fee == DEFAULT_MINIMUM_DEPLOYMENT_FEE

    def test_set_fee_committee_only(self):
        cm = _fresh_cm()
        snap = MockSnapshot()
        engine = MockEngine(snap, is_committee=False)

        with pytest.raises(PermissionError, match="Committee"):
            cm.set_minimum_deployment_fee(engine, 5_00000000)

    def test_set_fee_negative_raises(self):
        cm = _fresh_cm()
        snap = MockSnapshot()
        engine = MockEngine(snap, is_committee=True)

        with pytest.raises(ValueError, match="negative"):
            cm.set_minimum_deployment_fee(engine, -1)


class TestContractManagementInitialize:
    """initialize() on genesis."""

    def test_initialize_sets_defaults(self):
        cm = _fresh_cm()
        snap = MockSnapshot()
        engine = MockEngine(snap)
        cm.initialize(engine)

        # Verify fee was stored
        fee = cm.get_minimum_deployment_fee(snap)
        assert fee == DEFAULT_MINIMUM_DEPLOYMENT_FEE
