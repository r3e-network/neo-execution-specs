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

    # StackItem types allowed as Map keys (C# PrimitiveType: Boolean, Integer,
    # ByteString). Buffer derives from StackItem, not PrimitiveType, so a Buffer
    # key faults via the `(PrimitiveType)key` cast in C#.
    _PRIMITIVE_KEY_TYPES = (
        StackItemType.BOOLEAN,
        StackItemType.INTEGER,
        StackItemType.BYTESTRING,
    )

    @classmethod
    def deserialize(cls, data: bytes, max_size: int = MAX_SIZE) -> StackItem:
        """Deserialize bytes to a stack item.

        Mirrors C# BinarySerializer.Deserialize: a flat work-stack bounded by a
        single cumulative item count (MaxStackSize), not per-container length.
        """
        if len(data) > max_size:
            raise ValueError(f"Data size {len(data)} exceeds max {max_size}")

        reader = BytesIO(data)
        max_items = cls.MAX_ITEMS

        # Phase 1: flat parse. Each produced node (leaf or container
        # placeholder) increments the running count, faulting when it exceeds
        # maxItems (strict >), matching C# `deserialized.Count > maxItems`.
        deserialized: list[StackItem] = []
        # ContainerPlaceholder is encoded as a (type, element_count) tuple.
        undeserialized = 1
        while undeserialized > 0:
            undeserialized -= 1
            type_byte = reader.read(1)
            if not type_byte:
                raise ValueError("Unexpected end of data")
            item_type = type_byte[0]

            if item_type == StackItemType.ANY:
                deserialized.append(NULL)
            elif item_type == StackItemType.BOOLEAN:
                value_byte = reader.read(1)
                if not value_byte:
                    raise ValueError("Unexpected end of data")
                deserialized.append(Boolean(value_byte[0] != 0))
            elif item_type == StackItemType.INTEGER:
                length = cls._read_var_int(reader, 32)  # Integer.MaxSize
                data_bytes = reader.read(length)
                if len(data_bytes) != length:
                    raise ValueError("Unexpected end of data")
                if length == 0:
                    deserialized.append(Integer(0))
                else:
                    deserialized.append(
                        Integer(int.from_bytes(data_bytes, 'little', signed=True))
                    )
            elif item_type == StackItemType.BYTESTRING:
                length = cls._read_var_int(reader, max_size)
                data_bytes = reader.read(length)
                if len(data_bytes) != length:
                    raise ValueError("Unexpected end of data")
                deserialized.append(ByteString(data_bytes))
            elif item_type == StackItemType.BUFFER:
                length = cls._read_var_int(reader, max_size)
                data_bytes = reader.read(length)
                if len(data_bytes) != length:
                    raise ValueError("Unexpected end of data")
                deserialized.append(Buffer(bytearray(data_bytes)))
            elif item_type in (StackItemType.ARRAY, StackItemType.STRUCT):
                count = cls._read_var_int(reader, max_items)
                deserialized.append((item_type, count))
                undeserialized += count
            elif item_type == StackItemType.MAP:
                count = cls._read_var_int(reader, max_items)
                deserialized.append((item_type, count))
                undeserialized += count * 2
            else:
                raise ValueError(f"Unknown type: {item_type:#x}")

            if len(deserialized) > max_items:
                raise ValueError(
                    f"Deserialized count({len(deserialized)}) is out of range "
                    f"(max:{max_items})"
                )

        # Phase 2: rebuild containers from placeholders, popping children.
        stack_temp: list[StackItem] = []
        while deserialized:
            item = deserialized.pop()
            if isinstance(item, tuple):
                placeholder_type, element_count = item
                if placeholder_type == StackItemType.ARRAY:
                    array_items: list[StackItem] = []
                    for _ in range(element_count):
                        array_items.append(stack_temp.pop())
                    item = Array(items=array_items)
                elif placeholder_type == StackItemType.STRUCT:
                    struct_items: list[StackItem] = []
                    for _ in range(element_count):
                        struct_items.append(stack_temp.pop())
                    item = Struct(items=struct_items)
                else:  # MAP
                    result = Map()
                    for _ in range(element_count):
                        key = stack_temp.pop()
                        value = stack_temp.pop()
                        # C# casts `(PrimitiveType)key`; non-primitive (incl.
                        # Buffer) keys fault here.
                        if key.type not in cls._PRIMITIVE_KEY_TYPES:
                            raise ValueError("Map key is not a PrimitiveType")
                        result[key] = value
                    item = result
            stack_temp.append(item)

        return stack_temp[-1]

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
    def _read_var_int(reader: BinaryIO, max_value: int = 0xFFFFFFFFFFFFFFFF) -> int:
        """Read a variable-length integer, faulting if it exceeds max_value.

        Mirrors C# MemoryReader.ReadVarInt(max) which throws FormatException
        when the decoded value exceeds the supplied maximum.
        """
        first = reader.read(1)
        if not first:
            raise ValueError("Unexpected end of data")

        fb = first[0]
        if fb < 0xFD:
            value = fb
        elif fb == 0xFD:
            data = reader.read(2)
            if len(data) != 2:
                raise ValueError("Unexpected end of data")
            value = int.from_bytes(data, 'little')
        elif fb == 0xFE:
            data = reader.read(4)
            if len(data) != 4:
                raise ValueError("Unexpected end of data")
            value = int.from_bytes(data, 'little')
        else:
            data = reader.read(8)
            if len(data) != 8:
                raise ValueError("Unexpected end of data")
            value = int.from_bytes(data, 'little')

        if value > max_value:
            raise ValueError(f"VarInt value {value} exceeds max {max_value}")
        return value
