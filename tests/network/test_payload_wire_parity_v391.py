"""Neo N3 v3.9.1 payload wire-format parity checks."""

from __future__ import annotations

import pytest

from neo.io.binary_reader import BinaryReader
from neo.io.binary_writer import BinaryWriter
from neo.network.payloads.filter_add import FilterAddPayload
from neo.network.payloads.filter_load import FilterLoadPayload
from neo.network.payloads.get_block_by_index import GetBlockByIndexPayload
from neo.network.payloads.get_blocks import GetBlocksPayload
from neo.network.payloads.get_data import GetDataPayload
from neo.network.payloads.header import Header
from neo.network.payloads.headers import HeadersPayload
from neo.network.payloads.inv import InvPayload
from neo.network.payloads.inventory_type import InventoryType
from neo.network.payloads.merkle_block import MerkleBlockPayload
from neo.network.payloads.witness import Witness


def _roundtrip(payload, cls):
    writer = BinaryWriter()
    payload.serialize(writer)
    data = writer.to_bytes()
    reader = BinaryReader(data)
    clone = cls.deserialize(reader)
    assert reader.remaining == 0
    return clone


def test_get_block_by_index_roundtrip_and_bounds() -> None:
    payload = GetBlockByIndexPayload(index_start=123, count=-1)
    clone = _roundtrip(payload, GetBlockByIndexPayload)
    assert clone.index_start == 123
    assert clone.count == -1

    with pytest.raises(ValueError):
        reader = BinaryReader((123).to_bytes(4, "little") + (0).to_bytes(2, "little", signed=True))
        GetBlockByIndexPayload.deserialize(reader)


def test_headers_roundtrip_requires_non_empty() -> None:
    header = Header(witness=Witness.empty())
    payload = HeadersPayload(headers=[header])
    clone = _roundtrip(payload, HeadersPayload)
    assert len(clone.headers) == 1
    assert clone.headers[0].index == header.index

    with pytest.raises(ValueError):
        HeadersPayload.deserialize(BinaryReader(b"\x00"))


def test_filter_load_roundtrip_and_k_limit() -> None:
    payload = FilterLoadPayload(filter=b"\x00\x01", k=50, tweak=42)
    clone = _roundtrip(payload, FilterLoadPayload)
    assert clone.filter == b"\x00\x01"
    assert clone.k == 50
    assert clone.tweak == 42

    writer = BinaryWriter()
    writer.write_var_bytes(b"\x00")
    writer.write_byte(51)
    writer.write_uint32(1)
    with pytest.raises(ValueError):
        FilterLoadPayload.deserialize(BinaryReader(writer.to_bytes()))


def test_filter_add_roundtrip_and_size_limit() -> None:
    payload = FilterAddPayload(data=b"\xAA" * 520)
    clone = _roundtrip(payload, FilterAddPayload)
    assert clone.data == payload.data

    writer = BinaryWriter()
    writer.write_var_bytes(b"\x01" * 521)
    with pytest.raises(ValueError):
        FilterAddPayload.deserialize(BinaryReader(writer.to_bytes()))


def test_merkle_block_roundtrip_and_flag_limit() -> None:
    payload = MerkleBlockPayload(
        header=Header(witness=Witness.empty()),
        tx_count=1,
        hashes=[],
        flags=b"",
    )
    clone = _roundtrip(payload, MerkleBlockPayload)
    assert clone.tx_count == 1
    assert clone.hashes == []
    assert clone.flags == b""

    writer = BinaryWriter()
    Header(witness=Witness.empty()).serialize(writer)
    writer.write_var_int(1)
    writer.write_var_int(0)
    writer.write_var_bytes(b"\x00\x00")
    with pytest.raises(ValueError):
        MerkleBlockPayload.deserialize(BinaryReader(writer.to_bytes()))


def test_get_blocks_roundtrip_and_count_bounds() -> None:
    payload = GetBlocksPayload(hash_start=b"\x01" * 32, count=5)
    clone = _roundtrip(payload, GetBlocksPayload)
    assert clone.hash_start == b"\x01" * 32
    assert clone.count == 5

    with pytest.raises(ValueError):
        GetBlocksPayload(hash_start=b"\x01" * 32, count=0)
    with pytest.raises(ValueError):
        GetBlocksPayload(hash_start=b"\x01" * 32, count=GetBlocksPayload.MAX_COUNT + 1)


def test_inv_roundtrip_and_type_validation() -> None:
    payload = InvPayload(type=InventoryType.TX, hashes=[b"\x02" * 32, b"\x03" * 32])
    clone = _roundtrip(payload, InvPayload)
    assert clone.type == InventoryType.TX
    assert clone.hashes == payload.hashes

    with pytest.raises(ValueError):
        writer = BinaryWriter()
        writer.write_byte(0xFF)
        writer.write_var_int(0)
        InvPayload.deserialize(BinaryReader(writer.to_bytes()))


def test_inv_create_group_max_hashes_count() -> None:
    hashes = [i.to_bytes(4, "little") + b"\x00" * 28 for i in range(InvPayload.MAX_HASHES_COUNT + 1)]
    chunks = InvPayload.create_group(InventoryType.TX, hashes)
    assert len(chunks) == 2
    assert len(chunks[0].hashes) == InvPayload.MAX_HASHES_COUNT
    assert len(chunks[1].hashes) == 1


def test_get_data_payload_wire_shape_matches_inv() -> None:
    payload = GetDataPayload(type=InventoryType.BLOCK, hashes=[b"\x04" * 32])
    clone = _roundtrip(payload, GetDataPayload)
    assert clone.type == InventoryType.BLOCK
    assert clone.hashes == [b"\x04" * 32]
