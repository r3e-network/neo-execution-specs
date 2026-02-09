"""Tests for Log."""

from neo.smartcontract.log import LogEventArgs


def test_log():
    """Test log event."""
    log = LogEventArgs(script_hash=bytes(20), message="test")
    assert log.message == "test"
