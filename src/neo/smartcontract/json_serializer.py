"""Neo N3 JSON Serializer.

Reference: Neo.SmartContract.JsonSerializer
"""

from __future__ import annotations
import json
from typing import Any, Dict, List, Union, Optional
from io import StringIO

from neo.vm.types import (
    StackItem, StackItemType, Integer, Boolean, ByteString,
    Buffer, Array, Struct, Map, Null, NULL
)


class JsonSerializer:
    """Serialize and deserialize stack items to/from JSON.
    
    Format follows Neo N3 specification for JSON serialization.
    """
    
    MAX_SIZE = 1024 * 1024  # 1MB max
    MAX_ITEMS = 2048
    
    @classmethod
    def serialize(cls, item: StackItem, max_size: int = MAX_SIZE) -> bytes:
        """Serialize a stack item to JSON bytes.
        
        Args:
            item: The stack item to serialize.
            max_size: Maximum allowed serialized size.
            
        Returns:
            JSON bytes (UTF-8 encoded).
        """
        json_value = cls._to_json(item, set())
        result = json.dumps(json_value, separators=(',', ':')).encode('utf-8')
        
        if len(result) > max_size:
            raise ValueError(f"Serialized size {len(result)} exceeds max {max_size}")
        
        return result
    
    @classmethod
    def _to_json(cls, item: StackItem, seen: set) -> Any:
        """Convert stack item to JSON-compatible value."""
        item_type = item.type
        
        # Check for circular references
        if item_type in (StackItemType.ARRAY, StackItemType.STRUCT, StackItemType.MAP):
            item_id = id(item)
            if item_id in seen:
                raise ValueError("Circular reference detected")
            seen = seen | {item_id}
        
        if item_type == StackItemType.ANY:
            return None
        
        elif item_type == StackItemType.BOOLEAN:
            return item.get_boolean()
        
        elif item_type == StackItemType.INTEGER:
            return item.value
        
        elif item_type == StackItemType.BYTESTRING:
            # Encode as base64
            import base64
            return base64.b64encode(item.value).decode('ascii')
        
        elif item_type == StackItemType.BUFFER:
            import base64
            return base64.b64encode(bytes(item.value)).decode('ascii')
        
        elif item_type == StackItemType.ARRAY:
            items = item._items
            if len(items) > cls.MAX_ITEMS:
                raise ValueError(f"Array too large: {len(items)}")
            return [cls._to_json(sub, seen) for sub in items]
        
        elif item_type == StackItemType.STRUCT:
            items = item._items
            if len(items) > cls.MAX_ITEMS:
                raise ValueError(f"Struct too large: {len(items)}")
            return [cls._to_json(sub, seen) for sub in items]
        
        elif item_type == StackItemType.MAP:
            entries = list(item._dict.items())
            if len(entries) > cls.MAX_ITEMS:
                raise ValueError(f"Map too large: {len(entries)}")
            result = {}
            for key, value in entries:
                # Map keys must be primitive types
                key_json = cls._key_to_string(key)
                result[key_json] = cls._to_json(value, seen)
            return result
        
        else:
            raise ValueError(f"Cannot serialize type: {item_type}")
    
    @classmethod
    def _key_to_string(cls, key: StackItem) -> str:
        """Convert a map key to string."""
        if key.type == StackItemType.BOOLEAN:
            return "true" if key.get_boolean() else "false"
        elif key.type == StackItemType.INTEGER:
            return str(key.value)
        elif key.type == StackItemType.BYTESTRING:
            import base64
            return base64.b64encode(key.value).decode('ascii')
        else:
            raise ValueError(f"Invalid map key type: {key.type}")
    
    @classmethod
    def deserialize(cls, data: bytes, max_size: int = MAX_SIZE) -> StackItem:
        """Deserialize JSON bytes to a stack item.
        
        Args:
            data: JSON bytes to deserialize.
            max_size: Maximum allowed data size.
            
        Returns:
            Deserialized stack item.
        """
        if len(data) > max_size:
            raise ValueError(f"Data size {len(data)} exceeds max {max_size}")
        
        json_value = json.loads(data.decode('utf-8'))
        return cls._from_json(json_value, 0)
    
    @classmethod
    def _from_json(cls, value: Any, depth: int) -> StackItem:
        """Convert JSON value to stack item."""
        if depth > 128:
            raise ValueError("Deserialization depth exceeded")
        
        if value is None:
            return NULL
        
        elif isinstance(value, bool):
            return Boolean(value)
        
        elif isinstance(value, int):
            return Integer(value)
        
        elif isinstance(value, str):
            # Try to decode as base64
            import base64
            try:
                decoded = base64.b64decode(value)
                return ByteString(decoded)
            except Exception:
                return ByteString(value.encode('utf-8'))
        
        elif isinstance(value, list):
            if len(value) > cls.MAX_ITEMS:
                raise ValueError(f"Array too large: {len(value)}")
            items = [cls._from_json(v, depth + 1) for v in value]
            return Array(items=items)
        
        elif isinstance(value, dict):
            if len(value) > cls.MAX_ITEMS:
                raise ValueError(f"Map too large: {len(value)}")
            result = Map()
            for k, v in value.items():
                key = ByteString(k.encode('utf-8'))
                result[key] = cls._from_json(v, depth + 1)
            return result
        
        else:
            raise ValueError(f"Unsupported JSON type: {type(value)}")
