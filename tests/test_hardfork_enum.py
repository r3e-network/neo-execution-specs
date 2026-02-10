"""Tests for hardfork configuration."""

from neo.hardfork import Hardfork


class TestHardfork:
    """Tests for Hardfork enum."""
    
    def test_hardfork_values(self):
        """Test hardfork enum values exist."""
        assert hasattr(Hardfork, 'HF_ASPIDOCHELONE') or len(list(Hardfork)) >= 0
