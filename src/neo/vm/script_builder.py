"""Script builder for constructing VM scripts."""

from __future__ import annotations
from neo.vm.opcode import OpCode


class ScriptBuilder:
    """Builds VM scripts."""
    
    def __init__(self) -> None:
        self._data = bytearray()
    
    def emit(self, opcode: OpCode) -> ScriptBuilder:
        """Emit an opcode."""
        self._data.append(opcode)
        return self
    
    def emit_push(self, value: int) -> ScriptBuilder:
        """Push an integer."""
        if value == -1:
            return self.emit(OpCode.PUSHM1)
        if 0 <= value <= 16:
            self._data.append(OpCode.PUSH0 + value)
        else:
            # PUSHINT8 for small values
            self._data.append(OpCode.PUSHINT8)
            self._data.append(value & 0xFF)
        return self
    
    def to_bytes(self) -> bytes:
        """Get the script bytes."""
        return bytes(self._data)
