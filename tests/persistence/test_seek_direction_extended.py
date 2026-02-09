"""Tests for seek direction."""

from neo.persistence.seek_direction import SeekDirection


class TestSeekDirection:
    """Seek direction tests."""
    
    def test_forward(self):
        """Test FORWARD direction."""
        assert SeekDirection.FORWARD is not None
    
    def test_backward(self):
        """Test BACKWARD direction."""
        assert SeekDirection.BACKWARD is not None
