"""Tests for Murmur hash."""

import pytest
from neo.crypto.murmur import murmur32


def test_murmur32_empty():
    """Test murmur32 with empty input."""
    result = murmur32(b"", 0)
    assert isinstance(result, int)


def test_murmur32_hello():
    """Test murmur32 with hello."""
    result = murmur32(b"hello", 0)
    assert result == 0x248bfa47
