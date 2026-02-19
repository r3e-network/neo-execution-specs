"""Integration tests for System.Contract.Call/CALLT with native contracts."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest

from neo.crypto import hash160
from neo.hardfork import Hardfork
from neo.native import initialize_native_contracts
from neo.native.contract_management import PREFIX_CONTRACT, ContractState
from neo.protocol_settings import ProtocolSettings
from neo.smartcontract.application_engine import ApplicationEngine
from neo.smartcontract.call_flags import CallFlags
from neo.smartcontract.nef_file import MethodToken
from neo.types import UInt160
from neo.vm.types import Array, ByteString, Integer


class _Snapshot:
    def __init__(self, *, settings: Any | None = None, index: int = 0) -> None:
        self._data: dict[Any, Any] = {}
        if settings is not None:
            self.protocol_settings = settings
        self.persisting_block = SimpleNamespace(index=index)

    def get(self, key: Any) -> Any | None:
        return self._data.get(key)

    def add(self, key: Any, value: Any) -> None:
        self._data[key] = value

    def contains(self, key: Any) -> bool:
        return key in self._data


def _settings_with_hardforks(
    *,
    echidna: int = 100,
    cockatrice: int = 150,
    faun: int = 200,
) -> ProtocolSettings:
    settings = ProtocolSettings.mainnet()
    settings.hardforks[Hardfork.HF_ECHIDNA] = echidna
    settings.hardforks[Hardfork.HF_COCKATRICE] = cockatrice
    settings.hardforks[Hardfork.HF_FAUN] = faun
    return settings


def test_system_contract_call_dispatches_native_method() -> None:
    contracts = initialize_native_contracts()
    policy = contracts["PolicyContract"]

    engine = ApplicationEngine(snapshot=_Snapshot())
    engine.load_script(b"\x00")

    engine.push(Array(items=[]))
    engine.push(ByteString(bytes(policy.hash)))
    engine.push(ByteString(b"getFeePerByte"))
    engine.push(Integer(int(CallFlags.READ_STATES)))
    engine._contract_call(engine)

    assert engine.pop().get_integer() == 1000


def test_callt_dispatches_native_method_token() -> None:
    contracts = initialize_native_contracts()
    policy = contracts["PolicyContract"]

    token = MethodToken(
        hash=bytes(policy.hash),
        method="getFeePerByte",
        parameters_count=0,
        has_return_value=True,
        call_flags=int(CallFlags.READ_STATES),
    )

    engine = ApplicationEngine(snapshot=_Snapshot())
    engine.load_script_with_tokens(b"\x00", [token])
    engine._handle_token_call(engine, 0)

    assert engine.pop().get_integer() == 1000


def test_system_contract_call_native_argument_order_is_preserved() -> None:
    contracts = initialize_native_contracts()
    stdlib = contracts["StdLib"]

    engine = ApplicationEngine(snapshot=_Snapshot())
    engine.load_script(b"\x00")

    args = Array(
        items=[
            ByteString(b"a,b,,c"),
            ByteString(b","),
            Integer(1),  # removeEmptyEntries=True
        ]
    )
    engine.push(args)
    engine.push(ByteString(bytes(stdlib.hash)))
    engine.push(ByteString(b"stringSplit"))
    engine.push(Integer(int(CallFlags.NONE)))
    engine._contract_call(engine)

    result = engine.pop()
    assert isinstance(result, Array)
    assert [item.get_string() for item in result] == ["a", "b", "c"]


def test_system_contract_call_native_enforces_caller_permissions() -> None:
    contracts = initialize_native_contracts()
    policy = contracts["PolicyContract"]

    engine = ApplicationEngine(snapshot=_Snapshot())
    caller_script = b"\x01"
    callee_script = b"\x02"
    caller_hash = UInt160(hash160(caller_script))

    caller_state = ContractState(
        id=1,
        hash=caller_hash,
        nef=caller_script,
        manifest=json.dumps({"permissions": []}).encode("utf-8"),
    )
    caller_key = bytes([PREFIX_CONTRACT]) + bytes(caller_hash)
    engine.snapshot.add(caller_key, caller_state.to_bytes())  # type: ignore[union-attr]

    engine.load_script(caller_script)
    engine.load_script(callee_script)
    assert len(engine.invocation_stack) == 2

    engine.push(Array(items=[]))
    engine.push(ByteString(bytes(policy.hash)))
    engine.push(ByteString(b"getFeePerByte"))
    engine.push(Integer(int(CallFlags.READ_STATES)))

    with pytest.raises(Exception, match="Method not allowed"):
        engine._contract_call(engine)


def test_system_contract_call_native_method_is_hardfork_gated() -> None:
    contracts = initialize_native_contracts()
    policy = contracts["PolicyContract"]
    settings = _settings_with_hardforks(echidna=100, faun=200)

    pre_engine = ApplicationEngine(snapshot=_Snapshot(settings=settings, index=199), protocol_settings=settings)
    pre_engine.load_script(b"\x00")
    pre_engine.push(Array(items=[]))
    pre_engine.push(ByteString(bytes(policy.hash)))
    pre_engine.push(ByteString(b"getExecPicoFeeFactor"))
    pre_engine.push(Integer(int(CallFlags.READ_STATES)))
    with pytest.raises(Exception, match="Method not allowed"):
        pre_engine._contract_call(pre_engine)

    post_engine = ApplicationEngine(snapshot=_Snapshot(settings=settings, index=200), protocol_settings=settings)
    post_engine.load_script(b"\x00")
    post_engine.push(Array(items=[]))
    post_engine.push(ByteString(bytes(policy.hash)))
    post_engine.push(ByteString(b"getExecPicoFeeFactor"))
    post_engine.push(Integer(int(CallFlags.READ_STATES)))
    post_engine._contract_call(post_engine)
    assert post_engine.pop().get_integer() == 300_000


def test_callt_native_method_token_is_hardfork_gated() -> None:
    contracts = initialize_native_contracts()
    policy = contracts["PolicyContract"]
    settings = _settings_with_hardforks(echidna=100, faun=200)

    token = MethodToken(
        hash=bytes(policy.hash),
        method="getExecPicoFeeFactor",
        parameters_count=0,
        has_return_value=True,
        call_flags=int(CallFlags.READ_STATES),
    )

    pre_engine = ApplicationEngine(snapshot=_Snapshot(settings=settings, index=199), protocol_settings=settings)
    pre_engine.load_script_with_tokens(b"\x00", [token])
    with pytest.raises(Exception, match="Method not allowed"):
        pre_engine._handle_token_call(pre_engine, 0)

    post_engine = ApplicationEngine(snapshot=_Snapshot(settings=settings, index=200), protocol_settings=settings)
    post_engine.load_script_with_tokens(b"\x00", [token])
    post_engine._handle_token_call(post_engine, 0)
    assert post_engine.pop().get_integer() == 300_000


def test_system_contract_call_native_contract_activation_is_hardfork_gated() -> None:
    contracts = initialize_native_contracts()
    treasury = contracts["Treasury"]
    settings = _settings_with_hardforks(echidna=100, faun=200)

    pre_engine = ApplicationEngine(snapshot=_Snapshot(settings=settings, index=199), protocol_settings=settings)
    pre_engine.load_script(b"\x00")
    pre_engine.push(Array(items=[]))
    pre_engine.push(ByteString(bytes(treasury.hash)))
    pre_engine.push(ByteString(b"verify"))
    pre_engine.push(Integer(int(CallFlags.READ_STATES)))
    with pytest.raises(Exception, match="Contract not found"):
        pre_engine._contract_call(pre_engine)

    post_engine = ApplicationEngine(snapshot=_Snapshot(settings=settings, index=200), protocol_settings=settings)
    post_engine.load_script(b"\x00")
    post_engine.push(Array(items=[]))
    post_engine.push(ByteString(bytes(treasury.hash)))
    post_engine.push(ByteString(b"verify"))
    post_engine.push(Integer(int(CallFlags.READ_STATES)))
    post_engine._contract_call(post_engine)
    assert post_engine.pop().get_integer() == 0


def test_system_contract_call_cryptolib_keccak256_is_cockatrice_gated() -> None:
    contracts = initialize_native_contracts()
    crypto = contracts["CryptoLib"]
    settings = _settings_with_hardforks(echidna=100, cockatrice=150, faun=200)

    pre_engine = ApplicationEngine(snapshot=_Snapshot(settings=settings, index=149), protocol_settings=settings)
    pre_engine.load_script(b"\x00")
    pre_engine.push(Array(items=[ByteString(b"neo")]))
    pre_engine.push(ByteString(bytes(crypto.hash)))
    pre_engine.push(ByteString(b"keccak256"))
    pre_engine.push(Integer(int(CallFlags.NONE)))
    with pytest.raises(Exception, match="Method not allowed"):
        pre_engine._contract_call(pre_engine)

    post_engine = ApplicationEngine(snapshot=_Snapshot(settings=settings, index=150), protocol_settings=settings)
    post_engine.load_script(b"\x00")
    post_engine.push(Array(items=[ByteString(b"neo")]))
    post_engine.push(ByteString(bytes(crypto.hash)))
    post_engine.push(ByteString(b"keccak256"))
    post_engine.push(Integer(int(CallFlags.NONE)))
    post_engine._contract_call(post_engine)
    result = post_engine.pop()
    assert isinstance(result, ByteString)
    assert len(result.get_bytes_unsafe()) == 32


def test_system_contract_call_cryptolib_verify_with_ecdsa_switches_at_cockatrice() -> None:
    contracts = initialize_native_contracts()
    crypto = contracts["CryptoLib"]
    settings = _settings_with_hardforks(echidna=100, cockatrice=150, faun=200)

    args = Array(
        items=[
            ByteString(b"message"),
            ByteString(b"\x02" + (b"\x01" * 32)),
            ByteString(b"\x00" * 64),
            Integer(24),  # secp256k1Keccak256
        ]
    )

    pre_engine = ApplicationEngine(snapshot=_Snapshot(settings=settings, index=149), protocol_settings=settings)
    pre_engine.load_script(b"\x00")
    pre_engine.push(args)
    pre_engine.push(ByteString(bytes(crypto.hash)))
    pre_engine.push(ByteString(b"verifyWithECDsa"))
    pre_engine.push(Integer(int(CallFlags.NONE)))
    with pytest.raises(Exception, match="curve_hash out of range"):
        pre_engine._contract_call(pre_engine)

    post_engine = ApplicationEngine(snapshot=_Snapshot(settings=settings, index=150), protocol_settings=settings)
    post_engine.load_script(b"\x00")
    post_engine.push(
        Array(
            items=[
                ByteString(b"message"),
                ByteString(b"\x02" + (b"\x01" * 32)),
                ByteString(b"\x00" * 64),
                Integer(24),  # secp256k1Keccak256
            ]
        )
    )
    post_engine.push(ByteString(bytes(crypto.hash)))
    post_engine.push(ByteString(b"verifyWithECDsa"))
    post_engine.push(Integer(int(CallFlags.NONE)))
    post_engine._contract_call(post_engine)
    assert post_engine.pop().get_integer() == 0
