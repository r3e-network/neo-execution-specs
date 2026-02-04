#!/usr/bin/env python3
"""State Transition Test Vector Generator."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from generator import StateVector, VectorCollection, VectorCategory


def generate_state_vectors() -> VectorCollection:
    """Generate state transition test vectors."""
    collection = VectorCollection(
        name="state_transitions",
        description="State transition test vectors",
        category=VectorCategory.STATE
    )
    
    # Simple transfer state change
    collection.add(StateVector(
        name="simple_transfer",
        description="Simple NEO transfer between accounts",
        transaction={
            "type": "InvocationTransaction",
            "script": "0x...",
            "sender": "NXV7ZhHiyM1aHXwpVsRZC6BwNFP2jghXAq",
            "signers": ["NXV7ZhHiyM1aHXwpVsRZC6BwNFP2jghXAq"]
        },
        pre_state={
            "balances": {
                "NXV7ZhHiyM1aHXwpVsRZC6BwNFP2jghXAq": 100,
                "NZNos2WqTbu5oCgyfss9kUJgBXJqhuYAaj": 0
            }
        },
        post_state={
            "balances": {
                "NXV7ZhHiyM1aHXwpVsRZC6BwNFP2jghXAq": 90,
                "NZNos2WqTbu5oCgyfss9kUJgBXJqhuYAaj": 10
            }
        },
        gas_consumed=997860
    ))
    
    return collection
