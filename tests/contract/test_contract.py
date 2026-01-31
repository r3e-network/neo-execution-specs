"""Tests for contract module."""

import pytest
from neo.contract import NefFile, ContractManifest


def test_nef_creation():
    """Test NEF file creation."""
    nef = NefFile(
        compiler="test-compiler",
        script=bytes([0x10, 0x40])  # PUSH0, RET
    )
    assert nef.compiler == "test-compiler"
    assert len(nef.script) == 2


def test_manifest_creation():
    """Test manifest creation."""
    manifest = ContractManifest(
        name="TestContract",
        supported_standards=["NEP-17"]
    )
    assert manifest.name == "TestContract"
    assert "NEP-17" in manifest.supported_standards
