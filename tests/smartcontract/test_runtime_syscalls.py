"""Tests for runtime syscalls."""

import pytest
from neo.smartcontract.syscalls import runtime


class TestRuntimeSyscalls:
    """Runtime syscall tests."""
    
    def test_platform_returns_neo(self):
        """Platform should return NEO."""
        from neo.vm.types import ByteString
        from unittest.mock import MagicMock
        
        engine = MagicMock()
        ctx = MagicMock()
        stack = MagicMock()
        ctx.evaluation_stack = stack
        engine.current_context = ctx
        
        pushed_value = None
        def capture_push(val):
            nonlocal pushed_value
            pushed_value = val
        stack.push = capture_push
        
        runtime.runtime_platform(engine)
        
        assert isinstance(pushed_value, ByteString)
        assert pushed_value.value == b"NEO"
    
    def test_get_trigger(self):
        """Get trigger should return trigger type."""
        from neo.vm.types import Integer
        from neo.smartcontract.trigger import TriggerType
        from unittest.mock import MagicMock
        
        engine = MagicMock()
        engine.trigger = TriggerType.APPLICATION
        ctx = MagicMock()
        stack = MagicMock()
        ctx.evaluation_stack = stack
        engine.current_context = ctx
        
        pushed_value = None
        def capture_push(val):
            nonlocal pushed_value
            pushed_value = val
        stack.push = capture_push
        
        runtime.runtime_get_trigger(engine)
        
        assert isinstance(pushed_value, Integer)
        assert pushed_value.get_integer() == int(TriggerType.APPLICATION)
    
    def test_gas_left(self):
        """Gas left should return remaining gas."""
        from neo.vm.types import Integer
        from unittest.mock import MagicMock
        
        engine = MagicMock()
        engine.gas_limit = 1000000
        engine.gas_consumed = 100000
        ctx = MagicMock()
        stack = MagicMock()
        ctx.evaluation_stack = stack
        engine.current_context = ctx
        
        pushed_value = None
        def capture_push(val):
            nonlocal pushed_value
            pushed_value = val
        stack.push = capture_push
        
        runtime.runtime_gas_left(engine)
        
        assert isinstance(pushed_value, Integer)
        assert pushed_value.get_integer() == 900000
