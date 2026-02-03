"""Tests for IO serialization."""

import pytest
from neo.io.binary_reader import BinaryReader
from neo.io.binary_writer import BinaryWriter


class TestBinaryWriter:
    """Tests for BinaryWriter."""
    
    def test_write_byte(self):
        """Test writing single byte."""
        writer = BinaryWriter()
        writer.write_byte(0x42)
        assert writer.to_bytes() == b'\x42'
    
    def test_write_bytes(self):
        """Test writing bytes."""
        writer = BinaryWriter()
        writer.write_bytes(b'\x01\x02\x03')
        assert writer.to_bytes() == b'\x01\x02\x03'
    
    def test_write_uint16(self):
        """Test writing uint16."""
        writer = BinaryWriter()
        writer.write_uint16(0x1234)
        assert writer.to_bytes() == b'\x34\x12'
    
    def test_write_uint32(self):
        """Test writing uint32."""
        writer = BinaryWriter()
        writer.write_uint32(0x12345678)
        assert writer.to_bytes() == b'\x78\x56\x34\x12'
    
    def test_write_uint64(self):
        """Test writing uint64."""
        writer = BinaryWriter()
        writer.write_uint64(0x123456789ABCDEF0)
        result = writer.to_bytes()
        assert len(result) == 8
    
    def test_write_var_int(self):
        """Test writing variable length integer."""
        writer = BinaryWriter()
        writer.write_var_int(100)
        assert writer.to_bytes()[0] == 100


class TestBinaryReader:
    """Tests for BinaryReader."""
    
    def test_read_byte(self):
        """Test reading single byte."""
        reader = BinaryReader(b'\x42')
        assert reader.read_byte() == 0x42
    
    def test_read_bytes(self):
        """Test reading bytes."""
        reader = BinaryReader(b'\x01\x02\x03')
        assert reader.read_bytes(3) == b'\x01\x02\x03'
    
    def test_read_uint16(self):
        """Test reading uint16."""
        reader = BinaryReader(b'\x34\x12')
        assert reader.read_uint16() == 0x1234
    
    def test_read_uint32(self):
        """Test reading uint32."""
        reader = BinaryReader(b'\x78\x56\x34\x12')
        assert reader.read_uint32() == 0x12345678
