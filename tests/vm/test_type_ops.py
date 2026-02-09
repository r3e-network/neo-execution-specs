"""Tests for type instructions (ISNULL, ISTYPE, CONVERT)."""

import pytest
from neo.vm.types import (
    Integer, Boolean, ByteString, StackItemType, NULL,
)
from neo.vm.instructions.types import (
    isnull, istype, convert, abortmsg, assertmsg,
)


class MockInstruction:
    """Mock instruction for testing."""
    def __init__(self, operand: bytes = b''):
        self.operand = operand


class MockEngine:
    """Mock engine for testing."""
    def __init__(self):
        self._stack = []
        self.reference_counter = None
    
    def pop(self):
        return self._stack.pop()
    
    def push(self, item):
        self._stack.append(item)


class TestIsNull:
    """Tests for ISNULL instruction."""
    
    def test_isnull_with_null(self):
        """Test ISNULL with null value."""
        engine = MockEngine()
        engine.push(NULL)
        isnull(engine, MockInstruction())
        assert engine.pop().get_boolean() is True
    
    def test_isnull_with_integer(self):
        """Test ISNULL with integer."""
        engine = MockEngine()
        engine.push(Integer(42))
        isnull(engine, MockInstruction())
        assert engine.pop().get_boolean() is False
    
    def test_isnull_with_zero(self):
        """Test ISNULL with zero (not null)."""
        engine = MockEngine()
        engine.push(Integer(0))
        isnull(engine, MockInstruction())
        assert engine.pop().get_boolean() is False


class TestIsType:
    """Tests for ISTYPE instruction."""
    
    def test_istype_integer(self):
        """Test ISTYPE with integer."""
        engine = MockEngine()
        engine.push(Integer(42))
        istype(engine, MockInstruction(bytes([StackItemType.INTEGER])))
        assert engine.pop().get_boolean() is True
    
    def test_istype_boolean(self):
        """Test ISTYPE with boolean."""
        engine = MockEngine()
        engine.push(Boolean(True))
        istype(engine, MockInstruction(bytes([StackItemType.BOOLEAN])))
        assert engine.pop().get_boolean() is True
    
    def test_istype_mismatch(self):
        """Test ISTYPE with type mismatch."""
        engine = MockEngine()
        engine.push(Integer(42))
        istype(engine, MockInstruction(bytes([StackItemType.BOOLEAN])))
        assert engine.pop().get_boolean() is False
    
    def test_istype_any_invalid(self):
        """Test ISTYPE with ANY type (invalid)."""
        engine = MockEngine()
        engine.push(Integer(42))
        with pytest.raises(Exception, match="Invalid type"):
            istype(engine, MockInstruction(bytes([StackItemType.ANY])))


class TestConvert:
    """Tests for CONVERT instruction."""
    
    def test_convert_to_boolean_true(self):
        """Test converting integer to boolean (true)."""
        engine = MockEngine()
        engine.push(Integer(42))
        convert(engine, MockInstruction(bytes([StackItemType.BOOLEAN])))
        result = engine.pop()
        assert isinstance(result, Boolean)
        assert result.get_boolean() is True
    
    def test_convert_to_boolean_false(self):
        """Test converting zero to boolean (false)."""
        engine = MockEngine()
        engine.push(Integer(0))
        convert(engine, MockInstruction(bytes([StackItemType.BOOLEAN])))
        result = engine.pop()
        assert isinstance(result, Boolean)
        assert result.get_boolean() is False
    
    def test_convert_to_integer(self):
        """Test converting boolean to integer."""
        engine = MockEngine()
        engine.push(Boolean(True))
        convert(engine, MockInstruction(bytes([StackItemType.INTEGER])))
        result = engine.pop()
        assert isinstance(result, Integer)
        assert result.get_integer() == 1
    
    def test_convert_same_type(self):
        """Test converting to same type returns same item."""
        engine = MockEngine()
        original = Integer(42)
        engine.push(original)
        convert(engine, MockInstruction(bytes([StackItemType.INTEGER])))
        result = engine.pop()
        assert result is original


class TestAbortMsg:
    """Tests for ABORTMSG instruction."""
    
    def test_abortmsg(self):
        """Test ABORTMSG throws with message."""
        engine = MockEngine()
        engine.push(ByteString(b'Test error'))
        with pytest.raises(Exception, match="ABORTMSG.*Test error"):
            abortmsg(engine, MockInstruction())


class TestAssertMsg:
    """Tests for ASSERTMSG instruction."""
    
    def test_assertmsg_true(self):
        """Test ASSERTMSG with true condition."""
        engine = MockEngine()
        engine.push(Boolean(True))
        engine.push(ByteString(b'Should not fail'))
        assertmsg(engine, MockInstruction())
        # Should not raise
    
    def test_assertmsg_false(self):
        """Test ASSERTMSG with false condition."""
        engine = MockEngine()
        engine.push(Boolean(False))
        engine.push(ByteString(b'Assertion failed'))
        with pytest.raises(Exception, match="ASSERTMSG.*Assertion failed"):
            assertmsg(engine, MockInstruction())
