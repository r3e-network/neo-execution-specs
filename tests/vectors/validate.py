#!/usr/bin/env python3
"""Test Vector Validator - Validates vectors against actual VM execution."""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.types import (
    StackItem, Integer, Boolean, ByteString,
    Array, Struct, Map, Null, Buffer
)


def hex_to_script(hex_str: str) -> bytes:
    """Convert hex string to script bytes."""
    if hex_str.startswith("0x"):
        hex_str = hex_str[2:]
    return bytes.fromhex(hex_str)


def stack_item_to_python(item: StackItem) -> dict | int | bool | str | list | None:
    """Convert a StackItem to a Python representation for comparison."""
    if isinstance(item, Null):
        return {"type": "Null", "value": None}
    elif isinstance(item, Boolean):
        return {"type": "Boolean", "value": item.get_boolean()}
    elif isinstance(item, Integer):
        return {"type": "Integer", "value": int(item.get_integer())}
    elif isinstance(item, ByteString):
        return {"type": "ByteString", "value": item.get_bytes_unsafe().hex()}
    elif isinstance(item, Buffer):
        return {"type": "Buffer", "value": item.get_bytes_unsafe().hex()}
    elif isinstance(item, Struct):
        return {
            "type": "Struct", 
            "value": [stack_item_to_python(x) for x in item]
        }
    elif isinstance(item, Array):
        return {
            "type": "Array",
            "value": [stack_item_to_python(x) for x in item]
        }
    elif isinstance(item, Map):
        # Map keys can be primitives, values can be anything
        result = {}
        for k, v in item.items():
            key_repr = stack_item_to_python(k)
            if isinstance(key_repr, dict) and "value" in key_repr:
                key_str = str(key_repr["value"])
            else:
                key_str = str(key_repr)
            result[key_str] = stack_item_to_python(v)
        return {"type": "Map", "value": result}
    else:
        return {"type": item.type.name, "value": repr(item)}


def normalize_expected(expected: dict | int | list) -> dict:
    """Normalize expected value to comparable format."""
    if isinstance(expected, int):
        return {"type": "Integer", "value": expected}
    elif isinstance(expected, bool):
        return {"type": "Boolean", "value": expected}
    elif isinstance(expected, dict):
        if "type" in expected:
            typ = expected["type"]
            val = expected.get("value")
            if typ == "Array" and isinstance(val, list):
                return {"type": "Array", "value": [normalize_expected(x) for x in val]}
            elif typ == "Struct" and isinstance(val, list):
                return {"type": "Struct", "value": [normalize_expected(x) for x in val]}
            elif typ == "Map" and isinstance(val, dict):
                return {"type": "Map", "value": {
                    str(k): normalize_expected(v) for k, v in val.items()
                }}
            return expected
        return expected
    elif isinstance(expected, list):
        return {"type": "Array", "value": [normalize_expected(x) for x in expected]}
    return expected


def compare_stack_items(actual: dict, expected: dict) -> bool:
    """Compare actual and expected stack items."""
    if actual.get("type") != expected.get("type"):
        return False
    
    actual_val = actual.get("value")
    expected_val = expected.get("value")
    
    if actual.get("type") in ("Array", "Struct"):
        if not isinstance(actual_val, list) or not isinstance(expected_val, list):
            return False
        if len(actual_val) != len(expected_val):
            return False
        return all(compare_stack_items(a, e) for a, e in zip(actual_val, expected_val))
    elif actual.get("type") == "Map":
        if not isinstance(actual_val, dict) or not isinstance(expected_val, dict):
            return False
        if set(actual_val.keys()) != set(expected_val.keys()):
            return False
        return all(compare_stack_items(actual_val[k], expected_val[k]) for k in actual_val)
    else:
        return actual_val == expected_val


def validate_vm_vector(vector: dict) -> tuple[bool, str]:
    """Validate a single VM vector against actual execution."""
    try:
        engine = ExecutionEngine()
        
        # Load and execute script
        script = hex_to_script(vector["script"])
        engine.load_script(script)
        engine.execute()
        
        # Check for expected error
        if vector.get("error"):
            if engine.state == VMState.FAULT:
                return True, "Expected fault occurred"
            return False, f"Expected error but got state: {engine.state}"
        
        # Check post-state
        if engine.state != VMState.HALT:
            return False, f"Expected HALT but got: {engine.state}"
        
        expected_stack = vector["post"].get("stack", [])
        actual_stack = []
        
        # Get results from result_stack
        while len(engine.result_stack) > 0:
            item = engine.result_stack.pop()
            actual_stack.insert(0, stack_item_to_python(item))
        
        # Normalize expected values
        expected_normalized = [normalize_expected(x) for x in expected_stack]
        
        # Compare stacks
        if len(actual_stack) != len(expected_normalized):
            return False, f"Stack size mismatch: {len(actual_stack)} vs {len(expected_normalized)}"
        
        for i, (actual, expected) in enumerate(zip(actual_stack, expected_normalized)):
            if not compare_stack_items(actual, expected):
                return False, f"Stack[{i}] mismatch: {actual} vs {expected}"
        
        return True, "OK"
        
    except Exception as e:
        if vector.get("error"):
            return True, f"Expected error: {type(e).__name__}"
        return False, f"Exception: {type(e).__name__}: {e}"


def validate_file(filepath: Path) -> tuple[int, int]:
    """Validate all vectors in a file."""
    with open(filepath) as f:
        data = json.load(f)
    
    passed = 0
    failed = 0
    
    print(f"\n{data['name']} ({len(data['vectors'])} vectors)")
    print("-" * 40)
    
    for vector in data["vectors"]:
        if data["category"] == "vm":
            success, msg = validate_vm_vector(vector)
        else:
            success, msg = True, "Skipped (non-VM)"
        
        status = "✓" if success else "✗"
        print(f"  {status} {vector['name']}: {msg}")
        
        if success:
            passed += 1
        else:
            failed += 1
    
    return passed, failed


def main():
    vectors_dir = Path(__file__).parent
    
    total_passed = 0
    total_failed = 0
    
    # Validate VM vectors
    vm_dir = vectors_dir / "vm"
    if vm_dir.exists():
        for json_file in sorted(vm_dir.glob("*.json")):
            passed, failed = validate_file(json_file)
            total_passed += passed
            total_failed += failed
    
    print("\n" + "=" * 40)
    print(f"Results: {total_passed} passed, {total_failed} failed")
    
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
