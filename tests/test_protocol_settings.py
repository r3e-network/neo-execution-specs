"""Tests for protocol settings."""

import pytest
from neo.protocol_settings import ProtocolSettings


class TestProtocolSettings:
    """Tests for ProtocolSettings."""
    
    def test_default_settings(self):
        """Test default protocol settings."""
        settings = ProtocolSettings()
        assert settings is not None
