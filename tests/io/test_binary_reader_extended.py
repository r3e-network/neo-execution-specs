"""Tests for BinaryReader extended."""

from neo.io.binary_reader import BinaryReader


class TestBinaryReaderExtended:
    """Extended BinaryReader tests."""
    
    def test_read_var_int_small(self):
        """Test reading small var int."""
        r = BinaryReader(bytes([0x10]))
        assert r.read_var_int() == 0x10
    
    def test_read_var_int_fd(self):
        """Test reading 2-byte var int."""
        r = BinaryReader(bytes([0xFD, 0x00, 0x01]))
        assert r.read_var_int() == 256
