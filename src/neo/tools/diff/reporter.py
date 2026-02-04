"""Report generator for diff testing framework."""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TextIO

from neo.tools.diff.comparator import ComparisonResult


@dataclass
class DiffReport:
    """Complete diff testing report."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    total_vectors: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    results: list[ComparisonResult] = field(default_factory=list)
    
    @property
    def pass_rate(self) -> float:
        if self.total_vectors == 0:
            return 0.0
        return self.passed / self.total_vectors * 100
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "summary": {
                "total": self.total_vectors,
                "passed": self.passed,
                "failed": self.failed,
                "errors": self.errors,
                "pass_rate": f"{self.pass_rate:.2f}%",
            },
            "results": [r.to_dict() for r in self.results],
        }


class DiffReporter:
    """Generate reports from diff test results."""
    
    def __init__(self):
        self.report = DiffReport()
    
    def add_result(self, result: ComparisonResult, error: bool = False) -> None:
        """Add a comparison result to the report."""
        self.report.total_vectors += 1
        self.report.results.append(result)
        
        if error:
            self.report.errors += 1
        elif result.is_match:
            self.report.passed += 1
        else:
            self.report.failed += 1
    
    def write_json(self, path: Path) -> None:
        """Write report as JSON file."""
        with open(path, "w") as f:
            json.dump(self.report.to_dict(), f, indent=2)
    
    def write_text(self, output: TextIO) -> None:
        """Write human-readable report."""
        r = self.report
        output.write("=" * 60 + "\n")
        output.write("NEO DIFF TEST REPORT\n")
        output.write("=" * 60 + "\n\n")
        
        output.write(f"Timestamp: {r.timestamp}\n")
        output.write(f"Total:     {r.total_vectors}\n")
        output.write(f"Passed:    {r.passed}\n")
        output.write(f"Failed:    {r.failed}\n")
        output.write(f"Errors:    {r.errors}\n")
        output.write(f"Pass Rate: {r.pass_rate:.2f}%\n\n")
        
        # Show failures
        if r.failed > 0:
            output.write("-" * 60 + "\n")
            output.write("FAILURES\n")
            output.write("-" * 60 + "\n\n")
            
            for result in r.results:
                if not result.is_match:
                    self._write_failure(output, result)
    
    def _write_failure(self, output: TextIO, result: ComparisonResult) -> None:
        """Write details of a single failure."""
        output.write(f"Vector: {result.vector_name}\n")
        for diff in result.differences:
            output.write(f"  - {diff.diff_type.value}: {diff.message}\n")
            output.write(f"    Python: {diff.python_value}\n")
            output.write(f"    C#:     {diff.csharp_value}\n")
        output.write("\n")
