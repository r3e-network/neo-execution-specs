"""Tests for trigger type."""

import pytest
from neo.smartcontract.trigger import TriggerType


class TestTriggerType:
    """Trigger type tests."""
    
    def test_application(self):
        """Test APPLICATION trigger."""
        assert TriggerType.APPLICATION != 0
    
    def test_verification(self):
        """Test VERIFICATION trigger."""
        assert TriggerType.VERIFICATION != 0
