"""Tests for ECPoint arithmetic operations on secp256r1 and secp256k1.

Validates point addition, scalar multiplication, negation, identity,
and associativity using the curve generator point G.
"""

import pytest

from neo.crypto.ecc.curve import ECCurve, SECP256R1, SECP256K1
from neo.crypto.ecc.point import ECPoint


CURVES = [
    pytest.param(SECP256R1, id="secp256r1"),
    pytest.param(SECP256K1, id="secp256k1"),
]


def _infinity(curve: ECCurve) -> ECPoint:
    """Return the point at infinity for the given curve."""
    return ECPoint(0, 0, curve)


class TestGeneratorOnCurve:
    """Verify the generator point satisfies the curve equation."""

    @pytest.mark.parametrize("curve", CURVES)
    def test_generator_is_on_curve(self, curve: ECCurve):
        G = curve.g
        p = curve.p
        lhs = pow(G.y, 2, p)
        rhs = (pow(G.x, 3, p) + curve.a * G.x + curve.b) % p
        assert lhs == rhs, "Generator point is not on the curve"

    @pytest.mark.parametrize("curve", CURVES)
    def test_generator_not_infinity(self, curve: ECCurve):
        G = curve.g
        assert not G.is_infinity


class TestPointAddition:
    """Point addition: P + Q."""

    @pytest.mark.parametrize("curve", CURVES)
    def test_g_plus_g_equals_2g(self, curve: ECCurve):
        G = curve.g
        assert G + G == G * 2

    @pytest.mark.parametrize("curve", CURVES)
    def test_addition_commutative(self, curve: ECCurve):
        G = curve.g
        G2 = G + G
        assert G + G2 == G2 + G

    @pytest.mark.parametrize("curve", CURVES)
    def test_addition_associative(self, curve: ECCurve):
        G = curve.g
        lhs = (G + G) + G
        rhs = G + (G + G)
        assert lhs == rhs


class TestIdentity:
    """Identity element: G + O = G, O + G = G."""

    @pytest.mark.parametrize("curve", CURVES)
    def test_g_plus_identity(self, curve: ECCurve):
        G = curve.g
        infinity = _infinity(curve)
        assert G + infinity == G

    @pytest.mark.parametrize("curve", CURVES)
    def test_identity_plus_g(self, curve: ECCurve):
        G = curve.g
        infinity = _infinity(curve)
        assert infinity + G == G

    @pytest.mark.parametrize("curve", CURVES)
    def test_identity_plus_identity(self, curve: ECCurve):
        infinity = _infinity(curve)
        assert (infinity + infinity).is_infinity


class TestNegation:
    """Negation: G + (-G) = O."""

    @pytest.mark.parametrize("curve", CURVES)
    def test_g_plus_neg_g_is_identity(self, curve: ECCurve):
        G = curve.g
        result = G + (-G)
        assert result.is_infinity

    @pytest.mark.parametrize("curve", CURVES)
    def test_neg_neg_g_equals_g(self, curve: ECCurve):
        G = curve.g
        assert -(-G) == G

    @pytest.mark.parametrize("curve", CURVES)
    def test_neg_identity_is_identity(self, curve: ECCurve):
        infinity = _infinity(curve)
        assert (-infinity).is_infinity


class TestSubtraction:
    """Subtraction: P - Q = P + (-Q)."""

    @pytest.mark.parametrize("curve", CURVES)
    def test_g_minus_g_is_identity(self, curve: ECCurve):
        G = curve.g
        assert (G - G).is_infinity

    @pytest.mark.parametrize("curve", CURVES)
    def test_2g_minus_g_equals_g(self, curve: ECCurve):
        G = curve.g
        assert (G * 2) - G == G


class TestScalarMultiplication:
    """Scalar multiplication: k * G."""

    @pytest.mark.parametrize("curve", CURVES)
    def test_0_times_g_is_identity(self, curve: ECCurve):
        G = curve.g
        assert (G * 0).is_infinity

    @pytest.mark.parametrize("curve", CURVES)
    def test_1_times_g_is_g(self, curve: ECCurve):
        G = curve.g
        assert G * 1 == G

    @pytest.mark.parametrize("curve", CURVES)
    def test_3g_equals_g_plus_g_plus_g(self, curve: ECCurve):
        G = curve.g
        assert G * 3 == G + G + G

    @pytest.mark.parametrize("curve", CURVES)
    def test_rmul(self, curve: ECCurve):
        """k * G via __rmul__ should equal G * k."""
        G = curve.g
        assert 5 * G == G * 5

    @pytest.mark.parametrize("curve", CURVES)
    def test_n_times_g_is_identity(self, curve: ECCurve):
        """n * G = O where n is the curve order."""
        G = curve.g
        result = G * curve.n
        assert result.is_infinity

    @pytest.mark.parametrize("curve", CURVES)
    def test_negative_scalar(self, curve: ECCurve):
        G = curve.g
        assert G * (-1) == -G


class TestEncodeRoundtrip:
    """Encode/decode round-trip for computed points."""

    @pytest.mark.parametrize("curve", CURVES)
    def test_compressed_roundtrip(self, curve: ECCurve):
        P = curve.g * 7
        encoded = P.encode(compressed=True)
        decoded = ECPoint.decode(encoded, curve)
        assert decoded == P

    @pytest.mark.parametrize("curve", CURVES)
    def test_uncompressed_roundtrip(self, curve: ECCurve):
        P = curve.g * 7
        encoded = P.encode(compressed=False)
        decoded = ECPoint.decode(encoded, curve)
        assert decoded == P
