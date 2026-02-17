"""Tests for ApplicationEngine native handler dispatch adaptation."""

from __future__ import annotations

from types import SimpleNamespace

from neo.hardfork import Hardfork
from neo.native.std_lib import StdLib
from neo.protocol_settings import ProtocolSettings
from neo.smartcontract.application_engine import ApplicationEngine
from neo.vm.types import ByteString, Integer


def _engine_with_context(*, snapshot: object | None = None, settings: object | None = None) -> ApplicationEngine:
    engine = ApplicationEngine(snapshot=snapshot, protocol_settings=settings)
    engine.load_script(bytes([0x40]))  # RET; creates an execution context with an eval stack
    return engine


def test_invoke_native_handler_pops_engine_method_arguments_in_order() -> None:
    engine = _engine_with_context()
    outer_engine = engine
    engine.push(Integer(2))
    engine.push(Integer(3))

    captured: dict[str, tuple[int, int]] = {}

    def handler(engine, left: int, right: int) -> int:
        captured["args"] = (left, right)
        assert engine is outer_engine
        return left + right

    engine._invoke_native_handler(handler)  # noqa: SLF001 - dispatch adaptation behavior lock

    assert captured["args"] == (2, 3)
    assert engine.pop().get_integer() == 5


def test_invoke_native_handler_converts_uint160_annotation() -> None:
    from neo.types import UInt160

    raw = bytes([0xAB]) * 20
    engine = _engine_with_context()
    engine.push(ByteString(raw))

    def handler(engine, account: UInt160) -> bytes:
        assert engine is not None
        return account.data

    engine._invoke_native_handler(handler)  # noqa: SLF001 - dispatch adaptation behavior lock
    assert engine.pop().get_bytes_unsafe() == raw


def test_invoke_native_handler_supports_snapshot_first_signature() -> None:
    snapshot = SimpleNamespace(name="snap")
    engine = _engine_with_context(snapshot=snapshot)
    engine.push(Integer(7))

    seen: dict[str, object] = {}

    def handler(snapshot, index: int) -> int:
        seen["snapshot"] = snapshot
        seen["index"] = index
        return index

    engine._invoke_native_handler(handler)  # noqa: SLF001 - dispatch adaptation behavior lock

    assert seen["snapshot"] is snapshot
    assert seen["index"] == 7
    assert engine.pop().get_integer() == 7


def test_invoke_native_handler_supports_stdlib_context_pattern() -> None:
    settings = ProtocolSettings.mainnet()
    settings.hardforks[Hardfork.HF_ECHIDNA] = 100
    snapshot = SimpleNamespace(
        protocol_settings=settings,
        persisting_block=SimpleNamespace(index=100),
    )
    engine = _engine_with_context(snapshot=snapshot, settings=settings)
    engine.push(ByteString(b"hello"))

    stdlib = StdLib()
    engine._invoke_native_handler(stdlib.base64_url_encode)  # noqa: SLF001 - dispatch adaptation behavior lock

    assert engine.pop().get_string() == "aGVsbG8"
