#!/usr/bin/env python3
"""Cryptographic Operation Test Vector Generator."""

import sys
import hashlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from generator import CryptoVector, VectorCollection, VectorCategory


def generate_hash_vectors() -> VectorCollection:
    """Generate hash function test vectors."""
    collection = VectorCollection(
        name="hash",
        description="Hash function test vectors (SHA256, RIPEMD160, etc.)",
        category=VectorCategory.CRYPTO
    )
    
    # SHA256 tests
    test_data = b"hello"
    sha256_hash = hashlib.sha256(test_data).hexdigest()
    
    collection.add(CryptoVector(
        name="SHA256_hello",
        description="SHA256 of 'hello'",
        operation="SHA256",
        input={"data": "0x" + test_data.hex()},
        output={"hash": "0x" + sha256_hash}
    ))
    
    collection.add(CryptoVector(
        name="SHA256_empty",
        description="SHA256 of empty data",
        operation="SHA256",
        input={"data": "0x"},
        output={"hash": "0x" + hashlib.sha256(b"").hexdigest()}
    ))
    
    # Double SHA256 (Hash256)
    double_sha = hashlib.sha256(hashlib.sha256(test_data).digest()).hexdigest()
    collection.add(CryptoVector(
        name="Hash256_hello",
        description="Double SHA256 of 'hello'",
        operation="Hash256",
        input={"data": "0x" + test_data.hex()},
        output={"hash": "0x" + double_sha}
    ))
    
    # RIPEMD160
    ripemd = hashlib.new('ripemd160', test_data).hexdigest()
    collection.add(CryptoVector(
        name="RIPEMD160_hello",
        description="RIPEMD160 of 'hello'",
        operation="RIPEMD160",
        input={"data": "0x" + test_data.hex()},
        output={"hash": "0x" + ripemd}
    ))
    
    # Hash160 (SHA256 + RIPEMD160)
    sha_first = hashlib.sha256(test_data).digest()
    hash160 = hashlib.new('ripemd160', sha_first).hexdigest()
    collection.add(CryptoVector(
        name="Hash160_hello",
        description="Hash160 (SHA256+RIPEMD160) of 'hello'",
        operation="Hash160",
        input={"data": "0x" + test_data.hex()},
        output={"hash": "0x" + hash160}
    ))
    
    return collection
