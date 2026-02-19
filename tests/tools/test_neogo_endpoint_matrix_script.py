"""Tests for the NeoGo endpoint matrix helper script."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _load_module(module_name: str, script_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_load_expected_vectors_rejects_duplicates(tmp_path: Path) -> None:
    script = Path("scripts/neogo_endpoint_matrix.py")
    module = _load_module("neogo_endpoint_matrix_duplicates", script)

    expected_file = tmp_path / "expected.txt"
    expected_file.write_text("TRY_no_exception\nTRY_no_exception\n", encoding="utf-8")

    with pytest.raises(ValueError, match="duplicates"):
        module._load_expected_vectors(expected_file)


def test_build_probe_vectors_selects_expected_entries(tmp_path: Path) -> None:
    script = Path("scripts/neogo_endpoint_matrix.py")
    module = _load_module("neogo_endpoint_matrix_probe_build", script)

    vectors_root = tmp_path / "vectors"
    (vectors_root / "vm").mkdir(parents=True)
    source_file = vectors_root / "vm" / "control_flow_deep.json"
    source_file.write_text(
        json.dumps(
            {
                "name": "control_flow_deep",
                "description": "test",
                "category": "vm",
                "version": "1.0.0",
                "vectors": [
                    {"name": "TRY_no_exception", "script": "0x00"},
                    {"name": "UNRELATED_VECTOR", "script": "0x01"},
                ],
            }
        ),
        encoding="utf-8",
    )

    probe_root = tmp_path / "probe"
    module._build_probe_vectors(vectors_root, {"TRY_no_exception"}, probe_root)

    generated = probe_root / "vm" / "control_flow_deep.json"
    assert generated.exists()
    payload = json.loads(generated.read_text(encoding="utf-8"))
    vector_names = [entry["name"] for entry in payload["vectors"]]
    assert vector_names == ["TRY_no_exception"]


def test_main_writes_summary_and_returns_zero(tmp_path: Path, monkeypatch) -> None:
    script = Path("scripts/neogo_endpoint_matrix.py")
    module = _load_module("neogo_endpoint_matrix_main_ok", script)

    vectors_root = tmp_path / "vectors"
    (vectors_root / "state").mkdir(parents=True)
    (vectors_root / "state" / "executable_state_deep.json").write_text(
        json.dumps(
            {
                "name": "state",
                "description": "test",
                "category": "state",
                "version": "1.0.0",
                "vectors": [{"name": "STATE_exec_try_l_no_exception", "script": "0x00"}],
            }
        ),
        encoding="utf-8",
    )

    expected_file = tmp_path / "expected.txt"
    expected_file.write_text("STATE_exec_try_l_no_exception\n", encoding="utf-8")

    def fake_probe(
        network: str,
        csharp_rpc: str,
        neogo_rpc: str,
        vectors_path: Path,
        output_dir: Path,
        prefix: str,
        gas_tolerance: int,
        expected_vectors: set[str],
        expected_network: int,
        csharp_useragent_token: str,
        neogo_useragent_token: str,
        enforce_protocol_checks: bool,
        rpc_timeout_seconds: float,
    ):
        assert vectors_path.exists()
        assert output_dir.exists()
        assert prefix == "matrix"
        assert gas_tolerance == 0
        assert expected_vectors == {"STATE_exec_try_l_no_exception"}
        assert expected_network in {860833102, 894710606}
        assert csharp_useragent_token == "Neo:3.9.1"
        assert neogo_useragent_token == "NEO-GO:"
        assert enforce_protocol_checks is True
        assert rpc_timeout_seconds == 5.0

        return module.EndpointMatrixResult(
            network=network,
            csharp_rpc=csharp_rpc,
            neogo_rpc=neogo_rpc,
            csharp_network=860833102,
            csharp_useragent="/Neo:3.9.1/",
            neogo_network=860833102 if network == "mainnet" else 894710606,
            neogo_useragent="/NEO-GO:0.117.0/",
            csharp_summary={"total": 1, "passed": 1, "failed": 0, "errors": 0},
            neogo_summary={"total": 0, "passed": 0, "failed": 1, "errors": 0},
            vector_deltas=["STATE_exec_try_l_no_exception"],
            matches_expected=True,
            protocol_matches_expected=True,
            protocol_mismatches=[],
            error=None,
        )

    monkeypatch.setattr(module, "_run_endpoint_probe", fake_probe)

    output_dir = tmp_path / "reports"
    exit_code = module.main(
        [
            "--vectors-root",
            str(vectors_root),
            "--expected-vectors-file",
            str(expected_file),
            "--mainnet-neogo-rpcs",
            "http://rpc1.n3.nspcc.ru:10332,http://rpc2.n3.nspcc.ru:10332",
            "--testnet-neogo-rpcs",
            "http://rpc.t5.n3.nspcc.ru:20332",
            "--output-dir",
            str(output_dir),
            "--prefix",
            "matrix",
        ]
    )

    assert exit_code == 0
    summary_path = output_dir / "matrix-summary.json"
    assert summary_path.exists()

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["all_matches_expected"] is True
    assert summary["all_vector_matches_expected"] is True
    assert summary["all_protocol_matches_expected"] is True
    assert summary["had_errors"] is False
    assert len(summary["results"]) == 3


def test_main_enforces_expected_vector_match_by_default(tmp_path: Path, monkeypatch) -> None:
    script = Path("scripts/neogo_endpoint_matrix.py")
    module = _load_module("neogo_endpoint_matrix_main_mismatch", script)

    vectors_root = tmp_path / "vectors"
    (vectors_root / "state").mkdir(parents=True)
    (vectors_root / "state" / "executable_state_deep.json").write_text(
        json.dumps(
            {
                "name": "state",
                "description": "test",
                "category": "state",
                "version": "1.0.0",
                "vectors": [{"name": "STATE_exec_try_l_no_exception", "script": "0x00"}],
            }
        ),
        encoding="utf-8",
    )

    expected_file = tmp_path / "expected.txt"
    expected_file.write_text("STATE_exec_try_l_no_exception\n", encoding="utf-8")

    def fake_probe(
        network: str,
        csharp_rpc: str,
        neogo_rpc: str,
        vectors_path: Path,
        output_dir: Path,
        prefix: str,
        gas_tolerance: int,
        expected_vectors: set[str],
        expected_network: int,
        csharp_useragent_token: str,
        neogo_useragent_token: str,
        enforce_protocol_checks: bool,
        rpc_timeout_seconds: float,
    ):
        del network, csharp_rpc, neogo_rpc, vectors_path, output_dir, prefix
        del gas_tolerance, expected_vectors, expected_network
        del csharp_useragent_token, neogo_useragent_token, enforce_protocol_checks
        del rpc_timeout_seconds
        return module.EndpointMatrixResult(
            network="mainnet",
            csharp_rpc="http://seed1.neo.org:10332",
            neogo_rpc="http://rpc1.n3.nspcc.ru:10332",
            csharp_network=860833102,
            csharp_useragent="/Neo:3.9.1/",
            neogo_network=860833102,
            neogo_useragent="/NEO-GO:0.117.0/",
            csharp_summary={"total": 1, "passed": 1, "failed": 0, "errors": 0},
            neogo_summary={"total": 1, "passed": 1, "failed": 0, "errors": 0},
            vector_deltas=[],
            matches_expected=False,
            protocol_matches_expected=True,
            protocol_mismatches=[],
            error=None,
        )

    monkeypatch.setattr(module, "_run_endpoint_probe", fake_probe)

    strict_exit = module.main(
        [
            "--vectors-root",
            str(vectors_root),
            "--expected-vectors-file",
            str(expected_file),
            "--mainnet-neogo-rpcs",
            "http://rpc1.n3.nspcc.ru:10332",
            "--testnet-neogo-rpcs",
            "",
            "--output-dir",
            str(tmp_path / "strict"),
            "--prefix",
            "strict",
        ]
    )
    permissive_exit = module.main(
        [
            "--vectors-root",
            str(vectors_root),
            "--expected-vectors-file",
            str(expected_file),
            "--mainnet-neogo-rpcs",
            "http://rpc1.n3.nspcc.ru:10332",
            "--testnet-neogo-rpcs",
            "",
            "--output-dir",
            str(tmp_path / "permissive"),
            "--prefix",
            "permissive",
            "--allow-inconsistent",
        ]
    )

    assert strict_exit == 1
    assert permissive_exit == 0


def test_main_enforces_protocol_expectations_by_default(
    tmp_path: Path, monkeypatch
) -> None:
    script = Path("scripts/neogo_endpoint_matrix.py")
    module = _load_module("neogo_endpoint_matrix_main_protocol_mismatch", script)

    vectors_root = tmp_path / "vectors"
    (vectors_root / "state").mkdir(parents=True)
    (vectors_root / "state" / "executable_state_deep.json").write_text(
        json.dumps(
            {
                "name": "state",
                "description": "test",
                "category": "state",
                "version": "1.0.0",
                "vectors": [{"name": "STATE_exec_try_l_no_exception", "script": "0x00"}],
            }
        ),
        encoding="utf-8",
    )

    expected_file = tmp_path / "expected.txt"
    expected_file.write_text("STATE_exec_try_l_no_exception\n", encoding="utf-8")

    def fake_probe(
        network: str,
        csharp_rpc: str,
        neogo_rpc: str,
        vectors_path: Path,
        output_dir: Path,
        prefix: str,
        gas_tolerance: int,
        expected_vectors: set[str],
        expected_network: int,
        csharp_useragent_token: str,
        neogo_useragent_token: str,
        enforce_protocol_checks: bool,
        rpc_timeout_seconds: float,
    ):
        del network, csharp_rpc, neogo_rpc, vectors_path, output_dir, prefix
        del gas_tolerance, expected_vectors, expected_network
        del csharp_useragent_token, neogo_useragent_token, enforce_protocol_checks
        del rpc_timeout_seconds
        return module.EndpointMatrixResult(
            network="mainnet",
            csharp_rpc="http://seed1.neo.org:10332",
            neogo_rpc="http://rpc1.n3.nspcc.ru:10332",
            csharp_network=860833102,
            csharp_useragent="/Neo:3.9.1/",
            neogo_network=860833102,
            neogo_useragent="/NEO-GO:0.117.0/",
            csharp_summary={"total": 1, "passed": 1, "failed": 0, "errors": 0},
            neogo_summary={"total": 0, "passed": 0, "failed": 1, "errors": 0},
            vector_deltas=["STATE_exec_try_l_no_exception"],
            matches_expected=True,
            protocol_matches_expected=False,
            protocol_mismatches=["neogo_useragent_missing_token_NEO-GO:"],
            error=None,
        )

    monkeypatch.setattr(module, "_run_endpoint_probe", fake_probe)

    strict_exit = module.main(
        [
            "--vectors-root",
            str(vectors_root),
            "--expected-vectors-file",
            str(expected_file),
            "--mainnet-neogo-rpcs",
            "http://rpc1.n3.nspcc.ru:10332",
            "--testnet-neogo-rpcs",
            "",
            "--output-dir",
            str(tmp_path / "strict-protocol"),
            "--prefix",
            "strict-protocol",
        ]
    )
    permissive_exit = module.main(
        [
            "--vectors-root",
            str(vectors_root),
            "--expected-vectors-file",
            str(expected_file),
            "--mainnet-neogo-rpcs",
            "http://rpc1.n3.nspcc.ru:10332",
            "--testnet-neogo-rpcs",
            "",
            "--output-dir",
            str(tmp_path / "permissive-protocol"),
            "--prefix",
            "permissive-protocol",
            "--allow-inconsistent",
        ]
    )

    assert strict_exit == 1
    assert permissive_exit == 0
