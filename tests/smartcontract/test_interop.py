"""Tests for InteropDescriptor."""

import pytest
from neo.smartcontract.interop_descriptor import InteropDescriptor


def test_interop():
    """Test interop descriptor."""
    desc = InteropDescriptor(name="test", hash=123, handler=lambda: None)
    assert desc.name == "test"
