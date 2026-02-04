#!/usr/bin/env python3
"""Native Contract Test Vector Generator."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from generator import NativeVector, VectorCollection, VectorCategory


def generate_neo_token_vectors() -> VectorCollection:
    """Generate NeoToken test vectors."""
    collection = VectorCollection(
        name="neo_token",
        description="NeoToken native contract test vectors",
        category=VectorCategory.NATIVE
    )
    
    collection.add(NativeVector(
        name="NEO_totalSupply",
        description="Get NEO total supply",
        contract="NeoToken",
        method="totalSupply",
        args=[],
        pre_state={},
        post_state={},
        result=100_000_000
    ))
    
    collection.add(NativeVector(
        name="NEO_symbol",
        description="Get NEO symbol",
        contract="NeoToken",
        method="symbol",
        args=[],
        pre_state={},
        post_state={},
        result="NEO"
    ))
    
    collection.add(NativeVector(
        name="NEO_decimals",
        description="Get NEO decimals",
        contract="NeoToken",
        method="decimals",
        args=[],
        pre_state={},
        post_state={},
        result=0
    ))
    
    return collection


def generate_gas_token_vectors() -> VectorCollection:
    """Generate GasToken test vectors."""
    collection = VectorCollection(
        name="gas_token",
        description="GasToken native contract test vectors",
        category=VectorCategory.NATIVE
    )
    
    collection.add(NativeVector(
        name="GAS_symbol",
        description="Get GAS symbol",
        contract="GasToken",
        method="symbol",
        args=[],
        pre_state={},
        post_state={},
        result="GAS"
    ))
    
    collection.add(NativeVector(
        name="GAS_decimals",
        description="Get GAS decimals",
        contract="GasToken",
        method="decimals",
        args=[],
        pre_state={},
        post_state={},
        result=8
    ))
    
    return collection
