"""Tests for Diagnostic."""

import pytest
from neo.smartcontract.diagnostic import Diagnostic


def test_diagnostic():
    """Test diagnostic."""
    d = Diagnostic()
    assert d.gas_consumed == 0
