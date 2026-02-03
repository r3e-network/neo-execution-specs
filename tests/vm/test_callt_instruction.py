"""Tests for CALLT instruction."""

import pytest
from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.opcode import OpCode
from neo.vm.script_builder import ScriptBuilder


class TestCalltInstruction:
    """Test CALLT instruction."""
    
    def test_callt_without_handler_raises(self):
        """Test CALLT without token handler raises exception."""
        sb = ScriptBuilder()
        sb.emit_callt(0)  # Token index 0
        script = sb.to_array()
        
        engine = ExecutionEngine()
        engine.load_script(script)
        engine.execute()
        
        # Should fault because no token handler
        assert engine.state == VMState.FAULT
    
    def test_callt_with_handler(self):
        """Test CALLT with token handler."""
        sb = ScriptBuilder()
        sb.emit_callt(5)  # Token index 5
        script = sb.to_array()
        
        engine = ExecutionEngine()
        
        # Track handler calls
        handler_calls = []
        
        def mock_handler(eng, token_idx):
            handler_calls.append(token_idx)
        
        engine.token_handler = mock_handler
        engine.load_script(script)
        engine.execute()
        
        # Handler should have been called with token index 5
        assert handler_calls == [5]
    
    def test_callt_token_index_parsing(self):
        """Test CALLT parses 2-byte token index correctly."""
        sb = ScriptBuilder()
        sb.emit_callt(258)  # 0x0102 in little-endian
        script = sb.to_array()
        
        engine = ExecutionEngine()
        
        handler_calls = []
        
        def mock_handler(eng, token_idx):
            handler_calls.append(token_idx)
        
        engine.token_handler = mock_handler
        engine.load_script(script)
        engine.execute()
        
        assert handler_calls == [258]
    
    def test_callt_max_token_index(self):
        """Test CALLT with maximum token index (65535)."""
        sb = ScriptBuilder()
        sb.emit_callt(65535)
        script = sb.to_array()
        
        engine = ExecutionEngine()
        
        handler_calls = []
        
        def mock_handler(eng, token_idx):
            handler_calls.append(token_idx)
        
        engine.token_handler = mock_handler
        engine.load_script(script)
        engine.execute()
        
        assert handler_calls == [65535]


class TestCalltInApplicationEngine:
    """Test CALLT in ApplicationEngine context."""
    
    def test_callt_invalid_token_index(self):
        """Test CALLT with invalid token index faults."""
        from neo.smartcontract.application_engine import ApplicationEngine
        
        sb = ScriptBuilder()
        sb.emit_callt(0)
        script = sb.to_array()
        
        engine = ApplicationEngine()
        engine.load_script(script)
        engine.execute()
        
        # Should fault - no tokens loaded
        assert engine.state == VMState.FAULT
    
    def test_callt_with_tokens(self):
        """Test CALLT with method tokens loaded."""
        from neo.smartcontract.application_engine import ApplicationEngine
        from neo.smartcontract.nef_file import MethodToken
        
        # Create a method token
        token = MethodToken(
            hash=bytes(20),  # Null contract hash
            method="test",
            parameters_count=0,
            has_return_value=False,
            call_flags=0x0F  # All flags
        )
        
        sb = ScriptBuilder()
        sb.emit_callt(0)
        script = sb.to_array()
        
        engine = ApplicationEngine()
        engine.load_script_with_tokens(script, [token])
        engine.execute()
        
        # Will fault because contract not found, but token was resolved
        assert engine.state == VMState.FAULT
