"""
Additional Runtime Syscalls.

Reference: Neo.SmartContract.ApplicationEngine.Runtime.cs
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.smartcontract.application_engine import ApplicationEngine


def runtime_load_script(engine: "ApplicationEngine") -> None:
    """System.Runtime.LoadScript
    
    Load and execute a script dynamically.
    
    Stack: [call_flags, script] -> []
    """
    from neo.smartcontract.call_flags import CallFlags
    
    stack = engine.current_context.evaluation_stack
    call_flags_int = stack.pop().get_integer()
    script = stack.pop().get_span()
    
    call_flags = CallFlags(call_flags_int)
    
    # Validate call flags
    if (call_flags & ~CallFlags.ALL) != 0:
        raise ValueError("Invalid call flags")
    
    # Load the script
    engine.load_script(script, call_flags=call_flags)


def runtime_get_current_signers(engine: "ApplicationEngine") -> None:
    """System.Runtime.CurrentSigners
    
    Get the signers of the current transaction.
    
    Stack: [] -> [signers_array]
    """
    from neo.vm.types import Array, InteropInterface, NULL
    
    stack = engine.current_context.evaluation_stack
    
    container = getattr(engine, 'script_container', None)
    if container is None or not hasattr(container, 'signers'):
        stack.push(NULL)
        return
    
    signers = [InteropInterface(s) for s in container.signers]
    stack.push(Array(items=signers))
