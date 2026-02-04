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

from neo.vm.types import (
    Integer, Boolean, Array, Struct, Map, Buffer,
    StackItemType, NULL
)

if TYPE_CHECKING:
    from neo.vm.execution_engine import ExecutionEngine, Instruction


def packmap(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Pack key-value pairs into a map.
    
    Keys must be PrimitiveType (Integer, ByteString, or Boolean).
    """
    from neo.vm.types import ByteString, Boolean
    
    size = int(engine.pop().get_integer())
    if size < 0 or size * 2 > len(engine.current_context.evaluation_stack):
        raise Exception(f"Invalid map size: {size}")
    result = Map(engine.reference_counter)
    for _ in range(size):
        key = engine.pop()
        # C# requires key to be PrimitiveType
        if not isinstance(key, (Integer, ByteString, Boolean)):
            raise Exception(f"Map key must be PrimitiveType, got {type(key).__name__}")
        value = engine.pop()
        result[key] = value
    engine.push(result)


def packstruct(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Pack items into a struct."""
    size = int(engine.pop().get_integer())
    if size < 0 or size > len(engine.current_context.evaluation_stack):
        raise Exception(f"Invalid struct size: {size}")
    result = Struct(engine.reference_counter)
    for _ in range(size):
        result.add(engine.pop())
    engine.push(result)


def pack(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Pack items into an array."""
    size = int(engine.pop().get_integer())
    if size < 0 or size > len(engine.current_context.evaluation_stack):
        raise Exception(f"Invalid array size: {size}")
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
        raise Exception(f"Invalid type for UNPACK: {compound.type}")
    engine.push(Integer(len(compound)))


def newarray0(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Create empty array."""
    engine.push(Array(engine.reference_counter))


def newarray(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Create array with n null elements."""
    n = int(engine.pop().get_integer())
    if n < 0 or n > engine.limits.max_stack_size:
        raise Exception(f"Invalid array size: {n}")
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
        raise Exception(f"Invalid array size: {n}")
    
    item_type = instruction.operand[0] if instruction.operand else 0
    
    # Validate type
    valid_types = {t.value for t in StackItemType}
    if item_type not in valid_types:
        raise Exception(f"Invalid type for NEWARRAY_T: {item_type}")
    
    # Determine default value based on type
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
        raise Exception(f"Invalid struct size: {n}")
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
        raise Exception(f"Invalid type for SIZE: {x.type}")


def haskey(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Check if compound type has key."""
    key = engine.pop()
    x = engine.pop()
    if isinstance(x, Array):
        idx = int(key.get_integer())
        engine.push(Boolean(0 <= idx < len(x)))
    elif isinstance(x, Map):
        engine.push(Boolean(key in x))
    elif isinstance(x, Buffer):
        idx = int(key.get_integer())
        engine.push(Boolean(0 <= idx < len(x)))
    else:
        raise Exception(f"Invalid type for HASKEY: {x.type}")


def keys(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Get keys of a map as array."""
    x = engine.pop()
    if not isinstance(x, Map):
        raise Exception(f"Invalid type for KEYS: {x.type}")
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
            result.add(value)
        engine.push(result)
    elif isinstance(x, Array):
        result = Array(engine.reference_counter)
        for item in x:
            result.add(item)
        engine.push(result)
    else:
        raise Exception(f"Invalid type for VALUES: {x.type}")


def pickitem(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Get item from compound type by key/index."""
    key = engine.pop()
    x = engine.pop()
    if isinstance(x, Array):
        idx = int(key.get_integer())
        if idx < 0 or idx >= len(x):
            raise Exception(f"Index out of range: {idx}")
        engine.push(x[idx])
    elif isinstance(x, Map):
        if key not in x:
            raise Exception(f"Key not found in map")
        engine.push(x[key])
    elif isinstance(x, Buffer):
        idx = int(key.get_integer())
        if idx < 0 or idx >= len(x):
            raise Exception(f"Index out of range: {idx}")
        engine.push(Integer(x[idx]))
    else:
        raise Exception(f"Invalid type for PICKITEM: {x.type}")


def append(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Append item to array."""
    item = engine.pop()
    x = engine.pop()
    if not isinstance(x, Array):
        raise Exception(f"Invalid type for APPEND: {x.type}")
    if len(x) >= engine.limits.max_stack_size:
        raise Exception("Array size limit exceeded")
    x.add(item)


def setitem(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Set item in compound type by key/index."""
    value = engine.pop()
    key = engine.pop()
    x = engine.pop()
    if isinstance(x, Array):
        idx = int(key.get_integer())
        if idx < 0 or idx >= len(x):
            raise Exception(f"Index out of range: {idx}")
        x[idx] = value
    elif isinstance(x, Map):
        if len(x) >= engine.limits.max_stack_size and key not in x:
            raise Exception("Map size limit exceeded")
        x[key] = value
    elif isinstance(x, Buffer):
        idx = int(key.get_integer())
        if idx < 0 or idx >= len(x):
            raise Exception(f"Index out of range: {idx}")
        val = int(value.get_integer())
        if val < 0 or val > 255:
            raise Exception(f"Value out of byte range: {val}")
        x[idx] = val
    else:
        raise Exception(f"Invalid type for SETITEM: {x.type}")


def reverseitems(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Reverse items in array or buffer."""
    x = engine.pop()
    if isinstance(x, Array):
        x.reverse()
    elif isinstance(x, Buffer):
        x.reverse()
    else:
        raise Exception(f"Invalid type for REVERSEITEMS: {x.type}")


def remove(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Remove item from compound type by key/index."""
    key = engine.pop()
    x = engine.pop()
    if isinstance(x, Array):
        idx = int(key.get_integer())
        if idx < 0 or idx >= len(x):
            raise Exception(f"Index out of range: {idx}")
        x.remove_at(idx)
    elif isinstance(x, Map):
        if key not in x:
            raise Exception("Key not found in map")
        del x[key]
    else:
        raise Exception(f"Invalid type for REMOVE: {x.type}")


def clearitems(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Clear all items from compound type."""
    x = engine.pop()
    if isinstance(x, (Array, Map)):
        x.clear()
    else:
        raise Exception(f"Invalid type for CLEARITEMS: {x.type}")


def popitem(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Pop last item from array."""
    x = engine.pop()
    if not isinstance(x, Array):
        raise Exception(f"Invalid type for POPITEM: {x.type}")
    if len(x) == 0:
        raise Exception("Array is empty")
    item = x[-1]
    x.remove_at(len(x) - 1)
    engine.push(item)
