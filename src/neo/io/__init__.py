"""
Binary IO utilities for Neo N3.

Reference: Neo.IO
"""

import struct
from typing import BinaryIO


class BinaryReader:
    """Binary reader for Neo serialization."""
    
    def __init__(self, stream: BinaryIO):
        self._stream = stream
    
    def read_byte(self) -> int:
        return self._stream.read(1)[0]
    
    def read_bytes(self, count: int) -> bytes:
        return self._stream.read(count)
    
    def read_uint16(self) -> int:
        return struct.unpack('<H', self._stream.read(2))[0]
    
    def read_uint32(self) -> int:
        return struct.unpack('<I', self._stream.read(4))[0]
    
    def read_uint64(self) -> int:
        return struct.unpack('<Q', self._stream.read(8))[0]
    
    def read_var_int(self) -> int:
        fb = self.read_byte()
        if fb < 0xFD:
            return fb
        elif fb == 0xFD:
            return self.read_uint16()
        elif fb == 0xFE:
            return self.read_uint32()
        else:
            return self.read_uint64()


class BinaryWriter:
    """Binary writer for Neo serialization."""
    
    def __init__(self, stream: BinaryIO):
        self._stream = stream
    
    def write_byte(self, value: int) -> None:
        self._stream.write(bytes([value]))
    
    def write_bytes(self, data: bytes) -> None:
        self._stream.write(data)
    
    def write_uint16(self, value: int) -> None:
        self._stream.write(struct.pack('<H', value))
    
    def write_uint32(self, value: int) -> None:
        self._stream.write(struct.pack('<I', value))
    
    def write_var_int(self, value: int) -> None:
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
            self._stream.write(struct.pack('<Q', value))
