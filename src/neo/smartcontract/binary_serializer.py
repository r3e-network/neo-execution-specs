"""BinarySerializer - Serialize/deserialize StackItems to binary."""

from __future__ import annotations
from typing import TYPE_CHECKING
import struct

if TYPE_CHECKING:
    from neo.vm.types import StackItem


class BinarySerializer:
    """Binary serializer for StackItems."""
    
    @staticmethod
    def serialize(item: StackItem, max_size: int = 65535) -> bytes:
        """Serialize a StackItem to bytes."""
        from neo.vm.types import (
            StackItem, Integer, ByteString, Boolean, 
            Array, Map, Struct, Buffer, NULL
        )
        
        data = bytearray()
        stack = [item]
        serialized = set()
        
        while stack:
            current = stack.pop()
            
            if current is NULL or current is None:
                data.append(0x00)  # Any/Null
            elif isinstance(current, Boolean):
                data.append(0x20)  # Boolean
                data.append(1 if current.value else 0)
            elif isinstance(current, Integer):
                data.append(0x21)  # Integer
                val = current.value
                if val == 0:
                    data.append(0)
                else:
                    int_bytes = BinarySerializer._int_to_bytes(val)
                    data.extend(BinarySerializer._write_var_int(len(int_bytes)))
                    data.extend(int_bytes)
            elif isinstance(current, (ByteString, Buffer)):
                data.append(0x28 if isinstance(current, ByteString) else 0x30)
                val_bytes = current.value if hasattr(current, 'value') else bytes(current)
                data.extend(BinarySerializer._write_var_int(len(val_bytes)))
                data.extend(val_bytes)
            elif isinstance(current, (Array, Struct)):
                if id(current) in serialized:
                    raise ValueError("Circular reference detected")
                serialized.add(id(current))
                data.append(0x40 if isinstance(current, Array) else 0x41)
                data.extend(BinarySerializer._write_var_int(len(current)))
                for i in range(len(current) - 1, -1, -1):
                    stack.append(current[i])
            elif isinstance(current, Map):
                if id(current) in serialized:
                    raise ValueError("Circular reference detected")
                serialized.add(id(current))
                data.append(0x48)  # Map
                data.extend(BinarySerializer._write_var_int(len(current)))
                for key, value in reversed(list(current.items())):
                    stack.append(value)
                    stack.append(key)
            else:
                raise ValueError(f"Unsupported type: {type(current)}")
            
            if len(data) > max_size:
                raise ValueError("Serialized data exceeds max size")
        
        return bytes(data)
    
    @staticmethod
    def _write_var_int(value: int) -> bytes:
        """Write variable-length integer."""
        if value < 0xFD:
            return bytes([value])
        elif value <= 0xFFFF:
            return b'\xFD' + struct.pack('<H', value)
        elif value <= 0xFFFFFFFF:
            return b'\xFE' + struct.pack('<I', value)
        else:
            return b'\xFF' + struct.pack('<Q', value)
    
    @staticmethod
    def _int_to_bytes(value: int) -> bytes:
        """Convert integer to bytes (little-endian, signed)."""
        if value == 0:
            return b''
        length = (value.bit_length() + 8) // 8
        return value.to_bytes(length, 'little', signed=True)
    
    @staticmethod
    def deserialize(data: bytes, max_size: int = 65535) -> StackItem:
        """Deserialize bytes to StackItem."""
        from neo.vm.types import (
            Integer, ByteString, Boolean, 
            Array, Map, Struct, Buffer, NULL
        )
        
        reader = _ByteReader(data)
        stack = []
        undeserialized = 1
        
        while undeserialized > 0:
            undeserialized -= 1
            item_type = reader.read_byte()
            
            if item_type == 0x00:  # Any/Null
                stack.append(NULL)
            elif item_type == 0x20:  # Boolean
                stack.append(Boolean(reader.read_byte() != 0))
            elif item_type == 0x21:  # Integer
                length = reader.read_var_int()
                if length == 0:
                    stack.append(Integer(0))
                else:
                    int_bytes = reader.read_bytes(length)
                    val = int.from_bytes(int_bytes, 'little', signed=True)
                    stack.append(Integer(val))
            elif item_type == 0x28:  # ByteString
                length = reader.read_var_int()
                stack.append(ByteString(reader.read_bytes(length)))
            elif item_type == 0x30:  # Buffer
                length = reader.read_var_int()
                stack.append(Buffer(reader.read_bytes(length)))
            elif item_type in (0x40, 0x41):  # Array or Struct
                count = reader.read_var_int()
                stack.append(_Placeholder(item_type, count))
                undeserialized += count
            elif item_type == 0x48:  # Map
                count = reader.read_var_int()
                stack.append(_Placeholder(item_type, count))
                undeserialized += count * 2
            else:
                raise ValueError(f"Invalid type: {item_type}")
        
        # Reconstruct compound types
        result = []
        for item in stack:
            if isinstance(item, _Placeholder):
                if item.type == 0x40:  # Array
                    arr = Array()
                    for _ in range(item.count):
                        arr.append(result.pop())
                    result.append(arr)
                elif item.type == 0x41:  # Struct
                    s = Struct()
                    for _ in range(item.count):
                        s.append(result.pop())
                    result.append(s)
                elif item.type == 0x48:  # Map
                    m = Map()
                    for _ in range(item.count):
                        key = result.pop()
                        value = result.pop()
                        m[key] = value
                    result.append(m)
            else:
                result.append(item)
        
        return result[0] if result else NULL


class _Placeholder:
    """Placeholder for compound types during deserialization."""
    
    def __init__(self, type_: int, count: int):
        self.type = type_
        self.count = count


class _ByteReader:
    """Helper class for reading bytes."""
    
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0
    
    def read_byte(self) -> int:
        val = self.data[self.pos]
        self.pos += 1
        return val
    
    def read_bytes(self, count: int) -> bytes:
        val = self.data[self.pos:self.pos + count]
        self.pos += count
        return val
    
    def read_var_int(self) -> int:
        fb = self.read_byte()
        if fb < 0xFD:
            return fb
        elif fb == 0xFD:
            return struct.unpack('<H', self.read_bytes(2))[0]
        elif fb == 0xFE:
            return struct.unpack('<I', self.read_bytes(4))[0]
        else:
            return struct.unpack('<Q', self.read_bytes(8))[0]
