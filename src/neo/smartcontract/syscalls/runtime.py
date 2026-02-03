"""Runtime syscalls.

Reference: Neo.SmartContract.ApplicationEngine.Runtime.cs
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from neo.smartcontract.application_engine import ApplicationEngine


def runtime_get_trigger(engine: "ApplicationEngine") -> None:
    """System.Runtime.GetTrigger
    
    Get the trigger type of the current execution.
    
    Stack: [] -> [trigger_type]
    """
    from neo.vm.types import Integer
    stack = engine.current_context.evaluation_stack
    stack.push(Integer(int(engine.trigger)))


def runtime_get_time(engine: "ApplicationEngine") -> None:
    """System.Runtime.GetTime
    
    Get the timestamp of the current block.
    
    Stack: [] -> [timestamp]
    """
    from neo.vm.types import Integer
    stack = engine.current_context.evaluation_stack
    
    # Get block time from persistent block if available
    timestamp = 0
    if hasattr(engine, 'snapshot') and engine.snapshot is not None:
        if hasattr(engine.snapshot, 'persisting_block'):
            block = engine.snapshot.persisting_block
            if block is not None:
                timestamp = block.timestamp
    
    stack.push(Integer(timestamp))


def runtime_get_script_container(engine: "ApplicationEngine") -> None:
    """System.Runtime.GetScriptContainer
    
    Get the script container (usually a transaction).
    
    Stack: [] -> [container]
    """
    from neo.vm.types import InteropInterface
    stack = engine.current_context.evaluation_stack
    
    container = getattr(engine, 'script_container', None)
    if container is None:
        raise ValueError("No script container")
    
    stack.push(InteropInterface(container))


def runtime_get_executing_script_hash(engine: "ApplicationEngine") -> None:
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


def runtime_get_calling_script_hash(engine: "ApplicationEngine") -> None:
    """System.Runtime.GetCallingScriptHash
    
    Get the script hash of the calling contract.
    
    Stack: [] -> [script_hash]
    """
    from neo.vm.types import ByteString
    from neo.vm.types import NULL
    stack = engine.current_context.evaluation_stack
    
    calling_hash = engine.calling_script_hash
    if calling_hash is None:
        stack.push(NULL)
    else:
        stack.push(ByteString(bytes(calling_hash)))


def runtime_get_entry_script_hash(engine: "ApplicationEngine") -> None:
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


def runtime_platform(engine: "ApplicationEngine") -> None:
    """System.Runtime.Platform
    
    Get the platform name.
    
    Stack: [] -> [platform_name]
    """
    from neo.vm.types import ByteString
    stack = engine.current_context.evaluation_stack
    stack.push(ByteString(b"NEO"))


def runtime_get_network(engine: "ApplicationEngine") -> None:
    """System.Runtime.GetNetwork
    
    Get the network magic number.
    
    Stack: [] -> [network]
    """
    from neo.vm.types import Integer
    stack = engine.current_context.evaluation_stack
    
    network = getattr(engine, 'network', 860833102)  # MainNet default
    stack.push(Integer(network))


def runtime_get_random(engine: "ApplicationEngine") -> None:
    """System.Runtime.GetRandom
    
    Get a random number based on block nonce.
    
    Stack: [] -> [random_number]
    """
    from neo.vm.types import Integer
    from neo.crypto import hash256
    stack = engine.current_context.evaluation_stack
    
    # Generate deterministic random based on block and invocation
    seed_data = b""
    if hasattr(engine, 'snapshot') and engine.snapshot is not None:
        if hasattr(engine.snapshot, 'persisting_block'):
            block = engine.snapshot.persisting_block
            if block is not None and hasattr(block, 'nonce'):
                seed_data += block.nonce.to_bytes(8, 'little')
    
    # Add invocation counter for uniqueness
    counter = getattr(engine, '_random_counter', 0)
    engine._random_counter = counter + 1
    seed_data += counter.to_bytes(8, 'little')
    
    # Hash to get random value
    random_hash = hash256(seed_data)
    random_value = int.from_bytes(random_hash, 'little')
    
    stack.push(Integer(random_value))


def runtime_get_address_version(engine: "ApplicationEngine") -> None:
    """System.Runtime.GetAddressVersion
    
    Get the address version byte.
    
    Stack: [] -> [version]
    """
    from neo.vm.types import Integer
    stack = engine.current_context.evaluation_stack
    
    # Neo N3 MainNet address version
    version = getattr(engine, 'address_version', 53)
    stack.push(Integer(version))


def runtime_log(engine: "ApplicationEngine") -> None:
    """System.Runtime.Log
    
    Emit a log message.
    
    Stack: [message] -> []
    """
    stack = engine.current_context.evaluation_stack
    message = stack.pop()
    
    # Get message as string
    msg_bytes = message.get_bytes()
    if len(msg_bytes) > 1024:
        raise ValueError("Log message too long")
    
    msg_str = msg_bytes.decode('utf-8', errors='replace')
    
    # Add to engine's log list
    if not hasattr(engine, '_logs'):
        engine._logs = []
    
    script_hash = engine.current_script_hash
    engine._logs.append({
        'script_hash': script_hash,
        'message': msg_str
    })


def runtime_notify(engine: "ApplicationEngine") -> None:
    """System.Runtime.Notify
    
    Emit a notification event.
    
    Stack: [state, event_name] -> []
    """
    from neo.vm.types import Array
    stack = engine.current_context.evaluation_stack
    
    state = stack.pop()
    event_name_item = stack.pop()
    
    event_name = event_name_item.get_bytes().decode('utf-8')
    if len(event_name) > 32:
        raise ValueError("Event name too long")
    
    # Convert state to array if needed
    if not isinstance(state, Array):
        state = Array([state])
    
    # Add to notifications
    if not hasattr(engine, '_notifications'):
        engine._notifications = []
    
    script_hash = engine.current_script_hash
    engine._notifications.append({
        'script_hash': script_hash,
        'event_name': event_name,
        'state': state
    })


def runtime_get_notifications(engine: "ApplicationEngine") -> None:
    """System.Runtime.GetNotifications
    
    Get notifications emitted by a contract.
    
    Stack: [script_hash] -> [notifications_array]
    """
    from neo.vm.types import Array, ByteString, Struct
    from neo.types import UInt160
    stack = engine.current_context.evaluation_stack
    
    hash_item = stack.pop()
    hash_bytes = hash_item.get_bytes()
    
    filter_hash = None
    if len(hash_bytes) == 20:
        filter_hash = UInt160(hash_bytes)
    
    notifications = getattr(engine, '_notifications', [])
    result = []
    
    for notif in notifications:
        if filter_hash is None or notif['script_hash'] == filter_hash:
            # Create notification struct: [script_hash, event_name, state]
            notif_struct = Struct([
                ByteString(bytes(notif['script_hash'])),
                ByteString(notif['event_name'].encode('utf-8')),
                notif['state']
            ])
            result.append(notif_struct)
    
    stack.push(Array(result))


def runtime_gas_left(engine: "ApplicationEngine") -> None:
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


def runtime_burn_gas(engine: "ApplicationEngine") -> None:
    """System.Runtime.BurnGas
    
    Burn a specified amount of GAS.
    
    Stack: [amount] -> []
    """
    stack = engine.current_context.evaluation_stack
    amount = stack.pop().get_integer()
    
    if amount < 0:
        raise ValueError("Cannot burn negative GAS")
    
    engine.add_gas(amount)


def runtime_get_invocation_counter(engine: "ApplicationEngine") -> None:
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


def runtime_check_witness(engine: "ApplicationEngine") -> None:
    """System.Runtime.CheckWitness
    
    Check if the specified account has witnessed the transaction.
    
    Stack: [hash_or_pubkey] -> [bool]
    """
    from neo.vm.types import Boolean
    from neo.types import UInt160
    from neo.crypto import hash160
    stack = engine.current_context.evaluation_stack
    
    hash_or_pubkey = stack.pop().get_bytes()
    
    # Convert pubkey to script hash if needed
    if len(hash_or_pubkey) == 33 or len(hash_or_pubkey) == 65:
        # It's a public key, convert to script hash
        from neo.smartcontract.syscalls.contract import _create_signature_redeem_script
        script = _create_signature_redeem_script(hash_or_pubkey)
        account_hash = UInt160(hash160(script))
    elif len(hash_or_pubkey) == 20:
        account_hash = UInt160(hash_or_pubkey)
    else:
        stack.push(Boolean(False))
        return
    
    # Check if account is in witnesses
    result = _check_witness_internal(engine, account_hash)
    stack.push(Boolean(result))


def _check_witness_internal(engine: "ApplicationEngine", account_hash) -> bool:
    """Internal witness checking logic."""
    # Check if it's the calling contract
    calling_hash = engine.calling_script_hash
    if calling_hash is not None and calling_hash == account_hash:
        return True
    
    # Check script container signers
    container = getattr(engine, 'script_container', None)
    if container is not None and hasattr(container, 'signers'):
        for signer in container.signers:
            if signer.account == account_hash:
                # Check witness scope
                if _check_witness_scope(engine, signer):
                    return True
    
    return False


def _check_witness_scope(engine, signer) -> bool:
    """Check if witness scope allows current call."""
    from neo.network.payloads.signer import WitnessScope
    
    scope = signer.scope
    
    if scope & WitnessScope.GLOBAL:
        return True
    
    if scope & WitnessScope.CALLED_BY_ENTRY:
        entry_hash = engine.entry_script_hash
        current_hash = engine.current_script_hash
        if entry_hash == current_hash:
            return True
    
    if scope & WitnessScope.CUSTOM_CONTRACTS:
        current_hash = engine.current_script_hash
        if current_hash in signer.allowed_contracts:
            return True
    
    if scope & WitnessScope.CUSTOM_GROUPS:
        # Check if current contract is in allowed groups
        pass
    
    return False
