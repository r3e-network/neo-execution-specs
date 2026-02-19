"""Neo N3 v3.9.1 network protocol-surface regression checks."""

from __future__ import annotations

from dataclasses import fields

from neo.network.p2p.capabilities.node_capability import NodeCapabilityType
from neo.network.p2p.message_command import MessageCommand
from neo.network.payloads.addr import AddrPayload, NetworkAddress
from neo.network.payloads.ping import PingPayload
from neo.network.payloads.version import VersionPayload


def _field_names(cls: type) -> set[str]:
    return {item.name for item in fields(cls)}


def test_message_command_values_match_neo_v391() -> None:
    expected_values = {
        "VERSION": 0x00,
        "VERACK": 0x01,
        "GETADDR": 0x10,
        "ADDR": 0x11,
        "PING": 0x18,
        "PONG": 0x19,
        "GETHEADERS": 0x20,
        "HEADERS": 0x21,
        "GETBLOCKS": 0x24,
        "MEMPOOL": 0x25,
        "INV": 0x27,
        "GETDATA": 0x28,
        "GETBLOCKBYINDEX": 0x29,
        "NOTFOUND": 0x2A,
        "TRANSACTION": 0x2B,
        "BLOCK": 0x2C,
        "EXTENSIBLE": 0x2E,
        "REJECT": 0x2F,
        "FILTERLOAD": 0x30,
        "FILTERADD": 0x31,
        "FILTERCLEAR": 0x32,
        "MERKLEBLOCK": 0x38,
        "ALERT": 0x40,
    }

    for name, expected in expected_values.items():
        assert getattr(MessageCommand, name).value == expected

    # Backward-compatible alias.
    assert MessageCommand.TX.value == MessageCommand.TRANSACTION.value


def test_node_capability_type_values_match_neo_v391() -> None:
    expected_values = {
        "TCP_SERVER": 0x01,
        "WS_SERVER": 0x02,
        "DISABLE_COMPRESSION": 0x03,
        "FULL_NODE": 0x10,
        "ARCHIVAL_NODE": 0x11,
        "EXTENSION0": 0xF0,
    }

    for name, expected in expected_values.items():
        assert getattr(NodeCapabilityType, name).value == expected


def test_version_payload_shape_matches_neo_v391() -> None:
    assert _field_names(VersionPayload) == {
        "network",
        "version",
        "timestamp",
        "nonce",
        "user_agent",
        "capabilities",
    }

    payload = VersionPayload(
        network=860833102,
        version=0,
        timestamp=0,
        nonce=1,
        user_agent="/Neo:3.9.1/",
        capabilities=[],
    )
    assert payload.allow_compression is True

    payload.capabilities = [NodeCapabilityType.DISABLE_COMPRESSION]
    assert payload.allow_compression is False


def test_addr_payload_shape_matches_neo_v391() -> None:
    assert _field_names(NetworkAddress) == {"timestamp", "address", "capabilities"}
    assert _field_names(AddrPayload) == {"address_list"}

    payload = AddrPayload(
        address_list=[
            NetworkAddress(
                timestamp=1,
                address="127.0.0.1",
                capabilities=[NodeCapabilityType.TCP_SERVER],
            )
        ]
    )
    assert len(payload.address_list) == 1


def test_message_command_only_has_transaction_alias_duplicate_value() -> None:
    value_to_names: dict[int, list[str]] = {}
    for name, member in MessageCommand.__members__.items():
        value_to_names.setdefault(member.value, []).append(name)

    duplicates = {
        value: names
        for value, names in value_to_names.items()
        if len(names) > 1
    }
    assert duplicates == {0x2B: ["TRANSACTION", "TX"]}


def test_ping_payload_shape_matches_neo_v391() -> None:
    assert _field_names(PingPayload) == {"last_block_index", "timestamp", "nonce"}

    payload = PingPayload(
        last_block_index=0xFFFFFFFF,
        timestamp=0xFFFFFFFF,
        nonce=0xFFFFFFFF,
    )

    assert payload.last_block_index == 0xFFFFFFFF
    assert payload.timestamp == 0xFFFFFFFF
    assert payload.nonce == 0xFFFFFFFF
