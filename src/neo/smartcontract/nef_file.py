"""NefFile - NEO Executable Format."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import struct

@dataclass
class MethodToken:
    """Method token for static calls."""
    
    hash: bytes = b""  # 20 bytes
    method: str = ""
    parameters_count: int = 0
    has_return_value: bool = False
    call_flags: int = 0
    
    def to_json(self) -> dict[str, Any]:
        """Convert to JSON."""
        return {
            "hash": self.hash.hex(),
            "method": self.method,
            "paramcount": self.parameters_count,
            "hasreturnvalue": self.has_return_value,
            "callflags": self.call_flags
        }

@dataclass
class NefFile:
    """NEO Executable Format 3 (NEF3)."""
    
    MAGIC = 0x3346454E  # "NEF3"
    
    compiler: str = ""
    source: str = ""
    tokens: list[MethodToken] = field(default_factory=list)
    script: bytes = b""
    checksum: int = 0
    
    def to_json(self) -> dict[str, Any]:
        """Convert to JSON."""
        import base64
        return {
            "magic": self.MAGIC,
            "compiler": self.compiler,
            "source": self.source,
            "tokens": [t.to_json() for t in self.tokens],
            "script": base64.b64encode(self.script).decode(),
            "checksum": self.checksum
        }
    
    def to_array(self) -> bytes:
        """Serialize to byte array."""
        data = bytearray()
        # Magic
        data.extend(struct.pack('<I', self.MAGIC))
        # Compiler (64 bytes, padded)
        compiler_bytes = self.compiler.encode('utf-8')[:64]
        data.extend(compiler_bytes.ljust(64, b'\x00'))
        # Source (var string)
        source_bytes = self.source.encode('utf-8')
        data.extend(self._write_var_int(len(source_bytes)))
        data.extend(source_bytes)
        # Reserve byte
        data.append(0)
        # Tokens
        data.extend(self._write_var_int(len(self.tokens)))
        for token in self.tokens:
            data.extend(token.hash)
            method_bytes = token.method.encode('utf-8')
            data.extend(struct.pack('<I', len(method_bytes)))
            data.extend(method_bytes)
            data.extend(struct.pack('<H', token.parameters_count))
            data.append(1 if token.has_return_value else 0)
            data.extend(struct.pack('<H', token.call_flags))
        # Reserve 2 bytes
        data.extend(b'\x00\x00')
        # Script
        data.extend(self._write_var_int(len(self.script)))
        data.extend(self.script)
        # Checksum
        data.extend(struct.pack('<I', self.checksum))
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
    def _read_var_int(data: bytes, offset: int) -> tuple:
        """Read variable-length integer, return (value, new_offset)."""
        fb = data[offset]
        offset += 1
        if fb < 0xFD:
            return fb, offset
        elif fb == 0xFD:
            return struct.unpack_from('<H', data, offset)[0], offset + 2
        elif fb == 0xFE:
            return struct.unpack_from('<I', data, offset)[0], offset + 4
        else:
            return struct.unpack_from('<Q', data, offset)[0], offset + 8

    @classmethod
    def from_array(cls, data: bytes) -> "NefFile":
        """Deserialize from byte array."""
        if len(data) < 4:
            raise ValueError("Data too short for NEF")

        offset = 0

        # Magic
        magic = struct.unpack_from('<I', data, offset)[0]
        if magic != cls.MAGIC:
            raise ValueError(f"Invalid NEF magic: 0x{magic:08X}")
        offset += 4

        # Compiler (64 bytes)
        compiler = data[offset:offset + 64].rstrip(b'\x00').decode('utf-8')
        offset += 64

        # Source (var string)
        src_len, offset = cls._read_var_int(data, offset)
        source = data[offset:offset + src_len].decode('utf-8')
        offset += src_len

        # Reserve byte
        offset += 1

        # Tokens
        token_count, offset = cls._read_var_int(data, offset)
        tokens: list[MethodToken] = []
        for _ in range(token_count):
            t_hash = data[offset:offset + 20]
            offset += 20
            m_len = struct.unpack_from('<I', data, offset)[0]
            offset += 4
            method = data[offset:offset + m_len].decode('utf-8')
            offset += m_len
            params = struct.unpack_from('<H', data, offset)[0]
            offset += 2
            has_rv = data[offset] != 0
            offset += 1
            flags = struct.unpack_from('<H', data, offset)[0]
            offset += 2
            tokens.append(MethodToken(t_hash, method, params, has_rv, flags))

        # Reserve 2 bytes
        offset += 2

        # Script (var bytes)
        script_len, offset = cls._read_var_int(data, offset)
        script = data[offset:offset + script_len]
        offset += script_len

        # Checksum
        checksum = struct.unpack_from('<I', data, offset)[0]

        return cls(
            compiler=compiler,
            source=source,
            tokens=tokens,
            script=script,
            checksum=checksum,
        )
