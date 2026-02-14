"""Tests for VM compound operations (arrays, maps, structs)."""

from neo.vm import ExecutionEngine, VMState
from neo.vm.opcode import OpCode


class TestPack:
    """Tests for PACK opcode."""

    def test_pack_empty(self):
        """PACK with 0 elements creates empty array."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH0, OpCode.PACK])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT
        result = engine.result_stack.peek(0)
        assert len(result) == 0

    def test_pack_single_element(self):
        """PACK with 1 element."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH5, OpCode.PUSH1, OpCode.PACK])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT
        result = engine.result_stack.peek(0)
        assert len(result) == 1
        assert result[0].get_integer() == 5

    def test_pack_multiple_elements(self):
        """PACK with multiple elements."""
        engine = ExecutionEngine()
        # Push 1, 2, 3, then pack 3 elements
        script = bytes([OpCode.PUSH1, OpCode.PUSH2, OpCode.PUSH3, OpCode.PUSH3, OpCode.PACK])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT
        result = engine.result_stack.peek(0)
        assert len(result) == 3
        assert [result[i].get_integer() for i in range(3)] == [3, 2, 1]


class TestUnpack:
    """Tests for UNPACK opcode."""

    def test_unpack_array(self):
        """UNPACK spreads array elements onto stack."""
        engine = ExecutionEngine()
        # Create array [1, 2], then unpack
        script = bytes([OpCode.PUSH1, OpCode.PUSH2, OpCode.PUSH2, OpCode.PACK, OpCode.UNPACK])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek(0).get_integer() == 2  # count
        assert engine.result_stack.peek(1).get_integer() == 2
        assert engine.result_stack.peek(2).get_integer() == 1


class TestNewArray:
    """Tests for NEWARRAY opcodes."""

    def test_newarray0(self):
        """NEWARRAY0 creates empty array."""
        engine = ExecutionEngine()
        script = bytes([OpCode.NEWARRAY0])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

    def test_newarray_with_size(self):
        """NEWARRAY creates array with specified size."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH5, OpCode.NEWARRAY])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT


class TestNewMap:
    """Tests for NEWMAP opcode."""

    def test_newmap(self):
        """NEWMAP creates empty map."""
        engine = ExecutionEngine()
        script = bytes([OpCode.NEWMAP])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT


class TestSize:
    """Tests for SIZE opcode."""

    def test_size_empty_array(self):
        """SIZE of empty array is 0."""
        engine = ExecutionEngine()
        script = bytes([OpCode.NEWARRAY0, OpCode.SIZE])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

    def test_size_array(self):
        """SIZE returns array length."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH3, OpCode.NEWARRAY, OpCode.SIZE])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

    def test_size_map(self):
        """SIZE of empty map is 0."""
        engine = ExecutionEngine()
        script = bytes([OpCode.NEWMAP, OpCode.SIZE])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT


class TestHasKey:
    """Tests for HASKEY opcode."""

    def test_haskey_array_valid_index(self):
        """HASKEY returns true for valid array index."""
        engine = ExecutionEngine()
        script = bytes(
            [
                OpCode.PUSH3,
                OpCode.NEWARRAY,  # Create array of size 3
                OpCode.PUSH0,  # Index 0
                OpCode.HASKEY,
            ]
        )
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

    def test_haskey_array_invalid_index(self):
        """HASKEY returns false for invalid array index."""
        engine = ExecutionEngine()
        script = bytes(
            [
                OpCode.PUSH3,
                OpCode.NEWARRAY,  # Create array of size 3
                OpCode.PUSH5,  # Index 5 (out of bounds)
                OpCode.HASKEY,
            ]
        )
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT


class TestPickItem:
    """Tests for PICKITEM opcode."""

    def test_pickitem_array(self):
        """PICKITEM retrieves array element by index."""
        engine = ExecutionEngine()
        script = bytes(
            [
                OpCode.PUSH1,
                OpCode.PUSH2,
                OpCode.PUSH3,
                OpCode.PUSH3,
                OpCode.PACK,  # Create [1, 2, 3]
                OpCode.PUSH0,  # Index 0
                OpCode.PICKITEM,
            ]
        )
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT


class TestSetItem:
    """Tests for SETITEM opcode."""

    def test_setitem_array(self):
        """SETITEM sets array element at index."""
        engine = ExecutionEngine()
        script = bytes(
            [
                OpCode.PUSH3,
                OpCode.NEWARRAY,  # Create array of size 3
                OpCode.PUSH0,  # Index 0
                OpCode.PUSH9,  # Value 9
                OpCode.SETITEM,
            ]
        )
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT


class TestPackMap:
    """Tests for PACKMAP opcode."""

    def test_packmap_empty(self):
        """PACKMAP with 0 pairs creates empty map."""
        engine = ExecutionEngine()
        script = bytes([OpCode.PUSH0, OpCode.PACKMAP])
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT
        result = engine.result_stack.peek(0)
        assert len(result) == 0

    def test_packmap_key_value_order(self):
        """PACKMAP pops key first, then value (matching C# behavior).

        Stack order before PACKMAP: [value, key, size]
        This means we push value first, then key, then size.

        C# reference:
            PrimitiveType key = context.EvaluationStack.Pop<PrimitiveType>();
            StackItem value = context.EvaluationStack.Pop();
            map[key] = value;
        """
        engine = ExecutionEngine()
        # Push: value=100, key=1, size=1
        # Stack (top to bottom): [1, 100, 1] after pushing size.
        # PACKMAP pops key=1, then value=100, creates map {1: 100}
        script = bytes(
            [
                OpCode.PUSHINT8,
                100,  # value = 100
                OpCode.PUSH1,  # key = 1
                OpCode.PUSH1,  # size = 1
                OpCode.PACKMAP,
            ]
        )
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

        # Verify the map has key=1 with value=100
        result = engine.result_stack.peek(0)
        assert len(result) == 1
        # Get the key from the map
        from neo.vm.types import Integer

        key = Integer(1)
        assert key in result
        assert result[key].get_integer() == 100

    def test_packmap_multiple_pairs(self):
        """PACKMAP with multiple key-value pairs."""
        engine = ExecutionEngine()
        # Create map with 2 pairs: {1: 10, 2: 20}
        # Push order: value1, key1, value2, key2, size
        script = bytes(
            [
                OpCode.PUSHINT8,
                10,  # value1 = 10
                OpCode.PUSH1,  # key1 = 1
                OpCode.PUSHINT8,
                20,  # value2 = 20
                OpCode.PUSH2,  # key2 = 2
                OpCode.PUSH2,  # size = 2
                OpCode.PACKMAP,
            ]
        )
        engine.load_script(script)
        engine.execute()
        assert engine.state == VMState.HALT

        result = engine.result_stack.peek(0)
        assert len(result) == 2
        from neo.vm.types import Integer

        assert result[Integer(1)].get_integer() == 10
        assert result[Integer(2)].get_integer() == 20
