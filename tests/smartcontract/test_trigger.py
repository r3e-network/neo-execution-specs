"""Tests for TriggerType."""

import pytest
from neo.smartcontract.trigger import TriggerType


class TestTriggerType:
    """Test TriggerType."""
    
    def test_application(self):
        """Test APPLICATION trigger."""
        assert TriggerType.APPLICATION.value == 0x40
