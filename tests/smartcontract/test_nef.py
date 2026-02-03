"""Tests for NEF file format."""

import pytest
from neo.smartcontract.nef_file import NefFile


class TestNefFile:
    """Tests for NefFile."""
    
    def test_create(self):
        """Test creating NEF file."""
        nef = NefFile()
        assert nef is not None
    
    def test_magic(self):
        """Test NEF magic number."""
        assert NefFile.MAGIC == 0x3346454E  # "NEF3"
    
    def test_has_script(self):
        """Test NEF has script attribute."""
        nef = NefFile()
        assert hasattr(nef, 'script')
