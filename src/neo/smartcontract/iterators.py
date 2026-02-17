"""Neo N3 Iterator interfaces and implementations.

Reference: Neo.SmartContract.Iterators

Provides the IIterator abstract base class and concrete StorageIterator
used by System.Iterator.Next / System.Iterator.Value syscalls and
System.Storage.Find.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from neo.vm.types import StackItem, ByteString, Array
from neo.smartcontract.storage.find_options import FindOptions

if TYPE_CHECKING:
    from neo.smartcontract.application_engine import ApplicationEngine

class IIterator(ABC):
    """Abstract iterator interface matching Neo N3 IIterator<StackItem>."""

    @abstractmethod
    def next(self) -> bool:
        """Advance to the next element. Returns False when exhausted."""
        ...

    @abstractmethod
    def value(self) -> StackItem:
        """Get the element at the current position.

        Raises ValueError if called before next() or after exhaustion.
        """
        ...

class StorageIterator(IIterator):
    """Iterator over storage find results.

    Wraps a list of (key, value) pairs from snapshot.find() and applies
    FindOptions transformations matching the C# reference behaviour.

    Parameters
    ----------
    engine : ApplicationEngine
        The executing engine (used for deserialization if needed).
    prefix : bytes
        The full storage key prefix (script_hash + user_prefix) used in
        the find call.  Needed for REMOVE_PREFIX.
    options : int
        Bitmask of FindOptions flags.
    """

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
        self._index: int = -1

        # Materialise results from snapshot
        snapshot = getattr(engine, "snapshot", None)
        if snapshot is not None:
            self._pairs = list(snapshot.find(prefix))

        # BACKWARDS: reverse iteration order
        if self._options & FindOptions.BACKWARDS:
            self._pairs.reverse()

    # ------------------------------------------------------------------
    # IIterator interface
    # ------------------------------------------------------------------

    def next(self) -> bool:
        self._index += 1
        return self._index < len(self._pairs)

    def value(self) -> StackItem:
        if self._index < 0 or self._index >= len(self._pairs):
            raise ValueError("No current element")

        raw_key, raw_value = self._pairs[self._index]
        return self._apply_options(raw_key, raw_value)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply_options(self, raw_key: bytes, raw_value: bytes) -> StackItem:
        """Transform a raw (key, value) pair according to FindOptions."""
        opts = self._options

        # Strip the prefix from the key when requested
        key_bytes = raw_key
        if opts & FindOptions.REMOVE_PREFIX:
            key_bytes = raw_key[len(self._prefix):]

        # Deserialise value if requested
        value_item: StackItem = ByteString(raw_value)
        if opts & FindOptions.DESERIALIZE_VALUES:
            value_item = self._deserialize(raw_value)

        # PICK_FIELD0 / PICK_FIELD1 — extract from deserialised array
        if opts & FindOptions.PICK_FIELD0:
            value_item = self._pick_field(value_item, 0)
        elif opts & FindOptions.PICK_FIELD1:
            value_item = self._pick_field(value_item, 1)

        # Return shape depends on KEYS_ONLY / VALUES_ONLY
        if opts & FindOptions.KEYS_ONLY:
            return ByteString(key_bytes)
        if opts & FindOptions.VALUES_ONLY:
            return value_item

        # Default: return (key, value) as a Struct
        from neo.vm.types import Struct
        result = Struct(self._engine.reference_counter)
        result.add(ByteString(key_bytes))
        result.add(value_item)
        return result

    @staticmethod
    def _deserialize(data: bytes) -> StackItem:
        """Best-effort BinarySerializer deserialization."""
        try:
            from neo.smartcontract.binary_serializer import BinarySerializer
            return BinarySerializer.deserialize(data)
        except (ValueError, TypeError, IndexError, KeyError):
            return ByteString(data)

    @staticmethod
    def _pick_field(item: StackItem, index: int) -> StackItem:
        """Pick a field from an Array/Struct item."""
        if isinstance(item, Array) and index < len(item):
            return item[index]
        return item
