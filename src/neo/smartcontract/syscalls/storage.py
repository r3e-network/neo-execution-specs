"""Storage syscalls.

Reference: Neo.SmartContract.ApplicationEngine.Storage.cs
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.smartcontract.application_engine import ApplicationEngine


# Storage price constants (in datoshi)
STORAGE_PRICE = 100000  # Per byte

# Storage size limits (Neo.SmartContract.ApplicationEngine.Storage.cs:24,29)
MAX_STORAGE_KEY_SIZE = 64       # MaxStorageKeySize
MAX_STORAGE_VALUE_SIZE = 65535  # MaxStorageValueSize (ushort.MaxValue)


def _validate_find_options(options: int) -> None:
    """Validate Storage.Find options, mirroring C# ApplicationEngine.Storage.cs:183-202.

    Raises a faulting exception on any invalid/conflicting option combination so
    that the fault occurs at the Find call site (before the iterator is pushed).
    """
    from neo.smartcontract.storage.find_options import FindOptions

    # 1. Out-of-range bits (anything outside FindOptions.All).
    if (options & ~int(FindOptions.ALL_MASK)) != 0:
        raise ValueError(f"Invalid find options: {options}")

    keys_only = bool(options & FindOptions.KEYS_ONLY)
    values_only = bool(options & FindOptions.VALUES_ONLY)
    deserialize = bool(options & FindOptions.DESERIALIZE_VALUES)
    pick0 = bool(options & FindOptions.PICK_FIELD0)
    pick1 = bool(options & FindOptions.PICK_FIELD1)
    remove_prefix = bool(options & FindOptions.REMOVE_PREFIX)

    # 2. KeysOnly cannot combine with ValuesOnly/DeserializeValues/PickField0/PickField1.
    if keys_only and (values_only or deserialize or pick0 or pick1):
        raise ValueError(
            "KeysOnly cannot be used with ValuesOnly, DeserializeValues, "
            "PickField0, or PickField1"
        )

    # 3. ValuesOnly cannot combine with KeysOnly or RemovePrefix.
    if values_only and (keys_only or remove_prefix):
        raise ValueError("ValuesOnly cannot be used with KeysOnly or RemovePrefix")

    # 4. PickField0 and PickField1 cannot both be set.
    if pick0 and pick1:
        raise ValueError("PickField0 and PickField1 cannot be used together")

    # 5. PickField0/PickField1 require DeserializeValues.
    if (pick0 or pick1) and not deserialize:
        raise ValueError("PickField0 or PickField1 requires DeserializeValues")


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

    # Validate sizes, then read-only — order mirrors C# Put (key -> value -> read-only).
    if len(key) > MAX_STORAGE_KEY_SIZE:
        raise ValueError(
            f"Key length {len(key)} exceeds maximum allowed size of "
            f"{MAX_STORAGE_KEY_SIZE} bytes."
        )
    if len(value) > MAX_STORAGE_VALUE_SIZE:
        raise ValueError(
            f"Value length {len(value)} exceeds maximum allowed size of "
            f"{MAX_STORAGE_VALUE_SIZE} bytes."
        )
    if ctx.is_read_only:
        raise ValueError("StorageContext is read-only")

    # Build full storage key
    storage_key = _build_storage_key(ctx, key)

    # Compute the differential newDataSize exactly like C# ApplicationEngine.Storage.cs Put.
    old_value = None
    if hasattr(engine, 'snapshot') and engine.snapshot is not None:
        old_value = engine.snapshot.storage_get(storage_key)

    if old_value is None:
        new_data_size = len(key) + len(value)
    else:
        if len(value) == 0:
            new_data_size = 0
        elif len(value) <= len(old_value):
            new_data_size = (len(value) - 1) // 4 + 1
        elif len(old_value) == 0:
            new_data_size = len(value)
        else:
            new_data_size = (len(old_value) - 1) // 4 + 1 + len(value) - len(old_value)

    # Charge before writing the new value (matching C# order). add_gas is in plain
    # GAS-datoshi here, so the C# FeeFactor pico multiplier is not applied (it cancels).
    engine.add_gas(new_data_size * STORAGE_PRICE)

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
    options = int(stack.pop().get_integer())
    prefix = stack.pop().get_bytes()
    ctx_item = stack.pop()
    
    ctx = ctx_item.value
    if not isinstance(ctx, StorageContext):
        raise ValueError("Invalid storage context")

    # Validate options BEFORE constructing the iterator (C# ApplicationEngine.Storage.cs:183-202).
    _validate_find_options(options)

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
