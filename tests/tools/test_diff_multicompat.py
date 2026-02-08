"""Tests for C#/NeoGo/neo-rs compatibility helper CLI."""

from __future__ import annotations

import json
from pathlib import Path

from neo.tools.diff.multicompat import (
    compare_triplet_reports,
    is_strictly_compatible_triplet,
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


def test_compare_triplet_reports_pairwise_deltas() -> None:
    csharp = _report(
        total=1,
        passed=1,
        failed=0,
        errors=0,
        results=[{"vector": "A", "match": True, "differences": []}],
    )
    neogo = _report(
        total=1,
        passed=1,
        failed=0,
        errors=0,
        results=[{"vector": "A", "match": True, "differences": []}],
    )
    neo_rs = _report(
        total=1,
        passed=0,
        failed=1,
        errors=0,
        results=[{"vector": "A", "match": False, "differences": [{"type": "state_mismatch", "path": "state"}]}],
    )

    deltas = compare_triplet_reports({"csharp": csharp, "neogo": neogo, "neo_rs": neo_rs})

    assert deltas["csharp_vs_neogo"] == []
    assert deltas["csharp_vs_neo_rs"] == ["A"]
    assert deltas["neo_rs_vs_neogo"] == ["A"]


def test_is_strictly_compatible_triplet_requires_clean_summaries() -> None:
    summaries = {
        "csharp": {"total": 2, "passed": 2, "failed": 0, "errors": 0},
        "neogo": {"total": 2, "passed": 2, "failed": 0, "errors": 0},
        "neo_rs": {"total": 2, "passed": 2, "failed": 0, "errors": 0},
    }

    assert is_strictly_compatible_triplet(summaries, {
        "csharp_vs_neo_rs": [],
        "csharp_vs_neogo": [],
        "neo_rs_vs_neogo": [],
    }) is True

    assert is_strictly_compatible_triplet(summaries, {
        "csharp_vs_neo_rs": ["A"],
        "csharp_vs_neogo": [],
        "neo_rs_vs_neogo": [],
    }) is False

    summaries_with_failure = dict(summaries)
    summaries_with_failure["neo_rs"] = {"total": 2, "passed": 1, "failed": 1, "errors": 0}
    assert is_strictly_compatible_triplet(summaries_with_failure, {
        "csharp_vs_neo_rs": [],
        "csharp_vs_neogo": [],
        "neo_rs_vs_neogo": [],
    }) is False


def test_main_returns_zero_for_strict_triplet_compatibility(tmp_path: Path, monkeypatch) -> None:
    clean_report = _report(
        total=1,
        passed=1,
        failed=0,
        errors=0,
        results=[{"vector": "A", "match": True, "differences": []}],
    )

    def fake_run(vectors: Path, rpc_url: str, output_path: Path, gas_tolerance: int) -> int:
        output_path.write_text(json.dumps(clean_report), encoding="utf-8")
        return 0

    monkeypatch.setattr("neo.tools.diff.multicompat._run_report", fake_run)

    exit_code = main([
        "--vectors",
        "tests/vectors/",
        "--output-dir",
        str(tmp_path),
    ])

    assert exit_code == 0


def test_main_allow_shared_failures_when_pairwise_equal(tmp_path: Path, monkeypatch) -> None:
    shared_fail_report = _report(
        total=1,
        passed=0,
        failed=1,
        errors=0,
        results=[{"vector": "A", "match": False, "differences": [{"type": "state_mismatch", "path": "state"}]}],
    )

    def fake_run(vectors: Path, rpc_url: str, output_path: Path, gas_tolerance: int) -> int:
        output_path.write_text(json.dumps(shared_fail_report), encoding="utf-8")
        return 1

    monkeypatch.setattr("neo.tools.diff.multicompat._run_report", fake_run)

    strict_exit = main([
        "--vectors",
        "tests/vectors/",
        "--output-dir",
        str(tmp_path),
    ])
    permissive_exit = main([
        "--vectors",
        "tests/vectors/",
        "--output-dir",
        str(tmp_path),
        "--allow-shared-failures",
    ])

    assert strict_exit == 1
    assert permissive_exit == 0


def test_main_returns_one_when_triplet_reports_differ(tmp_path: Path, monkeypatch) -> None:
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
    neo_rs_report = _report(
        total=1,
        passed=0,
        failed=1,
        errors=0,
        results=[{"vector": "A", "match": False, "differences": [{"type": "gas_mismatch", "path": "gas_consumed"}]}],
    )

    def fake_run(vectors: Path, rpc_url: str, output_path: Path, gas_tolerance: int) -> int:
        report = csharp_report
        if "nspcc" in rpc_url:
            report = neogo_report
        if "127.0.0.1" in rpc_url:
            report = neo_rs_report

        output_path.write_text(json.dumps(report), encoding="utf-8")
        return 1

    monkeypatch.setattr("neo.tools.diff.multicompat._run_report", fake_run)

    exit_code = main([
        "--vectors",
        "tests/vectors/",
        "--output-dir",
        str(tmp_path),
    ])

    assert exit_code == 1
