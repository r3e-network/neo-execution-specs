"""Neo N3 Binary Serializer.

Reference: Neo.SmartContract.BinarySerializer
"""

from __future__ import annotations

from io import BytesIO
from typing import BinaryIO

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


class BinarySerializer:
    """Serialize and deserialize stack items to/from bytes.

    Format follows Neo N3 specification for binary serialization.
    """

    MAX_SIZE = 1024 * 1024  # 1MB max (C# MaxItemSize)
    MAX_ITEMS = 2048  # Max items in compound types

    @classmethod
    def serialize(cls, item: StackItem, max_size: int = MAX_SIZE) -> bytes:
        """Serialize a stack item to bytes."""
        writer = BytesIO()
        cls._serialize_item(item, writer, set())
        result = writer.getvalue()

        if len(result) > max_size:
            raise ValueError(f"Serialized size {len(result)} exceeds max {max_size}")

        return result

    @classmethod
    def _serialize_item(cls, item: StackItem, writer: BinaryIO, seen: set[int]) -> None:
        """Serialize a single stack item."""
        item_type = item.type

        if item_type in (StackItemType.ARRAY, StackItemType.STRUCT, StackItemType.MAP):
            item_id = id(item)
            if item_id in seen:
                raise ValueError("Circular reference detected")
            seen = seen | {item_id}

        writer.write(bytes([item_type]))

        if item_type == StackItemType.ANY:
            return

        if item_type == StackItemType.BOOLEAN:
            writer.write(bytes([1 if item.get_boolean() else 0]))
            return

        if item_type == StackItemType.INTEGER:
            if not isinstance(item, Integer):
                raise ValueError("Invalid Integer item")
            int_value = int(item.value)
            if int_value == 0:
                writer.write(bytes([0]))  # Zero length
                return

            if int_value > 0:
                byte_len = (int_value.bit_length() + 8) // 8
            else:
                byte_len = ((-int_value - 1).bit_length() + 8) // 8
            data = int_value.to_bytes(byte_len, 'little', signed=True)
            cls._write_var_int(writer, len(data))
            writer.write(data)
            return

        if item_type == StackItemType.BYTESTRING:
            if not isinstance(item, ByteString):
                raise ValueError("Invalid ByteString item")
            data = item.value
            cls._write_var_int(writer, len(data))
            writer.write(data)
            return

        if item_type == StackItemType.BUFFER:
            if not isinstance(item, Buffer):
                raise ValueError("Invalid Buffer item")
            data = bytes(item.value)
            cls._write_var_int(writer, len(data))
            writer.write(data)
            return

        if item_type == StackItemType.ARRAY:
            if not isinstance(item, Array):
                raise ValueError("Invalid Array item")
            items = list(item)
            if len(items) > cls.MAX_ITEMS:
                raise ValueError(f"Array too large: {len(items)}")
            cls._write_var_int(writer, len(items))
            for sub_item in items:
                cls._serialize_item(sub_item, writer, seen)
            return

        if item_type == StackItemType.STRUCT:
            if not isinstance(item, Struct):
                raise ValueError("Invalid Struct item")
            items = list(item)
            if len(items) > cls.MAX_ITEMS:
                raise ValueError(f"Struct too large: {len(items)}")
            cls._write_var_int(writer, len(items))
            for sub_item in items:
                cls._serialize_item(sub_item, writer, seen)
            return

        if item_type == StackItemType.MAP:
            if not isinstance(item, Map):
                raise ValueError("Invalid Map item")
            entries = list(item.items())
            if len(entries) > cls.MAX_ITEMS:
                raise ValueError(f"Map too large: {len(entries)}")
            cls._write_var_int(writer, len(entries))
            for key, map_value in entries:
                cls._serialize_item(key, writer, seen)
                cls._serialize_item(map_value, writer, seen)
            return

        raise ValueError(f"Cannot serialize type: {item_type}")

    @classmethod
    def deserialize(cls, data: bytes, max_size: int = MAX_SIZE) -> StackItem:
        """Deserialize bytes to a stack item."""
        if len(data) > max_size:
            raise ValueError(f"Data size {len(data)} exceeds max {max_size}")

        reader = BytesIO(data)
        return cls._deserialize_item(reader, 0)

    @classmethod
    def _deserialize_item(cls, reader: BinaryIO, depth: int) -> StackItem:
        """Deserialize a single stack item."""
        if depth > 128:
            raise ValueError("Deserialization depth exceeded")

        type_byte = reader.read(1)
        if not type_byte:
            raise ValueError("Unexpected end of data")

        item_type = type_byte[0]

        if item_type == StackItemType.ANY:
            return NULL

        if item_type == StackItemType.BOOLEAN:
            value_byte = reader.read(1)
            if not value_byte:
                raise ValueError("Unexpected end of data")
            return Boolean(value_byte[0] != 0)

        if item_type == StackItemType.INTEGER:
            length = cls._read_var_int(reader)
            if length == 0:
                return Integer(0)
            if length > 32:
                raise ValueError(f"Integer too large: {length} bytes")
            data = reader.read(length)
            if len(data) != length:
                raise ValueError("Unexpected end of data")
            int_value = int.from_bytes(data, 'little', signed=True)
            return Integer(int_value)

        if item_type == StackItemType.BYTESTRING:
            length = cls._read_var_int(reader)
            if length > cls.MAX_SIZE:
                raise ValueError(f"ByteString too large: {length}")
            data = reader.read(length)
            if len(data) != length:
                raise ValueError("Unexpected end of data")
            return ByteString(data)

        if item_type == StackItemType.BUFFER:
            length = cls._read_var_int(reader)
            if length > cls.MAX_SIZE:
                raise ValueError(f"Buffer too large: {length}")
            data = reader.read(length)
            if len(data) != length:
                raise ValueError("Unexpected end of data")
            return Buffer(bytearray(data))

        if item_type == StackItemType.ARRAY:
            count = cls._read_var_int(reader)
            if count > cls.MAX_ITEMS:
                raise ValueError(f"Array too large: {count}")
            array_items: list[StackItem] = []
            for _ in range(count):
                array_items.append(cls._deserialize_item(reader, depth + 1))
            return Array(items=array_items)

        if item_type == StackItemType.STRUCT:
            count = cls._read_var_int(reader)
            if count > cls.MAX_ITEMS:
                raise ValueError(f"Struct too large: {count}")
            struct_items: list[StackItem] = []
            for _ in range(count):
                struct_items.append(cls._deserialize_item(reader, depth + 1))
            return Struct(items=struct_items)

        if item_type == StackItemType.MAP:
            count = cls._read_var_int(reader)
            if count > cls.MAX_ITEMS:
                raise ValueError(f"Map too large: {count}")
            result = Map()
            for _ in range(count):
                key_item = cls._deserialize_item(reader, depth + 1)
                map_value = cls._deserialize_item(reader, depth + 1)
                result[key_item] = map_value
            return result

        raise ValueError(f"Unknown type: {item_type:#x}")

    @staticmethod
    def _write_var_int(writer: BinaryIO, value: int) -> None:
        """Write a variable-length integer."""
        if value < 0:
            raise ValueError("Negative var int")
        if value < 0xFD:
            writer.write(bytes([value]))
        elif value <= 0xFFFF:
            writer.write(bytes([0xFD]))
            writer.write(value.to_bytes(2, 'little'))
        elif value <= 0xFFFFFFFF:
            writer.write(bytes([0xFE]))
            writer.write(value.to_bytes(4, 'little'))
        else:
            writer.write(bytes([0xFF]))
            writer.write(value.to_bytes(8, 'little'))

    @staticmethod
    def _read_var_int(reader: BinaryIO) -> int:
        """Read a variable-length integer."""
        first = reader.read(1)
        if not first:
            raise ValueError("Unexpected end of data")

        fb = first[0]
        if fb < 0xFD:
            return fb
        if fb == 0xFD:
            data = reader.read(2)
            if len(data) != 2:
                raise ValueError("Unexpected end of data")
            return int.from_bytes(data, 'little')
        if fb == 0xFE:
            data = reader.read(4)
            if len(data) != 4:
                raise ValueError("Unexpected end of data")
            return int.from_bytes(data, 'little')

        data = reader.read(8)
        if len(data) != 8:
            raise ValueError("Unexpected end of data")
        return int.from_bytes(data, 'little')
