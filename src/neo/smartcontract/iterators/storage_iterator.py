"""StorageIterator - Iterator for storage entries."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from .iterator import IIterator
from neo.smartcontract.storage.find_options import FindOptions
from neo.vm.types import Array, ByteString, StackItem, Struct

if TYPE_CHECKING:
    pass

class StorageIterator(IIterator):
    """Iterator for storage search results.

    Can be created in two ways:
    1. From an ApplicationEngine (queries snapshot.find)
    2. From a list of (key, value) pairs (for testing)
    """

    def __init__(
        self,
        engine_or_pairs,
        prefix: bytes = b"",
        options: int = 0,
    ) -> None:
        """Initialize StorageIterator.

        Args:
            engine_or_pairs: Either an ApplicationEngine or an iterator of (key, value) pairs.
            prefix: Storage key prefix (used with REMOVE_PREFIX option).
            options: FindOptions flags.
        """
        # Handle two calling conventions
        if isinstance(engine_or_pairs, Iterator):
            # Called from test with list of pairs: StorageIterator(iter(pairs), prefix_len, options)
            raw_pairs = list(engine_or_pairs)
            # Extract raw bytes from StorageKey/StorageItem if needed
            self._pairs: list[tuple[bytes, bytes]] = []
            for item in raw_pairs:
                if len(item) == 2:
                    key, value = item
                    # Extract key bytes
                    if hasattr(key, "key"):
                        key_bytes = key.key
                    else:
                        key_bytes = key
                    # Extract value bytes
                    if hasattr(value, "value"):
                        value_bytes = value.value
                    else:
                        value_bytes = value
                    self._pairs.append((key_bytes, value_bytes))
            self._engine = None
            self._prefix = prefix
            self._options = FindOptions(options)
        else:
            # Called from production: StorageIterator(engine, prefix, options)
            engine = engine_or_pairs
            self._engine = engine
            self._prefix = prefix
            self._options = FindOptions(options)
            self._pairs = []

            snapshot = getattr(engine, "snapshot", None)
            if snapshot is not None and hasattr(snapshot, "find"):
                self._pairs = list(snapshot.find(prefix))

        self._index = -1

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
            # Handle both int prefix_len and bytes prefix
            if isinstance(self._prefix, int):
                prefix_len = self._prefix
            else:
                prefix_len = len(self._prefix)
            key_bytes = raw_key[prefix_len:]

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
