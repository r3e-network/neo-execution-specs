"""Tests for IO module."""

from neo.io.binary_reader import BinaryReader
from neo.io.binary_writer import BinaryWriter


class TestBinaryReaderWriter:
    """Binary reader/writer tests."""
    
    def test_write_read_byte(self):
        """Test byte write/read."""
        writer = BinaryWriter()
        writer.write_byte(0x42)
        
        reader = BinaryReader(writer.to_bytes())
        assert reader.read_byte() == 0x42
    
    def test_write_read_uint16(self):
        """Test uint16 write/read."""
        writer = BinaryWriter()
        writer.write_uint16(0x1234)
        
        reader = BinaryReader(writer.to_bytes())
        assert reader.read_uint16() == 0x1234
    
    def test_write_read_uint32(self):
        """Test uint32 write/read."""
        writer = BinaryWriter()
        writer.write_uint32(0x12345678)
        
        reader = BinaryReader(writer.to_bytes())
        assert reader.read_uint32() == 0x12345678
    
    def test_write_read_int64(self):
        """Test int64 write/read."""
        writer = BinaryWriter()
        writer.write_int64(-12345678)
        
        reader = BinaryReader(writer.to_bytes())
        assert reader.read_int64() == -12345678
    
    def test_write_read_var_int(self):
        """Test var_int write/read."""
        writer = BinaryWriter()
        writer.write_var_int(100)
        writer.write_var_int(1000)
        writer.write_var_int(100000)
        
        reader = BinaryReader(writer.to_bytes())
        assert reader.read_var_int() == 100
        assert reader.read_var_int() == 1000
        assert reader.read_var_int() == 100000
    
    def test_write_read_var_bytes(self):
        """Test var_bytes write/read."""
        writer = BinaryWriter()
        writer.write_var_bytes(b"hello world")
        
        reader = BinaryReader(writer.to_bytes())
        assert reader.read_var_bytes() == b"hello world"
