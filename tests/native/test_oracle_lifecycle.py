"""Comprehensive tests for Oracle request/finish lifecycle.

Covers:
- OracleRequest serialization round-trip
- OracleResponseCode enum values
- request(): happy path, URL/filter/callback validation, gas minimum
- ID list serialization/deserialization
- get_request / get_requests_by_url lookups
- _remove_request cleanup
- verify() with OracleResponse attribute detection
- set_price / get_price with defaults
- initialize on genesis
"""

from __future__ import annotations

import pytest
from dataclasses import dataclass
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
    MAX_USER_DATA_LENGTH,
    PREFIX_PRICE,
    PREFIX_REQUEST,
    PREFIX_REQUEST_ID,
    PREFIX_ID_LIST,
)
from neo.native.native_contract import NativeContract, StorageItem, StorageKey


# ---------------------------------------------------------------------------
# Mock infrastructure
# ---------------------------------------------------------------------------

class MockSnapshot:
    """In-memory snapshot that accepts StorageKey objects."""

    def __init__(self) -> None:
        self._store: Dict[tuple, Any] = {}

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


class MockEngine:
    """Minimal engine mock for Oracle tests."""

    def __init__(self, snapshot: MockSnapshot) -> None:
        self.snapshot = snapshot
        self.script_container = None

    def check_committee(self) -> bool:
        return True


@dataclass
class _MockTx:
    sender: UInt160
    attributes: list = None

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = []


@dataclass
class _MockAttribute:
    type: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fresh_oracle() -> OracleContract:
    """Create a fresh OracleContract, clearing global registry."""
    NativeContract._contracts.clear()
    NativeContract._contracts_by_id.clear()
    NativeContract._contracts_by_name.clear()
    NativeContract._id_counter = 0
    return OracleContract()


def _initialized_oracle():
    """Return (oracle, snapshot, engine) with storage initialized."""
    oc = _fresh_oracle()
    snap = MockSnapshot()
    engine = MockEngine(snap)
    oc.initialize(engine)
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
    """get_request, get_requests_by_url, _remove_request."""

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
