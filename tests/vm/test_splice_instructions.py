"""Tests for splice instructions."""

from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


class TestSpliceInstructions:
    """Test splice/string operations."""

    def test_cat(self):
        """Test CAT concatenates two byte strings."""
        script = bytes([
            0x0C,
            2,
            ord("a"),
            ord("b"),  # PUSHDATA1 "ab"
            0x0C,
            2,
            ord("c"),
            ord("d"),  # PUSHDATA1 "cd"
            OpCode.CAT,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()

        assert engine.state == VMState.HALT
        result = engine.result_stack.peek()
        assert result.get_string() == "abcd"

    def test_substr(self):
        """Test SUBSTR extracts substring."""
        script = bytes([
            0x0C,
            5,
            ord("h"),
            ord("e"),
            ord("l"),
            ord("l"),
            ord("o"),
            OpCode.PUSH1,  # index
            OpCode.PUSH3,  # count
            OpCode.SUBSTR,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()

        assert engine.state == VMState.HALT
        result = engine.result_stack.peek()
        assert result.get_string() == "ell"

    def test_left(self):
        """Test LEFT extracts left portion."""
        script = bytes([
            0x0C,
            5,
            ord("h"),
            ord("e"),
            ord("l"),
            ord("l"),
            ord("o"),
            OpCode.PUSH2,  # count
            OpCode.LEFT,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()

        assert engine.state == VMState.HALT
        result = engine.result_stack.peek()
        assert result.get_string() == "he"

    def test_right(self):
        """Test RIGHT extracts right portion."""
        script = bytes([
            0x0C,
            5,
            ord("h"),
            ord("e"),
            ord("l"),
            ord("l"),
            ord("o"),
            OpCode.PUSH2,  # count
            OpCode.RIGHT,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()

        assert engine.state == VMState.HALT
        result = engine.result_stack.peek()
        assert result.get_string() == "lo"

    def test_newbuffer(self):
        """Test NEWBUFFER creates buffer."""
        script = bytes([
            OpCode.PUSH5,
            OpCode.NEWBUFFER,
            OpCode.SIZE,
        ])
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()

        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 5

    def test_memcpy_basic_copy(self):
        """Test MEMCPY copies range from source to destination buffer."""
        script = bytes.fromhex("13884a100c036162631112894aca")

        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()

        assert engine.state == VMState.HALT
        assert len(engine.result_stack) == 2

        copied_size = engine.result_stack.pop().get_integer()
        copied_buffer = engine.result_stack.pop()

        assert copied_size == 3
        assert copied_buffer.get_bytes_unsafe().hex() == "626300"

    def test_memcpy_faults_on_oob_source(self):
        """Test MEMCPY faults when source slice exceeds source length."""
        script = bytes.fromhex("12884a100c0161101289")

        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()

        assert engine.state == VMState.FAULT
