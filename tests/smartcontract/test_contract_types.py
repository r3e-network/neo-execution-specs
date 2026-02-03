"""Tests for contract types."""

import pytest
from neo.smartcontract.call_flags import CallFlags
from neo.smartcontract.trigger import TriggerType
from neo.smartcontract.contract_parameter_type import ContractParameterType


class TestCallFlags:
    """Tests for CallFlags enum."""
    
    def test_none(self):
        """Test None flag."""
        assert CallFlags.NONE == 0
    
    def test_read_states(self):
        """Test ReadStates flag."""
        assert CallFlags.READ_STATES == 0x01
    
    def test_write_states(self):
        """Test WriteStates flag."""
        assert CallFlags.WRITE_STATES == 0x02
    
    def test_allow_call(self):
        """Test AllowCall flag."""
        assert CallFlags.ALLOW_CALL == 0x04
    
    def test_allow_notify(self):
        """Test AllowNotify flag."""
        assert CallFlags.ALLOW_NOTIFY == 0x08
    
    def test_states(self):
        """Test States combination."""
        assert CallFlags.STATES == (CallFlags.READ_STATES | CallFlags.WRITE_STATES)
    
    def test_all(self):
        """Test All flag."""
        assert CallFlags.ALL == 0x0F


class TestTriggerType:
    """Tests for TriggerType enum."""
    
    def test_system(self):
        """Test System trigger."""
        assert TriggerType.SYSTEM == 0x01
    
    def test_verification(self):
        """Test Verification trigger."""
        assert TriggerType.VERIFICATION == 0x20
    
    def test_application(self):
        """Test Application trigger."""
        assert TriggerType.APPLICATION == 0x40
    
    def test_all(self):
        """Test All trigger combination."""
        expected = TriggerType.SYSTEM | TriggerType.VERIFICATION | TriggerType.APPLICATION
        assert TriggerType.ALL == expected


class TestContractParameterType:
    """Tests for ContractParameterType enum."""
    
    def test_any(self):
        """Test Any type."""
        assert ContractParameterType.ANY == 0x00
    
    def test_boolean(self):
        """Test Boolean type."""
        assert ContractParameterType.BOOLEAN == 0x10
    
    def test_integer(self):
        """Test Integer type."""
        assert ContractParameterType.INTEGER == 0x11
    
    def test_byte_array(self):
        """Test ByteArray type."""
        assert ContractParameterType.BYTE_ARRAY == 0x12
    
    def test_string(self):
        """Test String type."""
        assert ContractParameterType.STRING == 0x13
    
    def test_hash160(self):
        """Test Hash160 type."""
        assert ContractParameterType.HASH160 == 0x14
    
    def test_hash256(self):
        """Test Hash256 type."""
        assert ContractParameterType.HASH256 == 0x15
    
    def test_public_key(self):
        """Test PublicKey type."""
        assert ContractParameterType.PUBLIC_KEY == 0x16
    
    def test_signature(self):
        """Test Signature type."""
        assert ContractParameterType.SIGNATURE == 0x17
    
    def test_array(self):
        """Test Array type."""
        assert ContractParameterType.ARRAY == 0x20
    
    def test_map(self):
        """Test Map type."""
        assert ContractParameterType.MAP == 0x22
    
    def test_void(self):
        """Test Void type."""
        assert ContractParameterType.VOID == 0xFF
