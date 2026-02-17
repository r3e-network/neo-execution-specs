"""Integration tests for System.Contract.CallNative dispatch."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from neo.hardfork import Hardfork
from neo.native import initialize_native_contracts
from neo.protocol_settings import ProtocolSettings
from neo.smartcontract.application_engine import ApplicationEngine
from neo.smartcontract.call_flags import CallFlags
from neo.vm.types import Array, ByteString, Integer, InteropInterface, Map


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

    def find(self, prefix: Any):
        return iter([])


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


def _engine_for_native_method(
    *,
    contract: Any,
    offset: int,
    snapshot: Any | None = None,
    settings: Any | None = None,
) -> ApplicationEngine:
    engine = ApplicationEngine(snapshot=snapshot, protocol_settings=settings)
    engine.load_script(b"\x00" * (offset + 1))
    assert engine.current_context is not None
    engine.current_context.ip = offset
    engine._require_current_script_hash = lambda: contract.hash  # type: ignore[attr-defined]
    return engine


def _active_method_offset(contract: Any, context: Any, method_name: str) -> int | None:
    for offset, metadata in contract.get_active_methods_by_offset(context).items():
        if metadata.name == method_name:
            return offset
    return None


def _callnative_ip_for_method(method: Any) -> int:
    return method.descriptor.offset + 1


def test_callnative_policy_is_blocked_snapshot_signature() -> None:
    contracts = initialize_native_contracts()
    policy = contracts["PolicyContract"]
    method = policy.get_method("isBlocked")
    assert method is not None

    snapshot = _Snapshot()
    engine = _engine_for_native_method(
        contract=policy,
        offset=_callnative_ip_for_method(method),
        snapshot=snapshot,
    )

    engine.push(ByteString(bytes([0x11]) * 20))
    engine.push(Integer(0))  # version
    engine._contract_call_native(engine)  # noqa: SLF001 - integration lock

    assert engine.pop().get_integer() == 0


def test_callnative_notary_verify_engine_signature() -> None:
    contracts = initialize_native_contracts()
    notary = contracts["Notary"]
    method = notary.get_method("verify")
    assert method is not None

    snapshot = _Snapshot()
    engine = _engine_for_native_method(
        contract=notary,
        offset=_callnative_ip_for_method(method),
        snapshot=snapshot,
    )

    engine.push(ByteString(b"\x00" * 64))
    engine.push(Integer(0))  # version
    engine._contract_call_native(engine)  # noqa: SLF001 - integration lock

    assert engine.pop().get_integer() == 0


def test_callnative_stdlib_value_context_signature() -> None:
    contracts = initialize_native_contracts()
    stdlib = contracts["StdLib"]
    method = stdlib.get_method("base64UrlEncode")
    assert method is not None

    settings = ProtocolSettings.mainnet()
    settings.hardforks[Hardfork.HF_ECHIDNA] = 0
    snapshot = _Snapshot(settings=settings, index=0)
    engine = _engine_for_native_method(
        contract=stdlib,
        offset=_callnative_ip_for_method(method),
        snapshot=snapshot,
        settings=settings,
    )

    engine.push(ByteString(b"hello"))
    engine.push(Integer(0))  # version
    engine._contract_call_native(engine)  # noqa: SLF001 - integration lock

    assert engine.pop().get_string() == "aGVsbG8"


def test_callnative_contract_management_is_contract_hardfork_gated() -> None:
    contracts = initialize_native_contracts()
    contract_mgmt = contracts["ContractManagement"]
    settings = _settings_with_hardforks(echidna=100, faun=200)

    pre_snapshot = _Snapshot(settings=settings, index=99)
    assert _active_method_offset(contract_mgmt, pre_snapshot, "isContract") is None

    post_snapshot = _Snapshot(settings=settings, index=100)
    post_offset = _active_method_offset(contract_mgmt, post_snapshot, "isContract")
    assert post_offset is not None
    post_engine = _engine_for_native_method(
        contract=contract_mgmt,
        offset=post_offset,
        snapshot=post_snapshot,
        settings=settings,
    )
    post_engine.push(ByteString(bytes([0x33]) * 20))
    post_engine.push(Integer(0))  # version
    post_engine._contract_call_native(post_engine)  # noqa: SLF001 - integration lock
    assert post_engine.pop().get_integer() == 0


def test_callnative_policy_get_exec_pico_fee_factor_hardfork_gated() -> None:
    contracts = initialize_native_contracts()
    policy = contracts["PolicyContract"]
    settings = _settings_with_hardforks(echidna=100, faun=200)

    pre_snapshot = _Snapshot(settings=settings, index=199)
    assert _active_method_offset(policy, pre_snapshot, "getExecPicoFeeFactor") is None

    post_snapshot = _Snapshot(settings=settings, index=200)
    post_offset = _active_method_offset(policy, post_snapshot, "getExecPicoFeeFactor")
    assert post_offset is not None
    post_engine = _engine_for_native_method(
        contract=policy,
        offset=post_offset,
        snapshot=post_snapshot,
        settings=settings,
    )
    post_engine.push(Integer(0))  # version
    post_engine._contract_call_native(post_engine)  # noqa: SLF001 - integration lock
    assert post_engine.pop().get_integer() == 10_000


def test_callnative_stdlib_base64_url_encode_hardfork_gated() -> None:
    contracts = initialize_native_contracts()
    stdlib = contracts["StdLib"]
    settings = _settings_with_hardforks(echidna=100, faun=200)

    pre_snapshot = _Snapshot(settings=settings, index=99)
    assert _active_method_offset(stdlib, pre_snapshot, "base64UrlEncode") is None

    post_snapshot = _Snapshot(settings=settings, index=100)
    post_offset = _active_method_offset(stdlib, post_snapshot, "base64UrlEncode")
    assert post_offset is not None
    post_engine = _engine_for_native_method(
        contract=stdlib,
        offset=post_offset,
        snapshot=post_snapshot,
        settings=settings,
    )
    post_engine.push(ByteString(b"hello"))
    post_engine.push(Integer(0))  # version
    post_engine._contract_call_native(post_engine)  # noqa: SLF001 - integration lock
    assert post_engine.pop().get_string() == "aGVsbG8"


def test_callnative_cryptolib_keccak256_is_cockatrice_gated() -> None:
    contracts = initialize_native_contracts()
    crypto = contracts["CryptoLib"]
    settings = _settings_with_hardforks(echidna=100, cockatrice=150, faun=200)

    pre_snapshot = _Snapshot(settings=settings, index=149)
    assert _active_method_offset(crypto, pre_snapshot, "keccak256") is None

    post_snapshot = _Snapshot(settings=settings, index=150)
    post_offset = _active_method_offset(crypto, post_snapshot, "keccak256")
    assert post_offset is not None
    post_engine = _engine_for_native_method(
        contract=crypto,
        offset=post_offset,
        snapshot=post_snapshot,
        settings=settings,
    )
    post_engine.push(ByteString(b"neo"))
    post_engine.push(Integer(0))  # version
    post_engine._contract_call_native(post_engine)  # noqa: SLF001 - integration lock

    result = post_engine.pop()
    assert isinstance(result, ByteString)
    assert len(result.get_bytes_unsafe()) == 32


def test_callnative_cryptolib_verify_with_ecdsa_switches_at_cockatrice() -> None:
    contracts = initialize_native_contracts()
    crypto = contracts["CryptoLib"]
    settings = _settings_with_hardforks(echidna=100, cockatrice=150, faun=200)

    pre_snapshot = _Snapshot(settings=settings, index=149)
    pre_offset = _active_method_offset(crypto, pre_snapshot, "verifyWithECDsa")
    assert pre_offset is not None
    pre_engine = _engine_for_native_method(
        contract=crypto,
        offset=pre_offset,
        snapshot=pre_snapshot,
        settings=settings,
    )
    pre_engine.push(ByteString(b"message"))
    pre_engine.push(ByteString(b"\x02" + (b"\x01" * 32)))
    pre_engine.push(ByteString(b"\x00" * 64))
    pre_engine.push(Integer(24))  # secp256k1Keccak256
    pre_engine.push(Integer(0))  # version
    with pytest.raises(Exception, match="curve_hash out of range"):
        pre_engine._contract_call_native(pre_engine)  # noqa: SLF001 - integration lock

    post_snapshot = _Snapshot(settings=settings, index=150)
    post_offset = _active_method_offset(crypto, post_snapshot, "verifyWithECDsa")
    assert post_offset is not None
    post_engine = _engine_for_native_method(
        contract=crypto,
        offset=post_offset,
        snapshot=post_snapshot,
        settings=settings,
    )
    post_engine.push(ByteString(b"message"))
    post_engine.push(ByteString(b"\x02" + (b"\x01" * 32)))
    post_engine.push(ByteString(b"\x00" * 64))
    post_engine.push(Integer(24))  # secp256k1Keccak256
    post_engine.push(Integer(0))  # version
    post_engine._contract_call_native(post_engine)  # noqa: SLF001 - integration lock
    assert post_engine.pop().get_integer() == 0


def test_callnative_rejects_insufficient_call_flags() -> None:
    contracts = initialize_native_contracts()
    policy = contracts["PolicyContract"]
    method = policy.get_method("isBlocked")
    assert method is not None

    snapshot = _Snapshot()
    engine = _engine_for_native_method(
        contract=policy,
        offset=_callnative_ip_for_method(method),
        snapshot=snapshot,
    )
    engine._current_call_flags = CallFlags.NONE  # type: ignore[assignment]

    engine.push(ByteString(bytes([0x22]) * 20))
    engine.push(Integer(0))  # version

    with pytest.raises(Exception, match="Insufficient call flags"):
        engine._contract_call_native(engine)  # noqa: SLF001 - integration lock


def test_callnative_rejects_nonzero_version() -> None:
    contracts = initialize_native_contracts()
    policy = contracts["PolicyContract"]
    method = policy.get_method("isBlocked")
    assert method is not None

    snapshot = _Snapshot()
    engine = _engine_for_native_method(
        contract=policy,
        offset=_callnative_ip_for_method(method),
        snapshot=snapshot,
    )
    engine.push(ByteString(bytes([0x22]) * 20))
    engine.push(Integer(1))  # unsupported native-version selector

    with pytest.raises(Exception, match="version 1"):
        engine._contract_call_native(engine)  # noqa: SLF001 - integration lock


def test_callnative_policy_offset_map_shifts_across_hardforks() -> None:
    contracts = initialize_native_contracts()
    policy = contracts["PolicyContract"]
    settings = _settings_with_hardforks(echidna=100, faun=200)

    # Offset 29 points to getStoragePrice before HF_Faun because Faun-only
    # methods are excluded from the active native method map.
    pre_snapshot = _Snapshot(settings=settings, index=99)
    assert _active_method_offset(policy, pre_snapshot, "getStoragePrice") == 29
    pre_engine = _engine_for_native_method(
        contract=policy,
        offset=29,
        snapshot=pre_snapshot,
        settings=settings,
    )
    pre_engine.push(Integer(0))  # version
    pre_engine._contract_call_native(pre_engine)  # noqa: SLF001 - integration lock
    assert pre_engine.pop().get_integer() == 1_000

    # At HF_Faun, offset 29 resolves to getExecPicoFeeFactor.
    post_snapshot = _Snapshot(settings=settings, index=200)
    assert _active_method_offset(policy, post_snapshot, "getExecPicoFeeFactor") == 29
    post_engine = _engine_for_native_method(
        contract=policy,
        offset=29,
        snapshot=post_snapshot,
        settings=settings,
    )
    post_engine.push(Integer(0))  # version
    post_engine._contract_call_native(post_engine)  # noqa: SLF001 - integration lock
    assert post_engine.pop().get_integer() == 10_000


def test_callnative_requires_active_syscall_offset_without_descriptor_fallback() -> None:
    contracts = initialize_native_contracts()
    policy = contracts["PolicyContract"]
    method = policy.get_method("unblockAccount")
    assert method is not None

    settings = _settings_with_hardforks(echidna=100, faun=200)
    snapshot = _Snapshot(settings=settings, index=199)
    active_offset = _active_method_offset(policy, snapshot, "unblockAccount")
    assert active_offset is not None

    descriptor_ip = _callnative_ip_for_method(method)
    assert descriptor_ip != active_offset

    engine = _engine_for_native_method(
        contract=policy,
        offset=descriptor_ip,
        snapshot=snapshot,
        settings=settings,
    )
    engine.push(Integer(0))  # version
    with pytest.raises(Exception, match="Method not found at offset"):
        engine._contract_call_native(engine)  # noqa: SLF001 - integration lock


@pytest.mark.parametrize(
    ("method_name", "expected"),
    [
        ("getMillisecondsPerBlock", 15_000),
        ("getMaxValidUntilBlockIncrement", 5_760),
        ("getMaxTraceableBlocks", 2_102_400),
    ],
)
def test_callnative_policy_echidna_read_methods_hardfork_gated(
    method_name: str, expected: int
) -> None:
    contracts = initialize_native_contracts()
    policy = contracts["PolicyContract"]
    settings = _settings_with_hardforks(echidna=100, faun=200)

    pre_snapshot = _Snapshot(settings=settings, index=99)
    assert _active_method_offset(policy, pre_snapshot, method_name) is None

    post_snapshot = _Snapshot(settings=settings, index=100)
    post_offset = _active_method_offset(policy, post_snapshot, method_name)
    assert post_offset is not None
    post_engine = _engine_for_native_method(
        contract=policy,
        offset=post_offset,
        snapshot=post_snapshot,
        settings=settings,
    )
    post_engine.push(Integer(0))  # version
    post_engine._contract_call_native(post_engine)  # noqa: SLF001 - integration lock
    assert post_engine.pop().get_integer() == expected


@pytest.mark.parametrize(
    ("method_name", "arg"),
    [
        ("hexEncode", ByteString(b"hi")),
        ("hexDecode", ByteString(b"6869")),
    ],
)
def test_callnative_stdlib_faun_codec_methods_hardfork_gated(
    method_name: str, arg: ByteString
) -> None:
    contracts = initialize_native_contracts()
    stdlib = contracts["StdLib"]
    settings = _settings_with_hardforks(echidna=100, faun=200)

    pre_snapshot = _Snapshot(settings=settings, index=199)
    assert _active_method_offset(stdlib, pre_snapshot, method_name) is None

    post_snapshot = _Snapshot(settings=settings, index=200)
    post_offset = _active_method_offset(stdlib, post_snapshot, method_name)
    assert post_offset is not None
    post_engine = _engine_for_native_method(
        contract=stdlib,
        offset=post_offset,
        snapshot=post_snapshot,
        settings=settings,
    )
    post_engine.push(arg)
    post_engine.push(Integer(0))  # version
    post_engine._contract_call_native(post_engine)  # noqa: SLF001 - integration lock

    result = post_engine.pop()
    assert isinstance(result, ByteString)
    if method_name == "hexEncode":
        assert result.get_string() == "6869"
    else:
        assert result.get_bytes_unsafe() == b"hi"


@pytest.mark.parametrize(
    "method_name",
    ["getBlockedAccounts", "getWhitelistFeeContracts"],
)
def test_callnative_policy_faun_iterator_methods_hardfork_gated(method_name: str) -> None:
    contracts = initialize_native_contracts()
    policy = contracts["PolicyContract"]
    settings = _settings_with_hardforks(echidna=100, faun=200)

    pre_snapshot = _Snapshot(settings=settings, index=199)
    assert _active_method_offset(policy, pre_snapshot, method_name) is None

    post_snapshot = _Snapshot(settings=settings, index=200)
    post_offset = _active_method_offset(policy, post_snapshot, method_name)
    assert post_offset is not None
    post_engine = _engine_for_native_method(
        contract=policy,
        offset=post_offset,
        snapshot=post_snapshot,
        settings=settings,
    )
    post_engine.push(Integer(0))  # version
    post_engine._contract_call_native(post_engine)  # noqa: SLF001 - integration lock

    result = post_engine.pop()
    assert isinstance(result, InteropInterface)


def test_callnative_native_list_result_pushes_vm_array() -> None:
    contracts = initialize_native_contracts()
    neo_token = contracts["NeoToken"]
    method = neo_token.get_method("getCommittee")
    assert method is not None

    snapshot = _Snapshot()
    engine = _engine_for_native_method(
        contract=neo_token,
        offset=_callnative_ip_for_method(method),
        snapshot=snapshot,
    )
    engine.push(Integer(0))  # version
    engine._contract_call_native(engine)  # noqa: SLF001 - integration lock

    result = engine.pop()
    assert isinstance(result, Array)
    assert len(result) == 0


def test_callnative_native_uint160_result_pushes_bytestring() -> None:
    contracts = initialize_native_contracts()
    neo_token = contracts["NeoToken"]
    method = neo_token.get_method("getCommitteeAddress")
    assert method is not None

    snapshot = _Snapshot()
    engine = _engine_for_native_method(
        contract=neo_token,
        offset=_callnative_ip_for_method(method),
        snapshot=snapshot,
    )
    engine.push(Integer(0))  # version
    engine._contract_call_native(engine)  # noqa: SLF001 - integration lock

    result = engine.pop()
    assert isinstance(result, ByteString)
    assert result.get_bytes_unsafe() == b"\x00" * 20


def test_callnative_native_list_of_strings_result_is_vm_array() -> None:
    contracts = initialize_native_contracts()
    stdlib = contracts["StdLib"]
    method = stdlib.get_method("stringSplit")
    assert method is not None

    snapshot = _Snapshot()
    engine = _engine_for_native_method(
        contract=stdlib,
        offset=_callnative_ip_for_method(method),
        snapshot=snapshot,
    )
    engine.push(ByteString(b"a,b,,c"))
    engine.push(ByteString(b","))
    engine.push(Integer(1))  # removeEmptyEntries=True
    engine.push(Integer(0))  # version
    engine._contract_call_native(engine)  # noqa: SLF001 - integration lock

    result = engine.pop()
    assert isinstance(result, Array)
    assert [item.get_string() for item in result] == ["a", "b", "c"]


def test_callnative_native_uint256_result_pushes_bytestring() -> None:
    contracts = initialize_native_contracts()
    ledger = contracts["LedgerContract"]
    method = ledger.get_method("currentHash")
    assert method is not None

    snapshot = _Snapshot()
    engine = _engine_for_native_method(
        contract=ledger,
        offset=_callnative_ip_for_method(method),
        snapshot=snapshot,
    )
    engine.push(Integer(0))  # version
    engine._contract_call_native(engine)  # noqa: SLF001 - integration lock

    result = engine.pop()
    assert isinstance(result, ByteString)
    assert result.get_bytes_unsafe() == b"\x00" * 32


def test_callnative_native_dict_result_pushes_vm_map() -> None:
    contracts = initialize_native_contracts()
    stdlib = contracts["StdLib"]
    method = stdlib.get_method("jsonDeserialize")
    assert method is not None

    snapshot = _Snapshot()
    engine = _engine_for_native_method(
        contract=stdlib,
        offset=_callnative_ip_for_method(method),
        snapshot=snapshot,
    )
    engine.push(ByteString(b"{\"a\":1,\"b\":\"x\"}"))
    engine.push(Integer(0))  # version
    engine._contract_call_native(engine)  # noqa: SLF001 - integration lock

    result = engine.pop()
    assert isinstance(result, Map)
    assert len(result) == 2
