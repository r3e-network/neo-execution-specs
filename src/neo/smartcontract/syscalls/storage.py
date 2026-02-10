"""Storage syscalls.

Reference: Neo.SmartContract.ApplicationEngine.Storage.cs
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.smartcontract.application_engine import ApplicationEngine


# Storage price constants (in datoshi)
STORAGE_PRICE = 100000  # Per byte


def storage_get_context(engine: "ApplicationEngine") -> None:
    """System.Storage.GetContext
    
    Get the storage context for the current contract.
    
    Stack: [] -> [storage_context]
    """
    from neo.vm.types import InteropInterface
    from neo.smartcontract.storage_context import StorageContext
    
    stack = engine.current_context.evaluation_stack
    script_hash = engine.current_script_hash

    if script_hash is None:
        raise ValueError("No current script")

    contract_id = engine._get_contract_id(script_hash)
    ctx = StorageContext(id=contract_id, script_hash=script_hash, is_read_only=False)
    stack.push(InteropInterface(ctx))


def storage_get_read_only_context(engine: "ApplicationEngine") -> None:
    """System.Storage.GetReadOnlyContext

    Get a read-only storage context for the current contract.

    Stack: [] -> [storage_context]
    """
    from neo.vm.types import InteropInterface
    from neo.smartcontract.storage_context import StorageContext

    stack = engine.current_context.evaluation_stack
    script_hash = engine.current_script_hash

    if script_hash is None:
        raise ValueError("No current script")

    contract_id = engine._get_contract_id(script_hash)
    ctx = StorageContext(id=contract_id, script_hash=script_hash, is_read_only=True)
    stack.push(InteropInterface(ctx))


def storage_as_read_only(engine: "ApplicationEngine") -> None:
    """System.Storage.AsReadOnly
    
    Convert a storage context to read-only.
    
    Stack: [context] -> [read_only_context]
    """
    from neo.vm.types import InteropInterface
    from neo.smartcontract.storage_context import StorageContext
    
    stack = engine.current_context.evaluation_stack
    ctx_item = stack.pop()
    
    if not hasattr(ctx_item, 'value'):
        raise ValueError("Invalid storage context")
    
    ctx = ctx_item.value
    if not isinstance(ctx, StorageContext):
        raise ValueError("Invalid storage context")
    
    read_only_ctx = StorageContext(id=ctx.id, script_hash=ctx.script_hash, is_read_only=True)
    stack.push(InteropInterface(read_only_ctx))


def storage_get(engine: "ApplicationEngine") -> None:
    """System.Storage.Get
    
    Get a value from storage.
    
    Stack: [key, context] -> [value]
    """
    from neo.vm.types import ByteString, NULL
    from neo.smartcontract.storage_context import StorageContext
    
    stack = engine.current_context.evaluation_stack
    key = stack.pop().get_bytes()
    ctx_item = stack.pop()
    
    ctx = ctx_item.value
    if not isinstance(ctx, StorageContext):
        raise ValueError("Invalid storage context")
    
    # Build full storage key
    storage_key = _build_storage_key(ctx, key)
    
    # Get from snapshot
    value = None
    if hasattr(engine, 'snapshot') and engine.snapshot is not None:
        value = engine.snapshot.storage_get(storage_key)
    
    if value is None:
        stack.push(NULL)
    else:
        stack.push(ByteString(value))


def storage_put(engine: "ApplicationEngine") -> None:
    """System.Storage.Put
    
    Put a value into storage.
    
    Stack: [value, key, context] -> []
    """
    from neo.smartcontract.storage_context import StorageContext
    
    stack = engine.current_context.evaluation_stack
    value = stack.pop().get_bytes()
    key = stack.pop().get_bytes()
    ctx_item = stack.pop()
    
    ctx = ctx_item.value
    if not isinstance(ctx, StorageContext):
        raise ValueError("Invalid storage context")
    
    if ctx.is_read_only:
        raise ValueError("Cannot write to read-only context")
    
    # Validate key length
    if len(key) > 64:
        raise ValueError("Key too long")
    
    # Build full storage key
    storage_key = _build_storage_key(ctx, key)
    
    # Calculate and charge gas
    engine.add_gas(STORAGE_PRICE * (len(key) + len(value)))
    
    # Put to snapshot
    if hasattr(engine, 'snapshot') and engine.snapshot is not None:
        engine.snapshot.storage_put(storage_key, value)


def storage_delete(engine: "ApplicationEngine") -> None:
    """System.Storage.Delete
    
    Delete a value from storage.
    
    Stack: [key, context] -> []
    """
    from neo.smartcontract.storage_context import StorageContext
    
    stack = engine.current_context.evaluation_stack
    key = stack.pop().get_bytes()
    ctx_item = stack.pop()
    
    ctx = ctx_item.value
    if not isinstance(ctx, StorageContext):
        raise ValueError("Invalid storage context")
    
    if ctx.is_read_only:
        raise ValueError("Cannot delete from read-only context")
    
    storage_key = _build_storage_key(ctx, key)
    
    if hasattr(engine, 'snapshot') and engine.snapshot is not None:
        engine.snapshot.storage_delete(storage_key)


def storage_find(engine: "ApplicationEngine") -> None:
    """System.Storage.Find
    
    Find storage entries by prefix.
    
    Stack: [find_options, prefix, context] -> [iterator]
    """
    from neo.vm.types import InteropInterface
    from neo.smartcontract.storage_context import StorageContext
    from neo.smartcontract.iterators import StorageIterator
    
    stack = engine.current_context.evaluation_stack
    options = stack.pop().get_integer()
    prefix = stack.pop().get_bytes()
    ctx_item = stack.pop()
    
    ctx = ctx_item.value
    if not isinstance(ctx, StorageContext):
        raise ValueError("Invalid storage context")
    
    storage_key = _build_storage_key(ctx, prefix)
    
    # Create iterator
    iterator = StorageIterator(engine, storage_key, options)
    stack.push(InteropInterface(iterator))


def _build_storage_key(ctx, key: bytes) -> bytes:
    """Build full storage key from storage context and user key.

    Neo N3 storage key format: contract_id (int32 LE) + user_key.
    Matches the C# reference ``StorageKey`` implementation.
    """
    contract_id_bytes = ctx.id.to_bytes(4, byteorder="little", signed=True)
    return contract_id_bytes + key
