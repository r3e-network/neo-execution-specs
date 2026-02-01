"""Tests for BinaryReader."""

import pytest
from neo.io.binary_reader import BinaryReader


class TestBinaryReader:
    """Tests for BinaryReader."""
    
    def test_read_byte(self):
        """Test reading single byte."""
        r = BinaryReader(b"\x42")
        assert r.read_byte() == 0x42
    
    def test_read_uint32(self):
        """Test reading uint32."""
        r = BinaryReader(b"\x78\x56\x34\x12")
        assert r.read_uint32() == 0x12345678
    
    def test_position(self):
        """Test position tracking."""
        r = BinaryReader(b"\x01\x02\x03")
        assert r.position == 0
        r.read_byte()
        assert r.position == 1
    
    def test_remaining(self):
        """Test remaining bytes."""
        r = BinaryReader(b"\x01\x02\x03")
        assert r.remaining == 3
        r.read_byte()
        assert r.remaining == 2
