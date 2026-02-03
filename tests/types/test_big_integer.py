"""Tests for BigInteger."""

import pytest
from neo.types.big_integer import BigInteger


class TestBigInteger:
    """Test BigInteger."""
    
    def test_create_zero(self):
        """Test create with zero."""
        bi = BigInteger(0)
        assert bi == 0
    
    def test_create_positive(self):
        """Test create with positive value."""
        bi = BigInteger(100)
        assert bi == 100
    
    def test_create_negative(self):
        """Test create with negative value."""
        bi = BigInteger(-100)
        assert bi == -100
    
    def test_create_large(self):
        """Test create with large value."""
        bi = BigInteger(2**256)
        assert bi == 2**256
    
    def test_max_size(self):
        """Test MAX_SIZE constant."""
        assert BigInteger.MAX_SIZE == 32
    
    def test_is_int(self):
        """Test that BigInteger is an int subclass."""
        bi = BigInteger(42)
        assert isinstance(bi, int)


class TestBigIntegerToBytes:
    """Tests for to_bytes_le method."""
    
    def test_zero(self):
        """Test zero to bytes."""
        bi = BigInteger(0)
        assert bi.to_bytes_le() == b"\x00"
    
    def test_one(self):
        """Test one to bytes."""
        bi = BigInteger(1)
        assert bi.to_bytes_le() == b"\x01"
    
    def test_127(self):
        """Test 127 (max positive single byte)."""
        bi = BigInteger(127)
        assert bi.to_bytes_le() == b"\x7f"
    
    def test_128(self):
        """Test 128 (needs sign byte)."""
        bi = BigInteger(128)
        assert bi.to_bytes_le() == b"\x80\x00"
    
    def test_255(self):
        """Test 255."""
        bi = BigInteger(255)
        assert bi.to_bytes_le() == b"\xff\x00"
    
    def test_256(self):
        """Test 256."""
        bi = BigInteger(256)
        assert bi.to_bytes_le() == b"\x00\x01"
    
    def test_negative_one(self):
        """Test -1 to bytes."""
        bi = BigInteger(-1)
        assert bi.to_bytes_le() == b"\xff"
    
    def test_negative_128(self):
        """Test -128."""
        bi = BigInteger(-128)
        assert bi.to_bytes_le() == b"\x80"
    
    def test_negative_129(self):
        """Test -129."""
        bi = BigInteger(-129)
        assert bi.to_bytes_le() == b"\x7f\xff"


class TestBigIntegerFromBytes:
    """Tests for from_bytes_le method."""
    
    def test_empty(self):
        """Test empty bytes."""
        bi = BigInteger.from_bytes_le(b"")
        assert bi == 0
    
    def test_zero(self):
        """Test zero byte."""
        bi = BigInteger.from_bytes_le(b"\x00")
        assert bi == 0
    
    def test_one(self):
        """Test one."""
        bi = BigInteger.from_bytes_le(b"\x01")
        assert bi == 1
    
    def test_127(self):
        """Test 127."""
        bi = BigInteger.from_bytes_le(b"\x7f")
        assert bi == 127
    
    def test_128_with_sign(self):
        """Test 128 with sign byte."""
        bi = BigInteger.from_bytes_le(b"\x80\x00")
        assert bi == 128
    
    def test_negative_one(self):
        """Test -1."""
        bi = BigInteger.from_bytes_le(b"\xff")
        assert bi == -1
    
    def test_negative_128(self):
        """Test -128."""
        bi = BigInteger.from_bytes_le(b"\x80")
        assert bi == -128


class TestBigIntegerRoundTrip:
    """Tests for round-trip conversion."""
    
    @pytest.mark.parametrize("value", [
        0, 1, -1, 127, 128, -128, -129,
        255, 256, -255, -256,
        32767, 32768, -32768, -32769,
        2**31 - 1, 2**31, -2**31, -2**31 - 1,
        2**63 - 1, 2**63, -2**63, -2**63 - 1,
    ])
    def test_round_trip(self, value):
        """Test round-trip conversion."""
        bi = BigInteger(value)
        data = bi.to_bytes_le()
        result = BigInteger.from_bytes_le(data)
        assert result == value


class TestBigIntegerArithmetic:
    """Tests for arithmetic operations."""
    
    def test_add(self):
        """Test addition."""
        a = BigInteger(10)
        b = BigInteger(20)
        assert a + b == 30
    
    def test_sub(self):
        """Test subtraction."""
        a = BigInteger(30)
        b = BigInteger(10)
        assert a - b == 20
    
    def test_mul(self):
        """Test multiplication."""
        a = BigInteger(5)
        b = BigInteger(6)
        assert a * b == 30
    
    def test_div(self):
        """Test division."""
        a = BigInteger(30)
        b = BigInteger(5)
        assert a // b == 6
    
    def test_mod(self):
        """Test modulo."""
        a = BigInteger(17)
        b = BigInteger(5)
        assert a % b == 2
    
    def test_pow(self):
        """Test power."""
        a = BigInteger(2)
        assert a ** 10 == 1024
