"""Contract syscalls.

Reference: Neo.SmartContract.ApplicationEngine.Contract.cs
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.smartcontract.application_engine import ApplicationEngine


def contract_call(engine: "ApplicationEngine") -> None:
    """System.Contract.Call
    
    Call another contract dynamically.
    
    Stack: [args_array, call_flags, method, contract_hash] -> [result]
    """
    from neo.vm.types import Array, ByteString
    from neo.types import UInt160
    from neo.smartcontract.call_flags import CallFlags
    
    stack = engine.current_context.evaluation_stack
    
    # Pop arguments
    args = stack.pop()
    if not isinstance(args, Array):
        args = Array(items=[args])
    
    call_flags_int = stack.pop().get_integer()
    call_flags = CallFlags(call_flags_int)
    
    method = stack.pop()
    if isinstance(method, ByteString):
        method_name = method.value.decode('utf-8')
    else:
        method_name = str(method)
    
    contract_hash_bytes = stack.pop().get_bytes()
    contract_hash = UInt160(contract_hash_bytes)
    
    # Validate method name
    if method_name.startswith('_'):
        raise ValueError(f"Method name '{method_name}' cannot start with underscore")
    
    # Validate call flags
    if (call_flags & ~CallFlags.ALL) != 0:
        raise ValueError("Invalid call flags")
    
    # Call the contract
    _call_contract_internal(engine, contract_hash, method_name, call_flags, args)


def contract_call_native(engine: "ApplicationEngine") -> None:
    """System.Contract.CallNative
    
    Call a native contract. Internal use only.
    
    Stack: [version] -> [result]
    """
    stack = engine.current_context.evaluation_stack
    version = stack.pop().get_integer()
    
    # Get the current script hash to identify which native contract
    current_hash = engine.current_script_hash
    if current_hash is None:
        raise ValueError("No current script hash")
    
    # Look up native contract
    native_contract = _get_native_contract(engine, current_hash)
    if native_contract is None:
        raise ValueError("System.Contract.CallNative can only be used by native contracts")
    
    # Invoke the native contract
    native_contract.invoke(engine, version)


def contract_get_call_flags(engine: "ApplicationEngine") -> None:
    """System.Contract.GetCallFlags
    
    Get the CallFlags of the current context.
    
    Stack: [] -> [call_flags]
    """
    from neo.vm.types import Integer
    from neo.smartcontract.call_flags import CallFlags
    
    stack = engine.current_context.evaluation_stack
    
    # Get call flags from current context state
    ctx = engine.current_context
    if hasattr(ctx, 'call_flags'):
        flags = ctx.call_flags
    else:
        flags = CallFlags.ALL
    
    stack.push(Integer(int(flags)))


def contract_create_standard_account(engine: "ApplicationEngine") -> None:
    """System.Contract.CreateStandardAccount
    
    Calculate account scripthash for a public key.
    
    Stack: [pubkey] -> [script_hash]
    """
    from neo.vm.types import ByteString
    from neo.crypto import hash160
    
    stack = engine.current_context.evaluation_stack
    pubkey = stack.pop().get_bytes()
    
    # Add fee
    engine.add_gas(1 << 15)  # CheckSigPrice
    
    # Create signature redeem script: PUSHDATA1 <pubkey> SYSCALL CheckSig
    script = _create_signature_redeem_script(pubkey)
    script_hash = hash160(script)
    
    stack.push(ByteString(script_hash))


def contract_create_multisig_account(engine: "ApplicationEngine") -> None:
    """System.Contract.CreateMultisigAccount
    
    Calculate multisig account scripthash for public keys.
    
    Stack: [pubkeys_array, m] -> [script_hash]
    """
    from neo.vm.types import ByteString, Array
    from neo.crypto import hash160
    
    stack = engine.current_context.evaluation_stack
    
    pubkeys_item = stack.pop()
    m = stack.pop().get_integer()
    
    if isinstance(pubkeys_item, Array):
        pubkeys = [item.get_bytes() for item in pubkeys_item]
    else:
        pubkeys = [pubkeys_item.get_bytes()]
    
    n = len(pubkeys)
    
    # Add fee
    engine.add_gas((1 << 15) * n)  # CheckSigPrice * n
    
    # Create multisig redeem script
    script = _create_multisig_redeem_script(m, pubkeys)
    script_hash = hash160(script)
    
    stack.push(ByteString(script_hash))


# Helper functions

def _call_contract_internal(engine, contract_hash, method_name, call_flags, args):
    """Internal contract call implementation."""
    contract = None
    if hasattr(engine, 'snapshot') and engine.snapshot is not None:
        contract = engine.snapshot.get_contract(contract_hash)
    
    if contract is None:
        raise ValueError(f"Contract not found: {contract_hash}")
    
    method = contract.manifest.abi.get_method(method_name, len(args))
    if method is None:
        raise ValueError(f"Method '{method_name}' not found in contract")
    
    engine.load_contract(contract, method, call_flags, args)


def _get_native_contract(engine, script_hash):
    """Get native contract by script hash."""
    from neo.native import NativeContract
    return NativeContract.get_contract(script_hash)


def _create_signature_redeem_script(pubkey: bytes) -> bytes:
    """Create signature verification script for a public key."""
    from neo.vm.opcode import OpCode
    from neo.smartcontract.interop_service import get_interop_hash
    
    script = bytearray()
    
    # PUSHDATA1 <pubkey>
    script.append(OpCode.PUSHDATA1)
    script.append(len(pubkey))
    script.extend(pubkey)
    
    # SYSCALL System.Crypto.CheckSig
    script.append(OpCode.SYSCALL)
    syscall_hash = get_interop_hash("System.Crypto.CheckSig")
    script.extend(syscall_hash.to_bytes(4, 'little'))
    
    return bytes(script)


def _create_multisig_redeem_script(m: int, pubkeys: list) -> bytes:
    """Create multisig verification script."""
    from neo.vm.opcode import OpCode
    from neo.smartcontract.interop_service import get_interop_hash
    
    script = bytearray()
    
    # Push M
    script.extend(_push_integer(m))
    
    # Push each pubkey
    for pubkey in pubkeys:
        script.append(OpCode.PUSHDATA1)
        script.append(len(pubkey))
        script.extend(pubkey)
    
    # Push N
    script.extend(_push_integer(len(pubkeys)))
    
    # SYSCALL System.Crypto.CheckMultisig
    script.append(OpCode.SYSCALL)
    syscall_hash = get_interop_hash("System.Crypto.CheckMultisig")
    script.extend(syscall_hash.to_bytes(4, 'little'))
    
    return bytes(script)


def _push_integer(value: int) -> bytes:
    """Create opcode to push an integer."""
    from neo.vm.opcode import OpCode
    
    if value == -1:
        return bytes([OpCode.PUSHM1])
    elif 0 <= value <= 16:
        return bytes([OpCode.PUSH0 + value])
    else:
        data = value.to_bytes((value.bit_length() + 8) // 8, 'little', signed=True)
        if len(data) == 1:
            return bytes([OpCode.PUSHINT8]) + data
        elif len(data) <= 2:
            return bytes([OpCode.PUSHINT16]) + data.ljust(2, b'\x00')
        elif len(data) <= 4:
            return bytes([OpCode.PUSHINT32]) + data.ljust(4, b'\x00')
        else:
            return bytes([OpCode.PUSHINT64]) + data.ljust(8, b'\x00')
