"""Tests for ApplicationEngine."""

from types import SimpleNamespace

import pytest
from neo.smartcontract.application_engine import (
    ApplicationEngine,
    GasCost,
    Notification,
    LogEntry,
)
from neo.smartcontract.trigger import TriggerType
from neo.vm.execution_engine import VMState
from neo.vm.opcode import OpCode
from neo.vm.script_builder import ScriptBuilder


_MURMUR128_C1 = 0x87C37B91114253D5
_MURMUR128_C2 = 0x4CF5AD432745937F
_MURMUR128_MASK64 = (1 << 64) - 1


def _rotl64(value: int, shift: int) -> int:
    return ((value << shift) & _MURMUR128_MASK64) | (value >> (64 - shift))


def _fmix64(value: int) -> int:
    value ^= value >> 33
    value = (value * 0xFF51AFD7ED558CCD) & _MURMUR128_MASK64
    value ^= value >> 33
    value = (value * 0xC4CEB9FE1A85EC53) & _MURMUR128_MASK64
    value ^= value >> 33
    return value & _MURMUR128_MASK64


def _murmur128_reference(data: bytes, seed: int) -> bytes:
    seed_u32 = seed & 0xFFFFFFFF
    h1 = seed_u32
    h2 = seed_u32

    block_count = len(data) // 16
    for block_index in range(block_count):
        start = block_index * 16
        block = data[start : start + 16]
        k1 = int.from_bytes(block[:8], "little")
        k2 = int.from_bytes(block[8:], "little")

        mix1 = (_rotl64((k1 * _MURMUR128_C1) & _MURMUR128_MASK64, 31) * _MURMUR128_C2) & _MURMUR128_MASK64
        h1 = (h1 ^ mix1) & _MURMUR128_MASK64
        h1 = (_rotl64(h1, 27) + h2) & _MURMUR128_MASK64
        h1 = (h1 * 5 + 0x52DCE729) & _MURMUR128_MASK64

        mix2 = (_rotl64((k2 * _MURMUR128_C2) & _MURMUR128_MASK64, 33) * _MURMUR128_C1) & _MURMUR128_MASK64
        h2 = (h2 ^ mix2) & _MURMUR128_MASK64
        h2 = (_rotl64(h2, 31) + h1) & _MURMUR128_MASK64
        h2 = (h2 * 5 + 0x38495AB5) & _MURMUR128_MASK64

    tail = data[block_count * 16 :].ljust(16, b"\x00")
    if len(data) % 16:
        k1 = int.from_bytes(tail[:8], "little")
        k2 = int.from_bytes(tail[8:], "little")
        h2 ^= (_rotl64((k2 * _MURMUR128_C2) & _MURMUR128_MASK64, 33) * _MURMUR128_C1) & _MURMUR128_MASK64
        h2 &= _MURMUR128_MASK64
        h1 ^= (_rotl64((k1 * _MURMUR128_C1) & _MURMUR128_MASK64, 31) * _MURMUR128_C2) & _MURMUR128_MASK64
        h1 &= _MURMUR128_MASK64

    length = len(data)
    h1 ^= length
    h2 ^= length

    h1 = (h1 + h2) & _MURMUR128_MASK64
    h2 = (h2 + h1) & _MURMUR128_MASK64

    h1 = _fmix64(h1)
    h2 = _fmix64(h2)

    h1 = (h1 + h2) & _MURMUR128_MASK64
    h2 = (h2 + h1) & _MURMUR128_MASK64

    return h1.to_bytes(8, "little") + h2.to_bytes(8, "little")


def _reference_get_random_values(
    tx_hash: bytes,
    network: int,
    block_nonce: int,
    aspidochelone_enabled: bool,
    count: int,
) -> list[int]:
    nonce_data = bytearray(tx_hash[:16])
    nonce = int.from_bytes(nonce_data[:8], "little") ^ (block_nonce & 0xFFFFFFFFFFFFFFFF)
    nonce_data[:8] = nonce.to_bytes(8, "little")

    values: list[int] = []
    random_times = 0
    for _ in range(count):
        if aspidochelone_enabled:
            seed = (network + random_times) & 0xFFFFFFFF
            buffer = _murmur128_reference(bytes(nonce_data), seed)
            random_times += 1
        else:
            buffer = _murmur128_reference(bytes(nonce_data), network)
            nonce_data = bytearray(buffer)
        values.append(int.from_bytes(buffer, "little"))
    return values


class TestApplicationEngineBasics:
    """Test basic ApplicationEngine functionality."""
    
    def test_create_engine(self):
        """Test creating an application engine."""
        engine = ApplicationEngine()
        assert engine.trigger == TriggerType.APPLICATION
        assert engine.gas_consumed == 0
        assert engine.state == VMState.NONE
    
    def test_gas_consumption(self):
        """Test gas consumption tracking."""
        engine = ApplicationEngine(gas_limit=1000)
        engine.add_gas(100)
        assert engine.gas_consumed == 100
        engine.add_gas(200)
        assert engine.gas_consumed == 300
    
    def test_gas_limit_exceeded(self):
        """Test gas limit enforcement."""
        engine = ApplicationEngine(gas_limit=100)
        with pytest.raises(Exception, match="Out of gas"):
            engine.add_gas(200)
    
    def test_trigger_types(self):
        """Test different trigger types."""
        engine = ApplicationEngine(trigger=TriggerType.VERIFICATION)
        assert engine.trigger == TriggerType.VERIFICATION
        
        engine = ApplicationEngine(trigger=TriggerType.SYSTEM)
        assert engine.trigger == TriggerType.SYSTEM
    
    def test_network_magic(self):
        """Test network magic number."""
        engine = ApplicationEngine(network=12345)
        assert engine.network == 12345


class TestApplicationEngineExecution:
    """Test script execution in ApplicationEngine."""
    
    def test_simple_script(self):
        """Test executing a simple script."""
        sb = ScriptBuilder()
        sb.emit_push(42)
        script = sb.to_bytes()
        
        engine = ApplicationEngine.run(script)
        assert engine.state == VMState.HALT
        assert len(engine.result_stack) == 1
        assert engine.result_stack.peek().get_integer() == 42
    
    def test_arithmetic_script(self):
        """Test arithmetic operations."""
        sb = ScriptBuilder()
        sb.emit_push(10)
        sb.emit_push(20)
        sb.emit(OpCode.ADD)
        script = sb.to_bytes()
        
        engine = ApplicationEngine.run(script)
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 30
    
    def test_multiple_operations(self):
        """Test multiple operations."""
        sb = ScriptBuilder()
        sb.emit_push(5)
        sb.emit_push(3)
        sb.emit(OpCode.MUL)
        sb.emit_push(2)
        sb.emit(OpCode.ADD)
        script = sb.to_bytes()
        
        engine = ApplicationEngine.run(script)
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 17


class TestApplicationEngineNotifications:
    """Test notification system."""
    
    def test_notifications_list(self):
        """Test notifications list initialization."""
        engine = ApplicationEngine()
        assert engine.notifications == []
    
    def test_logs_list(self):
        """Test logs list initialization."""
        engine = ApplicationEngine()
        assert engine.logs == []


class TestApplicationEngineRuntimeNotifications:
    """Runtime.GetNotifications behavior checks."""

    @staticmethod
    def _get_notifications_result(engine: ApplicationEngine, filter_item):
        pushed_items = []
        engine.pop = lambda: filter_item
        engine.push = lambda item: pushed_items.append(item)
        engine._runtime_get_notifications(engine)
        assert len(pushed_items) == 1
        return pushed_items[0]

    def test_runtime_get_notifications_null_returns_all(self):
        from neo.types import UInt160
        from neo.vm.types import Integer, NULL, Array

        engine = ApplicationEngine()
        engine._notifications = [
            Notification(script_hash=UInt160(b"\x01" * 20), event_name="A", state=Integer(1)),
            Notification(script_hash=UInt160(b"\x00" * 20), event_name="B", state=Integer(2)),
        ]

        result = self._get_notifications_result(engine, NULL)
        assert isinstance(result, Array)
        assert len(result) == 2

    def test_runtime_get_notifications_zero_hash_is_exact_filter(self):
        from neo.types import UInt160
        from neo.vm.types import ByteString, Integer, Array

        engine = ApplicationEngine()
        engine._notifications = [
            Notification(script_hash=UInt160(b"\x01" * 20), event_name="A", state=Integer(1)),
            Notification(script_hash=UInt160(b"\x00" * 20), event_name="Zero", state=Integer(2)),
        ]

        result = self._get_notifications_result(engine, ByteString(b"\x00" * 20))
        assert isinstance(result, Array)
        assert len(result) == 1
        assert result[0][1].get_string() == "Zero"

    def test_runtime_get_notifications_invalid_hash_length_faults(self):
        from neo.exceptions import InvalidOperationException
        from neo.vm.types import ByteString

        engine = ApplicationEngine()
        engine._notifications = []

        with pytest.raises(InvalidOperationException, match="Invalid script hash length"):
            self._get_notifications_result(engine, ByteString(b"\x01"))

    def test_runtime_get_notifications_exceeding_stack_limit_faults(self):
        from neo.exceptions import InvalidOperationException
        from neo.types import UInt160
        from neo.vm.types import Integer, NULL

        engine = ApplicationEngine()
        engine._notifications = [
            Notification(script_hash=UInt160(b"\x01" * 20), event_name="A", state=Integer(1))
            for _ in range(engine.limits.max_stack_size + 1)
        ]

        with pytest.raises(InvalidOperationException, match="maximum stack size"):
            self._get_notifications_result(engine, NULL)


class TestApplicationEngineRuntimeCheckWitness:
    """Runtime.CheckWitness behavior checks."""

    def test_runtime_check_witness_matches_uint160_signer(self):
        from neo.network.payloads.signer import Signer
        from neo.network.payloads.witness_scope import WitnessScope
        from neo.types import UInt160
        from neo.vm.types import ByteString, Integer

        account = UInt160(b"\x11" * 20)
        engine = ApplicationEngine(script_container=SimpleNamespace(
            signers=[Signer(account=account, scopes=WitnessScope.GLOBAL)]
        ))
        engine.pop = lambda: ByteString(b"\x11" * 20)

        pushed_items: list = []
        engine.push = lambda item: pushed_items.append(item)

        engine._runtime_check_witness(engine)

        assert len(pushed_items) == 1
        assert isinstance(pushed_items[0], Integer)
        assert pushed_items[0].get_integer() == 1

    def test_runtime_check_witness_rejects_65byte_uncompressed_key(self):
        from neo.exceptions import InvalidOperationException
        from neo.vm.types import ByteString

        engine = ApplicationEngine()
        engine.pop = lambda: ByteString(b"\x04" + (b"\x01" * 64))

        with pytest.raises(InvalidOperationException, match="Invalid hashOrPubkey length"):
            engine._runtime_check_witness(engine)

    def test_check_witness_internal_allows_calling_script_hash(self, monkeypatch):
        from neo.types import UInt160

        account = UInt160(b"\x22" * 20)
        monkeypatch.setattr(
            ApplicationEngine,
            "calling_script_hash",
            property(lambda _self: account),
        )

        engine = ApplicationEngine(script_container=None)
        assert engine._check_witness_internal(account) is True

    def test_check_witness_internal_non_transaction_uses_script_hashes_for_verifying(self):
        from neo.types import UInt160

        account = UInt160(b"\x77" * 20)

        class _Container:
            def get_script_hashes_for_verifying(self, _snapshot):
                return [account]

        engine = ApplicationEngine(script_container=_Container(), snapshot=SimpleNamespace())
        assert engine._check_witness_internal(account) is True

    def test_check_witness_internal_non_transaction_requires_read_states(self):
        from neo.exceptions import InvalidOperationException
        from neo.smartcontract.call_flags import CallFlags
        from neo.types import UInt160

        account = UInt160(b"\x88" * 20)

        class _Container:
            def get_script_hashes_for_verifying(self, _snapshot):
                return [account]

        engine = ApplicationEngine(script_container=_Container(), snapshot=SimpleNamespace())
        engine._default_call_flags = CallFlags.NONE

        with pytest.raises(InvalidOperationException, match="call flags"):
            engine._check_witness_internal(account)

    def test_check_witness_scope_custom_contracts_accepts_uint160_entries(self, monkeypatch):
        from neo.network.payloads.witness_scope import WitnessScope
        from neo.types import UInt160

        target = UInt160(b"\x33" * 20)
        signer = SimpleNamespace(
            scopes=WitnessScope.CUSTOM_CONTRACTS,
            allowed_contracts=[target],
            allowed_groups=[],
            rules=[],
        )

        monkeypatch.setattr(
            ApplicationEngine,
            "current_script_hash",
            property(lambda _self: target),
        )

        engine = ApplicationEngine()
        assert engine._check_witness_scope(signer) is True

    def test_check_witness_scope_custom_contracts_accepts_hex_strings(self, monkeypatch):
        from neo.network.payloads.witness_scope import WitnessScope
        from neo.types import UInt160

        target = UInt160(b"\x66" * 20)
        signer = SimpleNamespace(
            scopes=WitnessScope.CUSTOM_CONTRACTS,
            allowed_contracts=[target.to_array().hex()],
            allowed_groups=[],
            rules=[],
        )

        monkeypatch.setattr(
            ApplicationEngine,
            "current_script_hash",
            property(lambda _self: target),
        )

        engine = ApplicationEngine()
        assert engine._check_witness_scope(signer) is True

    def test_check_witness_groups_accepts_manifest_dict(self, monkeypatch):
        from neo.types import UInt160

        pubkey_hex = "02" + ("11" * 32)
        current_hash = UInt160(b"\x44" * 20)
        signer = SimpleNamespace(allowed_groups=[bytes.fromhex(pubkey_hex)])
        contract = SimpleNamespace(manifest={"groups": [{"pubkey": pubkey_hex}]})

        monkeypatch.setattr(
            ApplicationEngine,
            "current_script_hash",
            property(lambda _self: current_hash),
        )

        engine = ApplicationEngine()
        monkeypatch.setattr(engine, "_get_contract", lambda _hash: contract)

        assert engine._check_witness_groups(signer) is True

    def test_check_witness_groups_accepts_encoded_group_objects(self, monkeypatch):
        from neo.types import UInt160

        class _GroupPoint:
            def __init__(self, data: bytes) -> None:
                self._data = data

            def encode(self) -> bytes:
                return self._data

        pubkey = bytes.fromhex("03" + ("22" * 32))
        current_hash = UInt160(b"\x55" * 20)
        signer = SimpleNamespace(allowed_groups=[_GroupPoint(pubkey)])
        contract = SimpleNamespace(manifest={"groups": [{"pubkey": pubkey.hex()}]})

        monkeypatch.setattr(
            ApplicationEngine,
            "current_script_hash",
            property(lambda _self: current_hash),
        )

        engine = ApplicationEngine()
        monkeypatch.setattr(engine, "_get_contract", lambda _hash: contract)

        assert engine._check_witness_groups(signer) is True

    def test_check_witness_scope_witness_rules_accepts_string_action(self):
        from neo.network.payloads.witness_scope import WitnessScope

        signer = SimpleNamespace(
            scopes=WitnessScope.WITNESS_RULES,
            allowed_contracts=[],
            allowed_groups=[],
            rules=[SimpleNamespace(action="Allow", condition=SimpleNamespace(type=0x00, expression=True))],
        )

        engine = ApplicationEngine()
        assert engine._check_witness_scope(signer) is True

    def test_check_witness_scope_witness_rules_respects_string_deny(self):
        from neo.network.payloads.witness_scope import WitnessScope

        signer = SimpleNamespace(
            scopes=WitnessScope.WITNESS_RULES,
            allowed_contracts=[],
            allowed_groups=[],
            rules=[SimpleNamespace(action="Deny", condition=SimpleNamespace(type=0x00, expression=True))],
        )

        engine = ApplicationEngine()
        assert engine._check_witness_scope(signer) is False


class TestApplicationEngineRuntimeGetRandom:
    """Runtime.GetRandom behavior checks."""

    @staticmethod
    def _get_random_output(engine: ApplicationEngine) -> int:
        pushed_items: list = []
        engine.push = lambda item: pushed_items.append(item)
        engine._runtime_get_random(engine)
        assert len(pushed_items) == 1
        return pushed_items[0].get_integer()

    def test_runtime_get_random_pre_aspidochelone_matches_reference(self):
        from neo.hardfork import Hardfork
        from neo.protocol_settings import ProtocolSettings

        tx_hash = bytes(range(32))
        network = 860833102
        block_nonce = 0x1122334455667788
        settings = ProtocolSettings.mainnet()
        settings.hardforks[Hardfork.HF_ASPIDOCHELONE] = 1

        engine = ApplicationEngine(
            network=network,
            protocol_settings=settings,
            script_container=SimpleNamespace(hash=tx_hash),
            snapshot=SimpleNamespace(
                persisting_block=SimpleNamespace(index=0, nonce=block_nonce)
            ),
        )

        outputs = [
            self._get_random_output(engine),
            self._get_random_output(engine),
        ]

        expected = _reference_get_random_values(
            tx_hash=tx_hash,
            network=network,
            block_nonce=block_nonce,
            aspidochelone_enabled=False,
            count=2,
        )
        assert outputs == expected
        assert engine.gas_consumed == (1 << 4) * 2

    def test_runtime_get_random_aspidochelone_matches_reference(self):
        from neo.hardfork import Hardfork
        from neo.protocol_settings import ProtocolSettings

        tx_hash = bytes(reversed(range(32)))
        network = 894710606
        block_nonce = 0x8877665544332211
        settings = ProtocolSettings.testnet()
        settings.hardforks[Hardfork.HF_ASPIDOCHELONE] = 0

        engine = ApplicationEngine(
            network=network,
            protocol_settings=settings,
            script_container=SimpleNamespace(hash=tx_hash),
            snapshot=SimpleNamespace(
                persisting_block=SimpleNamespace(index=0, nonce=block_nonce)
            ),
        )

        outputs = [
            self._get_random_output(engine),
            self._get_random_output(engine),
        ]

        expected = _reference_get_random_values(
            tx_hash=tx_hash,
            network=network,
            block_nonce=block_nonce,
            aspidochelone_enabled=True,
            count=2,
        )
        assert outputs == expected
        assert engine.gas_consumed == (1 << 13) * 2


class TestApplicationEngineRuntimeNetworkMetadata:
    """Runtime network metadata syscall behavior checks."""

    @staticmethod
    def _single_pushed_integer(engine: ApplicationEngine, method_name: str) -> int:
        pushed_items: list = []
        engine.push = lambda item: pushed_items.append(item)
        getattr(engine, method_name)(engine)
        assert len(pushed_items) == 1
        return pushed_items[0].get_integer()

    def test_runtime_get_network_uses_protocol_settings_network(self):
        engine = ApplicationEngine(
            network=111,
            protocol_settings=SimpleNamespace(network=222, address_version=53),
        )
        value = self._single_pushed_integer(engine, "_runtime_get_network")
        assert value == 222

    def test_runtime_get_address_version_uses_protocol_settings_value(self):
        engine = ApplicationEngine(
            protocol_settings=SimpleNamespace(network=860833102, address_version=45),
        )
        value = self._single_pushed_integer(engine, "_runtime_get_address_version")
        assert value == 45


class TestApplicationEngineRuntimeGetTime:
    """Runtime.GetTime behavior checks."""

    def test_runtime_get_time_without_persisting_block_faults(self):
        from neo.exceptions import InvalidOperationException

        engine = ApplicationEngine()
        with pytest.raises(InvalidOperationException, match="GetTime can only be called with Application trigger"):
            engine._runtime_get_time(engine)

    def test_runtime_get_time_returns_persisting_block_timestamp(self):
        from neo.vm.types import Integer

        engine = ApplicationEngine(
            snapshot=SimpleNamespace(
                persisting_block=SimpleNamespace(timestamp=123456789)
            )
        )
        pushed_items: list = []
        engine.push = lambda item: pushed_items.append(item)

        engine._runtime_get_time(engine)

        assert len(pushed_items) == 1
        assert isinstance(pushed_items[0], Integer)
        assert pushed_items[0].get_integer() == 123456789


class TestApplicationEngineRuntimeGetScriptContainer:
    """Runtime.GetScriptContainer behavior checks."""

    def test_runtime_get_script_container_without_container_faults(self):
        from neo.exceptions import InvalidOperationException

        engine = ApplicationEngine(script_container=None)
        engine.push = lambda _item: None
        with pytest.raises(InvalidOperationException):
            engine._runtime_get_script_container(engine)


class TestApplicationEngineRuntimeLog:
    """Runtime.Log behavior checks."""

    def test_runtime_log_invalid_utf8_faults(self):
        from neo.exceptions import InvalidOperationException
        from neo.vm.types import ByteString

        engine = ApplicationEngine()
        engine.pop = lambda: ByteString(b"\xFF")

        with pytest.raises(InvalidOperationException, match="Invalid UTF-8 sequence"):
            engine._runtime_log(engine)


class TestApplicationEngineRuntimeNotify:
    """Runtime.Notify behavior checks."""

    def test_runtime_notify_rejects_event_name_over_32_bytes(self):
        from neo.exceptions import InvalidOperationException
        from neo.vm.types import Array, ByteString

        values = iter([Array(), ByteString(b"A" * 33)])
        engine = ApplicationEngine()
        engine.pop = lambda: next(values)

        with pytest.raises(InvalidOperationException, match="Event name size"):
            engine._runtime_notify(engine)

    def test_runtime_notify_rejects_non_array_state(self):
        from neo.exceptions import InvalidOperationException
        from neo.types import UInt160
        from neo.vm.types import ByteString, Integer

        values = iter([Integer(1), ByteString(b"Evt")])
        engine = ApplicationEngine()
        engine.pop = lambda: next(values)
        engine._require_current_script_hash = lambda: UInt160(b"\x01" * 20)
        engine.send_notification = lambda _hash, _name, _state: None

        with pytest.raises(InvalidOperationException, match="Array"):
            engine._runtime_notify(engine)


class TestApplicationEngineRuntimeCurrentSigners:
    """Runtime.CurrentSigners behavior checks."""

    def test_runtime_current_signers_requires_transaction_container(self):
        from neo.vm.types import NULL

        signer = SimpleNamespace(
            account=b"\x11" * 20,
            scopes=0,
            allowed_contracts=[],
            allowed_groups=[],
            rules=[],
        )
        engine = ApplicationEngine(script_container=SimpleNamespace(signers=[signer]))
        pushed_items: list = []
        engine.push = lambda item: pushed_items.append(item)

        engine._runtime_current_signers(engine)

        assert len(pushed_items) == 1
        assert pushed_items[0] is NULL

    def test_runtime_current_signers_includes_rules_stack_projection(self):
        from neo.network.payloads.signer import Signer
        from neo.network.payloads.transaction import Transaction
        from neo.network.payloads.witness_condition import BooleanCondition
        from neo.network.payloads.witness_rule import WitnessRule, WitnessRuleAction
        from neo.network.payloads.witness_scope import WitnessScope
        from neo.types import UInt160
        from neo.vm.types import Array

        signer = Signer(
            account=UInt160(b"\x11" * 20),
            scopes=WitnessScope.WITNESS_RULES,
            allowed_contracts=[],
            allowed_groups=[],
            rules=[
                WitnessRule(
                    action=WitnessRuleAction.ALLOW,
                    condition=BooleanCondition(expression=True),
                )
            ],
        )
        engine = ApplicationEngine(script_container=Transaction(signers=[signer]))
        pushed_items: list = []
        engine.push = lambda item: pushed_items.append(item)

        engine._runtime_current_signers(engine)

        assert len(pushed_items) == 1
        assert isinstance(pushed_items[0], Array)
        assert len(pushed_items[0]) == 1

        signer_item = pushed_items[0][0]
        assert len(signer_item) == 5
        rules_item = signer_item[4]
        assert isinstance(rules_item, Array)
        assert len(rules_item) == 1
        assert rules_item[0][0].get_integer() == 1
        assert rules_item[0][1][0].get_integer() == 0
        assert rules_item[0][1][1].get_boolean() is True

    def test_runtime_current_signers_applies_scope_filters_to_lists(self):
        from neo.network.payloads.signer import Signer
        from neo.network.payloads.transaction import Transaction
        from neo.network.payloads.witness_condition import CalledByEntryCondition
        from neo.network.payloads.witness_rule import WitnessRule, WitnessRuleAction
        from neo.network.payloads.witness_scope import WitnessScope
        from neo.types import UInt160
        from neo.vm.types import Array

        signer = Signer(
            account=UInt160(b"\x22" * 20),
            scopes=WitnessScope.NONE,
            allowed_contracts=[b"\x01" * 20],
            allowed_groups=[bytes.fromhex("02" + ("aa" * 32))],
            rules=[
                WitnessRule(
                    action=WitnessRuleAction.DENY,
                    condition=CalledByEntryCondition(),
                )
            ],
        )
        engine = ApplicationEngine(script_container=Transaction(signers=[signer]))
        pushed_items: list = []
        engine.push = lambda item: pushed_items.append(item)

        engine._runtime_current_signers(engine)

        assert len(pushed_items) == 1
        assert isinstance(pushed_items[0], Array)
        assert len(pushed_items[0]) == 1

        signer_item = pushed_items[0][0]
        assert len(signer_item) == 5
        assert len(signer_item[2]) == 0
        assert len(signer_item[3]) == 0
        assert len(signer_item[4]) == 0


class TestApplicationEngineRuntimeLoadScript:
    """Runtime.LoadScript behavior checks."""

    def test_runtime_load_script_masks_call_flags_with_caller_and_read_only(self):
        from neo.smartcontract.call_flags import CallFlags
        from neo.vm.types import Array, ByteString, Integer

        engine = ApplicationEngine()
        engine.load_script(bytes([OpCode.RET]))
        engine._current_call_flags = CallFlags.STATES

        engine.push(ByteString(bytes([OpCode.RET])))
        engine.push(Integer(int(CallFlags.ALL)))
        engine.push(Array())

        engine._runtime_load_script(engine)

        assert engine._current_call_flags == CallFlags.READ_STATES

    def test_runtime_load_script_cannot_escalate_from_none(self):
        from neo.smartcontract.call_flags import CallFlags
        from neo.vm.types import Array, ByteString, Integer

        engine = ApplicationEngine()
        engine.load_script(bytes([OpCode.RET]))
        engine._current_call_flags = CallFlags.NONE

        engine.push(ByteString(bytes([OpCode.RET])))
        engine.push(Integer(int(CallFlags.ALLOW_CALL)))
        engine.push(Array())

        engine._runtime_load_script(engine)

        assert engine._current_call_flags == CallFlags.NONE

    def test_runtime_load_script_moves_args_into_new_context_in_order(self):
        from neo.smartcontract.call_flags import CallFlags
        from neo.vm.types import Array, ByteString, Integer

        engine = ApplicationEngine()
        engine.load_script(bytes([OpCode.RET]))
        engine._current_call_flags = CallFlags.READ_ONLY

        args = Array(items=[Integer(11), Integer(22)])
        engine.push(ByteString(bytes([OpCode.RET])))
        engine.push(Integer(int(CallFlags.READ_ONLY)))
        engine.push(args)

        engine._runtime_load_script(engine)

        child_stack = engine.current_context.evaluation_stack
        assert child_stack.peek(0).get_integer() == 11
        assert child_stack.peek(1).get_integer() == 22

    def test_runtime_load_script_requires_array_args(self):
        from neo.exceptions import InvalidOperationException
        from neo.smartcontract.call_flags import CallFlags
        from neo.vm.types import ByteString, Integer

        engine = ApplicationEngine()
        engine.load_script(bytes([OpCode.RET]))
        engine._current_call_flags = CallFlags.READ_ONLY

        engine.push(ByteString(bytes([OpCode.RET])))
        engine.push(Integer(int(CallFlags.READ_ONLY)))
        engine.push(Integer(1))  # not an Array

        with pytest.raises(InvalidOperationException, match="Array"):
            engine._runtime_load_script(engine)


class TestApplicationEngineRuntimeBurnGas:
    """Runtime.BurnGas behavior checks."""

    def test_runtime_burn_gas_rejects_zero(self):
        from neo.exceptions import InvalidOperationException
        from neo.vm.types import Integer

        engine = ApplicationEngine()
        engine.pop = lambda: Integer(0)

        with pytest.raises(InvalidOperationException, match="positive"):
            engine._runtime_burn_gas(engine)


class TestGasCost:
    """Test gas cost constants."""
    
    def test_base_cost(self):
        """Test base gas cost."""
        assert GasCost.BASE == 1
    
    def test_opcode_cost(self):
        """Test opcode gas cost."""
        assert GasCost.OPCODE == 8
    
    def test_storage_costs(self):
        """Test storage gas costs."""
        assert GasCost.STORAGE_READ == 1024
        assert GasCost.STORAGE_WRITE == 4096
    
    def test_contract_call_cost(self):
        """Test contract call gas cost."""
        assert GasCost.CONTRACT_CALL == 32768
    
    def test_crypto_costs(self):
        """Test crypto operation gas costs."""
        assert GasCost.CRYPTO_VERIFY == 32768
        assert GasCost.CRYPTO_HASH == 1024


class TestNotification:
    """Test Notification dataclass."""
    
    def test_create_notification(self):
        """Test creating a notification."""
        from neo.types import UInt160
        from neo.vm.types import Integer
        
        script_hash = UInt160(bytes(20))
        notification = Notification(
            script_hash=script_hash,
            event_name="Transfer",
            state=Integer(100)
        )
        assert notification.event_name == "Transfer"
        assert notification.state.get_integer() == 100


class TestLogEntry:
    """Test LogEntry dataclass."""
    
    def test_create_log_entry(self):
        """Test creating a log entry."""
        from neo.types import UInt160
        
        script_hash = UInt160(bytes(20))
        log = LogEntry(script_hash=script_hash, message="Hello")
        assert log.message == "Hello"
