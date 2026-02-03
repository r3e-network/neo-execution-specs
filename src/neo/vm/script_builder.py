"""Neo N3 Script Builder."""

from neo.vm.opcode import OpCode


class ScriptBuilder:
    """Build VM scripts."""
    
    def __init__(self):
        self._data = bytearray()
    
    def emit(self, op: int) -> "ScriptBuilder":
        """Emit opcode."""
        self._data.append(op)
        return self
    
    def to_bytes(self) -> bytes:
        """Get script bytes."""
        return bytes(self._data)
