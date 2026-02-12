"""
ISerializable - Interface for serializable objects.

Reference: Neo.IO.ISerializable
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from neo.io.binary_reader import BinaryReader
    from neo.io.binary_writer import BinaryWriter


class ISerializable(ABC):
    """Interface for objects that can be serialized/deserialized."""

    @property
    @abstractmethod
    def size(self) -> int:
        """Get the serialized size in bytes."""

    @abstractmethod
    def serialize(self, writer: "BinaryWriter") -> None:
        """Serialize the object to a binary writer."""

    @classmethod
    @abstractmethod
    def deserialize(cls, reader: "BinaryReader") -> Self:
        """Deserialize an object from a binary reader."""
