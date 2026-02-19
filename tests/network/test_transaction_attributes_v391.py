"""Neo N3 v3.9.1 transaction-attribute wire parity checks."""

from __future__ import annotations

import pytest

from neo.io.binary_reader import BinaryReader
from neo.io.binary_writer import BinaryWriter
from neo.network.payloads.transaction_attribute import (
    ConflictsAttribute,
    HighPriorityAttribute,
    NotValidBeforeAttribute,
    NotaryAssistedAttribute,
    OracleResponseAttribute,
    OracleResponseCode,
    TransactionAttribute,
    TransactionAttributeType,
)


def _roundtrip(attribute: TransactionAttribute) -> TransactionAttribute:
    writer = BinaryWriter()
    attribute.serialize(writer)
    reader = BinaryReader(writer.to_bytes())
    clone = TransactionAttribute.deserialize(reader)
    assert reader.remaining == 0
    return clone


def test_transaction_attribute_type_values_match_v391() -> None:
    assert TransactionAttributeType.HIGH_PRIORITY == 0x01
    assert TransactionAttributeType.ORACLE_RESPONSE == 0x11
    assert TransactionAttributeType.NOT_VALID_BEFORE == 0x20
    assert TransactionAttributeType.CONFLICTS == 0x21
    assert TransactionAttributeType.NOTARY_ASSISTED == 0x22


def test_high_priority_roundtrip() -> None:
    attribute = HighPriorityAttribute()
    clone = _roundtrip(attribute)
    assert isinstance(clone, HighPriorityAttribute)
    assert clone.type == TransactionAttributeType.HIGH_PRIORITY
    assert clone.allow_multiple is False
    assert clone.size == 1


def test_not_valid_before_roundtrip() -> None:
    attribute = NotValidBeforeAttribute(height=42)
    clone = _roundtrip(attribute)
    assert isinstance(clone, NotValidBeforeAttribute)
    assert clone.height == 42
    assert clone.allow_multiple is False
    assert clone.size == 5


def test_conflicts_roundtrip() -> None:
    attribute = ConflictsAttribute(hash=b"\x01" * 32)
    clone = _roundtrip(attribute)
    assert isinstance(clone, ConflictsAttribute)
    assert clone.hash == b"\x01" * 32
    assert clone.allow_multiple is True
    assert clone.size == 33


def test_notary_assisted_roundtrip() -> None:
    attribute = NotaryAssistedAttribute(nkeys=4)
    clone = _roundtrip(attribute)
    assert isinstance(clone, NotaryAssistedAttribute)
    assert clone.nkeys == 4
    assert clone.allow_multiple is False
    assert clone.size == 2


def test_oracle_response_roundtrip_success_and_non_success() -> None:
    success = OracleResponseAttribute(
        id=123,
        code=OracleResponseCode.SUCCESS,
        result=b"result",
    )
    clone = _roundtrip(success)
    assert isinstance(clone, OracleResponseAttribute)
    assert clone.id == 123
    assert clone.code == OracleResponseCode.SUCCESS
    assert clone.result == b"result"

    non_success = OracleResponseAttribute(
        id=456,
        code=OracleResponseCode.TIMEOUT,
        result=b"",
    )
    clone = _roundtrip(non_success)
    assert isinstance(clone, OracleResponseAttribute)
    assert clone.code == OracleResponseCode.TIMEOUT
    assert clone.result == b""


def test_oracle_response_non_success_requires_empty_result() -> None:
    writer = BinaryWriter()
    writer.write_byte(int(TransactionAttributeType.ORACLE_RESPONSE))
    writer.write_uint64(1)
    writer.write_byte(int(OracleResponseCode.TIMEOUT))
    writer.write_var_bytes(b"not-empty")
    with pytest.raises(ValueError):
        TransactionAttribute.deserialize(BinaryReader(writer.to_bytes()))


def test_oracle_response_invalid_code_rejected() -> None:
    writer = BinaryWriter()
    writer.write_byte(int(TransactionAttributeType.ORACLE_RESPONSE))
    writer.write_uint64(1)
    writer.write_byte(0xAA)  # Not defined in OracleResponseCode.
    writer.write_var_bytes(b"")
    with pytest.raises(ValueError):
        TransactionAttribute.deserialize(BinaryReader(writer.to_bytes()))


def test_transaction_attribute_unknown_type_rejected() -> None:
    writer = BinaryWriter()
    writer.write_byte(0xFF)
    with pytest.raises(ValueError):
        TransactionAttribute.deserialize(BinaryReader(writer.to_bytes()))

