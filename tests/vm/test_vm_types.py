"""Tests for VM types."""

from neo.vm.types import (
    Integer, ByteString, Boolean, Array, 
    Map, Null
)


class TestInteger:
    """Tests for Integer type."""
    
    def test_create(self):
        """Test creating integer."""
        i = Integer(42)
        assert i.get_integer() == 42
    
    def test_zero(self):
        """Test zero integer."""
        i = Integer(0)
        assert i.get_integer() == 0
    
    def test_negative(self):
        """Test negative integer."""
        i = Integer(-100)
        assert i.get_integer() == -100
    
    def test_value_property(self):
        """Test value property."""
        i = Integer(42)
        assert i.value == 42


class TestByteString:
    """Tests for ByteString type."""
    
    def test_create(self):
        """Test creating byte string."""
        bs = ByteString(b"hello")
        assert bs.value == b"hello"
    
    def test_empty(self):
        """Test empty byte string."""
        bs = ByteString(b"")
        assert bs.value == b""


class TestBoolean:
    """Tests for Boolean type."""
    
    def test_true(self):
        """Test true boolean."""
        b = Boolean(True)
        assert b.get_boolean()
    
    def test_false(self):
        """Test false boolean."""
        b = Boolean(False)
        assert not b.get_boolean()


class TestArray:
    """Tests for Array type."""
    
    def test_create_empty(self):
        """Test creating empty array."""
        arr = Array()
        assert len(arr) == 0
    
    def test_append(self):
        """Test appending to array."""
        arr = Array()
        arr.append(Integer(1))
        assert len(arr) == 1


class TestMap:
    """Tests for Map type."""
    
    def test_create_empty(self):
        """Test creating empty map."""
        m = Map()
        assert len(m) == 0


class TestNull:
    """Tests for Null type."""
    
    def test_create(self):
        """Test creating null."""
        n = Null()
        assert n is not None
