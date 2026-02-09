"""
BinaryWriter - Binary serialization helper.

Reference: Neo.IO.BinaryWriter extensions
"""

from typing import List, TYPE_CHECKING
import struct

if TYPE_CHECKING:
    from neo.io.serializable import ISerializable
    from neo.types.uint160 import UInt160
    from neo.types.uint256 import UInt256


class BinaryWriter:
    """Binary writer for serializing Neo data structures."""
    
    __slots__ = ("_data",)
    
    def __init__(self) -> None:
        self._data = bytearray()
    
    def to_bytes(self) -> bytes:
        """Get the written data as bytes."""
        return bytes(self._data)
    
    @property
    def length(self) -> int:
        """Get the current length of written data."""
        return len(self._data)
    
    def write_byte(self, value: int) -> None:
        """Write a single byte."""
        self._data.append(value & 0xFF)
    
    def write_bytes(self, data: bytes) -> None:
        """Write raw bytes."""
        self._data.extend(data)
    
    def write_bool(self, value: bool) -> None:
        """Write a boolean."""
        self.write_byte(1 if value else 0)
    
    def write_int8(self, value: int) -> None:
        """Write a signed 8-bit integer."""
        self._data.extend(struct.pack('<b', value))
    
    def write_uint16(self, value: int) -> None:
        """Write an unsigned 16-bit integer (little-endian)."""
        self._data.extend(struct.pack('<H', value))
    
    def write_int16(self, value: int) -> None:
        """Write a signed 16-bit integer (little-endian)."""
        self._data.extend(struct.pack('<h', value))
    
    def write_uint32(self, value: int) -> None:
        """Write an unsigned 32-bit integer (little-endian)."""
        self._data.extend(struct.pack('<I', value))
    
    def write_int32(self, value: int) -> None:
        """Write a signed 32-bit integer (little-endian)."""
        self._data.extend(struct.pack('<i', value))
    
    def write_uint64(self, value: int) -> None:
        """Write an unsigned 64-bit integer (little-endian)."""
        self._data.extend(struct.pack('<Q', value))
    
    def write_int64(self, value: int) -> None:
        """Write a signed 64-bit integer (little-endian)."""
        self._data.extend(struct.pack('<q', value))
    
    def write_var_int(self, value: int) -> None:
        """Write a variable-length integer."""
        if value < 0:
            raise ValueError("VarInt cannot be negative")
        if value < 0xFD:
            self.write_byte(value)
        elif value <= 0xFFFF:
            self.write_byte(0xFD)
            self.write_uint16(value)
        elif value <= 0xFFFFFFFF:
            self.write_byte(0xFE)
            self.write_uint32(value)
        else:
            self.write_byte(0xFF)
            self.write_uint64(value)
    
    def write_var_bytes(self, data: bytes) -> None:
        """Write a variable-length byte array."""
        self.write_var_int(len(data))
        self.write_bytes(data)
    
    def write_var_string(self, value: str) -> None:
        """Write a variable-length UTF-8 string."""
        self.write_var_bytes(value.encode('utf-8'))
    
    def write_uint160(self, value: "UInt160") -> None:
        """Write a UInt160 (20-byte hash)."""
        self.write_bytes(value.data)
    
    def write_uint256(self, value: "UInt256") -> None:
        """Write a UInt256 (32-byte hash)."""
        self.write_bytes(value.data)
    
    def write_serializable(self, obj: "ISerializable") -> None:
        """Write a serializable object."""
        obj.serialize(self)
    
    def write_serializable_array(self, items: List["ISerializable"]) -> None:
        """Write an array of serializable objects."""
        self.write_var_int(len(items))
        for item in items:
            item.serialize(self)
    
    def write_ec_point(self, point: bytes) -> None:
        """Write an EC point."""
        self.write_bytes(point)
