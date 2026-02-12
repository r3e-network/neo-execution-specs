"""StorageIterator - Iterator for storage entries."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .iterator import IIterator
from neo.smartcontract.storage.find_options import FindOptions
from neo.vm.types import Array, ByteString, StackItem, Struct

if TYPE_CHECKING:
    from neo.smartcontract.application_engine import ApplicationEngine


class StorageIterator(IIterator):
    """Iterator for storage search results."""

    def __init__(
        self,
        engine: "ApplicationEngine",
        prefix: bytes,
        options: int,
    ) -> None:
        self._engine = engine
        self._prefix = prefix
        self._options = FindOptions(options)
        self._pairs: list[tuple[bytes, bytes]] = []
        self._index = -1

        snapshot = getattr(engine, "snapshot", None)
        if snapshot is not None and hasattr(snapshot, "find"):
            self._pairs = list(snapshot.find(prefix))

        if self._options & FindOptions.BACKWARDS:
            self._pairs.reverse()

    def next(self) -> bool:
        """Advance to next element."""
        self._index += 1
        return self._index < len(self._pairs)

    def value(self) -> StackItem:
        """Get current element."""
        if self._index < 0 or self._index >= len(self._pairs):
            raise ValueError("No current element")

        raw_key, raw_value = self._pairs[self._index]
        return self._apply_options(raw_key, raw_value)

    def _apply_options(self, raw_key: bytes, raw_value: bytes) -> StackItem:
        key_bytes = raw_key
        if self._options & FindOptions.REMOVE_PREFIX:
            key_bytes = raw_key[len(self._prefix):]

        value_item: StackItem = ByteString(raw_value)
        if self._options & FindOptions.DESERIALIZE_VALUES:
            value_item = self._deserialize(raw_value)

        if self._options & FindOptions.PICK_FIELD0:
            value_item = self._pick_field(value_item, 0)
        elif self._options & FindOptions.PICK_FIELD1:
            value_item = self._pick_field(value_item, 1)

        if self._options & FindOptions.KEYS_ONLY:
            return ByteString(key_bytes)
        if self._options & FindOptions.VALUES_ONLY:
            return value_item

        return Struct(items=[ByteString(key_bytes), value_item])

    @staticmethod
    def _deserialize(data: bytes) -> StackItem:
        try:
            from neo.smartcontract.binary_serializer import BinarySerializer

            return BinarySerializer.deserialize(data)
        except (ValueError, TypeError, IndexError, KeyError):
            return ByteString(data)

    @staticmethod
    def _pick_field(item: StackItem, index: int) -> StackItem:
        if isinstance(item, Array) and index < len(item):
            return item[index]
        return item
