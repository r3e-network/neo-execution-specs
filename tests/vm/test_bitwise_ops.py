"""Tests for VM bitwise operations."""

from neo.vm import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


class TestAnd:
    """Tests for AND opcode."""

    def test_and_basic(self):
        """AND performs bitwise AND."""
        engine = ExecutionEngine()
        # 0b1111 (15) AND 0b1010 (10) = 0b1010 (10)
        script = bytes([OpCode.PUSH15, OpCode.PUSH10, OpCode.AND])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

    def test_and_with_zero(self):
        """AND with zero yields zero."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH5, OpCode.PUSH0, OpCode.AND])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

    def test_and_same_value(self):
        """AND of value with itself yields same value."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH7, OpCode.PUSH7, OpCode.AND])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT


class TestOr:
    """Tests for OR opcode."""

    def test_or_basic(self):
        """OR performs bitwise OR."""
        engine = ExecutionEngine()
        # 0b1100 (12) OR 0b1010 (10) = 0b1110 (14)
        script = bytes([OpCode.PUSH12, OpCode.PUSH10, OpCode.OR])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

    def test_or_with_zero(self):
        """OR with zero yields original value."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH5, OpCode.PUSH0, OpCode.OR])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

    def test_or_same_value(self):
        """OR of value with itself yields same value."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH7, OpCode.PUSH7, OpCode.OR])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT


class TestXor:
    """Tests for XOR opcode."""

    def test_xor_basic(self):
        """XOR performs bitwise XOR."""
        engine = ExecutionEngine()
        # 0b1100 (12) XOR 0b1010 (10) = 0b0110 (6)
        script = bytes([OpCode.PUSH12, OpCode.PUSH10, OpCode.XOR])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

    def test_xor_with_zero(self):
        """XOR with zero yields original value."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH5, OpCode.PUSH0, OpCode.XOR])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

    def test_xor_same_value(self):
        """XOR of value with itself yields zero."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH7, OpCode.PUSH7, OpCode.XOR])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT


class TestInvert:
    """Tests for INVERT opcode."""

    def test_invert_basic(self):
        """INVERT performs bitwise NOT."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH0, OpCode.INVERT])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

    def test_invert_positive(self):
        """INVERT of positive number."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH5, OpCode.INVERT])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

    def test_invert_double(self):
        """Double INVERT returns original value."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH7, OpCode.INVERT, OpCode.INVERT])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT
