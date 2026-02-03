"""Tests for FindOptions."""

import pytest
from neo.smartcontract.storage.find_options import FindOptions


def test_find_options():
    """Test find options."""
    assert FindOptions.NONE == 0
    assert FindOptions.KEYS_ONLY == 1
