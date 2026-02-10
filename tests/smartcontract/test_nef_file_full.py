"""Comprehensive tests for NefFile serialization/deserialization.

Covers:
- MethodToken.to_json()
- NefFile.to_json()
- NefFile.to_array() / from_array() round-trip
- _write_var_int / _read_var_int edge cases
- from_array() validation (short data, bad magic)
- Tokens serialization round-trip
"""

from __future__ import annotations

import pytest
import struct

from neo.smartcontract.nef_file import NefFile, MethodToken


# ---------------------------------------------------------------------------
# MethodToken tests
# ---------------------------------------------------------------------------

class TestMethodToken:
    """MethodToken.to_json() serialization."""

    def test_to_json_basic(self):
        t = MethodToken(
            hash=b"\xaa" * 20,
            method="transfer",
            parameters_count=3,
            has_return_value=True,
            call_flags=15,
        )
        j = t.to_json()
        assert j["hash"] == "aa" * 20
        assert j["method"] == "transfer"
        assert j["paramcount"] == 3
        assert j["hasreturnvalue"] is True
        assert j["callflags"] == 15

    def test_to_json_defaults(self):
        t = MethodToken()
        j = t.to_json()
        assert j["hash"] == ""
        assert j["method"] == ""
        assert j["paramcount"] == 0
        assert j["hasreturnvalue"] is False


# ---------------------------------------------------------------------------
# NefFile.to_json() tests
# ---------------------------------------------------------------------------

class TestNefFileToJson:
    """NefFile.to_json() serialization."""

    def test_to_json_basic(self):
        nef = NefFile(
            compiler="neo-test-compiler 1.0",
            source="https://example.com",
            tokens=[],
            script=b"\x01\x02\x03",
            checksum=12345,
        )
        j = nef.to_json()
        assert j["magic"] == 0x3346454E
        assert j["compiler"] == "neo-test-compiler 1.0"
        assert j["source"] == "https://example.com"
        assert j["tokens"] == []
        assert j["checksum"] == 12345

    def test_to_json_with_tokens(self):
        t = MethodToken(hash=b"\xbb" * 20, method="m", parameters_count=1)
        nef = NefFile(tokens=[t], script=b"\x00")
        j = nef.to_json()
        assert len(j["tokens"]) == 1
        assert j["tokens"][0]["method"] == "m"

    def test_to_json_script_is_base64(self):
        import base64
        nef = NefFile(script=b"\x01\x02\x03")
        j = nef.to_json()
        decoded = base64.b64decode(j["script"])
        assert decoded == b"\x01\x02\x03"


# ---------------------------------------------------------------------------
# NefFile.to_array() / from_array() round-trip
# ---------------------------------------------------------------------------

class TestNefFileRoundTrip:
    """NefFile serialization round-trip."""

    def test_roundtrip_no_tokens(self):
        nef = NefFile(
            compiler="test-compiler",
            source="https://example.com",
            tokens=[],
            script=b"\x01\x02\x03",
            checksum=0xDEADBEEF,
        )
        data = nef.to_array()
        restored = NefFile.from_array(data)
        assert restored.compiler == "test-compiler"
        assert restored.source == "https://example.com"
        assert restored.tokens == []
        assert restored.script == b"\x01\x02\x03"
        assert restored.checksum == 0xDEADBEEF

    def test_roundtrip_with_tokens(self):
        t = MethodToken(
            hash=b"\xcc" * 20,
            method="transfer",
            parameters_count=3,
            has_return_value=True,
            call_flags=15,
        )
        nef = NefFile(
            compiler="neo3-boa",
            source="",
            tokens=[t],
            script=b"\x40\x41\x42",
            checksum=999,
        )
        data = nef.to_array()
        restored = NefFile.from_array(data)
        assert restored.compiler == "neo3-boa"
        assert len(restored.tokens) == 1
        rt = restored.tokens[0]
        assert rt.hash == b"\xcc" * 20
        assert rt.method == "transfer"
        assert rt.parameters_count == 3
        assert rt.has_return_value is True
        assert rt.call_flags == 15
        assert restored.script == b"\x40\x41\x42"
        assert restored.checksum == 999

    def test_roundtrip_empty_script(self):
        nef = NefFile(compiler="c", source="", tokens=[], script=b"", checksum=0)
        data = nef.to_array()
        restored = NefFile.from_array(data)
        assert restored.script == b""
        assert restored.checksum == 0

    def test_roundtrip_multiple_tokens(self):
        tokens = [
            MethodToken(hash=b"\x01" * 20, method="a", parameters_count=0),
            MethodToken(hash=b"\x02" * 20, method="bb", parameters_count=2,
                        has_return_value=True, call_flags=7),
        ]
        nef = NefFile(compiler="x", tokens=tokens, script=b"\xff", checksum=42)
        data = nef.to_array()
        restored = NefFile.from_array(data)
        assert len(restored.tokens) == 2
        assert restored.tokens[0].method == "a"
        assert restored.tokens[1].method == "bb"
        assert restored.tokens[1].has_return_value is True

    def test_roundtrip_long_compiler(self):
        """Compiler field is truncated to 64 bytes."""
        long_name = "A" * 100
        nef = NefFile(compiler=long_name, script=b"\x00", checksum=1)
        data = nef.to_array()
        restored = NefFile.from_array(data)
        assert restored.compiler == "A" * 64


# ---------------------------------------------------------------------------
# _write_var_int / _read_var_int edge cases
# ---------------------------------------------------------------------------

class TestVarInt:
    """Variable-length integer encoding/decoding."""

    def test_single_byte_zero(self):
        data = NefFile._write_var_int(0)
        assert data == b"\x00"
        val, off = NefFile._read_var_int(data, 0)
        assert val == 0 and off == 1

    def test_single_byte_max(self):
        data = NefFile._write_var_int(0xFC)
        assert len(data) == 1
        val, off = NefFile._read_var_int(data, 0)
        assert val == 0xFC and off == 1

    def test_two_byte_boundary(self):
        """0xFD triggers 2-byte encoding."""
        data = NefFile._write_var_int(0xFD)
        assert data[0] == 0xFD
        assert len(data) == 3
        val, off = NefFile._read_var_int(data, 0)
        assert val == 0xFD and off == 3

    def test_two_byte_max(self):
        data = NefFile._write_var_int(0xFFFF)
        assert data[0] == 0xFD
        val, off = NefFile._read_var_int(data, 0)
        assert val == 0xFFFF and off == 3

    def test_four_byte_boundary(self):
        """0x10000 triggers 4-byte encoding."""
        data = NefFile._write_var_int(0x10000)
        assert data[0] == 0xFE
        assert len(data) == 5
        val, off = NefFile._read_var_int(data, 0)
        assert val == 0x10000 and off == 5

    def test_four_byte_max(self):
        data = NefFile._write_var_int(0xFFFFFFFF)
        assert data[0] == 0xFE
        val, off = NefFile._read_var_int(data, 0)
        assert val == 0xFFFFFFFF and off == 5

    def test_eight_byte_boundary(self):
        """0x100000000 triggers 8-byte encoding."""
        data = NefFile._write_var_int(0x100000000)
        assert data[0] == 0xFF
        assert len(data) == 9
        val, off = NefFile._read_var_int(data, 0)
        assert val == 0x100000000 and off == 9

    def test_read_with_offset(self):
        """_read_var_int respects starting offset."""
        prefix = b"\xAA\xBB"
        var_data = NefFile._write_var_int(300)
        combined = prefix + var_data
        val, off = NefFile._read_var_int(combined, 2)
        assert val == 300
        assert off == 2 + len(var_data)


# ---------------------------------------------------------------------------
# from_array() validation
# ---------------------------------------------------------------------------

class TestNefFileValidation:
    """from_array() error handling."""

    def test_short_data_raises(self):
        with pytest.raises(ValueError, match="too short"):
            NefFile.from_array(b"\x00\x01\x02")

    def test_empty_data_raises(self):
        with pytest.raises(ValueError, match="too short"):
            NefFile.from_array(b"")

    def test_bad_magic_raises(self):
        bad = struct.pack('<I', 0xDEADBEEF) + b"\x00" * 200
        with pytest.raises(ValueError, match="Invalid NEF magic"):
            NefFile.from_array(bad)

    def test_exactly_four_bytes_bad_magic(self):
        with pytest.raises(ValueError, match="Invalid NEF magic"):
            NefFile.from_array(b"\x00\x00\x00\x00")
