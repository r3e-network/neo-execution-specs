"""Tests for hardfork module."""

from neo.hardfork import Hardfork


class TestHardfork:
    """Hardfork tests."""
    
    def test_hardfork_enum(self):
        """Test hardfork enum exists."""
        assert hasattr(Hardfork, 'HF_ASPIDOCHELONE')
    
    def test_hardfork_values(self):
        """Test hardfork has values."""
        values = list(Hardfork)
        assert len(values) > 0
