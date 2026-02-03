"""Tests for ApplicationEngine."""

import pytest
from neo.smartcontract.application_engine import (
    ApplicationEngine, TriggerType, VMState, ExecutionContext
)


class TestApplicationEngine:
    """ApplicationEngine tests."""
    
    def test_create(self):
        """Test engine creation."""
        engine = ApplicationEngine()
        assert engine.trigger == TriggerType.APPLICATION
        assert engine.state == VMState.NONE
    
    def test_load_script(self):
        """Test script loading."""
        engine = ApplicationEngine()
        engine.load_script(bytes([0x10, 0x40]))
        assert engine.current_context is not None
    
    def test_execute_empty(self):
        """Test empty execution."""
        engine = ApplicationEngine()
        state = engine.execute()
        assert state == VMState.HALT
