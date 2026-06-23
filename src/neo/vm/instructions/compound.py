"""Compound type instructions for NeoVM.

This module implements all compound type opcodes (0xBE-0xD4):
- PACKMAP, PACKSTRUCT, PACK, UNPACK: Pack/unpack collections
- NEWARRAY0, NEWARRAY, NEWARRAY_T: Create arrays
- NEWSTRUCT0, NEWSTRUCT: Create structs
- NEWMAP: Create map
- SIZE, HASKEY, KEYS, VALUES: Collection info
- PICKITEM, APPEND, SETITEM: Item access
- REVERSEITEMS, REMOVE, CLEARITEMS, POPITEM: Modify collections
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from neo.exceptions import CatchableException, InvalidOperationException
from neo.vm.types import (
    Integer, Boolean, ByteString, Array, Struct, Map, Buffer,
    StackItemType, NULL
)


# PrimitiveType-equivalent stack items (C# PrimitiveType: Integer, ByteString,
# Boolean). Used to mirror C#'s `engine.Pop<PrimitiveType>()` key/operand
# checks, which fault UNCATCHABLY (InvalidCastException -> OnFault).
_PRIMITIVE_TYPES = (Integer, ByteString, Boolean)


def _require_primitive_key(key):
    """Mirror C# `Pop<PrimitiveType>()` — fault uncatchably on a non-primitive
    key (InvalidCastException routed through OnFault in C#)."""
    if not isinstance(key, _PRIMITIVE_TYPES):
        raise InvalidOperationException(
            f"Key must be a primitive type, got {type(key).__name__}"
        )


def _primitive_span(x) -> bytes:
    """Return the C# GetSpan() bytes for a PrimitiveType operand.

    - ByteString: raw bytes.
    - Integer: minimal two's-complement little-endian bytes (empty for zero),
      matching C# Integer.Memory (BigInteger.ToByteArray()).
    - Boolean: single byte 0x01/0x00, matching C# Boolean.GetSpan().
    """
    if isinstance(x, ByteString):
        return x.get_span()
    if isinstance(x, Integer):
        v = int(x.value)
        if v == 0:
            return b""
        return x.value.to_bytes_le()
    if isinstance(x, Boolean):
        return b"\x01" if x.get_boolean() else b"\x00"
    raise InvalidOperationException(f"Not a primitive type: {type(x).__name__}")

if TYPE_CHECKING:
    from neo.vm.execution_engine import ExecutionEngine, Instruction


def packmap(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Pack key-value pairs into a map.
    
    Keys must be PrimitiveType (Integer, ByteString, or Boolean).
    """
    from neo.vm.types import ByteString, Boolean
    
    size = int(engine.pop().get_integer())
    if size < 0 or size * 2 > len(engine.current_context.evaluation_stack):
        raise InvalidOperationException(f"Invalid map size: {size}")
    result = Map(engine.reference_counter)
    for _ in range(size):
        # C# pops key first (top of stack), then value below it.
        key = engine.pop()
        value = engine.pop()
        if not isinstance(key, (Integer, ByteString, Boolean)):
            raise InvalidOperationException(f"Map key must be PrimitiveType, got {type(key).__name__}")
        result[key] = value
    engine.push(result)


def packstruct(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Pack items into a struct."""
    size = int(engine.pop().get_integer())
    if size < 0 or size > len(engine.current_context.evaluation_stack):
        raise InvalidOperationException(f"Invalid struct size: {size}")
    result = Struct(engine.reference_counter)
    for _ in range(size):
        result.add(engine.pop())
    engine.push(result)


def pack(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Pack items into an array."""
    size = int(engine.pop().get_integer())
    if size < 0 or size > len(engine.current_context.evaluation_stack):
        raise InvalidOperationException(f"Invalid array size: {size}")
    result = Array(engine.reference_counter)
    for _ in range(size):
        result.add(engine.pop())
    engine.push(result)


def unpack(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Unpack collection onto stack."""
    compound = engine.pop()
    if isinstance(compound, Map):
        for key, value in reversed(list(compound.items())):
            engine.push(value)
            engine.push(key)
    elif isinstance(compound, Array):
        for i in range(len(compound) - 1, -1, -1):
            engine.push(compound[i])
    else:
        raise InvalidOperationException(f"Invalid type for UNPACK: {compound.type}")
    engine.push(Integer(len(compound)))


def newarray0(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Create empty array."""
    engine.push(Array(engine.reference_counter))


def newarray(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Create array with n null elements."""
    n = int(engine.pop().get_integer())
    if n < 0 or n > engine.limits.max_stack_size:
        raise InvalidOperationException(f"Invalid array size: {n}")
    result = Array(engine.reference_counter)
    for _ in range(n):
        result.add(NULL)
    engine.push(result)


def newarray_t(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Create array with n elements of specified type.
    
    The type is specified in the instruction operand. Elements are initialized
    to the default value for that type:
    - Boolean: False
    - Integer: 0
    - ByteString: empty
    - Others: Null
    """
    from neo.vm.types import ByteString
    
    n = int(engine.pop().get_integer())
    if n < 0 or n > engine.limits.max_stack_size:
        raise InvalidOperationException(f"Invalid array size: {n}")
    
    item_type = instruction.operand[0] if instruction.operand else 0
    
    # Validate type
    valid_types = {t.value for t in StackItemType}
    if item_type not in valid_types:
        raise InvalidOperationException(f"Invalid type for NEWARRAY_T: {item_type}")
    
    # Determine default value based on type
    from neo.vm.types import StackItem
    default_item: StackItem
    if item_type == StackItemType.BOOLEAN:
        default_item = Boolean(False)
    elif item_type == StackItemType.INTEGER:
        default_item = Integer(0)
    elif item_type == StackItemType.BYTESTRING:
        default_item = ByteString(b'')
    else:
        default_item = NULL
    
    result = Array(engine.reference_counter)
    for _ in range(n):
        result.add(default_item)
    engine.push(result)


def newstruct0(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Create empty struct."""
    engine.push(Struct(engine.reference_counter))


def newstruct(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Create struct with n null elements."""
    n = int(engine.pop().get_integer())
    if n < 0 or n > engine.limits.max_stack_size:
        raise InvalidOperationException(f"Invalid struct size: {n}")
    result = Struct(engine.reference_counter)
    for _ in range(n):
        result.add(NULL)
    engine.push(result)


def newmap(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Create empty map."""
    engine.push(Map(engine.reference_counter))


def size(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Get size of compound type or buffer."""
    x = engine.pop()
    if isinstance(x, (Array, Map)):
        engine.push(Integer(len(x)))
    elif isinstance(x, Buffer):
        engine.push(Integer(len(x)))
    elif hasattr(x, 'get_span'):
        # ByteString or similar
        engine.push(Integer(len(x.get_span())))
    else:
        raise InvalidOperationException(f"Invalid type for SIZE: {x.type}")


def haskey(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Check if compound type has key.

    Implements the C# v3.10.0 DefaultJumpTable (post-HF_Gorgon) behavior:
    Array/Buffer/ByteString operands fault (uncatchably) when the index is
    negative or >= MaxItemSize, otherwise push (index < count/size). The key
    is popped as a PrimitiveType (uncatchable on a non-primitive). The
    pre-Gorgon HasKey_Before543 override (negative-only check) lives in
    ApplicationEngine, outside the pure VM jump table.
    """
    key = engine.pop()
    _require_primitive_key(key)
    x = engine.pop()
    if isinstance(x, Array):
        idx = int(key.get_integer())
        if idx < 0 or idx >= engine.limits.max_item_size:
            raise InvalidOperationException(
                f"The index {idx} is invalid for OpCode HASKEY."
            )
        engine.push(Boolean(idx < len(x)))
    elif isinstance(x, Map):
        engine.push(Boolean(key in x))
    elif isinstance(x, Buffer):
        idx = int(key.get_integer())
        if idx < 0 or idx >= engine.limits.max_item_size:
            raise InvalidOperationException(
                f"The index {idx} is invalid for OpCode HASKEY."
            )
        engine.push(Boolean(idx < len(x)))
    elif isinstance(x, ByteString):
        idx = int(key.get_integer())
        if idx < 0 or idx >= engine.limits.max_item_size:
            raise InvalidOperationException(
                f"The index {idx} is invalid for OpCode HASKEY."
            )
        engine.push(Boolean(idx < len(x.get_span())))
    else:
        raise InvalidOperationException(f"Invalid type for HASKEY: {x.type}")


def keys(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Get keys of a map as array."""
    x = engine.pop()
    if not isinstance(x, Map):
        raise InvalidOperationException(f"Invalid type for KEYS: {x.type}")
    result = Array(engine.reference_counter)
    for key in x.keys():
        result.add(key)
    engine.push(result)


def values(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Get values of a map or array as array."""
    x = engine.pop()
    if isinstance(x, Map):
        result = Array(engine.reference_counter)
        for value in x.values():
            # C# clones top-level Struct elements (Struct.Clone), other items
            # by reference.
            result.add(value.clone() if isinstance(value, Struct) else value)
        engine.push(result)
    elif isinstance(x, Array):
        result = Array(engine.reference_counter)
        for item in x:
            result.add(item.clone() if isinstance(item, Struct) else item)
        engine.push(result)
    else:
        raise InvalidOperationException(f"Invalid type for VALUES: {x.type}")


def pickitem(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Get item from compound type by key/index."""
    key = engine.pop()
    _require_primitive_key(key)
    x = engine.pop()
    if isinstance(x, Array):
        idx = int(key.get_integer())
        if idx < 0 or idx >= len(x):
            raise CatchableException(
                f"The index of Array is out of range, {idx}/[0, {len(x)})."
            )
        engine.push(x[idx])
    elif isinstance(x, Map):
        if key not in x:
            raise CatchableException(f"Key {key} not found in Map.")
        engine.push(x[key])
    elif isinstance(x, Buffer):
        idx = int(key.get_integer())
        if idx < 0 or idx >= len(x):
            raise CatchableException(
                f"The index of Buffer is out of range, {idx}/[0, {len(x)})."
            )
        engine.push(Integer(x[idx]))
    elif isinstance(x, _PRIMITIVE_TYPES):
        # PrimitiveType (ByteString/Integer/Boolean): index into the GetSpan()
        # bytes and push the byte value, matching C#'s `case PrimitiveType`.
        span = _primitive_span(x)
        idx = int(key.get_integer())
        if idx < 0 or idx >= len(span):
            raise CatchableException(
                f"The index of PrimitiveType is out of range, {idx}/[0, {len(span)})."
            )
        engine.push(Integer(span[idx]))
    else:
        raise InvalidOperationException(f"Invalid type for PICKITEM: {x.type}")


def append(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Append item to array."""
    item = engine.pop()
    x = engine.pop()
    if not isinstance(x, Array):
        raise InvalidOperationException(f"Invalid type for APPEND: {x.type}")
    if len(x) >= engine.limits.max_stack_size:
        raise InvalidOperationException("Array size limit exceeded")
    x.add(item)


def setitem(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Set item in compound type by key/index."""
    value = engine.pop()
    if isinstance(value, Struct):
        value = value.clone()
    key = engine.pop()
    _require_primitive_key(key)
    x = engine.pop()
    if isinstance(x, Array):
        idx = int(key.get_integer())
        if idx < 0 or idx >= len(x):
            raise CatchableException(
                f"The index of Array is out of range, {idx}/[0, {len(x)})."
            )
        x[idx] = value
    elif isinstance(x, Map):
        # C# SETITEM has no Map-size check (only the global ref-counter
        # MaxStackSize bound, enforced via PostExecuteInstruction).
        x[key] = value
    elif isinstance(x, Buffer):
        idx = int(key.get_integer())
        if idx < 0 or idx >= len(x):
            raise CatchableException(
                f"The index of Buffer is out of range, {idx}/[0, {len(x)})."
            )
        # Non-primitive value and byte-range overflow are UNCATCHABLE faults
        # (C# throws InvalidOperationException, not CatchableException).
        if not isinstance(value, _PRIMITIVE_TYPES):
            raise InvalidOperationException(
                "Only primitive type values can be set in Buffer in SETITEM."
            )
        val = int(value.get_integer())
        if val < -128 or val > 255:
            raise InvalidOperationException(
                f"Overflow in SETITEM, {val} is not a byte type."
            )
        x[idx] = val & 0xFF
    else:
        raise InvalidOperationException(f"Invalid type for SETITEM: {x.type}")


def reverseitems(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Reverse items in array or buffer."""
    x = engine.pop()
    if isinstance(x, Array):
        x.reverse()
    elif isinstance(x, Buffer):
        x.reverse()
    else:
        raise InvalidOperationException(f"Invalid type for REVERSEITEMS: {x.type}")


def remove(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Remove item from compound type by key/index."""
    key = engine.pop()
    _require_primitive_key(key)
    x = engine.pop()
    if isinstance(x, Array):
        idx = int(key.get_integer())
        # C# REMOVE on Array uses InvalidOperationException (UNCATCHABLE), not
        # CatchableException, for an out-of-range index.
        if idx < 0 or idx >= len(x):
            raise InvalidOperationException(
                f"The index of Array is out of range, {idx}/[0, {len(x)})."
            )
        x.remove_at(idx)
    elif isinstance(x, Map):
        # C# Map.Remove returns null when the key is absent and the handler
        # ignores it — a missing key is a silent no-op.
        if key in x:
            del x[key]
    else:
        raise InvalidOperationException(f"Invalid type for REMOVE: {x.type}")


def clearitems(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Clear all items from compound type."""
    x = engine.pop()
    if isinstance(x, (Array, Map)):
        x.clear()
    else:
        raise InvalidOperationException(f"Invalid type for CLEARITEMS: {x.type}")


def popitem(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Pop last item from array."""
    x = engine.pop()
    if not isinstance(x, Array):
        raise InvalidOperationException(f"Invalid type for POPITEM: {x.type}")
    if len(x) == 0:
        raise InvalidOperationException("Array is empty")
    item = x[-1]
    x.remove_at(len(x) - 1)
    engine.push(item)
