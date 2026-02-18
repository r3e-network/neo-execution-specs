"""Neo t8n (transition) tool - Main logic.

Executes transactions against a pre-state and produces post-state.
"""

from __future__ import annotations

from collections.abc import Iterable
from types import SimpleNamespace
from typing import Any

from neo.crypto.hash import hash256
from neo.persistence.snapshot import MemorySnapshot
from neo.protocol_settings import ProtocolSettings
from neo.smartcontract.application_engine import ApplicationEngine, VMState
from neo.smartcontract.trigger import TriggerType
from neo.tools.t8n.types import (
    AccountState,
    Alloc,
    Environment,
    Receipt,
    T8NOutput,
    T8NResult,
    TransactionInput,
)

# t8n alloc key layout (tool-local representation)
PREFIX_BALANCE = 0x14
BALANCE_TYPE_GAS = 0x00
BALANCE_TYPE_NEO = 0x01
PREFIX_ACCOUNT_STORAGE = 0x70
ACCOUNT_LENGTH = 20


def _normalize_hex(hex_str: str) -> str:
    value = hex_str[2:] if hex_str.startswith(("0x", "0X")) else hex_str
    value = value.strip().lower()
    if len(value) % 2:
        value = f"0{value}"
    return value


def _hex_to_bytes(hex_str: str) -> bytes:
    """Convert hex string to bytes."""
    return bytes.fromhex(_normalize_hex(hex_str))


def _bytes_to_hex(data: bytes) -> str:
    """Convert bytes to 0x-prefixed hex string."""
    return "0x" + data.hex()


def _balance_key(addr: bytes, balance_type: int) -> bytes:
    return bytes([PREFIX_BALANCE, balance_type]) + addr


def _decode_uncaught_exception(error_item: Any) -> str:
    try:
        return error_item.get_string()
    except Exception:
        try:
            return error_item.get_bytes_unsafe().decode("utf-8", errors="replace")
        except Exception:
            return str(error_item)


def _to_uint32_hash_bytes(value: int) -> bytes:
    try:
        if isinstance(value, str):
            parsed = int(value.strip(), 0)
        else:
            parsed = int(value)
        return parsed.to_bytes(4, "little", signed=False)
    except Exception:
        return str(value).encode("utf-8", errors="replace")


def _to_int64_hash_bytes(value: int) -> bytes:
    try:
        if isinstance(value, str):
            parsed = int(value.strip(), 0)
        else:
            parsed = int(value)
        return parsed.to_bytes(8, "little", signed=True)
    except Exception:
        return str(value).encode("utf-8", errors="replace")


def _parse_integer(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError(f"{field_name} must be an integer")
        try:
            return int(text, 0)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be an integer") from exc
    raise ValueError(f"{field_name} must be an integer")


def _validate_compressed_ecpoint(value: bytes, field_name: str) -> None:
    if len(value) != 33:
        raise ValueError(f"{field_name} must be 33-byte ECPoint")
    if value[0] not in (0x02, 0x03):
        raise ValueError(f"{field_name} must use compressed ECPoint format")


def _var_int_size(value: int) -> int:
    if value < 0xFD:
        return 1
    if value <= 0xFFFF:
        return 3
    if value <= 0xFFFF_FFFF:
        return 5
    return 9


def _estimate_witness_condition_size(condition: Any) -> int:
    cond_type = getattr(condition, "type", None)
    if cond_type == 0x00:  # Boolean
        return 2
    if cond_type == 0x01:  # Not
        expression = getattr(condition, "expression", None)
        if expression is None:
            raise ValueError("Not witness condition is missing expression")
        return 1 + _estimate_witness_condition_size(expression)
    if cond_type in (0x02, 0x03):  # And / Or
        expressions = getattr(condition, "expressions", None)
        if expressions is None:
            raise ValueError("And/Or witness condition is missing expressions")
        return 1 + _var_int_size(len(expressions)) + sum(_estimate_witness_condition_size(expr) for expr in expressions)
    if cond_type in (0x18, 0x28):  # ScriptHash / CalledByContract
        return 1 + 20
    if cond_type in (0x19, 0x29):  # Group / CalledByGroup
        return 1 + 33
    if cond_type == 0x20:  # CalledByEntry
        return 1
    raise ValueError(f"Unsupported witness condition type for size estimation: {cond_type}")


def _estimate_witness_rule_size(rule: Any) -> int:
    condition = getattr(rule, "condition", None)
    if condition is None:
        raise ValueError("Witness rule is missing condition")
    return 1 + _estimate_witness_condition_size(condition)


def _normalize_symbol(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


_WITNESS_RULE_ACTIONS = {
    "deny": 0,
    "allow": 1,
}

_WITNESS_CONDITION_TYPES = {
    "boolean": 0x00,
    "not": 0x01,
    "and": 0x02,
    "or": 0x03,
    "scripthash": 0x18,
    "group": 0x19,
    "calledbyentry": 0x20,
    "calledbycontract": 0x28,
    "calledbygroup": 0x29,
}

_MAX_WITNESS_RULES = 16
_MAX_WITNESS_CONDITION_DEPTH = 2
_MAX_WITNESS_CONDITION_SUBITEMS = 16
_MAX_TX_SIGNERS = 16
_MAX_SIGNER_ALLOWED_CONTRACTS = 16
_MAX_SIGNER_ALLOWED_GROUPS = 16
_MAX_UINT32 = 0xFFFF_FFFF
_MAX_TRANSACTION_SIZE = 102400
_WITNESS_CONDITION_VALID_TYPES: frozenset[int] = frozenset(_WITNESS_CONDITION_TYPES.values())


def _parse_witness_rule_action(action: Any) -> int:
    if isinstance(action, bool):
        raise ValueError("Witness rule action must be 0/1 or Deny/Allow")
    if isinstance(action, int):
        if action in (0, 1):
            return action
        raise ValueError("Witness rule action must be 0/1")
    if isinstance(action, str):
        try:
            parsed = int(action, 0)
            if parsed in (0, 1):
                return parsed
        except ValueError:
            pass
        mapped = _WITNESS_RULE_ACTIONS.get(_normalize_symbol(action))
        if mapped is not None:
            return mapped
    raise ValueError("Witness rule action must be 0/1 or Deny/Allow")


def _parse_witness_condition_type(raw_type: Any) -> int:
    if isinstance(raw_type, bool):
        raise ValueError("Witness condition type must be integer or name")
    if isinstance(raw_type, int):
        if raw_type in _WITNESS_CONDITION_VALID_TYPES:
            return raw_type
        raise ValueError(f"Unknown witness condition type: {raw_type}")
    if isinstance(raw_type, str):
        try:
            parsed = int(raw_type, 0)
            if parsed in _WITNESS_CONDITION_VALID_TYPES:
                return parsed
        except ValueError:
            pass
        mapped = _WITNESS_CONDITION_TYPES.get(_normalize_symbol(raw_type))
        if mapped is not None:
            return mapped

    raise ValueError("Witness condition type must be integer or known name")


def _parse_witness_condition(condition: Any, depth: int = 0) -> Any:
    if depth > _MAX_WITNESS_CONDITION_DEPTH:
        raise ValueError(f"Witness condition nesting depth exceeds {_MAX_WITNESS_CONDITION_DEPTH}")
    if not isinstance(condition, dict):
        raise ValueError("Witness condition must be an object")

    if "type" not in condition:
        raise ValueError("Witness condition is missing type")
    cond_type = _parse_witness_condition_type(condition["type"])

    if cond_type == 0x00:  # Boolean
        if "expression" not in condition:
            raise ValueError("Boolean witness condition is missing expression")
        expression = condition["expression"]
        if not isinstance(expression, bool):
            raise ValueError("Boolean witness condition expression must be boolean")
        return SimpleNamespace(type=cond_type, expression=expression)

    if cond_type == 0x01:  # Not
        if "expression" not in condition:
            raise ValueError("Not witness condition is missing expression")
        return SimpleNamespace(
            type=cond_type,
            expression=_parse_witness_condition(condition["expression"], depth + 1),
        )

    if cond_type in (0x02, 0x03):  # And / Or
        expressions = condition.get("expressions")
        if not isinstance(expressions, list):
            raise ValueError("And/Or witness condition expressions must be an array")
        if len(expressions) > _MAX_WITNESS_CONDITION_SUBITEMS:
            raise ValueError(
                f"And/Or witness condition must contain at most {_MAX_WITNESS_CONDITION_SUBITEMS} expressions"
            )
        return SimpleNamespace(
            type=cond_type,
            expressions=[_parse_witness_condition(expr, depth + 1) for expr in expressions],
        )

    if cond_type in (0x18, 0x28):  # ScriptHash / CalledByContract
        hash_hex = condition.get("hash", condition.get("scriptHash"))
        if hash_hex is None:
            raise ValueError("Hash witness condition is missing hash")
        try:
            script_hash = _hex_to_bytes(hash_hex)
        except ValueError as exc:
            raise ValueError("Hash witness condition hash is not valid hex") from exc
        if len(script_hash) != ACCOUNT_LENGTH:
            raise ValueError("Hash witness condition hash must be 20 bytes")
        return SimpleNamespace(type=cond_type, hash=script_hash)

    if cond_type in (0x19, 0x29):  # Group / CalledByGroup
        group_hex = condition.get("group")
        if group_hex is None:
            raise ValueError("Group witness condition is missing group")
        try:
            group = _hex_to_bytes(group_hex)
        except ValueError as exc:
            raise ValueError("Group witness condition group is not valid hex") from exc
        _validate_compressed_ecpoint(group, "Group witness condition group")
        return SimpleNamespace(type=cond_type, group=group)

    if cond_type == 0x20:  # CalledByEntry
        return SimpleNamespace(type=cond_type)

    raise ValueError(f"Unsupported witness condition type: {cond_type}")


def _parse_witness_rules(rules: Any) -> list[Any]:
    if rules is None:
        return []
    if not isinstance(rules, list):
        raise ValueError("Signer witness rules must be an array")
    if len(rules) > _MAX_WITNESS_RULES:
        raise ValueError(f"Signer witness rules must contain at most {_MAX_WITNESS_RULES} entries")

    parsed_rules: list[Any] = []
    for rule in rules:
        if not isinstance(rule, dict):
            raise ValueError("Witness rule must be an object")
        if "action" not in rule:
            raise ValueError("Witness rule is missing action")
        if "condition" not in rule:
            raise ValueError("Witness rule is missing condition")
        parsed_rules.append(
            SimpleNamespace(
                action=_parse_witness_rule_action(rule["action"]),
                condition=_parse_witness_condition(rule["condition"]),
            )
        )
    return parsed_rules


class T8N:
    """Neo state transition tool.

    Executes transactions against a pre-state allocation
    and produces the resulting post-state.
    """

    def __init__(
        self,
        alloc: dict[str, Any],
        env: dict[str, Any],
        txs: list[dict[str, Any]],
        strict: bool = False,
    ):
        """Initialize t8n with input data.

        Args:
            alloc: Pre-state allocation (address -> account state)
            env: Block environment
            txs: List of transactions to execute
            strict: When True, fail fast on transaction validation/execution errors
        """
        self.pre_alloc = self._parse_alloc(alloc)
        self.env = Environment.from_dict(env)
        self.txs = [TransactionInput.from_dict(tx) for tx in txs]
        self.strict = strict
        self.snapshot = MemorySnapshot()
        self.protocol_settings = self._resolve_protocol_settings(self.env.network)
        self._bind_snapshot_context()
        self.receipts: list[Receipt] = []
        self.total_gas_used = 0

    @staticmethod
    def _resolve_protocol_settings(network: int) -> ProtocolSettings:
        if network == ProtocolSettings.mainnet().network:
            return ProtocolSettings.mainnet()
        if network == ProtocolSettings.testnet().network:
            return ProtocolSettings.testnet()

        # Unknown network: keep v3.9.1 defaults but report the configured magic.
        settings = ProtocolSettings.mainnet()
        settings.network = network
        return settings

    def _bind_snapshot_context(self) -> None:
        block = SimpleNamespace(
            index=self.env.current_block_number,
            timestamp=self.env.timestamp,
            nonce=self.env.nonce,
            primary_index=self.env.primary_index,
            transactions=[],
        )
        setattr(self.snapshot, "persisting_block", block)
        setattr(self.snapshot, "protocol_settings", self.protocol_settings)

    def _parse_alloc(self, alloc: dict[str, Any]) -> Alloc:
        """Parse allocation dictionary."""
        result: Alloc = {}
        for addr, state in alloc.items():
            result[_normalize_hex(addr)] = AccountState.from_dict(state)
        return result

    def _init_state(self) -> None:
        """Initialize snapshot from pre-state allocation."""
        for addr, state in self.pre_alloc.items():
            addr_bytes = _hex_to_bytes(addr)
            if len(addr_bytes) != ACCOUNT_LENGTH:
                raise ValueError(f"alloc address must be 20 bytes: {addr}")

            if state.gas_balance > 0:
                self.snapshot.put(
                    _balance_key(addr_bytes, BALANCE_TYPE_GAS),
                    state.gas_balance.to_bytes(32, "little", signed=False),
                )

            if state.neo_balance > 0:
                self.snapshot.put(
                    _balance_key(addr_bytes, BALANCE_TYPE_NEO),
                    state.neo_balance.to_bytes(32, "little", signed=False),
                )

            for storage_key, storage_value in state.storage.items():
                key = bytes([PREFIX_ACCOUNT_STORAGE]) + addr_bytes + _hex_to_bytes(storage_key)
                self.snapshot.put(key, _hex_to_bytes(storage_value))

    def _build_script_container(self, tx: TransactionInput) -> Any:
        signers = []
        for signer in tx.signers:
            rules = _parse_witness_rules(signer.rules)
            signers.append(
                SimpleNamespace(
                    account=_hex_to_bytes(signer.account),
                    scopes=signer.scopes,
                    allowed_contracts=[_hex_to_bytes(v) for v in signer.allowed_contracts],
                    allowed_groups=[_hex_to_bytes(v) for v in signer.allowed_groups],
                    rules=rules,
                )
            )

        return SimpleNamespace(
            signers=signers,
            nonce=tx.nonce,
            valid_until_block=tx.valid_until_block,
            timestamp=self.env.timestamp,
            network=self.env.network,
        )

    def _validate_tx(self, tx: TransactionInput) -> None:
        from neo.ledger.witness_scope import WitnessScope

        if tx.parse_error is not None:
            raise ValueError(tx.parse_error)

        if not isinstance(tx.script, str):
            raise ValueError("Transaction script must be a hex string")
        try:
            script = _hex_to_bytes(tx.script)
        except ValueError as exc:
            raise ValueError(f"Invalid tx script hex: {tx.script}") from exc
        if len(script) == 0:
            raise ValueError("Transaction script cannot be empty")
        if len(script) > _MAX_TRANSACTION_SIZE:
            raise ValueError(
                f"Transaction script exceeds max transaction size: {len(script)} > {_MAX_TRANSACTION_SIZE}"
            )

        system_fee = _parse_integer(tx.system_fee, "System fee")
        network_fee = _parse_integer(tx.network_fee, "Network fee")
        valid_until_block = _parse_integer(tx.valid_until_block, "Transaction validUntilBlock")
        nonce = _parse_integer(tx.nonce, "Transaction nonce")

        tx.system_fee = system_fee
        tx.network_fee = network_fee
        tx.valid_until_block = valid_until_block
        tx.nonce = nonce

        if system_fee < 0:
            raise ValueError("System fee cannot be negative")
        if network_fee < 0:
            raise ValueError("Network fee cannot be negative")
        if system_fee > 0x7FFF_FFFF_FFFF_FFFF:
            raise ValueError("System fee exceeds int64 range")
        if network_fee > 0x7FFF_FFFF_FFFF_FFFF:
            raise ValueError("Network fee exceeds int64 range")

        if valid_until_block < 0:
            raise ValueError("Transaction validUntilBlock cannot be negative")
        if valid_until_block > _MAX_UINT32:
            raise ValueError("Transaction validUntilBlock exceeds uint32 range")
        if valid_until_block > 0 and valid_until_block <= self.env.current_block_number:
            raise ValueError("Transaction validUntilBlock has expired for current block context")
        if valid_until_block > (self.env.current_block_number + self.protocol_settings.max_valid_until_block_increment):
            raise ValueError("Transaction validUntilBlock exceeds max valid-until increment for current block context")

        if nonce < 0:
            raise ValueError("Transaction nonce cannot be negative")
        if nonce > _MAX_UINT32:
            raise ValueError("Transaction nonce exceeds uint32 range")

        if len(tx.signers) > _MAX_TX_SIGNERS:
            raise ValueError(f"Transaction must contain at most {_MAX_TX_SIGNERS} signers")

        # Unsigned tx size:
        # version(1) + nonce(4) + systemFee(8) + networkFee(8) + validUntilBlock(4)
        estimated_tx_size = 25 + _var_int_size(len(tx.signers))

        seen_accounts: set[bytes] = set()
        for signer in tx.signers:
            if not isinstance(signer.account, str):
                raise ValueError("Signer account must be a hex string")
            try:
                account = _hex_to_bytes(signer.account)
            except ValueError as exc:
                raise ValueError("Invalid signer account hex") from exc
            if len(account) != ACCOUNT_LENGTH:
                raise ValueError("Invalid signer account length; expected 20-byte UInt160")
            if account in seen_accounts:
                raise ValueError("Duplicate signer account")
            seen_accounts.add(account)

            scope = _parse_integer(signer.scopes, "WitnessScope")
            if scope < 0 or scope > 0xFF:
                raise ValueError("Invalid WitnessScope value")
            signer.scopes = scope

            valid_scope_mask = int(
                WitnessScope.CALLED_BY_ENTRY
                | WitnessScope.CUSTOM_CONTRACTS
                | WitnessScope.CUSTOM_GROUPS
                | WitnessScope.WITNESS_RULES
                | WitnessScope.GLOBAL
            )
            if scope & ~valid_scope_mask:
                raise ValueError("Invalid WitnessScope flags")

            global_scope = int(WitnessScope.GLOBAL)
            if (scope & global_scope) and scope != global_scope:
                raise ValueError("Global WitnessScope cannot be combined with other scopes")

            custom_contracts_scope = int(WitnessScope.CUSTOM_CONTRACTS)
            custom_groups_scope = int(WitnessScope.CUSTOM_GROUPS)
            witness_rules_scope = int(WitnessScope.WITNESS_RULES)

            signer_size = 20 + 1

            if signer.allowed_contracts is None:
                signer.allowed_contracts = []
            if not isinstance(signer.allowed_contracts, list):
                raise ValueError("Signer allowedContracts must be an array")
            if len(signer.allowed_contracts) > _MAX_SIGNER_ALLOWED_CONTRACTS:
                raise ValueError(
                    f"Signer allowedContracts must contain at most {_MAX_SIGNER_ALLOWED_CONTRACTS} entries"
                )
            if signer.allowed_contracts and not (scope & custom_contracts_scope):
                raise ValueError("Signer allowedContracts require CUSTOM_CONTRACTS scope")
            if scope & custom_contracts_scope:
                signer_size += _var_int_size(len(signer.allowed_contracts))
                signer_size += 20 * len(signer.allowed_contracts)

            if signer.allowed_groups is None:
                signer.allowed_groups = []
            if not isinstance(signer.allowed_groups, list):
                raise ValueError("Signer allowedGroups must be an array")
            if len(signer.allowed_groups) > _MAX_SIGNER_ALLOWED_GROUPS:
                raise ValueError(f"Signer allowedGroups must contain at most {_MAX_SIGNER_ALLOWED_GROUPS} entries")
            if signer.allowed_groups and not (scope & custom_groups_scope):
                raise ValueError("Signer allowedGroups require CUSTOM_GROUPS scope")
            if scope & custom_groups_scope:
                signer_size += _var_int_size(len(signer.allowed_groups))
                signer_size += 33 * len(signer.allowed_groups)

            for allowed in signer.allowed_contracts:
                try:
                    contract_hash = _hex_to_bytes(allowed)
                except Exception as exc:
                    raise ValueError("Invalid signer allowedContracts entry; expected 20-byte UInt160") from exc
                if len(contract_hash) != ACCOUNT_LENGTH:
                    raise ValueError("Invalid signer allowedContracts entry; expected 20-byte UInt160")
            for group in signer.allowed_groups:
                try:
                    group_bytes = _hex_to_bytes(group)
                except Exception as exc:
                    raise ValueError("Invalid signer allowedGroups entry; expected 33-byte ECPoint") from exc
                if len(group_bytes) != 33:
                    raise ValueError("Invalid signer allowedGroups entry; expected 33-byte ECPoint")
                if group_bytes[0] not in (0x02, 0x03):
                    raise ValueError("Invalid signer allowedGroups entry; expected compressed ECPoint format")

            if signer.rules is None:
                signer.rules = []
            parsed_rules: list[Any] = []
            try:
                if scope & witness_rules_scope:
                    parsed_rules = _parse_witness_rules(signer.rules)
                elif signer.rules:
                    raise ValueError("Signer witness rules require WITNESS_RULES scope")
            except ValueError as exc:
                raise ValueError(f"Invalid witness rule: {exc}") from exc

            if scope & witness_rules_scope:
                signer_size += _var_int_size(len(parsed_rules))
                signer_size += sum(_estimate_witness_rule_size(rule) for rule in parsed_rules)

            estimated_tx_size += signer_size

        estimated_tx_size += _var_int_size(0)  # attributes count
        estimated_tx_size += _var_int_size(len(script)) + len(script)
        if estimated_tx_size > _MAX_TRANSACTION_SIZE:
            raise ValueError(
                f"Transaction size exceeds max transaction size: {estimated_tx_size} > {_MAX_TRANSACTION_SIZE}"
            )

    def _serialize_stack_item(self, item: Any) -> dict[str, Any]:
        from neo.vm.types import StackItemType

        item_type = item.type

        if item_type == StackItemType.ANY:
            return {"type": "Any", "value": None}
        if item_type == StackItemType.BOOLEAN:
            return {"type": "Boolean", "value": item.get_boolean()}
        if item_type == StackItemType.INTEGER:
            return {"type": "Integer", "value": str(item.get_integer())}
        if item_type == StackItemType.BYTESTRING:
            return {"type": "ByteString", "value": item.get_bytes_unsafe().hex()}
        if item_type == StackItemType.BUFFER:
            return {"type": "Buffer", "value": item.get_bytes_unsafe().hex()}
        if item_type == StackItemType.ARRAY:
            return {
                "type": "Array",
                "value": [self._serialize_stack_item(sub) for sub in item],
            }
        if item_type == StackItemType.STRUCT:
            return {
                "type": "Struct",
                "value": [self._serialize_stack_item(sub) for sub in item],
            }
        if item_type == StackItemType.MAP:
            pairs = []
            for key, value in item.items():
                pairs.append(
                    {
                        "key": self._serialize_stack_item(key),
                        "value": self._serialize_stack_item(value),
                    }
                )
            return {"type": "Map", "value": pairs}

        type_name = item_type.name if hasattr(item_type, "name") else str(item_type)
        return {"type": type_name, "value": None}

    def _serialize_notification_state(self, state: Any) -> dict[str, Any]:
        if hasattr(state, "type"):
            return self._serialize_stack_item(state)
        if state is None:
            return {"type": "Any", "value": None}
        if isinstance(state, bool):
            return {"type": "Boolean", "value": state}
        if isinstance(state, int):
            return {"type": "Integer", "value": str(state)}
        if isinstance(state, (bytes, bytearray)):
            return {"type": "ByteString", "value": bytes(state).hex()}
        if isinstance(state, str):
            return {"type": "ByteString", "value": state.encode("utf-8").hex()}
        if isinstance(state, (list, tuple)):
            return {
                "type": "Array",
                "value": [self._serialize_notification_state(item) for item in state],
            }
        if isinstance(state, dict):
            pairs = []
            for key, value in state.items():
                pairs.append(
                    {
                        "key": self._serialize_notification_state(key),
                        "value": self._serialize_notification_state(value),
                    }
                )
            return {"type": "Map", "value": pairs}
        return {"type": type(state).__name__, "value": str(state)}

    def _extract_stack(self, engine: ApplicationEngine) -> list[dict[str, Any]]:
        return [self._serialize_stack_item(engine.result_stack.peek(i)) for i in range(len(engine.result_stack))]

    def _extract_notifications(self, engine: ApplicationEngine) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for notification in engine.notifications:
            result.append(
                {
                    "contract": _bytes_to_hex(bytes(notification.script_hash)),
                    "eventName": notification.event_name,
                    "state": self._serialize_notification_state(notification.state),
                }
            )
        return result

    def _compute_tx_hash(self, tx: TransactionInput, index: int) -> str:
        try:
            script = _hex_to_bytes(tx.script)
        except ValueError:
            script = tx.script.encode("utf-8", errors="replace")
        material = b"".join(
            (
                script,
                _to_uint32_hash_bytes(tx.nonce),
                _to_int64_hash_bytes(tx.system_fee),
                _to_int64_hash_bytes(tx.network_fee),
                _to_uint32_hash_bytes(index),
            )
        )
        return _bytes_to_hex(hash256(material))

    def _execute_tx(self, tx: TransactionInput, index: int) -> Receipt:
        """Execute a single transaction."""
        tx_hash = self._compute_tx_hash(tx, index)

        try:
            self._validate_tx(tx)
            script = _hex_to_bytes(tx.script)

            engine = ApplicationEngine(
                trigger=TriggerType.APPLICATION,
                gas_limit=tx.system_fee if tx.system_fee > 0 else 10_000_000_000,
                snapshot=self.snapshot,
                script_container=self._build_script_container(tx),
                network=self.env.network,
                protocol_settings=self.protocol_settings,
            )
            setattr(engine, "persisting_block", getattr(self.snapshot, "persisting_block", None))
            engine.load_script(script)

            vm_state = "FAULT"
            exception: str | None = None

            try:
                state = engine.execute()
                vm_state = "HALT" if state == VMState.HALT else "FAULT"
                if vm_state == "FAULT" and engine.uncaught_exception is not None:
                    exception = _decode_uncaught_exception(engine.uncaught_exception)
            except Exception as exc:
                vm_state = "FAULT"
                exception = str(exc)

            if vm_state == "FAULT" and exception is None:
                exception = "Execution fault"

            gas_consumed = int(getattr(engine, "gas_consumed", 0))
            self.total_gas_used += gas_consumed

            return Receipt(
                tx_hash=tx_hash,
                vm_state=vm_state,
                gas_consumed=gas_consumed,
                exception=exception,
                stack=self._extract_stack(engine) if vm_state == "HALT" else [],
                notifications=self._extract_notifications(engine),
            )
        except Exception as exc:
            if self.strict:
                raise
            return Receipt(
                tx_hash=tx_hash,
                vm_state="FAULT",
                gas_consumed=0,
                exception=str(exc),
                stack=[],
                notifications=[],
            )

    def _iter_snapshot_items(self) -> Iterable[tuple[bytes, bytes]]:
        store = getattr(self.snapshot, "_store", None)
        if isinstance(store, dict):
            for key in sorted(store):
                value = store[key]
                if isinstance(value, bytes):
                    yield key, value
            return

        for key, value in self.snapshot.find(b""):
            if isinstance(key, bytes) and isinstance(value, bytes):
                yield key, value

    def _extract_post_alloc(self) -> dict[str, dict[str, Any]]:
        """Extract post-state allocation from snapshot."""
        result: dict[str, dict[str, Any]] = {}

        # Preserve non-balance metadata from input accounts.
        for addr, state in self.pre_alloc.items():
            entry: dict[str, Any] = {}
            if state.nef is not None:
                entry["nef"] = state.nef
            if state.manifest is not None:
                entry["manifest"] = state.manifest
            result[addr] = entry

        for key, value in self._iter_snapshot_items():
            if len(key) == 2 + ACCOUNT_LENGTH and key[0] == PREFIX_BALANCE:
                addr = key[2 : 2 + ACCOUNT_LENGTH].hex()
                entry = result.setdefault(addr, {})
                amount = int.from_bytes(value, "little", signed=False)
                if key[1] == BALANCE_TYPE_GAS:
                    if amount > 0:
                        entry["gasBalance"] = amount
                    else:
                        entry.pop("gasBalance", None)
                elif key[1] == BALANCE_TYPE_NEO:
                    if amount > 0:
                        entry["neoBalance"] = amount
                    else:
                        entry.pop("neoBalance", None)
                continue

            if key.startswith(bytes([PREFIX_ACCOUNT_STORAGE])) and len(key) > 1 + ACCOUNT_LENGTH:
                addr = key[1 : 1 + ACCOUNT_LENGTH].hex()
                user_key = key[1 + ACCOUNT_LENGTH :].hex()
                entry = result.setdefault(addr, {})
                storage = entry.setdefault("storage", {})
                storage[user_key] = value.hex()

        for entry in result.values():
            if entry.get("storage") == {}:
                entry.pop("storage", None)

        return result

    def _compute_state_root(self) -> str:
        """Compute state root hash."""
        data = b"".join(key + value for key, value in self._iter_snapshot_items())
        if not data:
            data = b"\x00"
        return _bytes_to_hex(hash256(data))

    def _validate_block_envelope(self) -> str | None:
        max_txs = int(self.protocol_settings.max_transactions_per_block)
        if len(self.txs) > max_txs:
            return f"Transaction list exceeds max transactions per block: {len(self.txs)} > {max_txs}"
        return None

    def run(self) -> T8NOutput:
        """Execute all transactions and return result."""
        self._init_state()

        block_error = self._validate_block_envelope()
        if block_error is not None:
            if self.strict:
                raise ValueError(block_error)
            # Preserve no-op state semantics for overflowed blocks.
            self.snapshot.commit()
            self.receipts = [
                Receipt(
                    tx_hash=self._compute_tx_hash(tx, index),
                    vm_state="FAULT",
                    gas_consumed=0,
                    exception=block_error,
                    stack=[],
                    notifications=[],
                )
                for index, tx in enumerate(self.txs)
            ]
            result = T8NResult(
                state_root=self._compute_state_root(),
                receipts=self.receipts,
                gas_used=self.total_gas_used,
            )
            return T8NOutput(result=result, alloc=self._extract_post_alloc())

        for index, tx in enumerate(self.txs):
            self.receipts.append(self._execute_tx(tx, index))

        self.snapshot.commit()

        result = T8NResult(
            state_root=self._compute_state_root(),
            receipts=self.receipts,
            gas_used=self.total_gas_used,
        )
        return T8NOutput(result=result, alloc=self._extract_post_alloc())
