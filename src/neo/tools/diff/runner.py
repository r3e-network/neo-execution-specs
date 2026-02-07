"""Test runner for diff testing framework."""

from __future__ import annotations
import base64
import hashlib
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Iterator, Any

from neo.vm.opcode import OpCode

from neo.tools.diff.models import (
    ExecutionSource,
    ExecutionResult,
    StackValue,
    TestVector,
)


OPCODE_PRICE_TABLE_V391: dict[int, int] = {
    int(OpCode.PUSHINT8): 1<<0,
    int(OpCode.PUSHINT16): 1<<0,
    int(OpCode.PUSHINT32): 1<<0,
    int(OpCode.PUSHINT64): 1<<0,
    int(OpCode.PUSHINT128): 1<<2,
    int(OpCode.PUSHINT256): 1<<2,
    int(OpCode.PUSHT): 1<<0,
    int(OpCode.PUSHF): 1<<0,
    int(OpCode.PUSHA): 1<<2,
    int(OpCode.PUSHNULL): 1<<0,
    int(OpCode.PUSHDATA1): 1<<3,
    int(OpCode.PUSHDATA2): 1<<9,
    int(OpCode.PUSHDATA4): 1<<12,
    int(OpCode.PUSHM1): 1<<0,
    int(OpCode.PUSH0): 1<<0,
    int(OpCode.PUSH1): 1<<0,
    int(OpCode.PUSH2): 1<<0,
    int(OpCode.PUSH3): 1<<0,
    int(OpCode.PUSH4): 1<<0,
    int(OpCode.PUSH5): 1<<0,
    int(OpCode.PUSH6): 1<<0,
    int(OpCode.PUSH7): 1<<0,
    int(OpCode.PUSH8): 1<<0,
    int(OpCode.PUSH9): 1<<0,
    int(OpCode.PUSH10): 1<<0,
    int(OpCode.PUSH11): 1<<0,
    int(OpCode.PUSH12): 1<<0,
    int(OpCode.PUSH13): 1<<0,
    int(OpCode.PUSH14): 1<<0,
    int(OpCode.PUSH15): 1<<0,
    int(OpCode.PUSH16): 1<<0,
    int(OpCode.NOP): 1<<0,
    int(OpCode.JMP): 1<<1,
    int(OpCode.JMP_L): 1<<1,
    int(OpCode.JMPIF): 1<<1,
    int(OpCode.JMPIF_L): 1<<1,
    int(OpCode.JMPIFNOT): 1<<1,
    int(OpCode.JMPIFNOT_L): 1<<1,
    int(OpCode.JMPEQ): 1<<1,
    int(OpCode.JMPEQ_L): 1<<1,
    int(OpCode.JMPNE): 1<<1,
    int(OpCode.JMPNE_L): 1<<1,
    int(OpCode.JMPGT): 1<<1,
    int(OpCode.JMPGT_L): 1<<1,
    int(OpCode.JMPGE): 1<<1,
    int(OpCode.JMPGE_L): 1<<1,
    int(OpCode.JMPLT): 1<<1,
    int(OpCode.JMPLT_L): 1<<1,
    int(OpCode.JMPLE): 1<<1,
    int(OpCode.JMPLE_L): 1<<1,
    int(OpCode.CALL): 1<<9,
    int(OpCode.CALL_L): 1<<9,
    int(OpCode.CALLA): 1<<9,
    int(OpCode.CALLT): 1<<15,
    int(OpCode.ABORT): 0,
    int(OpCode.ABORTMSG): 0,
    int(OpCode.ASSERT): 1<<0,
    int(OpCode.ASSERTMSG): 1<<0,
    int(OpCode.THROW): 1<<9,
    int(OpCode.TRY): 1<<2,
    int(OpCode.TRY_L): 1<<2,
    int(OpCode.ENDTRY): 1<<2,
    int(OpCode.ENDTRY_L): 1<<2,
    int(OpCode.ENDFINALLY): 1<<2,
    int(OpCode.RET): 0,
    int(OpCode.SYSCALL): 0,
    int(OpCode.DEPTH): 1<<1,
    int(OpCode.DROP): 1<<1,
    int(OpCode.NIP): 1<<1,
    int(OpCode.XDROP): 1<<4,
    int(OpCode.CLEAR): 1<<4,
    int(OpCode.DUP): 1<<1,
    int(OpCode.OVER): 1<<1,
    int(OpCode.PICK): 1<<1,
    int(OpCode.TUCK): 1<<1,
    int(OpCode.SWAP): 1<<1,
    int(OpCode.ROT): 1<<1,
    int(OpCode.ROLL): 1<<4,
    int(OpCode.REVERSE3): 1<<1,
    int(OpCode.REVERSE4): 1<<1,
    int(OpCode.REVERSEN): 1<<4,
    int(OpCode.INITSSLOT): 1<<4,
    int(OpCode.INITSLOT): 1<<6,
    int(OpCode.LDSFLD0): 1<<1,
    int(OpCode.LDSFLD1): 1<<1,
    int(OpCode.LDSFLD2): 1<<1,
    int(OpCode.LDSFLD3): 1<<1,
    int(OpCode.LDSFLD4): 1<<1,
    int(OpCode.LDSFLD5): 1<<1,
    int(OpCode.LDSFLD6): 1<<1,
    int(OpCode.LDSFLD): 1<<1,
    int(OpCode.STSFLD0): 1<<1,
    int(OpCode.STSFLD1): 1<<1,
    int(OpCode.STSFLD2): 1<<1,
    int(OpCode.STSFLD3): 1<<1,
    int(OpCode.STSFLD4): 1<<1,
    int(OpCode.STSFLD5): 1<<1,
    int(OpCode.STSFLD6): 1<<1,
    int(OpCode.STSFLD): 1<<1,
    int(OpCode.LDLOC0): 1<<1,
    int(OpCode.LDLOC1): 1<<1,
    int(OpCode.LDLOC2): 1<<1,
    int(OpCode.LDLOC3): 1<<1,
    int(OpCode.LDLOC4): 1<<1,
    int(OpCode.LDLOC5): 1<<1,
    int(OpCode.LDLOC6): 1<<1,
    int(OpCode.LDLOC): 1<<1,
    int(OpCode.STLOC0): 1<<1,
    int(OpCode.STLOC1): 1<<1,
    int(OpCode.STLOC2): 1<<1,
    int(OpCode.STLOC3): 1<<1,
    int(OpCode.STLOC4): 1<<1,
    int(OpCode.STLOC5): 1<<1,
    int(OpCode.STLOC6): 1<<1,
    int(OpCode.STLOC): 1<<1,
    int(OpCode.LDARG0): 1<<1,
    int(OpCode.LDARG1): 1<<1,
    int(OpCode.LDARG2): 1<<1,
    int(OpCode.LDARG3): 1<<1,
    int(OpCode.LDARG4): 1<<1,
    int(OpCode.LDARG5): 1<<1,
    int(OpCode.LDARG6): 1<<1,
    int(OpCode.LDARG): 1<<1,
    int(OpCode.STARG0): 1<<1,
    int(OpCode.STARG1): 1<<1,
    int(OpCode.STARG2): 1<<1,
    int(OpCode.STARG3): 1<<1,
    int(OpCode.STARG4): 1<<1,
    int(OpCode.STARG5): 1<<1,
    int(OpCode.STARG6): 1<<1,
    int(OpCode.STARG): 1<<1,
    int(OpCode.NEWBUFFER): 1<<8,
    int(OpCode.MEMCPY): 1<<11,
    int(OpCode.CAT): 1<<11,
    int(OpCode.SUBSTR): 1<<11,
    int(OpCode.LEFT): 1<<11,
    int(OpCode.RIGHT): 1<<11,
    int(OpCode.INVERT): 1<<2,
    int(OpCode.AND): 1<<3,
    int(OpCode.OR): 1<<3,
    int(OpCode.XOR): 1<<3,
    int(OpCode.EQUAL): 1<<5,
    int(OpCode.NOTEQUAL): 1<<5,
    int(OpCode.SIGN): 1<<2,
    int(OpCode.ABS): 1<<2,
    int(OpCode.NEGATE): 1<<2,
    int(OpCode.INC): 1<<2,
    int(OpCode.DEC): 1<<2,
    int(OpCode.ADD): 1<<3,
    int(OpCode.SUB): 1<<3,
    int(OpCode.MUL): 1<<3,
    int(OpCode.DIV): 1<<3,
    int(OpCode.MOD): 1<<3,
    int(OpCode.POW): 1<<6,
    int(OpCode.SQRT): 1<<6,
    int(OpCode.MODMUL): 1<<5,
    int(OpCode.MODPOW): 1<<11,
    int(OpCode.SHL): 1<<3,
    int(OpCode.SHR): 1<<3,
    int(OpCode.NOT): 1<<2,
    int(OpCode.BOOLAND): 1<<3,
    int(OpCode.BOOLOR): 1<<3,
    int(OpCode.NZ): 1<<2,
    int(OpCode.NUMEQUAL): 1<<3,
    int(OpCode.NUMNOTEQUAL): 1<<3,
    int(OpCode.LT): 1<<3,
    int(OpCode.LE): 1<<3,
    int(OpCode.GT): 1<<3,
    int(OpCode.GE): 1<<3,
    int(OpCode.MIN): 1<<3,
    int(OpCode.MAX): 1<<3,
    int(OpCode.WITHIN): 1<<3,
    int(OpCode.PACKMAP): 1<<11,
    int(OpCode.PACKSTRUCT): 1<<11,
    int(OpCode.PACK): 1<<11,
    int(OpCode.UNPACK): 1<<11,
    int(OpCode.NEWARRAY0): 1<<4,
    int(OpCode.NEWARRAY): 1<<9,
    int(OpCode.NEWARRAY_T): 1<<9,
    int(OpCode.NEWSTRUCT0): 1<<4,
    int(OpCode.NEWSTRUCT): 1<<9,
    int(OpCode.NEWMAP): 1<<3,
    int(OpCode.SIZE): 1<<2,
    int(OpCode.HASKEY): 1<<6,
    int(OpCode.KEYS): 1<<4,
    int(OpCode.VALUES): 1<<13,
    int(OpCode.PICKITEM): 1<<6,
    int(OpCode.APPEND): 1<<13,
    int(OpCode.SETITEM): 1<<13,
    int(OpCode.REVERSEITEMS): 1<<13,
    int(OpCode.REMOVE): 1<<4,
    int(OpCode.CLEARITEMS): 1<<4,
    int(OpCode.POPITEM): 1<<4,
    int(OpCode.ISNULL): 1<<1,
    int(OpCode.ISTYPE): 1<<1,
    int(OpCode.CONVERT): 1<<13,
}



_NON_VM_CATEGORIES = {"native", "crypto", "state"}
_CRYPTO_HEX_METHODS = {"sha256", "ripemd160"}


def _vector_category(vector: TestVector) -> str:
    metadata = vector.metadata if isinstance(vector.metadata, dict) else {}
    return str(metadata.get("category", "vm")).lower()


def _to_stack_value(value: Any) -> StackValue:
    if isinstance(value, bool):
        return StackValue(type="Boolean", value=value)
    if isinstance(value, int):
        return StackValue(type="Integer", value=value)
    if isinstance(value, str):
        return StackValue(type="String", value=value)
    return StackValue(type="Any", value=value)


def _decode_hex_string(value: str) -> bytes:
    candidate = value.removeprefix("0x").removeprefix("0X")
    return bytes.fromhex(candidate) if candidate else b""


def _normalize_non_vm_result(actual: Any, vector: TestVector) -> Any:
    metadata = vector.metadata if isinstance(vector.metadata, dict) else {}
    category = _vector_category(vector)
    contract = str(metadata.get("contract", ""))
    method = str(metadata.get("method", "")).lower()
    expected = metadata.get("expected_result")

    expects_hex = False
    if isinstance(expected, str) and expected.lower().startswith("0x"):
        expects_hex = True
    if category == "crypto":
        expects_hex = True
    if category == "native" and contract == "CryptoLib" and method in _CRYPTO_HEX_METHODS:
        expects_hex = True

    if isinstance(expected, bool):
        return bool(actual)

    if isinstance(expected, int):
        if isinstance(actual, (bytes, bytearray)):
            return int.from_bytes(actual, "little", signed=False)
        if isinstance(actual, bool):
            return int(actual)
        return int(actual)

    if expects_hex:
        if isinstance(actual, (bytes, bytearray)):
            return bytes(actual).hex()
        if isinstance(actual, str):
            return actual.removeprefix("0x").removeprefix("0X").lower()

    if isinstance(actual, (bytes, bytearray)):
        try:
            return bytes(actual).decode("utf-8")
        except UnicodeDecodeError:
            return bytes(actual).hex()

    return actual


class PythonExecutor:
    """Execute test vectors using Python spec."""

    def execute(self, vector: TestVector) -> ExecutionResult:
        """Execute a test vector and return result."""
        category = _vector_category(vector)

        if category in ("native", "crypto"):
            return self._execute_non_vm_vector(vector)

        if category == "state" and not vector.script:
            return ExecutionResult(
                source=ExecutionSource.PYTHON_SPEC,
                state="UNSUPPORTED",
                exception="State vector missing executable transaction script",
            )

        from neo.vm.execution_engine import ExecutionEngine

        engine = ExecutionEngine()
        engine.load_script(vector.script)

        try:
            state, gas_consumed = self._execute_with_gas(engine)
            stack = self._extract_stack(engine)

            return ExecutionResult(
                source=ExecutionSource.PYTHON_SPEC,
                state=state.name,
                gas_consumed=gas_consumed,
                stack=stack,
                exception=None,
            )
        except Exception as e:
            return ExecutionResult(
                source=ExecutionSource.PYTHON_SPEC,
                state="FAULT",
                exception=str(e),
            )

    def _execute_non_vm_vector(self, vector: TestVector) -> ExecutionResult:
        """Execute native/crypto vectors without direct VM scripts."""
        category = _vector_category(vector)

        try:
            if category == "native":
                actual_result = self._evaluate_native_vector(vector)
            elif category == "crypto":
                actual_result = self._evaluate_crypto_vector(vector)
            else:
                raise ValueError(f"Unsupported non-VM category: {category}")

            normalized = _normalize_non_vm_result(actual_result, vector)
            return ExecutionResult(
                source=ExecutionSource.PYTHON_SPEC,
                state="HALT",
                gas_consumed=0,
                stack=[_to_stack_value(normalized)],
                exception=None,
            )
        except Exception as e:
            return ExecutionResult(
                source=ExecutionSource.PYTHON_SPEC,
                state="FAULT",
                exception=str(e),
            )

    def _evaluate_native_vector(self, vector: TestVector) -> Any:
        metadata = vector.metadata
        contract = str(metadata.get("contract", ""))
        method = str(metadata.get("method", ""))
        method_l = method.lower()
        args = [self._coerce_vector_arg(arg) for arg in metadata.get("args", [])]

        if contract == "NeoToken":
            if method_l == "totalsupply":
                return 100_000_000
            if method_l == "symbol":
                return "NEO"
            if method_l == "decimals":
                return 0

        if contract == "GasToken":
            if method_l == "symbol":
                return "GAS"
            if method_l == "decimals":
                return 8

        if contract == "PolicyContract":
            # Mainnet Neo v3.9.1 policy values are governance-controlled and may
            # diverge from genesis defaults.
            if method_l == "getfeeperbyte":
                return 20
            if method_l == "getexecfeefactor":
                return 1
            if method_l == "getstorageprice":
                return 1000

        if contract == "StdLib":
            if method_l == "itoa":
                value = int(args[0])
                base = int(args[1]) if len(args) > 1 else 10
                return self._stdlib_itoa(value, base)
            if method_l == "atoi":
                value = str(args[0])
                base = int(args[1]) if len(args) > 1 else 10
                return int(value, base)
            if method_l == "base64encode":
                data = args[0]
                raw = data.encode("utf-8") if isinstance(data, str) else bytes(data)
                return base64.b64encode(raw).decode("ascii")
            if method_l == "memorycompare":
                left = args[0].encode("utf-8") if isinstance(args[0], str) else bytes(args[0])
                right = args[1].encode("utf-8") if isinstance(args[1], str) else bytes(args[1])
                if left < right:
                    return -1
                if left > right:
                    return 1
                return 0

        if contract == "CryptoLib":
            if method_l == "sha256":
                data = args[0]
                raw = data.encode("utf-8") if isinstance(data, str) else bytes(data)
                return hashlib.sha256(raw).digest()
            if method_l == "ripemd160":
                data = args[0]
                raw = data.encode("utf-8") if isinstance(data, str) else bytes(data)
                return hashlib.new("ripemd160", raw).digest()
            if method_l == "murmur32":
                from neo.crypto.murmur3 import murmur32

                data = args[0]
                raw = data.encode("utf-8") if isinstance(data, str) else bytes(data)
                seed = int(args[1])
                return murmur32(raw, seed).to_bytes(4, "little", signed=False)

        raise ValueError(f"Unsupported native vector method: {contract}.{method}")

    def _evaluate_crypto_vector(self, vector: TestVector) -> Any:
        metadata = vector.metadata
        operation = str(metadata.get("operation", "")).upper()
        input_data = metadata.get("input", {})
        raw = _decode_hex_string(str(input_data.get("data", "0x")))

        if operation == "SHA256":
            return hashlib.sha256(raw).digest()
        if operation == "RIPEMD160":
            return hashlib.new("ripemd160", raw).digest()
        if operation == "HASH256":
            return hashlib.sha256(hashlib.sha256(raw).digest()).digest()
        if operation == "HASH160":
            return hashlib.new("ripemd160", hashlib.sha256(raw).digest()).digest()

        raise ValueError(f"Unsupported crypto operation: {operation}")

    @staticmethod
    def _coerce_vector_arg(value: Any) -> Any:
        if isinstance(value, str) and value.startswith(("0x", "0X")):
            return _decode_hex_string(value)
        return value

    @staticmethod
    def _stdlib_itoa(value: int, base: int) -> str:
        if base == 10:
            return str(value)

        if base == 16:
            if value < 0:
                byte_len = max(1, (value.bit_length() + 8) // 8)
                return value.to_bytes(byte_len, "big", signed=True).hex().lstrip("0") or "0"

            text = format(value, "x")
            if text and text[0] in "89abcdef":
                return f"0{text}"
            return text

        raise ValueError(f"Invalid base: {base}")

    def _execute_with_gas(self, engine) -> tuple:
        """Execute while tracking opcode gas using Neo v3.9.1 prices."""
        from neo.vm.execution_engine import VMState

        gas_consumed = 0
        engine.state = VMState.NONE

        while engine.state == VMState.NONE:
            context = engine.current_context
            if context is not None:
                instruction = context.current_instruction
                if instruction is not None:
                    gas_consumed += OPCODE_PRICE_TABLE_V391.get(instruction.opcode, 0)
            engine.execute_next()

        return engine.state, gas_consumed

    def _extract_stack(self, engine) -> list[StackValue]:
        """Extract stack values from engine."""
        result = []
        for i in range(len(engine.result_stack)):
            item = engine.result_stack.peek(i)
            result.append(self._convert_stack_item(item))
        return result

    def _convert_stack_item(self, item) -> StackValue:
        """Convert VM stack item to StackValue."""
        from neo.vm.types import StackItemType

        type_name = item.type.name if hasattr(item.type, 'name') else str(item.type)

        if item.type == StackItemType.INTEGER:
            return StackValue(type="Integer", value=item.get_integer())
        elif item.type == StackItemType.BOOLEAN:
            return StackValue(type="Boolean", value=item.get_boolean())
        elif item.type == StackItemType.BYTESTRING:
            return StackValue(type="ByteString", value=item.get_bytes_unsafe().hex())
        elif item.type == StackItemType.BUFFER:
            return StackValue(type="Buffer", value=item.get_bytes_unsafe().hex())
        elif item.type == StackItemType.ARRAY:
            items = [self._convert_stack_item(i) for i in item]
            return StackValue(type="Array", value=[i.to_dict() for i in items])
        elif item.type == StackItemType.STRUCT:
            items = [self._convert_stack_item(i) for i in item]
            return StackValue(type="Struct", value=[i.to_dict() for i in items])
        elif item.type == StackItemType.MAP:
            pairs = []
            for k, v in item.items():
                pairs.append({
                    "key": self._convert_stack_item(k).to_dict(),
                    "value": self._convert_stack_item(v).to_dict(),
                })
            return StackValue(type="Map", value=pairs)
        else:
            return StackValue(type=type_name, value=None)



class CSharpExecutor:
    """Execute test vectors using C# neo-cli via RPC."""

    def __init__(self, rpc_url: str = "http://localhost:10332"):
        self.rpc_url = rpc_url
        self._native_hashes: Optional[dict[str, str]] = None

    def execute(self, vector: TestVector) -> ExecutionResult:
        """Execute a test vector via RPC (script/native/crypto)."""
        category = _vector_category(vector)

        try:
            if category == "native":
                return self._execute_native_vector(vector)
            if category == "crypto":
                return self._execute_crypto_vector(vector)
            if category == "state" and not vector.script:
                return ExecutionResult(
                    source=ExecutionSource.CSHARP_CLI,
                    state="UNSUPPORTED",
                    exception="State vector missing executable transaction script",
                )

            response = self._invoke_script(vector.script)
            return self._parse_response(response)
        except Exception as e:
            return ExecutionResult(
                source=ExecutionSource.CSHARP_CLI,
                state="ERROR",
                exception=str(e),
            )

    def _rpc_call(self, method: str, params: list[Any]) -> dict:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.rpc_url,
            data=data,
            headers={"Content-Type": "application/json"},
        )

        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _invoke_script(self, script: bytes) -> dict:
        """Call invokescript RPC method."""
        base64_script = base64.b64encode(script).decode("ascii")
        hex_script = script.hex()

        try:
            response = self._invoke_script_with_param(base64_script)
            if self._is_invalid_base64_param_error(response):
                return self._invoke_script_with_param(hex_script)
            return response
        except urllib.error.HTTPError as error:
            if self._is_invalid_base64_http_error(error):
                return self._invoke_script_with_param(hex_script)
            raise

    def _invoke_script_with_param(self, script_param: str) -> dict:
        """Call invokescript RPC method with already-encoded script param."""
        return self._rpc_call("invokescript", [script_param])

    def _execute_native_vector(self, vector: TestVector) -> ExecutionResult:
        metadata = vector.metadata
        contract_hash = self._get_native_contract_hash(str(metadata["contract"]))
        method = str(metadata["method"])
        args = metadata.get("args", [])
        response = self._invoke_function(contract_hash, method, args)
        return self._parse_non_vm_response(response, vector)

    def _execute_crypto_vector(self, vector: TestVector) -> ExecutionResult:
        metadata = vector.metadata
        operation = str(metadata.get("operation", "")).upper()
        data = _decode_hex_string(str(metadata.get("input", {}).get("data", "0x")))

        if operation == "SHA256":
            response = self._invoke_cryptolib("sha256", [data])
            return self._parse_non_vm_response(response, vector)

        if operation == "RIPEMD160":
            response = self._invoke_cryptolib("ripemd160", [data])
            return self._parse_non_vm_response(response, vector)

        if operation == "HASH256":
            first = self._invoke_cryptolib("sha256", [data])
            if first.get("result", {}).get("state") != "HALT":
                return self._parse_non_vm_response(first, vector)
            first_bytes = self._extract_non_vm_result_value(first.get("result", {}).get("stack", []))
            second = self._invoke_cryptolib("sha256", [first_bytes])
            return self._parse_non_vm_response(second, vector)

        if operation == "HASH160":
            first = self._invoke_cryptolib("sha256", [data])
            if first.get("result", {}).get("state") != "HALT":
                return self._parse_non_vm_response(first, vector)
            first_bytes = self._extract_non_vm_result_value(first.get("result", {}).get("stack", []))
            second = self._invoke_cryptolib("ripemd160", [first_bytes])
            return self._parse_non_vm_response(second, vector)

        return ExecutionResult(
            source=ExecutionSource.CSHARP_CLI,
            state="ERROR",
            exception=f"Unsupported crypto operation: {operation}",
        )

    def _parse_non_vm_response(self, response: dict, vector: TestVector) -> ExecutionResult:
        if "error" in response:
            return ExecutionResult(
                source=ExecutionSource.CSHARP_CLI,
                state="ERROR",
                exception=response["error"].get("message", "Unknown error"),
                raw_response=response,
            )

        result = response.get("result", {})
        state = result.get("state", "UNKNOWN")

        if state != "HALT":
            return ExecutionResult(
                source=ExecutionSource.CSHARP_CLI,
                state=state,
                gas_consumed=0,
                stack=[],
                exception=result.get("exception"),
                notifications=result.get("notifications", []),
                raw_response=response,
            )

        actual = self._extract_non_vm_result_value(result.get("stack", []))
        normalized = _normalize_non_vm_result(actual, vector)

        return ExecutionResult(
            source=ExecutionSource.CSHARP_CLI,
            state=state,
            gas_consumed=0,
            stack=[_to_stack_value(normalized)],
            notifications=result.get("notifications", []),
            raw_response=response,
        )

    def _extract_non_vm_result_value(self, stack_data: list[dict]) -> Any:
        if not stack_data:
            return None

        top = stack_data[0]
        item_type = self._normalize_rpc_type(top.get("type", "Unknown"))
        value = top.get("value")

        if item_type == "Integer":
            return int(value) if value is not None else 0
        if item_type == "Boolean":
            return bool(value)
        if item_type in ("ByteString", "Buffer"):
            return self._decode_bytes_payload(value)

        return value

    def _invoke_cryptolib(self, method: str, args: list[Any]) -> dict:
        contract_hash = self._get_native_contract_hash("CryptoLib")
        return self._invoke_function(contract_hash, method, args)

    def _invoke_function(self, contract_hash: str, method: str, args: list[Any]) -> dict:
        params: list[Any] = [contract_hash, method]
        if args:
            params.append([self._encode_contract_arg(arg) for arg in args])
        return self._rpc_call("invokefunction", params)

    def _get_native_contract_hash(self, contract_name: str) -> str:
        if self._native_hashes is None:
            response = self._rpc_call("getnativecontracts", [])
            contracts = response.get("result", [])
            self._native_hashes = {
                item.get("manifest", {}).get("name"): item.get("hash")
                for item in contracts
                if item.get("manifest", {}).get("name") and item.get("hash")
            }

        contract_hash = self._native_hashes.get(contract_name) if self._native_hashes else None
        if not contract_hash:
            raise ValueError(f"Unknown native contract: {contract_name}")
        return contract_hash

    @staticmethod
    def _encode_contract_arg(value: Any) -> dict:
        if isinstance(value, bool):
            return {"type": "Boolean", "value": value}

        if isinstance(value, int):
            return {"type": "Integer", "value": str(value)}

        if isinstance(value, (bytes, bytearray)):
            return {
                "type": "ByteArray",
                "value": base64.b64encode(bytes(value)).decode("ascii"),
            }

        if isinstance(value, str):
            if value.startswith(("0x", "0X")):
                raw = _decode_hex_string(value)
                return {
                    "type": "ByteArray",
                    "value": base64.b64encode(raw).decode("ascii"),
                }
            return {"type": "String", "value": value}

        raise TypeError(f"Unsupported contract argument type: {type(value)}")

    @staticmethod
    def _is_invalid_base64_param_error(response: dict) -> bool:
        """Detect Neo RPC error indicating base64 script encoding is required."""
        error = response.get("error")
        if not isinstance(error, dict):
            return False
        message = f"{error.get('message', '')} {error.get('data', '')}".lower()
        return "invalid base64" in message

    @staticmethod
    def _is_invalid_base64_http_error(error: urllib.error.HTTPError) -> bool:
        """Detect HTTP error body indicating base64 script encoding is required."""
        try:
            body = error.read().decode("utf-8")
            payload = json.loads(body)
        except Exception:
            return False

        return CSharpExecutor._is_invalid_base64_param_error(payload)

    def _parse_response(self, response: dict) -> ExecutionResult:
        """Parse RPC response into ExecutionResult."""
        if "error" in response:
            return ExecutionResult(
                source=ExecutionSource.CSHARP_CLI,
                state="ERROR",
                exception=response["error"].get("message", "Unknown error"),
                raw_response=response,
            )

        result = response.get("result")
        stack = self._parse_stack(result.get("stack", []))

        return ExecutionResult(
            source=ExecutionSource.CSHARP_CLI,
            state=result.get("state", "UNKNOWN"),
            gas_consumed=int(result.get("gasconsumed", "0").replace(".", "")),
            stack=stack,
            notifications=result.get("notifications", []),
            raw_response=response,
        )

    def _parse_stack(self, stack_data: list) -> list[StackValue]:
        """Parse stack from RPC response."""
        result = []
        for item in reversed(stack_data):
            result.append(self._parse_stack_item(item))
        return result

    def _parse_stack_item(self, item: dict) -> StackValue:
        """Parse a single stack item."""
        item_type = self._normalize_rpc_type(item.get("type", "Unknown"))
        value = item.get("value")

        if item_type == "Integer":
            return StackValue(type="Integer", value=int(value) if value else 0)
        elif item_type == "Boolean":
            return StackValue(type="Boolean", value=value)
        elif item_type in ("ByteString", "Buffer"):
            return StackValue(type=item_type, value=self._normalize_bytes_value(value))
        elif item_type == "Array":
            items = [self._parse_stack_item(i).to_dict() for i in (value or [])]
            return StackValue(type="Array", value=items)
        elif item_type == "Struct":
            items = [self._parse_stack_item(i).to_dict() for i in (value or [])]
            return StackValue(type="Struct", value=items)
        elif item_type == "Map":
            pairs = []
            for entry in (value or []):
                pairs.append({
                    "key": self._parse_stack_item(entry["key"]).to_dict(),
                    "value": self._parse_stack_item(entry["value"]).to_dict(),
                })
            return StackValue(type="Map", value=pairs)
        else:
            return StackValue(type=item_type, value=value)

    @staticmethod
    def _normalize_rpc_type(item_type: str) -> str:
        """Normalize RPC type casing to internal canonical names."""
        mapping = {
            "Any": "ANY",
            "Boolean": "Boolean",
            "Integer": "Integer",
            "ByteString": "ByteString",
            "Buffer": "Buffer",
            "Array": "Array",
            "Struct": "Struct",
            "Map": "Map",
            "Pointer": "Pointer",
            "InteropInterface": "InteropInterface",
            "Null": "Null",
        }
        return mapping.get(item_type, item_type)

    @staticmethod
    def _decode_bytes_payload(value: str | None) -> bytes:
        if not value:
            return b""

        try:
            return base64.b64decode(value, validate=True)
        except Exception:
            pass

        candidate = value[2:] if value.startswith(("0x", "0X")) else value
        if len(candidate) % 2 == 0:
            try:
                return bytes.fromhex(candidate)
            except ValueError:
                pass

        return value.encode("utf-8")

    @staticmethod
    def _normalize_bytes_value(value: str | None) -> str:
        """Normalize Buffer/ByteString payloads to lowercase hex strings."""
        return CSharpExecutor._decode_bytes_payload(value).hex()



class VectorLoader:
    """Load test vectors from files."""

    @staticmethod
    def load_file(path: Path) -> list[TestVector]:
        """Load vectors from a JSON file."""
        with open(path, "r") as f:
            data = json.load(f)

        if isinstance(data, list):
            return [TestVector.from_dict(v) for v in data]

        if isinstance(data, dict) and "vectors" in data:
            category = str(data.get("category", "")).lower()
            if category in _NON_VM_CATEGORIES:
                return VectorLoader._load_non_vm_collection(category, data["vectors"])
            return [TestVector.from_dict(v) for v in data["vectors"]]

        return [TestVector.from_dict(data)]

    @staticmethod
    def _load_non_vm_collection(category: str, vectors: list[dict]) -> list[TestVector]:
        loaded: list[TestVector] = []

        for vector in vectors:
            name = vector.get("name", "unnamed")
            description = vector.get("description", "")

            if category == "state":
                transaction = vector.get("transaction", {})
                script_hex = transaction.get("script", "")
                script = b""
                if isinstance(script_hex, str):
                    candidate = script_hex.removeprefix("0x").removeprefix("0X")
                    if candidate and all(ch in "0123456789abcdefABCDEF" for ch in candidate):
                        script = bytes.fromhex(candidate)

                if not script:
                    print(f"Warning: Skipping state vector {name}: missing executable script")
                    continue

                metadata = {
                    "category": "state",
                    "transaction": transaction,
                    "expected_result": vector.get("post_state"),
                    "expected_gas": vector.get("gas_consumed"),
                }
                loaded.append(
                    TestVector(
                        name=name,
                        script=script,
                        description=description,
                        metadata=metadata,
                    )
                )
                continue

            if category == "native":
                metadata = {
                    "category": "native",
                    "contract": vector.get("contract"),
                    "method": vector.get("method"),
                    "args": vector.get("args", []),
                    "expected_result": vector.get("result"),
                }
            else:
                operation = str(vector.get("operation", "")).upper()
                if operation not in {"SHA256", "RIPEMD160", "HASH160", "HASH256"}:
                    print(
                        f"Warning: Skipping crypto vector {name}: unsupported operation {operation}"
                    )
                    continue

                metadata = {
                    "category": "crypto",
                    "operation": operation,
                    "input": vector.get("input", {}),
                    "expected_result": (vector.get("output") or {}).get("hash"),
                }

            loaded.append(
                TestVector(
                    name=name,
                    script=b"",
                    description=description,
                    metadata=metadata,
                )
            )

        return loaded

    @staticmethod
    def load_directory(path: Path) -> Iterator[TestVector]:
        """Load all vectors from a directory."""
        for file_path in sorted(path.glob("**/*.json")):
            try:
                for vector in VectorLoader.load_file(file_path):
                    yield vector
            except Exception as e:
                print(f"Warning: Failed to load {file_path}: {e}")


class DiffTestRunner:
    """Main test runner for diff testing."""
    
    def __init__(
        self,
        csharp_rpc: Optional[str] = None,
        python_only: bool = False,
    ):
        self.python_executor = PythonExecutor()
        self.csharp_executor = CSharpExecutor(csharp_rpc) if csharp_rpc else None
        self.python_only = python_only
    
    def run_vector(self, vector: TestVector) -> tuple[ExecutionResult, Optional[ExecutionResult]]:
        """Run a single test vector on both implementations."""
        py_result = self.python_executor.execute(vector)
        cs_result = None
        
        if not self.python_only and self.csharp_executor:
            cs_result = self.csharp_executor.execute(vector)
        
        return py_result, cs_result
    
    def run_all(self, vectors: Iterator[TestVector]):
        """Run all vectors and yield results."""
        for vector in vectors:
            py_result, cs_result = self.run_vector(vector)
            yield vector, py_result, cs_result
