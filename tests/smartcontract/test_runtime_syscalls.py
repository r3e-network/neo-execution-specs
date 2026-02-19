"""Tests for runtime syscalls."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from neo.smartcontract.syscalls import runtime


def _engine_with_stack():
    engine = MagicMock()
    ctx = MagicMock()
    stack = MagicMock()
    pushed_items = []

    ctx.evaluation_stack = stack
    engine.current_context = ctx
    stack.push = lambda value: pushed_items.append(value)

    return engine, stack, pushed_items


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


class TestRuntimeSyscalls:
    """Runtime syscall tests."""

    def test_platform_returns_neo(self):
        """Platform should return NEO."""
        from neo.vm.types import ByteString

        engine, _, pushed_items = _engine_with_stack()
        runtime.runtime_platform(engine)

        assert len(pushed_items) == 1
        pushed_value = pushed_items[0]
        assert isinstance(pushed_value, ByteString)
        assert pushed_value.value == b"NEO"

    def test_get_trigger(self):
        """Get trigger should return trigger type."""
        from neo.vm.types import Integer
        from neo.smartcontract.trigger import TriggerType

        engine, _, pushed_items = _engine_with_stack()
        engine.trigger = TriggerType.APPLICATION

        runtime.runtime_get_trigger(engine)

        assert len(pushed_items) == 1
        pushed_value = pushed_items[0]
        assert isinstance(pushed_value, Integer)
        assert pushed_value.get_integer() == int(TriggerType.APPLICATION)

    def test_get_network_uses_protocol_settings_network(self):
        """Network should prefer protocol settings value."""
        from neo.vm.types import Integer

        engine, _, pushed_items = _engine_with_stack()
        engine.network = 111
        engine.protocol_settings = SimpleNamespace(network=222, address_version=53)

        runtime.runtime_get_network(engine)

        assert len(pushed_items) == 1
        pushed_value = pushed_items[0]
        assert isinstance(pushed_value, Integer)
        assert pushed_value.get_integer() == 222

    def test_get_address_version_uses_protocol_settings_value(self):
        """Address version should prefer protocol settings value."""
        from neo.vm.types import Integer

        engine, _, pushed_items = _engine_with_stack()
        engine.address_version = 53
        engine.protocol_settings = SimpleNamespace(network=860833102, address_version=45)

        runtime.runtime_get_address_version(engine)

        assert len(pushed_items) == 1
        pushed_value = pushed_items[0]
        assert isinstance(pushed_value, Integer)
        assert pushed_value.get_integer() == 45

    def test_get_time_without_persisting_block_faults(self):
        """GetTime should fault without persisting block context."""
        from neo.exceptions import InvalidOperationException

        engine, _, _ = _engine_with_stack()
        engine.snapshot = None

        with pytest.raises(InvalidOperationException, match="GetTime can only be called with Application trigger"):
            runtime.runtime_get_time(engine)

    def test_get_time_returns_persisting_block_timestamp(self):
        """GetTime should return persisting block timestamp."""
        from neo.vm.types import Integer

        engine, _, pushed_items = _engine_with_stack()
        engine.snapshot = SimpleNamespace(persisting_block=SimpleNamespace(timestamp=987654321))

        runtime.runtime_get_time(engine)

        assert len(pushed_items) == 1
        pushed_value = pushed_items[0]
        assert isinstance(pushed_value, Integer)
        assert pushed_value.get_integer() == 987654321

    def test_get_script_container_without_container_faults(self):
        """GetScriptContainer should fault when no container exists."""
        from neo.exceptions import InvalidOperationException

        engine, _, _ = _engine_with_stack()
        engine.script_container = None

        with pytest.raises(InvalidOperationException):
            runtime.runtime_get_script_container(engine)

    def test_log_invalid_utf8_faults(self):
        """Runtime.Log must reject invalid UTF-8 payloads."""
        from neo.exceptions import InvalidOperationException
        from neo.vm.types import ByteString

        engine, stack, _ = _engine_with_stack()
        stack.pop = lambda: ByteString(b"\xFF")
        engine.current_script_hash = None

        with pytest.raises(InvalidOperationException, match="Invalid UTF-8 sequence"):
            runtime.runtime_log(engine)

    def test_notify_rejects_event_name_over_32_bytes(self):
        """Runtime.Notify must reject names longer than 32 bytes."""
        from neo.exceptions import InvalidOperationException
        from neo.vm.types import Array, ByteString

        engine, stack, _ = _engine_with_stack()
        values = iter([Array(), ByteString(b"A" * 33)])
        stack.pop = lambda: next(values)
        engine.current_script_hash = None

        with pytest.raises(InvalidOperationException, match="Event name size"):
            runtime.runtime_notify(engine)

    def test_notify_rejects_non_array_state(self):
        """Runtime.Notify should reject non-Array state payloads."""
        from neo.exceptions import InvalidOperationException
        from neo.vm.types import ByteString, Integer

        engine, stack, _ = _engine_with_stack()
        values = iter([Integer(1), ByteString(b"Evt")])
        stack.pop = lambda: next(values)
        engine.current_script_hash = b"\x01" * 20
        engine.send_notification = lambda _hash, _name, _state: None

        with pytest.raises(InvalidOperationException, match="Array"):
            runtime.runtime_notify(engine)

    def test_gas_left(self):
        """Gas left should return remaining gas."""
        from neo.vm.types import Integer

        engine, _, pushed_items = _engine_with_stack()
        engine.gas_limit = 1000000
        engine.gas_consumed = 100000

        runtime.runtime_gas_left(engine)

        assert len(pushed_items) == 1
        pushed_value = pushed_items[0]
        assert isinstance(pushed_value, Integer)
        assert pushed_value.get_integer() == 900000

    def test_get_random_pre_aspidochelone_matches_reference(self):
        """Pre-Aspidochelone should mutate nonceData and use legacy price."""
        from neo.hardfork import Hardfork
        from neo.protocol_settings import ProtocolSettings

        tx_hash = bytes(range(32))
        network = 860833102
        block_nonce = 0x1122334455667788
        settings = ProtocolSettings.mainnet()
        settings.hardforks[Hardfork.HF_ASPIDOCHELONE] = 1

        engine, _, pushed_items = _engine_with_stack()
        engine.network = network
        engine.protocol_settings = settings
        engine.script_container = SimpleNamespace(hash=tx_hash)
        engine.snapshot = SimpleNamespace(
            persisting_block=SimpleNamespace(index=0, nonce=block_nonce)
        )
        engine.gas_consumed = 0

        def _add_gas(amount):
            engine.gas_consumed += amount

        engine.add_gas = _add_gas

        runtime.runtime_get_random(engine)
        runtime.runtime_get_random(engine)

        assert [item.get_integer() for item in pushed_items] == _reference_get_random_values(
            tx_hash=tx_hash,
            network=network,
            block_nonce=block_nonce,
            aspidochelone_enabled=False,
            count=2,
        )
        assert engine.gas_consumed == (1 << 4) * 2

    def test_get_random_aspidochelone_matches_reference(self):
        """Aspidochelone+ should keep nonceData stable and raise syscall cost."""
        from neo.hardfork import Hardfork
        from neo.protocol_settings import ProtocolSettings

        tx_hash = bytes(reversed(range(32)))
        network = 894710606
        block_nonce = 0x8877665544332211
        settings = ProtocolSettings.testnet()
        settings.hardforks[Hardfork.HF_ASPIDOCHELONE] = 0

        engine, _, pushed_items = _engine_with_stack()
        engine.network = network
        engine.protocol_settings = settings
        engine.script_container = SimpleNamespace(hash=tx_hash)
        engine.snapshot = SimpleNamespace(
            persisting_block=SimpleNamespace(index=0, nonce=block_nonce)
        )
        engine.gas_consumed = 0

        def _add_gas(amount):
            engine.gas_consumed += amount

        engine.add_gas = _add_gas

        runtime.runtime_get_random(engine)
        runtime.runtime_get_random(engine)

        assert [item.get_integer() for item in pushed_items] == _reference_get_random_values(
            tx_hash=tx_hash,
            network=network,
            block_nonce=block_nonce,
            aspidochelone_enabled=True,
            count=2,
        )
        assert engine.gas_consumed == (1 << 13) * 2

    def test_burn_gas_rejects_zero(self):
        """BurnGas must reject non-positive amounts."""
        from neo.vm.types import Integer

        engine, stack, _ = _engine_with_stack()
        stack.pop = lambda: Integer(0)

        with pytest.raises(ValueError, match="positive"):
            runtime.runtime_burn_gas(engine)

    def test_get_notifications_null_filter_returns_all(self):
        """Null filter should return all notifications."""
        from neo.types import UInt160
        from neo.vm.types import Array, Integer, NULL

        engine, stack, pushed_items = _engine_with_stack()
        stack.pop = lambda: NULL
        engine.notifications = [
            SimpleNamespace(script_hash=UInt160(b"\x01" * 20), event_name="A", state=Integer(1)),
            SimpleNamespace(script_hash=UInt160(b"\x00" * 20), event_name="B", state=Integer(2)),
        ]

        runtime.runtime_get_notifications(engine)

        assert len(pushed_items) == 1
        result = pushed_items[0]
        assert isinstance(result, Array)
        assert len(result) == 2

    def test_get_notifications_zero_hash_is_exact_filter(self):
        """Zero hash should be treated as an exact filter, not wildcard."""
        from neo.types import UInt160
        from neo.vm.types import Array, ByteString, Integer

        engine, stack, pushed_items = _engine_with_stack()
        stack.pop = lambda: ByteString(b"\x00" * 20)
        engine.notifications = [
            SimpleNamespace(script_hash=UInt160(b"\x01" * 20), event_name="A", state=Integer(1)),
            SimpleNamespace(
                script_hash=UInt160(b"\x00" * 20),
                event_name="Zero",
                state=Integer(2),
            ),
        ]

        runtime.runtime_get_notifications(engine)

        assert len(pushed_items) == 1
        result = pushed_items[0]
        assert isinstance(result, Array)
        assert len(result) == 1
        assert result[0][1].get_string() == "Zero"

    def test_get_notifications_invalid_hash_length_faults(self):
        """Non-null filters must be exactly 20 bytes."""
        from neo.vm.types import ByteString

        engine, stack, _ = _engine_with_stack()
        stack.pop = lambda: ByteString(b"\x01")
        engine.notifications = []

        with pytest.raises(ValueError, match="Invalid script hash length"):
            runtime.runtime_get_notifications(engine)

    def test_get_notifications_exceeding_stack_limit_faults(self):
        """GetNotifications must fault when result exceeds max stack size."""
        from neo.exceptions import InvalidOperationException
        from neo.types import UInt160
        from neo.vm.types import Integer, NULL

        engine, stack, _ = _engine_with_stack()
        stack.pop = lambda: NULL
        engine.notifications = [
            SimpleNamespace(script_hash=UInt160(b"\x01" * 20), event_name="E", state=Integer(1))
            for _ in range(3)
        ]
        engine.limits = SimpleNamespace(max_stack_size=2)

        with pytest.raises(InvalidOperationException, match="maximum stack size"):
            runtime.runtime_get_notifications(engine)

    def test_check_witness_hash_path_accepts_uint160(self, monkeypatch):
        """20-byte input should route through witness checker."""
        from neo.types import UInt160
        from neo.vm.types import Boolean, ByteString

        captured: dict[str, object] = {}

        def fake_check(_engine, account_hash):
            captured["account_hash"] = account_hash
            return True

        monkeypatch.setattr(runtime, "_check_witness_internal", fake_check)

        engine, stack, pushed_items = _engine_with_stack()
        raw_hash = b"\x11" * 20
        stack.pop = lambda: ByteString(raw_hash)

        runtime.runtime_check_witness(engine)

        assert len(pushed_items) == 1
        assert isinstance(pushed_items[0], Boolean)
        assert pushed_items[0].get_boolean() is True
        assert captured["account_hash"] == UInt160(raw_hash)

    def test_check_witness_pubkey_path_accepts_compressed_33_bytes(self, monkeypatch):
        """33-byte pubkey path should hash redeem script to UInt160."""
        from neo.types import UInt160
        from neo.vm.types import Boolean, ByteString

        monkeypatch.setattr("neo.types.ec_point.ECPoint.decode", lambda _data: object())
        monkeypatch.setattr(
            "neo.smartcontract.syscalls.contract._create_signature_redeem_script",
            lambda pubkey: b"\xAA" + pubkey,
        )
        monkeypatch.setattr("neo.crypto.hash160", lambda script: b"\x22" * 20)

        captured: dict[str, object] = {}

        def fake_check(_engine, account_hash):
            captured["account_hash"] = account_hash
            return False

        monkeypatch.setattr(runtime, "_check_witness_internal", fake_check)

        engine, stack, pushed_items = _engine_with_stack()
        stack.pop = lambda: ByteString(b"\x02" + (b"\x33" * 32))

        runtime.runtime_check_witness(engine)

        assert len(pushed_items) == 1
        assert isinstance(pushed_items[0], Boolean)
        assert pushed_items[0].get_boolean() is False
        assert captured["account_hash"] == UInt160(b"\x22" * 20)

    def test_check_witness_rejects_invalid_compressed_pubkey_encoding(self):
        """33-byte inputs must be valid compressed ECPoints."""
        from neo.vm.types import ByteString

        engine, stack, _ = _engine_with_stack()
        stack.pop = lambda: ByteString(b"\x05" + (b"\x00" * 32))

        with pytest.raises(ValueError, match="Invalid EC point encoding"):
            runtime.runtime_check_witness(engine)

    def test_check_witness_rejects_invalid_lengths(self):
        """Only 20-byte hashes and 33-byte pubkeys are valid."""
        from neo.vm.types import ByteString

        engine, stack, _ = _engine_with_stack()

        stack.pop = lambda: ByteString(b"\x01")
        with pytest.raises(ValueError, match="Invalid hashOrPubkey length"):
            runtime.runtime_check_witness(engine)

        stack.pop = lambda: ByteString(b"\x04" + (b"\x01" * 64))  # 65-byte uncompressed key
        with pytest.raises(ValueError, match="Invalid hashOrPubkey length"):
            runtime.runtime_check_witness(engine)

    def test_check_witness_internal_accepts_byte_signer_accounts(self):
        """Internal witness checker should handle byte-form signer accounts."""
        from neo.network.payloads.signer import WitnessScope
        from neo.types import UInt160

        account_hash = UInt160(b"\x11" * 20)
        signer = SimpleNamespace(
            account=b"\x11" * 20,
            scopes=WitnessScope.GLOBAL,
            allowed_contracts=[],
            allowed_groups=[],
            rules=[],
        )
        engine = SimpleNamespace(
            calling_script_hash=None,
            script_container=SimpleNamespace(signers=[signer]),
            current_script_hash=UInt160(b"\xAA" * 20),
            entry_script_hash=UInt160(b"\xBB" * 20),
        )

        assert runtime._check_witness_internal(engine, account_hash) is True

    def test_check_witness_internal_non_transaction_uses_script_hashes_for_verifying(self):
        """Non-transaction containers should use script hashes for verifying."""
        from neo.smartcontract.call_flags import CallFlags
        from neo.types import UInt160

        account_hash = UInt160(b"\x77" * 20)

        class _Container:
            def get_script_hashes_for_verifying(self, _snapshot):
                return [account_hash]

        engine = SimpleNamespace(
            calling_script_hash=None,
            script_container=_Container(),
            snapshot=SimpleNamespace(),
            _current_call_flags=CallFlags.READ_STATES,
        )

        assert runtime._check_witness_internal(engine, account_hash) is True

    def test_check_witness_internal_non_transaction_requires_read_states(self):
        """Non-transaction verify path requires READ_STATES call flag."""
        from neo.exceptions import InvalidOperationException
        from neo.smartcontract.call_flags import CallFlags
        from neo.types import UInt160

        account_hash = UInt160(b"\x88" * 20)

        class _Container:
            def get_script_hashes_for_verifying(self, _snapshot):
                return [account_hash]

        engine = SimpleNamespace(
            calling_script_hash=None,
            script_container=_Container(),
            snapshot=SimpleNamespace(),
            _current_call_flags=CallFlags.NONE,
        )

        with pytest.raises(InvalidOperationException, match="call flags"):
            runtime._check_witness_internal(engine, account_hash)

    def test_check_witness_scope_custom_contracts_accepts_uint160_entries(self):
        """CustomContracts scope should support UInt160 allowlist entries."""
        from neo.network.payloads.signer import WitnessScope
        from neo.types import UInt160

        target = UInt160(b"\x33" * 20)
        signer = SimpleNamespace(
            scopes=WitnessScope.CUSTOM_CONTRACTS,
            allowed_contracts=[target],
            allowed_groups=[],
            rules=[],
        )
        engine = SimpleNamespace(
            current_script_hash=target,
            entry_script_hash=target,
            calling_script_hash=None,
        )

        assert runtime._check_witness_scope(engine, signer) is True

    def test_check_witness_scope_custom_contracts_accepts_hex_strings(self):
        """CustomContracts scope should support hex-string allowlist entries."""
        from neo.network.payloads.signer import WitnessScope
        from neo.types import UInt160

        target = UInt160(b"\x66" * 20)
        signer = SimpleNamespace(
            scopes=WitnessScope.CUSTOM_CONTRACTS,
            allowed_contracts=[target.to_array().hex()],
            allowed_groups=[],
            rules=[],
        )
        engine = SimpleNamespace(
            current_script_hash=target,
            entry_script_hash=target,
            calling_script_hash=None,
        )

        assert runtime._check_witness_scope(engine, signer) is True

    def test_check_witness_scope_witness_rules_accepts_string_action(self):
        """Witness rules should accept string action names."""
        from neo.network.payloads.signer import WitnessScope

        signer = SimpleNamespace(
            scopes=WitnessScope.WITNESS_RULES,
            allowed_contracts=[],
            allowed_groups=[],
            rules=[SimpleNamespace(action="Allow", condition=SimpleNamespace(type=0x00, expression=True))],
        )
        engine = SimpleNamespace(
            current_script_hash=None,
            entry_script_hash=None,
            calling_script_hash=None,
            _evaluate_witness_condition=lambda condition: bool(condition.expression),
        )

        assert runtime._check_witness_scope(engine, signer) is True

    def test_check_witness_scope_witness_rules_respects_string_deny(self):
        """String deny action should short-circuit to False."""
        from neo.network.payloads.signer import WitnessScope

        signer = SimpleNamespace(
            scopes=WitnessScope.WITNESS_RULES,
            allowed_contracts=[],
            allowed_groups=[],
            rules=[SimpleNamespace(action="Deny", condition=SimpleNamespace(type=0x00, expression=True))],
        )
        engine = SimpleNamespace(
            current_script_hash=None,
            entry_script_hash=None,
            calling_script_hash=None,
            _evaluate_witness_condition=lambda condition: bool(condition.expression),
        )

        assert runtime._check_witness_scope(engine, signer) is False
