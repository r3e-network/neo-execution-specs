"""Tests for ProtocolSettings."""

from neo.protocol_settings import ProtocolSettings


class TestProtocolSettingsExtended:
    """Test ProtocolSettings."""
    
    def test_create(self):
        """Test create settings."""
        ps = ProtocolSettings()
        assert ps is not None
