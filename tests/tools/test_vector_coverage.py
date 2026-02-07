"""Coverage guards for execution-spec vector corpus."""

from __future__ import annotations

from pathlib import Path

from neo.vm.opcode import OpCode
from neo.tools.diff.runner import VectorLoader


def _category(vector) -> str:
    metadata = vector.metadata if isinstance(vector.metadata, dict) else {}
    return str(metadata.get("category", "vm")).lower()


def test_vector_corpus_minimum_counts() -> None:
    vectors = list(VectorLoader.load_directory(Path("tests/vectors")))

    assert len(vectors) >= 230

    vm_vectors = [v for v in vectors if _category(v) == "vm"]
    native_vectors = [v for v in vectors if _category(v) == "native"]
    crypto_vectors = [v for v in vectors if _category(v) == "crypto"]

    assert len(vm_vectors) >= 180
    assert len(native_vectors) >= 25
    assert len(crypto_vectors) >= 25


def test_advanced_vm_opcode_coverage_floor() -> None:
    vm_vectors = [
        vector
        for vector in VectorLoader.load_directory(Path("tests/vectors/vm"))
        if _category(vector) == "vm"
    ]

    observed_opcodes: set[int] = set()
    for vector in vm_vectors:
        observed_opcodes.update(vector.script)

    required = {
        int(OpCode.PUSHDATA2),
        int(OpCode.PUSHDATA4),
        int(OpCode.PACKMAP),
        int(OpCode.SETITEM),
        int(OpCode.REMOVE),
        int(OpCode.CLEARITEMS),
        int(OpCode.POPITEM),
        int(OpCode.KEYS),
        int(OpCode.VALUES),
    }

    assert required.issubset(observed_opcodes)
