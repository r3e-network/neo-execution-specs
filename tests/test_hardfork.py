"""Tests for hardfork."""

import pytest
from neo.hardfork import Hardfork


def test_hardforks():
    """Test hardfork values."""
    assert Hardfork.HF_ASPIDOCHELONE == 0
    assert Hardfork.HF_BASILISK == 1
