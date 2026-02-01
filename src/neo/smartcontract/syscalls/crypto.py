"""Crypto syscalls.

Reference: Neo.SmartContract.ApplicationEngine.Crypto.cs
"""

from __future__ import annotations
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from neo.smartcontract.application_engine import ApplicationEngine

# Price constants (in datoshi, 1 datoshi = 1e-8 GAS)
CHECK_SIG_PRICE = 1 << 15


def crypto_check_sig(engine: "ApplicationEngine") -> None:
    """System.Crypto.CheckSig
    
    Checks the signature for the current script container.
    
    Stack: [signature, pubkey] -> [bool]
    """
    from neo.vm.types import Boolean
    from neo.crypto.ecc import SECP256R1
    from neo.crypto.ecc.signature import verify_signature
    
    stack = engine.current_context.evaluation_stack
    signature = stack.pop().get_bytes()
    pubkey = stack.pop().get_bytes()
    
    # Get message to verify (script container's sign data)
    message = _get_sign_data(engine)
    
    try:
        result = verify_signature(message, signature, pubkey, SECP256R1)
    except Exception:
        result = False
    
    stack.push(Boolean(result))


def crypto_check_multisig(engine: "ApplicationEngine") -> None:
    """System.Crypto.CheckMultisig
    
    Checks multiple signatures for the current script container.
    
    Stack: [signatures_array, pubkeys_array] -> [bool]
    """
    from neo.vm.types import Boolean, Array
    from neo.crypto.ecc import SECP256R1
    from neo.crypto.ecc.signature import verify_signature
    
    stack = engine.current_context.evaluation_stack
    
    # Pop signatures and pubkeys arrays
    sigs_item = stack.pop()
    keys_item = stack.pop()
    
    # Convert to lists of bytes
    if isinstance(sigs_item, Array):
        signatures = [item.get_bytes() for item in sigs_item]
    else:
        signatures = [sigs_item.get_bytes()]
    
    if isinstance(keys_item, Array):
        pubkeys = [item.get_bytes() for item in keys_item]
    else:
        pubkeys = [keys_item.get_bytes()]
    
    n = len(pubkeys)
    m = len(signatures)
    
    # Validate counts
    if n == 0:
        stack.push(Boolean(False))
        return
    if m == 0:
        stack.push(Boolean(False))
        return
    if m > n:
        stack.push(Boolean(False))
        return
    
    # Add fee based on number of pubkeys
    engine.add_gas(CHECK_SIG_PRICE * n)
    
    # Get message to verify
    message = _get_sign_data(engine)
    
    try:
        result = _check_multisig_internal(
            message, signatures, pubkeys, SECP256R1
        )
    except Exception:
        result = False
    
    stack.push(Boolean(result))


def _check_multisig_internal(
    message: bytes,
    signatures: List[bytes],
    pubkeys: List[bytes],
    curve
) -> bool:
    """Internal multisig verification logic."""
    from neo.crypto.ecc.signature import verify_signature
    
    m = len(signatures)
    n = len(pubkeys)
    
    i = 0  # signature index
    j = 0  # pubkey index
    
    while i < m and j < n:
        if verify_signature(message, signatures[i], pubkeys[j], curve):
            i += 1
        j += 1
        # Check if remaining pubkeys can satisfy remaining signatures
        if m - i > n - j:
            return False
    
    return i == m


def _get_sign_data(engine: "ApplicationEngine") -> bytes:
    """Get the data to be signed from the script container."""
    from neo.crypto import hash256
    
    # If we have a script container with GetSignData, use it
    if hasattr(engine, 'script_container') and engine.script_container is not None:
        container = engine.script_container
        if hasattr(container, 'get_sign_data'):
            network = getattr(engine, 'network', 0)
            return container.get_sign_data(network)
        if hasattr(container, 'hash'):
            return container.hash
    
    # Fallback: hash the current script
    ctx = engine.current_context
    if ctx is not None:
        return hash256(ctx.script)
    
    return b'\x00' * 32
