"""Shared Runtime.GetRandom parity helpers."""

from __future__ import annotations

from typing import Any

from neo.crypto import murmur128
from neo.hardfork import Hardfork
from neo.native.native_contract import NativeContract

LEGACY_PRICE = 1 << 4
ASPIDOCHELONE_PRICE = 1 << 13


def _coerce_hash256_bytes(value: Any) -> bytes:
    if isinstance(value, (bytes, bytearray)):
        data = bytes(value)
    elif value is None:
        data = b""
    else:
        data = b""
        to_array = getattr(value, "to_array", None)
        if callable(to_array):
            try:
                maybe = to_array()
            except TypeError:
                maybe = None
            if isinstance(maybe, (bytes, bytearray)):
                data = bytes(maybe)
        if not data:
            to_bytes = getattr(value, "to_bytes", None)
            if callable(to_bytes):
                try:
                    maybe = to_bytes()
                except TypeError:
                    maybe = None
                if isinstance(maybe, (bytes, bytearray)):
                    data = bytes(maybe)
        if not data:
            raw_data = getattr(value, "data", None)
            if isinstance(raw_data, (bytes, bytearray)):
                data = bytes(raw_data)
        if not data:
            try:
                converted = bytes(value)
            except Exception:
                converted = b""
            data = converted if isinstance(converted, (bytes, bytearray)) else b""

    if len(data) < 32:
        data = data.ljust(32, b"\x00")
    return data[:32]


def _as_u64(value: Any) -> int:
    try:
        return int(value) & 0xFFFFFFFFFFFFFFFF
    except Exception:
        return 0


def _as_u32(value: Any) -> int:
    try:
        return int(value) & 0xFFFFFFFF
    except Exception:
        return 0


def _is_aspidochelone_enabled(engine: Any) -> bool:
    try:
        return bool(NativeContract.is_hardfork_enabled(engine, Hardfork.HF_ASPIDOCHELONE))
    except Exception:
        return False


def _ensure_nonce_data(engine: Any) -> bytes:
    existing = getattr(engine, "_random_nonce_data", None)
    if isinstance(existing, (bytes, bytearray)) and len(existing) == 16:
        return bytes(existing)

    container = getattr(engine, "script_container", None)
    tx_hash = _coerce_hash256_bytes(getattr(container, "hash", None))
    nonce_data = bytearray(tx_hash[:16])

    snapshot = getattr(engine, "snapshot", None)
    block = getattr(snapshot, "persisting_block", None) if snapshot is not None else None
    if block is not None:
        prefix = int.from_bytes(nonce_data[:8], "little") ^ _as_u64(getattr(block, "nonce", 0))
        nonce_data[:8] = prefix.to_bytes(8, "little")

    engine._random_nonce_data = bytes(nonce_data)
    counter = getattr(engine, "_random_counter", 0)
    if not isinstance(counter, int):
        engine._random_counter = 0
    return bytes(nonce_data)


def next_runtime_random(engine: Any) -> tuple[int, int]:
    """Return next Runtime.GetRandom value and its additional syscall price."""
    nonce_data = _ensure_nonce_data(engine)
    network_raw = getattr(engine, "network", 0)
    network = network_raw & 0xFFFFFFFF if isinstance(network_raw, int) else 0

    if _is_aspidochelone_enabled(engine):
        counter_raw = getattr(engine, "_random_counter", 0)
        random_times = counter_raw & 0xFFFFFFFF if isinstance(counter_raw, int) else 0
        seed = (network + random_times) & 0xFFFFFFFF
        buffer = murmur128(nonce_data, seed)
        engine._random_counter = (random_times + 1) & 0xFFFFFFFF
        price = ASPIDOCHELONE_PRICE
    else:
        buffer = murmur128(nonce_data, network)
        engine._random_nonce_data = buffer
        price = LEGACY_PRICE

    return int.from_bytes(buffer, "little", signed=False), price
