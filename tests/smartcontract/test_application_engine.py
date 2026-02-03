"""Tests for ApplicationEngine."""

import pytest
from neo.smartcontract.application_engine import (
    ApplicationEngine,
    GasCost,
    Notification,
    LogEntry,
)
from neo.smartcontract.trigger import TriggerType
from neo.vm.execution_engine import VMState
from neo.vm.opcode import OpCode
from neo.vm.script_builder import ScriptBuilder


class TestApplicationEngineBasics:
    """Test basic ApplicationEngine functionality."""
    
    def test_create_engine(self):
        """Test creating an application engine."""
        engine = ApplicationEngine()
        assert engine.trigger == TriggerType.APPLICATION
        assert engine.gas_consumed == 0
        assert engine.state == VMState.NONE
    
    def test_gas_consumption(self):
        """Test gas consumption tracking."""
        engine = ApplicationEngine(gas_limit=1000)
        engine.add_gas(100)
        assert engine.gas_consumed == 100
        engine.add_gas(200)
        assert engine.gas_consumed == 300
    
    def test_gas_limit_exceeded(self):
        """Test gas limit enforcement."""
        engine = ApplicationEngine(gas_limit=100)
        with pytest.raises(Exception, match="Out of gas"):
            engine.add_gas(200)
    
    def test_trigger_types(self):
        """Test different trigger types."""
        engine = ApplicationEngine(trigger=TriggerType.VERIFICATION)
        assert engine.trigger == TriggerType.VERIFICATION
        
        engine = ApplicationEngine(trigger=TriggerType.SYSTEM)
        assert engine.trigger == TriggerType.SYSTEM
    
    def test_network_magic(self):
        """Test network magic number."""
        engine = ApplicationEngine(network=12345)
        assert engine.network == 12345


class TestApplicationEngineExecution:
    """Test script execution in ApplicationEngine."""
    
    def test_simple_script(self):
        """Test executing a simple script."""
        sb = ScriptBuilder()
        sb.emit_push(42)
        script = sb.to_bytes()
        
        engine = ApplicationEngine.run(script)
        assert engine.state == VMState.HALT
        assert len(engine.result_stack) == 1
        assert engine.result_stack.peek().get_integer() == 42
    
    def test_arithmetic_script(self):
        """Test arithmetic operations."""
        sb = ScriptBuilder()
        sb.emit_push(10)
        sb.emit_push(20)
        sb.emit(OpCode.ADD)
        script = sb.to_bytes()
        
        engine = ApplicationEngine.run(script)
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 30
    
    def test_multiple_operations(self):
        """Test multiple operations."""
        sb = ScriptBuilder()
        sb.emit_push(5)
        sb.emit_push(3)
        sb.emit(OpCode.MUL)
        sb.emit_push(2)
        sb.emit(OpCode.ADD)
        script = sb.to_bytes()
        
        engine = ApplicationEngine.run(script)
        assert engine.state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 17


class TestApplicationEngineNotifications:
    """Test notification system."""
    
    def test_notifications_list(self):
        """Test notifications list initialization."""
        engine = ApplicationEngine()
        assert engine.notifications == []
    
    def test_logs_list(self):
        """Test logs list initialization."""
        engine = ApplicationEngine()
        assert engine.logs == []


class TestGasCost:
    """Test gas cost constants."""
    
    def test_base_cost(self):
        """Test base gas cost."""
        assert GasCost.BASE == 1
    
    def test_opcode_cost(self):
        """Test opcode gas cost."""
        assert GasCost.OPCODE == 8
    
    def test_storage_costs(self):
        """Test storage gas costs."""
        assert GasCost.STORAGE_READ == 1024
        assert GasCost.STORAGE_WRITE == 4096
    
    def test_contract_call_cost(self):
        """Test contract call gas cost."""
        assert GasCost.CONTRACT_CALL == 32768
    
    def test_crypto_costs(self):
        """Test crypto operation gas costs."""
        assert GasCost.CRYPTO_VERIFY == 32768
        assert GasCost.CRYPTO_HASH == 1024


class TestNotification:
    """Test Notification dataclass."""
    
    def test_create_notification(self):
        """Test creating a notification."""
        from neo.types import UInt160
        from neo.vm.types import Integer
        
        script_hash = UInt160(bytes(20))
        notification = Notification(
            script_hash=script_hash,
            event_name="Transfer",
            state=Integer(100)
        )
        assert notification.event_name == "Transfer"
        assert notification.state.get_integer() == 100


class TestLogEntry:
    """Test LogEntry dataclass."""
    
    def test_create_log_entry(self):
        """Test creating a log entry."""
        from neo.types import UInt160
        
        script_hash = UInt160(bytes(20))
        log = LogEntry(script_hash=script_hash, message="Hello")
        assert log.message == "Hello"
