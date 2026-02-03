"""Neo N3 NEF (Neo Executable Format) implementation."""

from dataclasses import dataclass, field
from typing import List, Optional
import struct

from neo.crypto.hash import hash256


# NEF magic number
NEF_MAGIC = 0x3346454E  # "NEF3"


@dataclass
class MethodToken:
    """Method token for contract calls."""
    hash: bytes  # 20 bytes
    method: str
    parameters_count: int
    has_return_value: bool
    call_flags: int
    
    def serialize(self) -> bytes:
        """Serialize method token."""
        data = bytearray()
        data.extend(self.hash)
        method_bytes = self.method.encode('utf-8')
        data.extend(struct.pack('<I', len(method_bytes)))
        data.extend(method_bytes)
        data.extend(struct.pack('<H', self.parameters_count))
        data.append(1 if self.has_return_value else 0)
        data.extend(struct.pack('<H', self.call_flags))
        return bytes(data)


@dataclass
class NefFile:
    """NEF file structure."""
    
    compiler: str = "neo-core-v3.0"
    source: str = ""
    tokens: List[MethodToken] = field(default_factory=list)
    script: bytes = b""
    checksum: int = 0
    
    def __post_init__(self):
        if len(self.compiler) > 64:
            raise ValueError("Compiler name too long")
    
    @property
    def script_hash(self) -> bytes:
        """Get script hash."""
        from neo.crypto.hash import hash160
        return hash160(self.script)
    
    def compute_checksum(self) -> int:
        """Compute NEF checksum."""
        data = self._serialize_without_checksum()
        hash_bytes = hash256(data)
        return struct.unpack('<I', hash_bytes[:4])[0]
    
    def _serialize_without_checksum(self) -> bytes:
        """Serialize without checksum."""
        data = bytearray()
        
        # Magic
        data.extend(struct.pack('<I', NEF_MAGIC))
        
        # Compiler (64 bytes, padded)
        compiler_bytes = self.compiler.encode('utf-8')[:64]
        data.extend(compiler_bytes.ljust(64, b'\x00'))
        
        # Source
        source_bytes = self.source.encode('utf-8')
        data.extend(write_var_bytes(source_bytes))
        
        # Reserved
        data.append(0)
        
        # Tokens
        data.extend(write_var_int(len(self.tokens)))
        for token in self.tokens:
            data.extend(token.serialize())
        
        # Reserved
        data.extend(bytes(2))
        
        # Script
        data.extend(write_var_bytes(self.script))
        
        return bytes(data)
    
    def serialize(self) -> bytes:
        """Serialize NEF file."""
        data = self._serialize_without_checksum()
        checksum = self.compute_checksum()
        return data + struct.pack('<I', checksum)


def write_var_int(value: int) -> bytes:
    """Write variable length integer."""
    if value < 0xFD:
        return bytes([value])
    elif value <= 0xFFFF:
        return bytes([0xFD]) + struct.pack('<H', value)
    elif value <= 0xFFFFFFFF:
        return bytes([0xFE]) + struct.pack('<I', value)
    else:
        return bytes([0xFF]) + struct.pack('<Q', value)


def write_var_bytes(data: bytes) -> bytes:
    """Write variable length bytes."""
    return write_var_int(len(data)) + data
