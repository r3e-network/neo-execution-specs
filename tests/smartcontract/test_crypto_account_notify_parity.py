"""v3.10.0 parity regression tests for crypto syscalls, account-creation fees,
notification limits and the dynamic-script notify rule.

References:
- ApplicationEngine.Crypto.cs (CheckSig / CheckMultisig fault semantics)
- ApplicationEngine.Contract.cs (CreateStandardAccount / CreateMultisigAccount fee)
- ApplicationEngine.Runtime.cs (SendNotification MaxNotificationCount, RuntimeNotify)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from neo.exceptions import InvalidOperationException, VMAbortException
from neo.hardfork import Hardfork
from neo.smartcontract.application_engine import ApplicationEngine
from neo.smartcontract.trigger import TriggerType
from neo.vm.types import Array, Integer, ByteString


@dataclass
class _Settings:
    """Minimal protocol-settings stub gating hardforks by membership.

    Mirrors the no-persisting-block branch of interop_service._is_hardfork_enabled:
    a hardfork is enabled iff it is present in the ``hardforks`` mapping.
    """

    hardforks: dict = field(default_factory=dict)


@dataclass
class _Container:
    hash: bytes = b"\x00" * 32


def _engine(*, gorgon=False, echidna=False, aspidochelone=False,
            trigger=TriggerType.APPLICATION) -> ApplicationEngine:
    hf: dict = {}
    if gorgon:
        hf[Hardfork.HF_GORGON] = 0
    if echidna:
        hf[Hardfork.HF_ECHIDNA] = 0
    if aspidochelone:
        hf[Hardfork.HF_ASPIDOCHELONE] = 0
    engine = ApplicationEngine(
        trigger=trigger,
        protocol_settings=_Settings(hardforks=hf),
        script_container=_Container(),
    )
    return engine


def _stack_handler(engine: ApplicationEngine, items: list):
    """Drive a handler with an explicit pop sequence and capture pushes."""
    pushed: list = []
    seq = list(items)
    engine.pop = lambda: seq.pop(0)  # type: ignore
    engine.push = lambda item: pushed.append(item)  # type: ignore
    return pushed


class TestCheckMultisigCountFaults:
    def test_empty_pubkeys_faults(self):
        engine = _engine()
        _stack_handler(engine, [Array(items=[]), Array(items=[ByteString(b"\x00" * 64)])])
        with pytest.raises(VMAbortException):
            engine._crypto_check_multisig(engine)

    def test_empty_signatures_faults(self):
        engine = _engine()
        _stack_handler(engine, [Array(items=[ByteString(b"\x02" + b"\x00" * 32)]), Array(items=[])])
        with pytest.raises(VMAbortException):
            engine._crypto_check_multisig(engine)

    def test_more_sigs_than_keys_faults(self):
        engine = _engine()
        pubkeys = Array(items=[ByteString(b"\x02" + b"\x00" * 32)])
        signatures = Array(items=[ByteString(b"\x00" * 64), ByteString(b"\x00" * 64)])
        _stack_handler(engine, [pubkeys, signatures])
        with pytest.raises(VMAbortException):
            engine._crypto_check_multisig(engine)


class TestCheckSigLengthFaults:
    def test_bad_pubkey_length_faults_unconditionally(self):
        # ECPoint.DecodePoint throws regardless of Gorgon.
        engine = _engine(gorgon=False)
        _stack_handler(engine, [ByteString(b"\x00" * 64), ByteString(b"\x00" * 10)])
        with pytest.raises(VMAbortException):
            engine._crypto_check_sig(engine)

    def test_bad_sig_length_pre_gorgon_returns_false(self):
        engine = _engine(gorgon=False)
        pushed = _stack_handler(engine, [ByteString(b"\x00" * 10), ByteString(b"\x02" + b"\x00" * 32)])
        engine._crypto_check_sig(engine)
        assert len(pushed) == 1
        assert int(pushed[0].get_integer()) == 0

    def test_bad_sig_length_post_gorgon_faults(self):
        engine = _engine(gorgon=True)
        _stack_handler(engine, [ByteString(b"\x00" * 10), ByteString(b"\x02" + b"\x00" * 32)])
        with pytest.raises(VMAbortException):
            engine._crypto_check_sig(engine)


class TestAccountCreationFee:
    def test_standard_account_fee_pre_aspidochelone(self):
        engine = _engine(aspidochelone=False)
        _stack_handler(engine, [ByteString(b"\x02" + b"\x00" * 32)])
        engine._contract_create_standard_account(engine)
        assert engine.gas_consumed == (1 << 8)

    def test_standard_account_fee_post_aspidochelone(self):
        engine = _engine(aspidochelone=True)
        _stack_handler(engine, [ByteString(b"\x02" + b"\x00" * 32)])
        engine._contract_create_standard_account(engine)
        assert engine.gas_consumed == (1 << 15)

    def test_multisig_account_fee_pre_aspidochelone_is_flat(self):
        engine = _engine(aspidochelone=False)
        keys = Array(items=[ByteString(b"\x02" + b"\x00" * 32), ByteString(b"\x02" + b"\x01" * 32)])
        # pop order: m (top), then pubkeys
        _stack_handler(engine, [Integer(1), keys])
        engine._contract_create_multisig_account(engine)
        assert engine.gas_consumed == (1 << 8)  # flat, NOT *n

    def test_multisig_account_fee_post_aspidochelone_scales(self):
        engine = _engine(aspidochelone=True)
        keys = Array(items=[ByteString(b"\x02" + b"\x00" * 32), ByteString(b"\x02" + b"\x01" * 32)])
        _stack_handler(engine, [Integer(1), keys])
        engine._contract_create_multisig_account(engine)
        assert engine.gas_consumed == (1 << 15) * 2


class TestNotificationLimit:
    def test_echidna_application_limit(self):
        from neo.types import UInt160

        engine = _engine(echidna=True, trigger=TriggerType.APPLICATION)
        sh = UInt160(b"\x01" * 20)
        for _ in range(ApplicationEngine.MAX_NOTIFICATION_COUNT):
            engine.send_notification(sh, "e", Integer(1))
        with pytest.raises(InvalidOperationException):
            engine.send_notification(sh, "e", Integer(1))

    def test_no_limit_without_echidna(self):
        from neo.types import UInt160

        engine = _engine(echidna=False, trigger=TriggerType.APPLICATION)
        sh = UInt160(b"\x01" * 20)
        for _ in range(ApplicationEngine.MAX_NOTIFICATION_COUNT + 5):
            engine.send_notification(sh, "e", Integer(1))
        assert len(engine.notifications) == ApplicationEngine.MAX_NOTIFICATION_COUNT + 5

    def test_no_limit_for_verification_trigger(self):
        from neo.types import UInt160

        engine = _engine(echidna=True, trigger=TriggerType.VERIFICATION)
        sh = UInt160(b"\x01" * 20)
        for _ in range(ApplicationEngine.MAX_NOTIFICATION_COUNT + 5):
            engine.send_notification(sh, "e", Integer(1))
        assert len(engine.notifications) == ApplicationEngine.MAX_NOTIFICATION_COUNT + 5


class TestRuntimeNotifyDynamicScript:
    def test_notify_from_dynamic_script_faults(self):
        engine = _engine()
        # No current script hash / no deployed contract -> dynamic script.
        _stack_handler(engine, [Array(items=[Integer(1)]), ByteString(b"Transfer")])
        with pytest.raises(InvalidOperationException):
            engine._runtime_notify(engine)


class TestCheckItemType:
    def test_byte_array_accepts_bytestring(self):
        from neo.smartcontract.contract_parameter_type import ContractParameterType as CPT

        assert ApplicationEngine._check_item_type(ByteString(b"\x01\x02"), CPT.BYTE_ARRAY)

    def test_hash160_requires_20_bytes(self):
        from neo.smartcontract.contract_parameter_type import ContractParameterType as CPT

        assert ApplicationEngine._check_item_type(ByteString(b"\x00" * 20), CPT.HASH160)
        assert not ApplicationEngine._check_item_type(ByteString(b"\x00" * 19), CPT.HASH160)

    def test_integer_param_rejects_bytestring(self):
        from neo.smartcontract.contract_parameter_type import ContractParameterType as CPT

        assert not ApplicationEngine._check_item_type(ByteString(b"\x01"), CPT.INTEGER)
        assert ApplicationEngine._check_item_type(Integer(1), CPT.INTEGER)
