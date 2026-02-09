"""Tests for StdLib native contract."""

from neo.native.std_lib import StdLib, MAX_INPUT_LENGTH


class TestStdLib:
    """Tests for StdLib."""
    
    def test_name(self):
        """Test contract name."""
        stdlib = StdLib()
        assert stdlib.name == "StdLib"
    
    def test_max_input_length(self):
        """Test max input length constant."""
        assert MAX_INPUT_LENGTH == 1024
