"""Tests for Hardfork."""

from neo.hardfork import Hardfork


class TestHardfork:
    """Test Hardfork enum."""
    
    def test_hardfork_exists(self):
        """Test Hardfork enum exists."""
        assert Hardfork is not None
