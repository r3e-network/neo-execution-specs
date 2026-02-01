"""Tests for BinaryWriter."""

import pytest
from neo.io.binary_writer import BinaryWriter


class TestBinaryWriter:
    """Tests for BinaryWriter."""
    
    def test_empty_writer(self):
        """Test empty writer."""
        w = BinaryWriter()
        assert w.to_bytes() == b""
        assert w.length == 0
    
    def test_write_byte(self):
        """Test writing single byte."""
        w = BinaryWriter()
        w.write_byte(0x42)
        assert w.to_bytes() == b"\x42"
    
    def test_write_uint32(self):
        """Test writing uint32."""
        w = BinaryWriter()
        w.write_uint32(0x12345678)
        assert w.to_bytes() == b"\x78\x56\x34\x12"
    
    def test_write_var_int_small(self):
        """Test writing small var int."""
        w = BinaryWriter()
        w.write_var_int(100)
        assert w.to_bytes() == b"\x64"
