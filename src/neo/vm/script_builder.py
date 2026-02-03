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
    
    def emit_raw(self, data: bytes) -> "ScriptBuilder":
        """Emit raw bytes."""
        self._data.extend(data)
        return self
    
    def emit_push(self, value) -> "ScriptBuilder":
        """Push a value onto the stack.
        
        Args:
            value: Integer, bytes, bool, or None
        """
        if value is None:
            return self.emit(OpCode.PUSHNULL)
        elif isinstance(value, bool):
            return self.emit(OpCode.PUSHT if value else OpCode.PUSHF)
        elif isinstance(value, int):
            return self._emit_push_int(value)
        elif isinstance(value, bytes):
            return self._emit_push_bytes(value)
        elif isinstance(value, str):
            return self._emit_push_bytes(value.encode('utf-8'))
        else:
            raise ValueError(f"Cannot push type: {type(value)}")
    
    def _emit_push_int(self, value: int) -> "ScriptBuilder":
        """Push an integer."""
        if value == -1:
            return self.emit(OpCode.PUSHM1)
        elif 0 <= value <= 16:
            return self.emit(OpCode.PUSH0 + value)
        else:
            # Convert to bytes
            if value == 0:
                data = b'\x00'
            elif value > 0:
                byte_len = (value.bit_length() + 8) // 8
                data = value.to_bytes(byte_len, 'little', signed=False)
            else:
                byte_len = (value.bit_length() + 9) // 8
                data = value.to_bytes(byte_len, 'little', signed=True)
            
            return self._emit_push_bytes(data)
    
    def _emit_push_bytes(self, data: bytes) -> "ScriptBuilder":
        """Push bytes."""
        length = len(data)
        
        if length < 0x100:
            self.emit(OpCode.PUSHDATA1)
            self._data.append(length)
        elif length < 0x10000:
            self.emit(OpCode.PUSHDATA2)
            self._data.extend(length.to_bytes(2, 'little'))
        else:
            self.emit(OpCode.PUSHDATA4)
            self._data.extend(length.to_bytes(4, 'little'))
        
        self._data.extend(data)
        return self
    
    def emit_call(self, offset: int) -> "ScriptBuilder":
        """Emit CALL instruction."""
        if -128 <= offset <= 127:
            self.emit(OpCode.CALL)
            self._data.append(offset & 0xFF)
        else:
            self.emit(OpCode.CALL_L)
            self._data.extend(offset.to_bytes(4, 'little', signed=True))
        return self
    
    def emit_jump(self, op: int, offset: int) -> "ScriptBuilder":
        """Emit jump instruction with offset."""
        self.emit(op)
        if op in (OpCode.JMP, OpCode.JMPIF, OpCode.JMPIFNOT, 
                  OpCode.JMPEQ, OpCode.JMPNE, OpCode.JMPGT,
                  OpCode.JMPGE, OpCode.JMPLT, OpCode.JMPLE):
            self._data.append(offset & 0xFF)
        else:
            self._data.extend(offset.to_bytes(4, 'little', signed=True))
        return self
    
    def emit_syscall(self, method_hash: int) -> "ScriptBuilder":
        """Emit SYSCALL instruction."""
        self.emit(OpCode.SYSCALL)
        self._data.extend(method_hash.to_bytes(4, 'little'))
        return self
    
    def to_bytes(self) -> bytes:
        """Get script bytes."""
        return bytes(self._data)
    
    def __len__(self) -> int:
        """Get script length."""
        return len(self._data)
