"""Tests for NEF (Neo Executable Format) module."""

import pytest
from neo.contract.nef import (
    NefFile,
    MethodToken,
    NEF_MAGIC,
    write_var_int,
    write_var_bytes,
)


class TestNefMagic:
    """Tests for NEF magic number."""
    
    def test_magic_value(self):
        """Test NEF magic number value."""
        assert NEF_MAGIC == 0x3346454E
    
    def test_magic_string(self):
        """Test NEF magic as string."""
        # "NEF3" in little-endian
        magic_bytes = NEF_MAGIC.to_bytes(4, 'little')
        assert magic_bytes == b'NEF3'


class TestWriteVarInt:
    """Tests for write_var_int function."""
    
    def test_small_value(self):
        """Test small value (< 0xFD)."""
        assert write_var_int(0) == b'\x00'
        assert write_var_int(100) == b'\x64'
        assert write_var_int(0xFC) == b'\xfc'
    
    def test_two_byte_value(self):
        """Test two-byte value."""
        result = write_var_int(0xFD)
        assert result[0] == 0xFD
        assert len(result) == 3
    
    def test_four_byte_value(self):
        """Test four-byte value."""
        result = write_var_int(0x10000)
        assert result[0] == 0xFE
        assert len(result) == 5


class TestWriteVarBytes:
    """Tests for write_var_bytes function."""
    
    def test_empty(self):
        """Test empty bytes."""
        assert write_var_bytes(b'') == b'\x00'
    
    def test_small(self):
        """Test small bytes."""
        result = write_var_bytes(b'hello')
        assert result[0] == 5
        assert result[1:] == b'hello'


class TestMethodToken:
    """Tests for MethodToken class."""
    
    def test_creation(self):
        """Test method token creation."""
        token = MethodToken(
            hash=b'\x00' * 20,
            method="transfer",
            parameters_count=3,
            has_return_value=True,
            call_flags=0x0F
        )
        assert token.method == "transfer"
        assert token.parameters_count == 3
    
    def test_serialize(self):
        """Test method token serialization."""
        token = MethodToken(
            hash=b'\x00' * 20,
            method="test",
            parameters_count=1,
            has_return_value=False,
            call_flags=0x01
        )
        data = token.serialize()
        assert len(data) > 20


class TestNefFile:
    """Tests for NefFile class."""
    
    def test_creation_basic(self):
        """Test basic NEF file creation."""
        nef = NefFile(
            compiler="test-compiler",
            script=b'\x10\x40'
        )
        assert nef.compiler == "test-compiler"
        assert nef.script == b'\x10\x40'
    
    def test_compiler_too_long(self):
        """Test compiler name too long."""
        with pytest.raises(ValueError, match="too long"):
            NefFile(compiler="x" * 65)
    
    def test_script_hash(self):
        """Test script hash property."""
        nef = NefFile(script=b'\x10\x40')
        hash_val = nef.script_hash
        assert len(hash_val) == 20
    
    def test_compute_checksum(self):
        """Test checksum computation."""
        nef = NefFile(script=b'\x10\x40')
        checksum = nef.compute_checksum()
        assert isinstance(checksum, int)
    
    def test_serialize(self):
        """Test NEF serialization."""
        nef = NefFile(
            compiler="test",
            script=b'\x10\x40'
        )
        data = nef.serialize()
        # Check magic
        assert data[:4] == b'NEF3'
    
    def test_default_values(self):
        """Test default values."""
        nef = NefFile()
        assert nef.compiler == "neo-core-v3.0"
        assert nef.source == ""
        assert nef.tokens == []
        assert nef.script == b""
