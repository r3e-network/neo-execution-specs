"""Tests for C# vs NeoGo compatibility helper CLI."""

from __future__ import annotations

from pathlib import Path

from neo.tools.diff.compat import (
    compare_report_results,
    is_strictly_compatible,
    main,
)


def _report(*, total: int, passed: int, failed: int, errors: int, results: list[dict]) -> dict:
    return {
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "pass_rate": "0.00%",
        },
        "results": results,
    }


def test_compare_report_results_identical() -> None:
    csharp = _report(
        total=2,
        passed=2,
        failed=0,
        errors=0,
        results=[
            {"vector": "A", "match": True, "differences": []},
            {"vector": "B", "match": True, "differences": []},
        ],
    )
    neogo = _report(
        total=2,
        passed=2,
        failed=0,
        errors=0,
        results=[
            {"vector": "A", "match": True, "differences": []},
            {"vector": "B", "match": True, "differences": []},
        ],
    )

    assert compare_report_results(csharp, neogo) == []


def test_compare_report_results_detects_vector_delta() -> None:
    csharp = _report(
        total=1,
        passed=1,
        failed=0,
        errors=0,
        results=[{"vector": "A", "match": True, "differences": []}],
    )
    neogo = _report(
        total=1,
        passed=0,
        failed=1,
        errors=0,
        results=[
            {
                "vector": "A",
                "match": False,
                "differences": [{"type": "state_mismatch", "path": "state"}],
            }
        ],
    )

    assert compare_report_results(csharp, neogo) == ["A"]


def test_compare_report_results_can_ignore_named_vectors() -> None:
    csharp = _report(
        total=1,
        passed=1,
        failed=0,
        errors=0,
        results=[{"vector": "TRY_no_exception", "match": True, "differences": []}],
    )
    neogo = _report(
        total=1,
        passed=0,
        failed=1,
        errors=0,
        results=[
            {
                "vector": "TRY_no_exception",
                "match": False,
                "differences": [{"type": "state_mismatch", "path": "state"}],
            }
        ],
    )

    assert compare_report_results(csharp, neogo) == ["TRY_no_exception"]
    assert (
        compare_report_results(csharp, neogo, ignored_vectors={"TRY_no_exception"})
        == []
    )


def test_is_strictly_compatible_requires_clean_summaries() -> None:
    summary = {"total": 1, "passed": 1, "failed": 0, "errors": 0}
    assert is_strictly_compatible(summary, summary, []) is True
    assert is_strictly_compatible(summary, {"total": 1, "passed": 0, "failed": 1, "errors": 0}, []) is False
    assert is_strictly_compatible(summary, summary, ["A"]) is False


def test_main_returns_zero_for_strict_compatibility(tmp_path: Path, monkeypatch) -> None:
    csharp_report = _report(
        total=1,
        passed=1,
        failed=0,
        errors=0,
        results=[{"vector": "A", "match": True, "differences": []}],
    )
    neogo_report = _report(
        total=1,
        passed=1,
        failed=0,
        errors=0,
        results=[{"vector": "A", "match": True, "differences": []}],
    )

    calls: list[str] = []

    def fake_run(vectors: Path, rpc_url: str, output_path: Path, gas_tolerance: int) -> int:
        calls.append(rpc_url)
        report = csharp_report if "seed1" in rpc_url else neogo_report
        output_path.write_text(__import__("json").dumps(report))
        return 0

    monkeypatch.setattr("neo.tools.diff.compat.run_neo_diff", fake_run)

    exit_code = main(
        [
            "--vectors",
            "tests/vectors/",
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    assert len(calls) == 2


def test_main_returns_one_when_reports_differ(tmp_path: Path, monkeypatch) -> None:
    csharp_report = _report(
        total=1,
        passed=1,
        failed=0,
        errors=0,
        results=[{"vector": "A", "match": True, "differences": []}],
    )
    neogo_report = _report(
        total=1,
        passed=0,
        failed=1,
        errors=0,
        results=[
            {
                "vector": "A",
                "match": False,
                "differences": [{"type": "gas_mismatch", "path": "gas_consumed"}],
            }
        ],
    )

    def fake_run(vectors: Path, rpc_url: str, output_path: Path, gas_tolerance: int) -> int:
        report = csharp_report if "seed1" in rpc_url else neogo_report
        output_path.write_text(__import__("json").dumps(report))
        return 1

    monkeypatch.setattr("neo.tools.diff.compat.run_neo_diff", fake_run)

    exit_code = main(
        [
            "--vectors",
            "tests/vectors/",
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 1


def test_main_ignore_vector_allows_known_single_sided_delta(tmp_path: Path, monkeypatch) -> None:
    csharp_report = _report(
        total=1,
        passed=1,
        failed=0,
        errors=0,
        results=[{"vector": "TRY_no_exception", "match": True, "differences": []}],
    )
    neogo_report = _report(
        total=1,
        passed=0,
        failed=1,
        errors=0,
        results=[
            {
                "vector": "TRY_no_exception",
                "match": False,
                "differences": [{"type": "state_mismatch", "path": "state"}],
            }
        ],
    )

    def fake_run(vectors: Path, rpc_url: str, output_path: Path, gas_tolerance: int) -> int:
        report = csharp_report if "seed1" in rpc_url else neogo_report
        output_path.write_text(__import__("json").dumps(report))
        return 1

    monkeypatch.setattr("neo.tools.diff.compat.run_neo_diff", fake_run)

    strict_exit = main(
        [
            "--vectors",
            "tests/vectors/",
            "--output-dir",
            str(tmp_path),
        ]
    )
    ignored_exit = main(
        [
            "--vectors",
            "tests/vectors/",
            "--output-dir",
            str(tmp_path),
            "--ignore-vector",
            "TRY_no_exception",
        ]
    )

    assert strict_exit == 1
    assert ignored_exit == 0
