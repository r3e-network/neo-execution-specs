"""Comprehensive tests for StorageIterator (neo.smartcontract.iterators).

Covers:
- Basic iteration: next/value lifecycle, empty results, exhaustion
- FindOptions: REMOVE_PREFIX, KEYS_ONLY, VALUES_ONLY
- FindOptions: DESERIALIZE_VALUES, PICK_FIELD0, PICK_FIELD1
- Combined option flags
- Edge cases: value before next, value after exhaustion
"""

from __future__ import annotations

import pytest
from typing import List, Tuple

from neo.smartcontract.iterators import StorageIterator
from neo.smartcontract.storage.find_options import FindOptions
from neo.smartcontract.storage import StorageKey, StorageItem
from neo.vm.types import ByteString, Struct, Array


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pair(key: bytes, value: bytes) -> Tuple[StorageKey, StorageItem]:
    """Create a (StorageKey, StorageItem) tuple."""
    return (StorageKey(id=0, key=key), StorageItem(value=value))


def _make_iter(
    pairs: List[Tuple[bytes, bytes]],
    prefix_len: int = 2,
    options: int = 0,
) -> StorageIterator:
    """Build a StorageIterator from raw (key_bytes, value_bytes) pairs."""
    typed = [_pair(k, v) for k, v in pairs]
    return StorageIterator(iter(typed), prefix_len, FindOptions(options))


def _collect(it: StorageIterator) -> list:
    """Drain iterator, return all value() results."""
    out = []
    while it.next():
        out.append(it.value())
    return out


# ---------------------------------------------------------------------------
# Basic iteration lifecycle
# ---------------------------------------------------------------------------

class TestBasicIteration:
    """StorageIterator next/value lifecycle."""

    def test_empty_iterator(self):
        it = _make_iter([])
        assert it.next() is False

    def test_single_pair_default_returns_struct(self):
        it = _make_iter([(b"\x01\x02\x03", b"val")])
        assert it.next() is True
        item = it.value()
        assert isinstance(item, Struct)
        assert it.next() is False

    def test_multiple_pairs(self):
        pairs = [(b"\x01\x02\x01", b"a"), (b"\x01\x02\x02", b"b")]
        results = _collect(_make_iter(pairs))
        assert len(results) == 2

    def test_value_before_next_raises(self):
        it = _make_iter([(b"\x01\x02\x03", b"v")])
        with pytest.raises(ValueError, match="No current element"):
            it.value()

    def test_value_after_exhaustion_raises(self):
        it = _make_iter([(b"\x01\x02\x03", b"v")])
        it.next()
        it.next()  # exhausted
        with pytest.raises(ValueError, match="No current element"):
            it.value()

    def test_default_struct_contains_full_key_and_value(self):
        it = _make_iter([(b"\x01\x02\xAA", b"data")])
        it.next()
        s = it.value()
        assert s[0].value == b"\x01\x02\xAA"
        assert s[1].value == b"data"


# ---------------------------------------------------------------------------
# REMOVE_PREFIX option
# ---------------------------------------------------------------------------

class TestRemovePrefix:
    """FindOptions.REMOVE_PREFIX strips prefix_length bytes from key."""

    def test_removes_prefix_from_key(self):
        it = _make_iter(
            [(b"\x01\x02\xAA\xBB", b"val")],
            prefix_len=2,
            options=FindOptions.REMOVE_PREFIX,
        )
        it.next()
        s = it.value()
        assert s[0].value == b"\xAA\xBB"

    def test_full_key_equals_prefix_yields_empty_key(self):
        it = _make_iter(
            [(b"\x01\x02", b"val")],
            prefix_len=2,
            options=FindOptions.REMOVE_PREFIX,
        )
        it.next()
        s = it.value()
        assert s[0].value == b""

    def test_value_unchanged_by_remove_prefix(self):
        it = _make_iter(
            [(b"\x01\x02\x03", b"data")],
            prefix_len=2,
            options=FindOptions.REMOVE_PREFIX,
        )
        it.next()
        s = it.value()
        assert s[1].value == b"data"


# ---------------------------------------------------------------------------
# KEYS_ONLY option
# ---------------------------------------------------------------------------

class TestKeysOnly:
    """FindOptions.KEYS_ONLY returns only the key as ByteString."""

    def test_returns_bytestring_key(self):
        it = _make_iter(
            [(b"\x01\x02\xAA", b"val")],
            options=FindOptions.KEYS_ONLY,
        )
        it.next()
        v = it.value()
        assert isinstance(v, ByteString)
        assert v.value == b"\x01\x02\xAA"

    def test_keys_only_with_remove_prefix(self):
        it = _make_iter(
            [(b"\x01\x02\xAA", b"val")],
            prefix_len=2,
            options=FindOptions.KEYS_ONLY | FindOptions.REMOVE_PREFIX,
        )
        it.next()
        v = it.value()
        assert isinstance(v, ByteString)
        assert v.value == b"\xAA"


# ---------------------------------------------------------------------------
# VALUES_ONLY option
# ---------------------------------------------------------------------------

class TestValuesOnly:
    """FindOptions.VALUES_ONLY returns only the value as ByteString."""

    def test_returns_bytestring_value(self):
        it = _make_iter(
            [(b"\x01\x02\xAA", b"myval")],
            options=FindOptions.VALUES_ONLY,
        )
        it.next()
        v = it.value()
        assert isinstance(v, ByteString)
        assert v.value == b"myval"

    def test_values_only_ignores_key(self):
        pairs = [(b"\x01\x02\x01", b"a"), (b"\x01\x02\x02", b"b")]
        results = _collect(_make_iter(pairs, options=FindOptions.VALUES_ONLY))
        assert len(results) == 2
        assert results[0].value == b"a"
        assert results[1].value == b"b"


# ---------------------------------------------------------------------------
# DESERIALIZE_VALUES option
# ---------------------------------------------------------------------------

# Pre-computed serialized Array([ByteString(b"field0"), ByteString(b"field1")])
_SERIALIZED_ARRAY = b'@\x02(\x06field0(\x06field1'


class TestDeserializeValues:
    """FindOptions.DESERIALIZE_VALUES deserializes the stored value."""

    def test_deserialize_returns_array(self):
        it = _make_iter(
            [(b"\x01\x02\x03", _SERIALIZED_ARRAY)],
            options=FindOptions.DESERIALIZE_VALUES,
        )
        it.next()
        s = it.value()
        # Default: Struct(key, deserialized_value)
        assert isinstance(s, Struct)
        result_val = s[1]
        assert isinstance(result_val, Array)
        assert len(result_val) == 2

    def test_deserialize_with_values_only(self):
        it = _make_iter(
            [(b"\x01\x02\x03", _SERIALIZED_ARRAY)],
            options=FindOptions.DESERIALIZE_VALUES | FindOptions.VALUES_ONLY,
        )
        it.next()
        v = it.value()
        assert isinstance(v, Array)
        assert v[0].value == b"field0"
        assert v[1].value == b"field1"


# ---------------------------------------------------------------------------
# PICK_FIELD0 / PICK_FIELD1 options
# ---------------------------------------------------------------------------

class TestPickField:
    """FindOptions.PICK_FIELD0/PICK_FIELD1 extract from deserialized array."""

    def test_pick_field0(self):
        it = _make_iter(
            [(b"\x01\x02\x03", _SERIALIZED_ARRAY)],
            options=(
                FindOptions.DESERIALIZE_VALUES
                | FindOptions.PICK_FIELD0
                | FindOptions.VALUES_ONLY
            ),
        )
        it.next()
        v = it.value()
        assert isinstance(v, ByteString)
        assert v.value == b"field0"

    def test_pick_field1(self):
        it = _make_iter(
            [(b"\x01\x02\x03", _SERIALIZED_ARRAY)],
            options=(
                FindOptions.DESERIALIZE_VALUES
                | FindOptions.PICK_FIELD1
                | FindOptions.VALUES_ONLY
            ),
        )
        it.next()
        v = it.value()
        assert isinstance(v, ByteString)
        assert v.value == b"field1"
