"""Tests for GAS costs."""

import pytest
from neo.vm.gas import OPCODE_PRICE


def test_gas_prices():
    """Test gas prices."""
    assert OPCODE_PRICE[0x10] == 1
