"""Validation tests for declared expected values in non-VM vectors."""

from __future__ import annotations

import json
from pathlib import Path

from neo.tools.diff.runner import (
    PythonExecutor,
    VectorLoader,
    _normalize_non_vm_result,
)

VECTORS_ROOT = Path("tests/vectors")
SUPPORTED_CRYPTO_FILES = {
    "hash.json",
    "hash_extended.json",
    "hash_deep.json",
    "hash_matrix.json",
}


def _iter_non_vm_vector_files() -> list[Path]:
    files: list[Path] = []
    files.extend(sorted((VECTORS_ROOT / "native").glob("*.json")))
    files.extend(
        sorted(
            path
            for path in (VECTORS_ROOT / "crypto").glob("*.json")
            if path.name in SUPPORTED_CRYPTO_FILES
        )
    )
    return files


def _raw_expected_value(entry: dict, category: str):
    if category == "native":
        return entry.get("result")
    return (entry.get("output") or {}).get("hash")


def test_non_vm_vectors_have_consistent_declared_expected_values() -> None:
    executor = PythonExecutor()

    for file_path in _iter_non_vm_vector_files():
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        category = str(payload.get("category", "")).lower()
        assert category in {"native", "crypto"}

        raw_vectors = payload.get("vectors") or []
        loaded_vectors = VectorLoader.load_file(file_path)

        loaded_by_name = {vector.name: vector for vector in loaded_vectors}
        assert len(loaded_by_name) == len(raw_vectors)

        for entry in raw_vectors:
            name = entry["name"]
            assert name in loaded_by_name
            vector = loaded_by_name[name]

            result = executor.execute(vector)
            assert result.state == "HALT"
            assert len(result.stack) == 1

            expected_raw = _raw_expected_value(entry, category)
            expected_normalized = _normalize_non_vm_result(expected_raw, vector)
            actual = result.stack[0].value

            assert actual == expected_normalized, (
                f"{file_path.name}:{name} expected {expected_normalized!r} but got {actual!r}"
            )
