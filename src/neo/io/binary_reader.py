"""
BinaryReader - Binary deserialization helper.

Reference: Neo.IO.MemoryReader
"""

from typing import Type, TypeVar, List, TYPE_CHECKING
import struct

if TYPE_CHECKING:
    from neo.io.serializable import ISerializable
    from neo.types.uint160 import UInt160
    from neo.types.uint256 import UInt256

T = TypeVar('T', bound='ISerializable')


class BinaryReader:
    """Binary reader for deserializing Neo data structures."""
    
    __slots__ = ("_data", "_position")
    
    def __init__(self, data: bytes) -> None:
        self._data = data
        self._position = 0
    
    @property
    def position(self) -> int:
        """Current read position."""
        return self._position
    
    @property
    def length(self) -> int:
        """Total length of data."""
        return len(self._data)
    
    @property
    def remaining(self) -> int:
        """Remaining bytes to read."""
        return len(self._data) - self._position
    
    def _check_size(self, size: int) -> None:
        """Check if enough bytes are available."""
        if self._position + size > len(self._data):
            raise ValueError(f"Not enough data: need {size}, have {self.remaining}")
    
    def read_byte(self) -> int:
        """Read a single byte."""
        self._check_size(1)
        value = self._data[self._position]
        self._position += 1
        return value
    
    def read_bytes(self, count: int) -> bytes:
        """Read a fixed number of bytes."""
        self._check_size(count)
        value = self._data[self._position:self._position + count]
        self._position += count
        return value
    
    def read_bool(self) -> bool:
        """Read a boolean."""
        return self.read_byte() != 0
    
    def read_int8(self) -> int:
        """Read a signed 8-bit integer."""
        value = self.read_byte()
        return value if value < 128 else value - 256
    
    def read_uint16(self) -> int:
        """Read an unsigned 16-bit integer (little-endian)."""
        self._check_size(2)
        value = struct.unpack_from('<H', self._data, self._position)[0]
        self._position += 2
        return value
    
    def read_int16(self) -> int:
        """Read a signed 16-bit integer (little-endian)."""
        self._check_size(2)
        value = struct.unpack_from('<h', self._data, self._position)[0]
        self._position += 2
        return value
    
    def read_uint32(self) -> int:
        """Read an unsigned 32-bit integer (little-endian)."""
        self._check_size(4)
        value = struct.unpack_from('<I', self._data, self._position)[0]
        self._position += 4
        return value
    
    def read_int32(self) -> int:
        """Read a signed 32-bit integer (little-endian)."""
        self._check_size(4)
        value = struct.unpack_from('<i', self._data, self._position)[0]
        self._position += 4
        return value
    
    def read_uint64(self) -> int:
        """Read an unsigned 64-bit integer (little-endian)."""
        self._check_size(8)
        value = struct.unpack_from('<Q', self._data, self._position)[0]
        self._position += 8
        return value
    
    def read_int64(self) -> int:
        """Read a signed 64-bit integer (little-endian)."""
        self._check_size(8)
        value = struct.unpack_from('<q', self._data, self._position)[0]
        self._position += 8
        return value
    
    def read_var_int(self, max_value: int = 0xFFFFFFFFFFFFFFFF) -> int:
        """Read a variable-length integer."""
        fb = self.read_byte()
        if fb == 0xFD:
            value = self.read_uint16()
        elif fb == 0xFE:
            value = self.read_uint32()
        elif fb == 0xFF:
            value = self.read_uint64()
        else:
            value = fb
        if value > max_value:
            raise ValueError(f"VarInt {value} exceeds max {max_value}")
        return value
    
    def read_var_bytes(self, max_length: int = 0x1000000) -> bytes:
        """Read a variable-length byte array."""
        length = self.read_var_int(max_length)
        return self.read_bytes(length)
    
    def read_var_string(self, max_length: int = 0x1000000) -> str:
        """Read a variable-length UTF-8 string."""
        return self.read_var_bytes(max_length).decode('utf-8')
    
    def read_uint160(self) -> "UInt160":
        """Read a UInt160 (20-byte hash)."""
        from neo.types.uint160 import UInt160
        return UInt160(self.read_bytes(20))
    
    def read_uint256(self) -> "UInt256":
        """Read a UInt256 (32-byte hash)."""
        from neo.types.uint256 import UInt256
        return UInt256(self.read_bytes(32))
    
    def read_serializable(self, cls: Type[T]) -> T:
        """Read a serializable object."""
        return cls.deserialize(self)
    
    def read_serializable_array(self, cls: Type[T], max_count: int = 0x1000000) -> List[T]:
        """Read an array of serializable objects."""
        count = self.read_var_int(max_count)
        return [cls.deserialize(self) for _ in range(count)]
    
    def read_ec_point(self) -> bytes:
        """Read an EC point (compressed format)."""
        prefix = self.read_byte()
        if prefix == 0x00:
            return bytes([0x00])  # Infinity point
        elif prefix in (0x02, 0x03):
            return bytes([prefix]) + self.read_bytes(32)
        elif prefix == 0x04:
            return bytes([prefix]) + self.read_bytes(64)
        else:
            raise ValueError(f"Invalid EC point prefix: {prefix}")
