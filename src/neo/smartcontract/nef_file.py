"""NefFile - NEO Executable Format."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any
import struct
import hashlib


@dataclass
class MethodToken:
    """Method token for static calls."""
    
    hash: bytes = b""  # 20 bytes
    method: str = ""
    parameters_count: int = 0
    has_return_value: bool = False
    call_flags: int = 0
    
    def to_json(self) -> Dict[str, Any]:
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
    tokens: List[MethodToken] = field(default_factory=list)
    script: bytes = b""
    checksum: int = 0
    
    def to_json(self) -> Dict[str, Any]:
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
