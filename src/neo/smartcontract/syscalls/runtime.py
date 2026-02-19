"""Runtime syscalls.

Reference: Neo.SmartContract.ApplicationEngine.Runtime.cs
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.smartcontract.application_engine import ApplicationEngine


def runtime_get_trigger(engine: ApplicationEngine) -> None:
    """System.Runtime.GetTrigger
    
    Get the trigger type of the current execution.
    
    Stack: [] -> [trigger_type]
    """
    from neo.vm.types import Integer
    stack = engine.current_context.evaluation_stack
    stack.push(Integer(int(engine.trigger)))


def runtime_get_time(engine: ApplicationEngine) -> None:
    """System.Runtime.GetTime
    
    Get the timestamp of the current block.
    
    Stack: [] -> [timestamp]
    """
    from neo.exceptions import InvalidOperationException
    from neo.vm.types import Integer
    stack = engine.current_context.evaluation_stack

    block = None
    if hasattr(engine, 'snapshot') and engine.snapshot is not None:
        if hasattr(engine.snapshot, 'persisting_block'):
            block = engine.snapshot.persisting_block

    if block is None or not hasattr(block, "timestamp"):
        raise InvalidOperationException("GetTime can only be called with Application trigger.")

    stack.push(Integer(int(block.timestamp)))


def runtime_get_script_container(engine: ApplicationEngine) -> None:
    """System.Runtime.GetScriptContainer
    
    Get the script container (usually a transaction).
    
    Stack: [] -> [container]
    """
    from neo.exceptions import InvalidOperationException
    from neo.vm.types import InteropInterface
    stack = engine.current_context.evaluation_stack
    
    container = getattr(engine, 'script_container', None)
    if container is None:
        raise InvalidOperationException("No script container")
    
    stack.push(InteropInterface(container))


def runtime_get_executing_script_hash(engine: ApplicationEngine) -> None:
    """System.Runtime.GetExecutingScriptHash
    
    Get the script hash of the currently executing contract.
    
    Stack: [] -> [script_hash]
    """
    from neo.vm.types import ByteString
    stack = engine.current_context.evaluation_stack
    
    script_hash = engine.current_script_hash
    if script_hash is None:
        raise ValueError("No executing script")
    
    stack.push(ByteString(bytes(script_hash)))


def runtime_get_calling_script_hash(engine: ApplicationEngine) -> None:
    """System.Runtime.GetCallingScriptHash
    
    Get the script hash of the calling contract.
    
    Stack: [] -> [script_hash]
    """
    from neo.vm.types import NULL, ByteString
    stack = engine.current_context.evaluation_stack
    
    calling_hash = engine.calling_script_hash
    if calling_hash is None:
        stack.push(NULL)
    else:
        stack.push(ByteString(bytes(calling_hash)))


def runtime_get_entry_script_hash(engine: ApplicationEngine) -> None:
    """System.Runtime.GetEntryScriptHash
    
    Get the script hash of the entry point contract.
    
    Stack: [] -> [script_hash]
    """
    from neo.vm.types import ByteString
    stack = engine.current_context.evaluation_stack
    
    entry_hash = engine.entry_script_hash
    if entry_hash is None:
        raise ValueError("No entry script")
    
    stack.push(ByteString(bytes(entry_hash)))


def runtime_platform(engine: ApplicationEngine) -> None:
    """System.Runtime.Platform
    
    Get the platform name.
    
    Stack: [] -> [platform_name]
    """
    from neo.vm.types import ByteString
    stack = engine.current_context.evaluation_stack
    stack.push(ByteString(b"NEO"))


def runtime_get_network(engine: ApplicationEngine) -> None:
    """System.Runtime.GetNetwork
    
    Get the network magic number.
    
    Stack: [] -> [network]
    """
    from neo.vm.types import Integer
    stack = engine.current_context.evaluation_stack
    
    settings = getattr(engine, "protocol_settings", None)
    network = getattr(settings, "network", getattr(engine, "network", 860833102))
    stack.push(Integer(int(network)))


def runtime_get_random(engine: ApplicationEngine) -> None:
    """System.Runtime.GetRandom
    
    Get deterministic random number.
    
    Stack: [] -> [random_number]
    """
    from neo.vm.types import Integer
    from neo.smartcontract.runtime_random import next_runtime_random

    stack = engine.current_context.evaluation_stack

    random_value, price = next_runtime_random(engine)
    add_gas = getattr(engine, "add_gas", None)
    if callable(add_gas):
        add_gas(price)

    stack.push(Integer(random_value))


def runtime_get_address_version(engine: ApplicationEngine) -> None:
    """System.Runtime.GetAddressVersion
    
    Get the address version byte.
    
    Stack: [] -> [version]
    """
    from neo.vm.types import Integer
    stack = engine.current_context.evaluation_stack
    
    settings = getattr(engine, "protocol_settings", None)
    version = getattr(settings, "address_version", getattr(engine, "address_version", 53))
    stack.push(Integer(int(version)))


def runtime_log(engine: ApplicationEngine) -> None:
    """System.Runtime.Log

    Emit a log message.

    Stack: [message] -> []
    """
    from neo.exceptions import InvalidOperationException

    stack = engine.current_context.evaluation_stack
    message = stack.pop()

    msg_bytes = message.get_bytes()
    if len(msg_bytes) > 1024:
        raise InvalidOperationException("Log message exceeds 1024 bytes")

    try:
        msg_str = msg_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InvalidOperationException("Failed to convert byte array to string: Invalid UTF-8 sequence") from exc
    script_hash = engine.current_script_hash
    if script_hash is None:
        raise InvalidOperationException("No current script hash")
    engine.write_log(script_hash, msg_str)


def runtime_notify(engine: ApplicationEngine) -> None:
    """System.Runtime.Notify

    Emit a notification event.

    Stack: [state, event_name] -> []
    """
    from neo.exceptions import InvalidOperationException
    from neo.vm.types import Array

    stack = engine.current_context.evaluation_stack

    state = stack.pop()
    event_name_item = stack.pop()

    event_name_bytes = event_name_item.get_bytes()
    if len(event_name_bytes) > 32:
        raise InvalidOperationException(
            f"Event name size {len(event_name_bytes)} exceeds maximum allowed size of 32 bytes"
        )
    try:
        event_name = event_name_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InvalidOperationException("Failed to convert byte array to string: Invalid UTF-8 sequence") from exc

    if not isinstance(state, Array):
        raise InvalidOperationException("Notify state must be an Array")

    script_hash = engine.current_script_hash
    if script_hash is None:
        raise InvalidOperationException("No current script hash")
    engine.send_notification(script_hash, event_name, state)


def runtime_get_notifications(engine: ApplicationEngine) -> None:
    """System.Runtime.GetNotifications

    Get notifications emitted by a contract.

    Stack: [script_hash] -> [notifications_array]
    """
    from neo.exceptions import InvalidOperationException
    from neo.types import UInt160
    from neo.vm.types import Array, ByteString, StackItem, Struct

    stack = engine.current_context.evaluation_stack

    hash_item = stack.pop()
    filter_hash: UInt160 | None = None
    if not hash_item.is_null:
        hash_bytes = hash_item.get_bytes()
        if len(hash_bytes) != UInt160.LENGTH:
            raise ValueError(f"Invalid script hash length: {len(hash_bytes)}")
        filter_hash = UInt160(hash_bytes)

    result: list[StackItem] = []
    for notification in engine.notifications:
        if filter_hash is None or notification.script_hash == filter_hash:
            notif_struct = Struct(items=[
                ByteString(bytes(notification.script_hash)),
                ByteString(notification.event_name.encode("utf-8")),
                notification.state,
            ])
            result.append(notif_struct)

    limits = getattr(engine, "limits", None)
    max_stack_size_raw = getattr(limits, "max_stack_size", 2048)
    max_stack_size = max_stack_size_raw if isinstance(max_stack_size_raw, int) else 2048
    if len(result) > max_stack_size:
        raise InvalidOperationException(
            f"Notification count {len(result)} exceeds maximum stack size {max_stack_size}"
        )

    stack.push(Array(items=result))


def runtime_gas_left(engine: ApplicationEngine) -> None:
    """System.Runtime.GasLeft
    
    Get remaining GAS for execution.
    
    Stack: [] -> [gas_left]
    """
    from neo.vm.types import Integer
    stack = engine.current_context.evaluation_stack
    
    gas_limit = getattr(engine, 'gas_limit', 0)
    gas_consumed = getattr(engine, 'gas_consumed', 0)
    gas_left = max(0, gas_limit - gas_consumed)
    
    stack.push(Integer(gas_left))


def runtime_burn_gas(engine: ApplicationEngine) -> None:
    """System.Runtime.BurnGas
    
    Burn a specified amount of GAS.
    
    Stack: [amount] -> []
    """
    stack = engine.current_context.evaluation_stack
    amount = stack.pop().get_integer()
    
    if amount <= 0:
        raise ValueError("GAS must be positive.")
    
    engine.add_gas(amount)


def runtime_get_invocation_counter(engine: ApplicationEngine) -> None:
    """System.Runtime.GetInvocationCounter
    
    Get the invocation counter for the current contract.
    
    Stack: [] -> [counter]
    """
    from neo.vm.types import Integer
    stack = engine.current_context.evaluation_stack
    
    script_hash = engine.current_script_hash
    counters = getattr(engine, '_invocation_counters', {})
    counter = counters.get(script_hash, 1)
    
    stack.push(Integer(counter))


def runtime_check_witness(engine: ApplicationEngine) -> None:
    """System.Runtime.CheckWitness
    
    Check if the specified account has witnessed the transaction.
    
    Stack: [hash_or_pubkey] -> [bool]
    """
    from neo.crypto import hash160
    from neo.types import UInt160
    from neo.vm.types import Boolean
    stack = engine.current_context.evaluation_stack
    
    hash_or_pubkey = stack.pop().get_bytes()
    
    # Convert pubkey to script hash if needed.
    # Neo N3 accepts UInt160 (20 bytes) or a compressed ECPoint (33 bytes).
    if len(hash_or_pubkey) == 33:
        from neo.types import ECPoint
        from neo.smartcontract.syscalls.contract import _create_signature_redeem_script
        ECPoint.decode(hash_or_pubkey)
        script = _create_signature_redeem_script(hash_or_pubkey)
        account_hash = UInt160(hash160(script))
    elif len(hash_or_pubkey) == 20:
        account_hash = UInt160(hash_or_pubkey)
    else:
        raise ValueError("Invalid hashOrPubkey length")
    
    # Check if account is in witnesses
    result = _check_witness_internal(engine, account_hash)
    stack.push(Boolean(result))


def _check_witness_internal(engine: ApplicationEngine, account_hash) -> bool:
    """Internal witness checking logic."""
    from neo.exceptions import InvalidOperationException
    from neo.smartcontract.call_flags import CallFlags
    from neo.types import UInt160

    # Check if it's the calling contract
    calling_hash = engine.calling_script_hash
    if calling_hash is not None and calling_hash == account_hash:
        return True
    
    # Check script container signers
    container = getattr(engine, 'script_container', None)
    if container is not None and hasattr(container, 'signers'):
        for signer in container.signers:
            signer_account = getattr(signer, "account", None)
            if signer_account is None:
                continue

            if isinstance(signer_account, UInt160):
                account_matches = signer_account == account_hash
            elif isinstance(signer_account, (bytes, bytearray)):
                account_matches = bytes(signer_account) == bytes(account_hash)
            else:
                account_matches = False

            if account_matches and _check_witness_scope(engine, signer):
                return True

    # Non-transaction script containers may expose script hashes for verifying.
    get_hashes = getattr(container, "get_script_hashes_for_verifying", None)
    if not callable(get_hashes):
        return False

    checker = getattr(engine, "_check_call_flags", None)
    if callable(checker):
        has_read_states = bool(checker(CallFlags.READ_STATES))
    else:
        current_flags = getattr(engine, "_current_call_flags", CallFlags.ALL)
        try:
            current_flags = CallFlags(int(current_flags))
        except Exception:
            current_flags = CallFlags.ALL
        has_read_states = (current_flags & CallFlags.READ_STATES) == CallFlags.READ_STATES

    if not has_read_states:
        raise InvalidOperationException("Invalid call flags for witness verification")

    snapshot = getattr(engine, "snapshot", None)
    try:
        hashes_for_verifying = get_hashes(snapshot)
    except TypeError:
        hashes_for_verifying = get_hashes()

    account_hash_bytes = bytes(account_hash)
    for item in hashes_for_verifying or []:
        item_bytes = _coerce_hash160_to_bytes(item)
        if item_bytes is not None and item_bytes == account_hash_bytes:
            return True
    
    return False


def _check_witness_scope(engine, signer) -> bool:
    """Check if witness scope allows current call."""
    from neo.network.payloads.signer import WitnessScope

    scope = signer.scopes

    if scope & WitnessScope.GLOBAL:
        return True

    if scope & WitnessScope.CALLED_BY_ENTRY:
        calling_hash = getattr(engine, "calling_script_hash", None)
        if (engine.current_script_hash == engine.entry_script_hash
                or calling_hash == engine.entry_script_hash):
            return True

    if scope & WitnessScope.CUSTOM_CONTRACTS:
        current_hash = engine.current_script_hash
        if current_hash is not None:
            current_hash_bytes = bytes(current_hash)
            for allowed_contract in getattr(signer, "allowed_contracts", []):
                allowed_bytes = _coerce_hash160_to_bytes(allowed_contract)
                if allowed_bytes is not None and allowed_bytes == current_hash_bytes:
                    return True

    if scope & WitnessScope.CUSTOM_GROUPS:
        if hasattr(engine, '_check_witness_groups'):
            if engine._check_witness_groups(signer):
                return True

    if scope & WitnessScope.WITNESS_RULES:
        rules = getattr(signer, "rules", [])
        for rule in rules:
            action = _coerce_witness_rule_action(getattr(rule, "action", None))
            condition = getattr(rule, "condition", None)
            if condition is not None and action is not None:
                evaluator = getattr(engine, "_evaluate_witness_condition", None)
                if evaluator and evaluator(condition):
                    if action == 1:  # Allow
                        return True
                    elif action == 0:  # Deny
                        return False

    return False


def _coerce_witness_rule_action(value) -> int | None:
    """Best-effort normalization for witness rule actions."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value in (0, 1) else None
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"allow"}:
            return 1
        if lowered in {"deny"}:
            return 0
        try:
            parsed = int(lowered, 0)
        except ValueError:
            return None
        return parsed if parsed in (0, 1) else None

    enum_value = getattr(value, "value", None)
    if isinstance(enum_value, int):
        return enum_value if enum_value in (0, 1) else None
    if isinstance(enum_value, str):
        return _coerce_witness_rule_action(enum_value)
    return None


def _coerce_hash160_to_bytes(value) -> bytes | None:
    """Best-effort conversion of hash160 values to canonical 20-byte bytes."""
    from neo.types import UInt160

    if isinstance(value, UInt160):
        return bytes(value)
    if isinstance(value, (bytes, bytearray)):
        data = bytes(value)
        return data if len(data) == UInt160.LENGTH else None
    if isinstance(value, str):
        candidate = value.removeprefix("0x").removeprefix("0X")
        try:
            data = bytes.fromhex(candidate)
        except ValueError:
            return None
        return data if len(data) == UInt160.LENGTH else None

    to_bytes = getattr(value, "to_bytes", None)
    if callable(to_bytes):
        try:
            maybe = to_bytes()
        except TypeError:
            return None
        if isinstance(maybe, (bytes, bytearray)):
            data = bytes(maybe)
            return data if len(data) == UInt160.LENGTH else None
    return None
