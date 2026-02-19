"""Neo v3.9.1 syscall compatibility tests.

These checks lock syscall metadata (price/call-flags/hardfork gating)
to official Neo v3.9.1 values so regressions are caught early.
"""

from types import SimpleNamespace

import pytest

from neo.hardfork import Hardfork
from neo.protocol_settings import ProtocolSettings
from neo.smartcontract.application_engine import ApplicationEngine
from neo.smartcontract.call_flags import CallFlags
from neo.smartcontract.interop_service import get_interop_hash, get_syscall, invoke_syscall
from neo.vm.types import NULL, ByteString

EXPECTED_SYSCALLS_V391: dict[str, tuple[int, CallFlags, Hardfork | None]] = {
    "System.Contract.Call": (1 << 15, CallFlags.READ_STATES | CallFlags.ALLOW_CALL, None),
    "System.Contract.CallNative": (0, CallFlags.NONE, None),
    "System.Contract.CreateMultisigAccount": (1 << 8, CallFlags.NONE, None),
    "System.Contract.CreateStandardAccount": (1 << 8, CallFlags.NONE, None),
    "System.Contract.GetCallFlags": (1 << 10, CallFlags.NONE, None),
    "System.Contract.NativeOnPersist": (0, CallFlags.STATES, None),
    "System.Contract.NativePostPersist": (0, CallFlags.STATES, None),
    "System.Crypto.CheckMultisig": (0, CallFlags.NONE, None),
    "System.Crypto.CheckSig": (1 << 15, CallFlags.NONE, None),
    "System.Iterator.Next": (1 << 15, CallFlags.NONE, None),
    "System.Iterator.Value": (1 << 4, CallFlags.NONE, None),
    "System.Runtime.BurnGas": (1 << 4, CallFlags.NONE, None),
    "System.Runtime.CheckWitness": (1 << 10, CallFlags.NONE, None),
    "System.Runtime.CurrentSigners": (1 << 4, CallFlags.NONE, None),
    "System.Runtime.GasLeft": (1 << 4, CallFlags.NONE, None),
    "System.Runtime.GetAddressVersion": (1 << 3, CallFlags.NONE, None),
    "System.Runtime.GetCallingScriptHash": (1 << 4, CallFlags.NONE, None),
    "System.Runtime.GetEntryScriptHash": (1 << 4, CallFlags.NONE, None),
    "System.Runtime.GetExecutingScriptHash": (1 << 4, CallFlags.NONE, None),
    "System.Runtime.GetInvocationCounter": (1 << 4, CallFlags.NONE, None),
    "System.Runtime.GetNetwork": (1 << 3, CallFlags.NONE, None),
    "System.Runtime.GetNotifications": (1 << 12, CallFlags.NONE, None),
    "System.Runtime.GetRandom": (0, CallFlags.NONE, None),
    "System.Runtime.GetScriptContainer": (1 << 3, CallFlags.NONE, None),
    "System.Runtime.GetTime": (1 << 3, CallFlags.NONE, None),
    "System.Runtime.GetTrigger": (1 << 3, CallFlags.NONE, None),
    "System.Runtime.LoadScript": (1 << 15, CallFlags.ALLOW_CALL, None),
    "System.Runtime.Log": (1 << 15, CallFlags.ALLOW_NOTIFY, None),
    "System.Runtime.Notify": (1 << 15, CallFlags.ALLOW_NOTIFY, None),
    "System.Runtime.Platform": (1 << 3, CallFlags.NONE, None),
    "System.Storage.AsReadOnly": (1 << 4, CallFlags.READ_STATES, None),
    "System.Storage.Delete": (1 << 15, CallFlags.WRITE_STATES, None),
    "System.Storage.Find": (1 << 15, CallFlags.READ_STATES, None),
    "System.Storage.Get": (1 << 15, CallFlags.READ_STATES, None),
    "System.Storage.GetContext": (1 << 4, CallFlags.READ_STATES, None),
    "System.Storage.GetReadOnlyContext": (1 << 4, CallFlags.READ_STATES, None),
    "System.Storage.Local.Delete": (1 << 15, CallFlags.WRITE_STATES, Hardfork.HF_FAUN),
    "System.Storage.Local.Find": (1 << 15, CallFlags.READ_STATES, Hardfork.HF_FAUN),
    "System.Storage.Local.Get": (1 << 15, CallFlags.READ_STATES, Hardfork.HF_FAUN),
    "System.Storage.Local.Put": (1 << 15, CallFlags.WRITE_STATES, Hardfork.HF_FAUN),
    "System.Storage.Put": (1 << 15, CallFlags.WRITE_STATES, None),
}


def test_syscall_table_matches_neo_v391() -> None:
    """Syscall registration metadata matches official Neo v3.9.1."""
    ApplicationEngine(protocol_settings=ProtocolSettings.mainnet())

    for name, (price, flags, hardfork) in EXPECTED_SYSCALLS_V391.items():
        syscall_hash = get_interop_hash(name)
        descriptor = get_syscall(syscall_hash)

        assert descriptor is not None, f"Missing syscall descriptor: {name}"
        assert descriptor.name == name
        assert descriptor.price == price
        assert descriptor.required_flags == flags
        assert descriptor.hardfork == hardfork


def test_syscall_enforces_required_call_flags() -> None:
    """Interop invocation must enforce descriptor required call flags."""
    engine = ApplicationEngine(protocol_settings=ProtocolSettings.mainnet())
    engine.load_script(bytes([0x40]))
    engine._current_call_flags = CallFlags.READ_STATES

    # System.Runtime.Log requires ALLOW_NOTIFY; invoke must fail before handler executes.
    engine.push(ByteString(b"log"))
    with pytest.raises(PermissionError):
        invoke_syscall(engine, get_interop_hash("System.Runtime.Log"))


def test_storage_local_syscall_hardfork_gating() -> None:
    """Storage.Local syscalls must activate only when HF_FAUN is enabled."""
    settings = ProtocolSettings.mainnet()
    settings.hardforks[Hardfork.HF_FAUN] = 100

    snapshot_pre = SimpleNamespace(
        persisting_block=SimpleNamespace(index=99),
        get=lambda _key: None,
    )
    engine = ApplicationEngine(protocol_settings=settings, snapshot=snapshot_pre)
    engine.load_script(bytes([0x40]))

    engine.push(ByteString(b"key"))
    with pytest.raises(KeyError):
        invoke_syscall(engine, get_interop_hash("System.Storage.Local.Get"))

    snapshot_post = SimpleNamespace(
        persisting_block=SimpleNamespace(index=100),
        get=lambda _key: None,
    )
    engine.snapshot = snapshot_post

    engine.push(ByteString(b"key"))
    invoke_syscall(engine, get_interop_hash("System.Storage.Local.Get"))

    assert engine.peek() == NULL
