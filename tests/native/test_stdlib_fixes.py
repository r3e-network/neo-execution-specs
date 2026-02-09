"""Tests for StdLib fixes - itoa negative hex and str_len grapheme."""

from neo.native.std_lib import StdLib


class TestItoaNegativeHex:
    """Test itoa with negative numbers in base 16."""
    
    def setup_method(self):
        self.stdlib = StdLib()
    
    def test_itoa_positive_hex(self):
        """Positive numbers should work as before."""
        assert self.stdlib.itoa(255, 16) == "FF"
        assert self.stdlib.itoa(16, 16) == "10"
        assert self.stdlib.itoa(0, 16) == "0"
        assert self.stdlib.itoa(1, 16) == "1"
    
    def test_itoa_negative_hex_small(self):
        """Small negative numbers use two's complement."""
        # -1 in two's complement is FF
        result = self.stdlib.itoa(-1, 16)
        assert result == "FF"
    
    def test_itoa_negative_hex_medium(self):
        """Medium negative numbers - C# BigInteger uses sign-extended two's complement."""
        # -128 needs sign extension: 0x80 would be +128, so it becomes FF80
        result = self.stdlib.itoa(-128, 16)
        assert result == "FF80"
        
        # -256 = FF00
        result = self.stdlib.itoa(-256, 16)
        assert result == "FF00"
    
    def test_itoa_negative_hex_large(self):
        """Larger negative numbers with sign extension."""
        # -32768 needs sign extension: 0x8000 would be +32768, so FF8000
        result = self.stdlib.itoa(-32768, 16)
        assert result == "FF8000"
    
    def test_itoa_decimal(self):
        """Decimal conversion should still work."""
        assert self.stdlib.itoa(123, 10) == "123"
        assert self.stdlib.itoa(-123, 10) == "-123"
        assert self.stdlib.itoa(0, 10) == "0"


class TestStrLenGrapheme:
    """Test str_len with grapheme clusters."""
    
    def setup_method(self):
        self.stdlib = StdLib()
    
    def test_str_len_ascii(self):
        """ASCII strings should count characters."""
        assert self.stdlib.str_len("hello") == 5
        assert self.stdlib.str_len("") == 0
        assert self.stdlib.str_len("a") == 1
    
    def test_str_len_emoji(self):
        """Emoji should count as single grapheme clusters."""
        # Single emoji
        assert self.stdlib.str_len("😀") == 1
        # Multiple emoji
        assert self.stdlib.str_len("😀😀😀") == 3
    
    def test_str_len_combined_emoji(self):
        """Combined emoji (ZWJ sequences) should count as one."""
        # Family emoji (man + ZWJ + woman + ZWJ + girl)
        family = "👨‍👩‍👧"
        assert self.stdlib.str_len(family) == 1
        
        # Flag emoji (regional indicators)
        flag = "🇺🇸"
        assert self.stdlib.str_len(flag) == 1
    
    def test_str_len_combining_marks(self):
        """Characters with combining marks should count as one."""
        # e + combining acute accent
        e_acute = "e\u0301"
        assert self.stdlib.str_len(e_acute) == 1
        
        # a + combining ring above
        a_ring = "a\u030a"
        assert self.stdlib.str_len(a_ring) == 1
    
    def test_str_len_mixed(self):
        """Mixed content."""
        # "Hello" + flag + emoji
        mixed = "Hello🇺🇸😀"
        assert self.stdlib.str_len(mixed) == 7  # 5 + 1 + 1
    
    def test_str_len_hangul(self):
        """Korean Hangul characters."""
        # 한글 = 2 grapheme clusters
        assert self.stdlib.str_len("한글") == 2
    
    def test_str_len_chinese(self):
        """Chinese characters."""
        assert self.stdlib.str_len("中文") == 2
        assert self.stdlib.str_len("你好世界") == 4
