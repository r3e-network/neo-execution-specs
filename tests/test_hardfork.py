"""Tests for Hardfork definitions."""

import pytest
from neo.hardfork import Hardfork


class TestHardfork:
    """Tests for Hardfork enum."""
    
    def test_aspidochelone(self):
        """Test HF_ASPIDOCHELONE value."""
        assert Hardfork.HF_ASPIDOCHELONE == 0
    
    def test_basilisk(self):
        """Test HF_BASILISK value."""
        assert Hardfork.HF_BASILISK == 1
    
    def test_cockatrice(self):
        """Test HF_COCKATRICE value."""
        assert Hardfork.HF_COCKATRICE == 2
    
    def test_domovoi(self):
        """Test HF_DOMOVOI value."""
        assert Hardfork.HF_DOMOVOI == 3

    def test_echidna(self):
        """Test HF_ECHIDNA value."""
        assert Hardfork.HF_ECHIDNA == 4

    def test_faun(self):
        """Test HF_FAUN value."""
        assert Hardfork.HF_FAUN == 5

    def test_gorgon(self):
        """Test HF_GORGON value."""
        assert Hardfork.HF_GORGON == 6
    
    def test_is_int_enum(self):
        """Test that Hardfork is IntEnum."""
        assert isinstance(Hardfork.HF_ASPIDOCHELONE, int)
    
    def test_ordering(self):
        """Test hardfork ordering."""
        assert Hardfork.HF_ASPIDOCHELONE < Hardfork.HF_BASILISK
        assert Hardfork.HF_BASILISK < Hardfork.HF_COCKATRICE
        assert Hardfork.HF_COCKATRICE < Hardfork.HF_DOMOVOI
        assert Hardfork.HF_DOMOVOI < Hardfork.HF_ECHIDNA
        assert Hardfork.HF_ECHIDNA < Hardfork.HF_FAUN
        assert Hardfork.HF_FAUN < Hardfork.HF_GORGON
    
    def test_all_hardforks(self):
        """Test all hardforks are defined."""
        hardforks = list(Hardfork)
        assert len(hardforks) == 7
