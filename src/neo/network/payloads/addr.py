"""Neo N3 Addr Payload."""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from neo.network.p2p.capabilities.node_capability import (
    MAX_CAPABILITIES,
    NodeCapability,
    NodeCapabilityType,
    capability_type_value,
    deserialize_capabilities,
    normalize_capabilities,
    serialize_capabilities,
)

if TYPE_CHECKING:
    from neo.io.binary_reader import BinaryReader
    from neo.io.binary_writer import BinaryWriter


@dataclass
class NetworkAddress:
    """Network address."""

    timestamp: int
    address: str
    capabilities: list[NodeCapability] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.timestamp < 0 or self.timestamp > 0xFFFFFFFF:
            raise ValueError(f"Invalid timestamp: {self.timestamp}")

        ip = ipaddress.ip_address(self.address)
        self.address = str(ip)

        self.capabilities = normalize_capabilities(self.capabilities, max_count=MAX_CAPABILITIES)

    @property
    def endpoint_port(self) -> int:
        """Get TCP endpoint port (0 when no TCP capability)."""
        for capability in self.capabilities:
            if capability_type_value(capability) == int(NodeCapabilityType.TCP_SERVER):
                if isinstance(capability, NodeCapability) and capability.port is not None:
                    return capability.port
                return 0
        return 0

    def serialize(self, writer: "BinaryWriter") -> None:
        """Serialize address to wire format."""
        writer.write_uint32(self.timestamp)

        ip = ipaddress.ip_address(self.address)
        if isinstance(ip, ipaddress.IPv4Address):
            ipv6 = ipaddress.IPv6Address(f"::ffff:{ip}")
        else:
            ipv6 = ip
        writer.write_bytes(ipv6.packed)

        serialize_capabilities(writer, self.capabilities)

    @classmethod
    def deserialize(cls, reader: "BinaryReader") -> "NetworkAddress":
        """Deserialize address from wire format."""
        timestamp = reader.read_uint32()
        raw = reader.read_bytes(16)
        ipv6 = ipaddress.IPv6Address(raw)
        if ipv6.ipv4_mapped is not None:
            ip = str(ipv6.ipv4_mapped)
        else:
            ip = str(ipv6)

        capabilities = deserialize_capabilities(reader)

        return cls(timestamp=timestamp, address=ip, capabilities=capabilities)


@dataclass
class AddrPayload:
    """Address list payload."""

    MAX_COUNT_TO_SEND = 200

    address_list: list[NetworkAddress] = field(default_factory=list)

    def __post_init__(self) -> None:
        if len(self.address_list) > self.MAX_COUNT_TO_SEND:
            raise ValueError(
                f"Address count exceeds limit: {len(self.address_list)}/{self.MAX_COUNT_TO_SEND}"
            )

    def serialize(self, writer: "BinaryWriter") -> None:
        """Serialize payload to wire format."""
        writer.write_var_int(len(self.address_list))
        for address in self.address_list:
            address.serialize(writer)

    @classmethod
    def deserialize(cls, reader: "BinaryReader") -> "AddrPayload":
        """Deserialize payload from wire format."""
        count = reader.read_var_int(cls.MAX_COUNT_TO_SEND)
        addresses = [NetworkAddress.deserialize(reader) for _ in range(count)]
        if not addresses:
            raise ValueError("`AddressList` in AddrPayload is empty")
        return cls(address_list=addresses)
