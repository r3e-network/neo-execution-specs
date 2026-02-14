"""Neo N3 NEF (Neo Executable Format) implementation."""

from dataclasses import dataclass, field
from typing import List
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

    @classmethod
    def deserialize(cls, data: bytes, offset: int) -> tuple["MethodToken", int]:
        """Deserialize method token, return (token, new_offset)."""
        token_hash = data[offset:offset + 20]
        offset += 20
        method_len = struct.unpack_from('<I', data, offset)[0]
        offset += 4
        method = data[offset:offset + method_len].decode('utf-8')
        offset += method_len
        params_count = struct.unpack_from('<H', data, offset)[0]
        offset += 2
        has_return = data[offset] != 0
        offset += 1
        call_flags = struct.unpack_from('<H', data, offset)[0]
        offset += 2
        return cls(token_hash, method, params_count, has_return, call_flags), offset


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

    @classmethod
    def deserialize(cls, data: bytes) -> "NefFile":
        """Deserialize NEF file from bytes.

        Binary layout:
          Magic        (4B LE uint32)
          Compiler     (64B, zero-padded)
          Source       (var_bytes)
          Reserved     (1B)
          Tokens       (var_int count + serialized tokens)
          Reserved     (2B)
          Script       (var_bytes)
          Checksum     (4B LE uint32)
        """
        if len(data) < 4:
            raise ValueError("Data too short for NEF")

        offset = 0

        # Magic
        magic = struct.unpack_from('<I', data, offset)[0]
        if magic != NEF_MAGIC:
            raise ValueError(f"Invalid NEF magic: 0x{magic:08X}")
        offset += 4

        # Compiler (64 bytes, strip trailing NULs)
        compiler_raw = data[offset:offset + 64]
        compiler = compiler_raw.rstrip(b'\x00').decode('utf-8')
        offset += 64

        # Source (var_bytes)
        source_bytes, offset = read_var_bytes(data, offset)
        source = source_bytes.decode('utf-8')

        # Reserved (1 byte)
        offset += 1

        # Tokens
        token_count, offset = read_var_int(data, offset)
        tokens: List[MethodToken] = []
        for _ in range(token_count):
            token, offset = MethodToken.deserialize(data, offset)
            tokens.append(token)

        # Reserved (2 bytes)
        offset += 2

        # Source URL length validation (max 256 bytes)
        MAX_SOURCE_URL_LENGTH = 256
        if len(source_bytes) > MAX_SOURCE_URL_LENGTH:
            raise ValueError(
                f"NEF source URL too long: {len(source_bytes)} > {MAX_SOURCE_URL_LENGTH}"
            )

        # Script (var_bytes)
        script, offset = read_var_bytes(data, offset)

        # Script size validation
        MAX_SCRIPT_LENGTH = 512 * 1024  # 512 KB
        if len(script) == 0:
            raise ValueError("NEF script cannot be empty")
        if len(script) > MAX_SCRIPT_LENGTH:
            raise ValueError(
                f"NEF script too large: {len(script)} > {MAX_SCRIPT_LENGTH}"
            )

        # Checksum
        stored_checksum = struct.unpack_from('<I', data, offset)[0]

        nef = cls(
            compiler=compiler,
            source=source,
            tokens=tokens,
            script=script,
            checksum=stored_checksum,
        )

        computed = nef.compute_checksum()
        if stored_checksum != computed:
            raise ValueError(
                f"NEF checksum mismatch: stored={stored_checksum}, computed={computed}"
            )

        return nef


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


def read_var_int(data: bytes, offset: int) -> tuple[int, int]:
    """Read variable length integer, return (value, new_offset)."""
    if offset >= len(data):
        raise ValueError("Unexpected end of data reading var_int")
    fb = data[offset]
    offset += 1
    if fb < 0xFD:
        return fb, offset
    elif fb == 0xFD:
        value = struct.unpack_from('<H', data, offset)[0]
        return value, offset + 2
    elif fb == 0xFE:
        value = struct.unpack_from('<I', data, offset)[0]
        return value, offset + 4
    else:
        value = struct.unpack_from('<Q', data, offset)[0]
        return value, offset + 8


def read_var_bytes(data: bytes, offset: int) -> tuple[bytes, int]:
    """Read variable length bytes, return (bytes, new_offset)."""
    length, offset = read_var_int(data, offset)
    result = data[offset:offset + length]
    if len(result) != length:
        raise ValueError(f"Expected {length} bytes, got {len(result)}")
    return result, offset + length
