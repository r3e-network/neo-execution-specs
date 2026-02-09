"""Tests for contract syscalls."""

from neo.smartcontract.syscalls import contract


class TestContractSyscalls:
    """Contract syscall tests."""
    
    def test_push_integer_small(self):
        """Test push integer for small values."""
        result = contract._push_integer(0)
        assert result[0] == 0x10  # PUSH0
        
        result = contract._push_integer(1)
        assert result[0] == 0x11  # PUSH1
        
        result = contract._push_integer(16)
        assert result[0] == 0x20  # PUSH16
    
    def test_push_integer_negative(self):
        """Test push integer for -1."""
        result = contract._push_integer(-1)
        assert result[0] == 0x0F  # PUSHM1
    
    def test_push_integer_large(self):
        """Test push integer for larger values."""
        from neo.vm.opcode import OpCode
        
        result = contract._push_integer(100)
        assert result[0] == OpCode.PUSHINT8
