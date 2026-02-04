#!/usr/bin/env python3
"""BLS12-381 Cryptographic Test Vector Generator."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from generator import CryptoVector, VectorCollection, VectorCategory


def generate_bls_vectors() -> VectorCollection:
    """Generate BLS12-381 test vectors."""
    collection = VectorCollection(
        name="bls12_381",
        description="BLS12-381 cryptographic operation test vectors",
        category=VectorCategory.CRYPTO
    )
    
    # G1 identity point (compressed)
    # Identity has the infinity flag set (0xc0 prefix)
    g1_identity = "0x" + "c0" + "00" * 47
    
    collection.add(CryptoVector(
        name="G1_identity",
        description="G1 identity point (compressed)",
        operation="G1_identity",
        input={},
        output={"point": g1_identity, "is_identity": True}
    ))
    
    # G1 generator point (compressed, from BLS12-381 spec)
    g1_generator = "0x17f1d3a73197d7942695638c4fa9ac0fc3688c4f9774b905a14e3a3f171bac586c55e83ff97a1aeffb3af00adb22c6bb"
    
    collection.add(CryptoVector(
        name="G1_generator",
        description="G1 generator point (compressed)",
        operation="G1_generator",
        input={},
        output={"point": g1_generator, "is_identity": False}
    ))
    
    # G2 identity point (compressed)
    g2_identity = "0x" + "c0" + "00" * 95
    
    collection.add(CryptoVector(
        name="G2_identity",
        description="G2 identity point (compressed)",
        operation="G2_identity",
        input={},
        output={"point": g2_identity, "is_identity": True}
    ))
    
    # Scalar operations
    collection.add(CryptoVector(
        name="Scalar_modular",
        description="Scalar modular reduction",
        operation="Scalar_mod",
        input={"value": "0x73eda753299d7d483339d80809a1d80553bda402fffe5bfeffffffff00000002"},
        output={"reduced": 1}
    ))
    
    # Pairing with identity
    collection.add(CryptoVector(
        name="Pairing_identity_g1",
        description="Pairing with G1 identity yields Gt identity",
        operation="pairing",
        input={"g1": g1_identity, "g2": g2_identity},
        output={"is_identity": True}
    ))
    
    return collection
