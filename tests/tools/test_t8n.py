"""Tests for Neo t8n tool."""

from neo.crypto.hash import hash160
from neo.protocol_settings import ProtocolSettings
from neo.smartcontract.interop_service import get_interop_hash
from neo.tools.t8n import T8N
from neo.tools.t8n.types import AccountState, Environment
from neo.vm.opcode import OpCode
from neo.vm.script_builder import ScriptBuilder


def _build_script_hex(builder_fn) -> str:
    sb = ScriptBuilder()
    builder_fn(sb)
    return sb.to_bytes().hex()


class TestTypes:
    """Test type parsing."""

    def test_account_state_from_dict(self):
        data = {
            "gasBalance": 1000000,
            "neoBalance": 100,
            "storage": {"0a": "0b"},
        }
        state = AccountState.from_dict(data)
        assert state.gas_balance == 1000000
        assert state.neo_balance == 100
        assert state.storage == {"0a": "0b"}

    def test_account_state_to_dict(self):
        state = AccountState(gas_balance=500, neo_balance=10)
        d = state.to_dict()
        assert d["gasBalance"] == 500
        assert d["neoBalance"] == 10

    def test_environment_from_dict(self):
        data = {"currentBlockNumber": 100, "timestamp": 12345}
        env = Environment.from_dict(data)
        assert env.current_block_number == 100
        assert env.timestamp == 12345


class TestT8N:
    """Test t8n execution."""

    def test_empty_execution(self):
        alloc = {}
        env = {"currentBlockNumber": 1}
        txs = []

        t8n = T8N(alloc=alloc, env=env, txs=txs)
        output = t8n.run()

        assert output.result.gas_used == 0
        assert output.result.receipts == []
        assert output.alloc == {}

    def test_receipt_projects_halt_and_stack(self):
        script = _build_script_hex(lambda sb: sb.emit_push(7))
        t8n = T8N(alloc={}, env={"currentBlockNumber": 100}, txs=[{"script": script, "signers": []}])
        output = t8n.run()

        assert len(output.result.receipts) == 1
        receipt = output.result.receipts[0]
        assert receipt.vm_state == "HALT"
        assert receipt.exception is None
        assert receipt.stack == [{"type": "Integer", "value": "7"}]
        assert receipt.notifications == []
        assert output.result.gas_used > 0

    def test_receipt_projects_fault_and_exception(self):
        script = _build_script_hex(lambda sb: sb.emit(OpCode.THROW))
        t8n = T8N(alloc={}, env={"currentBlockNumber": 100}, txs=[{"script": script, "signers": []}])
        output = t8n.run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert receipt.stack == []
        assert receipt.exception is not None
        assert "Stack underflow" in receipt.exception

    def test_receipt_projects_notifications(self):
        notify_hash = get_interop_hash("System.Runtime.Notify")
        sb = ScriptBuilder()
        sb.emit_push("Transfer")
        sb.emit_push(7)
        sb.emit_push(1)
        sb.emit(OpCode.PACK)
        sb.emit_syscall(notify_hash)
        sb.emit_push(1)
        script = sb.to_bytes()

        t8n = T8N(alloc={}, env={"currentBlockNumber": 100}, txs=[{"script": script.hex(), "signers": []}])
        output = t8n.run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "HALT"
        assert receipt.stack == [{"type": "Integer", "value": "1"}]
        assert len(receipt.notifications) == 1
        notification = receipt.notifications[0]
        assert notification["contract"] == f"0x{hash160(script).hex()}"
        assert notification["eventName"] == "Transfer"
        assert notification["state"] == {"type": "Array", "value": [{"type": "Integer", "value": "7"}]}

    def test_post_alloc_extracts_account_entries_in_schema(self):
        addr1 = "0000000000000000000000000000000000000001"
        addr2 = "0000000000000000000000000000000000000002"
        alloc = {
            addr1: {"neoBalance": 10, "gasBalance": 5000000, "storage": {"aa": "bb"}},
            addr2: {"gasBalance": 3},
        }

        output = T8N(alloc=alloc, env={"currentBlockNumber": 1}, txs=[]).run()

        assert set(output.alloc.keys()) == {addr1, addr2}
        assert output.alloc[addr1]["neoBalance"] == 10
        assert output.alloc[addr1]["gasBalance"] == 5000000
        assert output.alloc[addr1]["storage"] == {"aa": "bb"}
        assert output.alloc[addr2]["gasBalance"] == 3

    def test_environment_network_is_used_by_runtime_getnetwork(self):
        network = 894710606
        script = _build_script_hex(
            lambda sb: sb.emit_syscall(get_interop_hash("System.Runtime.GetNetwork"))
        )
        t8n = T8N(
            alloc={},
            env={"currentBlockNumber": 123, "network": network},
            txs=[{"script": script, "signers": []}],
        )
        output = t8n.run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "HALT"
        assert receipt.stack == [{"type": "Integer", "value": str(network)}]

    def test_invalid_script_hex_returns_fault_receipt_and_continues(self):
        valid_script = _build_script_hex(lambda sb: sb.emit_push(3))
        t8n = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[
                {"script": "not-hex", "signers": []},
                {"script": valid_script, "signers": []},
            ],
        )
        output = t8n.run()

        assert len(output.result.receipts) == 2
        first = output.result.receipts[0]
        second = output.result.receipts[1]
        assert first.vm_state == "FAULT"
        assert "hex" in (first.exception or "").lower()
        assert second.vm_state == "HALT"
        assert second.stack == [{"type": "Integer", "value": "3"}]

    def test_missing_script_field_returns_fault_receipt_and_continues(self):
        valid_script = _build_script_hex(lambda sb: sb.emit_push(3))
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[
                {"signers": []},
                {"script": valid_script, "signers": []},
            ],
        ).run()

        assert len(output.result.receipts) == 2
        first = output.result.receipts[0]
        second = output.result.receipts[1]
        assert first.vm_state == "FAULT"
        assert "missing required script" in (first.exception or "").lower()
        assert second.vm_state == "HALT"
        assert second.stack == [{"type": "Integer", "value": "3"}]

    def test_non_numeric_system_fee_returns_fault_receipt_and_continues(self):
        valid_script = _build_script_hex(lambda sb: sb.emit_push(3))
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[
                {"script": valid_script, "systemFee": "not-a-number", "signers": []},
                {"script": valid_script, "signers": []},
            ],
        ).run()

        assert len(output.result.receipts) == 2
        first = output.result.receipts[0]
        second = output.result.receipts[1]
        assert first.vm_state == "FAULT"
        assert "system fee" in (first.exception or "").lower()
        assert second.vm_state == "HALT"
        assert second.stack == [{"type": "Integer", "value": "3"}]

    def test_signers_must_be_array_returns_fault_receipt_and_continues(self):
        valid_script = _build_script_hex(lambda sb: sb.emit_push(3))
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[
                {"script": valid_script, "signers": "not-an-array"},
                {"script": valid_script, "signers": []},
            ],
        ).run()

        assert len(output.result.receipts) == 2
        first = output.result.receipts[0]
        second = output.result.receipts[1]
        assert first.vm_state == "FAULT"
        assert "signers must be an array" in (first.exception or "").lower()
        assert second.vm_state == "HALT"
        assert second.stack == [{"type": "Integer", "value": "3"}]

    def test_empty_script_returns_fault_receipt(self):
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[{"script": "", "signers": []}],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "empty" in (receipt.exception or "").lower()

    def test_oversized_script_returns_fault_receipt(self):
        oversized_nop_script = (f"{int(OpCode.NOP):02x}") * 102401
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[{"script": oversized_nop_script, "signers": []}],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "size" in (receipt.exception or "").lower()

    def test_script_at_102400_bytes_still_exceeds_tx_size_limit(self):
        max_script = (f"{int(OpCode.NOP):02x}") * 102400
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[{"script": max_script, "signers": []}],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "transaction size" in (receipt.exception or "").lower()

    def test_tx_size_exact_boundary_without_signers_halts(self):
        # unsigned tx overhead: 25 fixed + 1(signers varint) + 1(attrs varint) + 5(script varint)
        script_len = 102400 - 32
        script = (f"{int(OpCode.NOP):02x}") * script_len
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[{"script": script, "signers": []}],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "HALT"

    def test_tx_size_one_byte_over_boundary_without_signers_faults(self):
        script_len = 102400 - 31
        script = (f"{int(OpCode.NOP):02x}") * script_len
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[{"script": script, "signers": []}],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "transaction size" in (receipt.exception or "").lower()

    def test_tx_size_exact_boundary_with_one_signer_halts(self):
        # +21 signer bytes when CALLED_BY_ENTRY signer is present.
        script_len = 102400 - (32 + 21)
        script = (f"{int(OpCode.NOP):02x}") * script_len
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[{"script": script, "signers": [{"account": "11" * 20, "scopes": 0x01}]}],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "HALT"

    def test_tx_size_one_byte_over_boundary_with_one_signer_faults(self):
        script_len = 102400 - (32 + 21) + 1
        script = (f"{int(OpCode.NOP):02x}") * script_len
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[{"script": script, "signers": [{"account": "11" * 20, "scopes": 0x01}]}],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "transaction size" in (receipt.exception or "").lower()

    def test_tx_size_exact_boundary_with_max_scoped_signer_payload_halts(self):
        allowed_contracts = [f"{i + 1:040x}" for i in range(16)]
        allowed_groups = [f"02{i + 1:064x}" for i in range(16)]
        rules = [
            {"action": 1, "condition": {"type": 0x00, "expression": True}}
            for _ in range(16)
        ]
        # Signer size:
        # 21 (account + scope)
        # + (1 + 20*16) custom contracts
        # + (1 + 33*16) custom groups
        # + (1 + 3*16) witness rules with boolean conditions
        signer_size = 21 + (1 + 20 * 16) + (1 + 33 * 16) + (1 + 3 * 16)
        # Base unsigned tx overhead is 32 bytes for large scripts:
        # 25 header + 1 signer-count + 1 attrs-count + 5 script varint.
        script_len = 102400 - (32 + signer_size)
        script = (f"{int(OpCode.NOP):02x}") * script_len
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[
                {
                    "script": script,
                    "signers": [
                        {
                            "account": "11" * 20,
                            "scopes": 0x71,  # ENTRY | CUSTOM_CONTRACTS | CUSTOM_GROUPS | WITNESS_RULES
                            "allowedContracts": allowed_contracts,
                            "allowedGroups": allowed_groups,
                            "rules": rules,
                        }
                    ],
                }
            ],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "HALT"

    def test_tx_size_one_byte_over_boundary_with_max_scoped_signer_payload_faults(self):
        allowed_contracts = [f"{i + 1:040x}" for i in range(16)]
        allowed_groups = [f"02{i + 1:064x}" for i in range(16)]
        rules = [
            {"action": 1, "condition": {"type": 0x00, "expression": True}}
            for _ in range(16)
        ]
        signer_size = 21 + (1 + 20 * 16) + (1 + 33 * 16) + (1 + 3 * 16)
        script_len = 102400 - (32 + signer_size) + 1
        script = (f"{int(OpCode.NOP):02x}") * script_len
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[
                {
                    "script": script,
                    "signers": [
                        {
                            "account": "11" * 20,
                            "scopes": 0x71,
                            "allowedContracts": allowed_contracts,
                            "allowedGroups": allowed_groups,
                            "rules": rules,
                        }
                    ],
                }
            ],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "transaction size" in (receipt.exception or "").lower()

    def test_expired_valid_until_block_returns_fault_receipt(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 101},
            txs=[{"script": script, "validUntilBlock": 100, "signers": []}],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "validuntilblock" in (receipt.exception or "").lower()

    def test_invalid_signer_account_length_returns_fault_receipt(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[{"script": script, "signers": [{"account": "aa", "scopes": 1}]}],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "signer account" in (receipt.exception or "").lower()

    def test_strict_mode_raises_on_invalid_script_hex(self):
        t8n = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[{"script": "not-hex", "signers": []}],
            strict=True,
        )

        try:
            _ = t8n.run()
        except ValueError as exc:
            assert "script hex" in str(exc).lower()
        else:
            raise AssertionError("strict mode must raise on invalid tx input")

    def test_strict_mode_raises_on_missing_script_field(self):
        t8n = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[{"signers": []}],
            strict=True,
        )

        try:
            _ = t8n.run()
        except ValueError as exc:
            assert "missing required script" in str(exc).lower()
        else:
            raise AssertionError("strict mode must raise on missing script")

    def test_strict_mode_raises_on_empty_script(self):
        t8n = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[{"script": "", "signers": []}],
            strict=True,
        )

        try:
            _ = t8n.run()
        except ValueError as exc:
            assert "empty" in str(exc).lower()
        else:
            raise AssertionError("strict mode must raise on empty tx script")

    def test_strict_mode_raises_on_oversized_script(self):
        oversized_nop_script = (f"{int(OpCode.NOP):02x}") * 102401
        t8n = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[{"script": oversized_nop_script, "signers": []}],
            strict=True,
        )

        try:
            _ = t8n.run()
        except ValueError as exc:
            assert "size" in str(exc).lower()
        else:
            raise AssertionError("strict mode must raise on oversized tx script")

    def test_strict_mode_raises_when_tx_envelope_exceeds_size_limit(self):
        max_script = (f"{int(OpCode.NOP):02x}") * 102400
        t8n = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[{"script": max_script, "signers": []}],
            strict=True,
        )

        try:
            _ = t8n.run()
        except ValueError as exc:
            assert "transaction size" in str(exc).lower()
        else:
            raise AssertionError("strict mode must raise on tx-size overflow")

    def test_strict_mode_raises_on_expired_valid_until_block(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        t8n = T8N(
            alloc={},
            env={"currentBlockNumber": 101},
            txs=[{"script": script, "validUntilBlock": 100, "signers": []}],
            strict=True,
        )

        try:
            _ = t8n.run()
        except ValueError as exc:
            assert "validuntilblock" in str(exc).lower()
        else:
            raise AssertionError("strict mode must raise on expired validUntilBlock")

    def test_strict_mode_raises_on_invalid_witness_scope(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        t8n = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[{"script": script, "signers": [{"account": "11" * 20, "scopes": 0x02}]}],
            strict=True,
        )

        try:
            _ = t8n.run()
        except ValueError as exc:
            assert "witnessscope" in str(exc).lower()
        else:
            raise AssertionError("strict mode must raise on invalid WitnessScope")

    def test_valid_until_equal_current_block_returns_fault_receipt(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 100},
            txs=[{"script": script, "validUntilBlock": 100, "signers": []}],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "validuntilblock" in (receipt.exception or "").lower()

    def test_valid_until_too_far_in_future_returns_fault_receipt(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 100},
            txs=[{"script": script, "validUntilBlock": 6000, "signers": []}],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "validuntilblock" in (receipt.exception or "").lower()

    def test_valid_until_exceeds_uint32_returns_fault_receipt(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 0xFFFF_FFFE},
            txs=[{"script": script, "validUntilBlock": 0x1_0000_0000, "signers": []}],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "uint32" in (receipt.exception or "").lower()

    def test_negative_nonce_returns_fault_receipt(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[{"script": script, "nonce": -1, "signers": []}],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "nonce" in (receipt.exception or "").lower()

    def test_nonce_exceeds_uint32_returns_fault_receipt(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[{"script": script, "nonce": 0x1_0000_0000, "signers": []}],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "uint32" in (receipt.exception or "").lower()

    def test_tx_hash_is_canonical_for_numeric_string_fields(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        base_env = {"currentBlockNumber": 100}

        string_output = T8N(
            alloc={},
            env=base_env,
            txs=[
                {
                    "script": script,
                    "systemFee": "0x1",
                    "networkFee": "0x2",
                    "nonce": "0x3",
                    "validUntilBlock": "0x65",
                    "signers": [],
                }
            ],
        ).run()
        int_output = T8N(
            alloc={},
            env=base_env,
            txs=[
                {
                    "script": script,
                    "systemFee": 1,
                    "networkFee": 2,
                    "nonce": 3,
                    "validUntilBlock": 101,
                    "signers": [],
                }
            ],
        ).run()

        assert string_output.result.receipts[0].vm_state == "HALT"
        assert int_output.result.receipts[0].vm_state == "HALT"
        assert (
            string_output.result.receipts[0].tx_hash
            == int_output.result.receipts[0].tx_hash
        )

    def test_negative_system_fee_returns_fault_receipt(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[{"script": script, "systemFee": -1, "signers": []}],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "system fee" in (receipt.exception or "").lower()

    def test_negative_network_fee_returns_fault_receipt(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[{"script": script, "networkFee": -1, "signers": []}],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "network fee" in (receipt.exception or "").lower()

    def test_duplicate_signers_return_fault_receipt(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        signer = "11" * 20
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[
                {
                    "script": script,
                    "signers": [{"account": signer, "scopes": 1}, {"account": signer, "scopes": 1}],
                }
            ],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "duplicate signer" in (receipt.exception or "").lower()

    def test_invalid_signer_scope_bits_return_fault_receipt(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[{"script": script, "signers": [{"account": "11" * 20, "scopes": 0x02}]}],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "witnessscope" in (receipt.exception or "").lower()

    def test_global_scope_combined_with_other_scope_returns_fault_receipt(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[{"script": script, "signers": [{"account": "11" * 20, "scopes": 0x81}]}],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "global witnessscope" in (receipt.exception or "").lower()

    def test_invalid_allowed_group_length_returns_fault_receipt(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[
                {
                    "script": script,
                    "signers": [
                        {
                            "account": "11" * 20,
                            "scopes": 0x20,
                            "allowedGroups": ["22" * 20],
                        }
                    ],
                }
            ],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "allowedgroups" in (receipt.exception or "").lower()

    def test_invalid_allowed_group_prefix_returns_fault_receipt(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[
                {
                    "script": script,
                    "signers": [
                        {
                            "account": "11" * 20,
                            "scopes": 0x20,
                            "allowedGroups": ["04" + ("22" * 32)],
                        }
                    ],
                }
            ],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "compressed ecpoint" in (receipt.exception or "").lower()

    def test_check_witness_true_for_matching_signer_called_by_entry(self):
        account = "11" * 20
        syscall = get_interop_hash("System.Runtime.CheckWitness")
        script = _build_script_hex(
            lambda sb: (
                sb.emit_push(bytes.fromhex(account)),
                sb.emit_syscall(syscall),
            )
        )
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[{"script": script, "signers": [{"account": account, "scopes": 0x01}]}],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "HALT"
        assert receipt.stack == [{"type": "Integer", "value": "1"}]

    def test_check_witness_false_for_missing_signer(self):
        account = "11" * 20
        syscall = get_interop_hash("System.Runtime.CheckWitness")
        script = _build_script_hex(
            lambda sb: (
                sb.emit_push(bytes.fromhex(account)),
                sb.emit_syscall(syscall),
            )
        )
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[{"script": script, "signers": []}],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "HALT"
        assert receipt.stack == [{"type": "Integer", "value": "0"}]

    def test_check_witness_custom_contract_scope_respected(self):
        account = "11" * 20
        syscall = get_interop_hash("System.Runtime.CheckWitness")
        sb = ScriptBuilder()
        sb.emit_push(bytes.fromhex(account))
        sb.emit_syscall(syscall)
        script_bytes = sb.to_bytes()
        script = script_bytes.hex()

        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[
                {
                    "script": script,
                    "signers": [
                        {
                            "account": account,
                            "scopes": 0x10,
                            "allowedContracts": [hash160(script_bytes).hex()],
                        }
                    ],
                }
            ],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "HALT"
        assert receipt.stack == [{"type": "Integer", "value": "1"}]

    def test_check_witness_rules_allow_boolean_true(self):
        account = "11" * 20
        syscall = get_interop_hash("System.Runtime.CheckWitness")
        script = _build_script_hex(
            lambda sb: (
                sb.emit_push(bytes.fromhex(account)),
                sb.emit_syscall(syscall),
            )
        )
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[
                {
                    "script": script,
                    "signers": [
                        {
                            "account": account,
                            "scopes": 0x40,
                            "rules": [
                                {
                                    "action": 1,
                                    "condition": {"type": 0x00, "expression": True},
                                }
                            ],
                        }
                    ],
                }
            ],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "HALT"
        assert receipt.stack == [{"type": "Integer", "value": "1"}]

    def test_malformed_witness_rule_returns_fault_receipt(self):
        account = "11" * 20
        syscall = get_interop_hash("System.Runtime.CheckWitness")
        script = _build_script_hex(
            lambda sb: (
                sb.emit_push(bytes.fromhex(account)),
                sb.emit_syscall(syscall),
            )
        )
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[
                {
                    "script": script,
                    "signers": [
                        {
                            "account": account,
                            "scopes": 0x40,
                            "rules": [{"action": 1}],
                        }
                    ],
                }
            ],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "witness rule" in (receipt.exception or "").lower()

    def test_strict_mode_raises_on_malformed_witness_rule(self):
        account = "11" * 20
        syscall = get_interop_hash("System.Runtime.CheckWitness")
        script = _build_script_hex(
            lambda sb: (
                sb.emit_push(bytes.fromhex(account)),
                sb.emit_syscall(syscall),
            )
        )
        t8n = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[
                {
                    "script": script,
                    "signers": [
                        {
                            "account": account,
                            "scopes": 0x40,
                            "rules": [{"action": 1}],
                        }
                    ],
                }
            ],
            strict=True,
        )

        try:
            _ = t8n.run()
        except ValueError as exc:
            assert "witness rule" in str(exc).lower()
        else:
            raise AssertionError("strict mode must raise on malformed witness rule")

    def test_witness_rules_require_witness_rules_scope(self):
        account = "11" * 20
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[
                {
                    "script": script,
                    "signers": [
                        {
                            "account": account,
                            "scopes": 0x01,
                            "rules": [
                                {
                                    "action": 1,
                                    "condition": {"type": 0x00, "expression": True},
                                }
                            ],
                        }
                    ],
                }
            ],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "witness rules require" in (receipt.exception or "").lower()

    def test_check_witness_rules_allow_with_string_names(self):
        account = "11" * 20
        syscall = get_interop_hash("System.Runtime.CheckWitness")
        script = _build_script_hex(
            lambda sb: (
                sb.emit_push(bytes.fromhex(account)),
                sb.emit_syscall(syscall),
            )
        )
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[
                {
                    "script": script,
                    "signers": [
                        {
                            "account": account,
                            "scopes": 0x40,
                            "rules": [
                                {
                                    "action": "Allow",
                                    "condition": {"type": "Boolean", "expression": True},
                                }
                            ],
                        }
                    ],
                }
            ],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "HALT"
        assert receipt.stack == [{"type": "Integer", "value": "1"}]

    def test_witness_rules_over_max_entries_returns_fault_receipt(self):
        account = "11" * 20
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        rules = [
            {"action": 1, "condition": {"type": 0x00, "expression": True}}
            for _ in range(17)
        ]
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[
                {
                    "script": script,
                    "signers": [
                        {
                            "account": account,
                            "scopes": 0x40,
                            "rules": rules,
                        }
                    ],
                }
            ],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "at most 16" in (receipt.exception or "").lower()

    def test_witness_condition_nesting_depth_limit_returns_fault_receipt(self):
        account = "11" * 20
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        condition = {
            "type": 0x01,
            "expression": {
                "type": 0x01,
                "expression": {
                    "type": 0x01,
                    "expression": {"type": 0x00, "expression": True},
                },
            },
        }
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[
                {
                    "script": script,
                    "signers": [
                        {
                            "account": account,
                            "scopes": 0x40,
                            "rules": [{"action": 1, "condition": condition}],
                        }
                    ],
                }
            ],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "nesting depth" in (receipt.exception or "").lower()

    def test_invalid_witness_condition_group_prefix_returns_fault_receipt(self):
        account = "11" * 20
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[
                {
                    "script": script,
                    "signers": [
                        {
                            "account": account,
                            "scopes": 0x40,
                            "rules": [
                                {
                                    "action": 1,
                                    "condition": {"type": 0x19, "group": "04" + ("22" * 32)},
                                }
                            ],
                        }
                    ],
                }
            ],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "compressed ecpoint" in (receipt.exception or "").lower()

    def test_too_many_signers_returns_fault_receipt(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        signers = [{"account": f"{i + 1:040x}", "scopes": 0x01} for i in range(17)]
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[{"script": script, "signers": signers}],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "at most 16 signers" in (receipt.exception or "").lower()

    def test_allowed_contracts_require_custom_contracts_scope(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[
                {
                    "script": script,
                    "signers": [
                        {
                            "account": "11" * 20,
                            "scopes": 0x01,
                            "allowedContracts": ["22" * 20],
                        }
                    ],
                }
            ],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "allowedcontracts require custom_contracts scope" in (
            receipt.exception or ""
        ).lower()

    def test_allowed_groups_require_custom_groups_scope(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[
                {
                    "script": script,
                    "signers": [
                        {
                            "account": "11" * 20,
                            "scopes": 0x01,
                            "allowedGroups": ["02" + "33" * 32],
                        }
                    ],
                }
            ],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "allowedgroups require custom_groups scope" in (
            receipt.exception or ""
        ).lower()

    def test_too_many_allowed_contracts_returns_fault_receipt(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        allowed_contracts = [f"{i + 1:040x}" for i in range(17)]
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[
                {
                    "script": script,
                    "signers": [
                        {
                            "account": "11" * 20,
                            "scopes": 0x10,
                            "allowedContracts": allowed_contracts,
                        }
                    ],
                }
            ],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "allowedcontracts must contain at most 16 entries" in (
            receipt.exception or ""
        ).lower()

    def test_too_many_allowed_groups_returns_fault_receipt(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        allowed_groups = [f"02{i:064x}" for i in range(1, 18)]
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=[
                {
                    "script": script,
                    "signers": [
                        {
                            "account": "11" * 20,
                            "scopes": 0x20,
                            "allowedGroups": allowed_groups,
                        }
                    ],
                }
            ],
        ).run()

        receipt = output.result.receipts[0]
        assert receipt.vm_state == "FAULT"
        assert "allowedgroups must contain at most 16 entries" in (
            receipt.exception or ""
        ).lower()

    def test_too_many_transactions_returns_fault_receipts(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        txs = [{"script": script, "signers": []} for _ in range(513)]
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=txs,
        ).run()

        assert len(output.result.receipts) == 513
        assert all(r.vm_state == "FAULT" for r in output.result.receipts)
        assert "max transactions per block" in (
            output.result.receipts[0].exception or ""
        ).lower()

    def test_strict_mode_raises_on_too_many_transactions(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        txs = [{"script": script, "signers": []} for _ in range(513)]
        t8n = T8N(
            alloc={},
            env={"currentBlockNumber": 1},
            txs=txs,
            strict=True,
        )

        try:
            _ = t8n.run()
        except ValueError as exc:
            assert "max transactions per block" in str(exc).lower()
        else:
            raise AssertionError("strict mode must raise on tx-count overflow")

    def test_testnet_profile_allows_513_transactions(self):
        txs = [{"script": "not-hex", "signers": []} for _ in range(513)]
        output = T8N(
            alloc={},
            env={
                "currentBlockNumber": 1,
                "network": ProtocolSettings.testnet().network,
            },
            txs=txs,
        ).run()

        assert len(output.result.receipts) == 513
        assert all(r.vm_state == "FAULT" for r in output.result.receipts)
        assert "max transactions per block" not in (
            output.result.receipts[0].exception or ""
        ).lower()

    def test_unknown_network_uses_mainnet_tx_limit(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        txs = [{"script": script, "signers": []} for _ in range(513)]
        output = T8N(
            alloc={},
            env={"currentBlockNumber": 1, "network": 123456789},
            txs=txs,
        ).run()

        assert len(output.result.receipts) == 513
        assert all(r.vm_state == "FAULT" for r in output.result.receipts)
        assert "513 > 512" in (output.result.receipts[0].exception or "")

    def test_tx_count_overflow_preserves_prestate_alloc(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        alloc = {
            "11" * 20: {"neoBalance": 10, "gasBalance": 20, "storage": {"aa": "bb"}},
        }
        txs = [{"script": script, "signers": []} for _ in range(513)]
        output = T8N(
            alloc=alloc,
            env={"currentBlockNumber": 1},
            txs=txs,
        ).run()

        assert output.alloc["11" * 20]["neoBalance"] == 10
        assert output.alloc["11" * 20]["gasBalance"] == 20
        assert output.alloc["11" * 20]["storage"] == {"aa": "bb"}

    def test_tx_count_overflow_state_root_matches_noop_run(self):
        script = _build_script_hex(lambda sb: sb.emit_push(1))
        alloc = {
            "11" * 20: {"neoBalance": 10, "gasBalance": 20, "storage": {"aa": "bb"}},
        }
        txs = [{"script": script, "signers": []} for _ in range(513)]

        overflow_output = T8N(
            alloc=alloc,
            env={"currentBlockNumber": 1},
            txs=txs,
        ).run()
        noop_output = T8N(
            alloc=alloc,
            env={"currentBlockNumber": 1},
            txs=[],
        ).run()

        assert overflow_output.result.state_root == noop_output.result.state_root
