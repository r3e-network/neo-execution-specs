"""Test runner for diff testing framework."""

from __future__ import annotations
import json
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Iterator

from neo.tools.diff.models import (
    ExecutionSource,
    ExecutionResult,
    StackValue,
    TestVector,
)


class PythonExecutor:
    """Execute test vectors using Python spec."""
    
    def execute(self, vector: TestVector) -> ExecutionResult:
        """Execute a test vector and return result."""
        from neo.vm.execution_engine import ExecutionEngine, VMState
        
        engine = ExecutionEngine()
        engine.load_script(vector.script)
        
        try:
            state = engine.execute()
            stack = self._extract_stack(engine)
            
            return ExecutionResult(
                source=ExecutionSource.PYTHON_SPEC,
                state=state.name,
                gas_consumed=0,  # TODO: implement gas tracking
                stack=stack,
                exception=None,
            )
        except Exception as e:
            return ExecutionResult(
                source=ExecutionSource.PYTHON_SPEC,
                state="FAULT",
                exception=str(e),
            )
    
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
    
    def execute(self, vector: TestVector) -> ExecutionResult:
        """Execute a test vector via RPC invokescript."""
        try:
            response = self._invoke_script(vector.script)
            return self._parse_response(response)
        except Exception as e:
            return ExecutionResult(
                source=ExecutionSource.CSHARP_CLI,
                state="ERROR",
                exception=str(e),
            )
    
    def _invoke_script(self, script: bytes) -> dict:
        """Call invokescript RPC method."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "invokescript",
            "params": [script.hex()],
        }
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.rpc_url,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    
    def _parse_response(self, response: dict) -> ExecutionResult:
        """Parse RPC response into ExecutionResult."""
        if "error" in response:
            return ExecutionResult(
                source=ExecutionSource.CSHARP_CLI,
                state="ERROR",
                exception=response["error"].get("message", "Unknown error"),
                raw_response=response,
            )
        
        result = response.get("result", )
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
        for item in stack_data:
            result.append(self._parse_stack_item(item))
        return result
    
    def _parse_stack_item(self, item: dict) -> StackValue:
        """Parse a single stack item."""
        item_type = item.get("type", "Unknown")
        value = item.get("value")
        
        if item_type == "Integer":
            return StackValue(type="Integer", value=int(value) if value else 0)
        elif item_type == "Boolean":
            return StackValue(type="Boolean", value=value)
        elif item_type in ("ByteString", "Buffer"):
            return StackValue(type=item_type, value=value or "")
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


class VectorLoader:
    """Load test vectors from files."""
    
    @staticmethod
    def load_file(path: Path) -> list[TestVector]:
        """Load vectors from a JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return [TestVector.from_dict(v) for v in data]
        elif isinstance(data, dict) and "vectors" in data:
            return [TestVector.from_dict(v) for v in data["vectors"]]
        else:
            return [TestVector.from_dict(data)]
    
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
