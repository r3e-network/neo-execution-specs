"""StorageIterator - Iterator for storage entries."""

from __future__ import annotations
from typing import Iterator, Tuple, TYPE_CHECKING

from .iterator import IIterator
from neo.smartcontract.storage.find_options import FindOptions

if TYPE_CHECKING:
    from neo.vm.types import StackItem
    from neo.smartcontract.storage import StorageKey, StorageItem


class StorageIterator(IIterator):
    """Iterator for storage search results."""
    
    def __init__(
        self,
        enumerator: Iterator[Tuple[StorageKey, StorageItem]],
        prefix_length: int,
        options: FindOptions
    ):
        self._enumerator = enumerator
        self._prefix_length = prefix_length
        self._options = options
        self._current = None
    
    def next(self) -> bool:
        """Advance to next element."""
        try:
            self._current = next(self._enumerator)
            return True
        except StopIteration:
            self._current = None
            return False
    
    def value(self) -> StackItem:
        """Get current element."""
        from neo.vm.types import ByteString, Struct
        from neo.smartcontract.binary_serializer import BinarySerializer
        
        if self._current is None:
            raise ValueError("No current element")
        
        key, item = self._current
        key_bytes = key.key
        value_bytes = item.value
        
        # Remove prefix if requested
        if self._options & FindOptions.REMOVE_PREFIX:
            key_bytes = key_bytes[self._prefix_length:]
        
        # Deserialize value if requested
        if self._options & FindOptions.DESERIALIZE_VALUES:
            result = BinarySerializer.deserialize(value_bytes)
            # Pick field if requested
            if self._options & FindOptions.PICK_FIELD0:
                result = result[0]
            elif self._options & FindOptions.PICK_FIELD1:
                result = result[1]
        else:
            result = ByteString(value_bytes)
        
        # Return based on options
        if self._options & FindOptions.KEYS_ONLY:
            return ByteString(key_bytes)
        if self._options & FindOptions.VALUES_ONLY:
            return result
        
        return Struct([ByteString(key_bytes), result])
