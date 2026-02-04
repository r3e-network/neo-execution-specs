#!/usr/bin/env python3
"""Test Vector Generator for Neo Execution Specs.

This module provides utilities to generate and validate test vectors
for the Neo VM, native contracts, cryptographic operations, and state transitions.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Any, Optional, List, Dict
from pathlib import Path
from enum import Enum


class VectorCategory(Enum):
    """Test vector categories."""
    VM = "vm"
    NATIVE = "native"
    CRYPTO = "crypto"
    STATE = "state"


@dataclass
class VMVector:
    """VM instruction test vector."""
    name: str
    description: str
    pre: Dict[str, Any]
    script: str
    post: Dict[str, Any]
    error: Optional[str] = None
    gas: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = {
            "name": self.name,
            "description": self.description,
            "pre": self.pre,
            "script": self.script,
            "post": self.post,
        }
        if self.error is not None:
            result["error"] = self.error
        if self.gas is not None:
            result["gas"] = self.gas
        return result


@dataclass
class CryptoVector:
    """Cryptographic operation test vector."""
    name: str
    description: str
    operation: str
    input: Dict[str, Any]
    output: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NativeVector:
    """Native contract test vector."""
    name: str
    description: str
    contract: str
    method: str
    args: List[Any]
    pre_state: Dict[str, Any]
    post_state: Dict[str, Any]
    result: Any
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StateVector:
    """State transition test vector."""
    name: str
    description: str
    transaction: Dict[str, Any]
    pre_state: Dict[str, Any]
    post_state: Dict[str, Any]
    gas_consumed: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class VectorCollection:
    """Collection of test vectors."""
    
    def __init__(self, name: str, description: str, category: VectorCategory):
        self.name = name
        self.description = description
        self.category = category
        self.vectors: List[Any] = []
        self.version = "1.0.0"
    
    def add(self, vector):
        """Add a vector to the collection."""
        self.vectors.append(vector)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "version": self.version,
            "vectors": [v.to_dict() for v in self.vectors]
        }
    
    def save(self, base_path: Path):
        """Save collection to JSON file."""
        output_dir = base_path / self.category.value
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{self.name}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        
        print(f"Saved {len(self.vectors)} vectors to {filepath}")
        return filepath


def script_to_hex(script: bytes) -> str:
    """Convert script bytes to hex string."""
    return "0x" + script.hex()


def hex_to_script(hex_str: str) -> bytes:
    """Convert hex string to script bytes."""
    if hex_str.startswith("0x"):
        hex_str = hex_str[2:]
    return bytes.fromhex(hex_str)
