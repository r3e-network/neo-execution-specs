"""
BLS12-381 G2 group elements.

G2 is the group of points on the twisted curve over Fp2.
Points are represented in compressed form as 96 bytes.
"""

from __future__ import annotations
from typing import Union, Tuple

from .scalar import Scalar, SCALAR_MODULUS


# BLS12-381 base field modulus
P = 0x1a0111ea397fe69a4b1ba7b6434bacd764774b84f38512bf6730d2a0f6b0f6241eabfffeb153ffffb9feffffffffaaab


class Fp2:
    """Element of Fp2 = Fp[u]/(u^2 + 1)."""
    
    __slots__ = ('c0', 'c1')
    
    def __init__(self, c0: int = 0, c1: int = 0) -> None:
        self.c0 = c0 % P
        self.c1 = c1 % P
    
    @classmethod
    def zero(cls) -> Fp2:
        return cls(0, 0)
    
    @classmethod
    def one(cls) -> Fp2:
        return cls(1, 0)
    
    def is_zero(self) -> bool:
        return self.c0 == 0 and self.c1 == 0
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Fp2):
            return self.c0 == other.c0 and self.c1 == other.c1
        return False
    
    def __neg__(self) -> Fp2:
        return Fp2(P - self.c0 if self.c0 else 0, 
                   P - self.c1 if self.c1 else 0)
    
    def __add__(self, other: Fp2) -> Fp2:
        return Fp2((self.c0 + other.c0) % P, 
                   (self.c1 + other.c1) % P)
    
    def __sub__(self, other: Fp2) -> Fp2:
        return Fp2((self.c0 - other.c0) % P, 
                   (self.c1 - other.c1) % P)
    
    def __mul__(self, other: Fp2) -> Fp2:
        # (a + bu)(c + du) = (ac - bd) + (ad + bc)u
        ac = (self.c0 * other.c0) % P
        bd = (self.c1 * other.c1) % P
        ad = (self.c0 * other.c1) % P
        bc = (self.c1 * other.c0) % P
        return Fp2((ac - bd) % P, (ad + bc) % P)
    
    def square(self) -> Fp2:
        return self * self
    
    def invert(self) -> Fp2:
        # 1/(a + bu) = (a - bu)/(a^2 + b^2)
        denom = (self.c0 * self.c0 + self.c1 * self.c1) % P
        denom_inv = pow(denom, -1, P)
        return Fp2((self.c0 * denom_inv) % P, 
                   (P - self.c1 * denom_inv) % P)
