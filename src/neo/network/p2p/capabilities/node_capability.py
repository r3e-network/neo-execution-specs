"""Neo N3 Node capabilities."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING
from collections.abc import Sequence

if TYPE_CHECKING:
    from neo.io.binary_reader import BinaryReader
    from neo.io.binary_writer import BinaryWriter


class NodeCapabilityType(IntEnum):
    """Node capability types."""

    # Servers
    TCP_SERVER = 0x01
    WS_SERVER = 0x02
    DISABLE_COMPRESSION = 0x03

    # Data availability
    FULL_NODE = 0x10
    ARCHIVAL_NODE = 0x11

    # Private extensions
    EXTENSION0 = 0xF0


MAX_CAPABILITIES = 32
MAX_UNKNOWN_CAPABILITY_DATA_BYTES = 1024

_SERVER_TYPES = {
    int(NodeCapabilityType.TCP_SERVER),
    int(NodeCapabilityType.WS_SERVER),
}
_ZERO_MARKER_TYPES = {
    int(NodeCapabilityType.DISABLE_COMPRESSION),
    int(NodeCapabilityType.ARCHIVAL_NODE),
}
_FULL_NODE_TYPE = int(NodeCapabilityType.FULL_NODE)
_KNOWN_TYPES = _SERVER_TYPES | _ZERO_MARKER_TYPES | {_FULL_NODE_TYPE}


def capability_type_value(capability: "NodeCapability | NodeCapabilityType | int") -> int:
    if isinstance(capability, NodeCapability):
        return capability.type
    return int(capability)


def _to_capability(
    capability: "NodeCapability | NodeCapabilityType | int",
) -> "NodeCapability":
    if isinstance(capability, NodeCapability):
        return capability

    capability_type = int(capability)
    if capability_type in _SERVER_TYPES:
        return NodeCapability(type=capability_type, port=0)
    if capability_type == _FULL_NODE_TYPE:
        return NodeCapability(type=capability_type, start_height=0)
    if capability_type in _ZERO_MARKER_TYPES:
        return NodeCapability(type=capability_type)
    return NodeCapability(type=capability_type, data=b"")


def normalize_capabilities(
    capabilities: Sequence["NodeCapability | NodeCapabilityType | int"],
    *,
    max_count: int = MAX_CAPABILITIES,
) -> list["NodeCapability"]:
    """Normalize and validate a capability list."""
    if len(capabilities) > max_count:
        raise ValueError(f"Capabilities count exceeds limit: {len(capabilities)}/{max_count}")

    normalized = [_to_capability(capability) for capability in capabilities]

    # Neo v3.9.1 rejects duplicate non-unknown capabilities by type.
    known_types = [capability.type for capability in normalized if capability.type in _KNOWN_TYPES]
    if len(known_types) != len(set(known_types)):
        raise ValueError("Duplicating capabilities are included")

    return normalized


def serialize_capabilities(
    writer: "BinaryWriter",
    capabilities: Sequence["NodeCapability | NodeCapabilityType | int"],
    *,
    max_count: int = MAX_CAPABILITIES,
) -> None:
    """Serialize a capability list with Neo v3.9.1 validation semantics."""
    normalized = normalize_capabilities(capabilities, max_count=max_count)
    writer.write_var_int(len(normalized))
    for capability in normalized:
        capability.serialize(writer)


def deserialize_capabilities(
    reader: "BinaryReader",
    *,
    max_count: int = MAX_CAPABILITIES,
) -> list["NodeCapability"]:
    """Deserialize a capability list with Neo v3.9.1 validation semantics."""
    count = reader.read_var_int(max_count)
    return [NodeCapability.deserialize(reader) for _ in range(count)]


@dataclass
class NodeCapability:
    """Node capability with type-specific payload."""

    type: int | NodeCapabilityType
    port: int | None = None
    start_height: int | None = None
    data: bytes = b""

    def __post_init__(self) -> None:
        self.type = int(self.type)
        if self.type < 0 or self.type > 0xFF:
            raise ValueError(f"Invalid capability type: {self.type}")

        if self.type in _SERVER_TYPES:
            if self.port is None:
                self.port = 0
            if self.port < 0 or self.port > 0xFFFF:
                raise ValueError(f"Invalid capability port: {self.port}")
            if self.start_height is not None:
                raise ValueError("Server capability cannot include start_height")
            if self.data:
                raise ValueError("Server capability cannot include opaque data")
            return

        if self.type == _FULL_NODE_TYPE:
            if self.start_height is None:
                self.start_height = 0
            if self.start_height < 0 or self.start_height > 0xFFFFFFFF:
                raise ValueError(f"Invalid start_height: {self.start_height}")
            if self.port is not None:
                raise ValueError("FullNode capability cannot include port")
            if self.data:
                raise ValueError("FullNode capability cannot include opaque data")
            return

        if self.type in _ZERO_MARKER_TYPES:
            if self.port is not None or self.start_height is not None:
                raise ValueError("Zero-marker capability cannot include typed payload")
            if self.data:
                raise ValueError("Zero-marker capability cannot include opaque data")
            return

        if self.port is not None or self.start_height is not None:
            raise ValueError("Unknown capability cannot include typed payload")
        if len(self.data) > MAX_UNKNOWN_CAPABILITY_DATA_BYTES:
            raise ValueError(
                "Unknown capability data exceeds limit: "
                f"{len(self.data)}/{MAX_UNKNOWN_CAPABILITY_DATA_BYTES}"
            )

    def serialize(self, writer: "BinaryWriter") -> None:
        """Serialize capability to wire format."""
        writer.write_byte(self.type)
        if self.type in _SERVER_TYPES:
            writer.write_uint16(self.port or 0)
            return
        if self.type == _FULL_NODE_TYPE:
            writer.write_uint32(self.start_height or 0)
            return
        if self.type in _ZERO_MARKER_TYPES:
            writer.write_byte(0)
            return
        writer.write_var_bytes(self.data)

    @classmethod
    def deserialize(cls, reader: "BinaryReader") -> "NodeCapability":
        """Deserialize capability from wire format."""
        capability_type = reader.read_byte()
        if capability_type in _SERVER_TYPES:
            return cls(type=capability_type, port=reader.read_uint16())
        if capability_type == _FULL_NODE_TYPE:
            return cls(type=capability_type, start_height=reader.read_uint32())
        if capability_type in _ZERO_MARKER_TYPES:
            zero = reader.read_byte()
            if zero != 0:
                raise ValueError(f"Capability {capability_type} has non-zero marker: {zero}")
            return cls(type=capability_type)
        return cls(
            type=capability_type,
            data=reader.read_var_bytes(MAX_UNKNOWN_CAPABILITY_DATA_BYTES),
        )
