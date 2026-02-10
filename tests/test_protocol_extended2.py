"""Tests for protocol settings."""

from neo.protocol_settings import ProtocolSettings


class TestProtocolSettings:
    """Protocol settings tests."""
    
    def test_default_network(self):
        """Test default network."""
        settings = ProtocolSettings()
        assert settings.network is not None
    
    def test_has_network_attribute(self):
        """Test network attribute exists."""
        settings = ProtocolSettings()
        assert hasattr(settings, 'network')
