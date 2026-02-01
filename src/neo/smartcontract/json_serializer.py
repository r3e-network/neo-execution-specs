"""JsonSerializer - Serialize/deserialize StackItems to JSON."""

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, List, Union
import json

if TYPE_CHECKING:
    from neo.vm.types import StackItem


class JsonSerializer:
    """JSON serializer for StackItems."""
    
    MAX_SAFE_INTEGER = 9007199254740991
    MIN_SAFE_INTEGER = -9007199254740991
    
    @staticmethod
    def serialize(item: StackItem) -> Any:
        """Serialize StackItem to JSON-compatible value."""
        from neo.vm.types import (
            Integer, ByteString, Boolean,
            Array, Map, Buffer, NULL
        )
        
        if item is NULL or item is None:
            return None
        elif isinstance(item, Boolean):
            return item.value
        elif isinstance(item, Integer):
            val = item.value
            if val > JsonSerializer.MAX_SAFE_INTEGER:
                raise ValueError("Integer too large")
            if val < JsonSerializer.MIN_SAFE_INTEGER:
                raise ValueError("Integer too small")
            return val
        elif isinstance(item, (ByteString, Buffer)):
            val = item.value if hasattr(item, 'value') else bytes(item)
            try:
                return val.decode('utf-8')
            except:
                return val.hex()
        elif isinstance(item, Array):
            return [JsonSerializer.serialize(i) for i in item]
        elif isinstance(item, Map):
            result = {}
            for k, v in item.items():
                if not isinstance(k, ByteString):
                    raise ValueError("Map key must be ByteString")
                key_str = k.value.decode('utf-8')
                result[key_str] = JsonSerializer.serialize(v)
            return result
        else:
            raise ValueError(f"Unsupported type: {type(item)}")
    
    @staticmethod
    def deserialize(value: Any) -> StackItem:
        """Deserialize JSON value to StackItem."""
        from neo.vm.types import (
            Integer, ByteString, Boolean,
            Array, Map, NULL
        )
        
        if value is None:
            return NULL
        elif isinstance(value, bool):
            return Boolean(value)
        elif isinstance(value, int):
            return Integer(value)
        elif isinstance(value, float):
            if value % 1 != 0:
                raise ValueError("Decimal not allowed")
            return Integer(int(value))
        elif isinstance(value, str):
            return ByteString(value.encode('utf-8'))
        elif isinstance(value, list):
            arr = Array()
            for item in value:
                arr.append(JsonSerializer.deserialize(item))
            return arr
        elif isinstance(value, dict):
            m = Map()
            for k, v in value.items():
                m[ByteString(k.encode('utf-8'))] = JsonSerializer.deserialize(v)
            return m
        else:
            raise ValueError(f"Unsupported JSON type: {type(value)}")
