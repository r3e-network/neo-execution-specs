"""Tests for StdLib fixes - itoa negative hex and str_len grapheme."""

from types import SimpleNamespace

import pytest

from neo.hardfork import Hardfork
from neo.protocol_settings import ProtocolSettings
from neo.native.std_lib import StdLib
from neo.vm.types import ByteString


class TestItoaNegativeHex:
    """Test itoa with negative numbers in base 16."""
    
    def setup_method(self):
        self.stdlib = StdLib()
    
    def test_itoa_positive_hex(self):
        """Positive numbers should work as before."""
        assert self.stdlib.itoa(255, 16) == "0ff"
        assert self.stdlib.itoa(16, 16) == "10"
        assert self.stdlib.itoa(0, 16) == "0"
        assert self.stdlib.itoa(1, 16) == "1"
        assert self.stdlib.itoa(128, 16) == "080"
    
    def test_itoa_negative_hex_small(self):
        """Small negative numbers use minimal signed two's-complement hex."""
        result = self.stdlib.itoa(-1, 16)
        assert result == "f"
    
    def test_itoa_negative_hex_medium(self):
        """Medium negative numbers follow Neo/.NET BigInteger hex formatting."""
        result = self.stdlib.itoa(-128, 16)
        assert result == "80"
        
        result = self.stdlib.itoa(-256, 16)
        assert result == "f00"
    
    def test_itoa_negative_hex_large(self):
        """Larger negative numbers keep minimal signed width."""
        result = self.stdlib.itoa(-32768, 16)
        assert result == "8000"
    
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


class _StdLibHardforkEngine:
    def __init__(self, index: int, stack_items: list[ByteString] | None = None) -> None:
        settings = ProtocolSettings.mainnet()
        settings.hardforks[Hardfork.HF_ECHIDNA] = 100
        settings.hardforks[Hardfork.HF_FAUN] = 200

        self.protocol_settings = settings
        self.snapshot = SimpleNamespace(
            protocol_settings=settings,
            persisting_block=SimpleNamespace(index=index),
        )
        self._stack = list(stack_items or [])

    def pop(self) -> ByteString:
        return self._stack.pop()


class TestStdLibHardforkMethods:
    def setup_method(self):
        self.stdlib = StdLib()

    def test_echidna_methods_are_not_active_before_echidna_when_context_provided(self):
        pre = _StdLibHardforkEngine(index=99)
        with pytest.raises(KeyError, match="base64UrlEncode"):
            self.stdlib.base64_url_encode("hello", context=pre)
        with pytest.raises(KeyError, match="base64UrlDecode"):
            self.stdlib.base64_url_decode("aGVsbG8", context=pre)

        at = _StdLibHardforkEngine(index=100)
        encoded = self.stdlib.base64_url_encode("hello", context=at)
        assert encoded == "aGVsbG8"
        assert self.stdlib.base64_url_decode(encoded, context=at) == "hello"

    def test_faun_methods_are_not_active_before_faun_when_context_provided(self):
        pre = _StdLibHardforkEngine(index=199)
        with pytest.raises(KeyError, match="hexEncode"):
            self.stdlib.hex_encode(b"\xde\xad", context=pre)
        with pytest.raises(KeyError, match="hexDecode"):
            self.stdlib.hex_decode("deadbeef", context=pre)

        at = _StdLibHardforkEngine(index=200)
        assert self.stdlib.hex_encode(b"\xde\xad\xbe\xef", context=at) == "deadbeef"
        assert self.stdlib.hex_decode("deadbeef", context=at) == b"\xde\xad\xbe\xef"

    def test_engine_argument_dispatch_for_hardfork_unary_methods(self):
        pre_echidna = _StdLibHardforkEngine(index=99, stack_items=[ByteString(b"hello")])
        with pytest.raises(KeyError, match="base64UrlEncode"):
            self.stdlib.base64_url_encode(pre_echidna)

        at_echidna = _StdLibHardforkEngine(index=100, stack_items=[ByteString(b"hello")])
        assert self.stdlib.base64_url_encode(at_echidna) == "aGVsbG8"

        pre_faun = _StdLibHardforkEngine(index=199, stack_items=[ByteString(b"\xde\xad")])
        with pytest.raises(KeyError, match="hexEncode"):
            self.stdlib.hex_encode(pre_faun)

        at_faun = _StdLibHardforkEngine(index=200, stack_items=[ByteString(b"\xde\xad")])
        assert self.stdlib.hex_encode(at_faun) == "dead"

        at_faun_decode = _StdLibHardforkEngine(index=200, stack_items=[ByteString(b"deadbeef")])
        assert self.stdlib.hex_decode(at_faun_decode) == b"\xde\xad\xbe\xef"
