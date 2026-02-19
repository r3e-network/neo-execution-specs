"""Neo N3 v3.9.1 capabilities/address/version wire parity checks."""

from __future__ import annotations

import pytest

from neo.io.binary_reader import BinaryReader
from neo.io.binary_writer import BinaryWriter
from neo.network.p2p.capabilities.node_capability import (
    MAX_CAPABILITIES,
    NodeCapability,
    NodeCapabilityType,
    deserialize_capabilities,
    serialize_capabilities,
)
from neo.network.payloads.addr import AddrPayload, NetworkAddress
from neo.network.payloads.version import VersionPayload


def _roundtrip(payload, cls):
    writer = BinaryWriter()
    payload.serialize(writer)
    data = writer.to_bytes()
    reader = BinaryReader(data)
    clone = cls.deserialize(reader)
    assert reader.remaining == 0
    return clone


def test_node_capability_roundtrip_known_types() -> None:
    for capability in (
        NodeCapability(type=NodeCapabilityType.TCP_SERVER, port=20333),
        NodeCapability(type=NodeCapabilityType.WS_SERVER, port=20334),
        NodeCapability(type=NodeCapabilityType.FULL_NODE, start_height=12345),
        NodeCapability(type=NodeCapabilityType.ARCHIVAL_NODE),
        NodeCapability(type=NodeCapabilityType.DISABLE_COMPRESSION),
    ):
        clone = _roundtrip(capability, NodeCapability)
        assert clone.type == int(capability.type)
        assert clone.port == capability.port
        assert clone.start_height == capability.start_height
        assert clone.data == capability.data


def test_node_capability_roundtrip_unknown_type() -> None:
    payload = NodeCapability(type=0xFE, data=b"\x01\x02\x03")
    clone = _roundtrip(payload, NodeCapability)
    assert clone.type == 0xFE
    assert clone.data == b"\x01\x02\x03"


def test_capability_list_helpers_roundtrip_and_duplicate_guard() -> None:
    writer = BinaryWriter()
    serialize_capabilities(
        writer,
        [
            NodeCapabilityType.TCP_SERVER,
            NodeCapability(type=NodeCapabilityType.FULL_NODE, start_height=7),
            NodeCapability(type=0xFE, data=b"\xAA"),
        ],
    )
    reader = BinaryReader(writer.to_bytes())
    capabilities = deserialize_capabilities(reader)
    assert reader.remaining == 0
    assert len(capabilities) == 3
    assert capabilities[0].type == int(NodeCapabilityType.TCP_SERVER)
    assert capabilities[0].port == 0
    assert capabilities[1].type == int(NodeCapabilityType.FULL_NODE)
    assert capabilities[1].start_height == 7
    assert capabilities[2].type == 0xFE
    assert capabilities[2].data == b"\xAA"

    with pytest.raises(ValueError):
        serialize_capabilities(
            BinaryWriter(),
            [NodeCapabilityType.TCP_SERVER, NodeCapabilityType.TCP_SERVER],
        )


def test_node_capability_zero_marker_guard() -> None:
    writer = BinaryWriter()
    writer.write_byte(int(NodeCapabilityType.ARCHIVAL_NODE))
    writer.write_byte(1)
    with pytest.raises(ValueError):
        NodeCapability.deserialize(BinaryReader(writer.to_bytes()))

    writer = BinaryWriter()
    writer.write_byte(int(NodeCapabilityType.DISABLE_COMPRESSION))
    writer.write_byte(1)
    with pytest.raises(ValueError):
        NodeCapability.deserialize(BinaryReader(writer.to_bytes()))


def test_version_payload_roundtrip_and_limits() -> None:
    payload = VersionPayload(
        network=860833102,
        version=0,
        timestamp=123,
        nonce=456,
        user_agent="/Neo:3.9.1/",
        capabilities=[
            NodeCapability(type=NodeCapabilityType.TCP_SERVER, port=20333),
            NodeCapability(type=NodeCapabilityType.FULL_NODE, start_height=100),
            NodeCapability(type=NodeCapabilityType.DISABLE_COMPRESSION),
            NodeCapability(type=0xFE, data=b""),
            NodeCapability(type=0xFE, data=b"\x01"),
        ],
    )
    clone = _roundtrip(payload, VersionPayload)
    assert clone.network == payload.network
    assert clone.user_agent == payload.user_agent
    assert clone.allow_compression is False

    with pytest.raises(ValueError):
        VersionPayload(
            network=860833102,
            version=0,
            timestamp=0,
            nonce=1,
            user_agent="/Neo:3.9.1/",
            capabilities=[
                NodeCapability(type=NodeCapabilityType.TCP_SERVER, port=22),
                NodeCapability(type=NodeCapabilityType.TCP_SERVER, port=23),
            ],
        )

    with pytest.raises(ValueError):
        VersionPayload(
            network=860833102,
            version=0,
            timestamp=0,
            nonce=1,
            user_agent="/Neo:3.9.1/",
            capabilities=[NodeCapability(type=0xFE, data=b"")] * (MAX_CAPABILITIES + 1),
        )

    with pytest.raises(ValueError):
        VersionPayload(
            network=860833102,
            version=0,
            timestamp=0,
            nonce=1,
            user_agent="/" + ("a" * 2000),
            capabilities=[],
        )


def test_addr_payload_roundtrip_ipv4_ipv6_and_empty_deserialize_guard() -> None:
    payload = AddrPayload(
        address_list=[
            NetworkAddress(
                timestamp=1,
                address="127.0.0.1",
                capabilities=[NodeCapability(type=NodeCapabilityType.TCP_SERVER, port=20333)],
            ),
            NetworkAddress(
                timestamp=2,
                address="::1",
                capabilities=[NodeCapability(type=NodeCapabilityType.FULL_NODE, start_height=42)],
            ),
        ]
    )
    clone = _roundtrip(payload, AddrPayload)
    assert len(clone.address_list) == 2
    assert clone.address_list[0].address == "127.0.0.1"
    assert clone.address_list[0].endpoint_port == 20333

    with pytest.raises(ValueError):
        NetworkAddress(
            timestamp=1,
            address="127.0.0.1",
            capabilities=[
                NodeCapability(type=NodeCapabilityType.TCP_SERVER, port=22),
                NodeCapability(type=NodeCapabilityType.TCP_SERVER, port=23),
            ],
        )

    with pytest.raises(ValueError):
        AddrPayload.deserialize(BinaryReader(b"\x00"))


def test_version_payload_serialize_revalidates_mutated_capabilities() -> None:
    payload = VersionPayload(
        network=860833102,
        version=0,
        timestamp=0,
        nonce=1,
        user_agent="/Neo:3.9.1/",
        capabilities=[],
    )
    payload.capabilities.extend(
        [
            NodeCapabilityType.TCP_SERVER,
            NodeCapabilityType.TCP_SERVER,
        ]
    )

    with pytest.raises(ValueError):
        payload.serialize(BinaryWriter())


def test_network_address_serialize_revalidates_mutated_capabilities() -> None:
    address = NetworkAddress(
        timestamp=1,
        address="127.0.0.1",
        capabilities=[],
    )
    address.capabilities.extend(
        [NodeCapabilityType.TCP_SERVER] * (MAX_CAPABILITIES + 1)
    )

    with pytest.raises(ValueError):
        address.serialize(BinaryWriter())

    duplicate_types = NetworkAddress(
        timestamp=1,
        address="127.0.0.1",
        capabilities=[],
    )
    duplicate_types.capabilities.extend(
        [NodeCapabilityType.TCP_SERVER, NodeCapabilityType.TCP_SERVER]
    )

    with pytest.raises(ValueError):
        duplicate_types.serialize(BinaryWriter())
