"""Tests for WitnessCondition types."""

import pytest
from neo.network.payloads.witness_condition import (
    WitnessCondition,
    WitnessConditionType,
    BooleanCondition,
    CalledByEntryCondition,
    ScriptHashCondition,
    GroupCondition,
    CalledByContractCondition,
    CalledByGroupCondition,
    NotCondition,
    AndCondition,
    OrCondition,
)
from neo.io.binary_reader import BinaryReader
from neo.io.binary_writer import BinaryWriter


class TestWitnessConditionType:
    """Tests for WitnessConditionType enum."""
    
    def test_values(self):
        """Test enum values."""
        assert WitnessConditionType.BOOLEAN == 0x00
        assert WitnessConditionType.NOT == 0x01
        assert WitnessConditionType.AND == 0x02
        assert WitnessConditionType.OR == 0x03
        assert WitnessConditionType.SCRIPT_HASH == 0x18
        assert WitnessConditionType.GROUP == 0x19
        assert WitnessConditionType.CALLED_BY_ENTRY == 0x20
        assert WitnessConditionType.CALLED_BY_CONTRACT == 0x28
        assert WitnessConditionType.CALLED_BY_GROUP == 0x29


class TestBooleanCondition:
    """Tests for BooleanCondition."""
    
    def test_type(self):
        """Test condition type."""
        cond = BooleanCondition(expression=True)
        assert cond.type == WitnessConditionType.BOOLEAN
    
    def test_size(self):
        """Test size calculation."""
        cond = BooleanCondition(expression=True)
        assert cond.size == 2
    
    def test_serialize_true(self):
        """Test serialization with true."""
        cond = BooleanCondition(expression=True)
        writer = BinaryWriter()
        cond.serialize(writer)
        data = writer.to_bytes()
        assert data[0] == WitnessConditionType.BOOLEAN
        assert data[1] == 1
    
    def test_serialize_false(self):
        """Test serialization with false."""
        cond = BooleanCondition(expression=False)
        writer = BinaryWriter()
        cond.serialize(writer)
        data = writer.to_bytes()
        assert data[0] == WitnessConditionType.BOOLEAN
        assert data[1] == 0
    
    def test_deserialize(self):
        """Test deserialization."""
        data = bytes([WitnessConditionType.BOOLEAN, 1])
        reader = BinaryReader(data)
        cond = WitnessCondition.deserialize(reader)
        assert isinstance(cond, BooleanCondition)
        assert cond.expression is True


class TestCalledByEntryCondition:
    """Tests for CalledByEntryCondition."""
    
    def test_type(self):
        """Test condition type."""
        cond = CalledByEntryCondition()
        assert cond.type == WitnessConditionType.CALLED_BY_ENTRY
    
    def test_size(self):
        """Test size calculation."""
        cond = CalledByEntryCondition()
        assert cond.size == 1
    
    def test_serialize(self):
        """Test serialization."""
        cond = CalledByEntryCondition()
        writer = BinaryWriter()
        cond.serialize(writer)
        data = writer.to_bytes()
        assert data == bytes([WitnessConditionType.CALLED_BY_ENTRY])
    
    def test_deserialize(self):
        """Test deserialization."""
        data = bytes([WitnessConditionType.CALLED_BY_ENTRY])
        reader = BinaryReader(data)
        cond = WitnessCondition.deserialize(reader)
        assert isinstance(cond, CalledByEntryCondition)


class TestScriptHashCondition:
    """Tests for ScriptHashCondition."""
    
    def test_type(self):
        """Test condition type."""
        cond = ScriptHashCondition(hash=b'\x00' * 20)
        assert cond.type == WitnessConditionType.SCRIPT_HASH
    
    def test_size(self):
        """Test size calculation."""
        cond = ScriptHashCondition(hash=b'\x00' * 20)
        assert cond.size == 21
    
    def test_serialize(self):
        """Test serialization."""
        hash_bytes = bytes(range(20))
        cond = ScriptHashCondition(hash=hash_bytes)
        writer = BinaryWriter()
        cond.serialize(writer)
        data = writer.to_bytes()
        assert data[0] == WitnessConditionType.SCRIPT_HASH
        assert data[1:] == hash_bytes
    
    def test_deserialize(self):
        """Test deserialization."""
        hash_bytes = bytes(range(20))
        data = bytes([WitnessConditionType.SCRIPT_HASH]) + hash_bytes
        reader = BinaryReader(data)
        cond = WitnessCondition.deserialize(reader)
        assert isinstance(cond, ScriptHashCondition)
        assert cond.hash == hash_bytes


class TestCalledByContractCondition:
    """Tests for CalledByContractCondition."""
    
    def test_type(self):
        """Test condition type."""
        cond = CalledByContractCondition(hash=b'\x00' * 20)
        assert cond.type == WitnessConditionType.CALLED_BY_CONTRACT
    
    def test_size(self):
        """Test size calculation."""
        cond = CalledByContractCondition(hash=b'\x00' * 20)
        assert cond.size == 21
    
    def test_serialize(self):
        """Test serialization."""
        hash_bytes = bytes(range(20))
        cond = CalledByContractCondition(hash=hash_bytes)
        writer = BinaryWriter()
        cond.serialize(writer)
        data = writer.to_bytes()
        assert data[0] == WitnessConditionType.CALLED_BY_CONTRACT
        assert data[1:] == hash_bytes


class TestNotCondition:
    """Tests for NotCondition."""
    
    def test_type(self):
        """Test condition type."""
        inner = BooleanCondition(expression=True)
        cond = NotCondition(expression=inner)
        assert cond.type == WitnessConditionType.NOT
    
    def test_size(self):
        """Test size calculation."""
        inner = BooleanCondition(expression=True)
        cond = NotCondition(expression=inner)
        assert cond.size == 1 + inner.size
    
    def test_serialize(self):
        """Test serialization."""
        inner = BooleanCondition(expression=True)
        cond = NotCondition(expression=inner)
        writer = BinaryWriter()
        cond.serialize(writer)
        data = writer.to_bytes()
        assert data[0] == WitnessConditionType.NOT
        assert data[1] == WitnessConditionType.BOOLEAN
        assert data[2] == 1
    
    def test_deserialize(self):
        """Test deserialization."""
        data = bytes([
            WitnessConditionType.NOT,
            WitnessConditionType.BOOLEAN, 1
        ])
        reader = BinaryReader(data)
        cond = WitnessCondition.deserialize(reader)
        assert isinstance(cond, NotCondition)
        assert isinstance(cond.expression, BooleanCondition)
        assert cond.expression.expression is True


class TestAndCondition:
    """Tests for AndCondition."""
    
    def test_type(self):
        """Test condition type."""
        cond = AndCondition(expressions=[])
        assert cond.type == WitnessConditionType.AND
    
    def test_serialize_empty(self):
        """Test serialization with empty list."""
        cond = AndCondition(expressions=[])
        writer = BinaryWriter()
        cond.serialize(writer)
        data = writer.to_bytes()
        assert data[0] == WitnessConditionType.AND
        assert data[1] == 0  # count
    
    def test_serialize_multiple(self):
        """Test serialization with multiple conditions."""
        cond = AndCondition(expressions=[
            BooleanCondition(expression=True),
            BooleanCondition(expression=False),
        ])
        writer = BinaryWriter()
        cond.serialize(writer)
        data = writer.to_bytes()
        assert data[0] == WitnessConditionType.AND
        assert data[1] == 2  # count


class TestOrCondition:
    """Tests for OrCondition."""
    
    def test_type(self):
        """Test condition type."""
        cond = OrCondition(expressions=[])
        assert cond.type == WitnessConditionType.OR
    
    def test_serialize_empty(self):
        """Test serialization with empty list."""
        cond = OrCondition(expressions=[])
        writer = BinaryWriter()
        cond.serialize(writer)
        data = writer.to_bytes()
        assert data[0] == WitnessConditionType.OR
        assert data[1] == 0


class TestWitnessConditionDeserialize:
    """Tests for WitnessCondition.deserialize."""
    
    def test_unknown_type(self):
        """Test deserialization of unknown type."""
        data = bytes([0xFF])
        reader = BinaryReader(data)
        with pytest.raises(ValueError, match="is not a valid WitnessConditionType"):
            WitnessCondition.deserialize(reader)
