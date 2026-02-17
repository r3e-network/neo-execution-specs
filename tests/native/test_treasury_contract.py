"""Tests for Treasury contract."""

from types import SimpleNamespace

from neo.native.native_contract import CallFlags
from neo.native.treasury import Treasury


def test_treasury_name() -> None:
    treasury = Treasury()
    assert treasury.name == "Treasury"


def test_treasury_verify_checks_committee_signature() -> None:
    treasury = Treasury()

    assert treasury.verify(SimpleNamespace(check_committee=lambda: False)) is False
    assert treasury.verify(SimpleNamespace(check_committee=lambda: True)) is True


def test_treasury_method_metadata_matches_v391() -> None:
    treasury = Treasury()

    expected: dict[str, tuple[CallFlags, int]] = {
        "onNEP11Payment": (CallFlags.NONE, 1 << 5),
        "onNEP17Payment": (CallFlags.NONE, 1 << 5),
        "verify": (CallFlags.READ_STATES, 1 << 5),
    }

    for method_name, (expected_flags, expected_cpu_fee) in expected.items():
        metadata = treasury.get_method(method_name)
        assert metadata is not None, method_name
        assert metadata.required_call_flags == expected_flags, method_name
        assert metadata.cpu_fee == expected_cpu_fee, method_name
