"""Tests for neo-diff RPC runner behavior."""

import base64
import io
import json
import urllib.error

from neo.tools.diff.models import TestVector
from neo.tools.diff.runner import CSharpExecutor, PythonExecutor
import neo.tools.diff.runner as diff_runner


class _DummyResponse:
    def __init__(self, payload: dict):
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_invokescript_retries_with_base64_when_neo_v391_requires_it(monkeypatch):
    """C# Neo v3.9.1 endpoints reject hex and require base64 invokescript payload."""
    sent_scripts: list[str] = []

    def fake_urlopen(request, timeout=30):
        payload = json.loads(request.data.decode("utf-8"))
        sent_scripts.append(payload["params"][0])

        if len(sent_scripts) == 1:
            body = {
                "jsonrpc": "2.0",
                "id": 1,
                "error": {
                    "code": -32602,
                    "message": 'Invalid params - Invalid Base64-encoded bytes: "13159e"',
                    "data": 'Invalid Base64-encoded bytes: "13159e"',
                },
            }
            raise urllib.error.HTTPError(
                url=request.full_url,
                code=403,
                msg="Forbidden",
                hdrs=None,
                fp=io.BytesIO(json.dumps(body).encode("utf-8")),
            )

        return _DummyResponse(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "state": "HALT",
                    "gasconsumed": "0",
                    "stack": [],
                    "notifications": [],
                },
            }
        )

    monkeypatch.setattr(diff_runner.urllib.request, "urlopen", fake_urlopen)

    vector = TestVector(name="ADD_basic", script=bytes.fromhex("13159e"))
    result = CSharpExecutor("http://seed1.neo.org:10332").execute(vector)

    assert result.state == "HALT"
    assert len(sent_scripts) == 2
    assert sent_scripts[0] == base64.b64encode(vector.script).decode("ascii")
    assert sent_scripts[1] == "13159e"


def test_parse_stack_item_normalizes_rpc_types_and_buffer_base64():
    """RPC Any/Buffer representation should normalize to comparator-friendly form."""
    executor = CSharpExecutor("http://seed1.neo.org:10332")

    parsed_any = executor._parse_stack_item({"type": "Any", "value": None})
    assert parsed_any.type == "ANY"

    parsed_buffer = executor._parse_stack_item({"type": "Buffer", "value": "AAAAAA=="})
    assert parsed_buffer.type == "Buffer"
    assert parsed_buffer.value == "00000000"


def test_python_executor_tracks_opcode_gas_for_vm_vectors():
    """Python executor should report Neo v3.9.1 opcode gas for VM scripts."""
    executor = PythonExecutor()

    # PUSH3, PUSH5, ADD, RET => 1 + 1 + 8 + 0 = 10
    vector = TestVector(name="ADD_basic", script=bytes.fromhex("13159e40"))
    result = executor.execute(vector)

    assert result.state == "HALT"
    assert result.gas_consumed == 10

from pathlib import Path

from neo.tools.diff.runner import VectorLoader


def test_vector_loader_supports_non_vm_collection_formats():
    """Loader should parse native/crypto collections that don't have top-level script fields."""
    native_vectors = VectorLoader.load_file(Path("tests/vectors/native/neo_token.json"))
    assert len(native_vectors) == 3
    assert native_vectors[0].metadata["category"] == "native"
    assert native_vectors[0].metadata["contract"] == "NeoToken"
    assert native_vectors[0].script == b""

    crypto_vectors = VectorLoader.load_file(Path("tests/vectors/crypto/hash.json"))
    assert len(crypto_vectors) == 5
    assert crypto_vectors[0].metadata["category"] == "crypto"
    assert crypto_vectors[0].metadata["operation"] == "SHA256"


def test_python_executor_executes_native_vector_without_vm_script():
    """Native vectors should be executable without requiring a VM script payload."""
    executor = PythonExecutor()
    vector = TestVector(
        name="StdLib_itoa_decimal",
        script=b"",
        metadata={
            "category": "native",
            "contract": "StdLib",
            "method": "itoa",
            "args": [123, 10],
        },
    )

    result = executor.execute(vector)

    assert result.state == "HALT"
    assert len(result.stack) == 1
    assert result.stack[0].type == "String"
    assert result.stack[0].value == "123"


def test_python_executor_executes_crypto_vector_without_vm_script():
    """Crypto vectors should run through hash operation handlers without VM script bytes."""
    executor = PythonExecutor()
    vector = TestVector(
        name="Hash160_hello",
        script=b"",
        metadata={
            "category": "crypto",
            "operation": "Hash160",
            "input": {"data": "0x68656c6c6f"},
        },
    )

    result = executor.execute(vector)

    assert result.state == "HALT"
    assert len(result.stack) == 1
    assert result.stack[0].type == "String"
    assert result.stack[0].value == "b6a9c8c230722b7c748331a8b450f05566dc7d0f"


def test_vector_loader_skips_unsupported_crypto_operations():
    """BLS vectors are intentionally skipped until dedicated execution support exists."""
    vectors = VectorLoader.load_file(Path("tests/vectors/crypto/bls12_381.json"))
    assert vectors == []


def test_python_executor_policy_vectors_follow_mainnet_v391_values():
    """Policy read methods should reflect current Neo v3.9.1 mainnet values."""
    executor = PythonExecutor()

    fee_vector = TestVector(
        name="Policy_getFeePerByte",
        script=b"",
        metadata={"category": "native", "contract": "PolicyContract", "method": "getFeePerByte", "args": []},
    )
    exec_vector = TestVector(
        name="Policy_getExecFeeFactor",
        script=b"",
        metadata={"category": "native", "contract": "PolicyContract", "method": "getExecFeeFactor", "args": []},
    )
    storage_vector = TestVector(
        name="Policy_getStoragePrice",
        script=b"",
        metadata={"category": "native", "contract": "PolicyContract", "method": "getStoragePrice", "args": []},
    )

    fee_result = executor.execute(fee_vector)
    exec_result = executor.execute(exec_vector)
    storage_result = executor.execute(storage_vector)

    assert fee_result.state == "HALT"
    assert fee_result.stack[0].value == 20

    assert exec_result.state == "HALT"
    assert exec_result.stack[0].value == 1

    assert storage_result.state == "HALT"
    assert storage_result.stack[0].value == 1000
