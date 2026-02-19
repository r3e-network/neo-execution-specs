"""Neo N3 Version Payload."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from neo.network.p2p.capabilities.node_capability import (
    MAX_CAPABILITIES,
    capability_type_value,
    deserialize_capabilities,
    normalize_capabilities,
    NodeCapability,
    NodeCapabilityType,
    serialize_capabilities,
)

if TYPE_CHECKING:
    from neo.io.binary_reader import BinaryReader
    from neo.io.binary_writer import BinaryWriter


@dataclass
class VersionPayload:
    """Version message payload."""

    MAX_USER_AGENT_BYTES = 1024

    network: int
    version: int
    timestamp: int
    nonce: int
    user_agent: str
    capabilities: list[NodeCapability] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.network < 0 or self.network > 0xFFFFFFFF:
            raise ValueError(f"Invalid network: {self.network}")
        if self.version < 0 or self.version > 0xFFFFFFFF:
            raise ValueError(f"Invalid version: {self.version}")
        if self.timestamp < 0 or self.timestamp > 0xFFFFFFFF:
            raise ValueError(f"Invalid timestamp: {self.timestamp}")
        if self.nonce < 0 or self.nonce > 0xFFFFFFFF:
            raise ValueError(f"Invalid nonce: {self.nonce}")

        user_agent_bytes = self.user_agent.encode("utf-8")
        if len(user_agent_bytes) > self.MAX_USER_AGENT_BYTES:
            raise ValueError(
                "UserAgent length exceeds limit: "
                f"{len(user_agent_bytes)}/{self.MAX_USER_AGENT_BYTES}"
            )

        self.capabilities = normalize_capabilities(self.capabilities, max_count=MAX_CAPABILITIES)

    @property
    def allow_compression(self) -> bool:
        """Whether peer compression is allowed for this version payload."""
        return all(
            capability_type_value(capability) != int(NodeCapabilityType.DISABLE_COMPRESSION)
            for capability in self.capabilities
        )

    def serialize(self, writer: "BinaryWriter") -> None:
        """Serialize payload to wire format."""
        writer.write_uint32(self.network)
        writer.write_uint32(self.version)
        writer.write_uint32(self.timestamp)
        writer.write_uint32(self.nonce)
        writer.write_var_string(self.user_agent)
        serialize_capabilities(writer, self.capabilities, max_count=MAX_CAPABILITIES)

    @classmethod
    def deserialize(cls, reader: "BinaryReader") -> "VersionPayload":
        """Deserialize payload from wire format."""
        network = reader.read_uint32()
        version = reader.read_uint32()
        timestamp = reader.read_uint32()
        nonce = reader.read_uint32()
        user_agent = reader.read_var_string(cls.MAX_USER_AGENT_BYTES)
        capabilities = deserialize_capabilities(reader, max_count=MAX_CAPABILITIES)
        return cls(
            network=network,
            version=version,
            timestamp=timestamp,
            nonce=nonce,
            user_agent=user_agent,
            capabilities=capabilities,
        )
