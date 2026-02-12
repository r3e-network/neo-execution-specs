"""Neo N3 JSON Serializer.

Reference: Neo.SmartContract.JsonSerializer
"""

from __future__ import annotations

import base64
import json
from typing import Any

from neo.vm.types import (
    Array,
    Boolean,
    Buffer,
    ByteString,
    Integer,
    Map,
    NULL,
    StackItem,
    StackItemType,
    Struct,
)


class JsonSerializer:
    """Serialize and deserialize stack items to/from JSON.

    Format follows Neo N3 specification for JSON serialization.
    """

    MAX_SIZE = 1024 * 1024  # 1MB max
    MAX_ITEMS = 2048

    @classmethod
    def serialize(cls, item: StackItem, max_size: int = MAX_SIZE) -> bytes:
        """Serialize a stack item to JSON bytes."""
        json_value = cls._to_json(item, set())
        result = json.dumps(json_value, separators=(',', ':')).encode('utf-8')

        if len(result) > max_size:
            raise ValueError(f"Serialized size {len(result)} exceeds max {max_size}")

        return result

    @classmethod
    def _to_json(cls, item: StackItem, seen: set[int]) -> Any:
        """Convert stack item to JSON-compatible value."""
        item_type = item.type

        if item_type in (StackItemType.ARRAY, StackItemType.STRUCT, StackItemType.MAP):
            item_id = id(item)
            if item_id in seen:
                raise ValueError("Circular reference detected")
            seen = seen | {item_id}

        if item_type == StackItemType.ANY:
            return None

        if item_type == StackItemType.BOOLEAN:
            return item.get_boolean()

        if item_type == StackItemType.INTEGER:
            if not isinstance(item, Integer):
                raise ValueError("Invalid Integer item")
            return int(item.value)

        if item_type == StackItemType.BYTESTRING:
            if not isinstance(item, ByteString):
                raise ValueError("Invalid ByteString item")
            return base64.b64encode(item.value).decode('ascii')

        if item_type == StackItemType.BUFFER:
            if not isinstance(item, Buffer):
                raise ValueError("Invalid Buffer item")
            return base64.b64encode(bytes(item.value)).decode('ascii')

        if item_type == StackItemType.ARRAY:
            if not isinstance(item, Array):
                raise ValueError("Invalid Array item")
            items = list(item)
            if len(items) > cls.MAX_ITEMS:
                raise ValueError(f"Array too large: {len(items)}")
            return [cls._to_json(sub, seen) for sub in items]

        if item_type == StackItemType.STRUCT:
            if not isinstance(item, Struct):
                raise ValueError("Invalid Struct item")
            items = list(item)
            if len(items) > cls.MAX_ITEMS:
                raise ValueError(f"Struct too large: {len(items)}")
            return [cls._to_json(sub, seen) for sub in items]

        if item_type == StackItemType.MAP:
            if not isinstance(item, Map):
                raise ValueError("Invalid Map item")
            entries = list(item.items())
            if len(entries) > cls.MAX_ITEMS:
                raise ValueError(f"Map too large: {len(entries)}")
            result: dict[str, Any] = {}
            for key, value in entries:
                key_json = cls._key_to_string(key)
                result[key_json] = cls._to_json(value, seen)
            return result

        raise ValueError(f"Cannot serialize type: {item_type}")

    @classmethod
    def _key_to_string(cls, key: StackItem) -> str:
        """Convert a map key to string."""
        if key.type == StackItemType.BOOLEAN:
            return "true" if key.get_boolean() else "false"
        if key.type == StackItemType.INTEGER and isinstance(key, Integer):
            return str(int(key.value))
        if key.type == StackItemType.BYTESTRING and isinstance(key, ByteString):
            return base64.b64encode(key.value).decode('ascii')
        raise ValueError(f"Invalid map key type: {key.type}")

    @classmethod
    def deserialize(cls, data: bytes, max_size: int = MAX_SIZE) -> StackItem:
        """Deserialize JSON bytes to a stack item."""
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

        if isinstance(value, bool):
            return Boolean(value)

        if isinstance(value, int):
            return Integer(value)

        if isinstance(value, str):
            return ByteString(value.encode('utf-8'))

        if isinstance(value, list):
            if len(value) > cls.MAX_ITEMS:
                raise ValueError(f"Array too large: {len(value)}")
            items = [cls._from_json(v, depth + 1) for v in value]
            return Array(items=items)

        if isinstance(value, dict):
            if len(value) > cls.MAX_ITEMS:
                raise ValueError(f"Map too large: {len(value)}")
            result = Map()
            for k, v in value.items():
                key = ByteString(k.encode('utf-8'))
                result[key] = cls._from_json(v, depth + 1)
            return result

        raise ValueError(f"Unsupported JSON type: {type(value)}")
