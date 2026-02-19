"""Neo N3 v3.9.1 sync/SPV payload surface regression checks."""

from __future__ import annotations

from dataclasses import fields

import pytest

from neo.network.payloads.get_block_by_index import GetBlockByIndexPayload
from neo.network.payloads.headers import HeadersPayload
from neo.network.payloads.filter_load import FilterLoadPayload
from neo.network.payloads.filter_add import FilterAddPayload
from neo.network.payloads.merkle_block import MerkleBlockPayload
from neo.network.payloads.header import Header


def _field_names(cls: type) -> set[str]:
    return {item.name for item in fields(cls)}


def test_get_block_by_index_payload_shape_and_bounds() -> None:
    assert _field_names(GetBlockByIndexPayload) == {"index_start", "count"}
    assert HeadersPayload.MAX_HEADERS_COUNT == 2000

    assert GetBlockByIndexPayload(index_start=0, count=-1).count == -1
    assert GetBlockByIndexPayload(index_start=0, count=2000).count == 2000

    with pytest.raises(ValueError):
        GetBlockByIndexPayload(index_start=0, count=0)
    with pytest.raises(ValueError):
        GetBlockByIndexPayload(index_start=0, count=-2)
    with pytest.raises(ValueError):
        GetBlockByIndexPayload(index_start=0, count=2001)


def test_headers_payload_shape_and_bounds() -> None:
    assert _field_names(HeadersPayload) == {"headers"}
    assert HeadersPayload.MAX_HEADERS_COUNT == 2000

    payload = HeadersPayload(headers=[Header()])
    assert len(payload.headers) == 1

    with pytest.raises(ValueError):
        HeadersPayload(headers=[])
    with pytest.raises(ValueError):
        HeadersPayload(headers=[Header()] * 2001)


def test_filter_load_payload_shape_and_bounds() -> None:
    assert _field_names(FilterLoadPayload) == {"filter", "k", "tweak"}
    assert FilterLoadPayload.MAX_FILTER_BYTES == 36000
    assert FilterLoadPayload.MAX_HASH_FUNCTIONS == 50

    payload = FilterLoadPayload(filter=b"\x00", k=50, tweak=1)
    assert payload.k == 50

    with pytest.raises(ValueError):
        FilterLoadPayload(filter=b"\x00", k=51, tweak=1)
    with pytest.raises(ValueError):
        FilterLoadPayload(filter=b"\x00" * 36001, k=1, tweak=1)


def test_filter_add_payload_shape_and_bounds() -> None:
    assert _field_names(FilterAddPayload) == {"data"}
    assert FilterAddPayload.MAX_DATA_BYTES == 520

    payload = FilterAddPayload(data=b"\x01" * 520)
    assert len(payload.data) == 520

    with pytest.raises(ValueError):
        FilterAddPayload(data=b"\x01" * 521)


def test_merkle_block_payload_shape_and_bounds() -> None:
    assert _field_names(MerkleBlockPayload) == {"header", "tx_count", "hashes", "flags"}

    payload = MerkleBlockPayload(
        header=Header(),
        tx_count=5,
        hashes=[bytes(32)],
        flags=b"\x01",
    )
    assert payload.tx_count == 5

    with pytest.raises(ValueError):
        MerkleBlockPayload(
            header=Header(),
            tx_count=-1,
            hashes=[],
            flags=b"",
        )

    # Neo v3.9.1 wire deserializer allows empty hashes even when tx_count > 0.
    payload = MerkleBlockPayload(
        header=Header(),
        tx_count=5,
        hashes=[],
        flags=b"",
    )
    assert payload.tx_count == 5

    with pytest.raises(ValueError):
        MerkleBlockPayload(
            header=Header(),
            tx_count=1,
            hashes=[],
            flags=b"\x00\x00",
        )
