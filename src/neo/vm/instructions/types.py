"""Type instructions for NeoVM.

This module implements type checking and conversion opcodes (0xD8-0xE1):
- ISNULL: Check if item is null
- ISTYPE: Check if item is of specified type
- CONVERT: Convert item to specified type
- ABORTMSG: Abort with message
- ASSERTMSG: Assert with message
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from neo.exceptions import InvalidOperationException, VMAbortException
from neo.vm.types import (
    Boolean, Integer, ByteString, Buffer, Array, Struct, StackItemType, NULL
)

if TYPE_CHECKING:
    from neo.vm.execution_engine import ExecutionEngine
    from neo.vm.execution_context import Instruction


def isnull(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Check if item is null.
    
    Pop: 1 item
    Push: Boolean (true if null)
    """
    item = engine.pop()
    result = item is NULL or item.type == StackItemType.ANY
    engine.push(Boolean(result))


def istype(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Check if item is of specified type.
    
    The type is specified in the instruction operand.
    
    Pop: 1 item
    Push: Boolean (true if type matches)
    """
    item = engine.pop()
    item_type = instruction.operand[0] if instruction.operand else 0
    
    # Validate type - ANY is not allowed, and type must be defined
    if item_type == StackItemType.ANY:
        raise InvalidOperationException("Invalid type for ISTYPE: ANY")
    
    valid_types = {t.value for t in StackItemType}
    if item_type not in valid_types:
        raise InvalidOperationException(f"Invalid type for ISTYPE: {item_type}")
    
    result = item.type == item_type
    engine.push(Boolean(result))


def convert(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Convert item to specified type.
    
    The target type is specified in the instruction operand.
    Supported conversions:
    - Any -> Boolean (via get_boolean)
    - Any -> Integer (via get_integer)
    - Any -> ByteString (via get_span/bytes)
    - ByteString -> Buffer (copy)
    - Array -> Struct (copy elements)
    - Struct -> Array (copy elements)
    
    Pop: 1 item
    Push: Converted item
    """
    item = engine.pop()
    target_type = instruction.operand[0] if instruction.operand else 0
    
    # Validate target type
    valid_types = {t.value for t in StackItemType}
    if target_type not in valid_types:
        raise InvalidOperationException(f"Invalid type for CONVERT: {target_type}")
    
    result = _convert_to(item, target_type, engine)
    engine.push(result)


def _convert_to(item, target_type: int, engine):
    """Convert a stack item to the target type."""
    # If already the target type, return as-is
    if item.type == target_type:
        return item
    
    # Handle Null specially
    if item is NULL or item.type == StackItemType.ANY:
        if target_type == StackItemType.ANY:
            return NULL
        raise InvalidOperationException(f"Cannot convert Null to {StackItemType(target_type).name}")
    
    # Convert based on target type
    if target_type == StackItemType.BOOLEAN:
        return Boolean(item.get_boolean())
    
    elif target_type == StackItemType.INTEGER:
        return Integer(item.get_integer())
    
    elif target_type == StackItemType.BYTESTRING:
        if hasattr(item, 'get_span'):
            return ByteString(item.get_span())
        elif isinstance(item, Integer):
            # Convert integer to bytes
            value = int(item.get_integer())
            if value == 0:
                return ByteString(b'')
            # Determine byte length needed
            byte_len = (value.bit_length() + 8) // 8  # +8 for sign bit
            try:
                data = value.to_bytes(byte_len, 'little', signed=True)
            except OverflowError:
                byte_len += 1
                data = value.to_bytes(byte_len, 'little', signed=True)
            return ByteString(data)
        elif isinstance(item, Boolean):
            return ByteString(b'\x01' if item.get_boolean() else b'')
        else:
            raise InvalidOperationException(f"Cannot convert {item.type} to ByteString")
    
    elif target_type == StackItemType.BUFFER:
        if isinstance(item, (ByteString, Buffer)):
            data = item.get_span()
            return Buffer(data)
        elif isinstance(item, Integer):
            value = int(item.get_integer())
            if value == 0:
                return Buffer(b'')
            byte_len = (value.bit_length() + 8) // 8
            try:
                data = value.to_bytes(byte_len, 'little', signed=True)
            except OverflowError:
                byte_len += 1
                data = value.to_bytes(byte_len, 'little', signed=True)
            return Buffer(data)
        else:
            raise InvalidOperationException(f"Cannot convert {item.type} to Buffer")
    
    elif target_type == StackItemType.ARRAY:
        if isinstance(item, Struct):
            # Convert struct to array
            result = Array(engine.reference_counter)
            for i in range(len(item)):
                result.add(item[i])
            return result
        else:
            raise InvalidOperationException(f"Cannot convert {item.type} to Array")
    
    elif target_type == StackItemType.STRUCT:
        if isinstance(item, Array):
            # Convert array to struct
            result = Struct(engine.reference_counter)
            for i in range(len(item)):
                result.add(item[i])
            return result
        else:
            raise InvalidOperationException(f"Cannot convert {item.type} to Struct")
    
    elif target_type == StackItemType.MAP:
        raise InvalidOperationException(f"Cannot convert {item.type} to Map")
    
    elif target_type == StackItemType.INTEROP_INTERFACE:
        raise InvalidOperationException(f"Cannot convert {item.type} to InteropInterface")
    
    elif target_type == StackItemType.POINTER:
        raise InvalidOperationException(f"Cannot convert {item.type} to Pointer")
    
    elif target_type == StackItemType.ANY:
        return NULL
    
    else:
        raise InvalidOperationException(f"Unknown target type: {target_type}")


def abortmsg(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Abort execution with a message.
    
    Pop: 1 item (message)
    """
    msg = engine.pop()
    try:
        message = msg.get_string()
    except (AttributeError, UnicodeDecodeError):
        try:
            message = msg.get_span().decode('utf-8', errors='replace')
        except AttributeError:
            message = str(msg)
    raise VMAbortException(f"ABORTMSG is executed. Reason: {message}")


def assertmsg(engine: ExecutionEngine, instruction: Instruction) -> None:
    """Assert condition with a message.
    
    Pop: 2 items (message, condition)
    """
    msg = engine.pop()
    condition = engine.pop()
    
    if not condition.get_boolean():
        try:
            message = msg.get_string()
        except (AttributeError, UnicodeDecodeError):
            try:
                message = msg.get_span().decode('utf-8', errors='replace')
            except AttributeError:
                message = str(msg)
        raise InvalidOperationException(f"ASSERTMSG is executed with false result. Reason: {message}")
