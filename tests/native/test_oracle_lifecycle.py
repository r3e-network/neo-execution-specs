"""Comprehensive tests for the Oracle request/finish/post_persist lifecycle.

Mirrors C# Neo.SmartContract.Native.OracleContract (v3.10.0).

Covers:
- OracleRequest serialization round-trip (IInteroperable shape)
- OracleResponseCode enum values
- request(): happy path, URL/filter/callback validation, gas minimum,
  caller-must-be-a-contract fault, fee charge, reserved-GAS mint,
  OracleRequest notification
- ID list serialization/deserialization
- get_request / get_requests / get_requests_by_url lookups
- _remove_request cleanup
- finish(): invocation guards, OracleResponse-attribute requirement,
  OracleResponse notification, callback dispatch
- verify() with OracleResponse attribute detection
- set_price / get_price with defaults
- post_persist(): request cleanup + Oracle-node GAS payout
- initialize on genesis
"""

from __future__ import annotations

import pytest
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from neo.types import UInt160, UInt256
from neo.native.oracle import (
    OracleContract,
    OracleRequest,
    OracleResponseCode,
    DEFAULT_ORACLE_PRICE,
    MAX_URL_LENGTH,
    MAX_FILTER_LENGTH,
    MAX_CALLBACK_LENGTH,
    ORACLE_RESPONSE_ATTR_TYPE,
    _request_id_key_suffix,
)
from neo.native.native_contract import NativeContract, StorageKey


# ---------------------------------------------------------------------------
# Mock infrastructure
# ---------------------------------------------------------------------------

class MockSnapshot:
    """In-memory snapshot that accepts StorageKey objects."""

    def __init__(self) -> None:
        self._store: Dict[tuple, Any] = {}
        self.persisting_block: Any = None

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

    def find(self, prefix) -> list:
        tp = self._to_tuple(prefix)
        results = []
        for k, v in self._store.items():
            if isinstance(k, tuple) and isinstance(tp, tuple):
                if k[0] == tp[0] and k[1].startswith(tp[1]):
                    results.append((k[1], v))
        return sorted(results)


# A deployed-contract calling hash used across request tests.
CALLER_CONTRACT = UInt160(b'\xcc' * 20)


class _MockContractManagement:
    """Stand-in for ContractManagement.is_contract used by request()."""

    def __init__(self, contracts: Optional[set] = None) -> None:
        self._contracts = contracts if contracts is not None else {bytes(CALLER_CONTRACT.data)}

    @property
    def name(self) -> str:
        return "ContractManagement"

    def is_contract(self, snapshot: Any, hash: UInt160) -> bool:
        return bytes(hash.data) in self._contracts


class _MockGasToken:
    """Records GAS mints so tests can assert reserved-GAS / payout behaviour."""

    def __init__(self) -> None:
        self.mints: List[tuple] = []  # (account_bytes, amount, call_on_payment)

    @property
    def name(self) -> str:
        return "GasToken"

    def mint(self, engine: Any, account: UInt160, amount: int, call_on_payment: bool = True) -> None:
        self.mints.append((bytes(account.data), amount, call_on_payment))


class _MockRoleManagement:
    """Stand-in for RoleManagement.get_designated_by_role (Oracle nodes)."""

    def __init__(self, oracle_pubkeys: Optional[List[bytes]] = None) -> None:
        self._pubkeys = oracle_pubkeys or []

    @property
    def name(self) -> str:
        return "RoleManagement"

    def get_designated_by_role(self, snapshot: Any, role: Any, index: int) -> List[bytes]:
        return list(self._pubkeys)


class MockEngine:
    """Engine mock exposing the surface request/finish/post_persist need."""

    FeeFactor = 10000

    def __init__(
        self,
        snapshot: MockSnapshot,
        calling_script_hash: Optional[UInt160] = CALLER_CONTRACT,
        invocation_stack_len: int = 2,
        invocation_counter: int = 1,
    ) -> None:
        self.snapshot = snapshot
        self.script_container: Any = None
        self.persisting_block: Any = None
        self._calling = calling_script_hash
        # Provide an invocation stack of the requested depth so the Finish
        # guards observe a realistic count.
        self.invocation_stack = [object()] * invocation_stack_len
        self._invocation_counter = invocation_counter

        self.fees_charged: List[int] = []
        self.notifications: List[tuple] = []      # (script_hash_bytes, name, state)
        self.callbacks: List[tuple] = []          # (caller, target, method, args)

    # -- witness / committee ------------------------------------------------
    def check_committee(self) -> bool:
        return True

    # -- script hashes ------------------------------------------------------
    @property
    def calling_script_hash(self) -> Optional[UInt160]:
        return self._calling

    # -- fee accounting -----------------------------------------------------
    def add_fee(self, pico_gas: int) -> None:
        self.fees_charged.append(int(pico_gas))

    # -- notifications ------------------------------------------------------
    def send_notification(self, script_hash: UInt160, event_name: str, state: Any) -> None:
        self.notifications.append((bytes(script_hash.data), event_name, state))

    # -- invocation guards --------------------------------------------------
    def get_invocation_counter(self) -> int:
        return self._invocation_counter

    # -- callback dispatch --------------------------------------------------
    def call_from_native_contract(self, caller: UInt160, target: UInt160, method: str, *args: Any) -> None:
        self.callbacks.append((bytes(caller.data), bytes(target.data), method, args))


@dataclass
class _MockTx:
    sender: UInt160
    attributes: list = field(default_factory=list)
    hash: UInt256 = field(default_factory=lambda: UInt256(b'\x11' * 32))


@dataclass
class _MockAttribute:
    type: int


@dataclass
class _MockOracleResponse:
    """OracleResponse transaction attribute (type 0x11)."""

    id: int
    code: int = int(OracleResponseCode.Success)
    result: bytes = b''
    type: int = ORACLE_RESPONSE_ATTR_TYPE


@dataclass
class _MockBlock:
    index: int = 100
    transactions: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clear_registry() -> None:
    NativeContract._contracts.clear()
    NativeContract._contracts_by_id.clear()
    NativeContract._contracts_by_name.clear()
    NativeContract._id_counter = 0


def _fresh_oracle() -> OracleContract:
    """Create a fresh OracleContract, clearing the global registry."""
    _clear_registry()
    return OracleContract()


def _register_dependencies(
    cm: Optional[_MockContractManagement] = None,
    gas: Optional[_MockGasToken] = None,
    rm: Optional[_MockRoleManagement] = None,
) -> tuple:
    """Register mock dependency natives in the global registry."""
    cm = cm if cm is not None else _MockContractManagement()
    gas = gas if gas is not None else _MockGasToken()
    NativeContract._contracts_by_name["ContractManagement"] = cm
    NativeContract._contracts_by_name["GasToken"] = gas
    if rm is not None:
        NativeContract._contracts_by_name["RoleManagement"] = rm
    return cm, gas, rm


def _initialized_oracle():
    """Return (oracle, snapshot, engine) with storage + deps initialized."""
    oc = _fresh_oracle()
    snap = MockSnapshot()
    engine = MockEngine(snap)
    oc.initialize(engine)
    _register_dependencies()
    return oc, snap, engine


# ===========================================================================
# Tests: OracleRequest serialization
# ===========================================================================

class TestOracleRequestSerialization:
    """OracleRequest serialize / deserialize round-trip."""

    def test_round_trip_basic(self):
        req = OracleRequest(
            original_txid=UInt256(b'\xaa' * 32),
            gas_for_response=50_000_000,
            url="https://example.com/api",
            filter="$.result",
            callback_contract=UInt160(b'\xbb' * 20),
            callback_method="onResponse",
            user_data=b'\x01\x02\x03',
        )
        restored = OracleRequest.deserialize(req.serialize())

        assert restored.original_txid == req.original_txid
        assert restored.gas_for_response == req.gas_for_response
        assert restored.url == req.url
        assert restored.filter == req.filter
        assert restored.callback_contract == req.callback_contract
        assert restored.callback_method == req.callback_method
        assert restored.user_data == req.user_data

    def test_round_trip_no_filter(self):
        req = OracleRequest(
            original_txid=UInt256(b'\x00' * 32),
            gas_for_response=10_000_000,
            url="https://test.org",
            filter=None,
            callback_contract=UInt160(b'\x00' * 20),
            callback_method="cb",
            user_data=b'',
        )
        restored = OracleRequest.deserialize(req.serialize())
        assert restored.filter is None
        assert restored.user_data == b''

    def test_round_trip_empty_user_data(self):
        req = OracleRequest(user_data=b'')
        data = req.serialize()
        restored = OracleRequest.deserialize(data)
        assert restored.user_data == b''

    def test_to_stack_item_element_order(self):
        """ToStackItem must match C# OracleRequest.ToStackItem ordering."""
        req = OracleRequest(
            original_txid=UInt256(b'\xaa' * 32),
            gas_for_response=7,
            url="u",
            filter="f",
            callback_contract=UInt160(b'\xbb' * 20),
            callback_method="m",
            user_data=b'\x09',
        )
        item = req.to_stack_item()
        items = list(item)
        assert len(items) == 7
        assert bytes(items[0].value) == b'\xaa' * 32          # OriginalTxid
        assert int(items[1].value) == 7                        # GasForResponse
        assert bytes(items[2].value).decode() == "u"           # Url
        assert bytes(items[3].value).decode() == "f"           # Filter
        assert bytes(items[4].value) == b'\xbb' * 20           # CallbackContract
        assert bytes(items[5].value).decode() == "m"           # CallbackMethod
        assert bytes(items[6].value) == b'\x09'                # UserData


# ===========================================================================
# Tests: OracleResponseCode enum
# ===========================================================================

class TestOracleResponseCode:
    """Verify response code enum values match Neo N3 spec."""

    def test_success(self):
        assert OracleResponseCode.Success == 0x00

    def test_error_codes(self):
        assert OracleResponseCode.ProtocolNotSupported == 0x10
        assert OracleResponseCode.NotFound == 0x14
        assert OracleResponseCode.Timeout == 0x16
        assert OracleResponseCode.Forbidden == 0x18
        assert OracleResponseCode.ResponseTooLarge == 0x1a
        assert OracleResponseCode.InsufficientFunds == 0x1c
        assert OracleResponseCode.Error == 0xff


# ===========================================================================
# Tests: storage-key suffix encoding
# ===========================================================================

class TestRequestKeySuffix:
    """Request id is encoded 8-byte big-endian, matching C#."""

    def test_suffix_is_8_byte_big_endian(self):
        assert _request_id_key_suffix(0) == b'\x00' * 8
        assert _request_id_key_suffix(1) == b'\x00' * 7 + b'\x01'
        assert _request_id_key_suffix(258) == b'\x00' * 6 + b'\x01\x02'


# ===========================================================================
# Tests: Oracle price management
# ===========================================================================

class TestOraclePrice:
    """get_price / set_price."""

    def test_get_default_price(self):
        oc, snap, engine = _initialized_oracle()
        price = oc.get_price(snap)
        assert price == DEFAULT_ORACLE_PRICE

    def test_set_price(self):
        oc, snap, engine = _initialized_oracle()
        oc.set_price(engine, 100_000_000)
        assert oc.get_price(snap) == 100_000_000

    def test_set_price_zero_raises(self):
        oc, snap, engine = _initialized_oracle()
        with pytest.raises(ValueError, match="positive"):
            oc.set_price(engine, 0)

    def test_set_price_negative_raises(self):
        oc, snap, engine = _initialized_oracle()
        with pytest.raises(ValueError, match="positive"):
            oc.set_price(engine, -1)


# ===========================================================================
# Tests: Oracle request creation and validation
# ===========================================================================

class TestOracleRequest:
    """request() happy path and validation."""

    def test_request_happy_path(self):
        oc, snap, engine = _initialized_oracle()
        oc.request(
            engine,
            url="https://example.com/price",
            filter="$.usd",
            callback="onPrice",
            user_data=b'\x42',
            gas_for_response=10_000_000,
        )
        # Request should be retrievable
        req = oc.get_request(snap, 0)
        assert req is not None
        assert req.url == "https://example.com/price"
        assert req.filter == "$.usd"
        assert req.callback_method == "onPrice"
        assert req.callback_contract == CALLER_CONTRACT

    def test_request_increments_id(self):
        oc, snap, engine = _initialized_oracle()
        oc.request(engine, "https://a.com", None, "cb", b'', 10_000_000)
        oc.request(engine, "https://b.com", None, "cb", b'', 10_000_000)

        assert oc.get_request(snap, 0) is not None
        assert oc.get_request(snap, 1) is not None
        assert oc.get_request(snap, 0).url == "https://a.com"
        assert oc.get_request(snap, 1).url == "https://b.com"

    def test_request_url_too_long_raises(self):
        oc, snap, engine = _initialized_oracle()
        long_url = "https://x.com/" + "a" * MAX_URL_LENGTH
        with pytest.raises(ValueError, match="URL exceeds"):
            oc.request(engine, long_url, None, "cb", b'', 10_000_000)

    def test_request_filter_too_long_raises(self):
        oc, snap, engine = _initialized_oracle()
        long_filter = "x" * (MAX_FILTER_LENGTH + 1)
        with pytest.raises(ValueError, match="Filter exceeds"):
            oc.request(engine, "https://x.com", long_filter, "cb", b'', 10_000_000)

    def test_request_callback_too_long_raises(self):
        oc, snap, engine = _initialized_oracle()
        long_cb = "x" * (MAX_CALLBACK_LENGTH + 1)
        with pytest.raises(ValueError, match="Callback exceeds"):
            oc.request(engine, "https://x.com", None, long_cb, b'', 10_000_000)

    def test_request_callback_underscore_raises(self):
        oc, snap, engine = _initialized_oracle()
        with pytest.raises(ValueError, match="underscore"):
            oc.request(engine, "https://x.com", None, "_private", b'', 10_000_000)

    def test_request_gas_too_low_raises(self):
        oc, snap, engine = _initialized_oracle()
        with pytest.raises(ValueError, match="0.1 GAS"):
            oc.request(engine, "https://x.com", None, "cb", b'', 1_000_000)

    def test_request_no_filter(self):
        oc, snap, engine = _initialized_oracle()
        oc.request(engine, "https://x.com", None, "cb", b'', 10_000_000)
        req = oc.get_request(snap, 0)
        assert req.filter is None

    def test_request_caller_not_contract_faults(self):
        """C# faults when CallingScriptHash is not a deployed contract."""
        from neo.exceptions import InvalidOperationException

        oc = _fresh_oracle()
        snap = MockSnapshot()
        # Calling hash that is NOT registered as a contract.
        engine = MockEngine(snap, calling_script_hash=UInt160(b'\xee' * 20))
        oc.initialize(engine)
        _register_dependencies()  # default CM only knows CALLER_CONTRACT

        with pytest.raises(InvalidOperationException, match="Only contracts"):
            oc.request(engine, "https://x.com", None, "cb", b'', 10_000_000)

    def test_request_caller_none_faults(self):
        """A request with no caller frame faults."""
        from neo.exceptions import InvalidOperationException

        oc = _fresh_oracle()
        snap = MockSnapshot()
        engine = MockEngine(snap, calling_script_hash=None)
        oc.initialize(engine)
        _register_dependencies()

        with pytest.raises(InvalidOperationException, match="Only contracts"):
            oc.request(engine, "https://x.com", None, "cb", b'', 10_000_000)

    def test_request_charges_fees(self):
        """request() charges GetPrice()*FeeFactor and gasForResponse*FeeFactor."""
        oc, snap, engine = _initialized_oracle()
        oc.request(engine, "https://x.com", None, "cb", b'', 10_000_000)

        # Two AddFee calls: price and reserved GAS, both *FeeFactor.
        assert engine.fees_charged == [
            DEFAULT_ORACLE_PRICE * MockEngine.FeeFactor,
            10_000_000 * MockEngine.FeeFactor,
        ]

    def test_request_mints_reserved_gas_to_oracle(self):
        """request() mints gasForResponse GAS to the Oracle contract."""
        gas = _MockGasToken()
        oc = _fresh_oracle()
        snap = MockSnapshot()
        engine = MockEngine(snap)
        oc.initialize(engine)
        _register_dependencies(gas=gas)

        oc.request(engine, "https://x.com", None, "cb", b'', 25_000_000)

        assert len(gas.mints) == 1
        account_bytes, amount, call_on_payment = gas.mints[0]
        assert account_bytes == bytes(oc.hash.data)
        assert amount == 25_000_000
        assert call_on_payment is False

    def test_request_emits_oracle_request_event(self):
        oc, snap, engine = _initialized_oracle()
        oc.request(engine, "https://x.com", "$.f", "cb", b'', 10_000_000)

        events = [n for n in engine.notifications if n[1] == "OracleRequest"]
        assert len(events) == 1
        script_hash_bytes, name, state = events[0]
        assert script_hash_bytes == bytes(oc.hash.data)
        items = list(state)
        assert int(items[0].value) == 0                      # Id
        assert bytes(items[1].value) == bytes(CALLER_CONTRACT.data)  # RequestContract
        assert bytes(items[2].value).decode() == "https://x.com"     # Url
        assert bytes(items[3].value).decode() == "$.f"               # Filter

    def test_request_sets_original_txid_from_tx_hash(self):
        oc, snap, engine = _initialized_oracle()
        tx = _MockTx(sender=UInt160(b'\x01' * 20), hash=UInt256(b'\x77' * 32))
        engine.script_container = tx
        oc.request(engine, "https://x.com", None, "cb", b'', 10_000_000)
        req = oc.get_request(snap, 0)
        assert req.original_txid == UInt256(b'\x77' * 32)


# ===========================================================================
# Tests: ID list serialization
# ===========================================================================

class TestIdListSerialization:
    """_serialize_id_list / _deserialize_id_list round-trip."""

    def test_round_trip(self):
        oc = _fresh_oracle()
        ids = [0, 1, 42, 255]
        data = oc._serialize_id_list(ids)
        restored = oc._deserialize_id_list(data)
        assert restored == ids

    def test_empty_list(self):
        oc = _fresh_oracle()
        assert oc._deserialize_id_list(b'') == []

    def test_single_element(self):
        oc = _fresh_oracle()
        data = oc._serialize_id_list([7])
        restored = oc._deserialize_id_list(data)
        assert restored == [7]


# ===========================================================================
# Tests: Request retrieval and URL indexing
# ===========================================================================

class TestOracleRequestRetrieval:
    """get_request, get_requests, get_requests_by_url, _remove_request."""

    def test_get_request_missing(self):
        oc, snap, engine = _initialized_oracle()
        assert oc.get_request(snap, 999) is None

    def test_get_requests_by_url(self):
        oc, snap, engine = _initialized_oracle()
        oc.request(engine, "https://a.com", None, "cb", b'', 10_000_000)
        oc.request(engine, "https://a.com", None, "cb2", b'', 10_000_000)
        oc.request(engine, "https://b.com", None, "cb3", b'', 10_000_000)

        results = list(oc.get_requests_by_url(snap, "https://a.com"))
        assert len(results) == 2
        assert results[0][1].callback_method == "cb"
        assert results[1][1].callback_method == "cb2"

    def test_get_requests_all(self):
        oc, snap, engine = _initialized_oracle()
        oc.request(engine, "https://a.com", None, "cb", b'', 10_000_000)
        oc.request(engine, "https://b.com", None, "cb2", b'', 10_000_000)

        results = dict(oc.get_requests(snap))
        assert set(results.keys()) == {0, 1}
        assert results[0].url == "https://a.com"
        assert results[1].url == "https://b.com"

    def test_get_requests_by_url_empty(self):
        oc, snap, engine = _initialized_oracle()
        results = list(oc.get_requests_by_url(snap, "https://nonexistent.com"))
        assert results == []

    def test_remove_request_cleans_storage(self):
        oc, snap, engine = _initialized_oracle()
        oc.request(engine, "https://a.com", None, "cb", b'', 10_000_000)

        # Verify it exists
        assert oc.get_request(snap, 0) is not None

        # Remove it
        oc._remove_request(snap, 0, "https://a.com")

        # Verify it's gone
        assert oc.get_request(snap, 0) is None
        results = list(oc.get_requests_by_url(snap, "https://a.com"))
        assert results == []

    def test_remove_request_partial_url_list(self):
        oc, snap, engine = _initialized_oracle()
        oc.request(engine, "https://a.com", None, "cb1", b'', 10_000_000)
        oc.request(engine, "https://a.com", None, "cb2", b'', 10_000_000)

        # Remove only the first
        oc._remove_request(snap, 0, "https://a.com")

        remaining = list(oc.get_requests_by_url(snap, "https://a.com"))
        assert len(remaining) == 1
        assert remaining[0][0] == 1


# ===========================================================================
# Tests: Oracle finish
# ===========================================================================

class TestOracleFinish:
    """finish() guards, notification, and callback dispatch."""

    def _make_request(self, oc, snap, engine, *, user_data=b''):
        oc.request(engine, "https://a.com", "$.f", "onResp", user_data, 10_000_000)
        return oc.get_request(snap, 0)

    def test_finish_dispatches_callback(self):
        oc, snap, engine = _initialized_oracle()
        self._make_request(oc, snap, engine)

        # Build a finishing tx carrying the OracleResponse attribute.
        resp = _MockOracleResponse(id=0, code=int(OracleResponseCode.Success), result=b'\xde\xad')
        engine.script_container = _MockTx(sender=UInt160(b'\x01' * 20), attributes=[resp])

        oc.finish(engine)

        assert len(engine.callbacks) == 1
        caller, target, method, args = engine.callbacks[0]
        assert caller == bytes(oc.hash.data)
        assert target == bytes(CALLER_CONTRACT.data)
        assert method == "onResp"
        # args = (url, userData, code, result)
        assert bytes(args[0].value).decode() == "https://a.com"
        assert int(args[2].value) == int(OracleResponseCode.Success)
        assert bytes(args[3].value) == b'\xde\xad'

    def test_finish_emits_oracle_response_event(self):
        oc, snap, engine = _initialized_oracle()
        tx_for_request = _MockTx(sender=UInt160(b'\x01' * 20), hash=UInt256(b'\x55' * 32))
        engine.script_container = tx_for_request
        oc.request(engine, "https://a.com", None, "onResp", b'', 10_000_000)

        resp = _MockOracleResponse(id=0)
        engine.script_container = _MockTx(sender=UInt160(b'\x01' * 20), attributes=[resp])
        oc.finish(engine)

        events = [n for n in engine.notifications if n[1] == "OracleResponse"]
        assert len(events) == 1
        _, _, state = events[0]
        items = list(state)
        assert int(items[0].value) == 0                       # Id
        assert bytes(items[1].value) == b'\x55' * 32          # OriginalTx

    def test_finish_no_response_attr_raises(self):
        oc, snap, engine = _initialized_oracle()
        self._make_request(oc, snap, engine)
        engine.script_container = _MockTx(
            sender=UInt160(b'\x01' * 20),
            attributes=[_MockAttribute(type=0x01)],
        )
        with pytest.raises(ValueError, match="Oracle response not found"):
            oc.finish(engine)

    def test_finish_unknown_request_raises(self):
        oc, snap, engine = _initialized_oracle()
        resp = _MockOracleResponse(id=999)
        engine.script_container = _MockTx(sender=UInt160(b'\x01' * 20), attributes=[resp])
        with pytest.raises(ValueError, match="Oracle request not found"):
            oc.finish(engine)

    def test_finish_bad_invocation_stack_raises(self):
        from neo.exceptions import InvalidOperationException

        oc = _fresh_oracle()
        snap = MockSnapshot()
        engine = MockEngine(snap, invocation_stack_len=3)
        oc.initialize(engine)
        _register_dependencies()
        oc.request(engine, "https://a.com", None, "onResp", b'', 10_000_000)

        resp = _MockOracleResponse(id=0)
        engine.script_container = _MockTx(sender=UInt160(b'\x01' * 20), attributes=[resp])
        with pytest.raises(InvalidOperationException, match="single call frame"):
            oc.finish(engine)

    def test_finish_bad_invocation_counter_raises(self):
        from neo.exceptions import InvalidOperationException

        oc = _fresh_oracle()
        snap = MockSnapshot()
        engine = MockEngine(snap, invocation_counter=2)
        oc.initialize(engine)
        _register_dependencies()
        oc.request(engine, "https://a.com", None, "onResp", b'', 10_000_000)

        resp = _MockOracleResponse(id=0)
        engine.script_container = _MockTx(sender=UInt160(b'\x01' * 20), attributes=[resp])
        with pytest.raises(InvalidOperationException, match="counter"):
            oc.finish(engine)


# ===========================================================================
# Tests: Oracle verify
# ===========================================================================

class TestOracleVerify:
    """verify() with OracleResponse attribute detection."""

    def test_verify_with_oracle_response_attr(self):
        oc = _fresh_oracle()
        engine = MockEngine(MockSnapshot())
        engine.script_container = _MockTx(
            sender=UInt160(b'\x01' * 20),
            attributes=[_MockAttribute(type=0x11)],
        )
        assert oc.verify(engine) is True

    def test_verify_without_oracle_response_attr(self):
        oc = _fresh_oracle()
        engine = MockEngine(MockSnapshot())
        engine.script_container = _MockTx(
            sender=UInt160(b'\x01' * 20),
            attributes=[_MockAttribute(type=0x01)],
        )
        assert oc.verify(engine) is False

    def test_verify_no_attributes(self):
        oc = _fresh_oracle()
        engine = MockEngine(MockSnapshot())
        engine.script_container = _MockTx(
            sender=UInt160(b'\x01' * 20),
            attributes=[],
        )
        assert oc.verify(engine) is False

    def test_verify_no_script_container(self):
        oc = _fresh_oracle()
        engine = MockEngine(MockSnapshot())
        engine.script_container = None
        assert oc.verify(engine) is False


# ===========================================================================
# Tests: Oracle post_persist
# ===========================================================================

class TestOraclePostPersist:
    """post_persist() request cleanup + Oracle-node GAS payout."""

    def test_post_persist_removes_request(self):
        oc, snap, engine = _initialized_oracle()
        oc.request(engine, "https://a.com", None, "cb", b'', 10_000_000)
        assert oc.get_request(snap, 0) is not None

        resp = _MockOracleResponse(id=0)
        block = _MockBlock(index=100, transactions=[_MockTx(sender=UInt160(b'\x01' * 20), attributes=[resp])])
        engine.persisting_block = block

        oc.post_persist(engine)

        assert oc.get_request(snap, 0) is None
        assert list(oc.get_requests_by_url(snap, "https://a.com")) == []

    def test_post_persist_pays_oracle_node(self):
        oracle_pk = b'\x02' + b'\x03' * 32  # 33-byte compressed pubkey
        gas = _MockGasToken()
        rm = _MockRoleManagement(oracle_pubkeys=[oracle_pk])

        oc = _fresh_oracle()
        snap = MockSnapshot()
        engine = MockEngine(snap)
        oc.initialize(engine)
        _register_dependencies(gas=gas, rm=rm)

        oc.request(engine, "https://a.com", None, "cb", b'', 10_000_000)
        gas.mints.clear()  # drop the reserved-GAS mint from request()

        resp = _MockOracleResponse(id=0)
        block = _MockBlock(index=100, transactions=[_MockTx(sender=UInt160(b'\x01' * 20), attributes=[resp])])
        engine.persisting_block = block

        oc.post_persist(engine)

        # Exactly one payout mint for the designated Oracle node, equal to the
        # request price (default 0.5 GAS).
        assert len(gas.mints) == 1
        account_bytes, amount, call_on_payment = gas.mints[0]
        assert amount == DEFAULT_ORACLE_PRICE
        assert call_on_payment is False

        # Account is the signature-redeem-script hash of the designated key.
        from neo.crypto import hash160
        from neo.smartcontract.syscalls.contract import _create_signature_redeem_script
        expected = hash160(_create_signature_redeem_script(oracle_pk))
        assert account_bytes == expected

    def test_post_persist_no_nodes_no_payout(self):
        gas = _MockGasToken()
        rm = _MockRoleManagement(oracle_pubkeys=[])

        oc = _fresh_oracle()
        snap = MockSnapshot()
        engine = MockEngine(snap)
        oc.initialize(engine)
        _register_dependencies(gas=gas, rm=rm)

        oc.request(engine, "https://a.com", None, "cb", b'', 10_000_000)
        gas.mints.clear()

        resp = _MockOracleResponse(id=0)
        block = _MockBlock(index=100, transactions=[_MockTx(sender=UInt160(b'\x01' * 20), attributes=[resp])])
        engine.persisting_block = block

        oc.post_persist(engine)

        # Request still cleaned up, but no payout.
        assert oc.get_request(snap, 0) is None
        assert gas.mints == []

    def test_post_persist_ignores_non_response_txs(self):
        oc, snap, engine = _initialized_oracle()
        oc.request(engine, "https://a.com", None, "cb", b'', 10_000_000)

        block = _MockBlock(index=100, transactions=[
            _MockTx(sender=UInt160(b'\x01' * 20), attributes=[_MockAttribute(type=0x01)]),
        ])
        engine.persisting_block = block

        oc.post_persist(engine)

        # No OracleResponse => request remains.
        assert oc.get_request(snap, 0) is not None

    def test_post_persist_no_block_is_noop(self):
        oc, snap, engine = _initialized_oracle()
        oc.request(engine, "https://a.com", None, "cb", b'', 10_000_000)
        engine.persisting_block = None
        # Should not raise.
        oc.post_persist(engine)
        assert oc.get_request(snap, 0) is not None
