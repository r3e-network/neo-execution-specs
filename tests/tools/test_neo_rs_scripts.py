"""Tests for standalone neo-rs helper scripts."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType


def _load_module(module_name: str, script_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_vector_runner_returns_2_for_missing_vector_file() -> None:
    script = Path("scripts/neo_rs_vector_runner.py")
    module = _load_module("neo_rs_vector_runner_test_missing", script)

    status = module.main(["tests/vectors/does-not-exist.json"])
    assert status == 2


def test_vector_runner_treats_non_gas_failure_as_error(tmp_path: Path, monkeypatch) -> None:
    script = Path("scripts/neo_rs_vector_runner.py")
    module = _load_module("neo_rs_vector_runner_test_fail", script)

    vector_file = tmp_path / "vector.json"
    vector_file.write_text(json.dumps({"vectors": []}), encoding="utf-8")
    report_file = tmp_path / "report.json"

    def fake_run(_vectors: Path, _rpc_url: str, output: Path, _gas_tolerance: int) -> int:
        output.write_text(
            json.dumps(
                {
                    "summary": {"total": 1, "passed": 0, "failed": 1, "errors": 0},
                    "results": [
                        {
                            "vector": "x",
                            "match": False,
                            "differences": [{"type": "state_mismatch", "message": "boom"}],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return 1

    monkeypatch.setattr(module, "_run_neo_diff", fake_run)

    status = module.main([str(vector_file), "--output", str(report_file)])
    assert status == 1


def test_vector_runner_allows_gas_only_mismatch_by_default(tmp_path: Path, monkeypatch) -> None:
    script = Path("scripts/neo_rs_vector_runner.py")
    module = _load_module("neo_rs_vector_runner_test_gas", script)

    vector_file = tmp_path / "vector.json"
    vector_file.write_text(json.dumps({"vectors": []}), encoding="utf-8")
    report_file = tmp_path / "report.json"

    def fake_run(_vectors: Path, _rpc_url: str, output: Path, _gas_tolerance: int) -> int:
        output.write_text(
            json.dumps(
                {
                    "summary": {"total": 1, "passed": 0, "failed": 1, "errors": 0},
                    "results": [
                        {
                            "vector": "x",
                            "match": False,
                            "differences": [{"type": "gas_mismatch", "message": "gas"}],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return 1

    monkeypatch.setattr(module, "_run_neo_diff", fake_run)

    status = module.main([str(vector_file), "--output", str(report_file)])
    assert status == 0


def test_batch_diff_ignores_checklist_file(tmp_path: Path, monkeypatch) -> None:
    script = Path("scripts/neo_rs_batch_diff.py")
    module = _load_module("neo_rs_batch_diff_test_skip", script)

    vectors_dir = tmp_path / "vectors"
    vectors_dir.mkdir()
    (vectors_dir / "checklist_coverage.json").write_text("{}", encoding="utf-8")
    (vectors_dir / "one.json").write_text(json.dumps({"vectors": []}), encoding="utf-8")

    reports_dir = tmp_path / "reports"
    seen: list[Path] = []

    def fake_run(vectors: Path, _rpc_url: str, output: Path, _gas_tolerance: int) -> int:
        seen.append(vectors)
        output.write_text(
            json.dumps(
                {
                    "summary": {"total": 1, "passed": 1, "failed": 0, "errors": 0},
                    "results": [{"vector": vectors.stem, "match": True, "differences": []}],
                }
            ),
            encoding="utf-8",
        )
        return 0

    monkeypatch.setattr(module, "_run_neo_diff", fake_run)

    status = module.main(
        [
            "--vectors-dir",
            str(vectors_dir),
            "--reports-dir",
            str(reports_dir),
            "--delay-seconds",
            "0",
        ]
    )

    assert status == 0
    assert seen == [vectors_dir / "one.json"]


def test_batch_diff_fails_on_non_gas_mismatch(tmp_path: Path, monkeypatch) -> None:
    script = Path("scripts/neo_rs_batch_diff.py")
    module = _load_module("neo_rs_batch_diff_test_fail", script)

    vectors_dir = tmp_path / "vectors"
    vectors_dir.mkdir()
    (vectors_dir / "one.json").write_text(json.dumps({"vectors": []}), encoding="utf-8")

    reports_dir = tmp_path / "reports"

    def fake_run(_vectors: Path, _rpc_url: str, output: Path, _gas_tolerance: int) -> int:
        output.write_text(
            json.dumps(
                {
                    "summary": {"total": 1, "passed": 0, "failed": 1, "errors": 0},
                    "results": [
                        {
                            "vector": "one",
                            "match": False,
                            "differences": [{"type": "stack_value_mismatch", "message": "bad"}],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return 1

    monkeypatch.setattr(module, "_run_neo_diff", fake_run)

    status = module.main(
        [
            "--vectors-dir",
            str(vectors_dir),
            "--reports-dir",
            str(reports_dir),
            "--delay-seconds",
            "0",
        ]
    )

    assert status == 1
