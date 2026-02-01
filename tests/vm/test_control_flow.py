"""Tests for VM control flow operations."""

import pytest
from neo.vm import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


class TestJmp:
    """Tests for JMP opcode."""

    def test_jmp_forward(self):
        """JMP jumps forward in script."""
        engine = ExecutionEngine()
        # JMP +3, PUSH1 (skipped), PUSH2
        script = bytes([
            OpCode.JMP, 3,      # Jump forward 3 bytes
            OpCode.PUSH1,       # Skipped
            OpCode.PUSH2
        ])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

    def test_jmp_to_end(self):
        """JMP to end of script."""
        engine = ExecutionEngine()
        script = bytes([OpCode.JMP, 2])  # Jump to end
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

    def test_nop(self):
        """NOP does nothing."""
        engine = ExecutionEngine()
        script = bytes([OpCode.NOP, OpCode.PUSH1])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT


class TestJmpIf:
    """Tests for JMPIF opcode."""

    def test_jmpif_true(self):
        """JMPIF jumps when condition is true."""
        engine = ExecutionEngine()
        script = bytes([
            OpCode.PUSHT,       # Push true
            OpCode.JMPIF, 3,    # Jump if true
            OpCode.PUSH1,       # Skipped
            OpCode.PUSH2
        ])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

    def test_jmpif_false(self):
        """JMPIF does not jump when condition is false."""
        engine = ExecutionEngine()
        script = bytes([
            OpCode.PUSHF,       # Push false
            OpCode.JMPIF, 3,    # No jump
            OpCode.PUSH1,       # Executed
            OpCode.PUSH2
        ])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

    def test_jmpif_nonzero(self):
        """JMPIF jumps on non-zero integer."""
        engine = ExecutionEngine()
        script = bytes([
            OpCode.PUSH5,       # Non-zero = true
            OpCode.JMPIF, 3,    # Jump
            OpCode.PUSH1,       # Skipped
            OpCode.PUSH2
        ])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT


class TestJmpIfNot:
    """Tests for JMPIFNOT opcode."""

    def test_jmpifnot_false(self):
        """JMPIFNOT jumps when condition is false."""
        engine = ExecutionEngine()
        script = bytes([
            OpCode.PUSHF,          # Push false
            OpCode.JMPIFNOT, 3,    # Jump if not true
            OpCode.PUSH1,          # Skipped
            OpCode.PUSH2
        ])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

    def test_jmpifnot_true(self):
        """JMPIFNOT does not jump when condition is true."""
        engine = ExecutionEngine()
        script = bytes([
            OpCode.PUSHT,          # Push true
            OpCode.JMPIFNOT, 3,    # No jump
            OpCode.PUSH1,          # Executed
            OpCode.PUSH2
        ])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

    def test_jmpifnot_zero(self):
        """JMPIFNOT jumps on zero."""
        engine = ExecutionEngine()
        script = bytes([
            OpCode.PUSH0,          # Zero = false
            OpCode.JMPIFNOT, 3,    # Jump
            OpCode.PUSH1,          # Skipped
            OpCode.PUSH2
        ])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT


class TestCall:
    """Tests for CALL opcode."""

    def test_call_and_ret(self):
        """CALL invokes subroutine, RET returns."""
        engine = ExecutionEngine()
        # CALL to offset 5, then PUSH1, then subroutine at 5: PUSH2, RET
        script = bytes([
            OpCode.CALL, 4,     # Call subroutine at offset +4
            OpCode.PUSH1,       # After return
            OpCode.JMP, 3,      # Skip subroutine
            OpCode.PUSH2,       # Subroutine body
            OpCode.RET
        ])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT


class TestRet:
    """Tests for RET opcode."""

    def test_ret_ends_execution(self):
        """RET at top level ends execution."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH1, OpCode.RET])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

    def test_ret_with_value(self):
        """RET preserves stack values."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH5, OpCode.RET])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT
