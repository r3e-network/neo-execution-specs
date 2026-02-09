"""Boundary tests for VM operations."""

from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.opcode import OpCode
from neo.vm.script_builder import ScriptBuilder


class TestIntegerBoundaries:
    """Test integer operation boundaries."""
    
    def test_add_overflow_protection(self):
        """Test that large additions are handled."""
        sb = ScriptBuilder()
        sb.emit_push(2**200)
        sb.emit_push(2**200)
        sb.emit(OpCode.ADD)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_array())
        engine.execute()
        
        assert engine.state == VMState.HALT
        result = engine.result_stack.pop()
        assert result.get_integer() == 2**201
    
    def test_mul_large_numbers(self):
        """Test multiplication of large numbers."""
        sb = ScriptBuilder()
        sb.emit_push(2**100)
        sb.emit_push(2**100)
        sb.emit(OpCode.MUL)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_array())
        engine.execute()
        
        assert engine.state == VMState.HALT
        result = engine.result_stack.pop()
        assert result.get_integer() == 2**200
    
    def test_div_by_zero(self):
        """Test division by zero faults."""
        sb = ScriptBuilder()
        sb.emit_push(100)
        sb.emit_push(0)
        sb.emit(OpCode.DIV)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_array())
        engine.execute()
        
        assert engine.state == VMState.FAULT
    
    def test_mod_by_zero(self):
        """Test modulo by zero faults."""
        sb = ScriptBuilder()
        sb.emit_push(100)
        sb.emit_push(0)
        sb.emit(OpCode.MOD)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_array())
        engine.execute()
        
        assert engine.state == VMState.FAULT
    
    def test_negative_shift(self):
        """Test negative shift amount."""
        sb = ScriptBuilder()
        sb.emit_push(100)
        sb.emit_push(-1)
        sb.emit(OpCode.SHL)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_array())
        engine.execute()
        
        # Negative shift should fault
        assert engine.state == VMState.FAULT


class TestStackBoundaries:
    """Test stack operation boundaries."""
    
    def test_empty_stack_pop(self):
        """Test popping from empty stack faults."""
        sb = ScriptBuilder()
        sb.emit(OpCode.DROP)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_array())
        engine.execute()
        
        assert engine.state == VMState.FAULT
    
    def test_pick_out_of_range(self):
        """Test PICK with out of range index."""
        sb = ScriptBuilder()
        sb.emit_push(1)
        sb.emit_push(10)  # Index 10, but only 1 item
        sb.emit(OpCode.PICK)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_array())
        engine.execute()
        
        assert engine.state == VMState.FAULT
    
    def test_roll_out_of_range(self):
        """Test ROLL with out of range index."""
        sb = ScriptBuilder()
        sb.emit_push(1)
        sb.emit_push(10)
        sb.emit(OpCode.ROLL)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_array())
        engine.execute()
        
        assert engine.state == VMState.FAULT


class TestArrayBoundaries:
    """Test array operation boundaries."""
    
    def test_pickitem_negative_index(self):
        """Test PICKITEM with negative index."""
        sb = ScriptBuilder()
        sb.emit_push(0)
        sb.emit(OpCode.NEWARRAY)
        sb.emit_push(-1)
        sb.emit(OpCode.PICKITEM)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_array())
        engine.execute()
        
        assert engine.state == VMState.FAULT
    
    def test_setitem_out_of_range(self):
        """Test SETITEM with out of range index."""
        sb = ScriptBuilder()
        sb.emit_push(1)
        sb.emit(OpCode.NEWARRAY)
        sb.emit_push(10)  # Index 10, but array size is 1
        sb.emit_push(42)
        sb.emit(OpCode.SETITEM)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_array())
        engine.execute()
        
        assert engine.state == VMState.FAULT


class TestBufferBoundaries:
    """Test buffer operation boundaries."""
    
    def test_newbuffer_negative_size(self):
        """Test NEWBUFFER with negative size."""
        sb = ScriptBuilder()
        sb.emit_push(-1)
        sb.emit(OpCode.NEWBUFFER)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_array())
        engine.execute()
        
        assert engine.state == VMState.FAULT
    
    def test_substr_negative_index(self):
        """Test SUBSTR with negative index."""
        sb = ScriptBuilder()
        sb.emit_push(b"hello")
        sb.emit_push(-1)
        sb.emit_push(2)
        sb.emit(OpCode.SUBSTR)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_array())
        engine.execute()
        
        assert engine.state == VMState.FAULT
    
    def test_left_negative_count(self):
        """Test LEFT with negative count."""
        sb = ScriptBuilder()
        sb.emit_push(b"hello")
        sb.emit_push(-1)
        sb.emit(OpCode.LEFT)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_array())
        engine.execute()
        
        assert engine.state == VMState.FAULT
