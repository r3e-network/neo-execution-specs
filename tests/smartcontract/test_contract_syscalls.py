"""Tests for contract syscalls."""

import pytest
from neo.smartcontract.call_flags import CallFlags


class TestCallFlags:
    """Tests for CallFlags enum."""
    
    def test_none_flag(self):
        """Test NONE flag value."""
        assert CallFlags.NONE == 0
    
    def test_read_states_flag(self):
        """Test READ_STATES flag value."""
        assert CallFlags.READ_STATES == 0b00000001
    
    def test_write_states_flag(self):
        """Test WRITE_STATES flag value."""
        assert CallFlags.WRITE_STATES == 0b00000010
    
    def test_allow_call_flag(self):
        """Test ALLOW_CALL flag value."""
        assert CallFlags.ALLOW_CALL == 0b00000100
    
    def test_allow_notify_flag(self):
        """Test ALLOW_NOTIFY flag value."""
        assert CallFlags.ALLOW_NOTIFY == 0b00001000
    
    def test_states_combination(self):
        """Test STATES is READ_STATES | WRITE_STATES."""
        assert CallFlags.STATES == (CallFlags.READ_STATES | CallFlags.WRITE_STATES)
    
    def test_read_only_combination(self):
        """Test READ_ONLY is READ_STATES | ALLOW_CALL."""
        assert CallFlags.READ_ONLY == (CallFlags.READ_STATES | CallFlags.ALLOW_CALL)
    
    def test_all_combination(self):
        """Test ALL includes all flags."""
        assert CallFlags.ALL == (
            CallFlags.STATES | CallFlags.ALLOW_CALL | CallFlags.ALLOW_NOTIFY
        )


class TestContractHelpers:
    """Tests for contract helper functions."""
    
    def test_push_integer_small(self):
        """Test pushing small integers."""
        from neo.smartcontract.syscalls.contract import _push_integer
        from neo.vm.opcode import OpCode
        
        # Push 0
        result = _push_integer(0)
        assert result == bytes([OpCode.PUSH0])
        
        # Push 1
        result = _push_integer(1)
        assert result == bytes([OpCode.PUSH1])
        
        # Push 16
        result = _push_integer(16)
        assert result == bytes([OpCode.PUSH16])
    
    def test_push_integer_negative_one(self):
        """Test pushing -1."""
        from neo.smartcontract.syscalls.contract import _push_integer
        from neo.vm.opcode import OpCode
        
        result = _push_integer(-1)
        assert result == bytes([OpCode.PUSHM1])
    
    def test_push_integer_large(self):
        """Test pushing larger integers."""
        from neo.smartcontract.syscalls.contract import _push_integer
        from neo.vm.opcode import OpCode
        
        # Push 17 (needs PUSHINT8)
        result = _push_integer(17)
        assert result[0] == OpCode.PUSHINT8
        assert result[1] == 17
