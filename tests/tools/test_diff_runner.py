"""Tests for neo-diff RPC runner behavior."""

import base64
import gzip
import io
import json
import urllib.error
from pathlib import Path

from neo.tools.diff.models import TestVector
from neo.tools.diff.runner import CSharpExecutor, PythonExecutor, VectorLoader
import neo.tools.diff.runner as diff_runner


class _DummyResponse:
    def __init__(self, payload: dict, *, headers: dict[str, str] | None = None, gzipped: bool = False):
        raw = json.dumps(payload).encode("utf-8")
        self._raw = gzip.compress(raw) if gzipped else raw
        self.headers = headers or {}

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


def test_rpc_call_decodes_gzip_json_responses(monkeypatch):
    """Some RPC providers (e.g. neo-rs) always gzip JSON bodies."""

    def fake_urlopen(request, timeout=30):
        return _DummyResponse(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {"network": 860833102},
            },
            headers={"Content-Encoding": "gzip"},
            gzipped=True,
        )

    monkeypatch.setattr(diff_runner.urllib.request, "urlopen", fake_urlopen)

    response = CSharpExecutor("http://127.0.0.1:30332")._rpc_call("getversion", [])
    assert response["result"]["network"] == 860833102


def test_invokescript_retries_with_hex_on_invalid_character_error(monkeypatch):
    """Some nodes reject base64 script params and require plain hex script input."""
    sent_scripts: list[str] = []

    def fake_invoke_with_param(self, script_param: str):
        sent_scripts.append(script_param)
        if len(sent_scripts) == 1:
            return {
                "jsonrpc": "2.0",
                "id": 1,
                "error": {
                    "code": -32602,
                    "message": "Invalid params - Invalid character 'G' at position 1",
                    "data": "Invalid character 'G' at position 1",
                },
            }

        return {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "state": "HALT",
                "gasconsumed": "0",
                "stack": [],
                "notifications": [],
            },
        }

    monkeypatch.setattr(CSharpExecutor, "_invoke_script_with_param", fake_invoke_with_param)

    script = bytes.fromhex("13159e")
    response = CSharpExecutor("http://127.0.0.1:30332")._invoke_script(script)
    assert response["result"]["state"] == "HALT"
    assert sent_scripts == [base64.b64encode(script).decode("ascii"), "13159e"]


def test_invokefunction_retries_bytearray_args_with_hex(monkeypatch):
    """Some RPC providers require ByteArray args in hex instead of base64."""
    invoke_calls: list[list[dict]] = []

    def fake_rpc_call(self, method: str, params: list):
        if method == "getnativecontracts":
            return {
                "jsonrpc": "2.0",
                "id": 1,
                "result": [
                    {
                        "manifest": {"name": "CryptoLib"},
                        "hash": "0x726cb6e0cd8628a1350a611384688911ab75f51b",
                    }
                ],
            }

        if method == "invokefunction":
            encoded_args = params[2]
            invoke_calls.append(encoded_args)
            value = encoded_args[0]["value"]

            if value == "AQI=":
                return {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "error": {
                        "code": -32602,
                        "message": "Invalid params - Invalid character 'Q' at position 1",
                        "data": "Invalid character 'Q' at position 1",
                    },
                }

            return {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "state": "HALT",
                    "gasconsumed": "0",
                    "stack": [{"type": "ByteString", "value": "AQI="}],
                    "notifications": [],
                },
            }

        raise AssertionError(f"Unexpected RPC method: {method}")

    monkeypatch.setattr(CSharpExecutor, "_rpc_call", fake_rpc_call)

    response = CSharpExecutor("http://127.0.0.1:30332")._invoke_cryptolib("sha256", [b"\x01\x02"])

    assert response["result"]["state"] == "HALT"
    assert len(invoke_calls) == 2
    assert invoke_calls[0][0]["type"] == "ByteArray"
    assert invoke_calls[0][0]["value"] == "AQI="
    assert invoke_calls[1][0]["type"] == "ByteArray"
    assert invoke_calls[1][0]["value"] == "0102"


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

def test_python_executor_stdlib_atoi_hex_matches_neo_signed_semantics():
    """StdLib.atoi(base=16) should use signed interpretation consistent with Neo nodes."""
    executor = PythonExecutor()

    neg_vector = TestVector(
        name="StdLib_atoi_hex_signed",
        script=b"",
        metadata={"category": "native", "contract": "StdLib", "method": "atoi", "args": ["ff", 16]},
    )
    pos_vector = TestVector(
        name="StdLib_atoi_hex_positive",
        script=b"",
        metadata={"category": "native", "contract": "StdLib", "method": "atoi", "args": ["0100", 16]},
    )

    neg_result = executor.execute(neg_vector)
    pos_result = executor.execute(pos_vector)

    assert neg_result.state == "HALT"
    assert neg_result.stack[0].value == -1
    assert pos_result.state == "HALT"
    assert pos_result.stack[0].value == 256


def test_vector_loader_ignores_non_vector_metadata_files(tmp_path: Path, capsys):
    """Coverage manifest files should be ignored instead of producing load warnings."""
    metadata_path = tmp_path / "checklist_coverage.json"
    metadata_path.write_text(
        json.dumps(
            {
                "example/check": {
                    "vectors": ["ADD_basic"],
                    "evidence": ["manual"],
                }
            }
        ),
        encoding="utf-8",
    )

    vm_vector_path = tmp_path / "simple.json"
    vm_vector_path.write_text(
        json.dumps([
            {
                "name": "VM_simple",
                "script": "00",
                "description": "simple vector",
            }
        ]),
        encoding="utf-8",
    )

    vectors = list(VectorLoader.load_directory(tmp_path))

    assert [vector.name for vector in vectors] == ["VM_simple"]
    assert "Warning: Failed to load" not in capsys.readouterr().out
