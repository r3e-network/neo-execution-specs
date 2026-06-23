"""Neo N3 JSON Serializer.

Reference: Neo.SmartContract.JsonSerializer
"""

from __future__ import annotations

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
    # C# Neo.Json.JNumber safe-integer bounds (2^53 - 1)
    MAX_SAFE_INTEGER = (1 << 53) - 1
    MIN_SAFE_INTEGER = -MAX_SAFE_INTEGER
    # C# ExecutionEngineLimits.MaxStackSize, used as the cumulative deserialize budget
    MAX_STACK_SIZE = 2048

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
            value = int(item.value)
            # C# JsonSerializer faults when the integer is outside the
            # JavaScript safe-integer range (writes it as a double otherwise).
            if value > cls.MAX_SAFE_INTEGER or value < cls.MIN_SAFE_INTEGER:
                raise ValueError("Integer is out of safe-integer range")
            return value

        if item_type == StackItemType.BYTESTRING:
            if not isinstance(item, ByteString):
                raise ValueError("Invalid ByteString item")
            # C# writes GetString() = strict UTF-8 decoding; invalid UTF-8 faults.
            return cls._to_strict_utf8(item.value)

        if item_type == StackItemType.BUFFER:
            if not isinstance(item, Buffer):
                raise ValueError("Invalid Buffer item")
            return cls._to_strict_utf8(bytes(item.value))

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
        """Convert a map key to string.

        C# only permits ByteString keys (JsonSerializer.cs:136) and writes the
        key via GetString() = strict UTF-8 (JsonSerializer.cs:146). Boolean and
        Integer keys fault.
        """
        if key.type == StackItemType.BYTESTRING and isinstance(key, ByteString):
            return cls._to_strict_utf8(key.value)
        raise ValueError("Key is not a ByteString")

    @staticmethod
    def _to_strict_utf8(data: bytes) -> str:
        """Decode bytes as strict UTF-8, faulting on invalid sequences.

        Mirrors C# StackItem.GetString() = GetSpan().ToStrictUtf8String(),
        which throws on invalid UTF-8.
        """
        try:
            return data.decode('utf-8')
        except UnicodeDecodeError as exc:
            raise ValueError("Invalid UTF-8 byte sequence") from exc

    @classmethod
    def deserialize(cls, data: bytes, max_size: int = MAX_SIZE) -> StackItem:
        """Deserialize JSON bytes to a stack item."""
        if len(data) > max_size:
            raise ValueError(f"Data size {len(data)} exceeds max {max_size}")

        json_value = json.loads(data.decode('utf-8'))
        # C# JsonSerializer.Deserialize bounds the whole tree by a single
        # decrementing node budget seeded at MaxStackSize (not per-collection
        # length or depth). Use a mutable one-element list as the counter.
        budget = [cls.MAX_STACK_SIZE]
        return cls._from_json(json_value, 0, budget)

    @classmethod
    def _from_json(cls, value: Any, depth: int, budget: list[int]) -> StackItem:
        """Convert JSON value to stack item."""
        # Cumulative node budget: check-then-decrement once per node,
        # mirroring C# `if (maxStackSize-- == 0) throw`.
        if budget[0] == 0:
            raise ValueError("Max stack size reached")
        budget[0] -= 1

        # Harmless extra safety bound (not what C# uses; never fires before
        # the cumulative budget on wide inputs).
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
            items = [cls._from_json(v, depth + 1, budget) for v in value]
            return Array(items=items)

        if isinstance(value, dict):
            result = Map()
            for k, v in value.items():
                # C# decrements once per map property before recursing
                # into the value (JsonSerializer.cs:213).
                if budget[0] == 0:
                    raise ValueError("Max stack size reached")
                budget[0] -= 1
                key = ByteString(k.encode('utf-8'))
                result[key] = cls._from_json(v, depth + 1, budget)
            return result

        raise ValueError(f"Unsupported JSON type: {type(value)}")
