"""Result comparator for diff testing framework."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from neo.tools.diff.models import ExecutionResult, StackValue


class DiffType(Enum):
    """Type of difference found."""
    STATE_MISMATCH = "state_mismatch"
    STACK_LENGTH = "stack_length"
    STACK_TYPE = "stack_type"
    STACK_VALUE = "stack_value"
    GAS_MISMATCH = "gas_mismatch"
    NOTIFICATION_MISMATCH = "notification_mismatch"


@dataclass
class Difference:
    """A single difference between results."""
    diff_type: DiffType
    path: str
    python_value: any
    csharp_value: any
    message: str = ""
    
    def to_dict(self) -> dict:
        return {
            "type": self.diff_type.value,
            "path": self.path,
            "python": self.python_value,
            "csharp": self.csharp_value,
            "message": self.message,
        }


@dataclass
class ComparisonResult:
    """Result of comparing two execution results."""
    vector_name: str
    is_match: bool
    differences: list[Difference] = field(default_factory=list)
    python_result: Optional[ExecutionResult] = None
    csharp_result: Optional[ExecutionResult] = None
    
    def to_dict(self) -> dict:
        return {
            "vector": self.vector_name,
            "match": self.is_match,
            "differences": [d.to_dict() for d in self.differences],
        }


class ResultComparator:
    """Compare execution results between implementations."""
    
    def __init__(self, gas_tolerance: int = 0):
        self.gas_tolerance = gas_tolerance
    
    def compare(
        self,
        vector_name: str,
        py_result: ExecutionResult,
        cs_result: ExecutionResult,
    ) -> ComparisonResult:
        """Compare Python and C# execution results."""
        differences = []
        
        # Compare state
        if py_result.state != cs_result.state:
            differences.append(Difference(
                diff_type=DiffType.STATE_MISMATCH,
                path="state",
                python_value=py_result.state,
                csharp_value=cs_result.state,
                message=f"State mismatch: {py_result.state} vs {cs_result.state}",
            ))
        
        # Compare stack
        differences.extend(self._compare_stacks(py_result.stack, cs_result.stack))
        
        # Compare gas (with tolerance)
        gas_diff = abs(py_result.gas_consumed - cs_result.gas_consumed)
        if gas_diff > self.gas_tolerance:
            differences.append(Difference(
                diff_type=DiffType.GAS_MISMATCH,
                path="gas_consumed",
                python_value=py_result.gas_consumed,
                csharp_value=cs_result.gas_consumed,
                message=f"Gas difference: {gas_diff}",
            ))
        
        return ComparisonResult(
            vector_name=vector_name,
            is_match=len(differences) == 0,
            differences=differences,
            python_result=py_result,
            csharp_result=cs_result,
        )
    
    def _compare_stacks(
        self,
        py_stack: list[StackValue],
        cs_stack: list[StackValue],
    ) -> list[Difference]:
        """Compare stack contents."""
        differences = []
        
        if len(py_stack) != len(cs_stack):
            differences.append(Difference(
                diff_type=DiffType.STACK_LENGTH,
                path="stack",
                python_value=len(py_stack),
                csharp_value=len(cs_stack),
                message=f"Stack length: {len(py_stack)} vs {len(cs_stack)}",
            ))
            return differences
        
        for i, (py_item, cs_item) in enumerate(zip(py_stack, cs_stack)):
            differences.extend(self._compare_values(f"stack[{i}]", py_item, cs_item))
        
        return differences
    
    def _compare_values(
        self,
        path: str,
        py_val: StackValue,
        cs_val: StackValue,
    ) -> list[Difference]:
        """Compare two stack values."""
        differences = []
        
        if py_val.type != cs_val.type:
            differences.append(Difference(
                diff_type=DiffType.STACK_TYPE,
                path=path,
                python_value=py_val.type,
                csharp_value=cs_val.type,
                message=f"Type mismatch at {path}",
            ))
            return differences
        
        if py_val.value != cs_val.value:
            differences.append(Difference(
                diff_type=DiffType.STACK_VALUE,
                path=path,
                python_value=py_val.value,
                csharp_value=cs_val.value,
                message=f"Value mismatch at {path}",
            ))
        
        return differences
