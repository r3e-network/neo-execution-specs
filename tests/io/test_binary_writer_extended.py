"""Tests for BinaryWriter extended."""

from neo.io.binary_writer import BinaryWriter


class TestBinaryWriterExtended:
    """Extended BinaryWriter tests."""
    
    def test_write_var_int_small(self):
        """Test writing small var int."""
        w = BinaryWriter()
        w.write_var_int(0x10)
        assert w.to_bytes() == bytes([0x10])
    
    def test_write_var_int_fd(self):
        """Test writing 2-byte var int."""
        w = BinaryWriter()
        w.write_var_int(256)
        assert w.to_bytes() == bytes([0xFD, 0x00, 0x01])
