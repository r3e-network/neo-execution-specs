"""
ISerializable - Interface for serializable objects.

Reference: Neo.IO.ISerializable
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.io.binary_reader import BinaryReader
    from neo.io.binary_writer import BinaryWriter


class ISerializable(ABC):
    """Interface for objects that can be serialized/deserialized."""
    
    @property
    @abstractmethod
    def size(self) -> int:
        """Get the serialized size in bytes."""
        pass
    
    @abstractmethod
    def serialize(self, writer: "BinaryWriter") -> None:
        """Serialize the object to a binary writer."""
        pass
    
    @classmethod
    @abstractmethod
    def deserialize(cls, reader: "BinaryReader") -> "ISerializable":
        """Deserialize an object from a binary reader."""
        pass
