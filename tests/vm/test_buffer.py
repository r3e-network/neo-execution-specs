"""Tests for Buffer type."""

import pytest
from neo.vm.types import Buffer


class TestBuffer:
    """Buffer type tests."""
    
    def test_create_empty(self):
        """Test creating empty buffer."""
        buf = Buffer(0)
        assert len(buf) == 0
    
    def test_create_with_size(self):
        """Test creating buffer with size."""
        buf = Buffer(10)
        assert len(buf) == 10
        assert all(b == 0 for b in buf.value)
    
    def test_create_from_bytes(self):
        """Test creating buffer from bytes."""
        buf = Buffer(b'\x01\x02\x03')
        assert len(buf) == 3
        assert buf[0] == 1
        assert buf[1] == 2
        assert buf[2] == 3
    
    def test_setitem(self):
        """Test setting byte at index."""
        buf = Buffer(3)
        buf[0] = 0xFF
        assert buf[0] == 0xFF
    
    def test_reverse(self):
        """Test reverse method."""
        buf = Buffer(b'\x01\x02\x03\x04')
        buf.reverse()
        assert buf[0] == 4
        assert buf[1] == 3
        assert buf[2] == 2
        assert buf[3] == 1
    
    def test_reverse_empty(self):
        """Test reverse on empty buffer."""
        buf = Buffer(0)
        buf.reverse()  # Should not raise
        assert len(buf) == 0
    
    def test_reverse_single(self):
        """Test reverse on single byte buffer."""
        buf = Buffer(b'\x42')
        buf.reverse()
        assert buf[0] == 0x42
    
    def test_get_span(self):
        """Test get_span returns bytes."""
        buf = Buffer(b'\x01\x02\x03')
        span = buf.get_span()
        assert span == b'\x01\x02\x03'
        assert isinstance(span, bytes)
